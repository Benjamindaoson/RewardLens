#!/usr/bin/env python3
"""Locate audit/static/downstream artifacts and independently verify physical disjointness."""
from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict

PHASE2 = "/root/autodl-fs/RewardLens/results/phase2"
SHA_PATH = os.path.join(PHASE2, "phase2_v2_physical_sha_manifests.json")
SPOT_N = 12


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def numeric_tail(text: str) -> str:
    digits = []
    for ch in reversed(str(text)):
        if ch.isdigit():
            digits.append(ch)
        elif digits:
            break
    return "".join(reversed(digits))


def main() -> None:
    with open(SHA_PATH, "r", encoding="utf-8") as handle:
        sha = json.load(handle)

    sets = {}
    identity_rows = []
    collisions = []
    for split, rows in sha.items():
        phys = {}
        logical = {}
        numeric = defaultdict(list)
        source_ids = {}
        for row in rows:
            pid = row.get("physical_image_id")
            iid = str(row.get("item_id"))
            image_id = str(row.get("image_id") or "")
            phys.setdefault(pid, []).append(iid)
            logical.setdefault(iid, []).append(pid)
            tail = numeric_tail(iid)
            if tail:
                numeric[tail].append((split, iid, image_id, pid, row.get("factor"), row.get("carrier")))
            source_ids.setdefault(image_id, []).append((split, iid, pid))
            identity_rows.append(
                {
                    "split": split,
                    "dataset_or_carrier": row.get("carrier"),
                    "factor": row.get("factor"),
                    "variant": row.get("split"),
                    "item_id": iid,
                    "source_image_id": image_id,
                    "physical_image_id": pid,
                    "image_path": row.get("image_path"),
                    "numeric_tail": tail,
                }
            )
        sets[split] = {
            "n_rows": len(rows),
            "n_unique_item_id": len(logical),
            "n_unique_physical": len(phys),
            "n_unique_image_id": len({str(r.get("image_id") or "") for r in rows}),
            "duplicate_physical_groups": {k: v for k, v in phys.items() if len(v) > 1},
            "physical_ids": set(phys),
            "item_ids": set(logical),
            "image_ids": {str(r.get("image_id") or "") for r in rows if r.get("image_id")},
            "numeric": numeric,
        }

    pair_names = [("audit", "static"), ("audit", "downstream_v2"), ("static", "downstream_v2")]
    intersections = {}
    for a, b in pair_names:
        key = "%s__%s" % (a, b)
        intersections[key] = {
            "physical_image_id": len(sets[a]["physical_ids"] & sets[b]["physical_ids"]),
            "item_id": len(sets[a]["item_ids"] & sets[b]["item_ids"]),
            "source_image_id": len(sets[a]["image_ids"] & sets[b]["image_ids"]),
            "physical_examples": sorted(sets[a]["physical_ids"] & sets[b]["physical_ids"])[:10],
            "item_id_examples": sorted(sets[a]["item_ids"] & sets[b]["item_ids"])[:10],
            "source_image_id_examples": sorted(sets[a]["image_ids"] & sets[b]["image_ids"])[:10],
        }

    # Numeric-tail collisions across splits.
    all_numeric = defaultdict(list)
    for split, info in sets.items():
        for tail, recs in info["numeric"].items():
            all_numeric[tail].extend(recs)
    numeric_cross = []
    for tail, recs in all_numeric.items():
        splits = {r[0] for r in recs}
        if len(splits) > 1:
            phys = {r[3] for r in recs}
            numeric_cross.append(
                {
                    "numeric_tail": tail,
                    "n": len(recs),
                    "splits": sorted(splits),
                    "n_distinct_physical": len(phys),
                    "same_physical": len(phys) == 1,
                    "records": [
                        {
                            "split": r[0],
                            "item_id": r[1],
                            "image_id": r[2],
                            "physical_image_id": r[3],
                            "factor": r[4],
                            "carrier": r[5],
                        }
                        for r in recs
                    ],
                }
            )

    # Spot-check physical hashes against files that still exist.
    spot = []
    checked = 0
    for split, rows in sha.items():
        for row in rows:
            if checked >= SPOT_N:
                break
            path = row.get("image_path")
            pid = row.get("physical_image_id")
            exists = bool(path and os.path.isfile(path))
            rec = {
                "split": split,
                "item_id": row.get("item_id"),
                "image_path": path,
                "exists": exists,
                "declared_physical_image_id": pid,
            }
            if exists:
                rec["recomputed_sha256"] = sha256_file(path)
                rec["match"] = rec["recomputed_sha256"] == pid
                checked += 1
            spot.append(rec)
        if checked >= SPOT_N:
            continue

    # Model artifact hunt
    model_roots = {
        "qwen3_vl_4b_instruct": os.path.join(PHASE2, "gpu_4model_v1/qwen3_vl_4b_instruct"),
        "gemma3_4b_it": os.path.join(PHASE2, "gpu_4model_v1/gemma3_4b_it"),
        "molmo_7b_d_0924": os.path.join(PHASE2, "gpu_4model_v1/molmo_7b_d_0924"),
        "skywork_vl_reward_7b": os.path.join(PHASE2, "gpu_parallel_017/skywork_vl_reward_7b"),
        "idefics3_8b_llama3": os.path.join(PHASE2, "distributed_v1/idefics3_8b_llama3"),
        "phi35_vision_instruct": os.path.join(PHASE2, "distributed_v1/phi35_vision_instruct"),
        "llava_onevision_qwen2_7b": os.path.join(PHASE2, "distributed_v1/llava_onevision_qwen2_7b"),
        "internvl3_8b_hf": os.path.join(PHASE2, "distributed_v1/internvl3_8b_hf"),
    }
    artifacts = {}
    for model, root in model_roots.items():
        found = []
        if os.path.isdir(root):
            for dirpath, _, filenames in os.walk(root):
                for name in filenames:
                    if name.endswith((".jsonl", ".json")) and any(
                        token in name.lower() for token in ("audit", "static", "pairs", "selection", "utility", "metric")
                    ):
                        path = os.path.join(dirpath, name)
                        rec = {
                            "rel": os.path.relpath(path, root),
                            "size": os.path.getsize(path),
                            "sha256": sha256_file(path) if os.path.getsize(path) < 20_000_000 else "SKIPPED_LARGE",
                        }
                        if name.endswith(".jsonl") and os.path.getsize(path) > 0:
                            with open(path, "r", encoding="utf-8") as handle:
                                first = handle.readline()
                            try:
                                row = json.loads(first)
                                rec["keys"] = sorted(row)
                                rec["item_id"] = row.get("item_id")
                                rec["variant"] = row.get("variant")
                                rec["triplet_id"] = row.get("triplet_id")
                                rec["pool_id"] = row.get("pool_id")
                            except Exception as exc:
                                rec["parse_error"] = str(exc)
                        found.append(rec)
        artifacts[model] = {"root": root, "exists": os.path.isdir(root), "files": found}

    # Compact sets for JSON
    compact_sets = {}
    for split, info in sets.items():
        compact_sets[split] = {
            "n_rows": info["n_rows"],
            "n_unique_item_id": info["n_unique_item_id"],
            "n_unique_physical": info["n_unique_physical"],
            "n_unique_image_id": info["n_unique_image_id"],
            "n_duplicate_physical_groups": len(info["duplicate_physical_groups"]),
            "duplicate_physical_groups_preview": [
                {"physical_image_id": k, "item_ids": v[:8], "n": len(v)}
                for k, v in list(info["duplicate_physical_groups"].items())[:8]
            ],
        }

    same_physical_numeric = [c for c in numeric_cross if c["same_physical"]]
    different_physical_numeric = [c for c in numeric_cross if not c["same_physical"]]

    report = {
        "hostname": os.uname().nodename,
        "physical_identity_definition": "SHA256(raw image bytes) stored as physical_image_id",
        "sets": compact_sets,
        "intersections": intersections,
        "physical_disjoint_pass": all(v["physical_image_id"] == 0 for v in intersections.values()),
        "numeric_tail_cross_split": {
            "n_colliding_tails": len(numeric_cross),
            "n_same_physical": len(same_physical_numeric),
            "n_different_physical": len(different_physical_numeric),
            "same_physical_examples": same_physical_numeric[:15],
            "different_physical_examples": different_physical_numeric[:15],
        },
        "spot_check": {
            "n_attempted": len(spot),
            "n_existing_files": sum(1 for r in spot if r.get("exists")),
            "n_hash_match": sum(1 for r in spot if r.get("match")),
            "rows": [r for r in spot if r.get("exists")][:SPOT_N],
        },
        "artifacts": artifacts,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
