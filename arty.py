#!/usr/bin/env python3
from litex.boards.targets import arty

from litex.soc.interconnect import wishbone
from litex.soc.integration.builder import Builder

# LinuxSoC -----------------------------------------------------------------------------------------

class LinuxSoC(arty.EthernetSoC):
    csr_map = {
        "ddrphy": 16,
        "cpu":    17,
        "ethphy": 18,
        "ethmac": 19
    }
    csr_map.update(arty.EthernetSoC.csr_map)

    arty.EthernetSoC.mem_map = {
        "rom":          0x00000000,
        "sram":         0x10000000,
        "emulator_ram": 0x20000000,
        "ethmac":       0x30000000,
        "main_ram":     0xc0000000,
        "csr":          0xf0000000,
    }

    def __init__(self):
        arty.EthernetSoC.__init__(self, cpu_type="vexriscv", cpu_variant="linux")
        self.cpu.use_external_variant("VexRiscv.v")
        self.add_constant("NETBOOT_LINUX_VEXRISCV", None)

        # machine mode emulator ram
        self.submodules.emulator_ram = wishbone.SRAM(0x4000)
        self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

# Build --------------------------------------------------------------------------------------------

def main():
    soc = LinuxSoC()
    builder = Builder(soc, output_dir="build")
    builder.build()

if __name__ == "__main__":
    main()
