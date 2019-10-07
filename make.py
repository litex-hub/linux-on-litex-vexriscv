#!/usr/bin/env python3

import argparse
import os

from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

kB = 1024

# Board definition----------------------------------------------------------------------------------

class Board:
    def __init__(self, soc_cls, soc_capabilities):
        self.soc_cls = soc_cls
        self.soc_capabilities = soc_capabilities

    def load(self):
        raise NotImplementedError

    def flash(self):
        raise NotImplementedError

# Arty support -------------------------------------------------------------------------------------

class Arty(Board):
    SPIFLASH_PAGE_SIZE = 256
    SPIFLASH_SECTOR_SIZE = 64*kB
    def __init__(self):
        from litex_boards.targets import arty
        Board.__init__(self, arty.EthernetSoC, {"serial", "ethernet", "spiflash", "leds", "switches", "spi", "i2c", "xadc", "pwm"})

    def load(self):
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg")
        prog.load_bitstream("build/arty/gateware/top.bit")

    def flash(self):
        flash_regions = {
            "build/arty/gateware/top.bin": "0x00000000", # FPGA image:  loaded at startup
            "buildroot/Image":             "0x00400000", # Linux Image: copied to 0xc0000000 by bios
            "buildroot/rootfs.cpio":       "0x00800000", # File System: copied to 0xc0800000 by bios
            "buildroot/rv32.dtb":          "0x00f00000", # Device tree: copied to 0xc1000000 by bios
            "emulator/emulator.bin":       "0x00f80000", # MM Emulator: copied to 0x20000000 by bios
        }
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg",
            flash_proxy_basename="prog/bscan_spi_xc7a35t.bit")
        prog.set_flash_proxy_dir(".")
        for filename, base in flash_regions.items():
            base = int(base, 16)
            print("Flashing {} at 0x{:08x}".format(filename, base))
            prog.flash(base, filename)

# NeTV2 support ------------------------------------------------------------------------------------

class NeTV2(Board):
    SPIFLASH_PAGE_SIZE = 256
    SPIFLASH_SECTOR_SIZE = 64*kB
    def __init__(self):
        from litex_boards.targets import netv2
        Board.__init__(self, netv2.EthernetSoC, {"serial", "ethernet", "framebuffer", "spiflash", "leds", "xadc"})

    def load(self):
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_netv2_rpi.cfg")
        prog.load_bitstream("build/netv2/gateware/top.bit")

# Genesys2 support ---------------------------------------------------------------------------------

class Genesys2(Board):
    def __init__(self):
        from litex_boards.targets import genesys2
        Board.__init__(self, genesys2.BaseSoC, {"serial"})

    def load(self):
        from litex.build.xilinx import VivadoProgrammer
        prog = VivadoProgrammer()
        prog.load_bitstream("build/genesys2/gateware/top.bit")

# KCU105 support -----------------------------------------------------------------------------------

class KCU105(Board):
    def __init__(self):
        from litex_boards.targets import kcu105
        Board.__init__(self, kcu105.EthernetSoC, {"serial", "ethernet"})

    def load(self):
        from litex.build.xilinx import VivadoProgrammer
        prog = VivadoProgrammer()
        prog.load_bitstream("build/kcu105/gateware/top.bit")


# Nexys4DDR support --------------------------------------------------------------------------------

class Nexys4DDR(Board):
    def __init__(self):
        from litex_boards.targets import nexys4ddr
        Board.__init__(self, nexys4ddr.EthernetSoC, {"serial", "ethernet"})

    def load(self):
        from litex.build.xilinx import VivadoProgrammer
        prog = VivadoProgrammer()
        prog.load_bitstream("build/nexys4ddr/gateware/top.bit")

# NexysVideo support --------------------------------------------------------------------------------

class NexysVideo(Board):
    def __init__(self):
        from litex_boards.targets import nexys_video
        Board.__init__(self, nexys_video.EthernetSoC, {"serial", "framebuffer"})

    def load(self):
        from litex.build.xilinx import VivadoProgrammer
        prog = VivadoProgrammer()
        prog.load_bitstream("build/nexys_video/gateware/top.bit")

# MiniSpartan6 support -----------------------------------------------------------------------------

class MiniSpartan6(Board):
    def __init__(self):
        from litex_boards.targets import minispartan6
        Board.__init__(self, minispartan6.BaseSoC, {"serial"})

    def load(self):
        os.system("xc3sprog -c ftdi build/minispartan6/gateware/top.bit")


# Versa ECP5 support -------------------------------------------------------------------------------

