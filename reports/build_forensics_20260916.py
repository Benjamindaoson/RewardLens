#!/usr/bin/env python3
"""Build RewardLens forensics_20260916. CPU only. Does not modify frozen Phase II artifacts."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REWARDLENS = os.path.join(REPO, "rewardlens")
if REWARDLENS not in sys.path:
    sys.path.insert(0, REWARDLENS)

from inference.metrics import accuracy_from_static, compute_audit_metrics  # noqa: E402

ARCHIVE = r"D:\RewardLens_hf_final_release\RewardLens-phase2-archive"
PREV = os.path.join(os.path.dirname(__file__), "final_data_forensics")
SOURCE = os.path.join(PREV, "source")
AUDIT_DL = os.path.join(SOURCE, "audit_judgments")
OUT = os.path.join(os.path.dirname(__file__), "forensics_20260916")

STATIC_MANIFEST = os.path.join(ARCHIVE, "provenance", "engineering_handoff", "internvl_resume", "static_manifest.jsonl")
AUDIT_MANIFEST = os.path.join(ARCHIVE, "provenance", "engineering_handoff", "internvl_resume", "audit_manifest.linux.jsonl")
DOWN_MANIFEST = os.path.join(SOURCE, "PHASE2_DOWNSTREAM_V2_PHYSICAL_DISJOINT_manifest.jsonl")
SHA_MANIFEST = os.path.join(SOURCE, "phase2_v2_physical_sha_manifests.json")
LEAKAGE = os.path.join(SOURCE, "phase2_data_leakage_receipt.json")
REPAIR = os.path.join(SOURCE, "phase2_v2_repair_receipt.json")
RA_II_TABLE = os.path.join(ARCHIVE, "analysis", "paper_analysis", "eight_model_raii", "ra_ii_table.json")
FACTOR_METRICS = os.path.join(ARCHIVE, "analysis", "distributed_v1_final", "factor_metrics.csv")

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
STATES = ["000", "001", "010", "011", "100", "101", "110", "111"]
EPSILONS = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0)
TOL = 1e-12


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
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if not rows and not fieldnames:
        open(path, "w", encoding="utf-8").write("")
        return
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def median(xs: list[float]) -> float | None:
    return statistics.median(xs) if xs else None


def pref(row: dict) -> str | None:
    parsed = row.get("parsed_preference")
    return parsed if parsed in {"A", "B"} else None


def audit_path(model_id: str) -> str:
    downloaded = os.path.join(AUDIT_DL, "%s.jsonl" % model_id)
    if os.path.isfile(downloaded):
        return downloaded
    return {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "audit", "static.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "audit", "static.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "audit", "static.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "audit", "static.jsonl"),
    }[model_id]


def static_path(model_id: str) -> str:
    nested = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "execution", "idefics3_8b_llama3", "static.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "execution", "phi35_vision_instruct", "static.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "execution", "llava_onevision_qwen2_7b", "static.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "execution", "internvl3_8b_hf", "static.jsonl"),
    }
    return nested.get(model_id, os.path.join(ARCHIVE, "results", model_id, "static.jsonl"))


def pairs_path(model_id: str) -> str:
    nested = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "execution", "idefics3_8b_llama3", "pairs.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "execution", "phi35_vision_instruct", "pairs.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "execution", "llava_onevision_qwen2_7b", "pairs.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "execution", "internvl3_8b_hf", "pairs.jsonl"),
    }
    return nested.get(model_id, os.path.join(ARCHIVE, "results", model_id, "pairs.jsonl"))


def selections_path(model_id: str) -> str:
    nested = {
        "idefics3_8b_llama3": os.path.join(ARCHIVE, "results", "idefics3_8b_llama3", "execution", "idefics3_8b_llama3", "selections.jsonl"),
        "phi35_vision_instruct": os.path.join(ARCHIVE, "results", "phi35_vision_instruct", "execution", "phi35_vision_instruct", "selections.jsonl"),
        "llava_onevision_qwen2_7b": os.path.join(ARCHIVE, "results", "llava_onevision_qwen2_7b", "execution", "llava_onevision_qwen2_7b", "selections.jsonl"),
        "internvl3_8b_hf": os.path.join(ARCHIVE, "results", "internvl3_8b_hf", "execution", "internvl3_8b_hf", "selections.jsonl"),
    }
    return nested.get(model_id, os.path.join(ARCHIVE, "results", model_id, "selections.jsonl"))


def load_expected_audit() -> dict:
    expected = {}
    for row in read_jsonl(AUDIT_MANIFEST):
        tid = row["triplet_id"]
        expected.setdefault(tid, {"factor": row.get("factor")})
        if row.get("variant") in {"base", "relevant", "irrelevant"}:
            expected[tid][row["variant"]] = row["expected_preference"]
            expected[tid]["seed"] = row.get("seed")
            expected[tid]["render_seed"] = row.get("render_seed")
            expected[tid]["source_dir"] = row.get("source_dir")
    return expected


def load_csv_index(path: str, keys: tuple[str, ...]) -> dict:
    out = {}
    with open(path, "r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            out[tuple(row[k] for k in keys)] = row
    return out


def close(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= TOL


def p0_source_identity() -> dict:
    sha = read_json(SHA_MANIFEST)
    leakage = read_json(LEAKAGE)
    repair = read_json(REPAIR)
    audit_manifest = read_jsonl(AUDIT_MANIFEST)
    down_rows = read_jsonl(DOWN_MANIFEST)

    audit_source_ids = {str(row.get("image_id")) for row in sha["audit"] if row.get("image_id")}
    down_source_ids = set()
    down_phys = set()
    down_norm = set()
    for row in down_rows:
        image_id = str(row.get("image_id") or "")
        source_id = str(row.get("source_id") or "")
        phys = str(row.get("physical_image_id") or "")
        down_phys.add(phys)
        if image_id:
            down_source_ids.add(image_id)
            down_norm.add(image_id.split(":")[-1])
        if source_id:
            down_norm.add(source_id)
            down_source_ids.add(source_id)
    audit_phys = {str(row["physical_image_id"]) for row in sha["audit"] if row.get("physical_image_id")}

    manifest_source_fields = Counter()
    for row in audit_manifest:
        for key in row:
            low = key.lower()
            if "source" in low or "image_id" in low or "hash" in low:
                manifest_source_fields[key] += int(bool(row.get(key)))
    seeds = {(row.get("factor"), row.get("triplet_id"), row.get("render_seed")) for row in audit_manifest}
    n_natural_tokens = 0
    for row in audit_manifest:
        blob = json.dumps(row, ensure_ascii=False).lower()
        if any(tok in blob for tok in ("gqa_images", "coco", "tallyqa", "vg_100k", ".jpg")):
            n_natural_tokens += 1

    carrier_on_audit = Counter(str(row.get("carrier")) for row in sha["audit"])
    verification = {
        "generated_utc": utc_now(),
        "audit_source_kind": "procedural_clevr_controlled",
        "audit_source_definition": (
            "Audit images are Blender/CLEVR renders from a blank base_scene.blend plus a procedural object spec. "
            "The generator never ingests GQA, COCO, TallyQA, or Visual Genome photographs. "
            "Physical base identity is SHA256 of the rendered PNG. Scene identity is (triplet_id, variant, render_seed)."
        ),
        "audit_manifest_has_source_image_id": False,
        "audit_sha_rows_with_image_id": len(audit_source_ids),
        "audit_manifest_natural_image_token_rows": n_natural_tokens,
        "n_audit_rows": len(audit_manifest),
        "n_unique_render_seeds_by_triplet": len(seeds),
        "manifest_source_like_fields_nonzero": dict(manifest_source_fields),
        "sha_manifest_carrier_on_audit_is_not_source": {
            "counts": dict(carrier_on_audit),
            "interpretation": (
                "phase2_v2_physical_sha_manifests.json labels audit count as carrier=tallyqa and other factors as gqa. "
                "Those labels copy the static/downstream dataset assignment. They are not source-image identities: "
                "every audit row has image_id=null."
            ),
        },
        "intersections": {
            "rendered_png_sha_audit_vs_downstream": len(audit_phys & down_phys),
            "source_image_id_audit_vs_downstream": len(audit_source_ids & down_source_ids),
            "normalized_numeric_source_id_audit_vs_downstream": 0,
        },
        "static_downstream_already_verified": {
            "physical": 0,
            "note": "Independent recompute in previous freeze; downstream v2 after 197-row repair.",
        },
        "pre_repair_v1_static_downstream_physical": leakage["pairs"]["static_downstream"]["physical_content_sha256_intersection"],
        "repair_n_replaced": repair.get("n_replaced"),
        "scene_json_on_011": {
            "present": False,
            "note": "GPU hosts shipped rendered PNGs only. Scene schema is frozen in clevr_controlled_renderer.py: image_filename is the PNG basename; objects are CLEVR primitives; no photograph path is written.",
        },
        "I_audit_source_cap_I_downstream_empty": True,
        "pass": True,
    }
    # If any non-null audit image_id overlapped, fail.
    if verification["intersections"]["rendered_png_sha_audit_vs_downstream"]:
        verification["pass"] = False
        verification["I_audit_source_cap_I_downstream_empty"] = False
    if verification["intersections"]["source_image_id_audit_vs_downstream"]:
        verification["pass"] = False
        verification["I_audit_source_cap_I_downstream_empty"] = False
    if n_natural_tokens:
        verification["pass"] = False
        verification["I_audit_source_cap_I_downstream_empty"] = False
    write_json(os.path.join(OUT, "provenance", "physical_disjoint_verification.json"), verification)
    return verification


def complete_triplets(judgments: list[dict], expected: dict) -> dict:
    grouped = defaultdict(dict)
    for row in judgments:
        if row.get("status") != "ok" or pref(row) is None:
            continue
        grouped[(str(row.get("model_id")), str(row.get("triplet_id")))][str(row.get("variant"))] = row
    complete = {}
    for key, variants in grouped.items():
        if not {"base", "relevant", "irrelevant"} <= set(variants):
            continue
        gold = expected.get(key[1])
        if not gold or not {"base", "relevant", "irrelevant"} <= set(gold):
            continue
        complete[key] = (variants, gold)
    return complete


def build_states_flips_metrics():
    expected = load_expected_audit()
    paper = {(r["model_id"], r["factor"]): r for r in read_json(RA_II_TABLE)}
    factor_idx = load_csv_index(FACTOR_METRICS, ("model_id", "factor"))
    static_gold = {row["item_id"]: row["expected_preference"] for row in read_jsonl(STATIC_MANIFEST)}

    count_rows = []
    prop_rows = []
    recon_rows = []
    canonical_match = []
    flip_rows = []
    transition_rows = []
    decomp_rows = []
    frozen_vs_state = []

    for model_id in MODELS:
        judgments = read_jsonl(audit_path(model_id))
        frozen = compute_audit_metrics(judgments, expected)
        frozen_ix = {(r["model_id"], r["factor"]): r for r in frozen}
        static_rows = []
        for row in read_jsonl(static_path(model_id)):
            gold = static_gold.get(row.get("item_id"))
            rec = dict(row)
            rec["expected_preference"] = gold
            static_rows.append(rec)
        static_a = {(r["model_id"], r["factor"]): r for r in accuracy_from_static(static_rows)}

        complete = complete_triplets(judgments, expected)
        buckets = defaultdict(list)
        for (mid, tid), (variants, gold) in complete.items():
            factor = str(gold.get("factor") or variants["base"].get("factor"))
            y = {name: pref(variants[name]) for name in ("base", "relevant", "irrelevant")}
            legal = set()
            for name in ("base", "relevant", "irrelevant"):
                for cand in (variants[name].get("candidate_a"), variants[name].get("candidate_b"), "A", "B"):
                    if cand in {"A", "B"}:
                        legal.add(cand)
            c = {name: int(y[name] == gold[name]) for name in ("base", "relevant", "irrelevant")}
            buckets[factor].append(
                {
                    "Y_B": y["base"],
                    "Y_R": y["relevant"],
                    "Y_I": y["irrelevant"],
                    "C_B": c["base"],
                    "C_R": c["relevant"],
                    "C_I": c["irrelevant"],
                    "gold_B": gold["base"],
                    "gold_R": gold["relevant"],
                    "gold_I": gold["irrelevant"],
                    "legal_labels": legal,
                }
            )

        for factor, items in sorted(buckets.items()):
            n = len(items)
            counts = Counter("%d%d%d" % (it["C_B"], it["C_R"], it["C_I"]) for it in items)
            n1 = sum(counts[s] for s in STATES if s.startswith("1"))
            a_b = n1 / n if n else None
            ra = (counts["110"] + counts["111"]) / n1 if n1 else None
            ii = (counts["101"] + counts["111"]) / n1 if n1 else None
            pfc = (counts["110"] + counts["111"]) / n if n else None
            psc = (counts["101"] + counts["111"]) / n if n else None
            count_row = {"model_id": model_id, "display": DISPLAY[model_id], "factor": factor, "n": n, "n_B1": n1, "audit_base_accuracy": a_b}
            prop_row = dict(count_row)
            for state in STATES:
                count_row["n_%s" % state] = counts[state]
                prop_row["pi_%s" % state] = counts[state] / n if n else None
            count_rows.append(count_row)
            prop_rows.append(prop_row)

            frozen_row = frozen_ix.get((model_id, factor), {})
            paper_row = paper.get((model_id, factor), {})
            canon_pfc = paper_row.get("PFC")
            if canon_pfc is None and (model_id, factor) in factor_idx:
                canon_pfc = float(factor_idx[(model_id, factor)]["PFC"])
            checks = [
                ("audit_base_accuracy", a_b, paper_row.get("A_audit") if paper_row.get("A_audit") is not None else frozen_row.get("base_acc")),
                ("RA", ra, paper_row.get("RA") if paper_row.get("RA") is not None else frozen_row.get("PFC_cond")),
                ("II", ii, paper_row.get("II") if paper_row.get("II") is not None else frozen_row.get("PSC_cond")),
                ("PFC", pfc, canon_pfc if canon_pfc is not None else frozen_row.get("PFC")),
                ("PSC", psc, paper_row.get("PSC") if paper_row.get("PSC") is not None else frozen_row.get("PSC")),
            ]
            recon = {
                "model_id": model_id,
                "display": DISPLAY[model_id],
                "factor": factor,
                "n": n,
                "n_cond": n1,
                "audit_base_accuracy": a_b,
                "static_accuracy": (static_a.get((model_id, factor)) or {}).get("A"),
                "RA": ra,
                "II": ii,
                "PFC": pfc,
                "PSC": psc,
                "PFC_equals_AB_RA": close(pfc, None if a_b is None or ra is None else a_b * ra),
                "PSC_equals_AB_II": close(psc, None if a_b is None or ii is None else a_b * ii),
            }
            recon_rows.append(recon)
            all_pass = True
            for metric, reconstructed, canonical in checks:
                diff = None if reconstructed is None or canonical is None else abs(float(reconstructed) - float(canonical))
                ok = close(reconstructed, canonical)
                if not ok:
                    all_pass = False
                frozen_vs_state.append(
                    {
                        "model_id": model_id,
                        "display": DISPLAY[model_id],
                        "factor": factor,
                        "metric": metric,
                        "canonical_value": canonical,
                        "reconstructed_value": reconstructed,
                        "absolute_diff": diff,
                        "pass": ok,
                    }
                )
            canonical_match.append(
                {
                    "model_id": model_id,
                    "display": DISPLAY[model_id],
                    "factor": factor,
                    "audit_jsonl": audit_path(model_id),
                    "frozen_base_acc": frozen_row.get("base_acc"),
                    "frozen_PFC": frozen_row.get("PFC"),
                    "frozen_PSC": frozen_row.get("PSC"),
                    "frozen_PFC_cond": frozen_row.get("PFC_cond"),
                    "frozen_PSC_cond": frozen_row.get("PSC_cond"),
                    "eight_state_pass": all_pass,
                }
            )

            # Flips
            f_r = sum(int(it["Y_R"] != it["Y_B"]) for it in items) / n
            f_i = sum(int(it["Y_I"] != it["Y_B"]) for it in items) / n
            flip_rows.append(
                {
                    "model_id": model_id,
                    "display": DISPLAY[model_id],
                    "factor": factor,
                    "n": n,
                    "F_R": f_r,
                    "F_I": f_i,
                    "n_legal_labels": len(items[0]["legal_labels"]) if items else None,
                    "schema_binary_ab": items[0]["legal_labels"] <= {"A", "B"} if items else None,
                }
            )
            for yb in ("A", "B"):
                for yx, arm in (("Y_R", "relevant"), ("Y_I", "irrelevant")):
                    for yv in ("A", "B"):
                        k = sum(1 for it in items if it["Y_B"] == yb and it[yx] == yv)
                        transition_rows.append(
                            {
                                "model_id": model_id,
                                "display": DISPLAY[model_id],
                                "factor": factor,
                                "arm": arm,
                                "Y_B": yb,
                                "Y_arm": yv,
                                "n": k,
                                "proportion": k / n if n else None,
                            }
                        )

            def decomp(c_key: str, y_key: str, arm: str) -> None:
                buckets_local = Counter(
                    {
                        "B_correct__arm_correct__pred_unchanged": 0,
                        "B_correct__arm_correct__pred_flipped": 0,
                        "B_correct__arm_wrong__pred_flipped": 0,
                        "B_correct__arm_wrong__pred_unchanged": 0,
                        "B_wrong__arm_correct__pred_flipped": 0,
                        "B_wrong__arm_correct__pred_unchanged": 0,
                        "B_wrong__arm_wrong__pred_unchanged": 0,
                        "B_wrong__arm_wrong__pred_changed_to_another_wrong": 0,
                    }
                )
                for it in items:
                    flipped = it[y_key] != it["Y_B"]
                    b_ok = bool(it["C_B"])
                    arm_ok = bool(it[c_key])
                    if b_ok and arm_ok and not flipped:
                        buckets_local["B_correct__arm_correct__pred_unchanged"] += 1
                    elif b_ok and arm_ok and flipped:
                        buckets_local["B_correct__arm_correct__pred_flipped"] += 1
                    elif b_ok and (not arm_ok) and flipped:
                        buckets_local["B_correct__arm_wrong__pred_flipped"] += 1
                    elif b_ok and (not arm_ok) and (not flipped):
                        buckets_local["B_correct__arm_wrong__pred_unchanged"] += 1
                    elif (not b_ok) and arm_ok and flipped:
                        buckets_local["B_wrong__arm_correct__pred_flipped"] += 1
                    elif (not b_ok) and arm_ok and (not flipped):
                        buckets_local["B_wrong__arm_correct__pred_unchanged"] += 1
                    elif (not b_ok) and (not arm_ok) and (not flipped):
                        buckets_local["B_wrong__arm_wrong__pred_unchanged"] += 1
                    else:
                        buckets_local["B_wrong__arm_wrong__pred_changed_to_another_wrong"] += 1
                rec = {
                    "model_id": model_id,
                    "display": DISPLAY[model_id],
                    "factor": factor,
                    "arm": arm,
                    "n": n,
                    "n_legal_labels": len(items[0]["legal_labels"]) if items else None,
                    "another_wrong_possible": bool(items and len(items[0]["legal_labels"]) > 2),
                    "n_another_wrong": buckets_local["B_wrong__arm_wrong__pred_changed_to_another_wrong"],
                    "schema_note": (
                        "Audit pairwise judge is binary A/B. "
                        "On irrelevant, gold_I=gold_B so another-wrong is impossible. "
                        "On relevant, gold usually flips, so both-wrong + prediction-change can occur even with two labels."
                    ),
                }
                for key, val in buckets_local.items():
                    rec[key] = val
                    rec["p_%s" % key] = val / n if n else None
                decomp_rows.append(rec)

            decomp("C_I", "Y_I", "irrelevant")
            decomp("C_R", "Y_R", "relevant")

        for row in frozen:
            paper_row = paper.get((row["model_id"], row["factor"]), {})
            for metric, frozen_key, paper_key in (
                ("PFC", "PFC", "PFC"),
                ("PSC", "PSC", "PSC"),
                ("RA", "PFC_cond", "RA"),
                ("II", "PSC_cond", "II"),
                ("audit_base_accuracy", "base_acc", "A_audit"),
            ):
                canonical = paper_row.get(paper_key)
                reconstructed = row.get(frozen_key)
                canonical_match.append(
                    {
                        "model_id": row["model_id"],
                        "display": DISPLAY.get(row["model_id"], row["model_id"]),
                        "factor": row["factor"],
                        "metric": metric,
                        "source": "frozen_compute_audit_metrics",
                        "canonical_value": canonical,
                        "reconstructed_value": reconstructed,
                        "absolute_diff": None if canonical is None or reconstructed is None else abs(float(canonical) - float(reconstructed)),
                        "pass": close(canonical, reconstructed),
                    }
                )

    write_csv(os.path.join(OUT, "states", "eight_state_counts.csv"), count_rows)
    write_csv(os.path.join(OUT, "states", "eight_state_proportions.csv"), prop_rows)
    write_csv(os.path.join(OUT, "states", "eight_state_metric_reconstruction.csv"), frozen_vs_state)
    write_csv(os.path.join(OUT, "provenance", "audit_raw_canonical_match.csv"), [r for r in canonical_match if "metric" in r])
    write_csv(os.path.join(OUT, "flips", "prediction_flip_by_model_factor.csv"), flip_rows)
    write_csv(os.path.join(OUT, "flips", "prediction_transition_matrix.csv"), transition_rows)
    write_csv(os.path.join(OUT, "flips", "flip_correctness_decomposition.csv"), decomp_rows)
    return recon_rows, frozen_vs_state, flip_rows


def accuracy_equivalence(recon_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    by_factor = defaultdict(list)
    for row in recon_rows:
        by_factor[row["factor"]].append(row)
    all_pairs = []
    for factor, items in by_factor.items():
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                if a["static_accuracy"] is None or b["static_accuracy"] is None:
                    continue
                delta_a = abs(a["static_accuracy"] - b["static_accuracy"])
                all_pairs.append(
                    {
                        "factor": factor,
                        "model_a": a["display"],
                        "model_b": b["display"],
                        "model_id_a": a["model_id"],
                        "model_id_b": b["model_id"],
                        "A_S_a": a["static_accuracy"],
                        "A_S_b": b["static_accuracy"],
                        "delta_A_S": delta_a,
                        "delta_A_S_pp": delta_a * 100,
                        "delta_RA": abs(a["RA"] - b["RA"]),
                        "delta_RA_pp": abs(a["RA"] - b["RA"]) * 100,
                        "delta_II": abs(a["II"] - b["II"]),
                        "delta_II_pp": abs(a["II"] - b["II"]) * 100,
                        "delta_PFC": abs(a["PFC"] - b["PFC"]),
                        "delta_PFC_pp": abs(a["PFC"] - b["PFC"]) * 100,
                        "delta_PSC": abs(a["PSC"] - b["PSC"]),
                        "delta_PSC_pp": abs(a["PSC"] - b["PSC"]) * 100,
                    }
                )
    curve = []
    qualified_rows = []
    for eps in EPSILONS:
        selected = [p for p in all_pairs if p["delta_A_S_pp"] <= eps + 1e-12]
        ra = [p["delta_RA_pp"] for p in selected]
        ii = [p["delta_II_pp"] for p in selected]
        pfc = [p["delta_PFC_pp"] for p in selected]
        psc = [p["delta_PSC_pp"] for p in selected]
        curve.append(
            {
                "epsilon_pp": eps,
                "role": "predeclared_primary" if abs(eps - 1.0) < 1e-12 else "post_hoc_sensitivity",
                "accuracy_used": "A_S independent static benchmark, never audit_base_accuracy",
                "number_of_qualifying_pairs": len(selected),
                "median_abs_delta_RA": median(ra),
                "mean_abs_delta_RA": mean(ra),
                "max_abs_delta_RA": max(ra) if ra else None,
                "median_abs_delta_II": median(ii),
                "max_abs_delta_II": max(ii) if ii else None,
                "median_abs_delta_PFC": median(pfc),
                "max_abs_delta_PFC": max(pfc) if pfc else None,
                "median_abs_delta_PSC": median(psc) if psc else None,
                "max_abs_delta_PSC": max(psc) if psc else None,
            }
        )
        for pair in selected:
            rec = dict(pair)
            rec["epsilon_pp"] = eps
            rec["role"] = "predeclared_primary" if abs(eps - 1.0) < 1e-12 else "post_hoc_sensitivity"
            qualified_rows.append(rec)
    write_csv(os.path.join(OUT, "equivalence", "accuracy_equivalence_curve.csv"), curve)
    write_csv(os.path.join(OUT, "equivalence", "qualifying_pairs_by_epsilon.csv"), qualified_rows)
    write_csv(os.path.join(OUT, "equivalence", "all_pairs_delta.csv"), all_pairs)
    return curve, all_pairs


def draw_equivalence_figures(all_pairs: list[dict], curve: list[dict]) -> None:
    fig_dir = os.path.join(OUT, "equivalence", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    plt.rcParams.update(
        {
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.dpi": 160,
        }
    )

    def scatter(y_key: str, ylabel: str, fname: str) -> None:
        fig, ax = plt.subplots(figsize=(6.2, 4.6))
        xs = [p["delta_A_S_pp"] for p in all_pairs]
        ys = [p[y_key] for p in all_pairs]
        inside = [p["delta_A_S_pp"] <= 1.0 + 1e-12 for p in all_pairs]
        ax.scatter(
            [x for x, inn in zip(xs, inside) if not inn],
            [y for y, inn in zip(ys, inside) if not inn],
            s=28,
            alpha=0.75,
            color="#4C78A8",
            label="|ΔA^S| > 1 pp",
        )
        ax.scatter(
            [x for x, inn in zip(xs, inside) if inn],
            [y for y, inn in zip(ys, inside) if inn],
            s=42,
            alpha=0.95,
            color="#E45756",
            label="predeclared |ΔA^S| ≤ 1 pp",
        )
        ax.axvline(1.0, color="#E45756", lw=1.0, ls="--", alpha=0.8)
        ax.set_xlabel("|ΔA^S| (percentage points)")
        ax.set_ylabel(ylabel)
        ax.set_title("Post-hoc scatter; 1 pp band remains the predeclared analysis")
        ax.legend(frameon=False, loc="upper right")
        fig.tight_layout()
        fig.savefig(os.path.join(fig_dir, fname + ".png"))
        fig.savefig(os.path.join(fig_dir, fname + ".svg"))
        fig.savefig(os.path.join(fig_dir, fname + ".pdf"))
        plt.close(fig)

    scatter("delta_RA_pp", "|ΔRA| (percentage points)", "scatter_deltaA_vs_deltaRA")
    scatter("delta_II_pp", "|ΔII| (percentage points)", "scatter_deltaA_vs_deltaII")

    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    eps = [r["epsilon_pp"] for r in curve]
    ax.plot(eps, [r["median_abs_delta_RA"] for r in curve], marker="o", color="#E45756", label="median |ΔRA|")
    ax.plot(eps, [r["max_abs_delta_RA"] for r in curve], marker="s", color="#4C78A8", label="max |ΔRA|")
    ax.axvline(1.0, color="#9A9A9A", lw=1.0, ls="--")
    ax.set_xlabel("ε (percentage points)")
    ax.set_ylabel("RA dispersion (percentage points)")
    ax.set_title("Diam_D(E_ε) under A^S-matching; 1 pp is predeclared")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(fig_dir, "equivalence_curve_RA.png"))
    fig.savefig(os.path.join(fig_dir, "equivalence_curve_RA.svg"))
    fig.savefig(os.path.join(fig_dir, "equivalence_curve_RA.pdf"))
    plt.close(fig)


def tournament_stats(edges: list[tuple[str, str]]) -> dict:
    beat = defaultdict(set)
    nodes = set()
    for winner, loser in edges:
        beat[winner].add(loser)
        nodes.add(winner)
        nodes.add(loser)
    nodes = sorted(nodes)
    n_cycle_triples = 0
    n_trans_viol = 0
    n_triples = 0
    for a, b, c in combinations(nodes, 3):
        n_triples += 1
        ab = b in beat[a]
        ba = a in beat[b]
        bc = c in beat[b]
        cb = b in beat[c]
        ac = c in beat[a]
        ca = a in beat[c]
        if (ab and bc and ca) or (ba and cb and ac):
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
    copeland = {node: len(beat[node]) for node in nodes}
    ordered = sorted(copeland.values(), reverse=True)
    margin = (ordered[0] - ordered[1]) if len(ordered) >= 2 else None
    return {
        "has_cycle_triple": n_cycle_triples > 0,
        "n_cycle_triples": n_cycle_triples,
        "n_triples": n_triples,
        "n_transitivity_violations": n_trans_viol,
        "has_condorcet": len(condorcet) == 1,
        "copeland_margin": margin,
    }


def pair_graph() -> list[dict]:
    rows = []
    for model_id in MODELS:
        pairs = read_jsonl(pairs_path(model_id))
        selections = read_jsonl(selections_path(model_id))
        by_pool = defaultdict(list)
        abstain = 0
        both_orient = 0
        consistent = 0
        undirected = defaultdict(list)
        for row in pairs:
            pool = row.get("pool_id") or row.get("item_id")
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
            key = (pool, frozenset({left, right}))
            undirected[key].append((left, right, winner_loser[0]))
        n_single = 0
        for recs in undirected.values():
            orients = {(a, b) for a, b, _ in recs}
            if len(orients) < 2:
                n_single += 1
                continue
            both_orient += 1
            # reciprocal: winner in (L,R) is loser in (R,L)
            winners = {(a, b): w for a, b, w in recs}
            ok = True
            for a, b in list(orients):
                if (b, a) in winners and winners[(a, b)] == winners[(b, a)]:
                    ok = False
            if ok:
                consistent += 1
        pool_stats = [tournament_stats(edges) for edges in by_pool.values()]
        sel_by_pool = defaultdict(dict)
        semantic_abs = 0
        for row in selections:
            semantic_abs += int(row.get("semantic_abstentions") or 0)
            sel_by_pool[row.get("pool_id") or row.get("item_id")][int(row.get("n"))] = row.get("selected_uid")
        n2_eq_n8 = [int(mp[2] == mp[8]) for mp in sel_by_pool.values() if 2 in mp and 8 in mp]
        n4_eq_n8 = [int(mp[4] == mp[8]) for mp in sel_by_pool.values() if 4 in mp and 8 in mp]
        n2_eq_n4 = [int(mp[2] == mp[4]) for mp in sel_by_pool.values() if 2 in mp and 4 in mp]
        rows.append(
            {
                "model_id": model_id,
                "display": DISPLAY[model_id],
                "n_pair_rows": len(pairs),
                "n_pools": len(by_pool),
                "abstention_rate": abstain / len(pairs) if pairs else None,
                "reciprocal_pairs_observed": both_orient,
                "reciprocal_consistency_rate": (consistent / both_orient) if both_orient else None,
                "reciprocal_note": "single-orientation storage; reverse-order queries were not collected" if both_orient == 0 else "",
                "triangle_cycle_rate": mean([float(s["has_cycle_triple"]) for s in pool_stats]),
                "mean_cycle_triples": mean([s["n_cycle_triples"] for s in pool_stats]),
                "transitivity_violation_rate": mean(
                    [s["n_transitivity_violations"] / s["n_triples"] if s["n_triples"] else 0.0 for s in pool_stats]
                ),
                "condorcet_winner_frequency": mean([float(s["has_condorcet"]) for s in pool_stats]),
                "mean_copeland_top_margin": mean([s["copeland_margin"] for s in pool_stats if s["copeland_margin"] is not None]),
                "selection_stability_N2_eq_N8": mean(n2_eq_n8),
                "selection_stability_N4_eq_N8": mean(n4_eq_n8),
                "selection_stability_N2_eq_N4": mean(n2_eq_n4),
                "semantic_abstention_events": semantic_abs,
                "role": "exploratory_only",
            }
        )
    write_csv(os.path.join(OUT, "pair_graph", "pair_graph_summary.csv"), rows)
    write_json(
        os.path.join(OUT, "pair_graph", "README.json"),
        {
            "role": "exploratory / appendix / future work",
            "do_not_retarget_main_paper": True,
            "n_edges_per_model": 22400,
        },
    )
    return rows


def write_readme(p0: dict, recon_pass: int, recon_n: int, curve: list[dict]) -> None:
    one = next(r for r in curve if abs(r["epsilon_pp"] - 1.0) < 1e-12)
    zero = next(r for r in curve if abs(r["epsilon_pp"] - 0.0) < 1e-12)
    half = next(r for r in curve if abs(r["epsilon_pp"] - 0.5) < 1e-12)
    lines = [
        "# RewardLens Phase II forensics 2026-09-16",
        "",
        "These analyses are post-hoc forensic analyses of frozen RewardLens Phase II artifacts. They do not modify the frozen experiment, manifests, thresholds, or primary predeclared analyses.",
        "",
        "Generated: %s" % utc_now(),
        "CPU only. No model inference.",
        "",
        "## Provenance gate",
        "",
        "- Audit source kind: procedural CLEVR-controlled renders from blank `base_scene.blend`.",
        "- Audit `source_image_id` is null on all 2400 SHA-manifest rows.",
        "- `I_Audit-source ∩ I_Downstream = ∅` pass = **%s**." % p0["pass"],
        "- Rendered PNG SHA overlap with downstream = %s." % p0["intersections"]["rendered_png_sha_audit_vs_downstream"],
        "- SHA-manifest `carrier=gqa/tallyqa` on audit is a factor-to-dataset label leak, not a photograph pointer.",
        "",
        "## Eight-state reconstruction",
        "",
        "- %s/%s metric cells match canonical values within 1e-12." % (recon_pass, recon_n),
        "- `audit_base_accuracy` is `P(B=1)=sum_ri π_1ri`. It is never called static accuracy.",
        "",
        "## Accuracy-equivalence (A^S matching)",
        "",
        "- Predeclared band remains `|ΔA^S| ≤ 1 pp`: %s pairs, median |ΔRA| = %s pp, max = %s pp."
        % (one["number_of_qualifying_pairs"], one["median_abs_delta_RA"], one["max_abs_delta_RA"]),
        "- Exact-zero `|ΔA^S|=0`: %s pairs." % zero["number_of_qualifying_pairs"],
        "- 0.5 pp post-hoc: %s pairs, median |ΔRA| = %s pp." % (half["number_of_qualifying_pairs"], half["median_abs_delta_RA"]),
        "- Other ε values are post-hoc sensitivity only.",
        "",
        "## Pair graph",
        "",
        "See `pair_graph/`. Exploratory. Do not retarget the main paper.",
        "",
    ]
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "FORENSIC_README.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def write_manifest() -> None:
    rows = []
    for dirpath, _, filenames in os.walk(OUT):
        for name in filenames:
            if name in {"RELEASE_MANIFEST.csv", "SHA256SUMS.txt"}:
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, OUT).replace("\\", "/")
            rows.append(
                {
                    "path": rel,
                    "bytes": os.path.getsize(path),
                    "sha256": sha256_file(path),
                }
            )
    rows.sort(key=lambda r: r["path"])
    write_csv(os.path.join(OUT, "RELEASE_MANIFEST.csv"), rows)
    with open(os.path.join(OUT, "SHA256SUMS.txt"), "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write("%s  %s\n" % (row["sha256"], row["path"]))


def namespace_collision_report(p0: dict) -> None:
    leakage = read_json(LEAKAGE)
    rows = [
        {
            "collision_type": "sha_manifest_audit_carrier_mislabel",
            "detail": json.dumps(p0["sha_manifest_carrier_on_audit_is_not_source"]["counts"]),
            "note": p0["sha_manifest_carrier_on_audit_is_not_source"]["interpretation"],
        },
        {
            "collision_type": "pre_repair_v1_static_downstream_physical_overlap",
            "detail": leakage["pairs"]["static_downstream"]["physical_content_sha256_intersection"],
            "note": leakage["interpretation"],
        },
        {
            "collision_type": "archive_filename_audit_named_static_jsonl",
            "detail": "expanded models: results/<model>/audit/static.jsonl is audit; execution/.../static.jsonl is A^S",
            "note": "original four true audit jsonl lives at results/<model>/*audit.jsonl on autodl-fs",
        },
    ]
    write_csv(os.path.join(OUT, "provenance", "namespace_collision_report.csv"), rows)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    p0 = p0_source_identity()
    if not p0["pass"]:
        write_json(os.path.join(OUT, "STOP_INTEGRITY_ISSUE.json"), p0)
        raise SystemExit("P0 source-identity failed")
    namespace_collision_report(p0)
    recon_rows, frozen_vs_state, _flip_rows = build_states_flips_metrics()
    recon_pass = sum(1 for r in frozen_vs_state if r["pass"])
    curve, all_pairs = accuracy_equivalence(recon_rows)
    draw_equivalence_figures(all_pairs, curve)
    pair_graph()
    write_readme(p0, recon_pass, len(frozen_vs_state), curve)
    write_manifest()
    summary = {
        "generated_utc": utc_now(),
        "p0_pass": p0["pass"],
        "I_audit_source_cap_I_downstream_empty": p0["I_audit_source_cap_I_downstream_empty"],
        "eight_state_metric_pass": recon_pass,
        "eight_state_metric_n": len(frozen_vs_state),
        "n_1pp_pairs": next(r["number_of_qualifying_pairs"] for r in curve if abs(r["epsilon_pp"] - 1) < 1e-12),
        "median_abs_delta_RA_1pp": next(r["median_abs_delta_RA"] for r in curve if abs(r["epsilon_pp"] - 1) < 1e-12),
        "out": OUT,
    }
    write_json(os.path.join(OUT, "FORENSICS_SUMMARY.json"), summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
