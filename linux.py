#!/usr/bin/env python3

import argparse

from migen import *
from migen.genlib.io import CRG
from migen.genlib.misc import timeline

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

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


class VexRiscvPeriphs(Module):
    def __init__(self, platform, debug=False):
        self.bus = bus = wishbone.Interface()
        self.timer_interrupt = Signal()

        # # #

        self.sync += bus.ack.eq(0)

        # timer
        time = Signal(64)
        time_cmp = Signal(64, reset=0xffffffffffffffff)
        self.sync += [
            time.eq(time + 1),
            If(bus.stb & bus.cyc,
                If(bus.adr == 0xffffffe0//4,
                    If(~bus.we,
                        bus.dat_r.eq(time[:32]),
                        bus.ack.eq(1)
                    )
                ).Elif(bus.adr == 0xffffffe4//4,
                    If(~bus.we,
                        bus.dat_r.eq(time[32:]),
                        bus.ack.eq(1)
                    )
                ).Elif(bus.adr == 0xffffffe8//4,
                    If(bus.we,
                        time_cmp.eq(bus.dat_w[:32]),
                    ).Else(
                        bus.dat_r.eq(time_cmp[:32])
                    ),
                    bus.ack.eq(1)
                ).Elif(bus.adr == 0xffffffec//4,
                    If(bus.we,
                        time_cmp[32:].eq(bus.dat_w),
                    ).Else(
                        bus.dat_r.eq(time_cmp[32:]),
                    ),
                    bus.ack.eq(1)
                )
            )
        ]
        self.comb += self.timer_interrupt.eq(time >= time_cmp)

        # uart
        uart_phy = uart.RS232PHYModel(platform.request("serial"))
        uart_tx_fifo = stream.SyncFIFO([("data", 8)], 8)
        uart_rx_fifo = stream.SyncFIFO([("data", 8)], 8)
        self.submodules += uart_phy, uart_tx_fifo, uart_rx_fifo
        self.comb += uart_phy.source.connect(uart_rx_fifo.sink)
        self.comb += uart_tx_fifo.source.connect(uart_phy.sink)
        self.sync += [
            uart_tx_fifo.sink.valid.eq(0),
            uart_rx_fifo.source.ready.eq(0),
            If(bus.stb & bus.cyc,
                If(bus.adr == 0xfffffff8//4,
                    If(bus.we,
                        uart_tx_fifo.sink.valid.eq(~bus.ack),
                        uart_tx_fifo.sink.data.eq(bus.dat_w),
                        bus.ack.eq(1)
                    ).Else(
                        If(uart_rx_fifo.source.valid,
                            bus.dat_r.eq(uart_rx_fifo.source.data),
                            uart_rx_fifo.source.ready.eq(~bus.ack)
                        ).Else(
                            bus.dat_r.eq(0xffffffff),
                        ),
                        bus.ack.eq(1)
                    )
                )
            )
        ]

        bus_stb_d = Signal()
        bus_cyc_d = Signal()
        self.sync += bus_stb_d.eq(bus.stb)
        self.sync += bus_cyc_d.eq(bus.cyc)

        # simulation end
        finish = Signal()
        self.comb += If(bus.stb & bus_stb_d & bus.cyc & bus_cyc_d & ~bus.ack, finish.eq(1))
        self.sync += timeline(finish, [(100, [Finish()])])

        # debug
        if debug:
            timer_interrupt_d = Signal()
            self.sync += [
                timer_interrupt_d.eq(self.timer_interrupt),
                If(self.timer_interrupt & ~timer_interrupt_d,
                    Display("[%016x]: timer interrupt, time_cmp: %016x", time, time_cmp)
                )
            ]

            bus_adr_bytes = Signal(32)
            self.comb += bus_adr_bytes.eq(bus.adr << 2)
            self.sync += [
                If(bus_stb_d & bus_cyc_d & bus.ack,
                    If(bus.we,
                        Display("[%016x]: write: 0x%08x@0x%08x acked:%d", time, bus.dat_w, bus_adr_bytes, bus.ack)
                    ).Else(
                        Display("[%016x]: read:  0x%08x@0x%08x acked:%d", time, bus.dat_r, bus_adr_bytes, bus.ack)
                    )
                )
            ]


class LinuxSoC(SoCCore):
    SoCCore.mem_map = {
        "sram":     0x80000000,
        "main_ram": 0xc0000000,
        "periphs":  0xf0000000,
        "csr":      0x10000000, # not used
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

        # crg
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # periphs
        self.submodules.periphs = VexRiscvPeriphs(platform, debug=False)
        self.add_wb_slave(mem_decoder(self.mem_map["periphs"]), self.periphs.bus)
        self.add_memory_region("periphs", self.mem_map["periphs"], 0x10000000)

        # vexriscv
        ibus = wishbone.Interface()
        dbus = wishbone.Interface()
        self.specials += Instance("VexRiscv",
            i_clk=ClockSignal(),
            i_reset=ResetSignal(),

            i_externalResetVector=0x80000000,

            i_timerInterrupt=self.periphs.timer_interrupt,
            i_externalInterrupt=0,
            i_softwareInterrupt=0,
            i_externalInterruptS=0,

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
    builder = Builder(soc, output_dir="build")
    builder.build(sim_config=sim_config, trace=args.trace)


if __name__ == "__main__":
    main()
