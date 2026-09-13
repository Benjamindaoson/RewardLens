#!/usr/bin/env python3
"""Shared CLI runner used by probe / signal-gate / full-audit scripts."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from inference.adapters.dummy import DummyAdapter  # noqa: E402
from inference.common import load_items, run_items  # noqa: E402
from inference.device import probe_device, write_probe  # noqa: E402
from inference.parsers.ab_parser import parse_ab  # noqa: E402


def build_adapter(args: argparse.Namespace):
    if args.adapter == "dummy":
        adapter = DummyAdapter(model_id=args.model_id, fail_mode=args.fail_mode or None)
        return adapter
    from inference.adapters.hf_vlm import HuggingFaceVLMAdapter
    from models.registry import get_model

    rec = get_model(args.model_id)
    from inference.adapters import ADAPTERS

    cls = ADAPTERS.get(args.adapter, HuggingFaceVLMAdapter)
    if args.adapter == "hf":
        cls = HuggingFaceVLMAdapter
    adapter = cls(
        model_id=rec["model_id"],
        checkpoint=rec["checkpoint"],
        dtype="bfloat16",
        attn_implementation="sdpa",
        trust_remote_code=bool(rec.get("trust_remote_code")),
        requires_flash_attention=bool(rec.get("requires_flash_attention")),
        requires_quantization=bool(rec.get("requires_quantization")),
    )
    return adapter


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--fail-jsonl", default=None)
    parser.add_argument("--model-id", default="dummy_cpu")
    parser.add_argument("--adapter", choices=["dummy", "hf", "qwen_vl", "gemma", "llama_vision", "molmo", "specialized_reward"], default="dummy")
    parser.add_argument("--images-root", default=None)
    parser.add_argument("--fail-mode", default="", help="dummy only: oom|error|parse|timeout")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--env-json", default=None)


def main_with_stage(stage: str) -> int:
    parser = argparse.ArgumentParser()
    add_common_args(parser)
    args = parser.parse_args()
    fail_jsonl = args.fail_jsonl or os.path.join(os.path.dirname(args.out_jsonl), "failures.jsonl")
    env_path = args.env_json or os.path.join(os.path.dirname(args.out_jsonl), "environment_report.json")
    items = load_items(args.manifest)
    if args.limit:
        items = items[: args.limit]
    report = probe_device()
    report["stage"] = stage
    report["model_id"] = args.model_id
    write_probe(env_path, report)
    adapter = build_adapter(args)
    adapter.load_model()
    try:
        summary = run_items(
            items=items,
            adapter=adapter,
            model_id=args.model_id,
            out_jsonl=args.out_jsonl,
            fail_jsonl=fail_jsonl,
            parse_fn=parse_ab,
            images_root=args.images_root,
        )
    finally:
        adapter.cleanup()
    summary_path = os.path.join(os.path.dirname(args.out_jsonl), "run_summary.json")
    with open(summary_path, "w", encoding="utf-8") as handle:
        json.dump({"stage": stage, **summary}, handle, indent=2)
    print(json.dumps({"stage": stage, **summary}, indent=2))
    return 0 if summary["failed"] == 0 or args.adapter == "dummy" else 1
