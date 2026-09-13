#!/usr/bin/env python3
"""Validate a GPU bundle. Extra checks on top of verify_bundle.py."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402


REQUIRED_ANALYSIS = [
    os.path.join("rewardlens", "configs", "rq2_analysis.json"),
    os.path.join("rewardlens", "configs", "rq3_analysis.json"),
    os.path.join("rewardlens", "scripts", "run_rq2_analysis.py"),
    os.path.join("rewardlens", "scripts", "run_rq3_analysis.py"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--mode", choices=["signal-gate", "fast-track"], default="signal-gate")
    parser.add_argument("--report", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = os.path.abspath(args.bundle)
    code = subprocess.run(
        [sys.executable, os.path.join(ROOT, "scripts", "verify_bundle.py"), "--bundle", bundle]
    ).returncode
    extra = []
    for rel in REQUIRED_ANALYSIS:
        if not os.path.isfile(os.path.join(bundle, rel)):
            extra.append("missing %s" % rel)
    sums = os.path.join(bundle, "SHA256SUMS.txt")
    if not os.path.isfile(sums):
        extra.append("SHA256SUMS.txt missing")
    if args.mode == "fast-track":
        if not os.path.isfile(os.path.join(PROJECT, "outputs", "fast_track_audit_v1", "hashes.json")):
            extra.append("FAST_TRACK_AUDIT_V1 not frozen")
    report = {
        "bundle": bundle,
        "mode": args.mode,
        "verify_bundle_exit": code,
        "extra_errors": extra,
        "status": "PASS" if code == 0 and not extra else "FAIL",
    }
    out = args.report or os.path.join(bundle, "bundle_validate.json")
    write_json(out, report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
