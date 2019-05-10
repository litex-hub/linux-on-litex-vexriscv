#!/usr/bin/env python3

import argparse
import os

from migen import *

from litex.boards.targets import versa_ecp5

from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

# Build / Load -------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv with Versa ECP5 board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    parser.add_argument("--diamond", action="store_true", help="use Diamond instead of Trellis")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")
    args = parser.parse_args()

    soc = SoCLinux(versa_ecp5.EthernetSoC, toolchain="diamond" if args.diamond else "trellis")
    soc.configure_ethernet(local_ip=args.local_ip, remote_ip=args.remote_ip)
    soc.configure_boot()
    soc.compile_device_tree("versa_ecp5")

    if args.diamond:
        toolchain_path = "/usr/local/diamond/3.10_x64/bin/lin64"
    else:
        toolchain_path = "/usr/share/trellis"

    if args.load:
        print("Compile board device tree...")
        os.system("dtc -O dtb -o binaries/rv32.dtb buildroot/board/litex_vexriscv/litex_vexriscv_versa_ecp5.dts")

    if args.build:
        builder = Builder(soc, output_dir="build_versa5g")
        builder.build(toolchain_path=toolchain_path)
        if args.diamond:
            os.system("python3 prog/bit_to_svf.py build_versa5g/gateware/top.bit build_versa5g/gateware/top.svf")

    if args.load:
        os.system("openocd -f prog/ecp5-versa5g.cfg -c \"transport select jtag; init; svf build_versa5g/gateware/top.svf; exit\"")

if __name__ == "__main__":
    main()
