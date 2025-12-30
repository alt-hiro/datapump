"""Command-line interface for datapump."""

from __future__ import annotations

import argparse

from datapump.commands.run import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datapump")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a datapump job")
    run_parser.set_defaults(handler=run)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.error("No command specified")

    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
