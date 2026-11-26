"""The `scribe` command."""

import argparse

from scribe import __version__


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scribe",
        description="Takes a module from idea to published design, tracks its work, "
        "presents the system as a site, and sets up each piece of coding.",
    )
    p.add_argument("--version", action="version", version=f"scribe {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    parser().parse_args(argv)
    return 0
