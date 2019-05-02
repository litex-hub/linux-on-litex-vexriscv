PROJ_NAME=emulator
DEBUG=no
MULDIV=no
COMPRESSED=no
STANDALONE = ..


SRCS = 	$(wildcard src/*.c) \
		$(wildcard src/*.cpp)  \
		$(wildcard src/*.S)


LDSCRIPT = ram.ld

include riscv64-unknown-elf.mk
include standalone.mk

