#!/usr/bin/env python3
"""CPU finalize pipeline: QC -> freeze -> GPU subsets. Safe to re-run. Does not stop Blender."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)

SCALE = {
    "count": os.path.join(PROJECT, "outputs", "count_scale_v1"),
    "attribute": os.path.join(PROJECT, "outputs", "attribute_scale_v1"),
    "presence": os.path.join(PROJECT, "outputs", "presence_scale_v1"),
    "spatial": os.path.join(PROJECT, "outputs", "spatial_scale_v1"),
}


def run(cmd: list[str]) -> int:
    print("RUN", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd)
    return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    py = sys.executable
    qc_cmd = [py, os.path.join(ROOT, "scripts", "qc_controlled.py")]
    for path in SCALE.values():
        qc_cmd.extend(["--output-dir", path])
    code = run(qc_cmd)
    if code != 0:
        return code
    freeze = [py, os.path.join(ROOT, "scripts", "freeze_audit_dataset.py")]
    if args.require_complete:
        freeze.append("--require-complete")
    code = run(freeze)
    if code != 0:
        return code
    code = run([py, os.path.join(ROOT, "scripts", "sample_gpu_subsets.py")])
    if code != 0:
        return code
    code = run([py, os.path.join(ROOT, "scripts", "make_figure1.py")])
    if code != 0:
        print("FIGURE1_WARN", code, flush=True)
    code = run([py, os.path.join(ROOT, "scripts", "assemble_gpu_bundle.py")])
    print("FINALIZE_DONE", json.dumps({"ok": code == 0}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
