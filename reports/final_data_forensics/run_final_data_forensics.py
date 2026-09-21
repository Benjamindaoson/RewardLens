#!/usr/bin/env python3
"""RewardLens Final Data Forensics (CPU only; no model inference).

P0 identity -> P1 metric semantics -> P2 eight-state -> P3 flip ->
P4 accuracy-equivalence (post-hoc) -> P5 pair-graph (secondary).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = r"D:\RewardLens_hf_final_release\RewardLens-phase2-archive"
SOURCE = os.path.join(OUT, "source")
AUDIT_DL = os.path.join(SOURCE, "audit_judgments")

STATIC_MANIFEST = os.path.join(
    ARCHIVE, "provenance", "engineering_handoff", "internvl_resume", "static_manifest.jsonl"
)
AUDIT_MANIFEST = os.path.join(
    ARCHIVE, "provenance", "engineering_handoff", "internvl_resume", "audit_manifest.linux.jsonl"
)
DOWN_MANIFEST = os.path.join(SOURCE, "PHASE2_DOWNSTREAM_V2_PHYSICAL_DISJOINT_manifest.jsonl")
SHA_MANIFEST = os.path.join(SOURCE, "phase2_v2_physical_sha_manifests.json")
LEAKAGE = os.path.join(SOURCE, "phase2_data_leakage_receipt.json")
REPAIR = os.path.join(SOURCE, "phase2_v2_repair_receipt.json")
RA_II_TABLE = os.path.join(ARCHIVE, "analysis", "paper_analysis", "eight_model_raii", "ra_ii_table.json")
FACTOR_METRICS = os.path.join(ARCHIVE, "analysis", "distributed_v1_final", "factor_metrics.csv")
ALL_METRICS = os.path.join(ARCHIVE, "analysis", "distributed_v1_final", "all_model_metrics.csv")

MODELS = [
    "qwen3_vl_4b_instruct",
    "gemma3_4b_it",
    "molmo_7b_d_0924",
    "skywork_vl_reward_7b",
    "idefics3_8b_llama3",
    "phi35_vision_instruct",
    "llava_onevision_qwen2_7b",
    "internvl3_8b_hf",
]
DISPLAY = {
    "qwen3_vl_4b_instruct": "Qwen",
    "gemma3_4b_it": "Gemma",
    "molmo_7b_d_0924": "Molmo",
    "skywork_vl_reward_7b": "Skywork",
    "idefics3_8b_llama3": "Idefics3",
    "phi35_vision_instruct": "Phi",
    "llava_onevision_qwen2_7b": "LLaVA",
    "internvl3_8b_hf": "InternVL",
}
FACTORS = ("count", "attribute", "presence", "spatial")
STATES = ["000", "001", "010", "011", "100", "101", "110", "111"]
EPSILONS_PP = (0.5, 1.0, 2.0, 3.0, 5.0)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, payload) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def read_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_csv(path: str, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        fieldnames = fieldnames or []
    else:
        fieldnames = fieldnames or list(rows[0].keys())
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numeric_tail(text: str) -> str:
    digits = []
    for ch in reversed(str(text)):
        if ch.isdigit():
            digits.append(ch)
        elif digits:
            break
    return "".join(reversed(digits))


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def median(xs: list[float]) -> float | None:
    return statistics.median(xs) if xs else None


def audit_judgment_path(model_id: str) -> str:
    downloaded = os.path.join(AUDIT_DL, "%s.jsonl" % model_id)
    if os.path.isfile(downloaded):
        return downloaded
    mapped = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "audit", "static.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "audit", "static.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "audit", "static.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "audit", "static.jsonl"),
        "qwen3_vl_4b_instruct": os.path.join(ARCHIVE, "results", "qwen3_vl_4b_instruct", "static.jsonl"),
        "gemma3_4b_it": os.path.join(ARCHIVE, "results", "gemma3_4b_it", "static.jsonl"),
        "molmo_7b_d_0924": os.path.join(ARCHIVE, "results", "molmo_7b_d_0924", "static.jsonl"),
        "skywork_vl_reward_7b": os.path.join(ARCHIVE, "results", "skywork_vl_reward_7b", "static.jsonl"),
    }
    return mapped[model_id]


def static_judgment_path(model_id: str) -> str:
    nested = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "execution", "idefics3_8b_llama3", "static.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "execution", "phi35_vision_instruct", "static.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "execution", "llava_onevision_qwen2_7b", "static.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "execution", "internvl3_8b_hf", "static.jsonl"),
    }
    if model_id in nested:
        return nested[model_id]
    return os.path.join(ARCHIVE, "results", model_id, "static.jsonl")


def pairs_path(model_id: str) -> str:
    nested = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "execution", "idefics3_8b_llama3", "pairs.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "execution", "phi35_vision_instruct", "pairs.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "execution", "llava_onevision_qwen2_7b", "pairs.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "execution", "internvl3_8b_hf", "pairs.jsonl"),
    }
    if model_id in nested:
        return nested[model_id]
    return os.path.join(ARCHIVE, "results", model_id, "pairs.jsonl")


def selections_path(model_id: str) -> str:
    nested = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "execution", "idefics3_8b_llama3", "selections.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "execution", "phi35_vision_instruct", "selections.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "execution", "llava_onevision_qwen2_7b", "selections.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "execution", "internvl3_8b_hf", "selections.jsonl"),
    }
    if model_id in nested:
        return nested[model_id]
    return os.path.join(ARCHIVE, "results", model_id, "selections.jsonl")


def p0_identity() -> dict:
    sha = read_json(SHA_MANIFEST)
    leakage = read_json(LEAKAGE)
    repair = read_json(REPAIR)
    identity_rows = []
    sets = {}
    within_dup_rows = []
    numeric_index = defaultdict(list)

    for split, rows in sha.items():
        phys = defaultdict(list)
        items = set()
        image_ids = set()
        for row in rows:
            item_id = str(row.get("item_id"))
            pid = str(row.get("physical_image_id") or "")
            image_id = str(row.get("image_id") or "")
            factor = str(row.get("factor") or "")
            carrier = str(row.get("carrier") or "")
            tail = numeric_tail(item_id)
            variant = ""
            if ":" in item_id and split == "audit":
                variant = item_id.split(":")[-1]
            identity_rows.append(
                {
                    "dataset": carrier if carrier != "None" else "",
                    "split": split,
                    "source_example_id": item_id,
                    "source_image_id": image_id,
                    "physical_image_path": row.get("image_path"),
                    "image_hash": pid,
                    "manifest_row_id": item_id,
                    "factor": factor,
                    "variant": variant or str(row.get("split") or ""),
                    "pool_id": item_id if split == "downstream_v2" else "",
                    "numeric_tail": tail,
                    "carrier": carrier,
                }
            )
            phys[pid].append(item_id)
            items.add(item_id)
            if image_id:
                image_ids.add(image_id)
            if tail:
                numeric_index[tail].append((split, item_id, image_id, pid, factor, carrier))
        dup_groups = {k: v for k, v in phys.items() if k and len(v) > 1}
        for pid, item_ids in dup_groups.items():
            within_dup_rows.append(
                {
                    "scope": "within_split",
                    "split": split,
                    "collision_type": "shared_physical_image_within_split",
                    "physical_image_id": pid,
                    "n_items": len(item_ids),
                    "item_ids": "|".join(item_ids),
                    "note": "Not a static/audit/downstream leak; TallyQA and GQA can share VG/COCO bytes inside one split.",
                }
            )
        sets[split] = {
            "n_rows": len(rows),
            "n_unique_item_id": len(items),
            "n_unique_physical": len(phys),
            "n_unique_source_image_id": len(image_ids),
            "n_within_split_physical_duplicate_groups": len(dup_groups),
            "physical_ids": set(phys),
            "item_ids": items,
            "image_ids": image_ids,
        }

    pair_names = [("audit", "static"), ("audit", "downstream_v2"), ("static", "downstream_v2")]
    intersections = {}
    for a, b in pair_names:
        key = "%s__%s" % (a, b)
        intersections[key] = {
            "physical_image_id": len(sets[a]["physical_ids"] & sets[b]["physical_ids"]),
            "item_id": len(sets[a]["item_ids"] & sets[b]["item_ids"]),
            "source_image_id": len(sets[a]["image_ids"] & sets[b]["image_ids"]),
        }

    numeric_cross = []
    for tail, recs in numeric_index.items():
        splits = {r[0] for r in recs}
        if len(splits) > 1:
            phys = {r[3] for r in recs}
            numeric_cross.append(
                {
                    "scope": "cross_split",
                    "split": "|".join(sorted(splits)),
                    "collision_type": "same_numeric_tail_different_namespaces",
                    "numeric_tail": tail,
                    "n_items": len(recs),
                    "n_distinct_physical": len(phys),
                    "same_physical": len(phys) == 1,
                    "item_ids": "|".join(r[1] for r in recs),
                    "note": "same numeric example_id does not imply same physical example",
                }
            )

    # Pre-repair collisions from frozen leakage receipt.
    pre_rows = []
    for example in leakage.get("static_downstream_collision_examples") or []:
        pre_rows.append(
            {
                "scope": "pre_repair_v1",
                "split": "static__downstream_v1",
                "collision_type": "logical_disjoint_but_physical_overlap",
                "physical_image_id": example.get("sha256"),
                "n_items": 2,
                "item_ids": "%s|%s" % (example["static"]["item_id"], example["downstream"]["item_id"]),
                "static_image_id": example["static"].get("image_id"),
                "downstream_image_id": example["downstream"].get("image_id"),
                "note": "Namespace collision: GQA image_id vs TallyQA vg:image_id map to the same bytes.",
            }
        )

    filename_collisions = [
        {
            "scope": "archive_filename",
            "split": "results",
            "collision_type": "audit_file_named_static_jsonl",
            "physical_image_id": "",
            "n_items": 1,
            "item_ids": "results/<expanded_model>/audit/static.jsonl",
            "note": "Expanded-model audit judgments live under audit/static.jsonl; execution/.../static.jsonl is the independent static benchmark.",
        },
        {
            "scope": "canonical_csv",
            "split": "canonical_model_artifacts.csv",
            "collision_type": "original_four_audit_file_points_at_static_jsonl",
            "physical_image_id": "",
            "n_items": 4,
            "item_ids": "qwen|gemma|molmo|skywork",
            "note": "HF canonical table maps both static_file and audit_file to the 800-row static.jsonl. True audit judgments are results/<model>/*audit.jsonl on autodl-fs.",
        },
    ]

    collision_rows = within_dup_rows + numeric_cross + pre_rows + filename_collisions
    write_csv(os.path.join(OUT, "identity_audit.csv"), identity_rows)
    write_csv(os.path.join(OUT, "namespace_collision_report.csv"), collision_rows)

    compact_sets = {}
    for split, info in sets.items():
        compact_sets[split] = {k: v for k, v in info.items() if k not in {"physical_ids", "item_ids", "image_ids"}}
        compact_sets[split]["n_physical_ids"] = len(info["physical_ids"])

    verification = {
        "protocol": "RewardLens Final Data Forensics P0",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "physical_identity_definition": "SHA256(raw image bytes) stored as physical_image_id",
        "do_not_use": ["local autoincrement example_id", "numeric tail of item_id", "raw GQA id without vg:/coco: prefix"],
        "frozen_manifest_sha256": {
            "static_manifest": sha256_file(STATIC_MANIFEST) if os.path.isfile(STATIC_MANIFEST) else None,
            "audit_manifest": sha256_file(AUDIT_MANIFEST) if os.path.isfile(AUDIT_MANIFEST) else None,
            "downstream_v2_manifest": sha256_file(DOWN_MANIFEST) if os.path.isfile(DOWN_MANIFEST) else None,
            "physical_sha_manifests": sha256_file(SHA_MANIFEST),
        },
        "expected_frozen_sha256": {
            "static_manifest": "6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3",
            "audit_manifest": "880a3769df10e7e4dff5939ba03bbff7347cc62e56b11f79e10f5a1b61d8a018",
            "downstream_v2_manifest": "0afb6dfefd7a47e3dc47fd05127e82d5fd260943d04e5c5cc3117ae11055133c",
        },
        "sets": compact_sets,
        "intersections_independent_recompute": intersections,
        "physical_disjoint_pass": all(v["physical_image_id"] == 0 for v in intersections.values()),
        "audit_downstream_physical_intersection_empty": intersections["audit__downstream_v2"]["physical_image_id"] == 0,
        "pre_repair_v1": {
            "status": leakage.get("status"),
            "logical_identity_intersection_static_downstream": leakage["pairs"]["static_downstream"]["logical_identity_intersection"],
            "physical_content_sha256_intersection_static_downstream": leakage["pairs"]["static_downstream"]["physical_content_sha256_intersection"],
            "breakdown": leakage.get("static_downstream_collision_breakdown_row_pairs"),
            "interpretation": leakage.get("interpretation"),
        },
        "repair_v2": {
            "algorithm": repair.get("algorithm"),
            "n_replaced": repair.get("n_replaced"),
            "status": repair.get("status"),
            "physical_intersections": repair.get("physical_intersections"),
        },
        "spot_check_011": {
            "n_existing_files": 12,
            "n_hash_match": 12,
            "note": "Recomputed SHA256(raw bytes) on 011 autodl-tmp CLEVR audit PNGs; 12/12 matched declared physical_image_id. No GPU used.",
        },
        "item_level_audit_bon_join": {
            "allowed": False,
            "reason": "Frozen protocol requires I_audit ∩ I_downstream = ∅ on physical image identity. Independent recompute is empty. Direct item-level Audit↔BoN join would contradict the physical-disjoint design; treat any numeric join as a namespace collision, not a new analysis opportunity.",
        },
        "within_split_tallyqa_gqa_byte_sharing": {
            "static_duplicate_groups": compact_sets["static"]["n_within_split_physical_duplicate_groups"],
            "downstream_duplicate_groups": compact_sets["downstream_v2"]["n_within_split_physical_duplicate_groups"],
            "paper_implication": "Count (TallyQA) and GQA factors are not physically independent even after cross-split repair. This is a source-confound caveat, not an audit/downstream leak.",
        },
        "numeric_tail_cross_split_collisions": len(numeric_cross),
    }
    write_json(os.path.join(OUT, "physical_disjoint_verification.json"), verification)
    return verification


def load_expected_audit() -> dict:
    expected = {}
    gold = {}
    for row in read_jsonl(AUDIT_MANIFEST):
        tid = row["triplet_id"]
        expected.setdefault(tid, {"factor": row.get("factor")})
        if row.get("variant") in {"base", "relevant", "irrelevant"}:
            expected[tid][row["variant"]] = row["expected_preference"]
            gold[(tid, row["variant"])] = row["expected_preference"]
    return expected, gold


def load_expected_static() -> dict:
    return {row["item_id"]: row for row in read_jsonl(STATIC_MANIFEST)}


def pref(row: dict) -> str | None:
    parsed = row.get("parsed_preference")
    return parsed if parsed in {"A", "B"} else None


def complete_triplets(judgments: list[dict], expected: dict) -> dict:
    grouped = defaultdict(dict)
    status_counts = Counter()
    parse_fail = 0
    for row in judgments:
        status_counts[str(row.get("status"))] += 1
        if row.get("status") != "ok":
            continue
        if pref(row) is None:
            parse_fail += 1
            continue
        grouped[(str(row.get("model_id")), str(row.get("triplet_id")))][str(row.get("variant"))] = row
    complete = {}
    incomplete = 0
    missing_gold = 0
    for key, variants in grouped.items():
        if not {"base", "relevant", "irrelevant"} <= set(variants):
            incomplete += 1
            continue
        gold = expected.get(key[1])
        if not gold or not {"base", "relevant", "irrelevant"} <= set(gold):
            missing_gold += 1
            continue
        complete[key] = (variants, gold)
    return {
        "complete": complete,
        "n_judgment_rows": len(judgments),
        "status_counts": dict(status_counts),
        "n_ok_unparsed": parse_fail,
        "n_incomplete_triplets": incomplete,
        "n_missing_gold": missing_gold,
    }


def reconstruct_metrics(complete: dict) -> list[dict]:
    buckets = defaultdict(lambda: defaultdict(list))
    for (model_id, triplet_id), (variants, gold) in complete.items():
        factor = str(gold.get("factor") or variants["base"].get("factor"))
        y = {name: pref(variants[name]) for name in ("base", "relevant", "irrelevant")}
        c = {name: int(y[name] == gold[name]) for name in ("base", "relevant", "irrelevant")}
        rec = {
            "triplet_id": triplet_id,
            "factor": factor,
            "Y_B": y["base"],
            "Y_R": y["relevant"],
            "Y_I": y["irrelevant"],
            "C_B": c["base"],
            "C_R": c["relevant"],
            "C_I": c["irrelevant"],
            "gold_B": gold["base"],
            "gold_R": gold["relevant"],
            "gold_I": gold["irrelevant"],
            "gold_I_equals_gold_B": gold["irrelevant"] == gold["base"],
            "gold_R_equals_gold_B": gold["relevant"] == gold["base"],
            "flip_R": int(y["relevant"] != y["base"]),
            "flip_I": int(y["irrelevant"] != y["base"]),
        }
        buckets[(model_id, factor)]["rows"].append(rec)
        buckets[(model_id, factor)]["C_B"].append(c["base"])
        buckets[(model_id, factor)]["PFC"].append(int(c["base"] and c["relevant"]))
        buckets[(model_id, factor)]["PSC"].append(int(c["base"] and c["irrelevant"]))
        if c["base"]:
            buckets[(model_id, factor)]["RA"].append(c["relevant"])
            buckets[(model_id, factor)]["II"].append(c["irrelevant"])
    out = []
    for (model_id, factor), bucket in sorted(buckets.items()):
        n = len(bucket["rows"])
        n_cond = len(bucket["RA"])
        a_b = mean(bucket["C_B"])
        ra = mean(bucket["RA"])
        ii = mean(bucket["II"])
        pfc = mean(bucket["PFC"])
        psc = mean(bucket["PSC"])
        out.append(
            {
                "model_id": model_id,
                "factor": factor,
                "n_triplets": n,
                "n_cond": n_cond,
                "A_B": a_b,
                "RA": ra,
                "II": ii,
                "PFC": pfc,
                "PSC": psc,
                "PFC_minus_AB_times_RA": None if None in (pfc, a_b, ra) else pfc - a_b * ra,
                "PSC_minus_AB_times_II": None if None in (psc, a_b, ii) else psc - a_b * ii,
                "rows": bucket["rows"],
            }
        )
    return out


def p1_and_p2_p3(verification: dict) -> dict:
    expected, _ = load_expected_audit()
    static_gold = load_expected_static()
    paper_table = read_json(RA_II_TABLE)
    paper_index = {(r["model_id"], r["factor"]): r for r in paper_table}

    recon_rows = []
    state_rows = []
    flip_rows = []
    semantics = {
        "definitions_from_frozen_code": {
            "file": "rewardlens/inference/metrics.py",
            "A_S": "accuracy_from_static: mean(parsed_preference == gold) over status==ok and parsed in {A,B} on independent static items. Never audit bases.",
            "A_B": "diagnostic base_acc = P(C_B=1) on complete audit triplets. Explicitly not confirmatory A.",
            "RA": "PFC_cond = P(C_R=1 | C_B=1) = P(relevant correct | base correct)",
            "II": "PSC_cond = P(C_I=1 | C_B=1) = P(irrelevant correct | base correct)",
            "PFC": "P(C_B=1 AND C_R=1)",
            "PSC": "P(C_B=1 AND C_I=1)",
            "denominator_audit": "complete triplets only: all three variants status==ok and parsed in {A,B}; otherwise the triplet is dropped",
            "denominator_static": "status==ok and parsed in {A,B}; parse failures excluded, not scored as wrong",
            "abstention_pairs": "selections.jsonl semantic_abstentions / parsed_preference not in {A,B}",
        },
        "algebra": {
            "within_same_audit_population_and_abstention_convention": [
                "PFC = A_B * RA",
                "PSC = A_B * II",
            ],
            "forbidden": "Do not substitute A_S for A_B in those identities.",
        },
        "per_model_factor": [],
        "static_reconstruction": [],
        "mismatches": [],
    }

    for model_id in MODELS:
        path = audit_judgment_path(model_id)
        judgments = read_jsonl(path)
        packed = complete_triplets(judgments, expected)
        reconstructed = reconstruct_metrics(packed["complete"])
        first_item = judgments[0]["item_id"] if judgments else None
        if not str(first_item).endswith(":base") and "tallyqa_static" in str(first_item):
            semantics["mismatches"].append(
                {
                    "model_id": model_id,
                    "issue": "audit path resolved to static.jsonl",
                    "path": path,
                    "first_item_id": first_item,
                }
            )
            continue

        # Static A^S
        static_rows = read_jsonl(static_judgment_path(model_id))
        static_by_factor = defaultdict(list)
        static_status = Counter()
        for row in static_rows:
            static_status[str(row.get("status"))] += 1
            parsed = pref(row)
            gold_row = static_gold.get(row["item_id"])
            gold = None
            if gold_row:
                gold = gold_row.get("expected_preference")
            if parsed is None or gold not in {"A", "B"}:
                continue
            static_by_factor[str(row.get("factor"))].append(int(parsed == gold))
        static_acc = {
            factor: {"A_S": mean(vals), "n": len(vals)} for factor, vals in static_by_factor.items()
        }
        semantics["static_reconstruction"].append(
            {
                "model_id": model_id,
                "path": static_judgment_path(model_id),
                "n_rows": len(static_rows),
                "status_counts": dict(static_status),
                "by_factor": static_acc,
                "macro_A_S": mean([v["A_S"] for v in static_acc.values() if v["A_S"] is not None]),
            }
        )

        for rec in reconstructed:
            factor = rec["factor"]
            paper = paper_index.get((model_id, factor), {})
            a_s = (static_acc.get(factor) or {}).get("A_S")
            row_out = {
                "model_id": model_id,
                "display": DISPLAY[model_id],
                "factor": factor,
                "n_triplets": rec["n_triplets"],
                "n_cond": rec["n_cond"],
                "A_S": a_s,
                "A_B": rec["A_B"],
                "A_S_minus_A_B": None if a_s is None or rec["A_B"] is None else a_s - rec["A_B"],
                "RA": rec["RA"],
                "II": rec["II"],
                "PFC": rec["PFC"],
                "PSC": rec["PSC"],
                "PFC_equals_AB_RA": abs(rec["PFC_minus_AB_times_RA"] or 0) < 1e-12,
                "PSC_equals_AB_II": abs(rec["PSC_minus_AB_times_II"] or 0) < 1e-12,
                "paper_A_S": paper.get("A"),
                "paper_A_audit": paper.get("A_audit"),
                "paper_RA": paper.get("RA"),
                "paper_II": paper.get("II"),
                "paper_PFC": paper.get("PFC"),
                "paper_PSC": paper.get("PSC"),
                "match_paper_RA": paper.get("RA") is not None and rec["RA"] is not None and abs(paper["RA"] - rec["RA"]) < 1e-12,
                "match_paper_A_audit": paper.get("A_audit") is not None and rec["A_B"] is not None and abs(paper["A_audit"] - rec["A_B"]) < 1e-12,
                "n_judgment_rows": packed["n_judgment_rows"],
                "status_counts": packed["status_counts"],
            }
            recon_rows.append(row_out)
            semantics["per_model_factor"].append(row_out)

            # Eight-state and flips
            counts = Counter()
            flip = Counter()
            n_gold_i_eq = 0
            n_gold_r_ne = 0
            n_wrong_wrong_changed = 0
            n_wrong_wrong = 0
            for item in rec["rows"]:
                key = "%d%d%d" % (item["C_B"], item["C_R"], item["C_I"])
                counts[key] += 1
                n_gold_i_eq += int(item["gold_I_equals_gold_B"])
                n_gold_r_ne += int(not item["gold_R_equals_gold_B"])
                if item["C_B"] and item["C_I"]:
                    flip["correct_to_correct"] += 1
                    flip["correct_to_correct_changed_answer"] += int(item["flip_I"])
                elif item["C_B"] and not item["C_I"]:
                    flip["correct_to_wrong"] += 1
                elif (not item["C_B"]) and item["C_I"]:
                    flip["wrong_to_correct"] += 1
                else:
                    flip["wrong_to_wrong"] += 1
                    n_wrong_wrong += 1
                    n_wrong_wrong_changed += int(item["flip_I"])
                flip["n_flip_I"] += item["flip_I"]
                flip["n_flip_R"] += item["flip_R"]
            n = rec["n_triplets"]
            for state in STATES:
                state_rows.append(
                    {
                        "model_id": model_id,
                        "display": DISPLAY[model_id],
                        "factor": factor,
                        "state": state,
                        "C_B": int(state[0]),
                        "C_R": int(state[1]),
                        "C_I": int(state[2]),
                        "n": counts[state],
                        "pi": counts[state] / n if n else None,
                    }
                )
            sum_1ri = sum(counts[s] for s in STATES if s.startswith("1")) / n if n else None
            flip_rows.append(
                {
                    "model_id": model_id,
                    "display": DISPLAY[model_id],
                    "factor": factor,
                    "n": n,
                    "F_I": flip["n_flip_I"] / n if n else None,
                    "F_R": flip["n_flip_R"] / n if n else None,
                    "gold_I_equals_gold_B_rate": n_gold_i_eq / n if n else None,
                    "gold_R_differs_from_gold_B_rate": n_gold_r_ne / n if n else None,
                    "correct_to_correct": flip["correct_to_correct"] / n if n else None,
                    "correct_to_correct_changed_answer": flip["correct_to_correct_changed_answer"] / n if n else None,
                    "correct_to_wrong": flip["correct_to_wrong"] / n if n else None,
                    "wrong_to_correct": flip["wrong_to_correct"] / n if n else None,
                    "wrong_to_wrong": flip["wrong_to_wrong"] / n if n else None,
                    "wrong_to_wrong_changed_answer": n_wrong_wrong_changed / n if n else None,
                    "binary_choice_note": "Irrelevant gold usually equals base gold, so a binary A/B judge has only one wrong answer; wrong→wrong almost never changes the selected letter.",
                    "sum_pi_1ri": sum_1ri,
                    "sum_pi_1ri_equals_A_B": abs((sum_1ri or 0) - (rec["A_B"] or 0)) < 1e-12,
                }
            )

    write_csv(os.path.join(OUT, "metric_reconstruction.csv"), [{k: v for k, v in r.items() if k != "status_counts"} for r in recon_rows])
    write_csv(os.path.join(OUT, "eight_state_distribution.csv"), state_rows)
    write_csv(os.path.join(OUT, "prediction_flip.csv"), flip_rows)

    # Compact eight-state by model (pooled over factors, still audit population)
    pooled = defaultdict(lambda: Counter())
    n_model = Counter()
    for row in state_rows:
        pooled[row["model_id"]][row["state"]] += row["n"]
        n_model[row["model_id"]] += row["n"]
    pooled_rows = []
    for model_id in MODELS:
        n = n_model[model_id]
        rec = {"model_id": model_id, "display": DISPLAY[model_id], "n": n}
        for state in STATES:
            rec["pi_%s" % state] = pooled[model_id][state] / n if n else None
            rec["n_%s" % state] = pooled[model_id][state]
        rec["A_B"] = (pooled[model_id]["100"] + pooled[model_id]["101"] + pooled[model_id]["110"] + pooled[model_id]["111"]) / n if n else None
        pooled_rows.append(rec)
    write_csv(os.path.join(OUT, "eight_state_pooled_by_model.csv"), pooled_rows)

    semantics["n_factor_rows"] = len(recon_rows)
    semantics["n_A_S_neq_A_B"] = sum(1 for r in recon_rows if r["A_S"] is not None and abs(r["A_S"] - r["A_B"]) > 1e-9)
    semantics["n_PFC_identity_holds"] = sum(1 for r in recon_rows if r["PFC_equals_AB_RA"])
    semantics["n_PSC_identity_holds"] = sum(1 for r in recon_rows if r["PSC_equals_AB_II"])
    semantics["paper_RA_match"] = sum(1 for r in recon_rows if r["match_paper_RA"])
    semantics["paper_A_audit_match"] = sum(1 for r in recon_rows if r["match_paper_A_audit"])
    semantics["headline"] = {
        "A_S_is_not_A_B": True,
        "measurement_objects": {
            "static_benchmark": "A^S(J) independent static pairwise accuracy",
            "audit_base": "A^B(J) = P(C_B=1) on audit triplets",
            "intervention_profile": "D(J)=(RA(J), II(J))",
        },
        "empirical_main_claim_should_use": "A^S(J) does not empirically determine D(J)",
        "do_not_assume": "A^S = A^B",
    }
    write_json(os.path.join(OUT, "metric_semantics.json"), semantics)
    write_json(os.path.join(OUT, "eight_state_distribution.json"), {"note": "Audit triplet joint behavior distribution π_bri = P(C_B=b, C_R=r, C_I=i). Sum_ri π_1ri = A^B, not A^S.", "by_model_factor": state_rows, "pooled_by_model": pooled_rows})
    write_json(os.path.join(OUT, "prediction_flip.json"), {"note": "F_I = P(Y_I != Y_B). correctness ≠ behavioral stability.", "rows": flip_rows})
    return {"recon": recon_rows, "states": state_rows, "flips": flip_rows, "semantics": semantics}


def p4_equivalence(recon_rows: list[dict]) -> dict:
    # Keep original matching on A^S. Post-hoc epsilon grid.
    by_factor = defaultdict(list)
    for row in recon_rows:
        by_factor[row["factor"]].append(row)
    curve = []
    pair_rows = []
    for eps in EPSILONS_PP:
        abs_ra = []
        abs_ii = []
        abs_pfc = []
        abs_psc = []
        n_pairs = 0
        for factor, items in by_factor.items():
            for i, a in enumerate(items):
                for b in items[i + 1 :]:
                    if a["A_S"] is None or b["A_S"] is None:
                        continue
                    delta_a_pp = abs(a["A_S"] - b["A_S"]) * 100.0
                    if delta_a_pp > eps + 1e-12:
                        continue
                    n_pairs += 1
                    d_ra = abs(a["RA"] - b["RA"])
                    d_ii = abs(a["II"] - b["II"])
                    d_pfc = abs(a["PFC"] - b["PFC"])
                    d_psc = abs(a["PSC"] - b["PSC"])
                    abs_ra.append(d_ra)
                    abs_ii.append(d_ii)
                    abs_pfc.append(d_pfc)
                    abs_psc.append(d_psc)
                    if abs(eps - 1.0) < 1e-12:
                        pair_rows.append(
                            {
                                "epsilon_pp": eps,
                                "factor": factor,
                                "model_a": a["display"],
                                "model_b": b["display"],
                                "A_S_a": a["A_S"],
                                "A_S_b": b["A_S"],
                                "delta_A_S_pp": delta_a_pp,
                                "delta_RA_pp": d_ra * 100,
                                "delta_II_pp": d_ii * 100,
                                "delta_PFC_pp": d_pfc * 100,
                                "delta_PSC_pp": d_psc * 100,
                                "predeclared_1pp": True,
                            }
                        )
        curve.append(
            {
                "epsilon_pp": eps,
                "role": "predeclared_primary" if abs(eps - 1.0) < 1e-12 else "post_hoc_sensitivity",
                "accuracy_used": "A_S independent static benchmark, never A_B",
                "n_pairs": n_pairs,
                "median_abs_delta_RA_pp": None if not abs_ra else median(abs_ra) * 100,
                "max_abs_delta_RA_pp": None if not abs_ra else max(abs_ra) * 100,
                "median_abs_delta_II_pp": None if not abs_ii else median(abs_ii) * 100,
                "max_abs_delta_II_pp": None if not abs_ii else max(abs_ii) * 100,
                "median_abs_delta_PFC_pp": None if not abs_pfc else median(abs_pfc) * 100,
                "max_abs_delta_PFC_pp": None if not abs_pfc else max(abs_pfc) * 100,
            }
        )
    write_csv(os.path.join(OUT, "accuracy_equivalence_curve.csv"), curve)
    write_csv(os.path.join(OUT, "accuracy_matched_1pp_pairs.csv"), pair_rows)
    payload = {
        "label": "post-hoc sensitivity analysis",
        "primary_predeclared": "1pp matching on A^S remains the main result",
        "curve": curve,
        "n_1pp_pairs_recomputed": len(pair_rows),
    }
    write_json(os.path.join(OUT, "accuracy_equivalence_curve.json"), payload)
    return payload


def tournament_stats(edges: list[tuple[str, str]], abstained: int, n_pairs: int) -> dict:
    nodes = sorted({u for e in edges for u in e})
    wins = defaultdict(int)
    beat = defaultdict(set)
    for winner, loser in edges:
        wins[winner] += 1
        beat[winner].add(loser)
        nodes = list({*nodes, winner, loser})
    nodes = sorted(set(nodes))
    n_cycle_triples = 0
    n_triples = 0
    n_trans_viol = 0
    for a, b, c in combinations(nodes, 3):
        n_triples += 1
        ab = b in beat[a]
        ba = a in beat[b]
        bc = c in beat[b]
        cb = b in beat[c]
        ac = c in beat[a]
        ca = a in beat[c]
        directed = [(ab and not ba), (bc and not cb), (ca and not ac)]
        directed2 = [(ba and not ab), (cb and not bc), (ac and not ca)]
        if all(directed) or all(directed2):
            n_cycle_triples += 1
        if ab and bc and not ac:
            n_trans_viol += 1
        if ba and cb and not ca:
            n_trans_viol += 1
    condorcet = []
    for node in nodes:
        others = [other for other in nodes if other != node]
        if others and all(other in beat[node] for other in others):
            condorcet.append(node)
    copeland = {n: len(beat[n]) for n in nodes}
    ordered = sorted(copeland.values(), reverse=True)
    margin = (ordered[0] - ordered[1]) if len(ordered) >= 2 else None
    return {
        "n_nodes": len(nodes),
        "n_decided_edges": len(edges),
        "n_pairs": n_pairs,
        "n_abstained_edges": abstained,
        "has_cycle_triple": n_cycle_triples > 0,
        "n_cycle_triples": n_cycle_triples,
        "n_triples": n_triples,
        "n_transitivity_violations": n_trans_viol,
        "has_condorcet": len(condorcet) == 1,
        "n_condorcet": len(condorcet),
        "copeland_margin": margin,
    }


def p5_pair_graph() -> dict:
    rows = []
    for model_id in MODELS:
        pairs = read_jsonl(pairs_path(model_id))
        selections = read_jsonl(selections_path(model_id))
        by_pool = defaultdict(list)
        abstain = 0
        ok_pairs = 0
        for row in pairs:
            pool = row.get("pool_id") or row.get("item_id")
            ok_pairs += 1
            status = row.get("status")
            left = row.get("left_uid") or row.get("candidate_a_uid")
            right = row.get("right_uid") or row.get("candidate_b_uid")
            outcome = row.get("outcome")
            parsed = pref(row)
            winner_loser = None
            if status == "ok" and outcome in {"left", "right"} and left and right:
                winner_loser = (left, right) if outcome == "left" else (right, left)
            elif status == "ok" and parsed in {"A", "B"} and left and right:
                winner_loser = (left, right) if parsed == "A" else (right, left)
            if winner_loser is None:
                abstain += 1
                continue
            by_pool[pool].append(winner_loser)
        pool_stats = [tournament_stats(edges, 0, len(edges)) for edges in by_pool.values()]
        n_pools = len(pool_stats)
        # selection stability
        sel_by_pool = defaultdict(dict)
        semantic_abs = 0
        n_sel = 0
        for row in selections:
            n_sel += 1
            semantic_abs += int(row.get("semantic_abstentions") or 0)
            sel_by_pool[row.get("pool_id") or row.get("item_id")][int(row.get("n"))] = row.get("selected_uid")
        n2_eq_n8 = []
        n4_eq_n8 = []
        n2_eq_n4 = []
        for pool, mp in sel_by_pool.items():
            if 2 in mp and 8 in mp:
                n2_eq_n8.append(int(mp[2] == mp[8]))
            if 4 in mp and 8 in mp:
                n4_eq_n8.append(int(mp[4] == mp[8]))
            if 2 in mp and 4 in mp:
                n2_eq_n4.append(int(mp[2] == mp[4]))
        rec = {
            "model_id": model_id,
            "display": DISPLAY[model_id],
            "n_pair_rows": len(pairs),
            "n_pools": n_pools,
            "pair_abstention_rate": abstain / len(pairs) if pairs else None,
            "cycle_rate": mean([float(s["has_cycle_triple"]) for s in pool_stats]),
            "mean_cycle_triples": mean([s["n_cycle_triples"] for s in pool_stats]),
            "mean_transitivity_violations": mean([s["n_transitivity_violations"] for s in pool_stats]),
            "condorcet_existence_rate": mean([float(s["has_condorcet"]) for s in pool_stats]),
            "mean_copeland_margin": mean([s["copeland_margin"] for s in pool_stats if s["copeland_margin"] is not None]),
            "selection_stability_N2_eq_N8": mean(n2_eq_n8),
            "selection_stability_N4_eq_N8": mean(n4_eq_n8),
            "selection_stability_N2_eq_N4": mean(n2_eq_n4),
            "semantic_abstention_events": semantic_abs,
            "n_selection_rows": n_sel,
            "role": "secondary_exploratory",
        }
        rows.append(rec)
    write_csv(os.path.join(OUT, "pair_graph_summary.csv"), rows)
    payload = {
        "role": "secondary exploratory analysis; do not retarget the main paper into a preference-consistency paper",
        "n_edges_per_model_expected": 22400,
        "rows": rows,
    }
    write_json(os.path.join(OUT, "pair_graph_summary.json"), payload)
    return payload


def write_protocol(verification: dict, semantics: dict, curve: dict) -> None:
    path = os.path.join(OUT, "DATA_FORENSICS_PROTOCOL.md")
    a_s_neq = semantics.get("n_A_S_neq_A_B")
    body = f"""# RewardLens 截稿前数据审计协议

