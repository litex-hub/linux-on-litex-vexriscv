#!/usr/bin/env python3

import argparse

from migen import *
from migen.genlib.io import CRG

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
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


class SimSoC(SoCCore):
    def __init__(self, **kwargs):
        platform = Platform()
        sys_clk_freq = int(1e6)
        SoCCore.__init__(self, platform, cpu_type=None, clk_freq=sys_clk_freq,
            ident="LiteX Linux VexRiscvSimulation", ident_version=True,
            with_timer=False, with_uart=False,
            **kwargs)

        # crg
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # serial
        self.submodules.uart_phy = uart.RS232PHYModel(platform.request("serial"))
        self.submodules.uart = uart.UART(self.uart_phy)

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

    soc_kwargs["integrated_main_ram_size"] = 0x10000000 # 256 MB
    if args.ram_init is not None:
        soc_kwargs["integrated_main_ram_init"] = get_mem_data(args.ram_init, cpu_endianness)

    soc = SimSoC(**soc_kwargs)
    builder = Builder(soc, **builder_kwargs)
    builder.build(threads=args.threads, sim_config=sim_config, trace=args.trace)


if __name__ == "__main__":
    main()
