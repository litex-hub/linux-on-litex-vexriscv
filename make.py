#!/usr/bin/env python3

#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2022, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import os
import sys
import argparse

from litex.soc.integration.builder import Builder
from litex.soc.cores.cpu.vexriscv_smp import VexRiscvSMP

from soc_linux import SoCLinux

# Board Definition ---------------------------------------------------------------------------------

class Board:
    soc_kwargs = {
        "integrated_rom_size"  : 0x10000,
        "integrated_sram_size" : 0x1800,
        "l2_size"              : 0
    }
    def __init__(self, soc_cls=None, soc_capabilities={}, soc_constants={}):
        self.soc_cls          = soc_cls
        self.soc_capabilities = soc_capabilities
        self.soc_constants    = soc_constants

    def load(self, filename):
        prog = self.platform.create_programmer()
        prog.load_bitstream(filename)

    def flash(self, filename):
        prog = self.platform.create_programmer()
        prog.flash(0, filename)

#---------------------------------------------------------------------------------------------------
# Xilinx Boards
#---------------------------------------------------------------------------------------------------

# Acorn support ------------------------------------------------------------------------------------

class Acorn(Board):
    soc_kwargs = {"uart_name": "jtag_uart", "sys_clk_freq": int(150e6)}
    def __init__(self):
        from litex_boards.targets import sqrl_acorn
        Board.__init__(self, sqrl_acorn.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sata",
        })

# Acorn PCIe support -------------------------------------------------------------------------------

class AcornPCIe(Board):
    soc_kwargs = {"uart_name": "crossover", "sys_clk_freq": int(125e6)}
    def __init__(self):
        from litex_boards.targets import sqrl_acorn
        Board.__init__(self, sqrl_acorn.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "pcie",
        })

    def flash(self, filename):
        prog = self.platform.create_programmer()
        prog.flash(0, filename.replace(".bin", "_fallback.bin"))

# Arty support -------------------------------------------------------------------------------------

class Arty(Board):
    def __init__(self):
        from litex_boards.targets import digilent_arty
        Board.__init__(self, digilent_arty.BaseSoC, soc_capabilities={
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
        })

class ArtyA7(Arty): pass

class ArtyS7(Board):
    def __init__(self):
        from litex_boards.targets import digilent_arty_s7
        Board.__init__(self, digilent_arty_s7.BaseSoC, soc_capabilities={
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
        })

# NeTV2 support ------------------------------------------------------------------------------------

class NeTV2(Board):
    def __init__(self):
        from litex_boards.targets import kosagi_netv2
        Board.__init__(self, kosagi_netv2.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
            # GPIOs
            "leds",
            # Video
            "framebuffer",
            # Monitoring
            "xadc",
        })

# Genesys2 support ---------------------------------------------------------------------------------

class Genesys2(Board):
    def __init__(self):
        from litex_boards.targets import digilent_genesys2
        Board.__init__(self, digilent_genesys2.BaseSoC, soc_capabilities={
            # Communication
            "usb_fifo",
            "ethernet",
            # Storage
            "sdcard",
        })

# KC705 support ---------------------------------------------------------------------------------

class KC705(Board):
    def __init__(self):
        from litex_boards.targets import xilinx_kc705
        Board.__init__(self, xilinx_kc705.BaseSoC, soc_capabilities={
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
        })

# VC707 support ---------------------------------------------------------------------------------

class VC707(Board):
    def __init__(self):
        from litex_boards.targets import xilinx_vc707
        Board.__init__(self, xilinx_vc707.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
            # GPIOs
            "leds",
            # Monitoring
            "xadc",
        })

# KCU105 support -----------------------------------------------------------------------------------

class KCU105(Board):
    def __init__(self):
        from litex_boards.targets import xilinx_kcu105
        Board.__init__(self, xilinx_kcu105.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
        })

# ZCU104 support -----------------------------------------------------------------------------------

class ZCU104(Board):
    def __init__(self):
        from litex_boards.targets import xilinx_zcu104
        Board.__init__(self, xilinx_zcu104.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

# Nexys4DDR support --------------------------------------------------------------------------------

class Nexys4DDR(Board):
    def __init__(self):
        from litex_boards.targets import digilent_nexys4ddr
        Board.__init__(self, digilent_nexys4ddr.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
            # Video
            "framebuffer",
        })

# NexysVideo support -------------------------------------------------------------------------------

class NexysVideo(Board):
    def __init__(self):
        from litex_boards.targets import digilent_nexys_video
        Board.__init__(self, digilent_nexys_video.BaseSoC, soc_capabilities={
            # Communication
            "usb_fifo",
            # Storage
            "sdcard",
            # Video
            "framebuffer",
        })

# MiniSpartan6 support -----------------------------------------------------------------------------

