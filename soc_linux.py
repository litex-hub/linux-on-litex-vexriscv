#!/usr/bin/env python3

import os
import subprocess

from migen import *

from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import *

from litex.soc.cores.gpio import GPIOOut, GPIOIn
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.xadc import XADC
from litex.soc.cores.pwm import PWM
from litex.soc.cores.icap import ICAPBitstream
from litex.soc.cores.clock import S7MMCM

from litevideo.output import VideoOut

from migen.build.generic_platform import Pins, IOStandard, Subsignal
from litex.build.generic_platform import *

from litesdcard.phy import SDPHY
from litesdcard.core import SDCore

# Predefined values --------------------------------------------------------------------------------

video_resolutions = {
    "1920x1080_60Hz" : {
        "pix_clk"        : 148.5e6,
        "h-active"       : 1920,
        "h-blanking"     : 280,
        "h-sync"         : 44,
        "h-front-porch"  : 148,
        "v-active"       : 1080,
        "v-blanking"     : 45,
        "v-sync"         : 5,
        "v-front-porch"  : 36,
    },
    "1280x720_60Hz"  : {
        "pix_clk"        : 74.25e6,
        "h-active"       : 1280,
        "h-blanking"     : 370,
        "h-sync"         : 40,
        "h-front-porch"  : 220,
        "v-active"       : 720,
        "v-blanking"     : 30,
        "v-sync"         : 5,
        "v-front-porch"  : 20,
    },
    "640x480_75Hz"   : {
        "pix_clk"        : 31.5e6,
        "h-active"       : 640,
        "h-blanking"     : 200,
        "h-sync"         : 64,
        "h-front-porch"  : 16,
        "v-active"       : 480,
        "v-blanking"     : 20,
        "v-sync"         : 3,
        "v-front-porch"  : 1,
    }
}

# Helpers ------------------------------------------------------------------------------------------

def platform_request_all(platform, name):
    from litex.build.generic_platform import ConstraintError
    r = []
    while True:
        try:
            r += [platform.request(name, len(r))]
        except ConstraintError:
            break
    if r == []:
        raise ValueError
    return r

# SoCLinux -----------------------------------------------------------------------------------------

