"""The `scribe` command."""

import argparse
from pathlib import Path

from scribe import __version__
from scribe.check import check


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scribe",
        description="Takes a module from idea to published design, tracks its work, "
        "presents the system as a site, and sets up each piece of coding.",
    )
    p.add_argument("--version", action="version", version=f"scribe {__version__}")
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("check", help="refuse docs that do not match scribe's schema")
    c.add_argument("repo", nargs="?", default=".", type=Path, help="the repo's root, holding scribe.toml")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "check":
        findings = check(args.repo.resolve())
        for f in findings:
            print(f)
        return 1 if findings else 0
    return 0
