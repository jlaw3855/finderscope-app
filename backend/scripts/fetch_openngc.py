#!/usr/bin/env python3
"""Download OpenNGC NGC.csv into backend/data/openngc/."""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

OPENNGC_CSV_URL = (
    "https://raw.githubusercontent.com/mattiaverga/OpenNGC/master/database_files/NGC.csv"
)
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1] / "data" / "openngc" / "NGC.csv"
)


def fetch_openngc(output_path: Path = DEFAULT_OUTPUT) -> Path:
    """Download NGC.csv and return the output path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(OPENNGC_CSV_URL, output_path)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download OpenNGC NGC.csv catalog.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    path = fetch_openngc(args.output)
    print(f"Downloaded OpenNGC catalog to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
