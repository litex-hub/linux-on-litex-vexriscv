#include "hal.h"
#include "config.h"

void stopSim(){
	*((volatile uint32_t*) 0xFFFFFFFC) = 0;
	while(1);
}

void putC(char c){
	*((volatile uint32_t*) 0xFFFFFFF8) = c;
}

int32_t getC(){
	return *((volatile int32_t*) 0xFFFFFFF8);
}

uint32_t rdtime(){
	return *((volatile uint32_t*) 0xFFFFFFE0);
}

uint32_t rdtimeh(){
	return *((volatile uint32_t*) 0xFFFFFFE4);
}

void setMachineTimerCmp(uint32_t low, uint32_t high){
	volatile uint32_t* base = (volatile uint32_t*) 0xFFFFFFE8;
	base[1] = 0xffffffff;
	base[0] = low;
	base[1] = high;
}


void halInit(){
//	putC('*');
//	putC('*');
//	putC('*');
//	while(1){
//		int32_t c = getC();
//		if(c > 0) putC(c);
//	}
}
