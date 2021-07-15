#!/usr/bin/env python3

#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2021, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import sys
import argparse
import os

from litex.soc.cores.cpu import VexRiscvSMP
from litex.soc.integration.builder import Builder

from soc_linux import SoCLinux

kB = 1024

# Board definition----------------------------------------------------------------------------------

class Board:
    soc_kwargs = {"integrated_rom_size": 0x10000, "l2_size": 0}
    def __init__(self, soc_cls=None, soc_capabilities={}, soc_constants={}, bitstream_ext=""):
        self.soc_cls          = soc_cls
        self.soc_capabilities = soc_capabilities
        self.soc_constants    = soc_constants
        self.bitstream_ext    = bitstream_ext

    def load(self, filename):
        prog = self.platform.create_programmer()
        prog.load_bitstream(filename)

    def flash(self, filename):
        prog = self.platform.create_programmer()
        prog.flash(0, filename)

#---------------------------------------------------------------------------------------------------
# Xilinx Boards
#---------------------------------------------------------------------------------------------------

# Acorn CLE 215+ support ---------------------------------------------------------------------------

class AcornCLE215(Board):
    def __init__(self):
        from litex_boards.targets import acorn
        Board.__init__(self, acorn.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sata",
        }, bitstream_ext=".bit")

# Arty support -------------------------------------------------------------------------------------

class Arty(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    def __init__(self):
        from litex_boards.targets import arty
        Board.__init__(self, arty.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "spiflash",
            "sdcard",
            # GPIOs
            "leds",
            "rgb_led",
            "switches",
            # Buses
            "spi",
            "i2c",
            # Monitoring
            "xadc",
            # 7-Series specific
            "mmcm",
            "icap_bitstream",
        }, bitstream_ext=".bit")

class ArtyA7(Arty):
    SPIFLASH_DUMMY_CYCLES = 7

class ArtyS7(Arty):
    def __init__(self):
        from litex_boards.targets import arty_s7
        Board.__init__(self, arty_s7.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "spiflash",
            # GPIOs
            "leds",
            "rgb_led",
            "switches",
            # Buses
            "spi",
            "i2c",
            # Monitoring
            "xadc",
            # 7-Series specific
            "mmcm",
            "icap_bitstream",
        }, bitstream_ext=".bit")

# NeTV2 support ------------------------------------------------------------------------------------

class NeTV2(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    def __init__(self):
        from litex_boards.targets import netv2
        Board.__init__(self, netv2.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "spiflash",
            "sdcard",
            # GPIOs
            "leds",
            # Video
            "framebuffer",
            # Monitoring
            "xadc",
        }, bitstream_ext=".bit")

# Genesys2 support ---------------------------------------------------------------------------------

class Genesys2(Board):
    def __init__(self):
        from litex_boards.targets import genesys2
        Board.__init__(self, genesys2.BaseSoC, soc_capabilities={
            # Communication
            "usb_fifo",
            "ethernet",
            # Storage
            "sdcard",
        }, bitstream_ext=".bit")

# KC705 support ---------------------------------------------------------------------------------

class KC705(Board):
    soc_kwargs = {"uart_baudrate": 500e3} # 1Mbauds not supported by CP210x.
    def __init__(self):
        from litex_boards.targets import kc705
        Board.__init__(self, kc705.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
            #"sata",
            # GPIOs
            "leds",
            # Monitoring
            "xadc",
        }, bitstream_ext=".bit")

# KCU105 support -----------------------------------------------------------------------------------

class KCU105(Board):
    soc_kwargs = {"uart_baudrate": 115.2e3} # FIXME: understand why not working with more.
    def __init__(self):
        from litex_boards.targets import kcu105
        Board.__init__(self, kcu105.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
        }, bitstream_ext=".bit")

# VC707 support ---------------------------------------------------------------------------------

class VC707(Board):
    soc_kwargs = {"uart_baudrate": 500e3} # 1Mbauds not supported by CP210x.
    def __init__(self):
        from litex_boards.targets import vc707
        Board.__init__(self, vc707.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            #"ethernet",
            # Storage
            #"sdcard",
            #"sata",
            # GPIOs
            "leds",
            # Monitoring
            #"xadc",
        }, bitstream_ext=".bit")

# ZCU104 support -----------------------------------------------------------------------------------

class ZCU104(Board):
    def __init__(self):
        from litex_boards.targets import zcu104
        Board.__init__(self, zcu104.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        }, bitstream_ext=".bit")

# Nexys4DDR support --------------------------------------------------------------------------------

class Nexys4DDR(Board):
    def __init__(self):
        from litex_boards.targets import nexys4ddr
        Board.__init__(self, nexys4ddr.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
            # Video
            "framebuffer",
        }, bitstream_ext=".bit")

