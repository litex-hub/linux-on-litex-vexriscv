#!/usr/bin/env python3

#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2021, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import json
import argparse

from litex.soc.cores.cpu import VexRiscvSMP
from migen import *

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.interconnect.csr import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.interconnect import wishbone

from litedram import modules as litedram_modules
from litedram.phy.model import SDRAMPHYModel
from litex.tools.litex_sim import sdram_module_nphases, get_sdram_phy_settings
from litedram.core.controller import ControllerSettings

from liteeth.phy.model import LiteEthPHYModel
from liteeth.mac import LiteEthMAC

from litex.tools.litex_json2dts import generate_dts

# IOs ----------------------------------------------------------------------------------------------

_io = [
    ("sys_clk", 0, Pins(1)),
    ("sys_rst", 0, Pins(1)),
    ("serial", 0,
        Subsignal("source_valid", Pins(1)),
        Subsignal("source_ready", Pins(1)),
        Subsignal("source_data",  Pins(8)),

        Subsignal("sink_valid", Pins(1)),
        Subsignal("sink_ready", Pins(1)),
        Subsignal("sink_data",  Pins(8)),
    ),
    ("eth_clocks", 0,
        Subsignal("none", Pins()),
    ),
    ("eth", 0,
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

class Supervisor(Module, AutoCSR):
    def __init__(self):
        self._finish  = CSR()  # controlled from CPU
        self.finish = Signal() # controlled from logic
        self.sync += If(self._finish.re | self.finish, Finish())

# SoCLinux -----------------------------------------------------------------------------------------

class SoCLinux(SoCCore):
    csr_map = {**SoCCore.csr_map, **{
        "ctrl":   0,
        "uart":   2,
        "timer0": 3,
    }}
    interrupt_map = {**SoCCore.interrupt_map, **{
        "uart":   0,
        "timer0": 1,
    }}
    mem_map = {**SoCCore.mem_map, **{
        "ethmac":   0xb0000000,
        "spiflash": 0xd0000000,
        "csr":      0xf0000000,
    }}

    def __init__(self,
        init_memories    = False,
        sdram_module     = "MT48LC16M16",
        sdram_data_width = 32,
        sdram_verbosity  = 0,
        with_ethernet    = False):
        platform     = Platform()
        sys_clk_freq = int(100e6)

        ram_init = []
        if init_memories:
            ram_init = get_mem_data({
                "images/Image":       "0x00000000",
                "images/rv32.dtb":    "0x00ef0000",
                "images/rootfs.cpio": "0x01000000",
                "images/opensbi.bin": "0x00f00000"
            }, "little")

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # SoCCore ----------------------------------------------------------------------------------
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            cpu_type                 = "vexriscv_smp",
            cpu_variant              = "linux",
            integrated_rom_size      = 0x8000,
            uart_name                = "sim")
        self.add_config("DISABLE_DELAYS")

        # Add linker region for OpenSBI
        self.add_memory_region("opensbi", self.mem_map["main_ram"] + 0x00f00000, 0x80000, type="cached+linker")
        self.add_constant("ROM_BOOT_ADDRESS", self.bus.regions["opensbi"].origin)

        # Supervisor -------------------------------------------------------------------------------
        self.submodules.supervisor = Supervisor()
        self.add_csr("supervisor")

        # SDRAM ------------------------------------------------------------------------------------
        sdram_clk_freq   = int(100e6) # FIXME: use 100MHz timings
        sdram_module_cls = getattr(litedram_modules, sdram_module)
        sdram_rate       = "1:{}".format(sdram_module_nphases[sdram_module_cls.memtype])
        sdram_module     = sdram_module_cls(sdram_clk_freq, sdram_rate)
        phy_settings     = get_sdram_phy_settings(
            memtype    = sdram_module.memtype,
            data_width = sdram_data_width,
            clk_freq   = sdram_clk_freq)
        self.submodules.sdrphy = SDRAMPHYModel(
            module    = sdram_module,
            settings  = phy_settings,
            clk_freq  = sdram_clk_freq,
            verbosity = sdram_verbosity,
            init      = ram_init)
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = sdram_module,
            origin        = self.mem_map["main_ram"],
            l2_cache_size = 0)
        self.add_constant("SDRAM_TEST_DISABLE") # Skip SDRAM test to avoid corrupting pre-initialized contents.

        # Ethernet ---------------------------------------------------------------------------------
        if with_ethernet:
            # eth phy
            self.submodules.ethphy = LiteEthPHYModel(self.platform.request("eth", 0))
            self.add_csr("ethphy")
            # eth mac
            ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
                interface="wishbone", endianness=self.cpu.endianness)
            self.submodules.ethmac = ethmac
            self.add_memory_region("ethmac", self.mem_map["ethmac"], 0x2000, type="io")
            self.add_wb_slave(self.mem_map["ethmac"], self.ethmac.bus)
            self.add_csr("ethmac")
            self.add_interrupt("ethmac")

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
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv Simulation")
    parser.add_argument("--with-sdram",           action="store_true",     help="enable SDRAM support")
    parser.add_argument("--sdram-module",         default="MT48LC16M16",   help="Select SDRAM chip")
    parser.add_argument("--sdram-data-width",     default=32,              help="Set SDRAM chip data width")
    parser.add_argument("--sdram-verbosity",      default=0,               help="Set SDRAM checker verbosity")
    parser.add_argument("--with-ethernet",        action="store_true",     help="enable Ethernet support")
    parser.add_argument("--local-ip",             default="192.168.1.50",  help="Local IP address of SoC (default=192.168.1.50)")
    parser.add_argument("--remote-ip",            default="192.168.1.100", help="Remote IP address of TFTP server (default=192.168.1.100)")
    parser.add_argument("--trace",                action="store_true",     help="enable VCD tracing")
    parser.add_argument("--trace-start",          default=0,               help="cycle to start VCD tracing")
    parser.add_argument("--trace-end",            default=-1,              help="cycle to end VCD tracing")
    parser.add_argument("--opt-level",            default="O3",            help="compilation optimization level")
    VexRiscvSMP.args_fill(parser)
    args = parser.parse_args()

    VexRiscvSMP.args_read(args)
    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")
    if args.with_ethernet:
        sim_config.add_module("ethernet", "eth", args={"interface": "tap0", "ip": args.remote_ip})

    for i in range(2):
        soc = SoCLinux( i!=0,
            sdram_module     = args.sdram_module,
            sdram_data_width = int(args.sdram_data_width),
            sdram_verbosity  = int(args.sdram_verbosity),
            with_ethernet    = args.with_ethernet)
        if args.with_ethernet:
            for i in range(4):
                soc.add_constant("LOCALIP{}".format(i+1), int(args.local_ip.split(".")[i]))
            for i in range(4):
                soc.add_constant("REMOTEIP{}".format(i+1), int(args.remote_ip.split(".")[i]))
        board_name = "sim"
        build_dir  = os.path.join("build", board_name)
        builder = Builder(soc, output_dir=build_dir,
            compile_gateware = i != 0 ,
            csr_json         = os.path.join(build_dir, "csr.json"))
        builder.build(sim_config=sim_config,
            run         = i != 0,
            opt_level   = args.opt_level,
            trace       = args.trace,
            trace_start = int(args.trace_start),
            trace_end   = int(args.trace_end))
        if i == 0:
            soc.generate_dts(board_name)
            soc.compile_dts(board_name)


if __name__ == "__main__":
    main()
