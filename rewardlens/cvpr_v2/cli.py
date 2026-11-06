"""Offline, zero-service CVPR audit CLI with machine-readable and HTML output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import audit_summary, matched_pairs, shared_support_gaps
from .predictive import compare_predictors
from .protocol import validate_records
from .report import render_html


def _jsonl(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as handle:
        for lineno, line in enumerate(handle, 1):
            if line.strip():
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{lineno}: {exc}") from exc
                if not isinstance(value, dict):
                    raise ValueError(f"{path}:{lineno}: expected object")
                out.append(value)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="RewardLens CVPR V2 strict evaluation")
    parser.add_argument("--audit-jsonl", required=True, help="one row per model/triplet/image variant")
    parser.add_argument("--static-jsonl", help="independent static accuracies, not derived from audit")
    parser.add_argument("--shift-jsonl", help="held-out model/domain shift outcomes with independent targets")
    parser.add_argument("--matching-tolerance", type=float, default=0.01)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-html")
    args = parser.parse_args()
    if not 0 <= args.matching_tolerance <= 1:
        parser.error("matching tolerance must be between 0 and 1")
    observations = validate_records(_jsonl(args.audit_jsonl))
    pairs = matched_pairs(_jsonl(args.static_jsonl), tolerance=args.matching_tolerance) if args.static_jsonl else []
    result = {"schema_version": "rewardlens-cvpr-v2-prototype-1",
              "data_type": "external_predictions_not_generated_by_this_tool",
              "n_observations": len(observations),
              "audit": audit_summary(observations),
              "matched_pairs": shared_support_gaps(observations, pairs),
              "predictive": compare_predictors(_jsonl(args.shift_jsonl)) if args.shift_jsonl else None}
    output = Path(args.out_json)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.out_html:
        html = Path(args.out_html)
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text(render_html(result), encoding="utf-8")
    print(json.dumps({"json": str(output), "n_observations": len(observations),
                      "n_metrics": len(result["audit"]), "n_matched_pairs": len(pairs)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
