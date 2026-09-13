#!/usr/bin/env python3
"""Poll until 100 PASS/factor then freeze SIGNAL_GATE_V1. Independent of GQA image download."""

from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> int:
    interval = 120
    while True:
        code = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "freeze_signal_gate.py")]
        ).returncode
        if code == 0:
            signal_dir = os.path.join(PROJECT, "outputs", "signal_gate_v1")
            subprocess.run(
                [
                    sys.executable,
                    os.path.join(ROOT, "scripts", "build_compatibility_probe.py"),
                    "--audit-manifest",
                    os.path.join(signal_dir, "signal_gate_manifest.jsonl"),
                    "--out-dir",
                    signal_dir,
                    "--probe-judgments",
                    "50",
                    "--copy-signal-alias",
                ]
            )
            env = os.environ.copy()
            env["REWARDLENS_BUNDLE_MANIFEST_ROOT"] = signal_dir
            subprocess.run(
                [
                    sys.executable,
                    os.path.join(ROOT, "scripts", "assemble_gpu_bundle.py"),
                    "--out",
                    os.path.join(PROJECT, "gpu_bundle_signal_v1"),
                    "--manifest-root",
                    signal_dir,
                ],
                env=env,
            )
            print("SIGNAL_WATCHER_DONE", flush=True)
            return 0
        print("SIGNAL_WATCHER_WAIT", flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