class MiniSpartan6(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import scarabhardware_minispartan6
        Board.__init__(self, scarabhardware_minispartan6.BaseSoC, soc_capabilities={
            # Communication
            "usb_fifo",
            # Storage
            "sdcard",
            # Video
            "framebuffer",
        })

# Pipistrello support ------------------------------------------------------------------------------

class Pipistrello(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import saanlima_pipistrello
        Board.__init__(self, saanlima_pipistrello.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

# XCU1525 support ----------------------------------------------------------------------------------

class XCU1525(Board):
    def __init__(self):
        from litex_boards.targets import xilinx_xcu1525
        Board.__init__(self, xilinx_xcu1525.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sata",
        })

# AlveoU280 (ES1) support -------------------------------------------------------------------------------

class AlveoU280(Board):
    soc_kwargs = {
        "with_hbm"     : True, # Use HBM @ 250MHz (Min).
        "sys_clk_freq" : 250e6
    }
    def __init__(self):
        from litex_boards.targets import xilinx_alveo_u280
        Board.__init__(self, xilinx_alveo_u280.BaseSoC, soc_capabilities={
            # Communication
            "serial"
        })

# AlveoU250 support -------------------------------------------------------------------------------

class AlveoU250(Board):
    def __init__(self):
        from litex_boards.targets import xilinx_alveo_u250
        Board.__init__(self, xilinx_alveo_u250.BaseSoC, soc_capabilities={
            # Communication
            "serial"
        })

# SDS1104X-E support -------------------------------------------------------------------------------

class SDS1104XE(Board):
    soc_kwargs = {"l2_size" : 8192} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import siglent_sds1104xe
        Board.__init__(self, siglent_sds1104xe.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Video
            "framebuffer",
        })

    def load(self, filename):
        prog = self.platform.create_programmer()
        prog.load_bitstream(filename, device=1)

# QMTECH WuKong support ---------------------------------------------------------------------------

class Qmtech_WuKong(Board):
    def __init__(self):
        from litex_boards.targets import qmtech_wukong
        Board.__init__(self, qmtech_wukong.BaseSoC, soc_capabilities={
            "leds",
            # Communication
            "serial",
            "ethernet",
            # Video
            "framebuffer",
        })


# MNT RKX7 support ---------------------------------------------------------------------------------

class MNT_RKX7(Board):
    def __init__(self):
        from litex_boards.targets import mnt_rkx7
        Board.__init__(self, mnt_rkx7.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "spisdcard",
        })

# STLV7325 -----------------------------------------------------------------------------------------

class STLV7325(Board):
    def __init__(self):
        from litex_boards.targets import aliexpress_stlv7325
        Board.__init__(self, aliexpress_stlv7325.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
        })

# Decklink Quad HDMI Recorder ----------------------------------------------------------------------

class DecklinkQuadHDMIRecorder(Board):
    soc_kwargs = {"uart_name": "crossover",  "sys_clk_freq": int(125e6)}
    def __init__(self):
        from litex_boards.targets import decklink_quad_hdmi_recorder
        Board.__init__(self, decklink_quad_hdmi_recorder.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "pcie",
        })

#---------------------------------------------------------------------------------------------------
# Lattice Boards
#---------------------------------------------------------------------------------------------------

# Versa ECP5 support -------------------------------------------------------------------------------

class VersaECP5(Board):
    def __init__(self):
        from litex_boards.targets import lattice_versa_ecp5
        Board.__init__(self, lattice_versa_ecp5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
        })

# ULX3S support ------------------------------------------------------------------------------------

class ULX3S(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import radiona_ulx3s
        Board.__init__(self, radiona_ulx3s.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
            # Video,
            "framebuffer",
        })

# HADBadge support ---------------------------------------------------------------------------------

class HADBadge(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import hackaday_hadbadge
        Board.__init__(self, hackaday_hadbadge.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

    def load(self, filename):
        os.system("dfu-util --alt 2 --download {} --reset".format(filename))

# OrangeCrab support -------------------------------------------------------------------------------

class OrangeCrab(Board):
    soc_kwargs = {"sys_clk_freq" : int(64e6) } # Increase sys_clk_freq to 64MHz (48MHz default).
    def __init__(self):
        from litex_boards.targets import gsd_orangecrab
        Board.__init__(self, gsd_orangecrab.BaseSoC, soc_capabilities={
            # Communication
            "usb_acm",
            # Buses
            "i2c",
            # Storage
            "sdcard",
        })

# Butterstick support ------------------------------------------------------------------------------

class ButterStick(Board):
    soc_kwargs = {"uart_name": "jtag_uart"}
    def __init__(self):
        from litex_boards.targets import gsd_butterstick
        Board.__init__(self, gsd_butterstick.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
        })

# Cam Link 4K support ------------------------------------------------------------------------------

class CamLink4K(Board):
    def __init__(self):
        from litex_boards.targets import camlink_4k
        Board.__init__(self, camlink_4k.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

    def load(self, filename):
        os.system("camlink configure {}".format(filename))

# TrellisBoard support -----------------------------------------------------------------------------

class TrellisBoard(Board):
    def __init__(self):
        from litex_boards.targets import trellisboard
        Board.__init__(self, trellisboard.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
        })

# ECPIX5 support -----------------------------------------------------------------------------------

class ECPIX5(Board):
    def __init__(self):
        from litex_boards.targets import lambdaconcept_ecpix5
        Board.__init__(self, lambdaconcept_ecpix5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
            # Storage
            "sdcard",
        })

