#include "hal.h"
#include "config.h"

#define UART_EV_TX  0x1
#define UART_EV_RX  0x2

static inline void csr_writeb(uint8_t value, unsigned long addr)
{
    *((volatile uint8_t *)addr) = value;
}

static inline uint8_t csr_readb(unsigned long addr)
{
    return *(volatile uint8_t *)addr;
}

static inline void csr_writel(uint32_t value, unsigned long addr)
{
    *((volatile uint32_t *)addr) = value;
}

static inline uint32_t csr_readl(unsigned long addr)
{
    return *(volatile uint32_t *)addr;
}

void stopSim(){
    csr_writeb(1, 0xf0008000);
	while(1);
}

void putC(char c){
    uint32_t full;
    full = 1;
    while ((full & 0x1) != 0)
        full = csr_readl(0xf0001804);
    if (c != '\r')
        csr_writeb(c, 0xf0001800);
}

int32_t getC(){
    int32_t c;
    uint32_t empty;
    c = 0xffffffff;
    empty = csr_readl(0xf0001808);
    if ((empty & 0x1) == 0) {
        c = csr_readb(0xf0001800);
        csr_writeb(UART_EV_RX, 0xf0001810);
    }
    return c;
}

uint32_t rdtime(){
    uint8_t i;
    uint32_t t;
    csr_writeb(1, 0xf0008800);
    t = 0;
    for (i=0; i<4; i++) {
        t <<= 8;
        t |= csr_readb(0xf0008804 + 4*(i + 4));
    }
	return t;
}

uint32_t rdtimeh(){
    uint8_t i;
    uint32_t t;
    csr_writeb(1, 0xf0008800);
    t = 0;
    for (i=0; i<4; i++) {
        t <<= 8;
        t |= csr_readb(0xf0008804 + 4*(i + 0));
    }
    return t;
}

void setMachineTimerCmp(uint32_t low, uint32_t high){
    uint8_t i;
    for (i=0; i<4; i++) {
        csr_writeb(low >> (8*(3-i)), 0xf0008824 + 4*(i + 4));
    }
    for (i=0; i<4; i++) {
        csr_writeb(high >> (8*(3-i)), 0xf0008824 + 4*(i + 0));
    }
    csr_writeb(1, 0xf0008800);
}


void halInit(){
//	putC('*');
//	putC('*');
//	putC('*');
//	while(1){
//        uint32_t t;
//        t = rdtime();
//        setMachineTimerCmp(0, t);
//		//int32_t c = getC();
//		//if(c > 0) putC(c);
//	}
}
