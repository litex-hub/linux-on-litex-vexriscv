#!/usr/bin/env python3

#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2024, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import json
import argparse

from migen import *

from litex.gen import *

from litex.build.generic_platform import *
from litex.build.sim              import SimPlatform
from litex.build.sim.config       import SimConfig
from litex.build.sim.verilator    import verilator_build_args, verilator_build_argdict

from litex.soc.interconnect.csr       import *
from litex.soc.integration.soc_core   import *
from litex.soc.integration.builder    import *
from litex.soc.interconnect           import wishbone
from litex.soc.cores.cpu.vexriscv_smp import VexRiscvSMP

from litedram import modules as litedram_modules
from litedram.phy.model       import SDRAMPHYModel
from litex.tools.litex_sim    import sdram_module_nphases, get_sdram_phy_settings
from litedram.core.controller import ControllerSettings

from liteeth.phy.model import LiteEthPHYModel
from liteeth.mac       import LiteEthMAC

from litex.tools.litex_json2dts_linux import generate_dts

# IOs ----------------------------------------------------------------------------------------------

_io = [
    # Clk / Rst.
    ("sys_clk", 0, Pins(1)),
    ("sys_rst", 0, Pins(1)),

    # Serial.
    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),

        Subsignal("sink_valid", Pins(1)),
        Subsignal("sink_ready", Pins(1)),
        Subsignal("sink_data",  Pins(8)),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(SimPlatform):
    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

# Supervisor ---------------------------------------------------------------------------------------

class Supervisor(LiteXModule):
    def __init__(self):
        self._finish = CSR()    # Controlled from CPU.
        self.finish  = Signal() # Controlled from logic.
        self.sync += If(self._finish.re | self.finish, Finish())

# SoCLinux -----------------------------------------------------------------------------------------

class SoCLinux(SoCCore):
    def __init__(self, sys_clk_freq=int(100e6),
        init_memories    = False,
        sdram_module     = "MT48LC16M16",
        sdram_data_width = 32,
        sdram_verbosity  = 0
    ):
        # Platform ---------------------------------------------------------------------------------
        platform     = Platform()
        self.comb += platform.trace.eq(1)

        # RAM Init ---------------------------------------------------------------------------------
        ram_init = []
        if init_memories:
            ram_init = get_mem_data("images/boot.json", endianness="little", offset=0x40000000)

        # CRG --------------------------------------------------------------------------------------
        self.crg = CRG(platform.request("sys_clk"))

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            cpu_type            = "vexriscv_smp",
            cpu_variant         = "linux",
            integrated_rom_size = 0x10000,
            uart_name           = "sim",
        )
        self.add_config("DISABLE_DELAYS")

        # Boot from OpenSBI.
        self.add_constant("ROM_BOOT_ADDRESS", self.bus.regions["opensbi"].origin)

        # Supervisor -------------------------------------------------------------------------------
        self.supervisor = Supervisor()

        # SDRAM ------------------------------------------------------------------------------------
        sdram_clk_freq   = int(100e6) # FIXME: use 100MHz timings
        sdram_module_cls = getattr(litedram_modules, sdram_module)
        sdram_rate       = "1:{}".format(sdram_module_nphases[sdram_module_cls.memtype])
        sdram_module     = sdram_module_cls(sdram_clk_freq, sdram_rate)
        phy_settings     = get_sdram_phy_settings(
            memtype    = sdram_module.memtype,
            data_width = sdram_data_width,
            clk_freq   = sdram_clk_freq,
        )
        self.sdrphy = SDRAMPHYModel(
            module    = sdram_module,
            settings  = phy_settings,
            clk_freq  = sdram_clk_freq,
            verbosity = sdram_verbosity,
            init      = ram_init,
        )
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = sdram_module,
            l2_cache_size = 0,
        )
        self.add_constant("SDRAM_TEST_DISABLE") # Skip SDRAM test to avoid corrupting pre-initialized contents.

    def generate_dts(self, board_name):
        json_src = os.path.join("build", board_name, "csr.json")
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        with open(json_src) as json_file, open(dts, "w") as dts_file:
            dts_content = generate_dts(json.load(json_file))
            dts_file.write(dts_content)

    def compile_dts(self, board_name):
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        dtb = os.path.join("images", "rv32.dtb")
        os.system("dtc -O dtb -o {} {}".format(dtb, dts))

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv Simulation.")
    parser.add_argument("--with-sdram",       action="store_true",   help="Enable SDRAM support.")
    parser.add_argument("--sdram-module",     default="MT48LC16M16", help="Select SDRAM chip.")
    parser.add_argument("--sdram-data-width", default=32,            help="Set SDRAM chip data width.")
    parser.add_argument("--sdram-verbosity",  default=0,             help="Set SDRAM checker verbosity.")
    VexRiscvSMP.args_fill(parser)
    verilator_build_args(parser)
    args = parser.parse_args()

    VexRiscvSMP.args_read(args)
    verilator_build_kwargs = verilator_build_argdict(args)
    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    for i in range(2):
        prepare = (i == 0)
        run     = (i == 1)
        soc = SoCLinux(
            init_memories    = run,
            sdram_module     = args.sdram_module,
            sdram_data_width = int(args.sdram_data_width),
            sdram_verbosity  = int(args.sdram_verbosity)
        )
        board_name = "sim"
        build_dir  = os.path.join("build", board_name)
        builder = Builder(soc, output_dir=build_dir,
            compile_gateware = run,
            csr_json         = os.path.join(build_dir, "csr.json"))
        builder.build(sim_config=sim_config, run=run, **verilator_build_kwargs)
        if prepare:
            soc.generate_dts(board_name)
            soc.compile_dts(board_name)

if __name__ == "__main__":
    main()
