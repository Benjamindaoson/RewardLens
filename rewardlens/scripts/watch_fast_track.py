#!/usr/bin/env python3
"""Poll until each factor hits 200 PASS (freeze immediately), then FAST_TRACK_AUDIT_V1.

Does not stop Blender. Does not modify SIGNAL_GATE_V1.
Does not assemble a full P0 bundle until FAST_TRACK_AUDIT_V1 is frozen.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-sec", type=int, default=180)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    freeze = os.path.join(ROOT, "scripts", "freeze_fast_track.py")
    snapshot = os.path.join(ROOT, "scripts", "snapshot_blender.py")
    sample = os.path.join(ROOT, "scripts", "sample_gpu_subsets.py")
    bundle = os.path.join(ROOT, "scripts", "build_gpu_bundle.py")
    while True:
        subprocess.run([sys.executable, snapshot])
        proc = subprocess.run([sys.executable, freeze])
        if proc.returncode == 0:
            fast_dir = os.path.join(PROJECT, "outputs", "fast_track_audit_v1")
            subprocess.run(
                [
                    sys.executable,
                    sample,
                    "--audit-manifest",
                    os.path.join(fast_dir, "audit_manifest.jsonl"),
                    "--out-dir",
                    fast_dir,
                    "--per-factor",
                    "100",
                    "--probe-judgments",
                    "50",
                ]
            )
            bundle_code = subprocess.run([sys.executable, bundle, "--fast-track"]).returncode
            verify = os.path.join(ROOT, "scripts", "verify_bundle.py")
            verify_code = subprocess.run(
                [sys.executable, verify, "--bundle", os.path.join(PROJECT, "gpu_bundle_fast_v1")]
            ).returncode
            print("GPU_BUNDLE_FAST_V1", "PASS" if bundle_code == 0 and verify_code == 0 else "FAIL", flush=True)
            print("FAST_TRACK_WATCH_DONE", flush=True)
            return 0 if bundle_code == 0 and verify_code == 0 else 1
        if args.once:
            return proc.returncode
        print("sleep", args.interval_sec, flush=True)
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
