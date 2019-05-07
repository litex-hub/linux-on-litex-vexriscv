# Experiments with Linux on LiteX-VexRiscv

> **Note:** Tested on Ubuntu 18.04.

## Demo:
https://asciinema.org/a/WfNA99RCdVi8kTPfzNTeoMTtY :)

## Supported boards/provided bitstreams:
| Name         |       FPGA        |     RAM    |    Flash        | Ethernet | SDCard |
|--------------|-------------------|------------|-----------------|----------|--------|
| Arty         | Artix7 XC7A35T    | 256MB/DDR3 |   16MB/QSPI     |  100Mbps |   No   |
| Versa ECP5   | ECP5 LFE5UM5G-45F | 128MB/DDR3 |   16MB/QSPI*    |   1Gbps  |   No   |
| ULX3S        | ECP5 LFE5U-45F    | 32MB/SDRAM |   4MB/QSPI*     |    No    |   Yes* |
| miniSpartan6+| Spartan6 XC6SLX25 | 32MB/SDRAM |   8MB/QSPI*     |    No    |   Yes* |

> **Note:** \*=present on the board but not yet supported.

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
## Installing Verilator (only needed for simulation)
```sh
$ apt install verilator
$ apt install libevent-dev libjson-c-dev
```
## Installing OpenOCD (only needed for hardware test)
```sh
$ git clone https://github.com/ntfreak/openocd.git
$ cd openocd
$ ./bootstrap
$ ./configure --enable-ftdi
$ make
$ sudo make install
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
VexRiscv Machine Mode software built May  3 2019 19:33:43
--========== Booting Linux =============--
[    0.000000] No DTB passed to the kernel
[    0.000000] Linux version 5.0.9 (florent@lab) (gcc version 8.3.0 (Buildroot 2019.05-git-00938-g75f9fcd0c9)) #1 Thu May 2 17:43:30 CEST 2019
[    0.000000] Initial ramdisk at: 0x(ptrval) (8388608 bytes)
[    0.000000] Zone ranges:
[    0.000000]   Normal   [mem 0x00000000c0000000-0x00000000c7ffffff]
[    0.000000] Movable zone start for each node
[    0.000000] Early memory node ranges
[    0.000000]   node   0: [mem 0x00000000c0000000-0x00000000c7ffffff]
[    0.000000] Initmem setup node 0 [mem 0x00000000c0000000-0x00000000c7ffffff]
[    0.000000] elf_hwcap is 0x1100
[    0.000000] Built 1 zonelists, mobility grouping on.  Total pages: 32512
[    0.000000] Kernel command line: mem=128M@0x40000000 rootwait console=hvc0 root=/dev/ram0 init=/sbin/init swiotlb=32
[    0.000000] Dentry cache hash table entries: 16384 (order: 4, 65536 bytes)
[    0.000000] Inode-cache hash table entries: 8192 (order: 3, 32768 bytes)
[    0.000000] Sorting __ex_table...
[    0.000000] Memory: 119052K/131072K available (1957K kernel code, 92K rwdata, 317K rodata, 104K init, 184K bss, 12020K reserved, 0K cma-reserved)
[    0.000000] SLUB: HWalign=64, Order=0-3, MinObjects=0, CPUs=1, Nodes=1
[    0.000000] NR_IRQS: 0, nr_irqs: 0, preallocated irqs: 0
[    0.000000] clocksource: riscv_clocksource: mask: 0xffffffffffffffff max_cycles: 0x114c1bade8, max_idle_ns: 440795203839 ns
[    0.000155] sched_clock: 64 bits at 75MHz, resolution 13ns, wraps every 2199023255546ns
[    0.001515] Console: colour dummy device 80x25
[    0.008297] printk: console [hvc0] enabled
[    0.009219] Calibrating delay loop (skipped), value calculated using timer frequency.. 150.00 BogoMIPS (lpj=300000)
[    0.009919] pid_max: default: 32768 minimum: 301
[    0.016255] Mount-cache hash table entries: 1024 (order: 0, 4096 bytes)
[    0.016802] Mountpoint-cache hash table entries: 1024 (order: 0, 4096 bytes)
[    0.044297] devtmpfs: initialized
[    0.061343] clocksource: jiffies: mask: 0xffffffff max_cycles: 0xffffffff, max_idle_ns: 7645041785100000 ns
[    0.061981] futex hash table entries: 256 (order: -1, 3072 bytes)
[    0.117611] clocksource: Switched to clocksource riscv_clocksource
[    0.251970] Unpacking initramfs...
[    2.005474] workingset: timestamp_bits=30 max_order=15 bucket_order=0
[    2.178440] Block layer SCSI generic (bsg) driver version 0.4 loaded (major 254)
[    2.178909] io scheduler mq-deadline registered
[    2.179271] io scheduler kyber registered
[    3.031140] random: get_random_bytes called from init_oops_id+0x4c/0x60 with crng_init=0
[    3.043743] Freeing unused kernel memory: 104K
[    3.044070] This architecture does not have kernel memory protection.
[    3.044472] Run /init as init process
mount: mounting tmpfs on /dev/shm failed: Invalid argument
mount: mounting tmpfs on /tmp failed: Invalid argument
mount: mounting tmpfs on /run failed: Invalid argument
Starting syslogd: OK
Starting klogd: OK
Initializing random number generator... [    4.374589] random: dd: uninitialized urandom read (512 bytes read)
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

## Running on hardware with  the Digilent Arty board
To build the target, you will need to install Vivado and run:
```sh
$ ./arty.py --build
```
**The bitstream used for the demo is also provided ( *build_arty/gateware/top.bit/bin*) if you don't want to rebuild it.**

The board will load the kernel binaries over TFTP from 192.168.1.100. You need to copy the files in *binaries* directory and *emulator/emulator.bin* to your TFTP root directory. Once done, you can load the bitstream with:
```sh
$ ./arty.py --load
```
You can also flash the binaries to the SPI Flash of the board and directly boot from it with (**this is the recommended way if you don't want to set up a TFTP server**):
```sh
$ ./arty.py --flash
```
Open your prefered terminal or use lxterm:
```sh
$ lxterm /dev/ttyUSBX
```
And you should see the BIOS prompt and Linux booting :)

## Running on hardware with the Versa ECP5-5G board

To build the target, you will need to install the Yosys/nextpnr/Trellis toolchain and run:
```sh
$ ./versa_ecp5.py --build
```

**The bitstream used for the demo is also provided ( *build_versa5g/gateware/top.bit/svf*) if you don't want to rebuild it.**

The board will load the kernel binaries over TFTP from 192.168.1.100 (you can override this with `--local-ip` and `--remote-ip`). You need to copy the files in *binaries* directory and *emulator/emulator.bin* to your TFTP root directory. Once done, you can load the bitstream with:
```sh
$ ./versa_ecp5.py --load
```

Open your prefered terminal or use lxterm:
```sh
$ lxterm /dev/ttyUSBX
```
And you should see the BIOS prompt and Linux booting :)

## Running on hardware with the ULX3S board

To build the target, you will need to install the Yosys/nextpnr/Trellis toolchain and run:
```sh
$ ./ulx3s.py --build
```

**The bitstream used for the demo is also provided ( *build_ulx3s/gateware/top.bit/svf*) if you don't want to rebuild it.**

You can load the bitstream with:
```sh
$ ./versa_ecp5.py --load
```

The kernel binaries needs to be loaded over serial with using LXTerm:
```sh
$ lxterm --images=serialboot.json --speed=3e6 /dev/ttyUSBX
```

> **Note:** since JTAG/Serial is shared, when you will run lxterm after loading the board, the BIOS serialboot will already have timeout.
You will need to press Enter, see if you have the BIOS prompt and type *reboot*.

And you should see the BIOS prompt and Linux booting :)

## Running on hardware with the miniSpartan6+ board

To build the target, you will need to install ISE and run:
```sh
$ ./minispartan6.py --build
```

**The bitstream used for the demo is also provided ( *build_minispartan6/gateware/top.bit*) if you don't want to rebuild it.**

You can load the bitstream with:
```sh
$ ./minispartan6.py --load
```

The kernel binaries needs to be loaded over serial with using LXTerm:
```sh
$ lxterm --images=serialboot.json --speed=3e6 /dev/ttyUSBX
```

> **Note:** since JTAG/Serial is shared, when you will run lxterm after loading the board, the BIOS serialboot will already have timeout.
You will need to press Enter, see if you have the BIOS prompt and type *reboot*.

And you should see the BIOS prompt and Linux booting :)

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
$ sbt "runMain vexriscv.GenCoreDefault --externalInterruptArray=true --csrPluginConfig=linux-minimal"
```
The Linux variant is the *VexRiscv.v* file.