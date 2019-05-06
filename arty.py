#!/usr/bin/env python3

import argparse
import os

from migen import *

from litex.boards.targets import arty

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.builder import Builder

from litex.soc.cores.spi_flash import SpiFlash

# LinuxSoC -----------------------------------------------------------------------------------------

class LinuxSoC(arty.EthernetSoC):
    csr_map = {
        "ddrphy": 16,
        "cpu":    17,
        "ethphy": 18,
        "ethmac": 19
    }
    csr_map.update(arty.EthernetSoC.csr_map)

    arty.EthernetSoC.mem_map = {
        "rom":          0x00000000,
        "sram":         0x10000000,
        "emulator_ram": 0x20000000,
        "ethmac":       0x30000000,
        "spiflash":     0x50000000,
        "main_ram":     0xc0000000,
        "csr":          0xf0000000,
    }

    def __init__(self, local_ip="192.168.1.50", remote_ip="192.168.1.100"):
        arty.EthernetSoC.__init__(self, cpu_type="vexriscv", cpu_variant="linux")
        self.cpu.use_external_variant("VexRiscv.v")
        self.add_constant("NETBOOT_LINUX_VEXRISCV", None)

        # machine mode emulator ram
        self.submodules.emulator_ram = wishbone.SRAM(0x4000)
        self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

        local_ip = local_ip.split(".")
        remote_ip = remote_ip.split(".")

        self.add_constant("LOCALIP1", int(local_ip[0]))
        self.add_constant("LOCALIP2", int(local_ip[1]))
        self.add_constant("LOCALIP3", int(local_ip[2]))
        self.add_constant("LOCALIP4", int(local_ip[3]))

        self.add_constant("REMOTEIP1", int(remote_ip[0]))
        self.add_constant("REMOTEIP2", int(remote_ip[1]))
        self.add_constant("REMOTEIP3", int(remote_ip[2]))
        self.add_constant("REMOTEIP4", int(remote_ip[3]))

          # spiflash
        spiflash_pads = self.platform.request("spiflash4x")
        spiflash_pads.clk = Signal()
        self.specials += Instance("STARTUPE2",
            i_CLK=0,
            i_GSR=0,
            i_GTS=0,
            i_KEYCLEARB=0,
            i_PACK=0,
            i_USRCCLKO=spiflash_pads.clk,
            i_USRCCLKTS=0,
            i_USRDONEO=1,
            i_USRDONETS=1)

        self.submodules.spiflash = SpiFlash(
                spiflash_pads,
                dummy=11,
                div=2,
                endianness=self.cpu.endianness)
        self.add_wb_slave(mem_decoder(self.mem_map["spiflash"]), self.spiflash.bus)
        self.add_memory_region("spiflash", self.mem_map["spiflash"] | self.shadow_base, 0x1000000)

        self.add_constant("FLASHBOOT_LINUX_VEXRISCV", None)
        self.add_constant("FLASH_BOOT_ADDRESS", None)

# Build / Load / Flash -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    parser.add_argument("--flash", action="store_true", help="flash bitstream (SPI Flash)")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")

    args = parser.parse_args()

    if args.build:
        soc = LinuxSoC(local_ip=args.local_ip, remote_ip=args.remote_ip)
        builder = Builder(soc, output_dir="build_arty")
        builder.build()

    if args.load:
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg")
        prog.load_bitstream("build/gateware/top.bit")

    if args.flash:
        flash_regions = {
            "build/gateware/top.bin": "0x00000000", # FPGA image: automatically loaded at startup
            "binaries/Image":         "0x00400000", # Linux Image: copied to 0xc0000000 by bios
            "binaries/rootfs.cpio":   "0x00800000", # File System: copied to 0xc2000000 by bios
            "binaries/rv32.dtb":      "0x00f00000", # Device tree: copied to 0xc3000000 by bios
            "emulator/emulator.bin":  "0x00f80000", # MM Emulator: copied to 0x20000000 by bios
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
