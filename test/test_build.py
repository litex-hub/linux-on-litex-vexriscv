#
# This file is part of Linux-on-LiteX-VexRiscv
#
# Copyright (c) 2019-2024, Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil
import subprocess
import unittest

from make import supported_boards

class TestBuild(unittest.TestCase):
    def board_build_test(self, board, cpu_count=1):
        # Build Board software/gateware.
        shutil.rmtree("build", ignore_errors=True)
        subprocess.run(
            ["./make.py", f"--board={board}", f"--cpu-count={cpu_count}"],
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
                self.board_build_test(board=board)

    def test_cpu_count(self):
        for cpu_count in [1, 2, 4]:
            with self.subTest(msg=f"cpu_count={cpu_count} build test..."):
                self.board_build_test(board="arty", cpu_count=cpu_count)


