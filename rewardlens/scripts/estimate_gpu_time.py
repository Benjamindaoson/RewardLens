#!/usr/bin/env python3
"""Estimate GPU hours from measured throughput. No guessed constants unless --allow-placeholder-throughput."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--throughput-json", default=os.path.join(PROJECT, "outputs", "gpu_qualification_report.json"))
    parser.add_argument("--items-per-sec", type=float, default=None)
    parser.add_argument("--sec-per-judgment", type=float, default=None)
    parser.add_argument("--load-seconds", type=float, default=0.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--probe-items", type=int, default=None)
    parser.add_argument("--signal-items", type=int, default=None)
    parser.add_argument("--audit-items", type=int, default=None)
    parser.add_argument("--gqa-static-items", type=int, default=None)
    parser.add_argument("--gqa-bon-items", type=int, default=None)
    parser.add_argument("--n-pool", type=int, default=8)
    parser.add_argument("--n-models", type=int, default=8)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--price-rmb-per-gpu-hour", type=float, default=5.59)
    parser.add_argument("--allow-placeholder-throughput", action="store_true")
    parser.add_argument("--out", default=None)
    return parser.parse_args()


def count_jsonl(path: str) -> int:
    return len(read_jsonl(path)) if os.path.isfile(path) else 0


def estimate_seconds(n_forwards: int, items_per_sec: float, load_seconds: float, n_models: int) -> float:
    compute = n_forwards / items_per_sec if items_per_sec else float("inf")
    return compute + load_seconds * n_models


def main() -> int:
    args = parse_args()
    thr = {}
    if os.path.isfile(args.throughput_json):
        with open(args.throughput_json, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        thr = payload.get("throughput") or payload
    items_per_sec = args.items_per_sec
    if args.sec_per_judgment:
        items_per_sec = 1.0 / args.sec_per_judgment
    items_per_sec = items_per_sec or thr.get("items_per_sec") or thr.get("items/sec")
    if not items_per_sec and args.allow_placeholder_throughput:
        items_per_sec = None
    signal_dir = os.path.join(PROJECT, "outputs", "signal_gate_v1")
    fast_dir = os.path.join(PROJECT, "outputs", "fast_track_audit_v1")
    derived = os.path.join(PROJECT, "datasets", "gqa", "derived")
    combined = os.path.join(PROJECT, "datasets", "processed", "fast_eval")
    tally = os.path.join(PROJECT, "datasets", "tallyqa", "derived")
    probe_n = args.probe_items if args.probe_items is not None else (
        count_jsonl(os.path.join(signal_dir, "compatibility_probe_manifest.jsonl"))
        or count_jsonl(os.path.join(fast_dir, "compatibility_probe_manifest.jsonl"))
        or 50
    )
    signal_n = args.signal_items if args.signal_items is not None else (
        count_jsonl(os.path.join(signal_dir, "signal_gate_manifest.jsonl")) or 1200
    )
    audit_n = args.audit_items if args.audit_items is not None else (
        count_jsonl(os.path.join(fast_dir, "audit_manifest.jsonl")) or 2400
    )
    gqa_static_n = args.gqa_static_items if args.gqa_static_items is not None else (
        count_jsonl(os.path.join(combined, "static_manifest.jsonl"))
        or (
            count_jsonl(os.path.join(tally, "tallyqa_count_static_manifest.jsonl"))
            + count_jsonl(os.path.join(derived, "gqa_static_manifest.jsonl"))
        )
        or 800
    )
    gqa_bon_n = args.gqa_bon_items if args.gqa_bon_items is not None else (
        count_jsonl(os.path.join(combined, "downstream_manifest.jsonl"))
        or (
            count_jsonl(os.path.join(tally, "tallyqa_count_downstream_manifest.jsonl"))
            + count_jsonl(os.path.join(derived, "gqa_downstream_manifest.jsonl"))
        )
        or 800
    )
    counts = {
        "compatibility_probe": {"items": probe_n, "candidates": 1},
        "signal_gate": {"items": signal_n, "candidates": 1},
        "full_controlled_audit": {"items": audit_n, "candidates": 1},
        "gqa_static": {"items": gqa_static_n, "candidates": 1},
        "gqa_bon": {"items": gqa_bon_n, "candidates": args.n_pool},
    }
    if not items_per_sec:
        payload = {
            "status": "MISSING_THROUGHPUT",
            "note": "Run gpu_qualification.sh on A800. Refusing to invent hours.",
            "counts": counts,
            "n_models": args.n_models,
            "num_workers": args.num_workers,
            "price_rmb_per_gpu_hour": args.price_rmb_per_gpu_hour,
            "batch_size": args.batch_size,
            "load_seconds": args.load_seconds,
        }
        print(json.dumps(payload, indent=2))
        if args.out:
            write_json(args.out, payload)
        return 2
    per_model = {}
    for name, spec in counts.items():
        forwards = spec["items"] * spec["candidates"]
        seconds = forwards / float(items_per_sec) + args.load_seconds
        per_model[name] = {
            "status": "OK",
            "items": spec["items"],
            "candidates_per_item": spec["candidates"],
            "forwards": forwards,
            "seconds": seconds,
            "hours": seconds / 3600.0,
        }
    gpu_hours = sum(v["hours"] for v in per_model.values()) * args.n_models
    wall = {}
    for n_workers in (1, 2, 3):
        wall[str(n_workers)] = {
            "gpu_hours": gpu_hours,
            "wall_hours": gpu_hours / n_workers,
            "cost_rmb": gpu_hours * args.price_rmb_per_gpu_hour,
        }
    payload = {
        "status": "OK",
        "items_per_sec": items_per_sec,
        "sec_per_judgment": 1.0 / items_per_sec,
        "batch_size": args.batch_size,
        "load_seconds": args.load_seconds,
        "n_models": args.n_models,
        "num_workers_requested": args.num_workers,
        "price_rmb_per_gpu_hour": args.price_rmb_per_gpu_hour,
        "per_model": per_model,
        "total_gpu_hours": gpu_hours,
        "wall_clock": wall,
        "signal_eta_hours": (per_model["compatibility_probe"]["hours"] + per_model["signal_gate"]["hours"]) * args.n_models / max(args.num_workers, 1),
        "full_audit_eta_hours": per_model["full_controlled_audit"]["hours"] * args.n_models / max(args.num_workers, 1),
        "static_eta_hours": per_model["gqa_static"]["hours"] * args.n_models / max(args.num_workers, 1),
        "bon_eta_hours": per_model["gqa_bon"]["hours"] * args.n_models / max(args.num_workers, 1),
        "estimated_autodl_cost_rmb": gpu_hours * args.price_rmb_per_gpu_hour,
        "policy": "Throughput must be measured. Price is configurable (default 5.59 RMB/GPU-hour).",
    }
    print(json.dumps(payload, indent=2))
    if args.out:
        write_json(args.out, payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
