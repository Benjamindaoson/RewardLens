"""Programmatic QC for RewardLens-CLEVR controlled triplets.

Never deletes or rewrites FAIL rows to force a PASS quota.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

import numpy as np
from PIL import Image

from .common import REL_EPS, VARIANTS, load_json


EDGE_MARGIN = 8
MIN_PROJECTED_RADIUS = 6.0
NEAR_OVERLAP_RATIO = 0.55


def close(a: Any, b: Any, tol: float = 1e-4) -> bool:
    return abs(float(a) - float(b)) < tol


def close_vec(a: list[Any], b: list[Any], tol: float = 1e-4) -> bool:
    return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))


def by_id(objects: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {obj["object_id"]: obj for obj in objects if obj.get("object_id")}


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
        "width": int(a.shape[1]),
        "height": int(a.shape[0]),
    }


def projected_radius_px(obj: dict[str, Any]) -> float:
    size = str(obj.get("size", "small"))
    coords = obj.get("pixel_coords") or [160, 120, 10.0]
    depth = float(coords[2]) if len(coords) > 2 else 10.0
    base = 30.0 if size == "large" else 16.0
    return base * (9.0 / max(depth, 1.0))


def relation_holds(obj_a: dict[str, Any], obj_b: dict[str, Any], direction: list[float], eps: float = REL_EPS) -> bool:
    coords_a = obj_a.get("3d_coords", [obj_a["x"], obj_a["y"], 0.0])
    coords_b = obj_b.get("3d_coords", [obj_b["x"], obj_b["y"], 0.0])
    diff = [float(coords_a[k]) - float(coords_b[k]) for k in range(3)]
    return sum(diff[k] * float(direction[k]) for k in range(3)) > eps


def _flag(flags: list[str], message: str) -> None:
    flags.append(message)


def _status_from_flags(flags: list[str]) -> str:
    if any(item.startswith("FAIL:") for item in flags):
        return "FAIL"
    if any(item.startswith("BORDERLINE:") for item in flags):
        return "BORDERLINE"
    return "PASS"


def check_files_and_dims(output_dir: str, manifest: dict[str, Any], flags: list[str], width: int = 320, height: int = 240) -> dict[str, Any]:
    images = {}
    scenes = {}
    missing = False
    for variant in VARIANTS:
        image_path = os.path.join(output_dir, manifest[variant]["image"])
        scene_path = os.path.join(output_dir, manifest[variant]["scene"])
        if not os.path.isfile(image_path):
            _flag(flags, "FAIL: missing image %s" % variant)
            missing = True
        else:
            with Image.open(image_path) as img:
                if img.size != (width, height):
                    _flag(flags, "FAIL: %s image size %s" % (variant, img.size))
                images[variant] = image_path
        if not os.path.isfile(scene_path):
            _flag(flags, "FAIL: missing scene %s" % variant)
            missing = True
        else:
            scenes[variant] = load_json(scene_path)
    return {"images": images, "scenes": scenes, "complete": not missing and len(images) == 3 and len(scenes) == 3}


def check_preference_labels(manifest: dict[str, Any], flags: list[str]) -> None:
    ca, cb = str(manifest["candidate_a"]), str(manifest["candidate_b"])
    if ca == cb:
        _flag(flags, "FAIL: duplicate candidates")
    for variant in VARIANTS:
        pref = manifest[variant].get("preferred")
        if pref not in {"A", "B"}:
            _flag(flags, "FAIL: %s preferred not A/B" % variant)
    if manifest["relevant"].get("preferred") == manifest["base"].get("preferred"):
        _flag(flags, "FAIL: relevant preference did not flip")
    if manifest["irrelevant"].get("preferred") != manifest["base"].get("preferred"):
        _flag(flags, "FAIL: irrelevant preference changed")


def check_scene_consistency(scenes: dict[str, Any], flags: list[str]) -> dict[str, Any]:
    contracts = [scenes[v]["render_contract"] for v in VARIANTS]
    seeds = {int(c["cycles_seed"]) for c in contracts}
    if len(seeds) != 1:
        _flag(flags, "FAIL: cycles seed mismatch")
    if not all(close_vec(contracts[0]["camera_location"], c["camera_location"]) for c in contracts[1:]):
        _flag(flags, "FAIL: camera mismatch")
    for key in ("lamp_key_location", "lamp_fill_location", "lamp_back_location"):
        if not all(close_vec(contracts[0][key], c[key]) for c in contracts[1:]):
            _flag(flags, "FAIL: light mismatch %s" % key)
    if any(float(c.get("camera_jitter", 0)) != 0.0 for c in contracts):
        _flag(flags, "FAIL: camera jitter")
    return {"cycles_seed": list(seeds)[0] if seeds else None}


def check_visibility(scenes: dict[str, Any], flags: list[str], width: int = 320, height: int = 240) -> dict[str, Any]:
    vis = []
    for variant, scene in scenes.items():
        objects = scene.get("objects", [])
        centers = []
        for obj in objects:
            px, py, depth = obj.get("pixel_coords", [None, None, None])
            radius = projected_radius_px(obj)
            rec = {
                "variant": variant,
                "object_id": obj.get("object_id") or obj.get("role"),
                "px": px,
                "py": py,
                "depth": depth,
                "size": obj.get("size"),
                "projected_radius_px": radius,
            }
            vis.append(rec)
            if px is None or py is None:
                _flag(flags, "FAIL: %s missing pixel_coords" % variant)
                continue
            if px < 0 or py < 0 or px >= width or py >= height:
                _flag(flags, "FAIL: %s %s out_of_frame" % (variant, rec["object_id"]))
            elif px < EDGE_MARGIN or py < EDGE_MARGIN or px > width - EDGE_MARGIN or py > height - EDGE_MARGIN:
                _flag(flags, "BORDERLINE: %s %s near_edge" % (variant, rec["object_id"]))
            if radius < MIN_PROJECTED_RADIUS:
                _flag(flags, "BORDERLINE: %s %s tiny_projected_size" % (variant, rec["object_id"]))
            centers.append((float(px), float(py), radius, rec["object_id"], variant))
        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                x1, y1, r1, id1, _v = centers[i]
                x2, y2, r2, id2, _v2 = centers[j]
                dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
                if dist < NEAR_OVERLAP_RATIO * min(r1, r2):
                    _flag(flags, "BORDERLINE: %s possible_occlusion %s/%s" % (variant, id1, id2))
    return {"objects": vis}


def check_count_semantics(manifest: dict[str, Any], scenes: dict[str, Any], flags: list[str]) -> None:
    color = manifest.get("target_color")
    if not color:
        _flag(flags, "FAIL: missing target_color")
        return

    def n_target(objects):
        return sum(1 for obj in objects if obj.get("color") == color)

    base_n = n_target(scenes["base"]["objects"])
    rel_n = n_target(scenes["relevant"]["objects"])
    irr_n = n_target(scenes["irrelevant"]["objects"])
    expected_base = int(manifest["base"].get("target_count", base_n))
    if base_n != expected_base:
        _flag(flags, "FAIL: base target count %s != %s" % (base_n, expected_base))
    if rel_n != base_n + 1:
        _flag(flags, "FAIL: relevant did not add one target (%s -> %s)" % (base_n, rel_n))
    if irr_n != base_n:
        _flag(flags, "FAIL: irrelevant changed target count (%s -> %s)" % (base_n, irr_n))
    if len(scenes["relevant"]["objects"]) != len(scenes["base"]["objects"]) + 1:
        _flag(flags, "FAIL: relevant object cardinality")
    if len(scenes["irrelevant"]["objects"]) != len(scenes["base"]["objects"]) + 1:
        _flag(flags, "FAIL: irrelevant object cardinality")


def check_attribute_semantics(manifest: dict[str, Any], scenes: dict[str, Any], flags: list[str]) -> None:
    query = manifest.get("query") or {}
    shape = query.get("target_shape")
    color_from = query.get("color_from")
    color_to = query.get("color_to")
    for variant in VARIANTS:
        n = sum(1 for obj in scenes[variant]["objects"] if obj.get("shape") == shape)
        if n != 1:
            _flag(flags, "FAIL: %s target shape not unique" % variant)
        target = [obj for obj in scenes[variant]["objects"] if obj.get("shape") == shape]
        if not target:
            continue
        expected = color_to if variant == "relevant" else color_from
        if target[0].get("color") != expected:
            _flag(flags, "FAIL: %s target color %s != %s" % (variant, target[0].get("color"), expected))
    ids_b = by_id(scenes["base"]["objects"])
    ids_r = by_id(scenes["relevant"]["objects"])
    ids_i = by_id(scenes["irrelevant"]["objects"])
    if "target" not in ids_b or "matched" not in ids_b:
        _flag(flags, "FAIL: missing target/matched ids")
        return
    if ids_r.get("target", {}).get("color") != color_to:
        _flag(flags, "FAIL: relevant did not flip target attribute")
    if ids_r.get("matched", {}).get("color") != color_from:
        _flag(flags, "FAIL: relevant changed irrelevant target")
    if ids_i.get("matched", {}).get("color") != color_to:
        _flag(flags, "FAIL: irrelevant did not apply matched flip")
    if ids_i.get("target", {}).get("color") != color_from:
        _flag(flags, "FAIL: irrelevant changed queried target")


def check_presence_semantics(manifest: dict[str, Any], scenes: dict[str, Any], flags: list[str]) -> None:
    query = manifest.get("query") or {}
    color, shape = query.get("target_color"), query.get("target_shape")

    def n_target(objects):
        return sum(1 for obj in objects if obj.get("color") == color and obj.get("shape") == shape)

    if n_target(scenes["base"]["objects"]) != 1:
        _flag(flags, "FAIL: base missing unique target")
    if n_target(scenes["relevant"]["objects"]) != 0:
        _flag(flags, "FAIL: relevant did not remove target")
    if n_target(scenes["irrelevant"]["objects"]) != 1:
        _flag(flags, "FAIL: irrelevant removed queried target")
    ids_r = by_id(scenes["relevant"]["objects"])
    ids_i = by_id(scenes["irrelevant"]["objects"])
    if "target" in ids_r:
        _flag(flags, "FAIL: relevant still has target id")
    if "matched" in by_id(scenes["base"]["objects"]) and "matched" in ids_i:
        _flag(flags, "FAIL: irrelevant did not remove matched")
    if "target" not in ids_i:
        _flag(flags, "FAIL: irrelevant dropped target")


def check_spatial_semantics(manifest: dict[str, Any], scenes: dict[str, Any], flags: list[str]) -> None:
    left_vec = list(scenes["base"]["directions"]["left"])
    right_vec = list(scenes["base"]["directions"]["right"])
    try:
        ref_b = by_id(scenes["base"]["objects"])["referent"]
        anc_b = by_id(scenes["base"]["objects"])["anchor"]
        ref_r = by_id(scenes["relevant"]["objects"])["referent"]
        anc_r = by_id(scenes["relevant"]["objects"])["anchor"]
        ref_i = by_id(scenes["irrelevant"]["objects"])["referent"]
        anc_i = by_id(scenes["irrelevant"]["objects"])["anchor"]
        dist_b = by_id(scenes["base"]["objects"])["distractor"]
        dist_i = by_id(scenes["irrelevant"]["objects"])["distractor"]
    except KeyError:
        _flag(flags, "FAIL: missing spatial role ids")
        return
    if not relation_holds(ref_b, anc_b, left_vec):
        _flag(flags, "FAIL: base relation is not left-of")
    if not relation_holds(ref_r, anc_r, right_vec):
        _flag(flags, "FAIL: relevant did not flip to right-of")
    if relation_holds(ref_r, anc_r, left_vec):
        _flag(flags, "FAIL: relevant still left-of")
    if not relation_holds(ref_i, anc_i, left_vec):
        _flag(flags, "FAIL: irrelevant changed queried relation")
    dx_rel = float(ref_r["x"]) - float(ref_b["x"])
    dy_rel = float(ref_r["y"]) - float(ref_b["y"])
    dx_irr = float(dist_i["x"]) - float(dist_b["x"])
    dy_irr = float(dist_i["y"]) - float(dist_b["y"])
    if not (close(dx_rel, dx_irr, 1e-3) and close(dy_rel, dy_irr, 1e-3)):
        _flag(flags, "FAIL: displacement matching broken")


def check_matching_magnitude(factor: str, manifest: dict[str, Any], images: dict[str, str], flags: list[str]) -> dict[str, Any]:
    if len(images) != 3:
        return {}
    diff_rel = image_diff(images["base"], images["relevant"])
    diff_irr = image_diff(images["base"], images["irrelevant"])
    denom = diff_irr["mean_absolute_rgb_difference"]
    ratio = None if denom == 0 else diff_rel["mean_absolute_rgb_difference"] / denom
    if denom == 0:
        _flag(flags, "FAIL: irrelevant image identical to base")
    if diff_rel["mean_absolute_rgb_difference"] == 0:
        _flag(flags, "FAIL: relevant image identical to base")
    if ratio is not None and (ratio < 0.25 or ratio > 4.0):
        _flag(flags, "BORDERLINE: relevant/irrelevant RGB magnitude ratio %s" % round(ratio, 3))
    return {
        "base_vs_relevant": diff_rel,
        "base_vs_irrelevant": diff_irr,
        "relevant_to_irrelevant_diff_ratio": ratio,
        "factor": factor,
        "matching_contract": deepcopy(manifest.get("matching_contract") or {}),
    }


FACTOR_CHECKERS = {
    "count": check_count_semantics,
    "attribute": check_attribute_semantics,
    "presence": check_presence_semantics,
    "spatial": check_spatial_semantics,
}


def qc_triplet(output_dir: str, manifest: dict[str, Any], width: int = 320, height: int = 240) -> dict[str, Any]:
    flags: list[str] = []
    factor = str(manifest.get("factor", "unknown"))
    loaded = check_files_and_dims(output_dir, manifest, flags, width=width, height=height)
    check_preference_labels(manifest, flags)
    magnitude = {}
    visibility = {}
    if loaded["complete"]:
        check_scene_consistency(loaded["scenes"], flags)
        visibility = check_visibility(loaded["scenes"], flags, width=width, height=height)
        checker = FACTOR_CHECKERS.get(factor)
        if checker is None:
            _flag(flags, "FAIL: unknown factor %s" % factor)
        else:
            checker(manifest, loaded["scenes"], flags)
        magnitude = check_matching_magnitude(factor, manifest, loaded["images"], flags)
    status = _status_from_flags(flags)
    return {
        "triplet_id": manifest["triplet_id"],
        "factor": factor,
        "status": status,
        "flags": flags,
        "complete": loaded["complete"],
        "question": manifest.get("question"),
        "candidate_a": manifest.get("candidate_a"),
        "candidate_b": manifest.get("candidate_b"),
        "expected_preference": {
            "base": manifest["base"].get("preferred"),
            "relevant": manifest["relevant"].get("preferred"),
            "irrelevant": manifest["irrelevant"].get("preferred"),
        },
        "visibility": visibility,
        "magnitude": magnitude,
    }
