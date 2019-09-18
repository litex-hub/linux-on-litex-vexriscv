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

from liteeth.common import convert_ip
from liteeth.phy.model import LiteEthPHYModel
from liteeth.core.mac import LiteEthMAC


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
    ("eth_clocks", 0,
        Subsignal("none", SimPins()),
    ),
    ("eth", 0,
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
    default_clk_period = 1e9/1e9 # ~ 1MHz

    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

    def do_finalize(self, fragment):
        pass


class Supervisor(Module, AutoCSR):
    def __init__(self):
        self._finish  = CSR()  # controlled from CPU
        self.finish = Signal() # controlled from logic
        self.sync += If(self._finish.re | self.finish, Finish())


class SoCLinux(SoCCore):
    SoCCore.csr_map.update({
        "ctrl":       0,
        "uart":       2,
        "timer0":     3,
    })
    SoCCore.interrupt_map.update({
        "uart":       0,
        "timer0":     1,
    })
    SoCCore.mem_map = {
        "rom":          0x00000000,
        "sram":         0x10000000,
        "emulator_ram": 0x20000000,
        "ethmac":       0x30000000,
        "main_ram":     0xC0000000,
        "csr":          0xf0000000,
    }

    def __init__(self, init_memories=False, with_ethernet=False):
        platform = Platform()
        sys_clk_freq = int(1e6)
        SoCCore.__init__(self, platform, clk_freq=sys_clk_freq,
            cpu_type="vexriscv", cpu_variant="linux",
            with_uart=False,
            integrated_rom_size=0x8000,
            integrated_main_ram_size=0x02000000, # 32MB
            integrated_main_ram_init=get_mem_data({
                "buildroot/Image":         "0x00000000",
                "buildroot/rootfs.cpio":   "0x00800000",
                "buildroot/rv32.dtb":      "0x01000000"
                }, "little") if init_memories else [])
        self.add_constant("SIM", None)

        # supervisor
        self.submodules.supervisor = Supervisor()
        self.add_csr("supervisor")

        # crg
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # machine mode emulator ram
        emulator_rom = get_mem_data("emulator/emulator.bin", "little") if init_memories else []
        self.submodules.emulator_ram = wishbone.SRAM(0x4000, init=emulator_rom)
        self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)
        self.add_constant("ROM_BOOT_ADDRESS",self.mem_map["emulator_ram"])

        # serial
        self.submodules.uart_phy = uart.RS232PHYModel(platform.request("serial"))
        self.submodules.uart = uart.UART(self.uart_phy)
        self.add_csr("uart", allow_user_defined=True)
        self.add_interrupt("uart", allow_user_defined=True)

        # ethernet
        if with_ethernet:
            # eth phy
            self.submodules.ethphy = LiteEthPHYModel(self.platform.request("eth", 0))
            self.add_csr("ethphy")
            # eth mac
            ethmac = LiteEthMAC(phy=self.ethphy, dw=32,
                interface="wishbone", endianness=self.cpu.endianness)
            self.submodules.ethmac = ethmac
            self.add_wb_slave(mem_decoder(self.mem_map["ethmac"]), self.ethmac.bus)
            self.add_memory_region("ethmac", self.mem_map["ethmac"] | self.shadow_base, 0x2000)
            self.add_csr("ethmac")
            self.add_interrupt("ethmac")

    def generate_dts(self, board_name):
        json = os.path.join("build", board_name, "csr.json")
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        os.system("./json2dts.py {} > {}".format(json, dts))

    def compile_dts(self, board_name):
        dts = os.path.join("build", board_name, "{}.dts".format(board_name))
        dtb = os.path.join("buildroot", "rv32.dtb")
        os.system("dtc -O dtb -o {} {}".format(dtb, dts))

    def compile_emulator(self, board_name):
        os.environ["BOARD"] = board_name
        os.system("cd emulator && make")

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv Simulation")
    parser.add_argument("--with-ethernet", action="store_true",
                        help="enable Ethernet support")
    parser.add_argument("--trace", action="store_true", help="enable VCD tracing")
    parser.add_argument("--trace-start", default=0,
                        help="cycle to start VCD tracing")
    parser.add_argument("--trace-end", default=-1,
                        help="cycle to end VCD tracing")
    parser.add_argument("--opt-level", default="O3",
                        help="compilation optimization level")
    args = parser.parse_args()

    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")
    if args.with_ethernet:
        sim_config.add_module("ethernet", "eth", args={"interface": "tap0", "ip": "192.168.1.100"})

    for i in range(2):
        soc = SoCLinux(i!=0, args.with_ethernet)
        board_name = "sim"
        build_dir = os.path.join("build", board_name)
        builder = Builder(soc, output_dir=build_dir,
            compile_gateware=i!=0,
            csr_json=os.path.join(build_dir, "csr.json"))
        builder.build(sim_config=sim_config,
            run=i!=0,
            opt_level=args.opt_level,
            trace=args.trace,
            trace_start=int(args.trace_start),
            trace_end=int(args.trace_end))
        if i == 0:
            os.chdir("..")
            soc.generate_dts(board_name)
            soc.compile_dts(board_name)
            soc.compile_emulator(board_name)


if __name__ == "__main__":
    main()
