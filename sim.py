#!/usr/bin/env python3

import argparse

from migen import *
from migen.genlib.io import CRG

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
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
    def __init__(self, platform):
        self.bus = bus = wishbone.Interface()

        # # #

        # uart
        self.submodules.uart = uart.RS232PHYModel(platform.request("serial"))
        self.comb += [
            If(bus.stb & bus.cyc,
                # uart
                If(bus.adr == 0xfffffff8//4,
                    If(bus.we,
                        self.uart.sink.valid.eq(1),
                        self.uart.sink.data.eq(bus.dat_w),
                        bus.ack.eq(1)
                    )
                )
            )
        ]

        # simulation end
        finish = Signal()
        self.comb += [
            If(bus.stb & bus.cyc,
                # simulation end
                If(bus.adr == 0xfffffffc//4,
                    If(bus.we,
                        finish.eq(1),
                        bus.ack.eq(1),
                    )
                )
            )
        ]
        self.sync += If(finish, Finish())


class SimSoC(SoCCore):
    mem_map = {
        "periphs": 0x70000000,  # (shadow @0xf0000000)
    }
    mem_map.update(SoCCore.mem_map)

    def __init__(self, **kwargs):
        platform = Platform()
        sys_clk_freq = int(1e6)
        SoCCore.__init__(self, platform, cpu_type=None, clk_freq=sys_clk_freq,
            ident="LiteX Linux VexRiscv Simulation", ident_version=True,
            with_timer=False, with_uart=False,
            **kwargs)

        # crg
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # periphs
        self.submodules.periphs = VexRiscvPeriphs(platform)
        self.add_wb_slave(mem_decoder(self.mem_map["periphs"]), self.periphs.bus)
        self.add_memory_region("periphs", self.mem_map["periphs"] | self.shadow_base, 0x10000000)

        # vexriscv
        ibus = wishbone.Interface()
        dbus = wishbone.Interface()
        self.specials += Instance("VexRiscv",
            i_clk=ClockSignal(),
            i_reset=ResetSignal(),

            i_externalResetVector=0x80000000,

            i_timerInterrupt=0,
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
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    builder_args(parser)
    soc_core_args(parser)
    parser.add_argument("--threads", default=1,
                        help="set number of threads (default=1)")
    parser.add_argument("--ram-init", default=None,
                        help="ram_init file")
    parser.add_argument("--trace", action="store_true",
                        help="enable VCD tracing")
    args = parser.parse_args()

    soc_kwargs = soc_core_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    cpu_endianness = "little"

    soc_kwargs["integrated_rom_size"] = 0x8000 # 32KB
    soc_kwargs["integrated_rom_init"] = get_mem_data("bootloader.bin", "little")
    soc_kwargs["integrated_sram_size"] = 0x8000 # 32KB
    soc_kwargs["integrated_main_ram_size"] = 0x10000000 # 256 MB
    soc_kwargs["integrated_main_ram_init"] = get_mem_data("main_ram_init.json", "little")

    builder_kwargs["output_dir"] = "build"

    soc = SimSoC(**soc_kwargs)
    builder = Builder(soc, **builder_kwargs)
    builder.build(threads=args.threads, sim_config=sim_config, trace=args.trace)


if __name__ == "__main__":
    main()
