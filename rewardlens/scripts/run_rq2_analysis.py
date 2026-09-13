#!/usr/bin/env python3
"""RQ2 confirmatory analysis. Factor-wise only. Synthetic/fixture until official outputs exist."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from stats import incremental_validity_factorwise  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", default=os.path.join(ROOT, "tests", "fixtures", "rq2_rq3_table.json"))
    parser.add_argument("--config", default=os.path.join(ROOT, "configs", "rq2_analysis.json"))
    parser.add_argument("--out", default=os.path.join(ROOT, "tests", "fixtures", "rq2_analysis_out.json"))
    parser.add_argument("--allow-official", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out = os.path.abspath(args.out)
    if ("outputs" in out.replace("\\", "/").split("/")) and not args.allow_official:
        raise SystemExit("refusing to write RQ2 under outputs/ without --allow-official")
    with open(args.config, "r", encoding="utf-8") as handle:
        config = json.load(handle)
    with open(args.table, "r", encoding="utf-8") as handle:
        table = json.load(handle)
    if isinstance(table, dict):
        table = table.get("rows") or table.get("table") or []
    if any(r.get("official_gpu") for r in table) and not args.allow_official:
        raise SystemExit("refusing official GPU rows without --allow-official")
    result = incremental_validity_factorwise(table)
    result["config"] = config
    result["synthetic_or_fixture"] = not args.allow_official
    result["note"] = "Confirmatory RQ2 is per-factor LOFO. Do not interpret a pooled U~A fit."
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({"out": out, "factors": sorted((result.get("by_factor") or {}).keys()), "do_not_pool_raw_U": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
