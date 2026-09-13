#!/usr/bin/env python3
"""Validate attribute / presence / spatial controlled pilots."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import (  # noqa: E402
    REL_EPS,
    VARIANTS,
    detect_roots,
    load_json,
    resolve_path,
    write_json,
)


def close(a: Any, b: Any, tol: float = 1e-4) -> bool:
    return abs(float(a) - float(b)) < tol


def close_vec(a: list[Any], b: list[Any], tol: float = 1e-4) -> bool:
    return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))


def by_id(objects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {obj["object_id"]: obj for obj in objects if obj.get("object_id")}


def check(ok: bool, message: str, failures: list[str], checks: list[dict[str, Any]]) -> None:
    checks.append({"ok": bool(ok), "message": message})
    if not ok:
        failures.append(message)


def load_rgb(path: str) -> np.ndarray:
    with Image.open(path) as img:
        return np.asarray(img.convert("RGB"), dtype=np.float32)


def image_diff(path_a: str, path_b: str, change_threshold: float = 1.0) -> dict[str, float]:
    a = load_rgb(path_a)
    b = load_rgb(path_b)
    absdiff = np.abs(a - b)
    return {
        "mean_absolute_rgb_difference": float(absdiff.mean()),
        "changed_pixel_fraction": float((absdiff.max(axis=2) > change_threshold).mean()),
    }


def relation_holds(obj_a: dict[str, Any], obj_b: dict[str, Any], direction: list[float], eps: float = REL_EPS) -> bool:
    coords_a = obj_a.get("3d_coords", [obj_a["x"], obj_a["y"], 0.0])
    coords_b = obj_b.get("3d_coords", [obj_b["x"], obj_b["y"], 0.0])
    diff = [float(coords_a[k]) - float(coords_b[k]) for k in range(3)]
    return sum(diff[k] * float(direction[k]) for k in range(3)) > eps


def validate_attribute(triplet_id: str, manifest: dict[str, Any], scenes: dict[str, Any], failures, checks) -> None:
    query = manifest["query"]
    target_shape = query["target_shape"]
    color_from = query["color_from"]
    color_to = query["color_to"]
    for variant in VARIANTS:
        n = sum(1 for obj in scenes[variant]["objects"] if obj["shape"] == target_shape)
        check(n == 1, "%s %s unique target shape" % (triplet_id, variant), failures, checks)
        target = [obj for obj in scenes[variant]["objects"] if obj["shape"] == target_shape][0]
        expected = color_to if variant == "relevant" else color_from
        check(target["color"] == expected, "%s %s target color == %s" % (triplet_id, variant, expected), failures, checks)

    base_ids = by_id(scenes["base"]["objects"])
    rel_ids = by_id(scenes["relevant"]["objects"])
    irr_ids = by_id(scenes["irrelevant"]["objects"])
    target = base_ids["target"]
    matched = base_ids["matched"]
    check(target["size"] == matched["size"], "%s target/matched same size" % triplet_id, failures, checks)
    check(target["material"] == matched["material"], "%s target/matched same material" % triplet_id, failures, checks)
    check(target["shape"] != matched["shape"], "%s matched has different shape" % triplet_id, failures, checks)
    check(rel_ids["target"]["color"] == color_to, "%s relevant recolored target" % triplet_id, failures, checks)
    check(rel_ids["matched"]["color"] == color_from, "%s relevant matched unchanged" % triplet_id, failures, checks)
    check(irr_ids["matched"]["color"] == color_to, "%s irrelevant recolored matched" % triplet_id, failures, checks)
    check(irr_ids["target"]["color"] == color_from, "%s irrelevant target unchanged" % triplet_id, failures, checks)


def validate_presence(triplet_id: str, manifest: dict[str, Any], scenes: dict[str, Any], failures, checks) -> None:
    query = manifest["query"]
    color, shape = query["target_color"], query["target_shape"]

    def n_target(objects):
        return sum(1 for obj in objects if obj["color"] == color and obj["shape"] == shape)

    check(n_target(scenes["base"]["objects"]) == 1, "%s base has target" % triplet_id, failures, checks)
    check(n_target(scenes["relevant"]["objects"]) == 0, "%s relevant removed target" % triplet_id, failures, checks)
    check(n_target(scenes["irrelevant"]["objects"]) == 1, "%s irrelevant kept target" % triplet_id, failures, checks)
    check(len(scenes["relevant"]["objects"]) == len(scenes["base"]["objects"]) - 1, "%s relevant object count -1" % triplet_id, failures, checks)
    check(len(scenes["irrelevant"]["objects"]) == len(scenes["base"]["objects"]) - 1, "%s irrelevant object count -1" % triplet_id, failures, checks)

    base_ids = by_id(scenes["base"]["objects"])
    target, matched = base_ids["target"], base_ids["matched"]
    check(target["shape"] == matched["shape"], "%s removed objects same shape" % triplet_id, failures, checks)
    check(target["size"] == matched["size"], "%s removed objects same size" % triplet_id, failures, checks)
    check(target["material"] == matched["material"], "%s removed objects same material" % triplet_id, failures, checks)
    check("target" not in by_id(scenes["relevant"]["objects"]), "%s relevant lacks target id" % triplet_id, failures, checks)
    check("matched" not in by_id(scenes["irrelevant"]["objects"]), "%s irrelevant lacks matched id" % triplet_id, failures, checks)
    check("target" in by_id(scenes["irrelevant"]["objects"]), "%s irrelevant still has target" % triplet_id, failures, checks)


def validate_spatial(triplet_id: str, manifest: dict[str, Any], scenes: dict[str, Any], failures, checks) -> None:
    query = manifest["query"]
    left_vec = list(scenes["base"]["directions"]["left"])
    right_vec = list(scenes["base"]["directions"]["right"])

    def pair(scene):
        ids = by_id(scene["objects"])
        return ids["referent"], ids["anchor"]

    ref_b, anc_b = pair(scenes["base"])
    ref_r, anc_r = pair(scenes["relevant"])
    ref_i, anc_i = pair(scenes["irrelevant"])
    check(relation_holds(ref_b, anc_b, left_vec), "%s base referent left of anchor" % triplet_id, failures, checks)
    check(not relation_holds(ref_r, anc_r, left_vec), "%s relevant not left" % triplet_id, failures, checks)
    check(relation_holds(ref_r, anc_r, right_vec), "%s relevant referent right of anchor" % triplet_id, failures, checks)
    check(relation_holds(ref_i, anc_i, left_vec), "%s irrelevant relation stays left" % triplet_id, failures, checks)

    dx_rel = float(ref_r["x"]) - float(ref_b["x"])
    dy_rel = float(ref_r["y"]) - float(ref_b["y"])
    irr_ids_b = by_id(scenes["base"]["objects"])["distractor"]
    irr_ids_i = by_id(scenes["irrelevant"]["objects"])["distractor"]
    dx_irr = float(irr_ids_i["x"]) - float(irr_ids_b["x"])
    dy_irr = float(irr_ids_i["y"]) - float(irr_ids_b["y"])
    check(close(dx_rel, dx_irr, 1e-3) and close(dy_rel, dy_irr, 1e-3), "%s displacement matched" % triplet_id, failures, checks)
    check(close_vec(anc_b["3d_coords"], anc_r["3d_coords"], 1e-3), "%s anchor unmoved in relevant" % triplet_id, failures, checks)
    check(close_vec(anc_b["3d_coords"], anc_i["3d_coords"], 1e-3), "%s anchor unmoved in irrelevant" % triplet_id, failures, checks)
    check(ref_b["size"] == irr_ids_b["size"], "%s moved objects same size" % triplet_id, failures, checks)
    check(ref_b["material"] == irr_ids_b["material"], "%s moved objects same material" % triplet_id, failures, checks)

    n_ref = lambda objs, c, s: sum(1 for o in objs if o["color"] == c and o["shape"] == s)
    check(n_ref(scenes["base"]["objects"], query["referent_color"], query["referent_shape"]) == 1, "%s unique referent" % triplet_id, failures, checks)
    check(n_ref(scenes["base"]["objects"], query["anchor_color"], query["anchor_shape"]) == 1, "%s unique anchor" % triplet_id, failures, checks)


FACTOR_VALIDATORS = {
    "attribute": validate_attribute,
    "presence": validate_presence,
    "spatial": validate_spatial,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--factor", required=True, choices=["attribute", "presence", "spatial"])
    parser.add_argument("--config", default=None)
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.config is None:
        args.config = os.path.join(ROOT, "configs", "%s_pilot_v1.json" % args.factor)
    config_path = os.path.abspath(args.config)
    config = load_json(config_path)
    project_root, _ = detect_roots(config_path)
    output_dir = args.output_dir or resolve_path(project_root, config["paths"]["output_dir"])
    width = int(config["render"]["width"])
    height = int(config["render"]["height"])
    num_triplets = int(config["num_triplets"])
    factor = config.get("factor", args.factor)

    failures: list[str] = []
    checks: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    warnings: list[str] = []

    jsonl_path = os.path.join(output_dir, "pilot_manifest.jsonl")
    check(os.path.isfile(jsonl_path), "aggregate manifest exists", failures, checks)
    manifests = []
    if os.path.isfile(jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            manifests = [json.loads(line) for line in f if line.strip()]
    check(len(manifests) == num_triplets, "exactly %d triplets" % num_triplets, failures, checks)

    a_flags = []
    for manifest in manifests:
        triplet_id = manifest["triplet_id"]
        check(manifest["relevant"]["preferred"] != manifest["base"]["preferred"], "%s relevant flips" % triplet_id, failures, checks)
        check(manifest["irrelevant"]["preferred"] == manifest["base"]["preferred"], "%s irrelevant stays" % triplet_id, failures, checks)
        a_flags.append(manifest["candidate_a"] != manifest["base"]["answer"] if "answer" in manifest["base"] else manifest["candidate_a"] == manifest["relevant"]["answer"])

        scenes = {}
        images = {}
        for variant in VARIANTS:
            image_path = os.path.join(output_dir, manifest[variant]["image"])
            scene_path = os.path.join(output_dir, manifest[variant]["scene"])
            check(os.path.isfile(image_path), "%s image %s" % (triplet_id, variant), failures, checks)
            check(os.path.isfile(scene_path), "%s scene %s" % (triplet_id, variant), failures, checks)
            if variant == "base":
                check(os.path.isfile(os.path.join(output_dir, "contact_sheets", "%s.png" % triplet_id)), "%s contact sheet" % triplet_id, failures, checks)
            if os.path.isfile(image_path):
                with Image.open(image_path) as img:
                    check(img.size == (width, height), "%s %s size" % (triplet_id, variant), failures, checks)
                images[variant] = image_path
            if os.path.isfile(scene_path):
                scenes[variant] = load_json(scene_path)

        if len(scenes) != 3:
            continue

        contracts = [scenes[v]["render_contract"] for v in VARIANTS]
        check(len({int(c["cycles_seed"]) for c in contracts}) == 1, "%s same seed" % triplet_id, failures, checks)
        check(all(close_vec(contracts[0]["camera_location"], c["camera_location"]) for c in contracts[1:]), "%s same camera" % triplet_id, failures, checks)
        lights_ok = True
        for key in ("lamp_key_location", "lamp_fill_location", "lamp_back_location"):
            lights_ok = lights_ok and all(close_vec(contracts[0][key], c[key]) for c in contracts[1:])
        check(lights_ok, "%s same lights" % triplet_id, failures, checks)
        check(all(float(c.get("camera_jitter", 0)) == 0.0 for c in contracts), "%s no camera jitter" % triplet_id, failures, checks)

        FACTOR_VALIDATORS[factor](triplet_id, manifest, scenes, failures, checks)

        if len(images) == 3:
            diff_rel = image_diff(images["base"], images["relevant"])
            diff_irr = image_diff(images["base"], images["irrelevant"])
            denom = diff_irr["mean_absolute_rgb_difference"]
            diagnostics.append(
                {
                    "triplet_id": triplet_id,
                    "base_vs_relevant": diff_rel,
                    "base_vs_irrelevant": diff_irr,
                    "relevant_to_irrelevant_diff_ratio": None if denom == 0 else diff_rel["mean_absolute_rgb_difference"] / denom,
                }
            )

    check(any(a_flags) and not all(a_flags), "candidate A/B shuffled", failures, checks)

    ratios = [d["relevant_to_irrelevant_diff_ratio"] for d in diagnostics if d["relevant_to_irrelevant_diff_ratio"] is not None]
    report = {
        "ok": len(failures) == 0,
        "factor": factor,
        "num_triplets": len(manifests),
        "num_checks": len(checks),
        "num_failures": len(failures),
        "failures": failures,
        "warnings": warnings,
        "image_diff_diagnostics": diagnostics,
        "image_diff_summary": {
            "relevant_to_irrelevant_diff_ratio_range": [min(ratios), max(ratios)] if ratios else None,
        },
        "checks": checks,
    }
    report_path = os.path.join(output_dir, "validation_report.json")
    write_json(report_path, report)
    print("WROTE VALIDATION REPORT:", report_path, flush=True)
    print("CHECKS:", len(checks), "FAILURES:", len(failures), flush=True)
    if failures:
        for item in failures:
            print("FAIL:", item, flush=True)
        print("%s_PILOT_VALIDATION_FAILED" % factor.upper(), flush=True)
        return 1
    print("%s_PILOT_VALIDATION_OK" % factor.upper(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
