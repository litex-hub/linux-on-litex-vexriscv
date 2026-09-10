#
# This file is part of Linux-on-LiteX-VexRiscv.
#
# Copyright (c) 2026 Linux-on-LiteX-VexRiscv Developers
# SPDX-License-Identifier: BSD-2-Clause

import subprocess
import sys
import unittest


class TestJTAGDebugArguments(unittest.TestCase):
    def test_old_litex_is_rejected_before_building(self):
        result = subprocess.run(
            [sys.executable, "-c", "import make; make.LiteXSoC = object; make.main()",
             "--board=arty", "--with-privileged-debug", "--with-cpu-jtag-debug"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("requires a newer LiteX", result.stderr)

    def test_invalid_debug_combinations_fail_before_building(self):
        cases = [
            (["--with-cpu-jtag-debug"], "requires --with-privileged-debug"),
            (["--with-cpu-jtag-debug", "--with-privileged-debug", "--jtag-tap"],
             "cannot be combined with --jtag-tap"),
            (["--cpu-jtag-debug-chain=5"], "invalid choice"),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, "make.py", "--board=arty", *args],
                    capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected, result.stderr)

    def test_help_exposes_transport_options(self):
        result = subprocess.run(
            [sys.executable, "make.py", "--help"],
            capture_output=True, text=True, check=True,
        )
        for option in ["--with-cpu-jtag-debug", "--cpu-jtag-debug-chain", "--cpu-jtag-debug-clk-freq"]:
            self.assertIn(option, result.stdout)
