#!/usr/bin/env python3

import argparse
import os

from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

# Targets Import -----------------------------------------------------------------------------------

from litex.boards.targets import arty
from litex.boards.targets import minispartan6
from litex.boards.targets import versa_ecp5
from litex.boards.targets import ulx3s

socs = {
    "arty":         arty.EthernetSoC,
    "minispartan6": minispartan6.BaseSoC,
    "versa_ecp5":   versa_ecp5.EthernetSoC,
    "ulx3s":        ulx3s.BaseSoC
}

socs_capabilities = {
    "arty":         "serial+ethernet+spiflash",
    "minispartan6": "serial",
    "versa_ecp5":   "serial+ethernet",
    "ulx3s":        "serial"
}

# Load Bistream ------------------------------------------------------------------------------------

def arty_load():
    from litex.build.openocd import OpenOCD
    prog = OpenOCD("prog/openocd_xilinx.cfg")
    prog.load_bitstream("build/arty/gateware/top.bit")

def minispartan6_load():
    os.system("xc3sprog -c ftdi build/minispartan6/gateware/top.bit")

def versa_ecp5_load():
    os.system("python3 prog/bit_to_svf.py build/versa_ecp5/gateware/top.bit build/versa_ecp5/gateware/top.svf")
    os.system("openocd -f prog/ecp5-versa5g.cfg -c \"transport select jtag; init; svf build/versa_ecp5/gateware/top.svf; exit\"")

def ulx3s_load():
    os.system("ujprog build/ulx3s/gateware/top.svf")

boards_load_functions = {
    "arty":         arty_load,
    "minispartan6": minispartan6_load,
    "versa_ecp5":   versa_ecp5_load,
    "ulx3s":        ulx3s_load,
}

# Flash Bistream/Images ----------------------------------------------------------------------------

def arty_flash():
    flash_regions = {
       "build/arty/gateware/top.bin": "0x00000000", # FPGA image:  loaded at startup
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

def minispartan6_flash():
    raise NotImplementedError

def versa_ecp5_flash():
    raise NotImplementedError

def ulx3s_flash():
    raise NotImplementedError

boards_flash_functions = {
    "arty":         arty_flash,
    "minispartan6": minispartan6_flash,
    "versa_ecp5":   versa_ecp5_flash,
    "ulx3s":        ulx3s_flash,
}

# Build / Load / Flash -----------------------------------------------------------------------------

def main():
    description = "Linux on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in socs.keys():
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board", required=True, help="FPGA board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (to SRAM)")
    parser.add_argument("--flash", action="store_true", help="flash bitstream/images (to SPI Flash)")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")
    args = parser.parse_args()

    soc_capabilities = socs_capabilities[args.board]
    soc_kwargs = {}
    if args.board in ["versa_ecp5", "ulx3s"]:
        soc_kwargs["toolchain"] = "trellis"
    soc = SoCLinux(socs[args.board], **soc_kwargs)
    if "spiflash" in soc_capabilities:
        soc.add_spi_flash()
    if "ethernet" in soc_capabilities:
        soc.configure_ethernet(local_ip=args.local_ip, remote_ip=args.remote_ip)
    soc.configure_boot()
    soc.compile_device_tree("arty")

    if args.build:
        builder = Builder(soc, output_dir="build/" + args.board)
        builder.build()

    if args.load:
        boards_load_functions[args.board]()

    if args.flash:
        boards_flash_functions[args.board]()

if __name__ == "__main__":
    main()