class VersaECP5(Board):
    SPIFLASH_PAGE_SIZE = 256
    SPIFLASH_SECTOR_SIZE = 64*kB
    def __init__(self):
        from litex_boards.targets import versa_ecp5
        Board.__init__(self, versa_ecp5.EthernetSoC, {"serial", "ethernet", "spiflash"})

    def load(self):
        os.system("openocd -f prog/ecp5-versa5g.cfg -c \"transport select jtag; init; svf build/versa_ecp5/gateware/top.svf; exit\"")

# ULX3S support ------------------------------------------------------------------------------------

class ULX3S(Board):
    def __init__(self):
        from litex_boards.targets import ulx3s
        Board.__init__(self, ulx3s.BaseSoC, {"serial"})

    def load(self):
        os.system("ujprog build/ulx3s/gateware/top.svf")

# De0Nano support ------------------------------------------------------------------------------------

class De0Nano(Board):
    def __init__(self):
        from litex_boards.targets import de0nano
        Board.__init__(self, de0nano.BaseSoC, {"serial"})

    def load(self):
        from litex.build.altera import USBBlaster
        prog = USBBlaster()
        prog.load_bitstream("build/de0nano/gateware/top.sof")

# Main ---------------------------------------------------------------------------------------------

supported_boards = {
    # Xilinx
    "arty":         Arty,
    "netv2":        NeTV2,
    "genesys2":     Genesys2,
    "kcu105":       KCU105,
    "nexys4ddr":    Nexys4DDR,
    "nexys_video":  NexysVideo,
    "minispartan6": MiniSpartan6,
    # Lattice
    "versa_ecp5":   VersaECP5,
    "ulx3s":        ULX3S,
    # Altera/Intel
    "de0nano":      De0Nano,
}

def main():
    description = "Linux on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in supported_boards.keys():
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board", required=True, help="FPGA board")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream (to SRAM)")
    parser.add_argument("--flash", action="store_true", help="flash bitstream/images (to SPI Flash)")
    parser.add_argument("--local-ip", default="192.168.1.50", help="local IP address")
    parser.add_argument("--remote-ip", default="192.168.1.100", help="remote IP address of TFTP server")
    parser.add_argument("--spi-bpw", type=int, default=8, help="Bits per word for SPI controller")
    parser.add_argument("--spi-sck-freq", type=int, default=1e6, help="SPI clock frequency")
    args = parser.parse_args()

    if args.board == "all":
        board_names = list(supported_boards.keys())
    else:
        board_names = [args.board]
    for board_name in board_names:
        board = supported_boards[board_name]()
        soc_kwargs = {}
        if board_name in ["versa_ecp5", "ulx3s"]:
            soc_kwargs["toolchain"] = "trellis"
            soc_kwargs["cpu_variant"] = "linux+no-dsp"
        if board_name in ["de0nano"]:
            soc_kwargs["l2_size"] = 1024 # FIXME: Reduce l2_size, blockram not infered correctly?
        soc = SoCLinux(board.soc_cls, **soc_kwargs)
        if "spiflash" in board.soc_capabilities:
            soc.add_spi_flash()
            soc.add_constant("SPIFLASH_PAGE_SIZE", board.SPIFLASH_PAGE_SIZE)
            soc.add_constant("SPIFLASH_SECTOR_SIZE", board.SPIFLASH_SECTOR_SIZE)
        if "ethernet" in board.soc_capabilities:
            soc.configure_ethernet(local_ip=args.local_ip, remote_ip=args.remote_ip)
        if "leds" in board.soc_capabilities:
            # pwm uses led0 so this one must be skipped
            soc.add_leds(1 if "pwm" in board.soc_capabilities else 0)
        if "pwm" in board.soc_capabilities:
            soc.add_pwm()
        if "switches" in board.soc_capabilities:
            soc.add_switches()
        if "spi" in board.soc_capabilities:
            soc.add_spi(args.spi_bpw, args.spi_sck_freq)
        if "i2c" in board.soc_capabilities:
            soc.add_i2c()
        if "xadc" in board.soc_capabilities:
            soc.add_xadc()
        if "framebuffer" in board.soc_capabilities:
            soc.add_framebuffer()
        soc.configure_boot()

        build_dir = os.path.join("build", board_name)
        if args.build:
            builder = Builder(soc, output_dir=build_dir,
                csr_json=os.path.join(build_dir, "csr.json"))
        else:
            builder = Builder(soc, output_dir="build/" + board_name,
                compile_software=False, compile_gateware=False,
                csr_json=os.path.join(build_dir, "csr.json"))
        builder.build()

        soc.generate_dts(board_name)
        soc.compile_dts(board_name)
        soc.compile_emulator(board_name)

        if args.load:
            board.load()

        if args.flash:
            board.flash()

if __name__ == "__main__":
    main()
