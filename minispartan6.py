#!/usr/bin/env python3

import argparse
import os

from migen import *

from litex.boards.targets import minispartan6

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.builder import Builder

# LinuxSoC -----------------------------------------------------------------------------------------

class LinuxSoC(minispartan6.BaseSoC):
    csr_map = {
        "ddrphy": 16,
        "cpu":    17,
    }
    csr_map.update(minispartan6.BaseSoC.csr_map)

    minispartan6.BaseSoC.mem_map = {
        "rom":          0x00000000,
        "sram":         0x10000000,
        "emulator_ram": 0x20000000,
        "spiflash":     0x50000000,
        "main_ram":     0xc0000000,
        "csr":          0xf0000000,
    }

    def __init__(self):
        minispartan6.BaseSoC.__init__(self, cpu_type="vexriscv", cpu_variant="linux", uart_baudrate=3e6)
        self.cpu.use_external_variant("VexRiscv.v")

        # machine mode emulator ram
        self.submodules.emulator_ram = wishbone.SRAM(0x4000)
        self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv with ULX3S board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    args = parser.parse_args()

    if args.load:
        print("Compile board device tree...")
        os.system("dtc -O dtb -o binaries/rv32.dtb buildroot/board/litex_vexriscv/litex_vexriscv_minispartan6.dts")

    if args.build:
        soc = LinuxSoC()
        builder = Builder(soc, output_dir="build_minispartan6")
        builder.build()

    if args.load:
        os.system("xc3sprog -c ftdi build_minispartan6/gateware/top.bit")

if __name__ == "__main__":
    main()
