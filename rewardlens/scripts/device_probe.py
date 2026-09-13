#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.device import format_probe_text, probe_device, write_probe  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    report = probe_device()
    print(format_probe_text(report))
    if args.out:
        write_probe(args.out, report)
        print("WROTE", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
