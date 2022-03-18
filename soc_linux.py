#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2022, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import os
import json
import shutil
import subprocess

from migen import *

from litex.soc.interconnect.csr import *

from litex.soc.cores.cpu.vexriscv_smp import VexRiscvSMP
from litex.soc.cores.gpio import GPIOOut, GPIOIn
from litex.soc.cores.spi import SPIMaster
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.xadc import XADC
from litex.soc.cores.pwm import PWM
from litex.soc.cores.icap import ICAPBitstream
from litex.soc.cores.clock import S7MMCM

from litex.tools.litex_json2dts_linux import generate_dts

# SoCLinux -----------------------------------------------------------------------------------------

def SoCLinux(soc_cls, **kwargs):
    class _SoCLinux(soc_cls):
        def __init__(self, **kwargs):

            # SoC ----------------------------------------------------------------------------------
            soc_cls.__init__(self,
                cpu_type       = "vexriscv_smp",
                cpu_variant    = "linux",
                **kwargs)

        # RGB Led ----------------------------------------------------------------------------------
        def add_rgb_led(self):
            rgb_led_pads = self.platform.request("rgb_led", 0)
            for n in "rgb":
                setattr(self.submodules, "rgb_led_{}0".format(n), PWM(getattr(rgb_led_pads, n)))

        # Switches ---------------------------------------------------------------------------------
        def add_switches(self):
            self.submodules.switches = GPIOIn(Cat(self.platform.request_all("user_sw")), with_irq=True)
            self.add_interrupt("switches")

        # SPI --------------------------------------------------------------------------------------
        def add_spi(self, data_width, clk_freq):
            spi_pads = self.platform.request("spi")
            self.submodules.spi = SPIMaster(spi_pads, data_width, self.clk_freq, clk_freq)

        # I2C --------------------------------------------------------------------------------------
        def add_i2c(self):
            self.submodules.i2c0 = I2CMaster(self.platform.request("i2c", 0))

        # XADC (Xilinx only) -----------------------------------------------------------------------
        def add_xadc(self):
            self.submodules.xadc = XADC()

        # ICAP Bitstream (Xilinx only) -------------------------------------------------------------
        def add_icap_bitstream(self):
            self.submodules.icap_bit = ICAPBitstream();

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

        # DTS generation ---------------------------------------------------------------------------
        def generate_dts(self, board_name):
            json_src = os.path.join("build", board_name, "csr.json")
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))

            with open(json_src) as json_file, open(dts, "w") as dts_file:
                dts_content = generate_dts(json.load(json_file), polling=False)
                dts_file.write(dts_content)

        # DTS compilation --------------------------------------------------------------------------
        def compile_dts(self, board_name, symbols=False):
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            dtb = os.path.join("build", board_name, "{}.dtb".format(board_name))
            subprocess.check_call(
                "dtc {} -O dtb -o {} {}".format("-@" if symbols else "", dtb, dts), shell=True)

        # DTB combination --------------------------------------------------------------------------
        def combine_dtb(self, board_name, overlays=""):
            dtb_in = os.path.join("build", board_name, "{}.dtb".format(board_name))
            dtb_out = os.path.join("images", "rv32.dtb")
            if overlays == "":
                shutil.copyfile(dtb_in, dtb_out)
            else:
                subprocess.check_call(
                    "fdtoverlay -i {} -o {} {}".format(dtb_in, dtb_out, overlays), shell=True)

        # Documentation generation -----------------------------------------------------------------
        def generate_doc(self, board_name):
            from litex.soc.doc import generate_docs
            doc_dir = os.path.join("build", board_name, "doc")
            generate_docs(self, doc_dir)
            os.system("sphinx-build -M html {}/ {}/_build".format(doc_dir, doc_dir))

    return _SoCLinux(**kwargs)
