#!/usr/bin/env python3
"""Freeze Phase II V2 COCO acquisition IDs from TallyQA annotation paths."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.tallyqa import split_bucket  # noqa: E402
from scripts.build_tallyqa_count import clean_row, load_rows  # noqa: E402

CANONICAL_COCO_PATH = re.compile(
    r"^(train2014|val2014)/(COCO_(train2014|val2014)_(\d{12})\.jpg)$"
)
DEFAULT_AVAILABILITY_ROOTS = (
    "/root/autodl-fs/RewardLens/phase2_v2_sources/coco",
    "/root/autodl-fs/RewardLens/phase2_v2_sources/tallyqa/coco",
    "/root/autodl-fs/RewardLens/phase2_v2_sources/tallyqa/images",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metadata_split_and_filename(image_rel: str) -> tuple[str, str, str]:
    normalized = image_rel.replace("\\", "/").lstrip("./")
    match = CANONICAL_COCO_PATH.fullmatch(normalized)
    if match is None:
        raise ValueError("noncanonical COCO image path: %s" % image_rel)
    outer_split, filename, inner_split, numeric_id = match.groups()
    if outer_split != inner_split:
        raise ValueError("COCO split/path mismatch: %s" % image_rel)
    return outer_split, numeric_id, filename


def _available(split: str, filename: str, roots: list[str]) -> bool:
    for root in roots:
        base = Path(root)
        if (base / split / filename).is_file() or (base / filename).is_file():
            return True
    return False


def build_required_coco_acquisition(
    ann_dir: str, *, availability_roots: list[str] | tuple[str, ...]
) -> dict:
    raw_rows = load_rows(ann_dir)
    if not raw_rows:
        raise ValueError("no TallyQA annotation rows: %s" % ann_dir)

    source_rows = Counter(str(row.get("_split_file") or "other") for row in raw_rows)
    seen_questions: set[tuple[str, str]] = set()
    cleaned_rows = 0
    downstream_rows = 0
    rows_by_split: Counter[str] = Counter()
    filenames_by_id: dict[str, tuple[str, str]] = {}

    for raw in raw_rows:
        item = clean_row(raw)
        if item is None:
            continue
        key = (item["image_id"], item["question"].lower())
        if key in seen_questions:
            continue
        seen_questions.add(key)
        cleaned_rows += 1
        if item["source"] != "coco" or split_bucket(item["image_id"]) != "downstream":
            continue

        split, numeric_id, filename = _metadata_split_and_filename(item["image_rel"])
        prior = filenames_by_id.setdefault(numeric_id, (split, filename))
        if prior != (split, filename):
            raise ValueError(
                "numeric COCO ID maps to multiple metadata paths: %s" % numeric_id
            )
        downstream_rows += 1
        rows_by_split[split] += 1

    ids = sorted(filenames_by_id)
    ids_by_split = {
        split: sum(1 for actual_split, _filename in filenames_by_id.values() if actual_split == split)
        for split in ("train2014", "val2014")
    }
    expected_filenames = {
        image_id: filenames_by_id[image_id][1] for image_id in ids
    }
    found_ids = [
        image_id
        for image_id in ids
        if _available(filenames_by_id[image_id][0], expected_filenames[image_id], list(availability_roots))
    ]
    found_set = set(found_ids)

    annotation_files = {}
    for path in sorted(Path(ann_dir).rglob("*.json")):
        annotation_files[path.name] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }

    return {
        "ids": ids,
        "receipt": {
            "schema": "RewardLens Phase II V2 required COCO image identity set v1",
            "purpose": "Frozen TallyQA Count downstream eligibility universe; no availability filtering or replacement selection.",
            "source_annotation_files": annotation_files,
            "source_tallyqa_row_counts": {
                "annotation_rows": dict(sorted(source_rows.items())),
                "annotation_rows_total": len(raw_rows),
                "deduplicated_count_eligibility_rows": cleaned_rows,
                "downstream_coco_count_rows": downstream_rows,
                "downstream_coco_rows_by_metadata_split": dict(sorted(rows_by_split.items())),
            },
            "total_unique_coco_ids": len(ids),
            "counts_by_coco_split": ids_by_split,
            "other_coco_splits": {},
            "expected_canonical_filename_by_id": expected_filenames,
            "already_available_locally": len(found_ids),
            "available_ids": found_ids,
            "missing": len(ids) - len(found_ids),
            "missing_ids": [image_id for image_id in ids if image_id not in found_set],
            "availability_roots_checked": list(availability_roots),
            "frozen_rules": {
                "count_tallyqa_only": True,
                "tallyqa_downstream_bucket": True,
                "split_resolved_from_annotation_image_path": True,
                "no_image_availability_filter": True,
                "no_replacement_selection": True,
            },
        },
    }


def _publish_once(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise FileExistsError("refusing to replace different frozen output: %s" % path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(content)
    os.replace(temporary, path)


def publish_required_coco_acquisition(
    ann_dir: str,
    output_list: str,
    output_receipt: str,
    *,
    availability_roots: list[str] | tuple[str, ...],
    expected_total: int | None = 49616,
) -> dict:
    result = build_required_coco_acquisition(
        ann_dir, availability_roots=availability_roots
    )
    if expected_total is not None and len(result["ids"]) != expected_total:
        raise ValueError(
            "frozen COCO quota mismatch: expected %s, got %s"
            % (expected_total, len(result["ids"]))
        )

    list_content = ("".join("%s\n" % image_id for image_id in result["ids"])).encode("utf-8")
    result["receipt"]["acquisition_list_sha256"] = hashlib.sha256(list_content).hexdigest()
    receipt_content = (
        json.dumps(result["receipt"], indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _publish_once(Path(output_list), list_content)
    _publish_once(Path(output_receipt), receipt_content)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ann-dir", required=True)
    parser.add_argument("--output-list", required=True)
    parser.add_argument("--output-receipt", required=True)
    parser.add_argument("--availability-root", action="append", default=[])
    parser.add_argument("--expected-total", type=int, default=49616)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    roots = args.availability_root or list(DEFAULT_AVAILABILITY_ROOTS)
    result = publish_required_coco_acquisition(
        args.ann_dir,
        args.output_list,
        args.output_receipt,
        availability_roots=roots,
        expected_total=args.expected_total,
    )
    receipt = result["receipt"]
    print(
        json.dumps(
            {
                "total_unique_coco_ids": receipt["total_unique_coco_ids"],
                "counts_by_coco_split": receipt["counts_by_coco_split"],
                "already_available_locally": receipt["already_available_locally"],
                "missing": receipt["missing"],
                "acquisition_list_sha256": receipt["acquisition_list_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
