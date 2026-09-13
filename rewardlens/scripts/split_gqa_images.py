#!/usr/bin/env python3
"""Image-disjoint GQA static vs downstream split. Intersection must be empty."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402


def bucket(image_id: str, seed: int) -> str:
    digest = hashlib.sha256(("%s:%s" % (seed, image_id)).encode("utf-8")).hexdigest()
    return "static" if int(digest[:8], 16) % 2 == 0 else "downstream"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping-jsonl", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_factor_mapping.jsonl"))
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "datasets", "gqa", "derived"))
    parser.add_argument("--seed", type=int, default=20260912)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_jsonl(args.mapping_jsonl)
    image_ids = sorted({str(r["image_id"]) for r in rows if r.get("image_id")})
    static = sorted(i for i in image_ids if bucket(i, args.seed) == "static")
    downstream = sorted(i for i in image_ids if bucket(i, args.seed) == "downstream")
    inter = sorted(set(static) & set(downstream))
    assert inter == [], "image split leaked: %s" % inter[:10]
    os.makedirs(args.out_dir, exist_ok=True)
    static_path = os.path.join(args.out_dir, "static_image_ids.json")
    down_path = os.path.join(args.out_dir, "downstream_image_ids.json")
    write_json(static_path, {"seed": args.seed, "n": len(static), "image_ids": static})
    write_json(down_path, {"seed": args.seed, "n": len(downstream), "image_ids": downstream})
    report = {
        "n_images": len(image_ids),
        "n_static": len(static),
        "n_downstream": len(downstream),
        "intersection": 0,
        "assert_ok": True,
        "seed": args.seed,
    }
    write_json(os.path.join(args.out_dir, "gqa_split_report.json"), report)
    write_json(os.path.join(args.out_dir, "split_validation.json"), {**report, "intersection_ids": inter})
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
