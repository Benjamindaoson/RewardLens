#!/usr/bin/env python3
"""Frozen Phase II V2 Best-of-N runner."""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from typing import Any, Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.bon import derive_subset_selections, evaluate_pairwise_graph, pool_candidates, scalar_pair_graph
from inference.common import load_items, resolve_image_path
from inference.device import probe_device, write_probe
from inference.runner_lib import add_common_args, build_adapter
from lib.jsonl_io import append_jsonl, read_jsonl, repair_jsonl


COMPLETE_PAIR_STATUSES = {"ok", "semantic_abstention"}
SELECTION_NS = (2, 4, 8)
SCHEMA_VERSION = "PHASE2_BON_V2"


def _pool_id(item: dict[str, Any]) -> str:
    return str(item.get("pool_id") or item.get("item_id") or item.get("question_id"))


def _completed_pairs(path: str) -> set[str]:
    return {
        str(row["pair_key"])
        for row in read_jsonl(path)
        if row.get("status") in COMPLETE_PAIR_STATUSES and row.get("pair_key")
    }


def _completed_pools(path: str) -> set[str]:
    by_pool: dict[str, set[int]] = {}
    for row in read_jsonl(path):
        if row.get("status") == "ok" and row.get("pool_id") is not None:
            by_pool.setdefault(str(row["pool_id"]), set()).add(int(row.get("n", 0)))
    return {pool_id for pool_id, ns in by_pool.items() if ns == set(SELECTION_NS)}


def _pair_rows_for_pool(path: str, pool_id: str) -> list[dict[str, Any]]:
    return [
        row for row in read_jsonl(path)
        if str(row.get("pool_id")) == pool_id and row.get("status") in COMPLETE_PAIR_STATUSES
    ]


def _metadata(item: dict[str, Any], model_id: str, pool_id: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "pool_id": pool_id,
        "item_id": str(item.get("item_id") or pool_id),
        "model_id": model_id,
        "factor": str(item.get("factor") or ""),
        "dataset": item.get("dataset") or item.get("carrier") or item.get("source"),
    }


def _failure(fail_jsonl: str, item: dict[str, Any], model_id: str, pool_id: str, exc: Exception) -> None:
    append_jsonl(
        fail_jsonl,
        {
            **_metadata(item, model_id, pool_id),
            "status": "error",
            "error": "%s\n%s" % (exc, traceback.format_exc()),
        },
    )


def run_bon_items(
    *,
    items: Iterable[dict[str, Any]],
    adapter,
    model_id: str,
    pair_out_jsonl: str,
    selection_out_jsonl: str,
    fail_jsonl: str,
    images_root: str | None = None,
) -> dict[str, Any]:
    """Run or resume each frozen N=8 graph and emit C2/C4/C8 selections."""
    for path in (pair_out_jsonl, selection_out_jsonl, fail_jsonl):
        if os.path.isfile(path):
            repair_jsonl(path)
    pairs_written = pools_completed = pools_skipped = pools_failed = 0
    for item in items:
        parsed = pool_candidates(item)
        pool_id = parsed["pool_id"]
        if pool_id in _completed_pools(selection_out_jsonl):
            pools_skipped += 1
            continue
        try:
            image_path = resolve_image_path(item, images_root)
            if not image_path or not os.path.isfile(image_path):
                raise FileNotFoundError("image missing: %s" % image_path)
            metadata = _metadata(item, model_id, pool_id)

            def persist_pair(row: dict[str, Any]) -> None:
                nonlocal pairs_written
                append_jsonl(pair_out_jsonl, {**metadata, **row})
                pairs_written += 1

            completed = _completed_pairs(pair_out_jsonl)
            if callable(getattr(adapter, "score_candidate", None)):
                scores = {
                    record["uid"]: float(
                        adapter.score_candidate(
                            image_path=image_path,
                            question=item.get("question"),
                            candidate=record["candidate"]["text"],
                        )
                    )
                    for record in parsed["records"]
                }
                for row in scalar_pair_graph(item, scores):
                    row["pair_key"] = pool_id + "|" + row["left_uid"] + "|" + row["right_uid"]
                    if row["pair_key"] not in completed:
                        persist_pair(row)
            else:
                evaluate_pairwise_graph(
                    item,
                    adapter,
                    image_path=image_path,
                    completed_pair_keys=completed,
                    on_row=persist_pair,
                )
            outcomes = _pair_rows_for_pool(pair_out_jsonl, pool_id)
            selections = derive_subset_selections(item, outcomes)
            for n in SELECTION_NS:
                result = selections[n]
                append_jsonl(
                    selection_out_jsonl,
                    {
                        **metadata,
                        "n": n,
                        "status": "ok",
                        **result,
                        "utility_success": result["success"],
                    },
                )
            pools_completed += 1
        except Exception as exc:
            _failure(fail_jsonl, item, model_id, pool_id, exc)
            pools_failed += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "pairs_written": pairs_written,
        "pools_completed": pools_completed,
        "pools_skipped": pools_skipped,
        "pools_failed": pools_failed,
        "pair_out_jsonl": pair_out_jsonl,
        "selection_out_jsonl": selection_out_jsonl,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    parser.add_argument("--selection-jsonl", required=True)
    args = parser.parse_args()
    fail_jsonl = args.fail_jsonl or os.path.join(os.path.dirname(args.out_jsonl), "failures.jsonl")
    env_path = args.env_json or os.path.join(os.path.dirname(args.out_jsonl), "environment_report.json")
    items = load_items(args.manifest)
    if args.limit:
        items = items[: args.limit]
    report = probe_device()
    report.update({"stage": "phase2_bon_v2", "model_id": args.model_id, "schema_version": SCHEMA_VERSION})
    write_probe(env_path, report)
    adapter = build_adapter(args)
    adapter.load_model()
    try:
        summary = run_bon_items(
            items=items,
            adapter=adapter,
            model_id=args.model_id,
            pair_out_jsonl=args.out_jsonl,
            selection_out_jsonl=args.selection_jsonl,
            fail_jsonl=fail_jsonl,
            images_root=args.images_root,
        )
    finally:
        adapter.cleanup()
    summary_path = os.path.join(os.path.dirname(args.out_jsonl), "run_summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)
    print(json.dumps(summary, indent=2))
    return 0 if not summary["pools_failed"] or args.adapter == "dummy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
