/* LiteX / VexRiscv Machine Mode Emulator */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <irq.h>
#include <uart.h>
#include <console.h>

#include <hw/flags.h>
#include <generated/csr.h>
#include <generated/mem.h>

#include "riscv.h"
#include "framebuffer.h"

#define LINUX_IMAGE_BASE 0xC0000000
#define LINUX_DTB_BASE   0xC1000000

#define max(a,b) \
  ({ __typeof__ (a) _a = (a); \
      __typeof__ (b) _b = (b); \
    _a > _b ? _a : _b; })


#define min(a,b) \
  ({ __typeof__ (a) _a = (a); \
      __typeof__ (b) _b = (b); \
    _a < _b ? _a : _b; })

extern const uint32_t _sp;

void vexriscv_machine_mode_trap(void);

/* LiteX peripherals access functions */

static void litex_putchar(char c){
    uint32_t full;
    full = 1;
    while ((full & 0x1) != 0)
        full = uart_txfull_read();
    if (c != '\r')
        uart_rxtx_write(c);
}

static int32_t litex_getchar(void){
    int32_t c;
    uint32_t empty;
    c = 0xffffffff;
    empty = uart_rxempty_read();
    if ((empty & 0x1) == 0) {
        c = uart_rxtx_read();
        uart_ev_pending_write(UART_EV_RX);
    }
    return c;
}

static uint32_t litex_read_cpu_timer_lsb(void){
    cpu_timer_latch_write(1);
    return ((cpu_timer_time_read() >> 0) & 0xffffffff);
}

static uint32_t litex_read_cpu_timer_msb(void){
    cpu_timer_latch_write(1);
    return ((cpu_timer_time_read() >> 32) & 0xffffffff);
}

static void litex_write_cpu_timer_cmp(uint32_t low, uint32_t high){
    cpu_timer_time_cmp_write(((uint64_t) high << 32) | low);
    cpu_timer_latch_write(1);
}

static void litex_stop(void){
#ifdef CSR_SUPERVISOR_FINISH_ADDR
    supervisor_finish_write(1);
#endif
	while(1);
}

/* VexRiscv Registers / Words access functions */

static int vexriscv_read_register(uint32_t id){
    unsigned int sp = (unsigned int) (&_sp);
	return ((int*) sp)[id-32];
}
static void vexriscv_write_register(uint32_t id, int value){
	uint32_t sp = (uint32_t) (&_sp);
	((uint32_t*) sp)[id-32] = value;
}



#define vexriscv_trap_barrier_start \
		"  	li       %[tmp],  0x00020000\n" \
		"	csrs     mstatus,  %[tmp]\n" \
		"  	la       %[tmp],  1f\n" \
		"	csrw     mtvec,  %[tmp]\n" \
		"	li       %[fail], 1\n" \

#define vexriscv_trap_barrier_end \
		"	li       %[fail], 0\n" \
		"1:\n" \
		"  	li       %[tmp],  0x00020000\n" \
		"	csrc     mstatus,  %[tmp]\n" \

static int32_t vexriscv_read_word(uint32_t address, int32_t *data){
	int32_t result, tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	lw       %[result], 0(%[address])\n"
		vexriscv_trap_barrier_end
		: [result]"=&r" (result), [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address)
		: "memory"
	);

	*data = result;
	return fail;
}

static int32_t vexriscv_read_word_unaligned(uint32_t address, int32_t *data){
	int32_t result, tmp;
	int32_t fail;
	__asm__ __volatile__ (
			vexriscv_trap_barrier_start
		"	lbu      %[result], 0(%[address])\n"
		"	lbu      %[tmp],    1(%[address])\n"
		"	slli     %[tmp],  %[tmp], 8\n"
		"	or       %[result], %[result], %[tmp]\n"
		"	lbu      %[tmp],    2(%[address])\n"
		"	slli     %[tmp],  %[tmp], 16\n"
		"	or       %[result], %[result], %[tmp]\n"
		"	lbu      %[tmp],    3(%[address])\n"
		"	slli     %[tmp],  %[tmp], 24\n"
		"	or       %[result], %[result], %[tmp]\n"
		vexriscv_trap_barrier_end
		: [result]"=&r" (result), [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address)
		: "memory"
	);

	*data = result;
	return fail;
}

