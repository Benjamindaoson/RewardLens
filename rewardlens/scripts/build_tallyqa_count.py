#!/usr/bin/env python3
"""Freeze TallyQA Count static (200) and downstream N=8 (200), image-disjoint.

Does not invent GQA Count. Prefer 100 simple + 100 complex per split.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import write_jsonl  # noqa: E402
from lib.tallyqa import (  # noqa: E402
    image_key,
    n8_pool,
    pairwise_candidates,
    parse_int_answer,
    resolve_local_image,
    split_bucket,
)

FACTOR = "count"
SEED = 20260912


def load_rows(ann_dir: str) -> list[dict]:
    rows = []
    for root, _dirs, files in os.walk(ann_dir):
        for name in files:
            if not name.endswith(".json"):
                continue
            path = os.path.join(root, name)
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            if isinstance(payload, dict):
                payload = payload.get("questions") or payload.get("data") or payload.get("annotations") or list(payload.values())
            if not isinstance(payload, list):
                continue
            split = "test" if "test" in name.lower() else "train" if "train" in name.lower() else os.path.splitext(name)[0]
            for item in payload:
                if isinstance(item, dict):
                    item = dict(item)
                    item["_file"] = name
                    item["_split_file"] = split
                    rows.append(item)
    return rows


def clean_row(row: dict) -> dict | None:
    gold = parse_int_answer(row.get("answer"))
    q = str(row.get("question") or "").strip()
    if gold is None or not q:
        return None
    if "?" not in q and not q.lower().startswith("how many"):
        # still allow if it is clearly a count question with numeric gold
        if "how many" not in q.lower():
            return None
    source, source_id, rel = image_key(row)
    if source == "other" or not source_id:
        return None
    image_id = "%s:%s" % (source, source_id)
    issimple = row.get("issimple")
    if isinstance(issimple, str):
        issimple = issimple.lower() in {"true", "1", "yes", "simple"}
    return {
        "question_id": str(row.get("question_id") or row.get("questionId") or "%s:%s" % (image_id, q)),
        "question": q,
        "gold": gold,
        "issimple": bool(issimple) if issimple is not None else ("how many" in q.lower() and q.lower().count(" ") <= 6),
        "source": source,
        "source_id": source_id,
        "image_rel": rel,
        "image_id": image_id,
        "data_source": row.get("data_source"),
        "tallyqa_split": row.get("_split_file"),
    }


def pick_unique_images(rows: list[dict], n: int, used_images: set[str]) -> list[dict]:
    chosen = []
    for row in rows:
        if row["image_id"] in used_images:
            continue
        used_images.add(row["image_id"])
        chosen.append(row)
        if len(chosen) >= n:
            break
    return chosen


def pick_balanced(pool: list[dict], n: int, rng: random.Random, used_images: set[str] | None = None) -> list[dict]:
    used_images = set() if used_images is None else used_images
    simple = [r for r in pool if r["issimple"]]
    complex_ = [r for r in pool if not r["issimple"]]
    rng.shuffle(simple)
    rng.shuffle(complex_)
    n_simple = min(n // 2, len(simple))
    n_complex = min(n - n_simple, len(complex_))
    chosen = pick_unique_images(simple, n_simple, used_images)
    chosen += pick_unique_images(complex_, n_complex, used_images)
    if len(chosen) < n:
        rest = simple + complex_
        rng.shuffle(rest)
        chosen += pick_unique_images(rest, n - len(chosen), used_images)
    return chosen[:n]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ann-dir", default=os.path.join(PROJECT, "datasets", "tallyqa", "annotations"))
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "datasets", "tallyqa", "derived"))
    parser.add_argument("--gqa-images", default=os.path.join(PROJECT, "datasets", "gqa", "images"))
    parser.add_argument("--tally-images", default=os.path.join(PROJECT, "datasets", "tallyqa", "images"))
    parser.add_argument("--coco-images", default=os.path.join(PROJECT, "datasets", "tallyqa", "coco"))
    parser.add_argument("--per-split", type=int, default=200)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--prefer-local-images", action="store_true", default=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    raw = load_rows(args.ann_dir)
    if not raw:
        print("NO_TALLYQA_ANNOTATIONS", args.ann_dir, flush=True)
        return 2
    cleaned = []
    seen_qi = set()
    for row in raw:
        item = clean_row(row)
        if item is None:
            continue
        key = (item["image_id"], item["question"].lower())
        if key in seen_qi:
            continue
        seen_qi.add(key)
        cleaned.append(item)
    rng = random.Random(args.seed)
    by_split: dict[str, list] = defaultdict(list)
    for item in cleaned:
        item["split"] = split_bucket(item["image_id"], args.seed)
        by_split[item["split"]].append(item)

    static_ids = sorted({r["image_id"] for r in by_split["static"]})
    down_ids = sorted({r["image_id"] for r in by_split["downstream"]})
    inter = sorted(set(static_ids) & set(down_ids))
    if inter:
        raise AssertionError("TallyQA image split leaked: %s" % inter[:10])

    def select(split_name: str) -> list[dict]:
        pool = by_split[split_name]
        if args.prefer_local_images:
            local = []
            remote = []
            for row in pool:
                path = resolve_local_image(
                    row["source"],
                    row["source_id"],
                    row["image_rel"],
                    gqa_images=args.gqa_images,
                    tally_images=args.tally_images,
                    coco_images=args.coco_images,
                )
                row = dict(row)
                row["image_path"] = path
                (local if path else remote).append(row)
            used: set[str] = set()
            chosen = pick_balanced(local, args.per_split, rng, used)
            if len(chosen) < args.per_split:
                extra = pick_balanced(remote, args.per_split - len(chosen), rng, used)
                chosen.extend(extra)
            return chosen
        return pick_balanced(pool, args.per_split, rng)

    static_rows = select("static")
    down_rows = select("downstream")
    assert not ({r["image_id"] for r in static_rows} & {r["image_id"] for r in down_rows})

    static_items = []
    for row in static_rows:
        item_rng = random.Random("%s:%s" % (args.seed, row["question_id"]))
        ca, cb, pref, hard = pairwise_candidates(row["gold"], item_rng)
        static_items.append(
            {
                "item_id": "tallyqa_static:count:%s" % row["question_id"],
                "question_id": row["question_id"],
                "image_id": row["image_id"],
                "image_path": row.get("image_path"),
                "image_rel": row["image_rel"],
                "source": row["source"],
                "source_id": row["source_id"],
                "factor": FACTOR,
                "variant": "static",
                "question": row["question"],
                "gold_answer": str(row["gold"]),
                "hard_negative": hard,
                "candidate_a": ca,
                "candidate_b": cb,
                "expected_preference": pref,
                "issimple": row["issimple"],
                "split": "static",
                "dataset": "tallyqa",
            }
        )

    down_items = []
    for row in down_rows:
        item_rng = random.Random("%s:%s:n8" % (args.seed, row["question_id"]))
        cands, gidx = n8_pool(row["gold"], item_rng)
        texts = [c["text"] for c in cands]
        assert len(texts) == 8
        assert len(set(texts)) == 8
        assert texts.count(str(row["gold"])) == 1
        assert all(int(t) >= 0 for t in texts)
        down_items.append(
            {
                "item_id": "tallyqa_down:count:%s" % row["question_id"],
                "question_id": row["question_id"],
                "image_id": row["image_id"],
                "image_path": row.get("image_path"),
                "image_rel": row["image_rel"],
                "source": row["source"],
                "source_id": row["source_id"],
                "factor": FACTOR,
                "question": row["question"],
                "gold": str(row["gold"]),
                "gold_answer": str(row["gold"]),
                "n_pool": 8,
                "candidates": cands,
                "gold_index": gidx,
                "issimple": row["issimple"],
                "split": "downstream",
                "dataset": "tallyqa",
                "partial": False,
            }
        )

    write_jsonl(os.path.join(args.out_dir, "tallyqa_count_static_manifest.jsonl"), static_items)
    write_jsonl(os.path.join(args.out_dir, "tallyqa_count_downstream_manifest.jsonl"), down_items)
    write_json(
        os.path.join(args.out_dir, "static_image_ids.json"),
        {"n": len({r["image_id"] for r in static_items}), "image_ids": sorted({r["image_id"] for r in static_items})},
    )
    write_json(
        os.path.join(args.out_dir, "downstream_image_ids.json"),
        {"n": len({r["image_id"] for r in down_items}), "image_ids": sorted({r["image_id"] for r in down_items})},
    )
    report = {
        "n_raw": len(raw),
        "n_clean": len(cleaned),
        "static_n": len(static_items),
        "downstream_n": len(down_items),
        "static_simple": sum(1 for r in static_items if r["issimple"]),
        "static_complex": sum(1 for r in static_items if not r["issimple"]),
        "down_simple": sum(1 for r in down_items if r["issimple"]),
        "down_complex": sum(1 for r in down_items if not r["issimple"]),
        "intersection": 0,
        "prefer_local_images": args.prefer_local_images,
        "static_local_images": sum(1 for r in static_items if r.get("image_path")),
        "down_local_images": sum(1 for r in down_items if r.get("image_path")),
        "policy": "Count static/downstream = TallyQA. GQA Count not invented.",
    }
    write_json(os.path.join(args.out_dir, "tallyqa_split_validation.json"), report)
    write_json(os.path.join(args.out_dir, "split_validation.json"), report)
    print(json.dumps(report, indent=2))
    if len(static_items) < args.per_split or len(down_items) < args.per_split:
        print("TALLYQA_SHORTFALL", flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
