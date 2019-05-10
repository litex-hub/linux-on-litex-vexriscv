#!/usr/bin/env python3

import argparse
import os

from litex.boards.targets import minispartan6
from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv with ULX3S board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    args = parser.parse_args()

    soc = SoCLinux(minispartan6.BaseSoC)
    soc.configure_boot()
    soc.compile_device_tree("minispartan6")

    if args.build:
        builder = Builder(soc, output_dir="build/minispartan6")
        builder.build()

    if args.load:
        os.system("xc3sprog -c ftdi build/minispartan6/gateware/top.bit")

if __name__ == "__main__":
    main()
