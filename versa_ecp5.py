#!/usr/bin/env python3

import argparse
import os

from migen import *

from litex.boards.targets import versa_ecp5

from litex.soc.interconnect import wishbone
from litex.soc.integration.soc_core import mem_decoder
from litex.soc.integration.builder import Builder

# LinuxSoC -----------------------------------------------------------------------------------------

class LinuxSoC(versa_ecp5.EthernetSoC):
    csr_map = {
        "ddrphy": 16,
        "cpu":    17,
        "ethphy": 18,
        "ethmac": 19
    }
    csr_map.update(versa_ecp5.EthernetSoC.csr_map)

    versa_ecp5.EthernetSoC.mem_map = {
        "rom":          0x00000000,
        "sram":         0x10000000,
        "emulator_ram": 0x20000000,
        "ethmac":       0x30000000,
        "spiflash":     0x50000000,
        "main_ram":     0xc0000000,
        "csr":          0xf0000000,
    }

    def __init__(self, toolchain="trellis", local_ip="192.168.1.50", remote_ip="192.168.1.100"):
        versa_ecp5.EthernetSoC.__init__(self, cpu_type="vexriscv", cpu_variant="linux", toolchain=toolchain)
        self.cpu.use_external_variant("VexRiscv.v")
        self.add_constant("NETBOOT_LINUX_VEXRISCV", None)

        # machine mode emulator ram
        self.submodules.emulator_ram = wishbone.SRAM(0x4000)
        self.register_mem("emulator_ram", self.mem_map["emulator_ram"], self.emulator_ram.bus, 0x4000)

        local_ip = local_ip.split(".")
        remote_ip = remote_ip.split(".")

        self.add_constant("LOCALIP1", int(local_ip[0]))
        self.add_constant("LOCALIP2", int(local_ip[1]))
        self.add_constant("LOCALIP3", int(local_ip[2]))
        self.add_constant("LOCALIP4", int(local_ip[3]))

        self.add_constant("REMOTEIP1", int(remote_ip[0]))
        self.add_constant("REMOTEIP2", int(remote_ip[1]))
        self.add_constant("REMOTEIP3", int(remote_ip[2]))
        self.add_constant("REMOTEIP4", int(remote_ip[3]))


# Build / Load -------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Linux on LiteX-VexRiscv")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (SRAM)")
    parser.add_argument("--diamond", action="store_true", help="use Diamond instead of Trellis")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")

    args = parser.parse_args()

    if args.diamond:
        toolchain_path = "/usr/local/diamond/3.10_x64/bin/lin64"
    else:
        toolchain_path = "/usr/share/trellis"

    if args.build:
        soc = LinuxSoC(toolchain="diamond" if args.diamond else "trellis", local_ip=args.local_ip, remote_ip=args.remote_ip)
        builder = Builder(soc, output_dir="build_versa5g")
        builder.build(toolchain_path=toolchain_path)
        if args.diamond:
            os.system("python3 prog/bit_to_svf.py build_versa5g/gateware/top.bit build_versa5g/gateware/top.svf")

    if args.load:
        os.system("openocd -f prog/ecp5-versa5g.cfg -c \"transport select jtag; init; svf build_versa5g/gateware/top.svf; exit\"")

if __name__ == "__main__":
    main()