# Colorlight i5 support ----------------------------------------------------------------------------

class Colorlight_i5(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import colorlight_i5
        Board.__init__(self, colorlight_i5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "ethernet",
        })

# Icesugar Pro support -----------------------------------------------------------------------------

class IcesugarPro(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import muselab_icesugar_pro
        Board.__init__(self, muselab_icesugar_pro.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "spiflash",
            "sdcard",
        })

#---------------------------------------------------------------------------------------------------
# Intel Boards
#---------------------------------------------------------------------------------------------------

# De10Nano support ---------------------------------------------------------------------------------

class De10Nano(Board):
    soc_kwargs = {
        "with_mister_sdram" : True, # Add MiSTer SDRAM extension.
        "l2_size"           : 2048, # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import terasic_de10nano
        Board.__init__(self, terasic_de10nano.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
            # GPIOs
            "leds",
            "switches",
        })

# De0Nano support ----------------------------------------------------------------------------------

class De0Nano(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import terasic_de0nano
        Board.__init__(self, terasic_de0nano.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

# De1-SoC support ----------------------------------------------------------------------------------

class De1SoC(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import terasic_de1soc
        Board.__init__(self, terasic_de1soc.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # GPIOs
            "leds",
            "switches",
        })

# QMTECH EP4CE15 support ---------------------------------------------------------------------------

class Qmtech_EP4CE15(Board):
    soc_kwargs = {
        "variant" : "ep4ce15",
        "l2_size" : 2048, # Use Wishbone and L2 for memory accesses.
        "integrated_sram_size" : 0x800,
    }
    def __init__(self):
        from litex_boards.targets import qmtech_ep4cex5
        Board.__init__(self, qmtech_ep4cex5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

# ... and its bigger brother 

class Qmtech_EP4CE55(Board):
    soc_kwargs = {
        "variant" : "ep4ce55",
        "l2_size" :  2048, # Use Wishbone and L2 for memory accesses.
    }
    def __init__(self):
        from litex_boards.targets import qmtech_ep4cex5
        Board.__init__(self, qmtech_ep4cex5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

#---------------------------------------------------------------------------------------------------
# Efinix Boards
#---------------------------------------------------------------------------------------------------

class TrionT120BGA576DevKit(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import efinix_trion_t120_bga576_dev_kit
        Board.__init__(self, efinix_trion_t120_bga576_dev_kit.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # GPIOs
             "leds",
        })

class TitaniumTi60F225DevKit(Board):
    soc_kwargs = {
        "with_hyperram" : True,
        "sys_clk_freq"  : 300e6,
    }
    def __init__(self):
        from litex_boards.targets import efinix_titanium_ti60_f225_dev_kit
        Board.__init__(self, efinix_titanium_ti60_f225_dev_kit.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
            # GPIOs
            "leds",
        })

#---------------------------------------------------------------------------------------------------
# Build
#---------------------------------------------------------------------------------------------------

supported_boards = {
    # Xilinx
    "acorn"                       : Acorn,
    "acorn_pcie"                  : AcornPCIe,
    "arty"                        : Arty,
    "arty_a7"                     : ArtyA7,
    "arty_s7"                     : ArtyS7,
    "netv2"                       : NeTV2,
    "genesys2"                    : Genesys2,
    "kc705"                       : KC705,
    "vc707"                       : VC707,
    "kcu105"                      : KCU105,
    "zcu104"                      : ZCU104,
    "nexys4ddr"                   : Nexys4DDR,
    "nexys_video"                 : NexysVideo,
    "minispartan6"                : MiniSpartan6,
    "pipistrello"                 : Pipistrello,
    "xcu1525"                     : XCU1525,
    "alveo_u280"                  : AlveoU280,
    "alveo_u250"                  : AlveoU250,
    "qmtech_wukong"               : Qmtech_WuKong,
    "sds1104xe"                   : SDS1104XE,
    "mnt_rkx7"                    : MNT_RKX7,
    "stlv7325"                    : STLV7325,
    "decklink_quad_hdmi_recorder" : DecklinkQuadHDMIRecorder,

    # Lattice
    "versa_ecp5"                  : VersaECP5,
    "ulx3s"                       : ULX3S,
    "hadbadge"                    : HADBadge,
    "orangecrab"                  : OrangeCrab,
    "butterstick"                 : ButterStick,
    "camlink_4k"                  : CamLink4K,
    "trellisboard"                : TrellisBoard,
    "ecpix5"                      : ECPIX5,
    "colorlight_i5"               : Colorlight_i5,
    "icesugar_pro"                : IcesugarPro,

    # Altera/Intel
    "de0nano"                     : De0Nano,
    "de10nano"                    : De10Nano,
    "de1soc"                      : De1SoC,
    "qmtech_ep4ce15"              : Qmtech_EP4CE15,
    "qmtech_ep4ce55"              : Qmtech_EP4CE55,

    # Efinix
    "trion_t120_bga576_dev_kit"   : TrionT120BGA576DevKit,
    "titanium_ti60_f225_dev_kit"  : TitaniumTi60F225DevKit,
    }

def main():
    description = "Linux on LiteX-VexRiscv\n\n"
    description += "Available boards:\n"
    for name in sorted(supported_boards.keys()):
        description += "- " + name + "\n"
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--board",          required=True,               help="FPGA board.")
    parser.add_argument("--device",         default=None,                help="FPGA device.")
    parser.add_argument("--variant",        default=None,                help="FPGA board variant.")
    parser.add_argument("--toolchain",      default=None,                help="Toolchain use to build.")
    parser.add_argument("--uart-baudrate",  default=115.2e3, type=float, help="UART baudrate.")
    parser.add_argument("--build",          action="store_true",         help="Build bitstream.")
    parser.add_argument("--load",           action="store_true",         help="Load bitstream (to SRAM).")
    parser.add_argument("--flash",          action="store_true",         help="Flash bitstream/images (to Flash).")
    parser.add_argument("--doc",            action="store_true",         help="Build documentation.")
    parser.add_argument("--local-ip",       default="192.168.1.50",      help="Local IP address.")
    parser.add_argument("--remote-ip",      default="192.168.1.100",     help="Remote IP address of TFTP server.")
    parser.add_argument("--spi-data-width", default=8,   type=int,       help="SPI data width (max bits per xfer).")
    parser.add_argument("--spi-clk-freq",   default=1e6, type=int,       help="SPI clock frequency.")
    parser.add_argument("--fdtoverlays",    default="",                  help="Device Tree Overlays to apply.")
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

        # If Wishbone Memory is forced, enabled L2 Cache (if not already):
        if args.with_wishbone_memory:
            soc_kwargs["l2_size"] = max(soc_kwargs["l2_size"], 2048) # Defaults to 2048.
        # Else if board is configured to use L2 Cache, force use of Wishbone Memory on VexRiscv-SMP.
        else:
            args.with_wishbone_memory = soc_kwargs["l2_size"] != 0

        VexRiscvSMP.args_read(args)

        # SoC parameters ---------------------------------------------------------------------------
        if args.device is not None:
            soc_kwargs.update(device=args.device)
        if args.variant is not None:
            soc_kwargs.update(variant=args.variant)
        if args.toolchain is not None:
            soc_kwargs.update(toolchain=args.toolchain)

        # UART.
        soc_kwargs["uart_baudrate"] = int(args.uart_baudrate)
        if "crossover" in board.soc_capabilities:
            soc_kwargs.update(uart_name="crossover")
        if "usb_fifo" in board.soc_capabilities:
            soc_kwargs.update(uart_name="usb_fifo")
        if "usb_acm" in board.soc_capabilities:
            soc_kwargs.update(uart_name="usb_acm")

        # Peripherals
        if "leds" in board.soc_capabilities:
            soc_kwargs.update(with_led_chaser=True)
        if "ethernet" in board.soc_capabilities:
            soc_kwargs.update(with_ethernet=True)
        if "pcie" in board.soc_capabilities:
            soc_kwargs.update(with_pcie=True)
        if "spiflash" in board.soc_capabilities:
            soc_kwargs.update(with_spi_flash=True)
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

        # PCIe Driver ------------------------------------------------------------------------------
        if "pcie" in board.soc_capabilities:
            from litepcie.software import generate_litepcie_software
            generate_litepcie_software(soc, os.path.join(builder.output_dir, "driver"))

        # Load FPGA bitstream ----------------------------------------------------------------------
        if args.load:
            board.load(filename=builder.get_bitstream_filename(mode="sram"))

        # Flash bitstream/images (to SPI Flash) ----------------------------------------------------
        if args.flash:
            board.flash(filename=builder.get_bitstream_filename(mode="flash"))

        # Generate SoC documentation ---------------------------------------------------------------
        if args.doc:
            soc.generate_doc(board_name)

if __name__ == "__main__":
    main()
