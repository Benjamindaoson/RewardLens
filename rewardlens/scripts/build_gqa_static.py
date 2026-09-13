#!/usr/bin/env python3
"""Build GQA-static pairwise items (~1000/factor) from the frozen image split."""

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

from lib.common import preferred_for_answer, write_json  # noqa: E402
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402

FACTORS = ("count", "attribute", "presence", "spatial")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping-jsonl", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_factor_mapping.jsonl"))
    parser.add_argument("--static-ids", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "static_image_ids.json"))
    parser.add_argument("--images-dir", default=os.path.join(PROJECT, "datasets", "gqa", "images"))
    parser.add_argument("--out", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_static_manifest.jsonl"))
    parser.add_argument("--per-factor", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260912)
    return parser.parse_args()


def image_path(images_dir: str, image_id: str) -> str | None:
    for name in ("%s.jpg" % image_id, "%s.png" % image_id, os.path.join("images", "%s.jpg" % image_id)):
        path = os.path.join(images_dir, name) if not os.path.isabs(name) else name
        # also search one extra known extract layout
        candidates = [
            os.path.join(images_dir, "%s.jpg" % image_id),
            os.path.join(images_dir, "images", "%s.jpg" % image_id),
        ]
        for cand in candidates:
            if os.path.isfile(cand):
                return cand
    return None


def main() -> int:
    args = parse_args()
    mapping = read_jsonl(args.mapping_jsonl)
    static_ids = set(json.load(open(args.static_ids, encoding="utf-8"))["image_ids"])
    rng = random.Random(args.seed)
    items = []
    report = {"per_factor": {}, "images_found": 0, "images_missing": 0}
    for factor in FACTORS:
        pool = [
            r
            for r in mapping
            if r["factor"] == factor
            and r.get("image_id") in static_ids
            and r.get("hard_negative")
            and str(r.get("hard_negative")).lower() != str(r.get("answer")).lower()
        ]
        rng.shuffle(pool)
        chosen = []
        for row in pool:
            if len(chosen) >= args.per_factor:
                break
            img = image_path(args.images_dir, row["image_id"])
            if img:
                report["images_found"] += 1
            else:
                report["images_missing"] += 1
            a_first = bool(rng.randrange(2))
            gold = str(row["answer"])
            hard = str(row["hard_negative"])
            candidate_a, candidate_b = (gold, hard) if a_first else (hard, gold)
            preferred = preferred_for_answer(candidate_a, candidate_b, gold)
            chosen.append(
                {
                    "item_id": "gqa_static:%s:%s" % (factor, row["question_id"]),
                    "question_id": row["question_id"],
                    "image_id": row["image_id"],
                    "image_path": img,
                    "factor": factor,
                    "variant": "static",
                    "question": row["question"],
                    "gold_answer": gold,
                    "hard_negative": hard,
                    "candidate_a": candidate_a,
                    "candidate_b": candidate_b,
                    "expected_preference": preferred,
                    "split": "static",
                    "mapping_source": row.get("mapping_source"),
                }
            )
        report["per_factor"][factor] = {"available": len(pool), "written": len(chosen)}
        items.extend(chosen)
    write_jsonl(args.out, items)
    write_json(os.path.splitext(args.out)[0] + "_report.json", report)
    print(json.dumps({"n": len(items), **report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
