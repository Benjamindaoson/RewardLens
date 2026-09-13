#!/usr/bin/env python3
"""Poll renders + GQA. Freeze SIGNAL at 100 PASS/factor, FAST_TRACK at 200. Do not stop Blender."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.freeze_controlled import FACTORS, freeze_pass_subset, incremental_qc_factor, SCALE_DIRS  # noqa: E402


def run(cmd: list[str]) -> int:
    print("RUN", " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


def write_readiness(states: dict) -> None:
    path = os.path.join(PROJECT, "outputs", "readiness_status.json")
    write_json(path, {"updated_at": datetime.now(timezone.utc).isoformat(), "states": states})


def sample_probe(signal_dir: str) -> None:
    manifest = os.path.join(signal_dir, "signal_gate_manifest.jsonl")
    run(
        [
            sys.executable,
            os.path.join(ROOT, "scripts", "build_compatibility_probe.py"),
            "--audit-manifest",
            manifest,
            "--out-dir",
            signal_dir,
            "--probe-judgments",
            "50",
            "--copy-signal-alias",
        ]
    )


def maybe_gqa() -> str:
    zip_path = os.path.join(PROJECT, "datasets", "gqa", "questions1.2.zip")
    expected = 1498616372
    if not os.path.isfile(zip_path):
        return "WAITING"
    size = os.path.getsize(zip_path)
    if size < expected:
        return "WAITING"
    derived = os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl")
    if os.path.isfile(derived):
        return "PASS"
    code = run([sys.executable, os.path.join(ROOT, "scripts", "process_gqa_fast.py"), "--skip-images"])
    return "PASS" if code == 0 else "FAIL"


def rebuild_bundle(kind: str) -> None:
    out = os.path.join(PROJECT, "gpu_bundle_signal_v1" if kind == "signal" else "gpu_bundle_fast_v1")
    cmd = [sys.executable, os.path.join(ROOT, "scripts", "assemble_gpu_bundle.py"), "--out", out]
    if kind == "signal":
        os.environ["REWARDLENS_BUNDLE_MANIFEST_ROOT"] = os.path.join(PROJECT, "outputs", "signal_gate_v1")
    else:
        os.environ["REWARDLENS_BUNDLE_MANIFEST_ROOT"] = os.path.join(PROJECT, "outputs", "fast_track_audit_v1")
    run(cmd)


def one_cycle(states: dict) -> dict:
    print("CYCLE", datetime.now(timezone.utc).isoformat(), flush=True)
    counts = {}
    for factor in FACTORS:
        summary, _ = incremental_qc_factor(factor, SCALE_DIRS[factor])
        counts[factor] = {
            "PASS": summary["PASS"],
            "BORDERLINE": summary["BORDERLINE"],
            "FAIL": summary["FAIL"],
            "n_qc": summary["n_qc"],
            "n_new": summary["n_new"],
            "n_incomplete": summary["n_incomplete"],
        }
        print("QC", factor, counts[factor], flush=True)
    write_json(os.path.join(PROJECT, "outputs", "dataset_status.json"), {"per_factor": counts, "updated_at": datetime.now(timezone.utc).isoformat()})

    min_pass = min(c["PASS"] for c in counts.values())
    signal_dir = os.path.join(PROJECT, "outputs", "signal_gate_v1")
    fast_dir = os.path.join(PROJECT, "outputs", "fast_track_audit_v1")
    signal_ready = os.path.isfile(os.path.join(signal_dir, "hashes.json"))
    fast_ready = os.path.isfile(os.path.join(fast_dir, "hashes.json"))

    if min_pass >= 100 and not signal_ready:
        result = freeze_pass_subset(
            version="SIGNAL_GATE_V1",
            n_pass=100,
            out_dir=signal_dir,
            manifest_name="signal_gate_manifest.jsonl",
        )
        if result.get("ready"):
            sample_probe(signal_dir)
            rebuild_bundle("signal")
            states["SIGNAL_DATA_READY"] = "PASS"
            print("FROZE SIGNAL_GATE_V1", result.get("n_items"), flush=True)
    elif signal_ready:
        states["SIGNAL_DATA_READY"] = "PASS"
    else:
        states["SIGNAL_DATA_READY"] = "WAITING"

    if min_pass >= 200 and not fast_ready:
        result = freeze_pass_subset(
            version="FAST_TRACK_AUDIT_V1",
            n_pass=200,
            out_dir=fast_dir,
            manifest_name="audit_manifest.jsonl",
        )
        if result.get("ready"):
            run(
                [
                    sys.executable,
                    os.path.join(ROOT, "scripts", "build_compatibility_probe.py"),
                    "--audit-manifest",
                    os.path.join(fast_dir, "audit_manifest.jsonl"),
                    "--out-dir",
                    fast_dir,
                    "--probe-judgments",
                    "50",
                ]
            )
            rebuild_bundle("fast")
            states["FAST_TRACK_DATA_READY"] = "PASS"
            print("FROZE FAST_TRACK_AUDIT_V1", result.get("n_items"), flush=True)
    elif fast_ready:
        states["FAST_TRACK_DATA_READY"] = "PASS"
    else:
        states["FAST_TRACK_DATA_READY"] = "WAITING"

    gqa = maybe_gqa()
    states["GQA_METADATA_READY"] = gqa if gqa != "PASS" else "PASS"
    if gqa == "PASS":
        states["GQA_STATIC_READY"] = "PASS" if os.path.isfile(os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl")) else "WAITING"
        states["GQA_DOWNSTREAM_READY"] = "PASS" if os.path.isfile(os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_downstream_manifest.jsonl")) else "WAITING"
        inv = os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_image_inventory.json")
        if os.path.isfile(inv):
            payload = json.load(open(inv, encoding="utf-8"))
            states["GQA_IMAGES_READY"] = "PASS" if payload.get("n_missing") == 0 else "WAITING"
    tally_static = os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_count_static_manifest.jsonl")
    tally_down = os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_count_downstream_manifest.jsonl")
    states["TALLYQA_COUNT_STATIC_READY"] = "PASS" if os.path.isfile(tally_static) else "WAITING"
    states["TALLYQA_COUNT_DOWNSTREAM_READY"] = "PASS" if os.path.isfile(tally_down) else "WAITING"
    tally_inv = os.path.join(PROJECT, "datasets", "tallyqa", "derived", "tallyqa_image_inventory.json")
    if os.path.isfile(tally_inv):
        payload = json.load(open(tally_inv, encoding="utf-8"))
        states["TALLYQA_IMAGES_READY"] = "PASS" if payload.get("n_missing") == 0 else "WAITING"
    else:
        states["TALLYQA_IMAGES_READY"] = "WAITING"
    combined = os.path.join(PROJECT, "datasets", "processed", "fast_eval", "static_manifest.jsonl")
    states["COMBINED_FAST_EVAL_READY"] = "PASS" if os.path.isfile(combined) else "WAITING"
    write_readiness(states)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-sec", type=int, default=120)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--until-fast-track", action="store_true", default=True)
    args = parser.parse_args()
    states = {
        "LOCAL_CODE_READY": "PASS",
        "SIGNAL_DATA_READY": "WAITING",
        "FAST_TRACK_DATA_READY": "WAITING",
        "GQA_METADATA_READY": "WAITING",
        "GQA_STATIC_READY": "WAITING",
        "GQA_DOWNSTREAM_READY": "WAITING",
        "GQA_IMAGES_READY": "WAITING",
        "TALLYQA_COUNT_STATIC_READY": "WAITING",
        "TALLYQA_COUNT_DOWNSTREAM_READY": "WAITING",
        "TALLYQA_IMAGES_READY": "WAITING",
        "COMBINED_FAST_EVAL_READY": "WAITING",
        "GPU_BUNDLE_SIGNAL_READY": "WAITING",
        "GPU_BUNDLE_FULL_READY": "WAITING",
        "CLOUD_STAGE_PACKAGE_READY": "WAITING",
        "FULL_READY": "WAITING",
    }
    while True:
        counts = one_cycle(states)
        min_pass = min(c["PASS"] for c in counts.values()) if counts else 0
        if args.once:
            return 0 if min_pass >= 200 else 2
        if min_pass >= 200 and states.get("FAST_TRACK_DATA_READY") == "PASS":
            print("ORCHESTRATOR_FAST_TRACK_DONE", flush=True)
            if states.get("GQA_STATIC_READY") == "PASS":
                print("ORCHESTRATOR_CAN_IDLE_ON_GQA_IMAGES", flush=True)
            # keep looping for GQA until static+downstream exist
            if states.get("GQA_STATIC_READY") == "PASS" and states.get("GQA_DOWNSTREAM_READY") == "PASS":
                print("ORCHESTRATOR_DATA_DONE", flush=True)
                return 0
        time.sleep(args.interval_sec)


if __name__ == "__main__":
    raise SystemExit(main())
