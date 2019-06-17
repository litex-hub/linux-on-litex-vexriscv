#!/usr/bin/env python3

import os

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import mem_decoder

from litex.soc.cores.spi_flash import SpiFlash

# SoCLinux -----------------------------------------------------------------------------------------

def SoCLinux(soc_cls, **kwargs):
    class _SoCLinux(soc_cls):
        soc_cls.csr_map.update({
            "ctrl":       0,
            "uart":       2,
            "timer0":     3,
        })
        soc_cls.interrupt_map.update({
            "uart":       0,
            "timer0":     1,
        })
        soc_cls.mem_map = {
            "rom":          0x00000000,
            "sram":         0x10000000,
            "emulator_ram": 0x20000000,
            "ethmac":       0x30000000,
            "spiflash":     0x50000000,
            "main_ram":     0xc0000000,
            "csr":          0xf0000000,
        }

        def __init__(self, cpu_variant="linux", **kwargs):
            soc_cls.__init__(self, cpu_type="vexriscv", cpu_variant=cpu_variant, **kwargs)

            # machine mode emulator ram
            self.submodules.emulator_ram = wishbone.SRAM(0x4000)
            self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

        def add_spi_flash(self):
            # FIXME: only support 7-series for now
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

        def configure_ethernet(self, local_ip, remote_ip):
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

        def configure_boot(self):
            self.add_constant("NETBOOT_LINUX_VEXRISCV", None)
            if hasattr(self, "spiflash"):
                self.add_constant("FLASHBOOT_LINUX_VEXRISCV", None)
                self.add_constant("FLASH_BOOT_ADDRESS", None)

        def compile_device_tree(self, name=""):
            if name != "":
                name = "_" + name
            print(name)
            os.system("dtc -O dtb -o buildroot/rv32.dtb buildroot/board/litex_vexriscv/litex_vexriscv{}.dts".format(name))

    return _SoCLinux(**kwargs)
