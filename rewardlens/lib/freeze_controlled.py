"""Incremental QC + deterministic PASS-subset freeze for RewardLens-CLEVR."""

from __future__ import annotations

import csv
import os
import shutil
from datetime import datetime, timezone
from typing import Any

from .common import VARIANTS, load_json, write_json
from .controlled_qc import qc_triplet
from .hashutil import sha256_file, sha256_json
from .jsonl_io import read_jsonl, write_jsonl

FACTORS = ("count", "attribute", "presence", "spatial")
LIB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LIB)
PROJECT = os.path.dirname(ROOT)

SCALE_DIRS = {
    "count": os.path.join(PROJECT, "outputs", "count_scale_v1"),
    "attribute": os.path.join(PROJECT, "outputs", "attribute_scale_v1"),
    "presence": os.path.join(PROJECT, "outputs", "presence_scale_v1"),
    "spatial": os.path.join(PROJECT, "outputs", "spatial_scale_v1"),
}
CONFIGS = {
    "count": os.path.join(ROOT, "configs", "count_scale_v1.json"),
    "attribute": os.path.join(ROOT, "configs", "attribute_scale_v1.json"),
    "presence": os.path.join(ROOT, "configs", "presence_scale_v1.json"),
    "spatial": os.path.join(ROOT, "configs", "spatial_scale_v1.json"),
}
SEEDS = {"count": 2026091205, "attribute": 2026091215, "presence": 2026091225, "spatial": 2026091235}
QC_RULES_VERSION = "controlled_qc.v1.20260912"
NATURAL_IMAGE_SOURCE = {
    "count": "tallyqa",
    "attribute": "gqa",
    "presence": "gqa",
    "spatial": "gqa",
}


def triplet_complete(output_dir: str, manifest: dict) -> bool:
    for variant in VARIANTS:
        if not os.path.isfile(os.path.join(output_dir, manifest[variant]["image"])):
            return False
        if not os.path.isfile(os.path.join(output_dir, manifest[variant]["scene"])):
            return False
    return True


def write_qc_csv(path: str, rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fields = ["factor", "triplet_id", "status", "n_flags", "flags"]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "factor": row["factor"],
                    "triplet_id": row["triplet_id"],
                    "status": row["status"],
                    "n_flags": len(row.get("flags") or []),
                    "flags": " | ".join(row.get("flags") or []),
                }
            )


def incremental_qc_factor(factor: str, output_dir: str) -> tuple[dict, list[dict]]:
    manifests = read_jsonl(os.path.join(output_dir, "pilot_manifest.jsonl"))
    cache_path = os.path.join(output_dir, "qc_report.json")
    cached: dict[str, dict] = {}
    if os.path.isfile(cache_path):
        try:
            old = load_json(cache_path)
            for row in old.get("triplets") or []:
                cached[row["triplet_id"]] = row
        except Exception:
            cached = {}
    rows = []
    incomplete = 0
    n_new = 0
    for manifest in manifests:
        if not triplet_complete(output_dir, manifest):
            incomplete += 1
            continue
        tid = manifest["triplet_id"]
        if tid in cached and cached[tid].get("status") in {"PASS", "BORDERLINE", "FAIL"}:
            rows.append(cached[tid])
            continue
        rows.append(qc_triplet(output_dir, manifest))
        n_new += 1
    summary = {
        "factor": factor,
        "output_dir": output_dir,
        "n_manifest_rows": len(manifests),
        "n_incomplete": incomplete,
        "n_qc": len(rows),
        "n_new": n_new,
        "PASS": sum(r["status"] == "PASS" for r in rows),
        "BORDERLINE": sum(r["status"] == "BORDERLINE" for r in rows),
        "FAIL": sum(r["status"] == "FAIL" for r in rows),
        "triplets": rows,
    }
    write_json(cache_path, summary)
    write_qc_csv(os.path.join(output_dir, "qc_summary.csv"), rows)
    write_jsonl(os.path.join(output_dir, "badcases.jsonl"), [r for r in rows if r["status"] != "PASS"])
    return summary, manifests