# NexysVideo support -------------------------------------------------------------------------------

class NexysVideo(Board):
    def __init__(self):
        from litex_boards.targets import nexys_video
        Board.__init__(self, nexys_video.BaseSoC, soc_capabilities={
            # Communication
            "usb_fifo",
            # Storage
            "sdcard",
            # Video
            "framebuffer",
        }, bitstream_ext=".bit")

# MiniSpartan6 support -----------------------------------------------------------------------------

class MiniSpartan6(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import minispartan6
        Board.__init__(self, minispartan6.BaseSoC, soc_capabilities={
            # Communication
            "usb_fifo",
            # Storage
            "sdcard",
            # Video
            "framebuffer",
        }, bitstream_ext=".bit")

# Pipistrello support ------------------------------------------------------------------------------

class Pipistrello(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import pipistrello
        Board.__init__(self, pipistrello.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        }, bitstream_ext=".bit")

# XCU1525 support ----------------------------------------------------------------------------------

class XCU1525(Board):
    def __init__(self):
        from litex_boards.targets import xcu1525
        Board.__init__(self, xcu1525.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sata",
        }, bitstream_ext=".bit")

# AlveoU280 (ES1) support -------------------------------------------------------------------------------

class AlveoU280(Board):
    soc_kwargs = {
        "ddram_channel": 0, # pick board DRAM channel
        "with_pcie": False,
        "driver": False,
        "with_led_chaser": False,
        "with_hbm": False,
        "sys_clk_freq": 150e6
    }
    def __init__(self):
        from litex_boards.targets import alveo_u280
        Board.__init__(self, alveo_u280.BaseSoC, soc_capabilities={
            # Communication
            # "serial"
        }, bitstream_ext=".bit")

# AlveoU250 support -------------------------------------------------------------------------------

class AlveoU250(Board):
    def __init__(self):
        from litex_boards.targets import alveo_u250
        Board.__init__(self, alveo_u250.BaseSoC, soc_capabilities={
            # Communication
            "serial"
        }, bitstream_ext=".bit")

# SDS1104X-E support -------------------------------------------------------------------------------

class SDS1104XE(Board):
    soc_kwargs = {"l2_size" : 8192} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import sds1104xe
        Board.__init__(self, sds1104xe.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Video
            "framebuffer",
        }, bitstream_ext=".bit")

    def load(self, filename):
        prog = self.platform.create_programmer()
        prog.load_bitstream(filename, device=1)

# QMTECH WuKong support ---------------------------------------------------------------------------

