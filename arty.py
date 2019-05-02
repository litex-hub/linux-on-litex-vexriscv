#!/usr/bin/env python3

import argparse

from migen import *

from litex.boards.platforms import arty

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.interconnect import wishbone
from litex.soc.integration.builder import *

from litedram.modules import MT41K128M16
from litedram.phy import s7ddrphy

from liteeth.phy.mii import LiteEthPHYMII
from liteeth.core.mac import LiteEthMAC

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys4x = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys4x_dqs = ClockDomain(reset_less=True)
        self.clock_domains.cd_clk200 = ClockDomain()

        self.submodules.pll = pll = S7PLL(speedgrade=-1)
        self.comb += pll.reset.eq(~platform.request("cpu_reset"))
        pll.register_clkin(platform.request("clk100"), 100e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)
        pll.create_clkout(self.cd_sys4x, 4*sys_clk_freq)
        pll.create_clkout(self.cd_sys4x_dqs, 4*sys_clk_freq, phase=90)
        pll.create_clkout(self.cd_clk200, 200e6)

        self.submodules.idelayctrl = S7IDELAYCTRL(self.cd_clk200)

        eth_clk = Signal()
        self.specials += [
            Instance("BUFR", p_BUFR_DIVIDE="4", i_CE=1, i_CLR=0, i_I=self.cd_sys.clk, o_O=eth_clk),
            Instance("BUFG", i_I=eth_clk, o_O=platform.request("eth_ref_clk")),
        ]

# LinuxSoC -----------------------------------------------------------------------------------------

class Timer(Module, AutoCSR):
    def __init__(self, debug=False):
        self._latch = CSR()
        self._time = CSRStatus(64)
        self._time_cmp = CSRStorage(64, reset=0xffffffffffffffff)
        self.interrupt = Signal()

        # # #

        time = Signal(64)
        self.sync += time.eq(time + 1)
        self.sync += If(self._latch.re, self._time.status.eq(time))

        time_cmp = Signal(64, reset=0xffffffffffffffff)
        self.sync += If(self._latch.re, time_cmp.eq(self._time_cmp.storage))

        self.comb += self.interrupt.eq(time >= time_cmp)


class LinuxSoC(SoCSDRAM):
    csr_map = {
        "ddrphy": 16,
        "timer":  17,
        "ethphy": 18,
        "ethmac": 19
    }
    csr_map.update(SoCSDRAM.csr_map)

    SoCSDRAM.mem_map = {
        "rom":      0x00000000,
        "sram":     0x10000000,
        "mm_ram":   0x20000000,
        "ethmac":   0x30000000,
        "main_ram": 0xc0000000,
        "csr":      0xf0000000,
    }

    def __init__(self, **kwargs):
        platform = arty.Platform()
        sys_clk_freq = int(100e6)
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
                         cpu_type="vexriscv",
                         integrated_rom_size=0x8000,
                         integrated_sram_size=0x8000,
                         **kwargs)
        self.cpu.use_external_variant("VexRiscv.v")

        # crg
        self.submodules.crg = _CRG(platform, sys_clk_freq)
        self.crg.cd_sys.clk.attr.add("keep")
        self.platform.add_period_constraint(self.crg.cd_sys.clk, 1e9/100e6)

        # timer
        self.submodules.timer = Timer()
        self.cpu.cpu_params.update(i_timerInterrupt=self.timer.interrupt)

        # machine mode emulator ram
        self.submodules.mm_ram = wishbone.SRAM(0x10000)
        self.register_mem("mm_ram", self.mem_map["mm_ram"], self.mm_ram.bus, 0x10000)

        # sdram
        self.submodules.ddrphy = s7ddrphy.A7DDRPHY(platform.request("ddram"), sys_clk_freq=sys_clk_freq)
        sdram_module = MT41K128M16(sys_clk_freq, "1:4")
        self.register_sdram(self.ddrphy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings)

        # ethernet
        self.submodules.ethphy = LiteEthPHYMII(self.platform.request("eth_clocks"),
                                               self.platform.request("eth"))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
            interface="wishbone", endianness=self.cpu.endianness)
        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)
        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 1e9/25e6)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 1e9/25e6)
        self.platform.add_false_path_constraints(
            self.crg.cd_sys.clk,
            self.ethphy.crg.cd_eth_rx.clk,
            self.ethphy.crg.cd_eth_tx.clk)

        self.add_constant("REMOTEIP1", 192)
        self.add_constant("REMOTEIP2", 168)
        self.add_constant("REMOTEIP3",   1)
        self.add_constant("REMOTEIP4", 113)
        self.add_constant("NETBOOT_LINUX_VEXRISCV", None)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Arty")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    soc = LinuxSoC(**soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build")
    builder.build()


if __name__ == "__main__":
    main()
