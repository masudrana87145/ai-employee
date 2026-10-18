"""Tests for the arithmetic function caller."""

from __future__ import annotations

import io
import unittest
from unittest.mock import patch

from arith import add, calculate, main, mult, sub


class TestFunctions(unittest.TestCase):
    def test_add(self) -> None:
        self.assertEqual(add(5, 4), 9)

    def test_mult(self) -> None:
        self.assertEqual(mult(5, 4), 20)

    def test_sub(self) -> None:
        self.assertEqual(sub(5, 4), 1)

    def test_sub_negative_result(self) -> None:
        self.assertEqual(sub(4, 5), -1)

    def test_zero_and_negative_operands(self) -> None:
        self.assertEqual(add(-2, 0), -2)


class TestCalculate(unittest.TestCase):
    def test_function_name_is_case_insensitive(self) -> None:
        self.assertEqual(calculate("ADD", 2, 3), 5)
        self.assertEqual(calculate("Mult", 2, 3), 6)
        self.assertEqual(calculate("sUb", 2, 3), -1)

    def test_function_name_whitespace_is_ignored(self) -> None:
        self.assertEqual(calculate("  add  ", 1, 1), 2)

    def test_unknown_function_lists_valid_functions(self) -> None:
        with self.assertRaises(ValueError) as caught:
            calculate("divide", 1, 2)
        message = str(caught.exception)
        self.assertIn("Unsupported function 'divide'", message)
        self.assertIn("add (Add two numbers)", message)
        self.assertIn("mult (Multiply two numbers)", message)
        self.assertIn("sub (Subtract the second number from the first)", message)

    def test_blank_function_name(self) -> None:
        with self.assertRaises(ValueError) as caught:
            calculate("   ", 1, 2)
        self.assertIn("Unsupported function", str(caught.exception))


class TestMain(unittest.TestCase):
    def test_main_add(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = main(["add", "5", "4"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "9\n")

    def test_main_mult(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = main(["mult", "5", "4"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "20\n")

    def test_main_sub(self) -> None:
        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            exit_code = main(["sub", "5", "4"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "1\n")

    def test_main_unknown_function(self) -> None:
        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            exit_code = main(["divide", "5", "4"])
        self.assertEqual(exit_code, 2)
        self.assertIn("Valid functions: add", stderr.getvalue())

    def test_main_rejects_non_integer(self) -> None:
        with (
            patch("sys.stderr", new_callable=io.StringIO),
            self.assertRaises(SystemExit) as caught,
        ):
            main(["add", "5.5", "4"])
        self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
