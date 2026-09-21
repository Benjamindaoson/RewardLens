#!/usr/bin/env python3
"""P0 source-identity probe: audit scenes vs downstream natural images. CPU only."""
from __future__ import annotations

import json
import os
import re
from collections import Counter

SCENE_ROOTS = [
    "/root/autodl-tmp/RewardLens/code/images/outputs",
    "/root/autodl-tmp/RewardLens/code/outputs",
    "/root/autodl-fs/RewardLens/phase2_v2_sources",
]
NATURAL_TOKENS = re.compile(
    r"(gqa|coco|tallyqa|visual.?genome|vg_100k|/images/\d+\.jpg|source_image)",
    re.I,
)


def walk_scenes(limit_files: int = 40) -> dict:
    found_dirs = []
    scenes = []
    for root in SCENE_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            if os.path.basename(dirpath) != "scenes":
                continue
            found_dirs.append(dirpath)
            for name in sorted(filenames):
                if name.endswith(".json"):
                    scenes.append(os.path.join(dirpath, name))
    report = {
        "scene_dirs": found_dirs,
        "n_scene_files_seen": len(scenes),
        "sampled": [],
        "keys_union": [],
        "natural_image_hits": [],
        "source_image_fields_present": Counter(),
    }
    keys = set()
    hits = []
    for path in scenes[:limit_files]:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        flat_keys = sorted(_all_keys(data))
        keys.update(flat_keys)
        blob = json.dumps(data, ensure_ascii=False)
        hit = bool(NATURAL_TOKENS.search(blob))
        if hit:
            hits.append({"path": path, "keys": flat_keys[:40]})
        report["sampled"].append(
            {
                "path": path,
                "top_keys": list(data)[:20] if isinstance(data, dict) else type(data).__name__,
                "n_objects": len(data.get("objects") or []) if isinstance(data, dict) else None,
                "image_filename": data.get("image_filename") if isinstance(data, dict) else None,
                "directions": list((data.get("directions") or {}))[:8] if isinstance(data, dict) else None,
                "natural_token_hit": hit,
            }
        )
    # Full scan for natural tokens (paths only, cheap).
    n_scan = 0
    n_hit = 0
    for path in scenes:
        n_scan += 1
        try:
            text = open(path, "r", encoding="utf-8").read(200000)
        except OSError:
            continue
        if NATURAL_TOKENS.search(text):
            n_hit += 1
            if len(hits) < 20:
                hits.append({"path": path, "preview": text[:200]})
    report["n_scene_files_scanned"] = n_scan
    report["n_natural_token_hits"] = n_hit
    report["natural_image_hits"] = hits
    report["keys_union"] = sorted(keys)
    return report


def _all_keys(obj, prefix=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = "%s%s" % (prefix, k)
            out.append(key)
            out.extend(_all_keys(v, key + "."))
    elif isinstance(obj, list) and obj:
        out.extend(_all_keys(obj[0], prefix + "[]."))
    return out


if __name__ == "__main__":
    print(json.dumps(walk_scenes(), indent=2)[:20000])
