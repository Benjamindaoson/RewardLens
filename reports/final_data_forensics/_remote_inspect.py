#!/usr/bin/env python3
"""Remote inventory for RewardLens Final Data Forensics P0. Read-only."""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter

PHASE2 = "/root/autodl-fs/RewardLens/results/phase2"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_jsonl(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.loads(handle.readline())


def summarize_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    out = {"path": path, "size": os.path.getsize(path), "type": type(data).__name__}
    if isinstance(data, dict):
        out["keys"] = list(data)
        kids = {}
        for key, value in data.items():
            if isinstance(value, list):
                kids[key] = {
                    "type": "list",
                    "n": len(value),
                    "keys0": list(value[0]) if value and isinstance(value[0], dict) else None,
                }
            elif isinstance(value, dict):
                kids[key] = {"type": "dict", "n": len(value), "sub": list(value)[:20]}
            else:
                kids[key] = {"type": type(value).__name__, "value": value}
        out["children"] = kids
    elif isinstance(data, list):
        out["n"] = len(data)
        out["keys0"] = list(data[0]) if data and isinstance(data[0], dict) else None
    return out


def main() -> None:
    report = {
        "hostname": os.uname().nodename,
        "gpu": os.popen("nvidia-smi -L 2>/dev/null").read().strip() or "NO_GPU",
        "files": {},
    }
    targets = [
        os.path.join(PHASE2, "PHASE2_DOWNSTREAM_V2_PHYSICAL_DISJOINT_manifest.jsonl"),
        os.path.join(PHASE2, "phase2_v2_physical_sha_manifests.json"),
        os.path.join(PHASE2, "phase2_v2_zero_overlap_receipt.json"),
        os.path.join(PHASE2, "phase2_data_leakage_receipt.json"),
        os.path.join(PHASE2, "phase2_v2_repair_receipt.json"),
        os.path.join(PHASE2, "READY_FOR_PHASE2_GPU.json"),
        os.path.join(PHASE2, "phase2_v2_final_hashes.json"),
        "/root/autodl-fs/RewardLens/engineering_handoff/internvl_resume/static_manifest.jsonl",
        "/root/autodl-fs/RewardLens/engineering_handoff/internvl_resume/audit_manifest.linux.jsonl",
        "/root/autodl-tmp/RewardLens/code/manifests/fast_eval/static_manifest.jsonl",
        "/root/autodl-tmp/RewardLens/code/manifests/fast_eval/downstream_manifest.jsonl",
        "/root/autodl-tmp/RewardLens/code/outputs/qwen_full/audit_manifest.linux.jsonl",
    ]
    for path in targets:
        info = {"exists": os.path.isfile(path)}
        if info["exists"]:
            info["size"] = os.path.getsize(path)
            info["sha256"] = sha256_file(path)
            if path.endswith(".jsonl"):
                row = first_jsonl(path)
                info["n_lines"] = sum(1 for _ in open(path, "r", encoding="utf-8"))
                info["keys"] = sorted(row)
                slim = {k: row[k] for k in row if k not in {"candidates", "source_manifest"}}
                if "candidates" in row:
                    slim["n_candidates"] = len(row["candidates"] or [])
                info["sample"] = slim
            elif path.endswith(".json"):
                info["summary"] = summarize_json(path)
        report["files"][path] = info

    sha_path = os.path.join(PHASE2, "phase2_v2_physical_sha_manifests.json")
    if os.path.isfile(sha_path):
        with open(sha_path, "r", encoding="utf-8") as handle:
            sha = json.load(handle)
        report["sha_manifest_top"] = summarize_json(sha_path)
        # Independent intersection if structure allows.
        def collect_hashes(obj):
            found = []
            if isinstance(obj, dict):
                if "sha256" in obj:
                    found.append(str(obj["sha256"]))
                if "physical_image_sha256" in obj:
                    found.append(str(obj["physical_image_sha256"]))
                for value in obj.values():
                    found.extend(collect_hashes(value))
            elif isinstance(obj, list):
                for value in obj:
                    found.extend(collect_hashes(value))
            return found

        report["sha_leaf_hash_count"] = len(collect_hashes(sha))

    down_path = os.path.join(PHASE2, "PHASE2_DOWNSTREAM_V2_PHYSICAL_DISJOINT_manifest.jsonl")
    if os.path.isfile(down_path):
        datasets = Counter()
        factors = Counter()
        image_ids = Counter()
        item_ids = []
        hash_keys = Counter()
        with open(down_path, "r", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                datasets[str(row.get("dataset"))] += 1
                factors[str(row.get("factor"))] += 1
                image_ids[str(row.get("image_id"))] += 1
                item_ids.append(str(row.get("item_id")))
                for key in ("image_sha256", "physical_image_sha256", "sha256", "content_sha256"):
                    if row.get(key):
                        hash_keys[key] += 1
        report["downstream_v2_counts"] = {
            "n": len(item_ids),
            "n_unique_item_id": len(set(item_ids)),
            "datasets": dict(datasets),
            "factors": dict(factors),
            "n_unique_image_id": len(image_ids),
            "hash_keys": dict(hash_keys),
        }

    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
