#!/usr/bin/env python3
"""Build the primary factor-wise RQ2 table from official Phase II outputs."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.phase2_analysis import merge_primary_table
from models.registry import iter_models, load_registry


def _rows(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("rows", []) if isinstance(payload, dict) else payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-metrics", required=True)
    parser.add_argument("--static-a", required=True)
    parser.add_argument("--downstream-u", required=True)
    parser.add_argument("--registry", default=None)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    families = {str(row["model_id"]): str(row["family"]) for row in iter_models(load_registry(args.registry))}
    rows = merge_primary_table(
        audit_rows=_rows(args.audit_metrics),
        static_rows=_rows(args.static_a),
        utility_rows=_rows(args.downstream_u),
        families=families,
    )
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
    print(json.dumps({"out": args.out, "rows": len(rows), "primary_n": 8}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
