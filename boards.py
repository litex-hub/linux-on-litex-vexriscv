#!/usr/bin/env python3

#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2024, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

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

# AESKU40 support -----------------------------------------------------------------------------------

class AESKU40(Board):
    soc_kwargs = {"uart_baudrate": 115.2e3} 
    def __init__(self):
        from litex_boards.targets import avnet_aesku40
        Board.__init__(self, avnet_aesku40.BaseSoC, soc_capabilities={
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
        from litex_boards.targets import sqrl_xcu1525
        Board.__init__(self, sqrl_xcu1525.BaseSoC, soc_capabilities={
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
        from litex_boards.targets import sitlinv_stlv7325_v1
        Board.__init__(self, sitlinv_stlv7325_v1.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
        })

class STLV7325_v2(Board):
    def __init__(self):
        from litex_boards.targets import sitlinv_stlv7325_v2
        Board.__init__(self, sitlinv_stlv7325_v2.BaseSoC, soc_capabilities={
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

# HSEDA XC7A35T -----------------------------------------------------------------------------------
class HSEDA_xc7a35t(Board):
    soc_kwargs = {"sys_clk_freq": int(80e6)}
    def __init__(self):
        from litex_boards.targets import hseda_xc7a35t
        Board.__init__(self, hseda_xc7a35t.BaseSoC, soc_capabilities={
            # Communication
            "serial",
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

# ULX4M-LD-V2 support ------------------------------------------------------------------------------------
class ULX4M_LD_V2(Board):
    soc_kwargs = {"uart_name": "serial", "sys_clk_freq": int(50e6), "l2_size" : 2048} #2048 } #32768} # Use Wishbone and L2 for memory accesse$
    def __init__(self):
        from litex_boards.targets import radiona_ulx4m_ld_v2
        Board.__init__(self, radiona_ulx4m_ld_v2.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            # Storage
            "sdcard",
            # Video,
            "framebuffer",
            "video_terminal",
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

# Schoko support -----------------------------------------------------------------------------------

class Schoko(Board):
    soc_kwargs = {"l2_size" : 8192}
    def __init__(self):
        from litex_boards.targets import machdyne_schoko
        Board.__init__(self, machdyne_schoko.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "usb_host",
            # Storage
            "spiflash",
            #"sdcard",
            "spisdcard",
            # Video,
            "framebuffer",
        })

# Konfekt support -----------------------------------------------------------------------------------

class Konfekt(Board):
    soc_kwargs = {"l2_size" : 0}
    def __init__(self):
        from litex_boards.targets import machdyne_konfekt
        Board.__init__(self, machdyne_konfekt.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "usb_host",
            # Storage
            #"spiflash",
            "spisdcard",
            #"sdcard",
            # Video,
            "framebuffer",
        })

# Noir support -----------------------------------------------------------------------------------

class Noir(Board):
    soc_kwargs = {"l2_size" : 8192}
    def __init__(self):
        from litex_boards.targets import machdyne_noir
        Board.__init__(self, machdyne_noir.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "usb_host",
            # Storage
            "spiflash",
            "spisdcard",
            #"sdcard",
            # Video,
            "framebuffer",
        })

#---------------------------------------------------------------------------------------------------
# Intel Boards
#---------------------------------------------------------------------------------------------------

# De10Nano support ---------------------------------------------------------------------------------

class De10Nano(Board):
    soc_kwargs = {
        "with_mister_sdram" : True, # Add MiSTer SDRAM extension.
        "l2_size"           : 2048, # Use Wishbone and L2 for memory accesses.
        "integrated_sram_size": 0x1000, # Power of 2 so Quartus infers it properly.
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
    soc_kwargs = {
        "l2_size" : 2048, # Use Wishbone and L2 for memory accesses.
        "integrated_sram_size": 0x1000, # Power of 2 so Quartus infers it properly.
    }
    def __init__(self):
        from litex_boards.targets import terasic_de0nano
        Board.__init__(self, terasic_de0nano.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })

# De1-SoC support ----------------------------------------------------------------------------------

class De1SoC(Board):
    soc_kwargs = {
        "l2_size" : 2048, # Use Wishbone and L2 for memory accesses.
        "integrated_sram_size": 0x1000, # Power of 2 so Quartus infers it properly.
    }
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
        "integrated_sram_size": 0x1000, # Power of 2 so Quartus infers it properly.
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
        "integrated_sram_size": 0x1000, # Power of 2 so Quartus infers it properly.
    }
    def __init__(self):
        from litex_boards.targets import qmtech_ep4cex5
        Board.__init__(self, qmtech_ep4cex5.BaseSoC, soc_capabilities={
            # Communication
            "serial",
        })


# QMTECH 5CEFA2 support
# It is possible to build the SoC --cpu-count=2 for this chip
class Qmtech_5CEFA2(Board):
    soc_kwargs = {
        "variant" : "5cefa2",
        "l2_size" :  2048, # Use Wishbone and L2 for memory accesses.
        "integrated_sram_size": 0x1000, # Power of 2 so Quartus infers it properly.
    }
    def __init__(self):
        from litex_boards.targets import qmtech_5cefa2
        Board.__init__(self, qmtech_5cefa2.BaseSoC, soc_capabilities={
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
# Gowin Boards
#---------------------------------------------------------------------------------------------------

# Sipeed Tang Nano 20K support ---------------------------------------------------------------------

class Sipeed_tang_nano_20k(Board):
    soc_kwargs = {"l2_size" : 2048} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import sipeed_tang_nano_20k
        Board.__init__(self, sipeed_tang_nano_20k.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "sdcard",
        })

# Sipeed Tang Primer 20K support -------------------------------------------------------------------

class Sipeed_tang_primer_20k(Board):
    soc_kwargs = {"l2_size" : 512} # Use Wishbone and L2 for memory accesses.
    def __init__(self):
        from litex_boards.targets import sipeed_tang_primer_20k
        Board.__init__(self, sipeed_tang_primer_20k.BaseSoC, soc_capabilities={
            # Communication
            "serial",
            "spisdcard",
        })
