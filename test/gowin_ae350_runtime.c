/* SPDX-License-Identifier: BSD-2-Clause */
/* Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr> */

#include <errno.h>
#include <pthread.h>
#include <sched.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <linux/futex.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

#ifndef SYS_futex
#define SYS_futex SYS_futex_time64
#endif

#define CHECK(condition) do { \
	if (!(condition)) { \
		fprintf(stderr, "Line %d: %s failed (errno %d)\n", __LINE__, #condition, errno); \
		return 1; \
	} \
} while (0)

static _Atomic unsigned counter;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
static unsigned protected_counter;

static void *worker(void *unused)
{
	for (unsigned i = 0; i < 10000; i++) {
		atomic_fetch_add(&counter, 1);
		if (pthread_mutex_lock(&mutex))
			abort();
		protected_counter++;
		if (pthread_mutex_unlock(&mutex))
			abort();
		if (!(i % 100))
			sched_yield();
	}
	return NULL;
}

static int test_futex_faults(void)
{
	uint32_t first = 0;
	uint32_t *second = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
		MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	int op = FUTEX_OP(FUTEX_OP_ADD, 3, FUTEX_OP_CMP_EQ, 7);

	CHECK(second != MAP_FAILED);
	*second = 7;
	CHECK(syscall(SYS_futex, &first, FUTEX_WAKE_OP, 1, 1, second, op) == 0);
	CHECK(*second == 10);
	CHECK(mprotect(second, 4096, PROT_READ) == 0);
	CHECK(syscall(SYS_futex, &first, FUTEX_WAKE_OP, 1, 1, second, op) == -1);
	CHECK(errno == EFAULT);
	CHECK(*second == 10);
	CHECK(mprotect(second, 4096, PROT_NONE) == 0);
	CHECK(syscall(SYS_futex, &first, FUTEX_WAKE_OP, 1, 1, second, op) == -1);
	CHECK(errno == EFAULT);
	CHECK(munmap(second, 4096) == 0);
	return 0;
}

int main(void)
{
	pthread_t threads[4];
	setbuf(stdout, NULL);

	CHECK(test_futex_faults() == 0);
	puts("Futex operations and fault handling: PASS");
	for (unsigned i = 0; i < 4; i++)
		CHECK(pthread_create(&threads[i], NULL, worker, NULL) == 0);
	for (unsigned i = 0; i < 4; i++)
		CHECK(pthread_join(threads[i], NULL) == 0);
	CHECK(counter == 40000 && protected_counter == 40000);
	puts("Threads: atomic=40000, mutex=40000: PASS");

	_Atomic unsigned *shared = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
		MAP_SHARED | MAP_ANONYMOUS, -1, 0);
	CHECK(shared != MAP_FAILED);
	atomic_init(shared, 0);
	for (unsigned i = 0; i < 25; i++) {
		pid_t pid = fork();
		CHECK(pid >= 0);
		if (!pid) {
			for (unsigned n = 0; n < 1000; n++)
				atomic_fetch_add(shared, 1);
			_exit(0);
		}
		for (unsigned n = 0; n < 1000; n++)
			atomic_fetch_add(shared, 1);
		int status;
		CHECK(waitpid(pid, &status, 0) == pid && status == 0);
	}
	CHECK(*shared == 50000);
	CHECK(munmap(shared, 4096) == 0);
	puts("Forks: shared atomic=50000: PASS");
	puts("Gowin AE350 runtime: PASS");
	return 0;
}
