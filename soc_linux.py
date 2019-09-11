#!/usr/bin/env python3

import os

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import mem_decoder

from litex.soc.cores.spi_flash import SpiFlash
from litex.soc.cores.gpio import GPIOOut, GPIOIn
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.xadc import XADC

from litevideo.output import VideoOut

# Helpers ------------------------------------------------------------------------------------------

def platform_request_all(platform, name):
    from litex.build.generic_platform import ConstraintError
    r = []
    while True:
        try:
            r += [platform.request(name, len(r))]
        except ConstraintError:
            break
    if r == []:
        raise ValueError
    return r

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
            soc_cls.__init__(self, cpu_type="vexriscv", cpu_variant=cpu_variant, uart_baudrate=2e6, **kwargs)

            # machine mode emulator ram
            self.submodules.emulator_ram = wishbone.SRAM(0x4000)
            self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

        def add_spi_flash(self):
            # TODO: add spiflash1x support
            spiflash_pads = self.platform.request("spiflash4x")
            self.submodules.spiflash = SpiFlash(
                spiflash_pads,
                dummy=11,
                div=2,
                with_bitbang=True,
                endianness=self.cpu.endianness)
            self.spiflash.add_clk_primitive(self.platform.device)
            self.add_wb_slave(mem_decoder(self.mem_map["spiflash"]), self.spiflash.bus)
            self.add_memory_region("spiflash", self.mem_map["spiflash"] | self.shadow_base, 0x1000000)
            self.add_csr("spiflash")

        def add_leds(self):
            self.submodules.leds = GPIOOut(Cat(platform_request_all(self.platform, "user_led")))
            self.add_csr("leds")

        def add_switches(self):
            self.submodules.switches = GPIOOut(Cat(platform_request_all(self.plarform, "user_sw")))
            self.add_csr("switches")

        def add_spi(self, data_width, spi_clk_freq):
            spi_pads = self.platform.request("spi")
            self.add_csr("spi")
            self.submodules.spi = SPIMaster(spi_pads, data_width, self.clk_freq, spi_clk_freq)

        def add_i2c(self):
            self.submodules.i2c0 = I2CMaster(self.platform.request("i2c", 0))
            self.add_csr("i2c0")

        def add_xadc(self):
            self.submodules.xadc = XADC()
            self.add_csr("xadc")

        def add_framebuffer(self):
            platform = self.platform
            assert platform.device[:4] == "xc7a"
            dram_port = self.sdram.crossbar.get_port(
                mode="read",
                data_width=32,
                clock_domain="pix",
                reverse=True)
            framebuffer = VideoOut(
                device=platform.device,
                pads=platform.request("hdmi_out"),
                dram_port=dram_port)
            self.submodules.framebuffer = framebuffer
            self.add_csr("framebuffer")

            framebuffer.driver.clocking.cd_pix.clk.attr.add("keep")
            framebuffer.driver.clocking.cd_pix5x.clk.attr.add("keep")
            platform.add_period_constraint(framebuffer.driver.clocking.cd_pix.clk, 1e9/74.25e6)
            platform.add_period_constraint(framebuffer.driver.clocking.cd_pix5x.clk, 1e9/(5*74.25e6))
            platform.add_false_path_constraints(
                self.crg.cd_sys.clk,
                framebuffer.driver.clocking.cd_pix.clk,
                framebuffer.driver.clocking.cd_pix5x.clk)

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
            if hasattr(self, "spiflash"):
                self.add_constant("FLASH_BOOT_ADDRESS", 0x00400000)

        def generate_dts(self, board_name):
            json = os.path.join("build", board_name, "csr.json")
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            os.system("./json2dts.py {} > {}".format(json, dts))

        def compile_dts(self, board_name):
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            dtb = os.path.join("buildroot", "rv32.dtb")
            os.system("dtc -O dtb -o {} {}".format(dtb, dts))

    return _SoCLinux(**kwargs)