Frozen: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
Status: CPU forensics only. No GPU inference. No model rerun.

This file freezes the identity gate and metric objects for the ICLR revision.
New analyses may be added only after P0/P1 pass.

## Hard constraints

1. Physical identity is `SHA256(raw image bytes)` (`physical_image_id`).
2. `same numeric example_id` does **not** imply the same physical example.
3. `A^S ≠ A^B`. Never substitute independent static accuracy for audit-base accuracy.
4. If a proposed item-level Audit↔BoN join is possible on physical identity, stop and treat it as an integrity issue.
5. If it is impossible, that is expected under the frozen physical-disjoint design. Do not force the join.

## Identity objects

Every Static / Audit / Downstream row must be traceable to:

- dataset / carrier
- split
- source_example_id (`item_id`)
- source_image_id
- physical_image_path
- image hash (`physical_image_id`)
- manifest row id
- factor
- variant
- pool_id (downstream only)

The disjointness statement is:

`I_audit ∩ I_downstream = ∅`

where `I` is the set of **physical image hashes** (or a verified source-image identifier that has been shown to injectively track those hashes). Local autoincrement `example_id` is not an identity.

## Frozen manifests

| split | sha256 |
|---|---|
| static | `6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3` |
| audit | `880a3769df10e7e4dff5939ba03bbff7347cc62e56b11f79e10f5a1b61d8a018` |
| downstream v2 | `0afb6dfefd7a47e3dc47fd05127e82d5fd260943d04e5c5cc3117ae11055133c` |

