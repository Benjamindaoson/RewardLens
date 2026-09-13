#!/usr/bin/env python3
"""Combine TallyQA Count + GQA Attribute/Spatial/Presence into GPU-ready manifests."""

from __future__ import annotations

import argparse
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gqa-derived", default=os.path.join(PROJECT, "datasets", "gqa", "derived"))
    parser.add_argument("--tally-derived", default=os.path.join(PROJECT, "datasets", "tallyqa", "derived"))
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "datasets", "processed", "fast_eval"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    static = read_jsonl(os.path.join(args.tally_derived, "tallyqa_count_static_manifest.jsonl"))
    static += [r for r in read_jsonl(os.path.join(args.gqa_derived, "gqa_static_manifest.jsonl")) if r.get("factor") != "count"]
    down = read_jsonl(os.path.join(args.tally_derived, "tallyqa_count_downstream_manifest.jsonl"))
    down += [r for r in read_jsonl(os.path.join(args.gqa_derived, "gqa_downstream_manifest.jsonl")) if r.get("factor") != "count"]
    write_jsonl(os.path.join(args.out_dir, "static_manifest.jsonl"), static)
    write_jsonl(os.path.join(args.out_dir, "downstream_manifest.jsonl"), down)
    from collections import Counter

    report = {
        "static_n": len(static),
        "downstream_n": len(down),
        "static_by_factor": dict(Counter(r.get("factor") for r in static)),
        "down_by_factor": dict(Counter(r.get("factor") for r in down)),
        "count_dataset": "tallyqa",
        "other_factors_dataset": "gqa",
        "static_images": sorted({str(r.get("image_id")) for r in static}),
        "down_images": sorted({str(r.get("image_id")) for r in down}),
    }
    tally_static = {r["image_id"] for r in static if r.get("dataset") == "tallyqa" or r.get("factor") == "count"}
    tally_down = {r["image_id"] for r in down if r.get("dataset") == "tallyqa" or r.get("factor") == "count"}
    tally_inter = sorted(tally_static & tally_down)
    gqa_static = {str(r.get("image_id")) for r in static if r.get("dataset") != "tallyqa" and r.get("factor") != "count"}
    gqa_down = {str(r.get("image_id")) for r in down if r.get("dataset") != "tallyqa" and r.get("factor") != "count"}
    gqa_inter = sorted(gqa_static & gqa_down)
    string_inter = sorted(set(report["static_images"]) & set(report["down_images"]))
    report["tallyqa_count_intersection"] = len(tally_inter)
    report["gqa_intersection"] = len(gqa_inter)
    report["combined_string_intersection"] = len(string_inter)
    report["intersection"] = len(tally_inter)
    write_json(os.path.join(args.out_dir, "combined_split_validation.json"), {k: report[k] for k in report if k not in {"static_images", "down_images"}})
    for name in (
        "tallyqa_count_static_manifest.jsonl",
        "tallyqa_count_downstream_manifest.jsonl",
        "tallyqa_image_inventory.json",
        "tallyqa_split_validation.json",
    ):
        src = os.path.join(args.tally_derived, name)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(args.out_dir, name))
    print("COMBINED_STATIC", len(static), "DOWNSTREAM", len(down), "tallyqa_inter", len(tally_inter), "gqa_inter", len(gqa_inter))
    if tally_inter or gqa_inter:
        print("SPLIT_LEAK", "tallyqa", tally_inter[:5], "gqa", gqa_inter[:5])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
