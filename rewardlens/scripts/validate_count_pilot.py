#!/usr/bin/env python3
"""Programmatic validation for COUNT PILOT V1."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

import numpy as np
from PIL import Image


VARIANTS = ("base", "relevant", "irrelevant")
REQUIRED_TRANSITIONS = {2, 3, 4}


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def detect_roots(config_path: str) -> tuple[str, str]:
    config_path = os.path.abspath(config_path)
    rewardlens_root = os.path.dirname(os.path.dirname(config_path))
    project_root = os.path.dirname(rewardlens_root)
    return project_root, rewardlens_root


def resolve_path(project_root: str, maybe_relative: str) -> str:
    if os.path.isabs(maybe_relative):
        return os.path.normpath(maybe_relative)
    return os.path.normpath(os.path.join(project_root, maybe_relative))


def close(a: Any, b: Any, tol: float = 1e-4) -> bool:
    return abs(float(a) - float(b)) < tol


def close_vec(a: list[Any], b: list[Any], tol: float = 1e-4) -> bool:
    if len(a) != len(b):
        return False
    return all(close(x, y, tol) for x, y in zip(a, b))


def count_targets(objects: list[dict[str, Any]], target_color: str) -> int:
    return sum(1 for obj in objects if obj.get("color") == target_color)


def base_objects(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [obj for obj in objects if obj.get("role") != "intervention"]


def intervention_object(objects: list[dict[str, Any]]) -> dict[str, Any]:
    marked = [obj for obj in objects if obj.get("role") == "intervention"]
    if marked:
        if len(marked) != 1:
            raise ValueError("expected exactly one intervention object, got %d" % len(marked))
        return marked[0]
    if not objects:
        raise ValueError("no objects in scene")
    return objects[-1]


def identity_fields(obj: dict[str, Any], include_color: bool = True) -> dict[str, Any]:
    payload = {
        "shape": obj["shape"],
        "size": obj["size"],
        "material": obj["material"],
        "rotation": float(obj["rotation"]),
        "x": float(obj["x"]),
        "y": float(obj["y"]),
    }
    if include_color:
        payload["color"] = obj["color"]
    return payload


def objects_equal(a: list[dict[str, Any]], b: list[dict[str, Any]]) -> bool:
    if len(a) != len(b):
        return False
    for oa, ob in zip(a, b):
        if identity_fields(oa, include_color=True) != identity_fields(ob, include_color=True):
            if not (
                oa["shape"] == ob["shape"]
                and oa["size"] == ob["size"]
                and oa["material"] == ob["material"]
                and oa["color"] == ob["color"]
                and close(oa["rotation"], ob["rotation"])
                and close(oa["x"], ob["x"])
                and close(oa["y"], ob["y"])
            ):
                return False
        if "3d_coords" in oa and "3d_coords" in ob and not close_vec(oa["3d_coords"], ob["3d_coords"], tol=1e-3):
            return False
    return True


def load_rgb(path: str) -> np.ndarray:
    with Image.open(path) as img:
        return np.asarray(img.convert("RGB"), dtype=np.float32)


def image_diff(path_a: str, path_b: str, change_threshold: float = 1.0) -> dict[str, float]:
    a = load_rgb(path_a)
    b = load_rgb(path_b)
    absdiff = np.abs(a - b)
    mad = float(absdiff.mean())
    changed = float((absdiff.max(axis=2) > change_threshold).mean())
    return {
        "mean_absolute_rgb_difference": mad,
        "changed_pixel_fraction": changed,
    }


def check(ok: bool, message: str, failures: list[str], checks: list[dict[str, Any]]) -> None:
    checks.append({"ok": bool(ok), "message": message})
    if not ok:
        failures.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate COUNT PILOT V1")
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "..", "configs", "count_pilot_v1.json"),
    )
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = os.path.abspath(args.config)
    config = load_json(config_path)
    project_root, _rewardlens_root = detect_roots(config_path)
    output_dir = args.output_dir or resolve_path(project_root, config["paths"]["output_dir"])
    width = int(config["render"]["width"])
    height = int(config["render"]["height"])
    num_triplets = int(config["num_triplets"])

    failures: list[str] = []
    checks: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    warnings: list[str] = []

    jsonl_path = os.path.join(output_dir, "pilot_manifest.jsonl")
    check(os.path.isfile(jsonl_path), "aggregate manifest exists: %s" % jsonl_path, failures, checks)

    manifests: list[dict[str, Any]] = []
    if os.path.isfile(jsonl_path):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    manifests.append(json.loads(line))

    check(len(manifests) == num_triplets, "exactly %d triplets in jsonl (got %d)" % (num_triplets, len(manifests)), failures, checks)

    manifest_dir_files = []
    manifest_dir = os.path.join(output_dir, "manifests")
    if os.path.isdir(manifest_dir):
        manifest_dir_files = sorted(name for name in os.listdir(manifest_dir) if name.endswith(".json"))
    check(len(manifest_dir_files) == num_triplets, "exactly %d per-triplet manifests" % num_triplets, failures, checks)

    transitions = []
    target_colors = []
    a_is_plus_one = []

    for manifest in manifests:
        triplet_id = manifest["triplet_id"]
        n = int(manifest["base"]["target_count"])
        n1 = n + 1
        transitions.append(n)
        target_colors.append(manifest["target_color"])

        cand = {str(manifest["candidate_a"]), str(manifest["candidate_b"])}
        check(cand == {str(n), str(n1)}, "%s candidates == {%s, %s}" % (triplet_id, n, n1), failures, checks)
        a_is_plus_one.append(str(manifest["candidate_a"]) == str(n1))

        check(
            manifest["relevant"]["preferred"] != manifest["base"]["preferred"],
            "%s relevant preferred flips vs base" % triplet_id,
            failures,
            checks,
        )
        check(
            manifest["irrelevant"]["preferred"] == manifest["base"]["preferred"],
            "%s irrelevant preferred stays with base" % triplet_id,
            failures,
            checks,
        )
        check(
            manifest["relevant"]["target_count_after"] == n1,
            "%s relevant target count after == n+1" % triplet_id,
            failures,
            checks,
        )
        check(
            manifest["irrelevant"]["target_count_after"] == n,
            "%s irrelevant target count after == n" % triplet_id,
            failures,
            checks,
        )

        scenes = {}
        images = {}
        for variant in VARIANTS:
            image_rel = manifest[variant]["image"]
            scene_rel = manifest[variant]["scene"]
            image_path = os.path.join(output_dir, image_rel)
            scene_path = os.path.join(output_dir, scene_rel)
            check(os.path.isfile(image_path), "%s image exists: %s" % (triplet_id, image_rel), failures, checks)
            check(os.path.isfile(scene_path), "%s scene exists: %s" % (triplet_id, scene_rel), failures, checks)
            contact_path = os.path.join(output_dir, "contact_sheets", "%s.png" % triplet_id)
            if variant == "base":
                check(os.path.isfile(contact_path), "%s contact sheet exists" % triplet_id, failures, checks)
            if os.path.isfile(image_path):
                with Image.open(image_path) as img:
                    check(img.size == (width, height), "%s %s PNG is %dx%d" % (triplet_id, variant, width, height), failures, checks)
                images[variant] = image_path
            if os.path.isfile(scene_path):
                scenes[variant] = load_json(scene_path)

        if len(scenes) != 3:
            continue

        for variant in VARIANTS:
            scene = scenes[variant]
            actual = count_targets(scene["objects"], manifest["target_color"])
            expected = n if variant != "relevant" else n1
            check(actual == expected, "%s %s scene target count == %s (got %s)" % (triplet_id, variant, expected, actual), failures, checks)

        check(
            objects_equal(base_objects(scenes["base"]["objects"]), base_objects(scenes["relevant"]["objects"])),
            "%s base objects identical in base vs relevant" % triplet_id,
            failures,
            checks,
        )
        check(
            objects_equal(base_objects(scenes["base"]["objects"]), base_objects(scenes["irrelevant"]["objects"])),
            "%s base objects identical in base vs irrelevant" % triplet_id,
            failures,
            checks,
        )

        rel_i = intervention_object(scenes["relevant"]["objects"])
        irr_i = intervention_object(scenes["irrelevant"]["objects"])
        geometry_ok = (
            rel_i["shape"] == irr_i["shape"]
            and rel_i["size"] == irr_i["size"]
            and rel_i["material"] == irr_i["material"]
            and close(rel_i["x"], irr_i["x"])
            and close(rel_i["y"], irr_i["y"])
            and close(rel_i["rotation"], irr_i["rotation"])
        )
        check(geometry_ok, "%s intervention geometry matched" % triplet_id, failures, checks)
        check(rel_i["color"] != irr_i["color"], "%s intervention colors differ" % triplet_id, failures, checks)
        check(rel_i["color"] == manifest["target_color"], "%s relevant intervention is target color" % triplet_id, failures, checks)
        check(irr_i["color"] != manifest["target_color"], "%s irrelevant intervention is non-target color" % triplet_id, failures, checks)

        contracts = [scenes[v]["render_contract"] for v in VARIANTS]
        seed_ok = len({int(c["cycles_seed"]) for c in contracts}) == 1
        check(seed_ok, "%s same cycles seed across variants" % triplet_id, failures, checks)
        camera_ok = all(close_vec(contracts[0]["camera_location"], c["camera_location"]) for c in contracts[1:])
        camera_ok = camera_ok and all(
            close_vec(contracts[0]["camera_rotation_euler"], c["camera_rotation_euler"]) for c in contracts[1:]
        )
        check(camera_ok, "%s same camera pose across variants" % triplet_id, failures, checks)
        lights_ok = True
        for key in ("lamp_key_location", "lamp_fill_location", "lamp_back_location"):
            lights_ok = lights_ok and all(close_vec(contracts[0][key], c[key]) for c in contracts[1:])
        check(lights_ok, "%s same lighting across variants" % triplet_id, failures, checks)
        jitter_ok = all(
            float(c.get("camera_jitter", 0)) == 0.0
            and float(c.get("key_light_jitter", 0)) == 0.0
            and float(c.get("fill_light_jitter", 0)) == 0.0
            and float(c.get("back_light_jitter", 0)) == 0.0
            for c in contracts
        )
        check(jitter_ok, "%s camera/light jitter disabled" % triplet_id, failures, checks)
        check(
            all(c.get("use_animated_seed") is False for c in contracts),
            "%s use_animated_seed disabled" % triplet_id,
            failures,
            checks,
        )

        if len(images) == 3:
            diff_rel = image_diff(images["base"], images["relevant"])
            diff_irr = image_diff(images["base"], images["irrelevant"])
            diff_pair = image_diff(images["relevant"], images["irrelevant"])
            denom = diff_irr["mean_absolute_rgb_difference"]
            ratio = None if denom == 0 else diff_rel["mean_absolute_rgb_difference"] / denom
            diagnostics.append(
                {
                    "triplet_id": triplet_id,
                    "base_vs_relevant": diff_rel,
                    "base_vs_irrelevant": diff_irr,
                    "relevant_vs_irrelevant": diff_pair,
                    "relevant_to_irrelevant_diff_ratio": ratio,
                }
            )

        for variant in VARIANTS:
            for obj in scenes[variant]["objects"]:
                px, py = obj["pixel_coords"][0], obj["pixel_coords"][1]
                if px < 0 or py < 0 or px >= width or py >= height:
                    warnings.append("%s %s object pixel_coords out of frame: %s" % (triplet_id, variant, obj["pixel_coords"]))

    check(set(transitions) == REQUIRED_TRANSITIONS, "count transitions cover 2->3, 3->4, 4->5", failures, checks)
    check(len(set(target_colors)) >= 5, "multiple target colors used (got %s)" % sorted(set(target_colors)), failures, checks)
    check(any(a_is_plus_one) and not all(a_is_plus_one), "candidate A/B order is shuffled across triplets", failures, checks)

    ratios = [d["relevant_to_irrelevant_diff_ratio"] for d in diagnostics if d["relevant_to_irrelevant_diff_ratio"] is not None]
    rel_mads = [d["base_vs_relevant"]["mean_absolute_rgb_difference"] for d in diagnostics]
    irr_mads = [d["base_vs_irrelevant"]["mean_absolute_rgb_difference"] for d in diagnostics]
    rel_fracs = [d["base_vs_relevant"]["changed_pixel_fraction"] for d in diagnostics]
    irr_fracs = [d["base_vs_irrelevant"]["changed_pixel_fraction"] for d in diagnostics]

    report = {
        "ok": len(failures) == 0,
        "num_triplets": len(manifests),
        "num_checks": len(checks),
        "num_failures": len(failures),
        "failures": failures,
        "warnings": warnings,
        "count_transitions": transitions,
        "transition_counts": {
            "2->3": transitions.count(2),
            "3->4": transitions.count(3),
            "4->5": transitions.count(4),
        },
        "target_colors": target_colors,
        "unique_target_colors": sorted(set(target_colors)),
        "candidate_a_is_n_plus_one": a_is_plus_one,
        "image_diff_diagnostics": diagnostics,
        "image_diff_summary": {
            "base_vs_relevant_mad_range": [min(rel_mads), max(rel_mads)] if rel_mads else None,
            "base_vs_irrelevant_mad_range": [min(irr_mads), max(irr_mads)] if irr_mads else None,
            "base_vs_relevant_changed_frac_range": [min(rel_fracs), max(rel_fracs)] if rel_fracs else None,
            "base_vs_irrelevant_changed_frac_range": [min(irr_fracs), max(irr_fracs)] if irr_fracs else None,
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
        print("COUNT_PILOT_V1_VALIDATION_FAILED", flush=True)
        return 1

    print("COUNT_PILOT_V1_VALIDATION_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
