#!/usr/bin/env python3
from __future__ import annotations

import json
import os

NEEDLES = [
    "/root/autodl-tmp/RewardLens/code/images/outputs/count_scale_v1/images/count_000000_base.png",
    "/root/autodl-tmp/RewardLens/code/images/outputs",
    "/root/autodl-tmp/RewardLens/code/outputs",
    "/root/autodl-fs/RewardLens",
]


def exists(path):
    return {"path": path, "isfile": os.path.isfile(path), "isdir": os.path.isdir(path)}


out = {"checks": [exists(p) for p in NEEDLES], "listings": {}}
img_dir = "/root/autodl-tmp/RewardLens/code/images"
if os.path.isdir(img_dir):
    out["listings"]["images"] = os.listdir(img_dir)[:50]
root = "/root/autodl-tmp/RewardLens/code"
if os.path.isdir(root):
    out["listings"]["code"] = os.listdir(root)[:80]

# find scenes
hits = []
for start in ["/root/autodl-tmp/RewardLens", "/root/autodl-fs/RewardLens"]:
    if not os.path.isdir(start):
        continue
    for dirpath, dirnames, filenames in os.walk(start):
        base = os.path.basename(dirpath)
        if base in {"models", "expanded_models", "cache", ".git", "venv"}:
            dirnames[:] = []
            continue
        if "scenes" in base or any(name.endswith("_base.json") for name in filenames[:20]):
            jsons = [n for n in filenames if n.endswith(".json")]
            if jsons:
                hits.append({"dir": dirpath, "n_json": len(jsons), "sample": jsons[:5]})
        if len(hits) >= 30:
            break
    if len(hits) >= 30:
        break
out["scene_hits"] = hits
print(json.dumps(out, indent=2))