def freeze_pass_subset(
    *,
    version: str,
    n_pass: int,
    out_dir: str,
    manifest_name: str = "audit_manifest.jsonl",
) -> dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    all_items = []
    summaries = []
    factor_qc = {}
    ready = True
    for factor in FACTORS:
        summary, manifests = incremental_qc_factor(factor, SCALE_DIRS[factor])
        factor_qc[factor] = {k: summary[k] for k in summary if k != "triplets"}
        if summary["PASS"] < n_pass:
            ready = False
        id_to_manifest = {m["triplet_id"]: m for m in manifests}
        qc_map = {r["triplet_id"]: r for r in summary["triplets"]}
        pass_ids = sorted(r["triplet_id"] for r in summary["triplets"] if r["status"] == "PASS")
        keep = pass_ids[:n_pass] if ready or summary["PASS"] >= n_pass else []
        items = []
        for tid in keep:
            manifest = id_to_manifest[tid]
            qc = qc_map[tid]
            for variant in VARIANTS:
                items.append(
                    {
                        "item_id": "%s:%s" % (tid, variant),
                        "triplet_id": tid,
                        "factor": factor,
                        "variant": variant,
                        "image_path": os.path.normpath(os.path.join(SCALE_DIRS[factor], manifest[variant]["image"])),
                        "scene_path": os.path.normpath(os.path.join(SCALE_DIRS[factor], manifest[variant]["scene"])),
                        "question": manifest["question"],
                        "candidate_a": manifest["candidate_a"],
                        "candidate_b": manifest["candidate_b"],
                        "expected_preference": manifest[variant]["preferred"],
                        "seed": manifest.get("seed"),
                        "render_seed": manifest.get("render_seed"),
                        "qc_status": "PASS",
                        "qc_flags": qc.get("flags") or [],
                        "matching_contract": manifest.get("matching_contract"),
                        "audit_dataset_version": version,
                        "source_dir": SCALE_DIRS[factor],
                    }
                )
        all_items.extend(items)
        summaries.append(
            {
                "factor": factor,
                "generated_complete": summary["n_qc"],
                "PASS": summary["PASS"],
                "BORDERLINE": summary["BORDERLINE"],
                "FAIL": summary["FAIL"],
                "frozen_pass_n": len(keep),
                "needed": n_pass,
            }
        )
    status = {
        "audit_dataset_version": version,
        "ready": ready,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "per_factor": factor_qc,
        "policy": "PASS only, first N sorted triplet_ids. BORDERLINE/FAIL retained in QC, never upgraded.",
    }
    write_json(os.path.join(out_dir, "dataset_status.json"), status)
    write_json(os.path.join(PROJECT, "outputs", "dataset_status.json"), {"version_check": version, **status})
    if not ready:
        return {"ready": False, "status": status, "out_dir": out_dir}

    full_path = os.path.join(out_dir, manifest_name)
    write_jsonl(full_path, all_items)
    config_hashes = {f: sha256_file(CONFIGS[f]) for f in FACTORS if os.path.isfile(CONFIGS[f])}
    dataset_summary = {
        "audit_dataset_version": version,
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "factors": summaries,
        "PASS": sum(s["frozen_pass_n"] for s in summaries),
        "target_triplets": n_pass * 4,
        "target_pngs": n_pass * 4 * 3,
        "n_items": len(all_items),
        "fail_rows_retained_in_qc": True,
    }
    write_json(os.path.join(out_dir, "dataset_summary.json"), dataset_summary)
    csv_path = os.path.join(out_dir, "dataset_summary.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["factor", "generated_complete", "PASS", "BORDERLINE", "FAIL", "frozen_pass_n", "needed"]
        )
        writer.writeheader()
        for row in summaries:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})
    hashes = {
        "audit_dataset_version": version,
        "generation_config_hash": config_hashes,
        "generation_config_hash_combined": sha256_json(config_hashes),
        "manifest_hash": sha256_file(full_path),
        "n_items": len(all_items),
        "n_triplets": len(all_items) // 3,
        "sample_rule": "first %d PASS triplet_ids per factor, sorted" % n_pass,
        "excludes": ["BORDERLINE", "FAIL"],
    }
    write_json(os.path.join(out_dir, "hashes.json"), hashes)
    write_json(os.path.join(out_dir, "freeze_meta.json"), hashes)
    write_json(
        os.path.join(out_dir, "config.json"),
        {
            "audit_dataset_version": version,
            "n_pass_per_factor": n_pass,
            "factors": list(FACTORS),
            "scale_dirs": SCALE_DIRS,
            "master_seeds": SEEDS,
        },
    )
    return {"ready": True, "status": status, "summary": dataset_summary, "out_dir": out_dir, "n_items": len(all_items)}


