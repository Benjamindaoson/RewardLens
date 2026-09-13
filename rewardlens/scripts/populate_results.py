#!/usr/bin/env python3
"""Fill paper/generated_results.md from real artifacts. Does not invent numbers."""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
try:
    import yaml
except ImportError:
    yaml = None


def load_placeholder_map(path: str) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required to read result_placeholders.yaml")
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def summarize_artifact(path: str) -> str:
    if not os.path.isfile(path):
        return "MISSING %s" % path
    if path.endswith(".json"):
        payload = json.load(open(path, encoding="utf-8"))
        if payload.get("synthetic") or payload.get("fixture"):
            return "REFUSED synthetic/fixture: %s" % path
        return json.dumps(payload, indent=2)[:4000]
    if path.endswith(".jsonl"):
        n = sum(1 for line in open(path, encoding="utf-8") if line.strip())
        return "%s n=%d" % (path, n)
    if path.endswith(".csv"):
        n = sum(1 for _ in open(path, encoding="utf-8")) - 1
        return "%s rows=%d" % (path, n)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default=os.path.join(ROOT, "paper", "result_placeholders.yaml"))
    parser.add_argument("--out", default=os.path.join(ROOT, "paper", "generated_results.md"))
    parser.add_argument("--unsafe-inject", action="store_true")
    args = parser.parse_args()
    mapping = load_placeholder_map(args.map)
    lines = [
        "# Generated result snippets",
        "",
        "Auto-generated from artifacts. Not a substitute for the paper draft.",
        "Missing or synthetic artifacts are reported, never invented.",
        "",
    ]
    for key, spec in (mapping.get("placeholders") or {}).items():
        lines.append("## %s" % key)
        lines.append("")
        lines.append("Anchor: `%s`" % spec.get("paper_anchor"))
        lines.append("")
        found = False
        for rel in spec.get("artifacts") or []:
            path = rel if os.path.isabs(rel) else os.path.join(PROJECT, rel)
            body = summarize_artifact(path)
            lines.append("```")
            lines.append(body)
            lines.append("```")
            lines.append("")
            if not body.startswith("MISSING") and not body.startswith("REFUSED"):
                found = True
        if not found:
            lines.append("*No real artifact yet.*")
            lines.append("")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    print("WROTE", args.out)
    if args.unsafe_inject:
        print("REFUSING to overwrite iclr2027_draft.md from this script; inject manually.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