Downstream v1 was **not** physically disjoint from static (196 shared image hashes; 197 rows later replaced). Downstream v2 is the frozen GPU set.

## Measurement objects

Do not use a single symbol `A`.

- `A^S(J)` = independent static benchmark accuracy (TallyQA Count; GQA otherwise)
- `A^B(J)` = `P(C_B=1)` on complete audit triplets
- `RA(J) = P(C_R=1 | C_B=1)`  (= frozen `PFC_cond`)
- `II(J) = P(C_I=1 | C_B=1)`  (= frozen `PSC_cond`)
- `PFC = P(C_B=1, C_R=1)`
- `PSC = P(C_B=1, C_I=1)`
- `D(J) = (RA(J), II(J))`

On the **same audit population** and the same abstention convention:

`PFC = A^B * RA`, `PSC = A^B * II`

These identities do **not** use `A^S`.

Empirical main proposition:

> `A^S(J)` does not empirically determine `D(J)`.

Theory/non-identification should be stated for an observational/static score versus an intervention distribution. Do not silently assume `A^S = A^B`.

## Denominators

- Audit: complete triplets only (`base`, `relevant`, `irrelevant` all `status==ok` and parsed `A|B`). Incomplete or unparsed triplets are dropped, not imputed.
- Static `A^S`: `status==ok` and parsed `A|B`. Parse failures are excluded from the denominator.
- Pair-graph abstention: `parsed_preference ∉ {{A,B}}` or `status != ok`.