def assemble_fast_track_from_factor_freezes(
    *,
    n_pass: int = 200,
    out_dir: str,
    version: str = "FAST_TRACK_AUDIT_V1",
) -> dict[str, Any]:
    """Build FAST_TRACK_AUDIT_V1 from already-frozen per-factor manifests.

    Does not re-select from live QC. Later PASS rows must not change the frozen subset.
    """
    os.makedirs(out_dir, exist_ok=True)
    all_items: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    factor_hashes: dict[str, dict] = {}
    missing: list[str] = []
    non_pass = 0
    image_paths: list[str] = []
    qc_rows: list[dict[str, Any]] = []
    for factor in FACTORS:
        fdir = os.path.join(out_dir, "factors", factor)
        man_path = os.path.join(fdir, "factor_audit_manifest.jsonl")
        hash_path = os.path.join(fdir, "hashes.json")
        if not os.path.isfile(man_path) or not os.path.isfile(hash_path):
            return {
                "ready": False,
                "status": {"ready": False, "missing_factor": factor},
                "out_dir": out_dir,
            }
        rows = read_jsonl(man_path)
        hashes = load_json(hash_path)
        factor_hashes[factor] = hashes
        triplet_ids = [r["triplet_id"] for r in rows]
        unique_triplets = sorted(set(triplet_ids))
        if len(unique_triplets) != n_pass or len(rows) != n_pass * len(VARIANTS):
            raise AssertionError(
                "factor %s freeze size mismatch triplets=%d items=%d need %d/%d"
                % (factor, len(unique_triplets), len(rows), n_pass, n_pass * len(VARIANTS))
            )
        if len(set(r["item_id"] for r in rows)) != len(rows):
            raise AssertionError("duplicate item_id in frozen factor %s" % factor)
        for row in rows:
            if row.get("qc_status") != "PASS":
                non_pass += 1
            img = row.get("image_path")
            if not img or not os.path.isfile(img):
                missing.append(str(img))
            else:
                image_paths.append(os.path.normpath(img))
            item = dict(row)
            item["audit_dataset_version"] = version
            all_items.append(item)
        ckpt_path = os.path.join(fdir, "freeze_checkpoint.json")
        ckpt = load_json(ckpt_path) if os.path.isfile(ckpt_path) else {}
        status_path = os.path.join(fdir, "factor_status.json")
        live = load_json(status_path) if os.path.isfile(status_path) else {}
        frozen_qc = os.path.join(fdir, "frozen_pass_qc.csv")
        if os.path.isfile(frozen_qc):
            with open(frozen_qc, "r", encoding="utf-8", newline="") as handle:
                qc_rows.extend(list(csv.DictReader(handle)))
        summaries.append(
            {
                "factor": factor,
                "generated_complete": live.get("source_item_count"),
                "PASS": live.get("PASS"),
                "BORDERLINE": live.get("BORDERLINE"),
                "FAIL": live.get("FAIL"),
                "frozen_pass_n": n_pass,
                "needed": n_pass,
                "source_pass_count_at_freeze": ckpt.get("source_pass_count_at_freeze"),
                "manifest_hash": hashes.get("manifest_hash"),
                "selection_rule": hashes.get("sample_rule") or ckpt.get("selection_rule"),
            }
        )
    if missing:
        raise AssertionError("missing images=%d e.g. %s" % (len(missing), missing[:5]))
    if non_pass:
        raise AssertionError("BORDERLINE/FAIL leaked into aggregate freeze: %d" % non_pass)
    expected_items = n_pass * len(FACTORS) * len(VARIANTS)
    if len(all_items) != expected_items:
        raise AssertionError("aggregate items %d != %d" % (len(all_items), expected_items))
    if len(set(image_paths)) != expected_items:
        raise AssertionError("unique images %d != %d" % (len(set(image_paths)), expected_items))

    full_path = os.path.join(out_dir, "audit_manifest.jsonl")
    write_jsonl(full_path, all_items)
    config_hashes = {f: sha256_file(CONFIGS[f]) for f in FACTORS if os.path.isfile(CONFIGS[f])}
    frozen_at = datetime.now(timezone.utc).isoformat()
    dataset_summary = {
        "audit_dataset_version": version,
        "frozen_at": frozen_at,
        "factors": summaries,
        "PASS": n_pass * len(FACTORS),
        "target_triplets": n_pass * len(FACTORS),
        "target_pngs": expected_items,
        "n_items": len(all_items),
        "n_images": len(set(image_paths)),
        "missing_images": 0,
        "BORDERLINE_included": 0,
        "FAIL_included": 0,
        "selection_rule": "union of per-factor frozen first %d PASS triplet_ids, sorted; not reselected from live QC" % n_pass,
        "pre_result": True,
        "model_blind": True,
        "fail_rows_retained_in_qc": True,
    }
    write_json(os.path.join(out_dir, "dataset_summary.json"), dataset_summary)
    csv_path = os.path.join(out_dir, "dataset_summary.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        fields = [
            "factor",
            "generated_complete",
            "PASS",
            "BORDERLINE",
            "FAIL",
            "frozen_pass_n",
            "needed",
            "source_pass_count_at_freeze",
            "manifest_hash",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in summaries:
            writer.writerow(row)
    if qc_rows:
        qc_csv = os.path.join(out_dir, "qc_summary.csv")
        fields = list(qc_rows[0].keys())
        with open(qc_csv, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(qc_rows)
    hashes = {
        "audit_dataset_version": version,
        "freeze_timestamp": frozen_at,
        "generation_config_hash": config_hashes,
        "generation_config_hash_combined": sha256_json(config_hashes),
        "manifest_hash": sha256_file(full_path),
        "factor_manifest_hashes": {f: factor_hashes[f].get("manifest_hash") for f in FACTORS},
        "n_items": len(all_items),
        "n_triplets": n_pass * len(FACTORS),
        "n_images": len(set(image_paths)),
        "sample_rule": dataset_summary["selection_rule"],
        "excludes": ["BORDERLINE", "FAIL"],
        "pre_result": True,
        "model_blind": True,
    }
    write_json(os.path.join(out_dir, "hashes.json"), hashes)
    write_json(os.path.join(out_dir, "freeze_meta.json"), hashes)
    write_json(
        os.path.join(out_dir, "config.json"),
        {
            "audit_dataset_version": version,
            "n_pass_per_factor": n_pass,
            "factors": list(FACTORS),
            "scale_dirs": SCALE_DIRS,
            "master_seeds": SEEDS,
            "qc_rules_version": QC_RULES_VERSION,
            "selection_rule": dataset_summary["selection_rule"],
        },
    )
    status = {
        "audit_dataset_version": version,
        "ready": True,
        "checked_at": frozen_at,
        "per_factor": {s["factor"]: s for s in summaries},
        "policy": "PASS only. Aggregate is the union of per-factor frozen manifests.",
    }
    write_json(os.path.join(out_dir, "dataset_status.json"), status)
    write_json(os.path.join(out_dir, "fast_track_status.json"), {"ready": True, "per_factor": summaries})
    return {"ready": True, "status": status, "summary": dataset_summary, "out_dir": out_dir, "n_items": len(all_items)}


def freeze_one_factor(factor: str, *, n_pass: int = 200, version: str = "FAST_TRACK_FACTOR") -> dict[str, Any]:
    """Freeze one audit factor as soon as it has n_pass PASS triplets. Does not wait for others."""
    if factor not in FACTORS:
        raise ValueError("unknown factor %s" % factor)
    summary, manifests = incremental_qc_factor(factor, SCALE_DIRS[factor])
    out_dir = os.path.join(PROJECT, "outputs", "fast_track_audit_v1", "factors", factor)
    os.makedirs(out_dir, exist_ok=True)
    report_dir = os.path.join(PROJECT, "reports", "runs")
    os.makedirs(report_dir, exist_ok=True)
    payload = {
        "factor": factor,
        "dataset_source_audit": "rewardlens_clevr",
        "dataset_source_static_downstream": NATURAL_IMAGE_SOURCE[factor],
        "PASS": summary["PASS"],
        "BORDERLINE": summary["BORDERLINE"],
        "FAIL": summary["FAIL"],
        "source_item_count": summary["n_qc"],
        "n_incomplete": summary["n_incomplete"],
        "needed": n_pass,
        "qc_rules_version": QC_RULES_VERSION,
        "ready": summary["PASS"] >= n_pass,
        "already_frozen": False,
        "out_dir": out_dir,
    }
    write_json(os.path.join(out_dir, "factor_status.json"), payload)
    if summary["PASS"] < n_pass:
        return payload
    hash_path = os.path.join(out_dir, "hashes.json")
    if os.path.isfile(hash_path):
        payload["already_frozen"] = True
        payload["ready"] = True
        payload["hashes"] = load_json(hash_path)
        payload["manifest_path"] = os.path.join(out_dir, "factor_audit_manifest.jsonl")
        alias_manifest = os.path.join(out_dir, "manifest.jsonl")
        if os.path.isfile(payload["manifest_path"]) and not os.path.isfile(alias_manifest):
            shutil.copy2(payload["manifest_path"], alias_manifest)
        cfg_src = CONFIGS.get(factor)
        if cfg_src and os.path.isfile(cfg_src) and not os.path.isfile(os.path.join(out_dir, "config.json")):
            shutil.copy2(cfg_src, os.path.join(out_dir, "config.json"))
        write_json(os.path.join(out_dir, "factor_status.json"), payload)
        return payload

    id_to_manifest = {m["triplet_id"]: m for m in manifests}
    qc_map = {r["triplet_id"]: r for r in summary["triplets"]}
    pass_ids = sorted(r["triplet_id"] for r in summary["triplets"] if r["status"] == "PASS")
    keep = pass_ids[:n_pass]
    items = []
    image_paths = []
    for tid in keep:
        manifest = id_to_manifest[tid]
        qc = qc_map[tid]
        if qc.get("status") != "PASS":
            raise AssertionError("non-PASS leaked into freeze: %s %s" % (tid, qc.get("status")))
        for variant in VARIANTS:
            img = os.path.normpath(os.path.join(SCALE_DIRS[factor], manifest[variant]["image"]))
            scene = os.path.normpath(os.path.join(SCALE_DIRS[factor], manifest[variant]["scene"]))
            if not os.path.isfile(img) or not os.path.isfile(scene):
                raise FileNotFoundError("missing asset %s %s" % (img, scene))
            image_paths.append(img)
            items.append(
                {
                    "item_id": "%s:%s" % (tid, variant),
                    "triplet_id": tid,
                    "factor": factor,
                    "variant": variant,
                    "image_path": img,
                    "scene_path": scene,
                    "question": manifest["question"],
                    "candidate_a": manifest["candidate_a"],
                    "candidate_b": manifest["candidate_b"],
                    "expected_preference": manifest[variant]["preferred"],
                    "seed": manifest.get("seed"),
                    "render_seed": manifest.get("render_seed"),
                    "qc_status": "PASS",
                    "qc_flags": qc.get("flags") or [],
                    "audit_dataset_version": version,
                    "source_dir": SCALE_DIRS[factor],
                }
            )
    item_ids = [r["item_id"] for r in items]
    triplet_ids = [r["triplet_id"] for r in items]
    dup_items = len(item_ids) != len(set(item_ids))
    dup_triplets = len(set(triplet_ids)) != n_pass
    dup_images = len(image_paths) != len(set(image_paths))
    if dup_items or dup_triplets or dup_images:
        raise AssertionError("duplicate freeze contents factor=%s items=%s triplets=%s images=%s" % (factor, dup_items, dup_triplets, dup_images))
    manifest_path = os.path.join(out_dir, "factor_audit_manifest.jsonl")
    write_jsonl(manifest_path, items)
    hashes = {
        "factor": factor,
        "audit_dataset_version": version,
        "qc_rules_version": QC_RULES_VERSION,
        "n_pass": n_pass,
        "n_items": len(items),
        "manifest_hash": sha256_file(manifest_path),
        "generation_config_hash": sha256_file(CONFIGS[factor]) if os.path.isfile(CONFIGS[factor]) else None,
        "sample_rule": "first %d PASS triplet_ids, sorted" % n_pass,
        "excludes": ["BORDERLINE", "FAIL"],
        "duplicate_status": "none",
        "unique_image_count": len(set(image_paths)),
        "frozen_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(hash_path, hashes)
    write_json(os.path.join(out_dir, "freeze_meta.json"), hashes)
    alias_manifest = os.path.join(out_dir, "manifest.jsonl")
    write_jsonl(alias_manifest, items)
    dataset_summary = {
        "factor": factor,
        "frozen_pass_n": n_pass,
        "n_items": len(items),
        "n_images": len(set(image_paths)),
        "source_pass_count_at_freeze": summary["PASS"],
        "BORDERLINE_at_freeze": summary["BORDERLINE"],
        "FAIL_at_freeze": summary["FAIL"],
        "selection_rule": "first %d PASS triplet_ids, sorted; skip BORDERLINE/FAIL" % n_pass,
        "pre_result": True,
        "model_blind": True,
        "audit_dataset_version": version,
    }
    write_json(os.path.join(out_dir, "dataset_summary.json"), dataset_summary)
    checkpoint = {
        "factor": factor,
        "freeze_timestamp": hashes["frozen_at"],
        "source_pass_count_at_freeze": summary["PASS"],
        "selection_rule": hashes["sample_rule"],
        "selected_triplet_ids": keep,
        "seed": SEEDS.get(factor),
        "config_hash": hashes["generation_config_hash"],
        "manifest_hash": hashes["manifest_hash"],
        "pre_result": True,
        "model_blind": True,
        "status_key": "%s_FAST_TRACK_FROZEN" % factor.upper(),
        "value": "PASS",
    }
    write_json(os.path.join(out_dir, "freeze_checkpoint.json"), checkpoint)
    cfg_src = CONFIGS.get(factor)
    if cfg_src and os.path.isfile(cfg_src):
        shutil.copy2(cfg_src, os.path.join(out_dir, "config.json"))
    src_qc_csv = os.path.join(SCALE_DIRS[factor], "qc_summary.csv")
    if os.path.isfile(src_qc_csv):
        shutil.copy2(src_qc_csv, os.path.join(out_dir, "qc_summary.csv"))
    write_qc_csv(os.path.join(out_dir, "frozen_pass_qc.csv"), [qc_map[tid] for tid in keep])
    payload.update(
        {
            "already_frozen": False,
            "frozen_pass_n": n_pass,
            "unique_image_count": len(set(image_paths)),
            "duplicate_status": "none",
            "manifest_path": manifest_path,
            "sha256": hashes["manifest_hash"],
            "freeze_timestamp": hashes["frozen_at"],
            "hashes": hashes,
        }
    )
    write_json(os.path.join(out_dir, "factor_status.json"), payload)
    write_json(os.path.join(report_dir, "fast_track_%s_freeze.json" % factor), payload)
    md = os.path.join(report_dir, "fast_track_%s_freeze.md" % factor)
    with open(md, "w", encoding="utf-8") as handle:
        handle.write(
            "\n".join(
                [
                    "# FAST_TRACK factor freeze — %s" % factor,
                    "",
                    "- factor: `%s`" % factor,
                    "- dataset source (audit): RewardLens-CLEVR",
                    "- dataset source (static/downstream): `%s`" % NATURAL_IMAGE_SOURCE[factor],
                    "- PASS count: %d" % summary["PASS"],
                    "- BORDERLINE count: %d" % summary["BORDERLINE"],
                    "- FAIL count: %d" % summary["FAIL"],
                    "- source item count (QC complete): %d" % summary["n_qc"],
                    "- unique image count frozen: %d" % len(set(image_paths)),
                    "- duplicate status: none",
                    "- static/downstream allocation: not this freeze (CLEVR audit only). Natural-image %s static/downstream already frozen independently."
                    % NATURAL_IMAGE_SOURCE[factor],
                    "- manifest path: `%s`" % manifest_path,
                    "- SHA256: `%s`" % hashes["manifest_hash"],
                    "- QC rules version: `%s`" % QC_RULES_VERSION,
                    "- freeze timestamp: `%s`" % hashes["frozen_at"],
                    "",
                    "## What this freeze can prove",
                    "",
                    "This factor now has a deterministic PASS-only 200-triplet audit subset for FAST_TRACK. BORDERLINE/FAIL were not upgraded. Sample rule is sorted triplet_id, independent of model scores.",
                    "",
                    "## What this freeze cannot prove",
                    "",
                    "It cannot prove RQ1–RQ3. It is not a natural-image result. It does not authorize combining this factor with unfrozen factors into FAST_TRACK_AUDIT_V1. GPU scores must not be used to re-pick these 200 rows.",
                    "",
                    "## Next dependency",
                    "",
                    "Wait until all four factors have this freeze, then freeze FAST_TRACK_AUDIT_V1. Do not build the full P0 GPU bundle before that combined freeze.",
                    "",
                ]
            )
        )
    payload["report_path"] = md
    return payload
