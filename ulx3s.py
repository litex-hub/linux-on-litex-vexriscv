#!/usr/bin/env python3

import argparse
import os

from litex.boards.targets import ulx3s

from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

# Build / Load -------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv with ULX3S board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    parser.add_argument("--diamond", action="store_true", help="use Diamond instead of Trellis")
    args = parser.parse_args()

    soc = SoCLinux(ulx3s.BaseSoC, toolchain="diamond" if args.diamond else "trellis")
    soc.configure_boot()
    soc.compile_device_tree("ulx3s")

    if args.diamond:
        toolchain_path = "/usr/local/diamond/3.10_x64/bin/lin64"
    else:
        toolchain_path = "/usr/share/trellis"

    if args.build:
        builder = Builder(soc, output_dir="build_ulx3s")
        builder.build(toolchain_path=toolchain_path)
        if args.diamond:
            os.system("python3 bit_to_svf.py build_ulx3s/gateware/top.bit build_ulx3s/gateware/top.svf")

    if args.load:
        os.system("ujprog build_ulx3s/gateware/top.svf")
        #os.system("openocd -f openocd/ulx3s.cfg -c \"transport select jtag; init; svf build_ulx3s/gateware/top.svf; exit\"")

if __name__ == "__main__":
    main()