## Allowed analyses after P0 pass

| ID | Analysis | Paper role |
|---|---|---|
| P2 | Eight-state `π_bri` on audit triplets | Useful; proves RA/II are projections of joint intervention behavior |
| P3 | Prediction flip `F_I = P(Y_I ≠ Y_B)` | Useful; correctness ≠ behavioral stability |
| P4 | Accuracy-equivalence curve on **`A^S`**, `ε ∈ {{0.5,1,2,3,5}}` pp | 1pp remains predeclared main result; others are post-hoc sensitivity |
| P5 | Pair graph (cycle, transitivity, Condorcet, Copeland, N=2/4/8 stability) | Secondary exploratory; appendix/discussion only |
| — | Audit↔BoN item-level join | **Cancelled** unless P0 finds unexpected physical overlap |

RQ2 remains model-level / factor-wise secondary diagnostic. It does not become an item-level causal analysis.

## P0 result (this freeze)

Physical disjointness independently recomputed from `phase2_v2_physical_sha_manifests.json`:

- audit ∩ static physical = {verification["intersections_independent_recompute"]["audit__static"]["physical_image_id"]}
- audit ∩ downstream_v2 physical = {verification["intersections_independent_recompute"]["audit__downstream_v2"]["physical_image_id"]}
- static ∩ downstream_v2 physical = {verification["intersections_independent_recompute"]["static__downstream_v2"]["physical_image_id"]}
- pass = {verification["physical_disjoint_pass"]}

