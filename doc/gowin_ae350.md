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
size. Serve that directory as your TFTP root, or copy the five boot files into
an existing server's `/tftpboot/ae350` directory. For the latter, prefix the
manifest's filenames (the BIOS does not resolve them relative to the manifest):

```sh
sudo install -d /tftpboot/ae350
sudo install -m 644 images/Image images/rv32.dtb images/rootfs.cpio.gz \
    images/opensbi.bin /tftpboot/ae350/
python3 - <<'PY' > /tmp/ae350-boot.json
import json
with open("images/boot.json") as f:
    boot = json.load(f)
files = {"Image", "rv32.dtb", "rootfs.cpio.gz", "opensbi.bin"}
print(json.dumps({"ae350/" + k if k in files else k: v for k, v in boot.items()}, indent=4))
PY
sudo install -m 644 /tmp/ae350-boot.json /tftpboot/ae350/boot.json
openFPGALoader -b tangmega138k \
    build/sipeed_tang_mega_138k_pro/gateware/sipeed_tang_mega_138k_pro.fs
pyterm.py -b 115200 ftdi://ftdi:2232/2
```

`pyterm.py` is supplied by PyFtdi. Interrupt BIOS autoboot and enter:

```text
netboot ae350/boot.json
```

Use `netboot` without an argument when serving `images/` directly as the TFTP
root. The generated manifest passes the DTB through the normal OpenSBI entry
argument. Log in as `root`; the default image has no password. Configure Linux:

```sh
ifconfig eth0 192.168.1.50 netmask 255.255.255.0 up
ping -c 5 192.168.1.125
```

From the host, `ping -c 20 192.168.1.50` checks the reverse direction. Ctrl-C
exits the default PyFtdi terminal. A power cycle requires reloading the SRAM
bitstream and netbooting again.

## What failed and what is worked around

There were separate failures during bring-up. LiteX's AE350 wrapper previously
deasserted the hard block's MBIST reset. A standalone cached store/load test
failed with `INTEG_TRST=1` and passed when only that input was changed to `0`.
Current LiteX holds this input low. This wiring fix is required even without
Linux and is separate from the software workarounds below.

The tested hard CPU reports `mvendorid=0x31e`, `marchid=0x80000a25` and
`mimpid=0x160`. With the MBIST fix, a cold LR/SC probe still exhausted 1000
retries, and a cold AMO probe timed out. Both passed after preloading the target
cache line. Thus the wiring fix alone does not make native atomics usable in
the tested cache-miss cases.
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
retains normal ASIDs, the standard RISC-V timer driver, and the default
top-down mmap layout with ASLR enabled. OpenSBI disables branch prediction
(`MMISC_CTL.BRPE`, CSR `0x7d0`, bit 3). With prediction disabled, 25 dynamic
launches passed. Enabling only BRPE on the same running CPU stalled the next
launch. A halt/resume control did not recover it; clearing only BRPE restored
progress immediately, without changing cache or MMU settings. The final
ordinary target passed 100 launches with prediction disabled.

These experiments identify effective workarounds on this hard CPU revision.
They do not establish the internal silicon mechanism or a manufacturer-confirmed
erratum, nor do they prove that every AE350 implementation needs them. Lowering
the CPU to 400 MHz and tying the other MBIST inputs low did not remove the
remaining stall; neither change is part of the solution.

LiteX UART and Ethernet use polling because their interrupt signals are not
connected to this hard CPU. Its internal PLMT supplies timer interrupts. All
software patches are scoped to the AE350 Buildroot profile. The profile covers
one hart, not SMP. Polling affects console latency and network load handling:
idle ping passed 20/20, while simultaneous TCP traffic yielded 14/20 replies
with the two-slot receive buffer. A 1 MiB TCP download completed with the
expected checksum.

The 800 MHz CPU clock does not imply equivalent DDR3 bandwidth. The measured
large-memory copy and dependent-load workloads remain slower than the default
50 MHz VexRiscv system, despite much faster CoreMark and system calls. This is
an observed integration limitation; its precise bottleneck has not been isolated.

