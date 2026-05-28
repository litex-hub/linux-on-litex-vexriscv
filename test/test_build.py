#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2024, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil
import tempfile
import unittest
import subprocess

from make import (
    generate_buildroot_defconfig,
    get_buildroot_base_defconfig,
    get_buildroot_config_overrides,
    supported_boards,
)

class TestBuild(unittest.TestCase):
    def board_build_test(
        self, board, cpu_count=1, extra_args=None,
        expected_base=None, expected_overrides=None):
        extra_args = extra_args or []

        # Build Board software/gateware.
        shutil.rmtree("build", ignore_errors=True)
        subprocess.run(
            [
                "./make.py",
                f"--board={board}",
                f"--cpu-count={cpu_count}",
                *extra_args,
            ],
            check=True,
        )

        # Check .csv/.json generation.
        self.assertEqual(os.path.isfile(f"build/{board}/csr.csv"),  True)
        self.assertEqual(os.path.isfile(f"build/{board}/csr.json"), True)

        # Check Software generation.
        self.assertEqual(os.path.isfile(f"build/{board}/{board}.dts"), True)
        self.assertEqual(os.path.isfile(f"build/{board}/software/include/generated/csr.h"), True)
        self.assertEqual(os.path.isfile(f"build/{board}/software/bios/bios.bin"),           True)

        # Check Gateware generation
        self.assertEqual(os.path.isfile(f"build/{board}/gateware/{board}.v"), True)

        # Check Buildroot defconfig selection.
        self.assertEqual(os.path.isfile(f"build/{board}/buildroot_defconfig"), True)
        with open(f"build/{board}/buildroot_defconfig", encoding="utf-8") as f:
            generated_defconfig = f.read()
        if expected_base is not None:
            base_filename = f"buildroot/configs/{expected_base}"
            with open(base_filename, encoding="utf-8") as f:
                base_defconfig = f.read().rstrip()
            if not expected_overrides:
                self.assertEqual(generated_defconfig, base_defconfig + "\n")
        for override in expected_overrides or []:
            self.assertIn(override, generated_defconfig)

    def test_buildroot_defconfigs(self):
        configs = [
            (False, False, False, False, "litex_vexriscv_defconfig"),
            (False, True,  False, False, "litex_vexriscv_defconfig"),
            (False, False, True,  False, "litex_vexriscv_defconfig"),
            (False, True,  True,  False, "litex_vexriscv_defconfig"),
            (True,  False, False, False, "litex_vexriscv_defconfig"),
            (True,  True,  False, False, "litex_vexriscv_defconfig"),
            (True,  False, True,  False, "litex_vexriscv_defconfig"),
            (True,  True,  True,  False, "litex_vexriscv_defconfig"),
            (False, False, False, True,  "litex_vexriscv_defconfig"),
            (False, True,  False, True,  "litex_vexriscv_defconfig"),
            (False, False, True,  True,  "litex_vexriscv_defconfig"),
            (False, True,  True,  True,  "litex_vexriscv_defconfig"),
            (True,  False, False, True,  "litex_vexriscv_defconfig"),
            (True,  True,  False, True,  "litex_vexriscv_defconfig"),
            (True,  False, True,  True,  "litex_vexriscv_defconfig"),
            (True,  True,  True,  True,  "litex_vexriscv_defconfig"),
        ]
        for with_usb_host, with_aes, with_fpu, with_nfs_root, expected_base in configs:
            with self.subTest(
                base          = expected_base,
                with_usb_host = with_usb_host,
                with_aes      = with_aes,
                with_fpu      = with_fpu,
                with_nfs_root = with_nfs_root,
            ):
                with tempfile.TemporaryDirectory() as tmpdir:
                    generated = os.path.join(tmpdir, "buildroot_defconfig")
                    base = generate_buildroot_defconfig(
                        filename      = generated,
                        with_usb_host = with_usb_host,
                        with_aes      = with_aes,
                        with_fpu      = with_fpu,
                        with_nfs_root = with_nfs_root,
                    )
                    self.assertEqual(base, expected_base)
                    self.assertEqual(get_buildroot_base_defconfig(), expected_base)

                    with open(f"buildroot/configs/{expected_base}", encoding="utf-8") as f:
                        base_defconfig = f.read().rstrip()
                    with open(generated, encoding="utf-8") as f:
                        generated_defconfig = f.read()
                    if not with_usb_host and not with_aes and not with_fpu and not with_nfs_root:
                        self.assertEqual(generated_defconfig, base_defconfig + "\n")
                    for override in get_buildroot_config_overrides(
                        with_usb_host = with_usb_host,
                        with_aes      = with_aes,
                        with_fpu      = with_fpu,
                        with_nfs_root = with_nfs_root,
                    ):
                        self.assertIn(override, generated_defconfig)
                    if with_fpu:
                        self.assertNotIn("\nBR2_RISCV_ABI_ILP32=y\n", "\n" + generated_defconfig)
                    if not with_aes:
                        self.assertNotIn("\nBR2_PACKAGE_VEXRISCV_AES=y\n", "\n" + generated_defconfig)
                    if with_nfs_root:
                        self.assertIn("linux-nfsroot.config", generated_defconfig)
                        self.assertIn("\nBR2_TARGET_ROOTFS_TAR=y\n", "\n" + generated_defconfig)
                    if not with_fpu and not with_nfs_root:
                        self.assertNotIn("BR2_LINUX_KERNEL_CONFIG_FRAGMENT_FILES", generated_defconfig)

    def test_boards(self):
        excluded_boards = [
            "schoko",                   # USB OHCI netlist generation issue.
            "trion_t120bga576dev_kit",  # Reason: Require Efinity toolchain.
            "titanium_ti60f225dev_kit", # Reason: Require Efinity toolchain.
        ]
        # Allow CI matrix jobs to target a single board via $LLV_BOARD.
        single = os.environ.get("LLV_BOARD")
        if single:
            boards = [single]
        else:
            boards = [b for b in supported_boards if b not in excluded_boards]
        for board in boards:
            with self.subTest(msg=f"board={board} build test..."):
                board_info = supported_boards[board]()
                with_usb_host = "usb_host" in board_info.soc_capabilities
                expected_overrides = get_buildroot_config_overrides(
                    with_usb_host = with_usb_host,
                )
                self.board_build_test(
                    board              = board,
                    expected_base      = get_buildroot_base_defconfig(),
                    expected_overrides = expected_overrides,
                )

    def test_cpu_count(self):
        for cpu_count in [1, 2, 4]:
            with self.subTest(msg=f"cpu_count={cpu_count} build test..."):
                self.board_build_test(
                    board         = "arty",
                    cpu_count     = cpu_count,
                    expected_base = "litex_vexriscv_defconfig",
                )

    def test_cpu_variants(self):
        with self.subTest(msg="AES/FPU build test..."):
            self.board_build_test(
                board="arty",
                cpu_count=1,
                extra_args=[
                    "--aes-instruction=True",
                    "--with-fpu",
                    "--cpu-per-fpu=1",
                ],
                expected_base      = "litex_vexriscv_defconfig",
                expected_overrides = get_buildroot_config_overrides(
                    with_aes = True,
                    with_fpu = True,
                ),
            )

    def test_nfs_rootfs(self):
        self.board_build_test(
            board="arty",
            cpu_count=1,
            extra_args=[
                "--rootfs=nfs",
                "--nfs-root=/srv/nfs/litex",
            ],
            expected_base      = "litex_vexriscv_defconfig",
            expected_overrides = get_buildroot_config_overrides(with_nfs_root=True),
        )

        with open("build/arty/arty.dts", encoding="utf-8") as f:
            dts = f.read()
        self.assertIn("root=/dev/nfs", dts)
        self.assertIn(
            "nfsroot=192.168.1.100:/srv/nfs/litex,vers=3,tcp,nolock",
            dts,
        )
        self.assertNotIn("linux,initrd-start", dts)

        with open("images/boot.json", encoding="utf-8") as f:
            boot = f.read()
        self.assertNotIn("rootfs.cpio", boot)

    def test_nfs_rootfs_requires_ethernet(self):
        result = subprocess.run(
            [
                "./make.py",
                "--board=arty_s7",
                "--rootfs=nfs",
            ],
            check=False,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not support Ethernet", result.stderr)