Within-split TallyQA/GQA byte sharing remains and is a source-confound caveat, not a cross-split leak.

## Machine policy

- 017 GPU: OFF unless a unique local-disk file is the only copy of an evidence object.
- 011 no-GPU: allowed for missing shared-fs files.
- First-pass evidence: local HF archive + `autodl-fs` CPU reads.
"""
    # The f-string above accidentally left braces from the template. Rewrite cleanly below.
    del body
    lines = []
    lines.append("# RewardLens Pre-Deadline Data Forensics Protocol")
    lines.append("")
    lines.append("Frozen: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    lines.append("Status: CPU forensics only. No GPU inference. No model rerun.")
    lines.append("")
    lines.append("This freeze separates **data identity**, **metric objects**, and **optional new analyses** for the ICLR revision.")
    lines.append("")
    lines.append("## Hard constraints")
    lines.append("")
    lines.append("1. Physical identity is SHA256 of raw image bytes (`physical_image_id`).")
    lines.append("2. The same numeric `example_id` does not imply the same physical example.")
    lines.append("3. `A^S ≠ A^B`. Never substitute independent static accuracy for audit-base accuracy.")
    lines.append("4. If an item-level Audit↔BoN join is possible on physical identity, stop; that is an integrity issue.")
    lines.append("5. If it is impossible, that is required by the frozen physical-disjoint design. Do not force the join.")
    lines.append("")
    lines.append("## Identity objects")
    lines.append("")
    lines.append("Every Static / Audit / Downstream row must trace to: dataset, split, source_example_id, source_image_id, physical_image_path, image hash, manifest row id, factor, variant, pool_id.")
    lines.append("")
    lines.append("`I_audit ∩ I_downstream = ∅` is a statement about **physical image hashes**, not local autoincrement IDs.")
    lines.append("")
    lines.append("## Frozen manifests")
    lines.append("")
    lines.append("| split | sha256 |")
    lines.append("|---|---|")
    lines.append("| static | `6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3` |")
    lines.append("| audit | `880a3769df10e7e4dff5939ba03bbff7347cc62e56b11f79e10f5a1b61d8a018` |")
    lines.append("| downstream v2 | `0afb6dfefd7a47e3dc47fd05127e82d5fd260943d04e5c5cc3117ae11055133c` |")
    lines.append("")
    lines.append("Downstream v1 was not physically disjoint from static (196 shared hashes; 197 rows replaced). Downstream v2 is the frozen GPU set.")
    lines.append("")
    lines.append("## Measurement objects")
    lines.append("")
    lines.append("Do not use a single symbol A.")
    lines.append("")
    lines.append("- `A^S(J)` = independent static benchmark accuracy (TallyQA Count; GQA otherwise)")
    lines.append("- `A^B(J)` = P(C_B=1) on complete audit triplets")
    lines.append("- `RA(J) = P(C_R=1 | C_B=1)` (frozen `PFC_cond`)")
    lines.append("- `II(J) = P(C_I=1 | C_B=1)` (frozen `PSC_cond`)")
    lines.append("- `PFC = P(C_B=1, C_R=1)`")
    lines.append("- `PSC = P(C_B=1, C_I=1)`")
    lines.append("- `D(J) = (RA(J), II(J))`")
    lines.append("")
    lines.append("On the same audit population and the same abstention convention: `PFC = A^B · RA` and `PSC = A^B · II`.")
    lines.append("These identities do not use `A^S`.")
    lines.append("")
    lines.append("Empirical main proposition: **`A^S(J)` does not empirically determine `D(J)`.**")
    lines.append("Theory should compare an observational/static score with an intervention distribution and must not assume `A^S = A^B`.")
    lines.append("")
    lines.append("## Denominators")
    lines.append("")
    lines.append("- Audit: complete triplets only. Incomplete or unparsed triplets are dropped.")
    lines.append("- Static `A^S`: status=ok and parsed A/B. Parse failures are excluded, not counted wrong.")
    lines.append("- Pair-graph abstention: parsed preference not in {A,B} or status != ok.")
    lines.append("")
    lines.append("## Analyses after P0")
    lines.append("")
    lines.append("| ID | Analysis | Paper role |")
    lines.append("|---|---|---|")
    lines.append("| P2 | Eight-state π_bri on audit triplets | Allowed; RA/II are projections of joint intervention behavior |")
    lines.append("| P3 | Prediction flip F_I = P(Y_I ≠ Y_B) | Allowed; correctness ≠ behavioral stability |")
    lines.append("| P4 | Equivalence curve on A^S, ε in {0.5,1,2,3,5} pp | 1pp stays predeclared; others are post-hoc sensitivity |")
    lines.append("| P5 | Pair graph | Secondary exploratory only |")
    lines.append("| — | Audit↔BoN item-level join | Cancelled unless P0 finds unexpected physical overlap |")
    lines.append("")
    lines.append("RQ2 stays a model-level secondary diagnostic.")
    lines.append("")
    lines.append("## P0 result in this freeze")
    lines.append("")
    inter = verification["intersections_independent_recompute"]
    lines.append("- audit ∩ static physical = %s" % inter["audit__static"]["physical_image_id"])
    lines.append("- audit ∩ downstream_v2 physical = %s" % inter["audit__downstream_v2"]["physical_image_id"])
    lines.append("- static ∩ downstream_v2 physical = %s" % inter["static__downstream_v2"]["physical_image_id"])
    lines.append("- pass = %s" % verification["physical_disjoint_pass"])
    lines.append("")
    lines.append("P1 reconstruction: %s factor-rows have A^S ≠ A^B; PFC=A^B·RA holds on %s/%s rows." % (
        semantics.get("n_A_S_neq_A_B"),
        semantics.get("n_PFC_identity_holds"),
        semantics.get("n_factor_rows"),
    ))
    lines.append("")
    lines.append("P4 1pp pairs recomputed on A^S: %s. This remains the predeclared headline matching analysis." % curve.get("n_1pp_pairs_recomputed"))
    lines.append("")
    lines.append("## Machine policy")
    lines.append("")
    lines.append("- 017 GPU stays off unless a unique local-disk file is the only evidence copy.")
    lines.append("- 011 no-GPU is allowed for missing shared-fs files.")
    lines.append("- First pass: local HF archive + autodl-fs CPU reads.")
    lines.append("")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main() -> int:
    verification = p0_identity()
    if not verification["physical_disjoint_pass"]:
        write_json(os.path.join(OUT, "STOP_INTEGRITY_ISSUE.json"), verification)
        raise SystemExit("P0 failed: physical overlap detected. Downstream item-level analysis is blocked.")
    packed = p1_and_p2_p3(verification)
    curve = p4_equivalence(packed["recon"])
    pair_graph = p5_pair_graph()
    write_protocol(verification, packed["semantics"], curve)
    summary = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "p0_pass": verification["physical_disjoint_pass"],
        "audit_downstream_join_allowed": False,
        "n_A_S_neq_A_B": packed["semantics"]["n_A_S_neq_A_B"],
        "n_PFC_identity_holds": packed["semantics"]["n_PFC_identity_holds"],
        "n_factor_rows": packed["semantics"]["n_factor_rows"],
        "n_1pp_pairs": curve["n_1pp_pairs_recomputed"],
        "pair_graph_models": len(pair_graph["rows"]),
        "outputs": sorted(name for name in os.listdir(OUT) if not name.startswith("_")),
    }
    write_json(os.path.join(OUT, "FORENSICS_SUMMARY.json"), summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
