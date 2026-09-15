# Gowin AE350 Linux profile

The AE350 profile runs a single-hart RV32 Linux system with musl. VexRiscv-SMP
remains the default CPU. Use current LiteX, LiteX-Boards, LiteDRAM and LiteEth,
including LiteX's AE350 Linux variant and device-tree support.

For a Tang Mega 138K Pro with Ethernet connected through SFP0:

```sh
./make.py --board=sipeed_tang_mega_138k_pro --cpu-type=gowin_ae350 \
    --remote-ip=192.168.1.125 --build -- --eth-phy=1000basex
```

Replace the server address with your TFTP server's address. The board retains
its standard 50 MHz system clock and uses the 800 MHz hard CPU. The last `--`
separates project options from LiteX-Boards target options.

Build the software in a fresh Buildroot output directory. From this repository:

```sh
make -C /path/to/buildroot O=/path/to/ae350-output \
    BR2_EXTERNAL="$PWD/buildroot" \
    BR2_DEFCONFIG="$PWD/build/sipeed_tang_mega_138k_pro/buildroot_defconfig" defconfig
make -C /path/to/buildroot O=/path/to/ae350-output
```

The post-image script populates `images/` and updates the generated DTB's initrd
size. Serve that directory as your TFTP root. Load the generated FPGA bitstream
into SRAM, interrupt BIOS autoboot, and run `netboot`. The generated `boot.json`
passes the DTB through the normal OpenSBI entry argument. No extra entry program
is needed. Log in as `root` on the 115200-baud console; the default image has no
root password. Configure Ethernet as needed, for example:

```sh
ifconfig eth0 192.168.1.50 netmask 255.255.255.0 up
ping -c 5 192.168.1.125
```

## CPU requirements

The tested hard CPU reports `mvendorid=0x31e`, `marchid=0x80000a25` and
`mimpid=0x160`. Its cache-miss atomics do not provide usable forward progress.
The kernel therefore uses Linux's existing interrupt-protected uniprocessor
atomic and futex operations. OpenSBI initializes the caches before its first
atomic operation. Musl and libatomic load and fence the target cache line before
each LR/SC attempt.

Userspace targets **RV32IM**, with software floating point. Use the generated
toolchain and link applications using C11 atomics with `-latomic`. Prebuilt
RV32IMA binaries and applications containing their own atomic assembly require
separate review; the profile does not make arbitrary native AMOs safe.

The [Andes 2X MMU workaround](https://github.com/andestech/linux/blob/7908d1aed3dbeea4173b92f90d67cf300d29f633/arch/riscv/errata/andes/errata.c)
synchronizes page-table writes with a walker that does not snoop L1D. The kernel
retains normal ASIDs and the standard RISC-V timer driver. Bottom-up mmap is
selected through `vm.legacy_va_layout=1`; ASLR remains enabled. The cause of the
observed stalls with the default top-down layout is still unresolved.

LiteX UART and Ethernet use polling because their interrupt signals are not
connected to this hard CPU. Its internal PLMT supplies timer interrupts. All
software patches are scoped to the AE350 Buildroot profile.

## Runtime check

Build the included test with the generated toolchain, copy it to the board, and
run it from the console:

```sh
/path/to/ae350-output/host/bin/riscv32-buildroot-linux-musl-gcc \
    -O2 -pthread -static test/gowin_ae350_runtime.c -latomic -o gowin-ae350-runtime
```

It checks futex updates and read-only/inaccessible user-memory faults, four
threads with atomic and mutex counters, and shared atomic increments across
25 forks. Success ends with `Gowin AE350 runtime: PASS`.
