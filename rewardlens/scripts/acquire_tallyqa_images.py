#!/usr/bin/env python3
"""Download only TallyQA images required by frozen Count manifests. Reuse GQA/VG files."""

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
from lib.jsonl_io import read_jsonl, write_jsonl  # noqa: E402
from lib.tallyqa import coco_urls, resolve_local_image, vg_urls  # noqa: E402


def download(url: str, dest: str, timeout: int = 60) -> bool:
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part.%d" % os.getpid()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RewardLens/tallyqa-images"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.getcode() not in (200, 206):
                return False
            with open(tmp, "wb") as handle:
                while True:
                    chunk = response.read(64 * 1024)
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
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--derived", default=os.path.join(PROJECT, "datasets", "tallyqa", "derived"))
    parser.add_argument("--gqa-images", default=os.path.join(PROJECT, "datasets", "gqa", "images"))
    parser.add_argument("--tally-images", default=os.path.join(PROJECT, "datasets", "tallyqa", "images"))
    parser.add_argument("--coco-images", default=os.path.join(PROJECT, "datasets", "tallyqa", "coco"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifests = [
        os.path.join(args.derived, "tallyqa_count_static_manifest.jsonl"),
        os.path.join(args.derived, "tallyqa_count_downstream_manifest.jsonl"),
    ]
    rows_by_path = {path: read_jsonl(path) for path in manifests if os.path.isfile(path)}
    required = []
    for rows in rows_by_path.values():
        for row in rows:
            required.append(row)
    ids = sorted({r["image_id"] for r in required})
    write_json(os.path.join(args.derived, "required_tallyqa_image_ids.json"), {"n": len(ids), "image_ids": ids})
    missing = []
    present = []
    reused = 0
    downloaded = 0
    for row in required:
        local = resolve_local_image(
            row["source"],
            row["source_id"],
            row["image_rel"],
            gqa_images=args.gqa_images,
            tally_images=args.tally_images,
            coco_images=args.coco_images,
        )
        if local:
            row["image_path"] = local
            present.append(row["image_id"])
            reused += 1
            continue
        dest = os.path.join(args.tally_images, "%s.jpg" % row["source_id"])
        urls = vg_urls(row["source_id"]) if row["source"] == "vg" else coco_urls(row["image_rel"])
        if row["source"] == "coco":
            dest = os.path.join(args.coco_images, os.path.basename(row["image_rel"]))
        ok = False
        for url in urls:
            if download(url, dest):
                ok = True
                break
        if ok:
            row["image_path"] = dest
            present.append(row["image_id"])
            downloaded += 1
            print("IMAGE_OK", row["image_id"], dest, flush=True)
        else:
            missing.append(row["image_id"])
            print("IMAGE_MISSING", row["image_id"], flush=True)
    present = sorted(set(present))
    missing = sorted(set(missing))
    for path, rows in rows_by_path.items():
        write_jsonl(path, rows)
    inventory = {
        "n_required": len(ids),
        "n_present": len(present),
        "n_missing": len(missing),
        "n_reused": reused,
        "n_downloaded": downloaded,
        "missing_ids": missing,
        "status": "PASS" if not missing else "FAIL",
    }
    write_json(os.path.join(args.derived, "tallyqa_image_inventory.json"), inventory)
    # Candidate-pool QC for downstream N=8.
    down_path = os.path.join(args.derived, "tallyqa_count_downstream_manifest.jsonl")
    pool_fail = []
    if os.path.isfile(down_path):
        for row in read_jsonl(down_path):
            texts = [str(c.get("text")) for c in row.get("candidates") or []]
            gold = str(row.get("gold") or row.get("gold_answer"))
            issues = []
            if len(texts) != 8:
                issues.append("n!=8")
            if len(set(texts)) != len(texts):
                issues.append("duplicate")
            if texts.count(gold) != 1:
                issues.append("gold_count")
            try:
                if any(int(t) < 0 for t in texts):
                    issues.append("negative")
            except ValueError:
                issues.append("non_int")
            if issues:
                pool_fail.append({"item_id": row.get("item_id"), "issues": issues})
    write_json(
        os.path.join(args.derived, "tallyqa_candidate_pool_qc.json"),
        {"n_fail": len(pool_fail), "failures": pool_fail[:20], "status": "PASS" if not pool_fail else "FAIL"},
    )
    print(json.dumps({k: inventory[k] for k in inventory if k != "missing_ids"}, indent=2))
    if pool_fail:
        print("TALLYQA_POOL_QC_FAIL", len(pool_fail), flush=True)
        return 3
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
