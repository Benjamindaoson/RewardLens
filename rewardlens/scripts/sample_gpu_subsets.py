#!/usr/bin/env python3
"""Deterministic GPU Signal Gate and compatibility probe subsets."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.hashutil import sha256_file  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402

FACTORS = ("count", "attribute", "presence", "spatial")
VARIANTS = ("base", "relevant", "irrelevant")


def sample_triplets(items: list[dict], n: int, seed: int) -> list[str]:
    by_factor: dict[str, list[str]] = {f: [] for f in FACTORS}
    for item in items:
        if item.get("qc_status") != "PASS":
            continue
        if item.get("variant") != "base":
            continue
        by_factor.setdefault(item["factor"], []).append(item["triplet_id"])
    rng = random.Random(seed)
    chosen = []
    for factor in FACTORS:
        ids = sorted(set(by_factor.get(factor) or []))
        rng.shuffle(ids)
        if len(ids) < n:
            print("WARN %s has only %d PASS triplets; taking all" % (factor, len(ids)), flush=True)
        chosen.extend(ids[:n])
    return chosen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-manifest", default=os.path.join(PROJECT, "outputs", "fast_track_audit_v1", "audit_manifest.jsonl"))
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "outputs", "fast_track_audit_v1"))
    parser.add_argument("--per-factor", type=int, default=100)
    parser.add_argument("--probe-judgments", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260912)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    items = read_jsonl(args.audit_manifest)
    chosen_ids = set(sample_triplets(items, args.per_factor, args.seed))
    gate = [it for it in items if it["triplet_id"] in chosen_ids]
    gate.sort(key=lambda r: (r["factor"], r["triplet_id"], VARIANTS.index(r["variant"]) if r["variant"] in VARIANTS else 9))
    gate_path = os.path.join(args.out_dir, "gpu_signal_gate_manifest.jsonl")
    write_jsonl(gate_path, gate)

    # Probe: cover 4 factors x 3 variants x mixed candidate order. Not Count-only.
    bases = [it for it in gate if it["variant"] == "base"]
    rng = random.Random(args.seed + 17)
    by_factor = {f: [it for it in bases if it["factor"] == f] for f in FACTORS}
    probe_triplets = []
    for factor in FACTORS:
        pool = list(by_factor[factor])
        rng.shuffle(pool)
        probe_triplets.extend(pool[: max(1, args.probe_judgments // 4)])
    probe_ids = {it["triplet_id"] for it in probe_triplets}
    probe_items = [it for it in gate if it["triplet_id"] in probe_ids]
    # Keep ~50 judgments, preserving factor/variant coverage.
    if len(probe_items) > args.probe_judgments:
        # round-robin variants
        grouped = {}
        for it in probe_items:
            grouped.setdefault((it["factor"], it["variant"]), []).append(it)
        probe_items = []
        while len(probe_items) < args.probe_judgments and any(grouped.values()):
            for factor in FACTORS:
                for variant in VARIANTS:
                    bucket = grouped.get((factor, variant)) or []
                    if bucket and len(probe_items) < args.probe_judgments:
                        probe_items.append(bucket.pop(0))
    probe_path = os.path.join(args.out_dir, "compatibility_probe_manifest.jsonl")
    write_jsonl(probe_path, probe_items)

    coverage = {}
    for it in probe_items:
        coverage.setdefault(it["factor"], {}).setdefault(it["variant"], 0)
        coverage[it["factor"]][it["variant"]] += 1
        order_key = "A_is_base_answer" if it["expected_preference"] == "A" else "B_is_base_answer"
        coverage[it["factor"]][order_key] = coverage[it["factor"]].get(order_key, 0) + (1 if it["variant"] == "base" else 0)

    meta = {
        "signal_gate_n_items": len(gate),
        "signal_gate_n_triplets": len(chosen_ids),
        "probe_n_items": len(probe_items),
        "probe_coverage": coverage,
        "seed": args.seed,
        "source_manifest_hash": sha256_file(args.audit_manifest) if os.path.isfile(args.audit_manifest) else None,
        "pass_only": True,
        "count_only": False,
    }
    write_json(os.path.join(args.out_dir, "gpu_subset_meta.json"), meta)
    print(json.dumps(meta, indent=2))
    if set(coverage) != set(FACTORS):
        print("WARN probe does not cover all four factors", coverage, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
