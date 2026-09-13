#!/usr/bin/env python3
"""Run one worker's model list. Independent resumable JSONL. No distributed training.

Partition is by model: --num-workers N --worker-index K, K in 0..N-1.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.registry import models_for_shard, models_for_worker  # noqa: E402

COMPAT_TIMEOUT_SEC = 40 * 60
STAGES = ("probe", "signal_gate", "full_audit", "gqa_static", "gqa_bon")


def first_existing(paths: list[str]) -> str:
    for path in paths:
        if os.path.isfile(path):
            return path
    return paths[-1]


def run_stage(stage: str, model_id: str, manifest: str, out_jsonl: str, timeout: int | None, images_root: str | None = None) -> dict:
    runner = {
        "probe": os.path.join(ROOT, "inference", "run_probe.py"),
        "signal_gate": os.path.join(ROOT, "inference", "run_signal_gate.py"),
        "full_audit": os.path.join(ROOT, "inference", "run_full_audit.py"),
        "gqa_static": os.path.join(ROOT, "inference", "run_static.py"),
        "gqa_bon": os.path.join(ROOT, "inference", "run_downstream.py"),
    }[stage]
    os.makedirs(os.path.dirname(os.path.abspath(out_jsonl)), exist_ok=True)
    env = os.environ.copy()
    env.setdefault("HF_HUB_OFFLINE", "1")
    env.setdefault("TRANSFORMERS_OFFLINE", "1")
    cmd = [
        sys.executable,
        runner,
        "--adapter",
        "hf",
        "--model-id",
        model_id,
        "--manifest",
        manifest,
        "--out-jsonl",
        out_jsonl,
    ]
    if images_root:
        cmd.extend(["--images-root", images_root])
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, timeout=timeout, env=env)
        code = proc.returncode
        status = "ok" if code == 0 else "failed"
    except subprocess.TimeoutExpired:
        code = 124
        status = "timeout_incompatible"
    return {
        "stage": stage,
        "model_id": model_id,
        "status": status,
        "returncode": code,
        "seconds": time.time() - t0,
        "out_jsonl": out_jsonl,
    }


def resolve_manifest_root(project: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    fast = os.path.join(project, "outputs", "fast_track_audit_v1")
    signal = os.path.join(project, "outputs", "signal_gate_v1")
    if os.path.isfile(os.path.join(fast, "audit_manifest.jsonl")):
        return fast
    if os.path.isfile(os.path.join(signal, "signal_gate_manifest.jsonl")):
        return signal
    return fast


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=int, default=None, help="legacy 0/1 using registry worker field")
    parser.add_argument("--worker-index", type=int, default=None)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--stage", default="all", choices=["all", *STAGES])
    parser.add_argument("--manifest-root", default=None)
    parser.add_argument("--out-root", default=None)
    parser.add_argument("--compat-timeout-sec", type=int, default=COMPAT_TIMEOUT_SEC)
    parser.add_argument("--online", action="store_true", help="do not force HF offline env")
    args = parser.parse_args()
    if args.online:
        os.environ.pop("HF_HUB_OFFLINE", None)
        os.environ.pop("TRANSFORMERS_OFFLINE", None)
    project = os.path.dirname(ROOT)
    worker_index = args.worker_index if args.worker_index is not None else (args.worker if args.worker is not None else 0)
    num_workers = args.num_workers if args.worker is None else 2
    manifest_root = resolve_manifest_root(project, args.manifest_root)
    out_root = args.out_root or os.path.join(project, "outputs", "runs", "worker_%d_of_%d" % (worker_index, num_workers))
    combined_static = first_existing(
        [
            os.path.join(project, "datasets", "processed", "fast_eval", "static_manifest.jsonl"),
            os.path.join(project, "manifests", "fast_eval", "static_manifest.jsonl"),
            os.path.join(project, "manifests", "static_manifest.jsonl"),
            os.path.join(project, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl"),
        ]
    )
    combined_down = first_existing(
        [
            os.path.join(project, "datasets", "processed", "fast_eval", "downstream_manifest.jsonl"),
            os.path.join(project, "manifests", "fast_eval", "downstream_manifest.jsonl"),
            os.path.join(project, "manifests", "downstream_manifest.jsonl"),
            os.path.join(project, "datasets", "gqa", "derived", "gqa_downstream_manifest.jsonl"),
        ]
    )
    images_root = None
    for candidate in (
        os.path.join(project, "gqa_images"),
        os.path.join(project, "datasets", "gqa", "images"),
        os.path.join(project, "images"),
    ):
        if os.path.isdir(candidate):
            images_root = candidate
            break
    manifests = {
        "probe": os.path.join(manifest_root, "compatibility_probe_manifest.jsonl"),
        "signal_gate": os.path.join(manifest_root, "gpu_signal_gate_manifest.jsonl")
        if os.path.isfile(os.path.join(manifest_root, "gpu_signal_gate_manifest.jsonl"))
        else os.path.join(manifest_root, "signal_gate_manifest.jsonl"),
        "full_audit": os.path.join(manifest_root, "audit_manifest.jsonl"),
        "gqa_static": combined_static,
        "gqa_bon": combined_down,
    }
    if args.worker is not None and args.worker_index is None:
        models = models_for_worker(args.worker)
    else:
        models = models_for_shard(worker_index, num_workers)
    stages = STAGES if args.stage == "all" else (args.stage,)
    log_path = os.path.join(out_root, "worker_log.jsonl")
    os.makedirs(out_root, exist_ok=True)
    print("WORKER", worker_index, "of", num_workers, "models", [m["model_id"] for m in models], flush=True)
    missing = [path for path in manifests.values() if not os.path.isfile(path)]
    if missing and args.stage in {"all", "probe", "signal_gate", "full_audit"}:
        print("MANIFEST_MISSING", missing, flush=True)
    for rec in models:
        model_id = rec["model_id"]
        probe_out = os.path.join(out_root, model_id, "probe.jsonl")
        probe = run_stage("probe", model_id, manifests["probe"], probe_out, args.compat_timeout_sec, images_root)
        append_log(log_path, probe)
        if probe["status"] != "ok":
            append_log(
                log_path,
                {
                    "model_id": model_id,
                    "status": "INCOMPATIBLE",
                    "reason": "compatibility probe did not finish cleanly within timeout",
                    "seconds": probe["seconds"],
                },
            )
            print("SKIP_INCOMPATIBLE", model_id, probe, flush=True)
            continue
        for stage in stages:
            if stage == "probe":
                continue
            out_jsonl = os.path.join(out_root, model_id, "%s.jsonl" % stage)
            result = run_stage(stage, model_id, manifests[stage], out_jsonl, None, images_root)
            append_log(log_path, result)
            print(json.dumps(result), flush=True)
    print("WORKER_DONE", worker_index, flush=True)
    return 0


def append_log(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")
        handle.flush()


if __name__ == "__main__":
    raise SystemExit(main())
