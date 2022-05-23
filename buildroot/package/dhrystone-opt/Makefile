CPPFLAGS += -DNO_PROTOTYPES=1 -DHZ=100
LDLIBS += -lm
CFLAGS += -O3 -fno-common -fno-inline
CFLAGS += -Wno-implicit-int -Wno-implicit-function-declaration

all: dhrystone

dhrystone: dhry_1.o dhry_2.o
	$(CC) -c $(CFLAGS) -D__riscv_xlen=32 -o strcmp.o strcmp.S
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ strcmp.o $(LDLIBS)

clean:
	rm -f *.o dhrystone

.PHONY: all clean
