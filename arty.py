#!/usr/bin/env python3

import argparse
import os

from litex.boards.targets import arty

from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

# Build / Load / Flash -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv with Arty board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    parser.add_argument("--flash", action="store_true", help="flash bitstream (SPI Flash)")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")
    args = parser.parse_args()

    soc = SoCLinux(arty.BaseSoC)
    soc.add_spi_flash()
    soc.configure_ethernet(local_ip=args.local_ip, remote_ip=args.remote_ip)
    soc.configure_boot()
    soc.compile_device_tree("arty")

    if args.build:
        builder = Builder(soc, output_dir="build_arty")
        builder.build()

    if args.load:
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg")
        prog.load_bitstream("build_arty/gateware/top.bit")

    if args.flash:
        flash_regions = {
            "build_arty/gateware/top.bin": "0x00000000", # FPGA image: automatically loaded at startup
            "binaries/Image":              "0x00400000", # Linux Image: copied to 0xc0000000 by bios
            "binaries/rootfs.cpio":        "0x00800000", # File System: copied to 0xc0800000 by bios
            "binaries/rv32.dtb":           "0x00f00000", # Device tree: copied to 0xc1000000 by bios
            "emulator/emulator.bin":       "0x00f80000", # MM Emulator: copied to 0x20000000 by bios
        }
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg",
            flash_proxy_basename="prog/bscan_spi_xc7a35t.bit")
        prog.set_flash_proxy_dir(".")
        for filename, base in flash_regions.items():
            base = int(base, 16)
            print("Flashing {} at 0x{:08x}".format(filename, base))
            prog.flash(base, filename)

if __name__ == "__main__":
    main()
