"""Arithmetic operations called by function name, then two integers."""

from __future__ import annotations

import argparse
import sys

SUPPORTED_FUNCTIONS: dict[str, str] = {
    "add": "Add two numbers",
    "mult": "Multiply two numbers",
    "sub": "Subtract the second number from the first",
    "div": "Divide the first number by the second",
}


def add(arg1: int, arg2: int) -> int:
    """Return the sum of *arg1* and *arg2*."""
    return arg1 + arg2


def mult(arg1: int, arg2: int) -> int:
    """Return the product of *arg1* and *arg2*."""
    return arg1 * arg2


def sub(arg1: int, arg2: int) -> int:
    """Return *arg1* minus *arg2*."""
    return arg1 - arg2


def div(arg1: int, arg2: int) -> float:
    """Return *arg1* divided by *arg2*.

    Raises ``ValueError`` when *arg2* is zero.
    """
    if arg2 == 0:
        raise ValueError("Cannot divide by zero")
    return arg1 / arg2


def calculate(function_name: str, arg1: int, arg2: int) -> int | float:
    """Run *function_name* on *arg1* and *arg2*.

    *function_name* may be any letter case. Unknown names raise ``ValueError``.
    """
    name = function_name.strip().lower()
    if name == "add":
        return add(arg1, arg2)
    if name == "mult":
        return mult(arg1, arg2)
    if name == "sub":
        return sub(arg1, arg2)
    if name == "div":
        return div(arg1, arg2)
    shown = function_name.strip() or function_name
    valid = ", ".join(
        f"{function} ({purpose})" for function, purpose in SUPPORTED_FUNCTIONS.items()
    )
    raise ValueError(f"Unsupported function '{shown}'. Valid functions: {valid}.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run add, mult, sub, or div. Pass the function name, then arg1 and arg2.",
    )
    parser.add_argument("function_name", help="Function name: add, mult, sub, or div")
    parser.add_argument("arg1", type=int, help="First integer")
    parser.add_argument("arg2", type=int, help="Second integer")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = calculate(args.function_name, args.arg1, args.arg2)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
