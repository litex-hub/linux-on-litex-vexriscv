/* SPDX-License-Identifier: BSD-2-Clause */
/* Copyright (c) 2026 Florent Kermarrec <florent@enjoy-digital.fr> */

#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static uint64_t now(void)
{
	struct timespec t;
	if (clock_gettime(CLOCK_MONOTONIC, &t)) {
		perror("clock_gettime");
		exit(2);
	}
	return (uint64_t)t.tv_sec * 1000000000 + t.tv_nsec;
}

static void report(const char *name, unsigned rep, uint64_t ns,
	unsigned work, unsigned result)
{
	printf("BENCH name=%s rep=%u ns=%llu work=%u result=%u\n",
		name, rep, (unsigned long long)ns, work, result);
}

int main(int argc, char **argv)
{
	if (argc > 1 && !strcmp(argv[1], "--child"))
		return 0;
	setbuf(stdout, NULL);
	printf("LINUX_OS_BENCH_START pid=%d\n", getpid());
	for (unsigned rep = 0; rep < 3; rep++) {
		unsigned sizes[] = {4096, 65536, 4194304};
		const char *names[] = {"chase_4KiB", "chase_64KiB", "chase_4MiB"};
		for (unsigned s = 0; s < 3; s++) {
			unsigned count = sizes[s] / 4, mask = count - 1, index = 0;
			unsigned steps = 1048576;
			volatile uint32_t *p = mmap(NULL, sizes[s], PROT_READ | PROT_WRITE,
				MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
			if (p == MAP_FAILED)
				return 3;
			/* Odd stride visits every word in each power-of-two working set. */
			for (unsigned i = 0; i < count; i++)
				p[i] = (i + 4093) & mask;
			for (unsigned i = 0; i < count; i++)
				index = p[index];
			uint64_t start = now();
			for (unsigned i = 0; i < steps; i++)
				index = p[index];
			uint64_t elapsed = now() - start;
			if (index != ((uint64_t)steps * 4093 & mask))
				return 4;
			report(names[s], rep, elapsed, steps, index);
			munmap((void *)p, sizes[s]);
		}
		unsigned size = 8 * 1024 * 1024, rounds = 16, sum = 0;
		unsigned char *a = mmap(NULL, size * 2, PROT_READ | PROT_WRITE,
			MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
		if (a == MAP_FAILED)
			return 5;
		unsigned char *b = a + size;
		for (unsigned i = 0; i < size; i++)
			a[i] = (i ^ (i >> 8)) & 255;
		memset(b, 0, size);
		uint64_t start = now();
		for (unsigned i = 0; i < rounds; i++) {
			memcpy(b, a, size);
			asm volatile("" ::: "memory");
		}
		uint64_t elapsed = now() - start;
		if (memcmp(a, b, size))
			return 6;
		for (unsigned i = 0; i < size; i++)
			sum += b[i];
		report("memcpy_8MiB", rep, elapsed, size * rounds, sum);
		munmap(a, size * 2);
		unsigned calls = 10000;
		long pid = getpid(), got = 0;
		start = now();
		for (unsigned i = 0; i < calls; i++)
			got = syscall(SYS_getpid);
		elapsed = now() - start;
		if (got != pid)
			return 7;
		report("getpid", rep, elapsed, calls, got);
		unsigned children = 10;
		start = now();
		for (unsigned i = 0; i < children; i++) {
			pid_t child = fork();
			if (!child) {
				execl(argv[0], argv[0], "--child", (char *)NULL);
				_exit(8);
			}
			if (child < 0)
				return 9;
			int status;
			if (waitpid(child, &status, 0) != child || status)
				return 10;
		}
		report("fork_exec", rep, now() - start, children, 0);
	}
	puts("LINUX_OS_BENCH_PASS");
	return 0;
}
