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

            video_framebuffer_fifo_depth = kwargs.pop("video_framebuffer_fifo_depth", None)
            if isinstance(video_framebuffer_fifo_depth, str):
                video_framebuffer_fifo_depth = int(video_framebuffer_fifo_depth, 0)
            self.video_framebuffer_fifo_depth = video_framebuffer_fifo_depth

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

        # Video ------------------------------------------------------------------------------------

        def add_video_framebuffer(self, *args, **kwargs):
            if self.video_framebuffer_fifo_depth is not None and len(args) < 6 and "fifo_depth" not in kwargs:
                kwargs["fifo_depth"] = self.video_framebuffer_fifo_depth
            return soc_cls.add_video_framebuffer(self, *args, **kwargs)

        # DTS generation ---------------------------------------------------------------------------

        def generate_dts(
            self,
            board_name,
            rootfs      = "ram0",
            nfs_server  = None,
            nfs_root    = None,
            nfs_options = None,
        ):
            json_src = os.path.join("build", board_name, "csr.json")
            dts = os.path.join("build", board_name, "{}.dts".format(board_name))
            if rootfs == "ram0":
                initrd = os.path.join("images", "rootfs.cpio")
                if not os.path.exists(initrd):
                    initrd = "enabled"
            else:
                initrd = "disabled"

            with open(json_src) as json_file, open(dts, "w") as dts_file:
                dts_content = generate_dts(json.load(json_file),
                    initrd      = initrd,
                    polling     = False,
                    root_device = rootfs
                )
                if rootfs == "nfs":
                    if nfs_server is None or nfs_root is None:
                        raise ValueError("nfs_server and nfs_root are required for NFS rootfs")
                    nfsroot = f"{nfs_server}:{nfs_root}"
                    if nfs_options:
                        nfsroot += f",{nfs_options}"
                    dts_content = dts_content.replace(
                        "rootwait root=/dev/nfs",
                        f"root=/dev/nfs nfsroot={nfsroot}",
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
