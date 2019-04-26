# Experiments with Linux on LiteX-VexRiscv

> **Note:** Tested on Ubuntu 18.04.

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
## Running the simulation
```sh
$ ./linux.py
```
## Generating the Linux binaries (optional)
```sh
$ git clone http://github.com/enjoy-digital/buildroot
$ cd buildroot
$ make litex_vexriscv_defconfig
$ make
```