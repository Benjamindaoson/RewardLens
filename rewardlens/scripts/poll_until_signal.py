#!/usr/bin/env python3
"""Poll QC/PNG until SIGNAL_GATE_V1 can freeze. Does not stop Blender."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.freeze_controlled import SCALE_DIRS  # noqa: E402

SIGNAL_HASH = os.path.join(PROJECT, "outputs", "signal_gate_v1", "hashes.json")


def read_qc(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("summary") or payload
    except Exception:
        return {}


def snapshot() -> dict:
    out = {}
    for factor, directory in SCALE_DIRS.items():
        png_dir = os.path.join(directory, "images")
        n = len([name for name in os.listdir(png_dir) if name.endswith(".png")]) if os.path.isdir(png_dir) else 0
        qc = read_qc(os.path.join(directory, "qc_report.json"))
        out[factor] = {
            "PASS": int(qc.get("PASS") or 0),
            "BORDERLINE": int(qc.get("BORDERLINE") or 0),
            "FAIL": int(qc.get("FAIL") or 0),
            "png": n,
            "triplets": n // 3,
        }
    return out


def main() -> int:
    deadline = time.time() + 20 * 60
    freeze = os.path.join(ROOT, "scripts", "freeze_signal_gate.py")
    while time.time() < deadline:
        if os.path.isfile(SIGNAL_HASH):
            print("SIGNAL_READY hashes present", flush=True)
            return 0
        row = snapshot()
        for factor, rec in row.items():
            print("POLL", factor, rec, flush=True)
        passes = [row[f]["PASS"] for f in ("count", "attribute", "presence", "spatial")]
        print("MIN_PASS", min(passes), flush=True)
        if min(passes) >= 100:
            print("THRESHOLD_MET running freeze_signal_gate", flush=True)
            code = subprocess.run([sys.executable, freeze]).returncode
            print("FREEZE_CODE", code, flush=True)
            if code == 0 and os.path.isfile(SIGNAL_HASH):
                print("SIGNAL_READY", flush=True)
                return 0
        time.sleep(45)
    print("SIGNAL_STILL_WAITING", json.dumps(snapshot()), flush=True)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
