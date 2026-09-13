#!/usr/bin/env python3
"""Build a GPU bundle. Full P0 / FAST_TRACK mode refuses unless FAST_TRACK_AUDIT_V1 is frozen."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--signal-gate", action="store_true")
    parser.add_argument("--fast-track", action="store_true")
    parser.add_argument("--out", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.signal_gate and not args.fast_track:
        print("Specify --signal-gate and/or --fast-track", flush=True)
        return 2
    if args.signal_gate:
        existing = os.path.join(PROJECT, "gpu_bundle_signal_v1")
        out = args.out or existing
        if os.path.isdir(existing) and os.path.isfile(os.path.join(existing, "SHA256SUMS.txt")):
            print("SIGNAL_BUNDLE_EXISTS_NOT_REBUILT", existing, flush=True)
            code = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "validate_gpu_bundle.py"), "--bundle", existing, "--mode", "signal-gate"]
            ).returncode
            if code != 0:
                return code
        else:
            env = os.environ.copy()
            env["REWARDLENS_BUNDLE_MANIFEST_ROOT"] = os.path.join(PROJECT, "outputs", "signal_gate_v1")
            code = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "assemble_gpu_bundle.py"), "--out", out],
                env=env,
            ).returncode
            if code != 0:
                return code
            subprocess.run(
                [
                    sys.executable,
                    os.path.join(ROOT, "scripts", "write_sha256sums.py"),
                    "--root",
                    out,
                    "--out",
                    os.path.join(out, "SHA256SUMS.txt"),
                ]
            )
            code = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scripts", "validate_gpu_bundle.py"), "--bundle", out, "--mode", "signal-gate"]
            ).returncode
            if code != 0:
                return code
    if args.fast_track:
        hashes = os.path.join(PROJECT, "outputs", "fast_track_audit_v1", "hashes.json")
        if not os.path.isfile(hashes):
            print("REFUSE_FULL_P0_BUNDLE FAST_TRACK_AUDIT_V1 != FROZEN", flush=True)
            return 3
        out = args.out or os.path.join(PROJECT, "gpu_bundle_fast_v1")
        env = os.environ.copy()
        env["REWARDLENS_BUNDLE_MANIFEST_ROOT"] = os.path.join(PROJECT, "outputs", "fast_track_audit_v1")
        code = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "assemble_gpu_bundle.py"), "--out", out],
            env=env,
        ).returncode
        if code != 0:
            return code
        subprocess.run(
            [
                sys.executable,
                os.path.join(ROOT, "scripts", "write_sha256sums.py"),
                "--root",
                out,
                "--out",
                os.path.join(out, "SHA256SUMS.txt"),
            ]
        )
        return subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "validate_gpu_bundle.py"), "--bundle", out, "--mode", "fast-track"]
        ).returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
