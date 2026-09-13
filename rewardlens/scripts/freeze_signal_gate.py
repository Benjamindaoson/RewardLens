#!/usr/bin/env python3
"""Freeze SIGNAL_GATE_V1 when every factor has >=100 PASS triplets."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.freeze_controlled import freeze_pass_subset  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "outputs", "signal_gate_v1"))
    parser.add_argument("--n-pass", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = freeze_pass_subset(
        version="SIGNAL_GATE_V1",
        n_pass=args.n_pass,
        out_dir=os.path.abspath(args.out_dir),
        manifest_name="signal_gate_manifest.jsonl",
    )
    if not result.get("ready"):
        print("SIGNAL_GATE_NOT_READY", flush=True)
        return 2
    print("SIGNAL_GATE_FROZEN", result["out_dir"], "items", result.get("n_items"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
