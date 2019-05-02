#!/usr/bin/env python3

import argparse

from migen import *
from migen.genlib.io import CRG
from migen.genlib.misc import timeline

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import stream
from litex.soc.interconnect import wishbone
from litex.soc.cores import uart


class SimPins(Pins):
    def __init__(self, n=1):
        Pins.__init__(self, "s "*n)


_io = [
    ("sys_clk", 0, SimPins(1)),
    ("sys_rst", 0, SimPins(1)),
    ("serial", 0,
        Subsignal("source_valid", SimPins()),
        Subsignal("source_ready", SimPins()),
        Subsignal("source_data", SimPins(8)),

        Subsignal("sink_valid", SimPins()),
        Subsignal("sink_ready", SimPins()),
        Subsignal("sink_data", SimPins(8)),
    ),
]


class Platform(SimPlatform):
    default_clk_name = "sys_clk"
    default_clk_period = 1000 # ~ 1MHz

    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

    def do_finalize(self, fragment):
        pass


class Supervisor(Module, AutoCSR):
    def __init__(self):
        self._finish  = CSR()  # controlled from CPU
        self.finish = Signal() # controlled from logic
        self.sync += If(self._finish.re | self.finish, Finish())


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


class LinuxSoC(SoCCore):
    csr_map = {
        "supervisor":    4,
        "timer":         5
    }
    csr_map.update(SoCCore.csr_map)

    SoCCore.mem_map = {
        "sram":     0x80000000,
        "main_ram": 0xc0000000,
        "csr":      0xf0000000,
    }

    def __init__(self, **kwargs):
        platform = Platform()
        sys_clk_freq = int(1e6)
        SoCCore.__init__(self, platform, cpu_type=None, clk_freq=sys_clk_freq,
            with_timer=False, with_uart=False,
            integrated_sram_size=0x10000, # 64KB
            integrated_sram_init=get_mem_data("sram.json", "little"),
            integrated_main_ram_size=0x08000000, # 128MB
            integrated_main_ram_init=get_mem_data("main_ram.json", "little"),
            **kwargs)

        # supervisor
        self.submodules.supervisor = Supervisor()

        # crg
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # serial
        self.submodules.uart_phy = uart.RS232PHYModel(platform.request("serial"))
        self.submodules.uart = uart.UART(self.uart_phy)
        counter = Signal(8)
        self.sync += counter.eq(counter + 1)

        # timer
        self.submodules.timer = Timer()

        # vexriscv
        ibus = wishbone.Interface()
        dbus = wishbone.Interface()
        self.specials += Instance("VexRiscv",
            i_clk=ClockSignal(),
            i_reset=ResetSignal(),

            i_externalResetVector=0x80000000,

            i_timerInterrupt=self.timer.interrupt,
            i_softwareInterrupt=0,
            i_externalInterruptS=0,
            i_externalInterruptArray=0,

            o_iBusWishbone_ADR=ibus.adr,
            o_iBusWishbone_DAT_MOSI=ibus.dat_w,
            o_iBusWishbone_SEL=ibus.sel,
            o_iBusWishbone_CYC=ibus.cyc,
            o_iBusWishbone_STB=ibus.stb,
            o_iBusWishbone_WE=ibus.we,
            o_iBusWishbone_CTI=ibus.cti,
            o_iBusWishbone_BTE=ibus.bte,
            i_iBusWishbone_DAT_MISO=ibus.dat_r,
            i_iBusWishbone_ACK=ibus.ack,
            i_iBusWishbone_ERR=ibus.err,

            o_dBusWishbone_ADR=dbus.adr,
            o_dBusWishbone_DAT_MOSI=dbus.dat_w,
            o_dBusWishbone_SEL=dbus.sel,
            o_dBusWishbone_CYC=dbus.cyc,
            o_dBusWishbone_STB=dbus.stb,
            o_dBusWishbone_WE=dbus.we,
            o_dBusWishbone_CTI=dbus.cti,
            o_dBusWishbone_BTE=dbus.bte,
            i_dBusWishbone_DAT_MISO=dbus.dat_r,
            i_dBusWishbone_ACK=dbus.ack,
            i_dBusWishbone_ERR=dbus.err
        )
        self.add_wb_master(ibus)
        self.add_wb_master(dbus)
        platform.add_source("VexRiscv.v")


def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv Simulation")
    parser.add_argument("--trace", action="store_true", help="enable VCD tracing")
    args = parser.parse_args()

    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    soc = LinuxSoC()
    builder = Builder(soc, output_dir="build", csr_csv="csr.csv")
    builder.build(sim_config=sim_config, trace=args.trace)


if __name__ == "__main__":
    main()
