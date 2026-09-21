#!/usr/bin/env python3
"""Find original-four audit judgment files by sha256 and first-row identity."""
from __future__ import annotations

import hashlib
import json
import os

TARGETS = {
    "qwen3_vl_4b_instruct": "36c02585da47bdbf1bfa4f71e2ca339b146f6adc9fe86623e9fe42988bd0c48e",
    "gemma3_4b_it": "3a38334405de61793afe5e947eb05c7725e8951ce63f830e5a11eef7e4b90b21",
    "molmo_7b_d_0924": "f6144834ef108523ef50fbc2c608df68cd0972b30c2d69c24444de63f9fd7115",
    "skywork_vl_reward_7b": "ba34dcc317ee395e36073454c1ee9e62f76d6205ae4f563e863292cb652fb0f2",
}

ROOTS = [
    "/root/autodl-fs/RewardLens/results/phase2/gpu_4model_v1",
    "/root/autodl-fs/RewardLens/results/phase2/gpu_parallel_017",
    "/root/autodl-fs/RewardLens/results/phase2/distributed_v1",
    "/root/autodl-fs/RewardLens/results/phase2/paper_analysis",
    "/root/autodl-fs/RewardLens/publication",
    "/root/autodl-tmp/RewardLens",
]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def peek_jsonl(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        first = handle.readline()
    row = json.loads(first)
    n = 1
    with open(path, "r", encoding="utf-8") as handle:
        n = sum(1 for line in handle if line.strip())
    return {
        "item_id": row.get("item_id"),
        "variant": row.get("variant"),
        "triplet_id": row.get("triplet_id"),
        "keys": sorted(row),
        "n_lines": n,
    }


def main() -> None:
    found_by_hash = {}
    candidates = []
    seen = set()
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in {".git", "models", "expanded_models", "cache", "__pycache__"}]
            for name in filenames:
                if name.endswith(".jsonl") and ("audit" in name.lower() or "static" in name.lower() or "judgment" in name.lower()):
                    path = os.path.join(dirpath, name)
                    if path in seen:
                        continue
                    seen.add(path)
                    try:
                        digest = sha256_file(path)
                    except OSError:
                        continue
                    rec = {"path": path, "sha256": digest, "size": os.path.getsize(path)}
                    try:
                        rec.update(peek_jsonl(path))
                    except Exception as exc:
                        rec["peek_error"] = str(exc)
                    for model, target in TARGETS.items():
                        if digest == target:
                            found_by_hash[model] = rec
                    if rec.get("variant") in {"base", "relevant", "irrelevant"} or str(rec.get("item_id", "")).endswith(":base"):
                        candidates.append(rec)
    print(json.dumps({"found_by_hash": found_by_hash, "audit_like": candidates[:40], "n_audit_like": len(candidates)}, indent=2))


if __name__ == "__main__":
    main()
