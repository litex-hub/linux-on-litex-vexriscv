#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2024, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import os
import json
import shutil
import subprocess

from migen import *

from litex.soc.interconnect.csr import *

from litex.soc.cores.cpu.vexriscv_smp import VexRiscvSMP
from litex.soc.cores.gpio    import GPIOOut, GPIOIn
from litex.soc.cores.spi     import SPIMaster
from litex.soc.cores.bitbang import I2CMaster
from litex.soc.cores.pwm     import PWM

from litex.tools.litex_json2dts_linux import generate_dts

# SoCLinux -----------------------------------------------------------------------------------------

def SoCLinux(soc_cls, **kwargs):
    class _SoCLinux(soc_cls):
        def __init__(self, **kwargs):

            # SoC ----------------------------------------------------------------------------------

            soc_cls.__init__(self, cpu_type="vexriscv_smp", cpu_variant="linux", **kwargs)

        # RGB Led ----------------------------------------------------------------------------------

        def add_rgb_led(self):
            rgb_led_pads = self.platform.request("rgb_led", 0)
            for n in "rgb":
                self.add_module(name=f"rgb_led_{n}0", module=PWM(getattr(rgb_led_pads, n)))

        # Switches ---------------------------------------------------------------------------------

        def add_switches(self):
            self.switches = GPIOIn(Cat(self.platform.request_all("user_sw")), with_irq=True)
            self.irq.add("switches")

        # SPI --------------------------------------------------------------------------------------

        def add_spi(self, data_width, clk_freq):
            spi_pads = self.platform.request("spi")
            self.spi = SPIMaster(spi_pads, data_width, self.clk_freq, clk_freq)

        # I2C --------------------------------------------------------------------------------------

        def add_i2c(self):
            self.i2c0 = I2CMaster(self.platform.request("i2c", 0))

        # Ethernet configuration -------------------------------------------------------------------

        def configure_ethernet(self, remote_ip, local_ip, use_gateway, gateway_ip, subnet_mask):
            remote_ip = remote_ip.split(".")
            local_ip = local_ip.split(".")
            gateway_ip = gateway_ip.split(".")
            subnet_mask = subnet_mask.split(".")

            try: # FIXME: Improve.
                self.constants.pop("REMOTEIP1")
                self.constants.pop("REMOTEIP2")
                self.constants.pop("REMOTEIP3")
                self.constants.pop("REMOTEIP4")
            except:
                pass
            self.add_constant("REMOTEIP1", int(remote_ip[0]))
            self.add_constant("REMOTEIP2", int(remote_ip[1]))
            self.add_constant("REMOTEIP3", int(remote_ip[2]))
            self.add_constant("REMOTEIP4", int(remote_ip[3]))

            try: # FIXME: Improve.
                self.constants.pop("LOCALIP1")
                self.constants.pop("LOCALIP2")
                self.constants.pop("LOCALIP3")
                self.constants.pop("LOCALIP4")
            except:
                pass
            self.add_constant("LOCALIP1", int(local_ip[0]))
            self.add_constant("LOCALIP2", int(local_ip[1]))
            self.add_constant("LOCALIP3", int(local_ip[2]))
            self.add_constant("LOCALIP4", int(local_ip[3]))

            try: # FIXME: Improve.
                self.constants.pop("GATEWAYIP1")
                self.constants.pop("GATEWAYIP2")
                self.constants.pop("GATEWAYIP3")
                self.constants.pop("GATEWAYIP4")
            except:
                pass
            self.add_constant("GATEWAYIP1", int(gateway_ip[0]))
            self.add_constant("GATEWAYIP2", int(gateway_ip[1]))
            self.add_constant("GATEWAYIP3", int(gateway_ip[2]))
            self.add_constant("GATEWAYIP4", int(gateway_ip[3]))

            try: # FIXME: Improve.
                self.constants.pop("SUBNETMASK1")
                self.constants.pop("SUBNETMASK2")
                self.constants.pop("SUBNETMASK3")
                self.constants.pop("SUBNETMASK4")
            except:
                pass
            self.add_constant("SUBNETMASK1", int(subnet_mask[0]))
            self.add_constant("SUBNETMASK2", int(subnet_mask[1]))
            self.add_constant("SUBNETMASK3", int(subnet_mask[2]))
            self.add_constant("SUBNETMASK4", int(subnet_mask[3]))

            if use_gateway:
                self.add_constant("ETH_NETBOOT_USE_GATEWAY")

        # DTS generation ---------------------------------------------------------------------------

        def generate_dts(self, board_name, rootfs="ram0"):
            json_src = os.path.join("build", board_name, "csr.json")
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            initrd = "enabled" if rootfs == "ram0" else "disabled"

            with open(json_src) as json_file, open(dts, "w") as dts_file:
                dts_content = generate_dts(json.load(json_file),
                    initrd      = initrd,
                    polling     = False,
                    root_device = rootfs
                )
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
