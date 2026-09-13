#!/usr/bin/env python3
"""Build ~50-judgment compatibility probe from a frozen PASS-only audit/signal manifest.

Deterministic. Does not shuffle the parent freeze. Covers 4 factors x 3 variants,
mixed candidate order, and mixed count/color/relation values when present.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-manifest", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--probe-judgments", type=int, default=50)
    parser.add_argument("--copy-signal-alias", action="store_true")
    return parser.parse_args()


def diversity_key(item: dict) -> tuple:
    return (
        item.get("factor"),
        str(item.get("candidate_a")),
        str(item.get("candidate_b")),
        str(item.get("expected_preference")),
        str(item.get("question")),
    )


def select_triplet_ids(items: list[dict], n_triplets_hint: int = 5) -> list[str]:
    bases = [it for it in items if it.get("variant") == "base" and it.get("qc_status", "PASS") == "PASS"]
    by_factor: dict[str, list[dict]] = {f: [] for f in FACTORS}
    for it in bases:
        by_factor.setdefault(it["factor"], []).append(it)
    chosen = []
    for factor in FACTORS:
        pool = sorted(by_factor.get(factor) or [], key=lambda r: r["triplet_id"])
        seen = set()
        picked = []
        for row in pool:
            key = diversity_key(row)
            if key in seen and len(picked) >= n_triplets_hint:
                continue
            seen.add(key)
            picked.append(row["triplet_id"])
            if len(picked) >= n_triplets_hint:
                break
        if len(picked) < n_triplets_hint:
            extra = [r["triplet_id"] for r in pool if r["triplet_id"] not in picked]
            picked.extend(extra[: n_triplets_hint - len(picked)])
        chosen.extend(picked)
    return chosen


def main() -> int:
    args = parse_args()
    items = read_jsonl(args.audit_manifest)
    os.makedirs(args.out_dir, exist_ok=True)
    if args.copy_signal_alias:
        alias = os.path.join(args.out_dir, "gpu_signal_gate_manifest.jsonl")
        if os.path.abspath(args.audit_manifest) != os.path.abspath(alias):
            shutil.copy2(args.audit_manifest, alias)

    triplet_ids = set(select_triplet_ids(items, n_triplets_hint=5))
    probe_all = [it for it in items if it["triplet_id"] in triplet_ids]
    probe_all.sort(
        key=lambda r: (r["factor"], r["triplet_id"], VARIANTS.index(r["variant"]) if r["variant"] in VARIANTS else 9)
    )
    grouped: dict[tuple, list] = {}
    for it in probe_all:
        grouped.setdefault((it["factor"], it["variant"]), []).append(it)
    probe_items = []
    while len(probe_items) < args.probe_judgments and any(grouped.values()):
        progressed = False
        for factor in FACTORS:
            for variant in VARIANTS:
                bucket = grouped.get((factor, variant)) or []
                if bucket and len(probe_items) < args.probe_judgments:
                    probe_items.append(bucket.pop(0))
                    progressed = True
        if not progressed:
            break

    probe_path = os.path.join(args.out_dir, "compatibility_probe_manifest.jsonl")
    write_jsonl(probe_path, probe_items)
    coverage = {}
    for it in probe_items:
        coverage.setdefault(it["factor"], {}).setdefault(it["variant"], 0)
        coverage[it["factor"]][it["variant"]] += 1
        order_key = "pref_A" if it.get("expected_preference") == "A" else "pref_B"
        coverage[it["factor"]][order_key] = coverage[it["factor"]].get(order_key, 0) + (1 if it["variant"] == "base" else 0)
    meta = {
        "probe_n_items": len(probe_items),
        "probe_coverage": coverage,
        "source_manifest": args.audit_manifest,
        "source_manifest_hash": sha256_file(args.audit_manifest) if os.path.isfile(args.audit_manifest) else None,
        "pass_only": True,
        "selection": "deterministic first diverse PASS triplets per factor, round-robin variants",
    }
    write_json(os.path.join(args.out_dir, "probe_meta.json"), meta)
    print(json.dumps(meta, indent=2))
    missing = [f for f in FACTORS if f not in coverage]
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