static int32_t vexriscv_read_half_unaligned(uint32_t address, int32_t *data){
	int32_t result, tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	lb       %[result], 1(%[address])\n"
		"	slli     %[result],  %[result], 8\n"
		"	lbu      %[tmp],    0(%[address])\n"
		"	or       %[result], %[result], %[tmp]\n"
		vexriscv_trap_barrier_end
		: [result]"=&r" (result), [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address)
		: "memory"
	);

	*data = result;
	return fail;
}

static int32_t vexriscv_write_word(uint32_t address, int32_t data){
	int32_t tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	sw       %[data], 0(%[address])\n"
		vexriscv_trap_barrier_end
		: [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address), [data]"r" (data)
		: "memory"
	);

	return fail;
}


static int32_t vexriscv_write_word_unaligned(uint32_t address, int32_t data){
	int32_t tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	sb       %[data], 0(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 1(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 2(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 3(%[address])\n"
		vexriscv_trap_barrier_end
		: [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address), [data]"r" (data)
		: "memory"
	);

	return fail;
}



static int32_t vexriscv_write_short_unaligned(uint32_t address, int32_t data){
	int32_t tmp;
	int32_t fail;
	__asm__ __volatile__ (
		vexriscv_trap_barrier_start
		"	sb       %[data], 0(%[address])\n"
		"	srl      %[data], %[data], 8\n"
		"	sb       %[data], 1(%[address])\n"
		vexriscv_trap_barrier_end
		: [fail]"=&r" (fail), [tmp]"=&r" (tmp)
		: [address]"r" (address), [data]"r" (data)
		: "memory"
	);

	return fail;
}

/* VexRiscv Machine Mode Emulator */

static void vexriscv_machine_mode_trap_entry(void) {
	__asm__ __volatile__ (
	"csrrw sp, mscratch, sp\n"
	"sw x1,   1*4(sp)\n"
	"sw x3,   3*4(sp)\n"
	"sw x4,   4*4(sp)\n"
	"sw x5,   5*4(sp)\n"
	"sw x6,   6*4(sp)\n"
	"sw x7,   7*4(sp)\n"
	"sw x8,   8*4(sp)\n"
	"sw x9,   9*4(sp)\n"
	"sw x10,   10*4(sp)\n"
	"sw x11,   11*4(sp)\n"
	"sw x12,   12*4(sp)\n"
	"sw x13,   13*4(sp)\n"
	"sw x14,   14*4(sp)\n"
	"sw x15,   15*4(sp)\n"
	"sw x16,   16*4(sp)\n"
	"sw x17,   17*4(sp)\n"
	"sw x18,   18*4(sp)\n"
	"sw x19,   19*4(sp)\n"
	"sw x20,   20*4(sp)\n"
	"sw x21,   21*4(sp)\n"
	"sw x22,   22*4(sp)\n"
	"sw x23,   23*4(sp)\n"
	"sw x24,   24*4(sp)\n"
	"sw x25,   25*4(sp)\n"
	"sw x26,   26*4(sp)\n"
	"sw x27,   27*4(sp)\n"
	"sw x28,   28*4(sp)\n"
	"sw x29,   29*4(sp)\n"
	"sw x30,   30*4(sp)\n"
	"sw x31,   31*4(sp)\n"
	"call vexriscv_machine_mode_trap\n"
	"lw x1,   1*4(sp)\n"
	"lw x3,   3*4(sp)\n"
	"lw x4,   4*4(sp)\n"
	"lw x5,   5*4(sp)\n"
	"lw x6,   6*4(sp)\n"
	"lw x7,   7*4(sp)\n"
	"lw x8,   8*4(sp)\n"
	"lw x9,   9*4(sp)\n"
	"lw x10,   10*4(sp)\n"
	"lw x11,   11*4(sp)\n"
	"lw x12,   12*4(sp)\n"
	"lw x13,   13*4(sp)\n"
	"lw x14,   14*4(sp)\n"
	"lw x15,   15*4(sp)\n"
	"lw x16,   16*4(sp)\n"
	"lw x17,   17*4(sp)\n"
	"lw x18,   18*4(sp)\n"
	"lw x19,   19*4(sp)\n"
	"lw x20,   20*4(sp)\n"
	"lw x21,   21*4(sp)\n"
	"lw x22,   22*4(sp)\n"
	"lw x23,   23*4(sp)\n"
	"lw x24,   24*4(sp)\n"
	"lw x25,   25*4(sp)\n"
	"lw x26,   26*4(sp)\n"
	"lw x27,   27*4(sp)\n"
	"lw x28,   28*4(sp)\n"
	"lw x29,   29*4(sp)\n"
	"lw x30,   30*4(sp)\n"
	"lw x31,   31*4(sp)\n"
	"csrrw sp, mscratch, sp\n"
	"mret\n"
	);
}

static void vexriscv_machine_mode_pmp_init(void)
{
  /* Allow access to all the memory, ignore the illegal
     instruction trap if PMPs are not supported */
  uintptr_t pmpc = PMP_NAPOT | PMP_R | PMP_W | PMP_X;
  asm volatile ("la t0, 1f\n\t"
                "csrw mtvec, t0\n\t"
                "csrw pmpaddr0, %1\n\t"
                "csrw pmpcfg0, %0\n\t"
                ".align 2\n\t"
                "1:"
                : : "r" (pmpc), "r" (-1UL) : "t0");
}

static void vexriscv_machine_mode_init(void) {
	vexriscv_machine_mode_pmp_init();
	uint32_t sp = (uint32_t) (&_sp);
	csr_write(mtvec,    vexriscv_machine_mode_trap_entry);
	csr_write(mscratch, sp -32*4);
	csr_write(mstatus,  0x0800 | MSTATUS_MPIE);
	csr_write(mie,      0);
	csr_write(mepc,     LINUX_IMAGE_BASE);
	/* Stop in case of miss-aligned accesses */
	csr_write(medeleg, MEDELEG_INSTRUCTION_PAGE_FAULT | MEDELEG_LOAD_PAGE_FAULT | MEDELEG_STORE_PAGE_FAULT | MEDELEG_USER_ENVIRONNEMENT_CALL);
	csr_write(mideleg, MIDELEG_SUPERVISOR_TIMER | MIDELEG_SUPERVISOR_EXTERNAL | MIDELEG_SUPERVISOR_SOFTWARE);
	/* Avoid simulation missmatch */
	csr_write(sbadaddr, 0);
}

static void vexriscv_machine_mode_trap_to_supervisor_trap(uint32_t sepc, uint32_t mstatus){
	csr_write(mtvec,    vexriscv_machine_mode_trap_entry);
	csr_write(sbadaddr, csr_read(mbadaddr));
	csr_write(scause,   csr_read(mcause));
	csr_write(sepc,     sepc);
	csr_write(mepc,	    csr_read(stvec));
	csr_write(mstatus,
			  (mstatus & ~(MSTATUS_SPP | MSTATUS_MPP | MSTATUS_SIE | MSTATUS_SPIE))
			| ((mstatus >> 3) & MSTATUS_SPP)
			| (0x0800 | MSTATUS_MPIE)
			| ((mstatus & MSTATUS_SIE) << 4)
	);
}


static uint32_t vexriscv_read_instruction(uint32_t pc){
	uint32_t i;
	if (pc & 2) {
		vexriscv_read_word(pc - 2, (int32_t*)&i);
		i >>= 16;
		if ((i & 3) == 3) {
			uint32_t u32Buf;
			vexriscv_read_word(pc+2, (int32_t*)&u32Buf);
			i |= u32Buf << 16;
		}
	} else {
		vexriscv_read_word(pc, (int32_t*)&i);
	}
	return i;
}


void vexriscv_machine_mode_trap(void) {
	int32_t cause = csr_read(mcause);

	/* Interrupt */
	if(cause < 0){
		switch(cause & 0xff){
			case CAUSE_MACHINE_TIMER: {
				csr_set(sip, MIP_STIP);
				csr_clear(mie, MIE_MTIE);
			} break;
			default: litex_stop(); break;
		}
	/* Exception */
	} else {
		switch(cause){
		    case CAUSE_UNALIGNED_LOAD:{
			    uint32_t mepc = csr_read(mepc);
			    uint32_t mstatus = csr_read(mstatus);
			    uint32_t instruction = vexriscv_read_instruction(mepc);
			    uint32_t address = csr_read(mbadaddr);
			    uint32_t func3 =(instruction >> 12) & 0x7;
			    uint32_t rd = (instruction >> 7) & 0x1F;
			    int32_t readValue;
			    int32_t fail = 1;

			    switch(func3){
			    case 1: fail = vexriscv_read_half_unaligned(address, &readValue); break;  //LH
			    case 2: fail = vexriscv_read_word_unaligned(address, &readValue); break; //LW
			    case 5: fail = vexriscv_read_half_unaligned(address, &readValue) & 0xFFFF; break; //LHU
			    }

			    if(fail){
				    vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
				    return;
			    }

			    vexriscv_write_register(rd, readValue);
			    csr_write(mepc, mepc + 4);
			    csr_write(mtvec, vexriscv_machine_mode_trap_entry); //Restore mtvec
		    }break;
		    case CAUSE_UNALIGNED_STORE:{
			    uint32_t mepc = csr_read(mepc);
			    uint32_t mstatus = csr_read(mstatus);
			    uint32_t instruction = vexriscv_read_instruction(mepc);
			    uint32_t address = csr_read(mbadaddr);
			    uint32_t func3 =(instruction >> 12) & 0x7;
			    int32_t writeValue = vexriscv_read_register((instruction >> 20) & 0x1F);
			    int32_t fail = 1;

			    switch(func3){
			    case 1: fail = vexriscv_write_short_unaligned(address, writeValue); break; //SH
			    case 2: fail = vexriscv_write_word_unaligned(address, writeValue); break; //SW
			    }

			    if(fail){
				    vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
				    return;
			    }

			    csr_write(mepc, mepc + 4);
			    csr_write(mtvec, vexriscv_machine_mode_trap_entry); //Restore mtvec
		    }break;
			/* Illegal instruction */
			case CAUSE_ILLEGAL_INSTRUCTION:{
				uint32_t mepc = csr_read(mepc);
				uint32_t mstatus = csr_read(mstatus);
				uint32_t instr = csr_read(mbadaddr);

				uint32_t opcode = instr & 0x7f;
				uint32_t funct3 = (instr >> 12) & 0x7;
				switch(opcode){
					/* Atomic */
					case 0x2f:
						switch(funct3){
							case 0x2:{
								uint32_t sel = instr >> 27;
								uint32_t addr = vexriscv_read_register((instr >> 15) & 0x1f);
								int32_t src = vexriscv_read_register((instr >> 20) & 0x1f);
								uint32_t rd = (instr >> 7) & 0x1f;
								int32_t read_value;
								int32_t write_value = 0
								;
								if(vexriscv_read_word(addr, &read_value)) {
									vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
									return;
								}

								switch(sel){
									case 0x0:  write_value = src + read_value; break;
									case 0x1:  write_value = src; break;
									case 0x2:  break; /*  LR, SC done in hardware (cheap) and require */
									case 0x3:  break; /*  to keep track of context switches */
									case 0x4:  write_value = src ^ read_value; break;
									case 0xC:  write_value = src & read_value; break;
									case 0x8:  write_value = src | read_value; break;
									case 0x10: write_value = min(src, read_value); break;
									case 0x14: write_value = max(src, read_value); break;
									case 0x18: write_value = min((unsigned int)src, (unsigned int)read_value); break;
									case 0x1C: write_value = max((unsigned int)src, (unsigned int)read_value); break;
									default: litex_stop(); return; break;
								}
								if(vexriscv_write_word(addr, write_value)){
									vexriscv_machine_mode_trap_to_supervisor_trap(mepc, mstatus);
									return;
								}
								vexriscv_write_register(rd, read_value);
								csr_write(mepc, mepc + 4);
								csr_write(mtvec, vexriscv_machine_mode_trap_entry); /* Restore MTVEC */
							} break;
							default: litex_stop(); break;
						} break;
					/* CSR */
					case 0x73:{
						uint32_t input = (instr & 0x4000) ? ((instr >> 15) & 0x1f) : vexriscv_read_register((instr >> 15) & 0x1f);
						__attribute__((unused)) uint32_t clear, set;
						uint32_t write;
						switch (funct3 & 0x3) {
							case 0: litex_stop(); break;
							case 1: clear = ~0; set = input; write = 1; break;
							case 2: clear = 0; set = input; write = ((instr >> 15) & 0x1f) != 0; break;
							case 3: clear = input; set = 0; write = ((instr >> 15) & 0x1f) != 0; break;
						}
						uint32_t csrAddress = instr >> 20;
						uint32_t old;
						switch(csrAddress){
							case RDCYCLE :
							case RDINSTRET:
							case RDTIME  : old = litex_read_cpu_timer_lsb(); break;
							case RDCYCLEH :
							case RDINSTRETH:
							case RDTIMEH : old = litex_read_cpu_timer_msb(); break;
							default: litex_stop(); break;
						}
						if(write) {
							switch(csrAddress){
								default: litex_stop(); break;
							}
						}

						vexriscv_write_register((instr >> 7) & 0x1f, old);
						csr_write(mepc, mepc + 4);

					} break;
					default: litex_stop(); break;
				}
			} break;
			/* System call */
			case CAUSE_SCALL:{
				uint32_t which = vexriscv_read_register(17);
				uint32_t a0 = vexriscv_read_register(10);
				uint32_t a1 = vexriscv_read_register(11);
				__attribute__((unused)) uint32_t a2 = vexriscv_read_register(12);
				switch(which){
					case SBI_CONSOLE_PUTCHAR: {
						litex_putchar(a0);
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					case SBI_CONSOLE_GETCHAR: {
						vexriscv_write_register(10, litex_getchar());
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					case SBI_SET_TIMER: {
						litex_write_cpu_timer_cmp(a0, a1);
						csr_set(mie, MIE_MTIE);
						csr_clear(sip, MIP_STIP);
						csr_write(mepc, csr_read(mepc) + 4);
					} break;
					default: litex_stop(); break;
				}
			} break;
			default: litex_stop(); break;
		}
	}
}

static void vexriscv_machine_mode_boot(void) {
	__asm__ __volatile__ (
		" li a0, 0\n"
		" li a1, %0\n"
		" mret"
		 : : "i" (LINUX_DTB_BASE)
	);
}

/* Main */

int main(void)
{
	irq_setmask(0);
	irq_setie(1);
	uart_init();
	puts("VexRiscv Machine Mode software built "__DATE__" "__TIME__"");
#ifdef CSR_FRAMEBUFFER_BASE
	framebuffer_init();
#endif
	printf("--========== \e[1mBooting Linux\e[0m =============--\n");
	uart_sync();
	vexriscv_machine_mode_init();
	vexriscv_machine_mode_boot();
}