class Qmtech_WuKong(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    soc_kwargs = {
        "uart_baudrate": 3e6,
        "l2_size" : 2048,              # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import qmtech_wukong
        Board.__init__(self, qmtech_wukong.BaseSoC, soc_capabilities={
            "leds",
            # Communication
            "serial",
            "ethernet",
            # Storage
            "spiflash",
            #"spisdcard",
            # Video
            #"video_terminal",
            "framebuffer",
        }, bitstream_ext=".bit")

#---------------------------------------------------------------------------------------------------
# Lattice Boards
#---------------------------------------------------------------------------------------------------

# Versa ECP5 support -------------------------------------------------------------------------------

class VersaECP5(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 11
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import versa_ecp5
        Board.__init__(self, versa_ecp5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "spiflash",
        }, bitstream_ext=".bit")

# ULX3S support ------------------------------------------------------------------------------------

class ULX3S(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import ulx3s
        Board.__init__(self, ulx3s.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
            # Video,
            "framebuffer",
        }, bitstream_ext=".svf")

# HADBadge support ---------------------------------------------------------------------------------

class HADBadge(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 8
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import hadbadge
        Board.__init__(self, hadbadge.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "spiflash",
        }, bitstream_ext=".bit")

    def load(self, filename):
        os.system("dfu-util --alt 2 --download {} --reset".format(filename))

# OrangeCrab support -------------------------------------------------------------------------------

class OrangeCrab(Board):
    soc_kwargs = {
        "sys_clk_freq" : int(64e6), # Increase sys_clk_freq to 64MHz (48MHz default).
        "l2_size"      : 2048,      # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import orangecrab
        os.system("git clone https://github.com/litex-hub/valentyusb -b hw_cdc_eptri")
        sys.path.append("valentyusb") # FIXME: do proper install of ValentyUSB.
        Board.__init__(self, orangecrab.BaseSoC, soc_capabilities={
            # Communication
            "usb_acm",
            # Buses
            "i2c",
            # Storage
            "spisdcard",
        }, bitstream_ext=".bit")

# Cam Link 4K support ------------------------------------------------------------------------------

class CamLink4K(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import camlink_4k
        Board.__init__(self, camlink_4k.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        }, bitstream_ext=".bit")

    def load(self, filename):
        os.system("camlink configure {}".format(filename))

# TrellisBoard support -----------------------------------------------------------------------------

class TrellisBoard(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import trellisboard
        Board.__init__(self, trellisboard.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
        }, bitstream_ext=".bit")

# ECPIX5 support -----------------------------------------------------------------------------------

class ECPIX5(Board):
    SPIFLASH_PAGE_SIZE    = 256
    SPIFLASH_SECTOR_SIZE  = 64*kB
    SPIFLASH_DUMMY_CYCLES = 8
    soc_kwargs = {
        "sys_clk_freq" : int(50e6),
        "l2_size"      : 2048, # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import ecpix5
        Board.__init__(self, ecpix5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # GPIO
            #"rgb_led",
            # Storage
            "sata",
            "sdcard",
            "spiflash",
        }, bitstream_ext=".bit")

# Colorlight i5 support ------------------------------------------------------------------------------------

class Colorlight_i5(Board):
    soc_kwargs = {
        "sys_clk_freq" : int(50e6), # 48MHz default.
        "l2_size"      : 2048,      # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import colorlight_i5
        Board.__init__(self, colorlight_i5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
        }, bitstream_ext=".bit")

#---------------------------------------------------------------------------------------------------
# Intel Boards
#---------------------------------------------------------------------------------------------------

# De10Nano support ---------------------------------------------------------------------------------

class De10Nano(Board):
    soc_kwargs = {
        "with_mister_sdram": True, # Add MiSTer SDRAM extension.
        "l2_size" : 2048,          # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import de10nano
        Board.__init__(self, de10nano.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
            # GPIOs
            "leds",
            "switches",
        }, bitstream_ext=".sof")

# De0Nano support ----------------------------------------------------------------------------------

class De0Nano(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import de0nano
        Board.__init__(self, de0nano.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        }, bitstream_ext=".sof")

# QMTECH EP4CE15 support ---------------------------------------------------------------------------

class Qmtech_EP4CE15(Board):
    soc_kwargs = {
        "integrated_sram_size" : 0x800,
        "l2_size"              : 2048, # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import qmtech_ep4ce15
        Board.__init__(self, qmtech_ep4ce15.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # "leds",
        }, bitstream_ext=".sof")

#---------------------------------------------------------------------------------------------------
# Build
#---------------------------------------------------------------------------------------------------

supported_boards = {
    # Xilinx
    "acorn_cle_215":    AcornCLE215,
    "arty":             Arty,
    "arty_a7":          ArtyA7,
    "arty_s7":          ArtyS7,
    "netv2":            NeTV2,
    "genesys2":         Genesys2,
    "kc705":            KC705,
    "kcu105":           KCU105,
    "vc707" :           VC707,
    "zcu104":           ZCU104,
    "nexys4ddr":        Nexys4DDR,
    "nexys_video":      NexysVideo,
    "minispartan6":     MiniSpartan6,
    "pipistrello":      Pipistrello,
    "xcu1525":          XCU1525,
    "alveo_u280":       AlveoU280,#ES1
    "alveo_u250":       AlveoU250,
    "qmtech_wukong":    Qmtech_WuKong,
    "sds1104xe":        SDS1104XE,

    # Lattice
    "versa_ecp5":      VersaECP5,
    "ulx3s":           ULX3S,
    "hadbadge":        HADBadge,
    "orangecrab":      OrangeCrab,
    "camlink_4k":      CamLink4K,
    "trellisboard":    TrellisBoard,
    "ecpix5":          ECPIX5,
    "colorlight_i5":   Colorlight_i5,

    # Altera/Intel
    "de0nano":         De0Nano,
    "de10nano":        De10Nano,
    "qmtech_ep4ce15":  Qmtech_EP4CE15,
}

def main():
    description = "Linux on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in supported_boards.keys():
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board",          required=True,            help="FPGA board")
    parser.add_argument("--device",         default=None,             help="FPGA device")
    parser.add_argument("--variant",        default=None,             help="FPGA board variant")
    parser.add_argument("--toolchain",      default=None,             help="Toolchain use to build")
    parser.add_argument("--build",          action="store_true",      help="Build bitstream")
    parser.add_argument("--load",           action="store_true",      help="Load bitstream (to SRAM)")
    parser.add_argument("--flash",          action="store_true",      help="Flash bitstream/images (to SPI Flash)")
    parser.add_argument("--doc",            action="store_true",      help="Build documentation")
    parser.add_argument("--local-ip",       default="192.168.1.50",   help="Local IP address")
    parser.add_argument("--remote-ip",      default="192.168.1.100",  help="Remote IP address of TFTP server")
    parser.add_argument("--spi-data-width", type=int, default=8,      help="SPI data width (maximum transfered bits per xfer)")
    parser.add_argument("--spi-clk-freq",   type=int, default=1e6,    help="SPI clock frequency")
    parser.add_argument("--fdtoverlays",    default="",               help="Device Tree Overlays to apply")
    VexRiscvSMP.args_fill(parser)
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
        soc_kwargs = Board.soc_kwargs
        soc_kwargs.update(board.soc_kwargs)

        # CPU parameters ---------------------------------------------------------------------------
        # Do memory accesses through Wishbone and L2 cache when L2 size is configured.
        args.with_wishbone_memory = soc_kwargs["l2_size"] != 0
        VexRiscvSMP.args_read(args)

        # SoC parameters ---------------------------------------------------------------------------
        if args.device is not None:
            soc_kwargs.update(device=args.device)
        if args.variant is not None:
            soc_kwargs.update(variant=args.variant)
        if args.toolchain is not None:
            soc_kwargs.update(toolchain=args.toolchain)
        if "usb_fifo" in board.soc_capabilities:
            soc_kwargs.update(uart_name="usb_fifo")
        if "usb_acm" in board.soc_capabilities:
            soc_kwargs.update(uart_name="usb_acm")
        if "ethernet" in board.soc_capabilities:
            soc_kwargs.update(with_ethernet=True)
        if "sata" in board.soc_capabilities:
            soc_kwargs.update(with_sata=True)
        if "video_terminal" in board.soc_capabilities:
            soc_kwargs.update(with_video_terminal=True)
        if "framebuffer" in board.soc_capabilities:
            soc_kwargs.update(with_video_framebuffer=True)

        # SoC creation -----------------------------------------------------------------------------
        soc = SoCLinux(board.soc_cls, **soc_kwargs)
        board.platform = soc.platform

        # SoC constants ----------------------------------------------------------------------------
        for k, v in board.soc_constants.items():
            soc.add_constant(k, v)

        # SoC peripherals --------------------------------------------------------------------------
        if board_name in ["arty", "arty_a7"]:
            from litex_boards.platforms.arty import _sdcard_pmod_io
            board.platform.add_extension(_sdcard_pmod_io)

        if board_name in ["orangecrab"]:
            from litex_boards.platforms.orangecrab import feather_i2c
            board.platform.add_extension(feather_i2c)

        if "mmcm" in board.soc_capabilities:
            soc.add_mmcm(2)
        if "spiflash" in board.soc_capabilities:
            soc.add_spi_flash(dummy_cycles=board.SPIFLASH_DUMMY_CYCLES)
            soc.add_constant("SPIFLASH_PAGE_SIZE", board.SPIFLASH_PAGE_SIZE)
            soc.add_constant("SPIFLASH_SECTOR_SIZE", board.SPIFLASH_SECTOR_SIZE)
        if "spisdcard" in board.soc_capabilities:
            soc.add_spi_sdcard()
        if "sdcard" in board.soc_capabilities:
            soc.add_sdcard()
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
        if "icap_bitstream" in board.soc_capabilities:
            soc.add_icap_bitstream()
        soc.configure_boot()

        # Build ------------------------------------------------------------------------------------
        build_dir = os.path.join("build", board_name)
        builder   = Builder(soc,
            output_dir   = os.path.join("build", board_name),
            bios_options = ["TERM_MINI"],
            csr_json     = os.path.join(build_dir, "csr.json"),
            csr_csv      = os.path.join(build_dir, "csr.csv")
        )
        builder.build(run=args.build, build_name=board_name)

        # DTS --------------------------------------------------------------------------------------
        soc.generate_dts(board_name)
        soc.compile_dts(board_name, args.fdtoverlays)

        # DTB --------------------------------------------------------------------------------------
        soc.combine_dtb(board_name, args.fdtoverlays)

        # Load FPGA bitstream ----------------------------------------------------------------------
        if args.load:
            board.load(filename=os.path.join(builder.gateware_dir, soc.build_name + board.bitstream_ext))

        # Flash bitstream/images (to SPI Flash) ----------------------------------------------------
        if args.flash:
            board.flash(filename=os.path.join(builder.gateware_dir, soc.build_name + board.bitstream_ext))

        # Generate SoC documentation ---------------------------------------------------------------
        if args.doc:
            soc.generate_doc(board_name)

if __name__ == "__main__":
    main()