def SoCLinux(soc_cls, **kwargs):
    class _SoCLinux(soc_cls):
        csr_map = {**soc_cls.csr_map, **{
            "ctrl":       0,
            "uart":       2,
            "timer0":     3,
        }}
        interrupt_map = {**soc_cls.interrupt_map, **{
            "uart":       0,
            "timer0":     1,
        }}
        mem_map = {**soc_cls.mem_map, **{
            "ethmac":       0xb0000000, # len: 0x2000
            "sdread":       0xb0002000, # len: 0x200
            "sdwrite":      0xb0002200, # len: 0x200
            "spiflash":     0xd0000000,
            "csr":          0xf0000000,
        }}

        def __init__(self, cpu_variant="linux", uart_baudrate=1e6, **kwargs):

            # SoC ----------------------------------------------------------------------------------
            soc_cls.__init__(self,
                cpu_type       = "vexriscv",
                cpu_variant    = cpu_variant,
                uart_baudrate  = uart_baudrate,
                max_sdram_size = 0x40000000, # Limit mapped SDRAM to 1GB.
                **kwargs)

            # Add linker region for machine mode emulator
            self.add_memory_region("emulator", self.mem_map["main_ram"] + 0x01100000, 0x4000,
                type="cached+linker")

        # Leds -------------------------------------------------------------------------------------
        def add_leds(self):
            self.submodules.leds = GPIOOut(Cat(platform_request_all(self.platform, "user_led")))
            self.add_csr("leds")

        # RGB Led ----------------------------------------------------------------------------------
        def add_rgb_led(self):
            rgb_led_pads = self.platform.request("rgb_led", 0)
            for n in "rgb":
                setattr(self.submodules, "rgb_led_{}0".format(n), PWM(getattr(rgb_led_pads, n)))
                self.add_csr("rgb_led_{}0".format(n))

        # Switches ---------------------------------------------------------------------------------
        def add_switches(self):
            self.submodules.switches = GPIOIn(Cat(platform_request_all(self.platform, "user_sw")))
            self.add_csr("switches")

        # SPI --------------------------------------------------------------------------------------
        def add_spi(self, data_width, clk_freq):
            spi_pads = self.platform.request("spi")
            self.submodules.spi = SPIMaster(spi_pads, data_width, self.clk_freq, clk_freq)
            self.add_csr("spi")

        # I2C --------------------------------------------------------------------------------------
        def add_i2c(self):
            self.submodules.i2c0 = I2CMaster(self.platform.request("i2c", 0))
            self.add_csr("i2c0")

        # XADC (Xilinx only) -----------------------------------------------------------------------
        def add_xadc(self):
            self.submodules.xadc = XADC()
            self.add_csr("xadc")

        # Framebuffer (Xilinx only) ----------------------------------------------------------------
        def add_framebuffer(self, video_settings):
            platform = self.platform
            assert platform.device[:4] == "xc7a"
            dram_port = self.sdram.crossbar.get_port(
                mode         = "read",
                data_width   = 32,
                clock_domain = "pix",
                reverse      = True)
            framebuffer = VideoOut(
                device    = platform.device,
                pads      = platform.request("hdmi_out"),
                dram_port = dram_port)
            self.submodules.framebuffer = framebuffer
            self.add_csr("framebuffer")

            clocking = framebuffer.driver.clocking
            platform.add_period_constraint(clocking.cd_pix.clk,   1e9/video_settings["pix_clk"])
            platform.add_period_constraint(clocking.cd_pix5x.clk, 1e9/(5*video_settings["pix_clk"]))
            platform.add_false_path_constraints(
                self.crg.cd_sys.clk,
                framebuffer.driver.clocking.cd_pix.clk,
                framebuffer.driver.clocking.cd_pix5x.clk)

            self.add_constant("litevideo_pix_clk",       video_settings["pix_clk"])
            self.add_constant("litevideo_h_active",      video_settings["h-active"])
            self.add_constant("litevideo_h_blanking",    video_settings["h-blanking"])
            self.add_constant("litevideo_h_sync",        video_settings["h-sync"])
            self.add_constant("litevideo_h_front_porch", video_settings["h-front-porch"])
            self.add_constant("litevideo_v_active",      video_settings["v-active"])
            self.add_constant("litevideo_v_blanking",    video_settings["v-blanking"])
            self.add_constant("litevideo_v_sync",        video_settings["v-sync"])
            self.add_constant("litevideo_v_front_porch", video_settings["v-front-porch"])

        # ICAP Bitstream (Xilinx only) -------------------------------------------------------------
        def add_icap_bitstream(self):
            self.submodules.icap_bit = ICAPBitstream();
            self.add_csr("icap_bit")

        # MMCM (Xilinx only) -----------------------------------------------------------------------
        def add_mmcm(self, nclkout):
            if (nclkout > 7):
                raise ValueError("nclkout cannot be above 7!")

            self.cd_mmcm_clkout = []
            self.submodules.mmcm = S7MMCM(speedgrade=-1)
            self.mmcm.register_clkin(self.crg.cd_sys.clk, self.clk_freq)

            for n in range(nclkout):
                self.cd_mmcm_clkout += [ClockDomain(name="cd_mmcm_clkout{}".format(n))]
                self.mmcm.create_clkout(self.cd_mmcm_clkout[n], self.clk_freq)
            self.mmcm.clock_domains.cd_mmcm_clkout = self.cd_mmcm_clkout

            self.add_constant("clkout_def_freq", int(self.clk_freq))
            self.add_constant("clkout_def_phase", int(0))
            self.add_constant("clkout_def_duty_num", int(50))
            self.add_constant("clkout_def_duty_den", int(100))
            # We need to write exponent of clkout_margin to allow the driver for smaller inaccuracy
            from math import log10
            exp = log10(self.mmcm.clkouts[0][3])
            if exp < 0:
                self.add_constant("clkout_margin_exp", int(abs(exp)))
                self.add_constant("clkout_margin", int(self.mmcm.clkouts[0][3] * 10 ** abs(exp)))
            else:
                self.add_constant("clkout_margin", int(self.mmcm.clkouts[0][3]))
                self.add_constant("clkout_margin_exp", int(0))

            self.add_constant("nclkout", int(nclkout))
            self.add_constant("mmcm_lock_timeout", int(10))
            self.add_constant("mmcm_drdy_timeout", int(10))
            self.add_constant("vco_margin", int(self.mmcm.vco_margin))
            self.add_constant("vco_freq_range_min", int(self.mmcm.vco_freq_range[0]))
            self.add_constant("vco_freq_range_max", int(self.mmcm.vco_freq_range[1]))
            self.add_constant("clkfbout_mult_frange_min", int(self.mmcm.clkfbout_mult_frange[0]))
            self.add_constant("clkfbout_mult_frange_max", int(self.mmcm.clkfbout_mult_frange[1]))
            self.add_constant("divclk_divide_range_min", int(self.mmcm.divclk_divide_range[0]))
            self.add_constant("divclk_divide_range_max", int(self.mmcm.divclk_divide_range[1]))
            self.add_constant("clkout_divide_range_min", int(self.mmcm.clkout_divide_range[0]))
            self.add_constant("clkout_divide_range_max", int(self.mmcm.clkout_divide_range[1]))

            self.mmcm.expose_drp()
            self.add_csr("mmcm")

            self.comb += self.mmcm.reset.eq(self.mmcm.drp_reset.re)

        # Ethernet configuration -------------------------------------------------------------------
        def configure_ethernet(self, local_ip, remote_ip):
            local_ip  = local_ip.split(".")
            remote_ip = remote_ip.split(".")

            self.add_constant("LOCALIP1", int(local_ip[0]))
            self.add_constant("LOCALIP2", int(local_ip[1]))
            self.add_constant("LOCALIP3", int(local_ip[2]))
            self.add_constant("LOCALIP4", int(local_ip[3]))

            self.add_constant("REMOTEIP1", int(remote_ip[0]))
            self.add_constant("REMOTEIP2", int(remote_ip[1]))
            self.add_constant("REMOTEIP3", int(remote_ip[2]))
            self.add_constant("REMOTEIP4", int(remote_ip[3]))

        # Boot configuration -----------------------------------------------------------------------
        def configure_boot(self):
            if hasattr(self, "spiflash"):
                self.add_constant("FLASH_BOOT_ADDRESS", self.mem_map["spiflash"])

        # DTS generation ---------------------------------------------------------------------------
        def generate_dts(self, board_name):
            json = os.path.join("build", board_name, "csr.json")
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            subprocess.check_call(
                "./json2dts.py {} > {}".format(json, dts), shell=True)

        # DTS compilation --------------------------------------------------------------------------
        def compile_dts(self, board_name):
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            dtb = os.path.join("buildroot", "rv32.dtb")
            subprocess.check_call(
                "dtc -O dtb -o {} {}".format(dtb, dts), shell=True)

        # Emulator compilation ---------------------------------------------------------------------
        def compile_emulator(self, board_name):
            os.environ["BOARD"] = board_name
            subprocess.check_call("cd emulator && make", shell=True)

        # Documentation generation -----------------------------------------------------------------
        def generate_doc(self, board_name):
            from litex.soc.doc import generate_docs
            doc_dir = os.path.join("build", board_name, "doc")
            generate_docs(self, doc_dir)
            os.system("sphinx-build -M html {}/ {}/_build".format(doc_dir, doc_dir))

    return _SoCLinux(**kwargs)