## Runtime check

Build the included test with the generated toolchain and copy it to the same
TFTP directory:

```sh
/path/to/ae350-output/host/bin/riscv32-buildroot-linux-musl-gcc \
    -O2 -pthread -static test/gowin_ae350_runtime.c -latomic -o gowin-ae350-runtime
sudo install -m 755 gowin-ae350-runtime /tftpboot/ae350/
```

On the Linux console:

```sh
cat /proc/sys/vm/legacy_va_layout /proc/sys/kernel/randomize_va_space
i=0
while [ "$i" -lt 100 ]; do
    /bin/busybox cat /proc/self/maps >/dev/null || break
    i=$((i + 1))
done
echo TOPDOWN_EXEC_COUNT=$i
tftp -g -r ae350/gowin-ae350-runtime -l /tmp/gowin-ae350-runtime 192.168.1.125
chmod +x /tmp/gowin-ae350-runtime
/tmp/gowin-ae350-runtime
```

Expect legacy layout `0`, ASLR nonzero, and `TOPDOWN_EXEC_COUNT=100`. The test
checks futex updates and read-only/inaccessible user-memory faults, four
threads with atomic and mutex counters, and shared atomic increments across
25 forks. Success ends with `Gowin AE350 runtime: PASS`.

## Reproducing the performance comparison

Build the same static binaries with the AE350 toolchain for both CPUs. From
this repository, with a fresh `coremark` checkout:

```sh
ae350_cc=/path/to/ae350-output/host/bin/riscv32-buildroot-linux-musl-gcc
git clone https://github.com/eembc/coremark.git
git -C coremark checkout 1f483d5b8316753a742cbf5590caf5bd0a4e4777
make -C coremark compile PORT_DIR=linux CC="$ae350_cc" \
    XCFLAGS='-march=rv32im_zicsr_zifencei -mabi=ilp32 -static'
"$ae350_cc" -O2 -march=rv32im_zicsr_zifencei -mabi=ilp32 -static \
    test/linux_bench.c -lrt -o linux-bench
sudo install -m 755 coremark/coremark.exe linux-bench /tftpboot/ae350/
```

The pinned CoreMark Linux port supplies `-O2`. Its bundled source MD5 list is
stale for `coremark.h`; the sources are unchanged from that commit. Require
both runtime seed/CRC validations and a run time of at least ten seconds.
On each board image:

```sh
tftp -g -r ae350/coremark.exe -l /tmp/coremark.exe 192.168.1.125
tftp -g -r ae350/linux-bench -l /tmp/linux-bench 192.168.1.125
chmod +x /tmp/coremark.exe /tmp/linux-bench
/tmp/coremark.exe 0 0 0x66 0 7 1 2000
/tmp/coremark.exe 0x3415 0x3415 0x66 0 7 1 2000
/tmp/linux-bench
```

`linux-bench` runs each workload three times and must end with
`LINUX_OS_BENCH_PASS`. For each `BENCH` row, divide `ns` by `work` for
nanoseconds per operation, or use `work / 1048576 * 1000000000 / ns` for
memcpy MiB/s. Report the median of each set of three repetitions.

To build the default one-core VexRiscv baseline, omit `--cpu-type`:

```sh
./make.py --board=sipeed_tang_mega_138k_pro \
    --remote-ip=192.168.1.125 --build -- --eth-phy=1000basex
```

Use a separate Buildroot output directory and copy its images to a separate
TFTP directory, following the same manifest-prefix procedure. The repository's
`build/` and `images/` paths are reused, so preserve each CPU's files before
building the other. Use the same benchmark executables for both systems.

For boot timing, load each FPGA image and issue `netboot` three times, recording
the console. Measure from sending the command to the first `login:` prompt,
and separately from the `Linux version` banner to that prompt. Exclude FPGA
programming and the user's login delay; take the median of three boots. These
are host-observed serial intervals and include receive/polling latency. They
compare the actual VexRiscv/glibc and AE350/musl profiles with different image
sizes, rather than isolating the CPU alone.
