#!/usr/bin/env python3

import sys
import argparse
import os

from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux, video_resolutions

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
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    def __init__(self):
        from litex_boards.targets import arty
        Board.__init__(self, arty.BaseSoC, {"serial", "ethernet", "spiflash", "leds", "rgb_led",
            "switches", "spi", "i2c", "xadc", "icap_bitstream", "mmcm", "mmc_sdcard"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/arty/gateware/top.bit")

    def flash(self):
        flash_regions = {
            "buildroot/Image.fbi":             "0x00000000", # Linux Image: copied to 0xc0000000 by bios
            "buildroot/rootfs.cpio.fbi":       "0x00500000", # File System: copied to 0xc0800000 by bios
            "buildroot/rv32.dtb.fbi":          "0x00d00000", # Device tree: copied to 0xc1000000 by bios
            "emulator/emulator.bin.fbi":       "0x00e00000", # MM Emulator: copied to 0xc1100000 by bios
        }
        prog = self.platform.create_programmer()
        prog.set_flash_proxy_dir(".")
        for filename, base in flash_regions.items():
            base = int(base, 16)
            print("Flashing {} at 0x{:08x}".format(filename, base))
            prog.flash(base, filename)

class ArtyA7(Arty):
    SPIFLASH_DUMMY_CYCLES = 7

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/arty_a7/gateware/top.bit")

class ArtyS7(Arty):
    def __init__(self):
        from litex_boards.targets import arty_s7
        Board.__init__(self, arty_s7.BaseSoC, {"serial", "spiflash", "leds", "rgb_led", "switches",
            "spi", "i2c", "xadc", "icap_bit", "mmcm"})

    def load(self):
        from litex.build.openocd import OpenOCD
        prog = OpenOCD("prog/openocd_xilinx.cfg")
        prog.load_bitstream("build/arty_s7/gateware/top.bit")

# NeTV2 support ------------------------------------------------------------------------------------

class NeTV2(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    def __init__(self):
        from litex_boards.targets import netv2
        Board.__init__(self, netv2.BaseSoC, {"serial", "ethernet", "framebuffer", "spiflash", "leds", "xadc"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/netv2/gateware/top.bit")

# Genesys2 support ---------------------------------------------------------------------------------

class Genesys2(Board):
    def __init__(self):
        from litex_boards.targets import genesys2
        Board.__init__(self, genesys2.BaseSoC, {"serial", "ethernet"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/genesys2/gateware/top.bit")

# KC705 support ---------------------------------------------------------------------------------

class KC705(Board):
    def __init__(self):
        from litex_boards.targets import kc705
        Board.__init__(self, kc705.BaseSoC, {"serial", "ethernet", "leds", "xadc"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/kc705/gateware/top.bit")


# KCU105 support -----------------------------------------------------------------------------------

class KCU105(Board):
    def __init__(self):
        from litex_boards.targets import kcu105
        Board.__init__(self, kcu105.BaseSoC, {"serial", "ethernet"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/kcu105/gateware/top.bit")


# ZCU104 support -----------------------------------------------------------------------------------

class ZCU104(Board):
    def __init__(self):
        from litex_boards.targets import zcu104
        Board.__init__(self, zcu104.BaseSoC, {"serial"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/zcu104/gateware/top.bit")


# Nexys4DDR support --------------------------------------------------------------------------------

class Nexys4DDR(Board):
    def __init__(self):
        from litex_boards.targets import nexys4ddr
        Board.__init__(self, nexys4ddr.BaseSoC, {"serial", "spisdcard", "ethernet"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/nexys4ddr/gateware/top.bit")

# NexysVideo support -------------------------------------------------------------------------------

class NexysVideo(Board):
    def __init__(self):
        from litex_boards.targets import nexys_video
        Board.__init__(self, nexys_video.BaseSoC, {"serial", "framebuffer"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/nexys_video/gateware/top.bit")

# MiniSpartan6 support -----------------------------------------------------------------------------

class MiniSpartan6(Board):
    def __init__(self):
        from litex_boards.targets import minispartan6
        Board.__init__(self, minispartan6.BaseSoC, {"usb_fifo", "spisdcard"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/minispartan6/gateware/top.bit")

# Pipistrello support ------------------------------------------------------------------------------

class Pipistrello(Board):
    def __init__(self):
        from litex_boards.targets import pipistrello
        Board.__init__(self, pipistrello.BaseSoC, {"serial"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/pipistrello/gateware/top.bit")

# Versa ECP5 support -------------------------------------------------------------------------------

class VersaECP5(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    def __init__(self):
        from litex_boards.targets import versa_ecp5
        Board.__init__(self, versa_ecp5.BaseSoC, {"serial", "ethernet", "spiflash"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/versa_ecp5/gateware/top.svf")

# ULX3S support ------------------------------------------------------------------------------------

class ULX3S(Board):
    def __init__(self):
        from litex_boards.targets import ulx3s
        Board.__init__(self, ulx3s.BaseSoC, {"serial", "spisdcard"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/ulx3s/gateware/top.svf")

# HADBadge support ---------------------------------------------------------------------------------

class HADBadge(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 8
    def __init__(self):
        from litex_boards.targets import hadbadge
        Board.__init__(self, hadbadge.BaseSoC, {"serial", "spiflash"})

    def load(self):
        os.system("dfu-util --alt 2 --download build/hadbadge/gateware/top.bit --reset")

# OrangeCrab support -------------------------------------------------------------------------------

class OrangeCrab(Board):
    def __init__(self, uart_name="usb_acm"):
        from litex_boards.targets import orangecrab
        if uart_name == "usb_acm": # FIXME: do proper install of ValentyUSB.
            os.system("git clone https://github.com/gregdavill/valentyusb -b hw_cdc_eptri")
            sys.path.append("valentyusb")
            Board.__init__(self, orangecrab.BaseSoC, {"usb_acm", "spisdcard"})
        else:
            Board.__init__(self, orangecrab.BaseSoC, {"serial", "spisdcard"})

# Cam Link 4K support ------------------------------------------------------------------------------

class CamLink4K(Board):
    def __init__(self):
        from litex_boards.targets import camlink_4k
        Board.__init__(self, camlink_4k.BaseSoC, {"serial"})

    def load(self):
        os.system("camlink configure build/gateware/top.bit")

# TrellisBoard support -----------------------------------------------------------------------------

class TrellisBoard(Board):
    def __init__(self):
        from litex_boards.targets import trellisboard
        Board.__init__(self, trellisboard.BaseSoC, {"serial"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/trellisboard/gateware/top.svf")

# ECPIX5 support -----------------------------------------------------------------------------------

class ECPIX5(Board):
    def __init__(self):
        from litex_boards.targets import ecpix5
        Board.__init__(self, ecpix5.BaseSoC, {"serial", "ethernet"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/ecpix5/gateware/top.svf")

# De10Lite support ---------------------------------------------------------------------------------

class De10Lite(Board):
    def __init__(self):
        from litex_boards.targets import de10lite
        Board.__init__(self, de10lite.BaseSoC, {"serial"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/de10lite/gateware/top.sof")

# De10Nano support ----------------------------------------------------------------------------------

class De10Nano(Board):
    def __init__(self):
        from litex_boards.targets import de10nano
        Board.__init__(self, de10nano.MiSTerSDRAMSoC, {"serial", "spisdcard", "leds", "switches"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/de10nano/gateware/top.sof")

# De0Nano support ----------------------------------------------------------------------------------

class De0Nano(Board):
    def __init__(self):
        from litex_boards.targets import de0nano
        Board.__init__(self, de0nano.BaseSoC, {"serial"})

    def load(self):
        prog = self.platform.create_programmer()
        prog.load_bitstream("build/de0nano/gateware/top.sof")

# Main ---------------------------------------------------------------------------------------------

supported_boards = {
    # Xilinx
    "arty":         Arty,
    "arty_a7":      ArtyA7,
    "arty_s7":      ArtyS7,
    "netv2":        NeTV2,
    "genesys2":     Genesys2,
    "kc705":        KC705,
    "kcu105":       KCU105,
    "zcu104":       ZCU104,
    "nexys4ddr":    Nexys4DDR,
    "nexys_video":  NexysVideo,
    "minispartan6": MiniSpartan6,
    "pipistrello":  Pipistrello,

    # Lattice
    "versa_ecp5":   VersaECP5,
    "ulx3s":        ULX3S,
    "hadbadge":     HADBadge,
    "orangecrab":   OrangeCrab,
    "camlink_4k":   CamLink4K,
    "trellisboard": TrellisBoard,
    "ecpix5":       ECPIX5,

    # Altera/Intel
    "de0nano":      De0Nano,
    "de10lite":     De10Lite,
    "de10nano":     De10Nano,
}

def main():
    description = "Linux on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in supported_boards.keys():
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board",          required=True,            help="FPGA board")
    parser.add_argument("--build",          action="store_true",      help="Build bitstream")
    parser.add_argument("--load",           action="store_true",      help="Load bitstream (to SRAM)")
    parser.add_argument("--flash",          action="store_true",      help="Flash bitstream/images (to SPI Flash)")
    parser.add_argument("--doc",            action="store_true",      help="Build documentation")
    parser.add_argument("--local-ip",       default="192.168.1.50",   help="Local IP address")
    parser.add_argument("--remote-ip",      default="192.168.1.100",  help="Remote IP address of TFTP server")
    parser.add_argument("--spi-data-width", type=int, default=8,      help="SPI data width (maximum transfered bits per xfer)")
    parser.add_argument("--spi-clk-freq",   type=int, default=1e6,    help="SPI clock frequency")
    parser.add_argument("--video",          default="1920x1080_60Hz", help="Video configuration")
    parser.add_argument("--fbi",            action="store_true",      help="Generate fbi images")
    parser.add_argument("--mmc-sdcard-freq",type=int, default=25e6,   help="MMC sdcard frequency")
    args = parser.parse_args()

    # Board(s) selection ---------------------------------------------------------------------------
    if args.board == "all":
        board_names = list(supported_boards.keys())
    else:
        args.board = args.board.lower()
        args.board = args.board.replace(" ", "_")
        board_names = [args.board]

    # Board(s) iteration ---------------------------------------------------------------------------
    for board_name in board_names:
        board = supported_boards[board_name]()

        # SoC parameters (and override for boards that don't support default parameters) -----------
        soc_kwargs = {}
        soc_kwargs.update(integrated_rom_size=0x10000)
        if board_name in ["de0nano"]:
            soc_kwargs.update(l2_size=2048) # Not enough blockrams for default l2_size of 8192
        if board_name in ["kc705"]:
            soc_kwargs.update(uart_baudrate=500e3) # Set UART baudrate to 500KBauds since 1Mbauds not supported
        if "usb_fifo" in board.soc_capabilities:
            soc_kwargs.update(uart_name="usb_fifo")
        if "usb_acm" in board.soc_capabilities:
            soc_kwargs.update(uart_name="usb_acm")
        if "ethernet" in board.soc_capabilities:
            soc_kwargs.update(with_ethernet=True)

        # SoC creation -----------------------------------------------------------------------------
        soc = SoCLinux(board.soc_cls, **soc_kwargs)
        board.platform = soc.platform

        # SoC peripherals --------------------------------------------------------------------------
        if "spiflash" in board.soc_capabilities:
            soc.add_spi_flash(dummy_cycles=board.SPIFLASH_DUMMY_CYCLES)
            soc.add_constant("SPIFLASH_PAGE_SIZE", board.SPIFLASH_PAGE_SIZE)
            soc.add_constant("SPIFLASH_SECTOR_SIZE", board.SPIFLASH_SECTOR_SIZE)
        if "spisdcard" in board.soc_capabilities:
            soc.add_spi_sdcard()
        if "ethernet" in board.soc_capabilities:
            soc.configure_ethernet(local_ip=args.local_ip, remote_ip=args.remote_ip)
        #if "leds" in board.soc_capabilities:
        #    soc.add_leds()
        if "rgb_led" in board.soc_capabilities:
            soc.add_rgb_led()
        if "switches" in board.soc_capabilities:
            soc.add_switches()
        if "spi" in board.soc_capabilities:
            soc.add_spi(args.spi_data_width, args.spi_clk_freq)
        if "i2c" in board.soc_capabilities:
            soc.add_i2c()
        if "xadc" in board.soc_capabilities:
            soc.add_xadc()
        if "framebuffer" in board.soc_capabilities:
            assert args.video in video_resolutions.keys(), "Unsupported video resolution"
            video_settings = video_resolutions[args.video]
            soc.add_framebuffer(video_settings)
        if "icap_bitstream" in board.soc_capabilities:
            soc.add_icap_bitstream()
        if "mmcm" in board.soc_capabilities:
            soc.add_mmcm(2)
        if "mmc_sdcard" in board.soc_capabilities:
            soc.add_mmc_sdcard(args.mmc_sdcard_freq)
        soc.configure_boot()

        # Build ------------------------------------------------------------------------------------
        build_dir = os.path.join("build", board_name)
        builder   = Builder(soc, output_dir=build_dir, csr_json=os.path.join(build_dir, "csr.json"), bios_options=["TERM_MINI"])
        builder.build(run=args.build)

        # DTS --------------------------------------------------------------------------------------
        soc.generate_dts(board_name)
        soc.compile_dts(board_name)

        # Machine Mode Emulator --------------------------------------------------------------------
        soc.compile_emulator(board_name)

        # Flash Linux images -----------------------------------------------------------------------
        if args.fbi:
            os.system("python3 -m litex.soc.software.mkmscimg buildroot/Image -o buildroot/Image.fbi --fbi --little")
            os.system("python3 -m litex.soc.software.mkmscimg buildroot/rootfs.cpio -o buildroot/rootfs.cpio.fbi --fbi --little")
            os.system("python3 -m litex.soc.software.mkmscimg buildroot/rv32.dtb -o buildroot/rv32.dtb.fbi --fbi --little")
            os.system("python3 -m litex.soc.software.mkmscimg emulator/emulator.bin -o emulator/emulator.bin.fbi --fbi --little")

        # Load FPGA bitstream ----------------------------------------------------------------------
        if args.load:
            board.load()

        # Flash FPGA bitstream ---------------------------------------------------------------------
        if args.flash:
            board.flash()

        # Generate SoC documentation ---------------------------------------------------------------
        if args.doc:
            soc.generate_doc(board_name)

if __name__ == "__main__":
    main()
