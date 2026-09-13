#!/usr/bin/env python3
"""GQA downstream N=8 pools from structured sources. Natural distractors queued, never faked."""

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
from lib.gqa_mapping import find_scene_graph_files, load_scene_graphs  # noqa: E402
from lib.gqa_pools import N_POOL, factor_vocab, structured_candidates  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402

FACTORS = ("count", "attribute", "presence", "spatial")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping-jsonl", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_factor_mapping.jsonl"))
    parser.add_argument("--downstream-ids", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "downstream_image_ids.json"))
    parser.add_argument("--gqa-dir", default=os.path.join(PROJECT, "datasets", "gqa"))
    parser.add_argument("--out", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_downstream_manifest.jsonl"))
    parser.add_argument("--jobs-out", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "natural_distractor_jobs.jsonl"))
    parser.add_argument("--per-factor", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260912)
    return parser.parse_args()


def gold_index(candidates: list[dict], gold: str) -> int:
    gold_l = gold.strip().lower()
    for i, cand in enumerate(candidates):
        if str(cand.get("text") or "").strip().lower() == gold_l:
            return i
    return 0


def main() -> int:
    args = parse_args()
    mapping = read_jsonl(args.mapping_jsonl)
    down_ids = set(json.load(open(args.downstream_ids, encoding="utf-8"))["image_ids"])
    scenes = {}
    sg_files = find_scene_graph_files(args.gqa_dir)
    if sg_files:
        scenes = load_scene_graphs(sg_files)
    rng = random.Random(args.seed)
    items = []
    jobs = []
    report = {
        "per_factor": {},
        "n_pool": N_POOL,
        "natural_distractors_faked": False,
        "n_full_pools": 0,
        "n_partial_skipped": 0,
    }
    vocabs = {factor: factor_vocab(mapping, factor) for factor in FACTORS}
    for factor in FACTORS:
        pool = [
            r
            for r in mapping
            if r["factor"] == factor
            and r.get("image_id") in down_ids
            and r.get("answer")
        ]
        pool.sort(key=lambda r: (r.get("mapping_confidence") != "high", str(r.get("question_id"))))
        rng.shuffle(pool)
        written = 0
        n_partial = 0
        for row in pool:
            if written >= args.per_factor:
                break
            gold = str(row.get("answer") or "")
            scene = scenes.get(str(row.get("image_id")))
            candidates = structured_candidates(row["factor"], row, vocab=vocabs[factor], scene=scene)
            if len(candidates) < N_POOL:
                n_partial += 1
                jobs.append(
                    {
                        "job_id": "nd:%s:%s" % (factor, row["question_id"]),
                        "question_id": row["question_id"],
                        "image_id": row["image_id"],
                        "factor": factor,
                        "question": row["question"],
                        "gold": gold,
                        "existing_candidates": [c["text"] for c in candidates],
                        "n_needed": N_POOL - len(candidates),
                        "status": "queued_needs_vlm",
                        "note": "Do not fill with invented strings. Requires a frozen VLM distractor job.",
                    }
                )
                continue
            rng.shuffle(candidates)
            gidx = gold_index(candidates, gold)
            items.append(
                {
                    "item_id": "gqa_down:%s:%s" % (factor, row["question_id"]),
                    "question_id": row["question_id"],
                    "image_id": row["image_id"],
                    "factor": factor,
                    "question": row["question"],
                    "gold": gold,
                    "gold_answer": gold,
                    "n_pool": N_POOL,
                    "candidates": candidates,
                    "gold_index": gidx,
                    "candidate_source": [c.get("source") for c in candidates],
                    "partial": False,
                    "split": "downstream",
                    "mapping_source": row.get("mapping_source"),
                }
            )
            written += 1
        report["per_factor"][factor] = {
            "available": len(pool),
            "written": written,
            "target": args.per_factor,
            "partial_skipped": n_partial,
            "shortfall_reason": None
            if written >= args.per_factor
            else "insufficient_clean_N8_pools_from_structured_sources",
        }
        report["n_full_pools"] += written
        report["n_partial_skipped"] += n_partial
    write_jsonl(args.out, items)
    write_jsonl(args.jobs_out, jobs)
    write_json(os.path.splitext(args.out)[0] + "_report.json", {**report, "n_items": len(items), "n_jobs": len(jobs)})
    print(json.dumps({"n_items": len(items), "n_jobs": len(jobs), **report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
