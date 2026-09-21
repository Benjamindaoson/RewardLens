#!/usr/bin/env python3
import hashlib
import json

files = {
    "qwen": "/root/autodl-fs/RewardLens/results/qwen3_vl_4b_instruct/qwen_full_audit.jsonl",
    "gemma": "/root/autodl-fs/RewardLens/results/gemma3_4b_it/full_audit.jsonl",
    "molmo": "/root/autodl-fs/RewardLens/results/molmo_7b_d_0924/full_audit.jsonl",
    "skywork": "/root/autodl-fs/RewardLens/results/skywork_vl_reward_7b/full_audit.jsonl",
}
want = {
    "qwen": "36c02585da47bdbf1bfa4f71e2ca339b146f6adc9fe86623e9fe42988bd0c48e",
    "gemma": "3a38334405de61793afe5e947eb05c7725e8951ce63f830e5a11eef7e4b90b21",
    "molmo": "f6144834ef108523ef50fbc2c608df68cd0972b30c2d69c24444de63f9fd7115",
    "skywork": "ba34dcc317ee395e36073454c1ee9e62f76d6205ae4f563e863292cb652fb0f2",
}
out = {}
for key, path in files.items():
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    h = digest.hexdigest()
    with open(path, "r", encoding="utf-8") as handle:
        first = handle.readline()
        n = 1 + sum(1 for line in handle if line.strip())
    row = json.loads(first)
    out[key] = {
        "path": path,
        "n": n,
        "sha256": h,
        "sha_match_integrity_audit": h == want[key],
        "item_id": row.get("item_id"),
        "variant": row.get("variant"),
        "keys": sorted(row),
    }
print(json.dumps(out, indent=2))
