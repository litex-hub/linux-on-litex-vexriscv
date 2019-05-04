#!/usr/bin/env python3

import argparse

from migen import *

from litex.boards.platforms import versa_ecp5

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.interconnect import wishbone
from litex.soc.integration.builder import *

from litedram.modules import MT41K64M16
from litedram.phy import ECP5DDRPHY

from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII
from liteeth.core.mac import LiteEthMAC

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_init = ClockDomain()
        self.clock_domains.cd_por = ClockDomain(reset_less=True)
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_sys2x = ClockDomain()
        self.clock_domains.cd_sys2x_i = ClockDomain(reset_less=True)

        # # #

        self.stop = Signal()

        # clk / rst
        clk100 = platform.request("clk100")
        rst_n = platform.request("rst_n")
        platform.add_period_constraint(clk100, 10.0)

        # power on reset
        por_count = Signal(16, reset=2**16-1)
        por_done = Signal()
        self.comb += self.cd_por.clk.eq(ClockSignal())
        self.comb += por_done.eq(por_count == 0)
        self.sync.por += If(~por_done, por_count.eq(por_count - 1))

        # pll
        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk100, 100e6)
        pll.create_clkout(self.cd_sys2x_i, 2*sys_clk_freq)
        pll.create_clkout(self.cd_init, 25e6)
        self.specials += [
            Instance("ECLKSYNCB",
                i_ECLKI=self.cd_sys2x_i.clk,
                i_STOP=self.stop,
                o_ECLKO=self.cd_sys2x.clk),
            Instance("CLKDIVF",
                p_DIV="2.0",
                i_ALIGNWD=0,
                i_CLKI=self.cd_sys2x.clk,
                i_RST=self.cd_sys2x.rst,
                o_CDIVX=self.cd_sys.clk),
            AsyncResetSynchronizer(self.cd_init, ~por_done | ~pll.locked | ~rst_n),
            AsyncResetSynchronizer(self.cd_sys, ~por_done | ~pll.locked | ~rst_n)
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
        platform = versa_ecp5.Platform(toolchain="trellis")
        sys_clk_freq = int(75e6)
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
        self.submodules.mm_ram = wishbone.SRAM(0x8000)
        self.register_mem("mm_ram", self.mem_map["mm_ram"], self.mm_ram.bus, 0x8000)

        # sdram
        self.submodules.ddrphy = ECP5DDRPHY(
            platform.request("ddram"),
            sys_clk_freq=sys_clk_freq)
        self.comb += self.crg.stop.eq(self.ddrphy.init.stop)
        sdram_module = MT41K64M16(sys_clk_freq, "1:2")
        self.register_sdram(self.ddrphy,
            sdram_module.geom_settings,
            sdram_module.timing_settings)

        # ethernet
        eth_port = 0
        self.submodules.ethphy = LiteEthPHYRGMII(
            self.platform.request("eth_clocks", eth_port),
            self.platform.request("eth", eth_port))
        self.submodules.ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
            interface="wishbone", endianness=self.cpu.endianness)

        self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
        self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)
        self.ethphy.crg.cd_eth_rx.clk.attr.add("keep")
        self.ethphy.crg.cd_eth_tx.clk.attr.add("keep")
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_rx.clk, 1e9/125e6)
        self.platform.add_period_constraint(self.ethphy.crg.cd_eth_tx.clk, 1e9/125e6)

        self.add_constant("NETBOOT_LINUX_VEXRISCV", None)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="LiteX SoC on Versa ECP5")
    builder_args(parser)
    soc_sdram_args(parser)
    args = parser.parse_args()

    soc = LinuxSoC(**soc_sdram_argdict(args))
    builder = Builder(soc, output_dir="build")
    builder.build(toolchain_path="/usr/share/trellis")


if __name__ == "__main__":
    main()
