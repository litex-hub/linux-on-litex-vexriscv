#
# This file is part of Linux-on-LiteX-VexRiscv.
#
# Copyright (c) 2026 Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import subprocess
import sys
import unittest


class TestSWDDebugArguments(unittest.TestCase):
    def test_board_without_swd_pmod_is_rejected(self):
        result = subprocess.run(
            [sys.executable, "make.py", "--board=arty_s7", "--with-swd-debug"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--with-swd-debug is only supported on", result.stderr)

    def test_old_litex_is_rejected_before_building(self):
        result = subprocess.run(
            [sys.executable, "-c", "import make; make.LiteXSoC = object; make.main()",
             "--board=arty", "--with-swd-debug"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires a newer LiteX", result.stderr)

    def test_swd_and_jtag_tap_are_exclusive(self):
        result = subprocess.run(
            [sys.executable, "make.py", "--board=arty", "--with-swd-debug", "--jtag-tap"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mutually exclusive", result.stderr)
