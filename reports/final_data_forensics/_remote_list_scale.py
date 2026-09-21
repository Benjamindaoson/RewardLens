#!/usr/bin/env python3
import json, os
root = "/root/autodl-tmp/RewardLens/code/images/outputs"
out = {"root_listing": os.listdir(root) if os.path.isdir(root) else None, "factors": {}}
if os.path.isdir(root):
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        rec = {"isdir": os.path.isdir(path)}
        if os.path.isdir(path):
            rec["children"] = os.listdir(path)
            for sub in rec["children"]:
                sp = os.path.join(path, sub)
                if os.path.isdir(sp):
                    files = os.listdir(sp)
                    rec[sub] = {"n": len(files), "sample": files[:8]}
        out["factors"][name] = rec
# also outputs/ at code root
alt = "/root/autodl-tmp/RewardLens/code/outputs"
out["code_outputs"] = os.listdir(alt)[:40] if os.path.isdir(alt) else None
if os.path.isdir(alt):
    for name in os.listdir(alt):
        p = os.path.join(alt, name)
        if os.path.isdir(p) and ("scale" in name or "qwen" in name or "scene" in name):
            out.setdefault("code_outputs_detail", {})[name] = os.listdir(p)[:20]
print(json.dumps(out, indent=2)[:15000])
