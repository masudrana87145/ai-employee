"""Print a greeting for a name passed as a command-line argument."""

from __future__ import annotations

import argparse
import sys


def greet(name: str) -> str:
    """Return a greeting for *name*.

    Example:
        >>> greet("Rana")
        'Hello Rana'
    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    return f"Hello {cleaned}"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print a greeting for the given name.",
    )
    parser.add_argument("name", help="Name to greet")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        print(greet(args.name))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
