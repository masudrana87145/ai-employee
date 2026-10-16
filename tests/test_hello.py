"""Tests for the hello greeting CLI."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from hello import greet, main


class TestGreet(unittest.TestCase):
    def test_greet_rana(self) -> None:
        self.assertEqual(greet("Rana"), "Hello Rana")

    def test_greet_other_name(self) -> None:
        self.assertEqual(greet("Ada"), "Hello Ada")

    def test_greet_strips_whitespace(self) -> None:
        self.assertEqual(greet("  Rana  "), "Hello Rana")

    def test_greet_rejects_empty(self) -> None:
        with self.assertRaises(ValueError):
            greet("   ")

    def test_main_prints_hello_rana(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = main(["Rana"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "Hello Rana\n")

    def test_main_rejects_blank_name(self) -> None:
        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            exit_code = main(["   "])
        self.assertEqual(exit_code, 2)
        self.assertIn("name must not be empty", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
