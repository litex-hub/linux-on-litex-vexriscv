# Experiments with Linux on LiteX-VexRiscv

> **Note:** Tested on Ubuntu 18.04.*

## Demo:
https://asciinema.org/a/WfNA99RCdVi8kTPfzNTeoMTtY :)

## Installing LiteX
```sh
$ wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
$ ./litex_setup.py init install --user
```
## Installing a RISC-V toolchain
```sh
$ wget https://static.dev.sifive.com/dev-tools/riscv64-unknown-elf-gcc-20171231-x86_64-linux-centos6.tar.gz
$ tar -xvf riscv64-unknown-elf-gcc-20171231-x86_64-linux-centos6.tar.gz
$ export PATH=$PATH:$PWD/riscv64-unknown-elf-gcc-20171231-x86_64-linux-centos6/bin/
```
## Installing Verilator
```sh
$ apt install verilator
$ apt install libevent-dev libjson-c-dev
```
## Running the LiteX simulation
```sh
$ ./sim.py
```
You should see Linux booting and be able to interact with it:
```
        __   _ __      _  __
       / /  (_) /____ | |/_/
      / /__/ / __/ -_)>  <
     /____/_/\__/\__/_/|_|

 (c) Copyright 2012-2019 Enjoy-Digital
 (c) Copyright 2012-2015 M-Labs Ltd

 BIOS built on May  2 2019 18:58:54
 BIOS CRC passed (97ea247b)

--============ SoC info ================--
CPU:       VexRiscv @ 1MHz
ROM:       32KB
SRAM:      4KB
MAIN-RAM:  131072KB

--========= Peripherals init ===========--

--========== Boot sequence =============--
Booting from serial...
Press Q or ESC to abort boot completely.
sL5DdSMmkekro
Timeout
Executing booted program at 0x20000000
--============= Liftoff! ===============--
*** VexRiscv BIOS ***
*** Supervisor ***
No DTB passed to the kernel
Linux version 5.0.9 (florent@lab) (gcc version 8.3.0 (Buildroot 2019.05-git-00938-g412d7a2bdc-dirty)) #1 Fri Apr 26 17:50:49 CEST 2019
Initial ramdisk at: 0x(ptrval) (8388608 bytes)
Zone ranges:
  Normal   [mem 0x00000000c0000000-0x00000000c7ffffff]
Movable zone start for each node
Early memory node ranges
  node   0: [mem 0x00000000c0000000-0x00000000c7ffffff]
Initmem setup node 0 [mem 0x00000000c0000000-0x00000000c7ffffff]
elf_hwcap is 0x1100
Built 1 zonelists, mobility grouping on.  Total pages: 32512
Kernel command line: mem=128M@0x40000000 rootwait console=hvc0 root=/dev/ram0 init=/sbin/init swiotlb=32
Dentry cache hash table entries: 16384 (order: 4, 65536 bytes)
Inode-cache hash table entries: 8192 (order: 3, 32768 bytes)
Sorting __ex_table...
Memory: 119052K/131072K available (1957K kernel code, 92K rwdata, 317K rodata, 104K init, 184K bss, 12020K reserved, 0K cma-reserved)
SLUB: HWalign=64, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
NR_IRQS: 0, nr_irqs: 0, preallocated irqs: 0
clocksource: riscv_clocksource: mask: 0xffffffffffffffff max_cycles: 0x114c1bade8, max_idle_ns: 440795203839 ns
sched_clock: 64 bits at 75MHz, resolution 13ns, wraps every 2199023255546ns
Console: colour dummy device 80x25
printk: console [hvc0] enabled
Calibrating delay loop (skipped), value calculated using timer frequency.. 150.00 BogoMIPS (lpj=300000)
pid_max: default: 32768 minimum: 301
Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
devtmpfs: initialized
clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 7645041785100000 ns
futex hash table entries: 256 (order: -1, 3072 bytes)
clocksource: Switched to clocksource riscv_clocksource
Unpacking initramfs...
workingset: timestamp_bits=30 max_order=15 bucket_order=0
Block layer SCSI generic (bsg) driver version 0.4 loaded (major 254)
io scheduler mq-deadline registered
io scheduler kyber registered
random: get_random_bytes called from init_oops_id+0x4c/0x60 with crng_init=0
Freeing unused kernel memory: 104K
This architecture does not have kernel memory protection.
Run /init as init process
mount: mounting tmpfs on /dev/shm failed: Invalid argument
mount: mounting tmpfs on /tmp failed: Invalid argument
mount: mounting tmpfs on /run failed: Invalid argument
Starting syslogd: OK
Starting klogd: OK
Initializing random number generator... random: dd: uninitialized urandom read (512 bytes read)
done.
Starting network: ip: socket: Function not implemented
ip: socket: Function not implemented
FAIL

Welcome to Buildroot
buildroot login: root
login[48]: root login on 'hvc0'
# help
Built-in commands:
------------------
	. : [ [[ alias bg break cd chdir command continue echo eval exec
	exit export false fg getopts hash help history jobs kill let
	local printf pwd read readonly return set shift source test times
	trap true type ulimit umask unalias unset wait
#
#
```

## Running on hardware (Digilent Arty board)
To build the target, you will need to install Vivado and run:
```sh
$ ./arty.py
```
 The bitstream used for the demo is also provided ( *build/gateware/top.bit*) if you don't want to rebuild it.

The board will load the kernel binaries over TFTP from 192.168.1.100. You need to copy the files in *binaries* directory and *emulator/build/emulator.bin* to your TFTP root directory. Once done, you can load the bitstream with:
```sh
$ ./load.py
```

## Generating the Linux binaries (optional)
```sh
$ git clone http://github.com/buildroot/buildroot
$ cd buildroot
$ cp -r ../linux-litex-vexriscv/buildroot/* ./
$ make litex_vexriscv_defconfig
$ make
```
The binaries are located in *output/images/*.

## Generating the VexRiscv Linux variant (optional)
Install VexRiscv requirements: https://github.com/enjoy-digital/VexRiscv-verilog#requirements

Clone VexRiscv repository and generate the Linux variant:
```sh
$ git clone http://github.com/enjoy-digital/Vexriscv-verilog --recursive
$ sbt "runMain vexriscv.GenCoreDefault --externalInterruptArray=true --csrPluginConfig=linux"
```
The Linux variant is the *VexRiscv.v* file.