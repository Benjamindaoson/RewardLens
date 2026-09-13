#!/usr/bin/env python3
"""Acquire only the GQA/Visual Genome images required by frozen manifests."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import write_json  # noqa: E402
from lib.jsonl_io import read_jsonl  # noqa: E402

VG_BASES = (
    "https://cs.stanford.edu/people/rak248/VG_100K/{id}.jpg",
    "https://cs.stanford.edu/people/rak248/VG_100K_2/{id}.jpg",
)


def collect_ids(manifests: list[str]) -> list[str]:
    ids = []
    for path in manifests:
        if not os.path.isfile(path):
            continue
        for row in read_jsonl(path):
            iid = row.get("image_id")
            if iid is not None:
                ids.append(str(iid))
    return sorted(set(ids))


def download_one(image_id: str, dest: str, timeout: int = 60) -> bool:
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part.%d" % os.getpid()
    for template in VG_BASES:
        url = template.format(id=image_id)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RewardLens/gqa-images"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.getcode() not in (200, 206):
                    continue
                with open(tmp, "wb") as handle:
                    while True:
                        chunk = response.read(1024 * 64)
                        if not chunk:
                            break
                        handle.write(chunk)
            if os.path.getsize(tmp) > 0:
                os.replace(tmp, dest)
                return True
        except Exception:
            if os.path.isfile(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            continue
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifests", nargs="+", default=[])
    parser.add_argument("--out-dir", default=os.path.join(PROJECT, "datasets", "gqa", "images"))
    parser.add_argument("--ids-json", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "required_gqa_image_ids.json"))
    parser.add_argument("--inventory", default=os.path.join(PROJECT, "datasets", "gqa", "derived", "gqa_image_inventory.json"))
    parser.add_argument("--margin", type=int, default=0)
    parser.add_argument("--max-download", type=int, default=0, help="0 = all required")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--num-workers", type=int, default=1)
    parser.add_argument("--worker-index", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    derived = os.path.join(PROJECT, "datasets", "gqa", "derived")
    manifests = args.manifests or [
        os.path.join(derived, "gqa_static_manifest.jsonl"),
        os.path.join(derived, "gqa_downstream_manifest.jsonl"),
    ]
    all_ids = collect_ids(manifests)
    payload = {"n": len(all_ids), "image_ids": all_ids, "margin": args.margin, "sources": manifests}
    if args.worker_index == 0:
        write_json(args.ids_json, payload)
    ids = all_ids
    if args.num_workers > 1:
        ids = [iid for i, iid in enumerate(all_ids) if i % args.num_workers == args.worker_index]
        print("SHARD", args.worker_index, "of", args.num_workers, "n", len(ids), flush=True)
    os.makedirs(args.out_dir, exist_ok=True)
    missing = []
    present = []
    n_dl = 0
    for image_id in ids:
        dest = os.path.join(args.out_dir, "%s.jpg" % image_id)
        if os.path.isfile(dest) and os.path.getsize(dest) > 0:
            present.append(image_id)
            continue
        if args.dry_run:
            missing.append(image_id)
            continue
        if args.max_download and n_dl >= args.max_download:
            missing.append(image_id)
            continue
        ok = download_one(image_id, dest)
        n_dl += 1
        if ok:
            present.append(image_id)
            print("IMAGE_OK", image_id, flush=True)
        else:
            missing.append(image_id)
            print("IMAGE_MISSING", image_id, flush=True)
    inventory = {
        "n_required": len(ids),
        "n_present": len(present),
        "n_missing": len(missing),
        "out_dir": args.out_dir,
        "missing_ids": missing,
        "status": "PASS" if not missing else "FAIL",
    }
    write_json(args.inventory, inventory)
    print(json.dumps({k: inventory[k] for k in inventory if k != "missing_ids"}, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
