from __future__ import annotations

import math
import random
from copy import deepcopy
from typing import Any

from .common import (
    CLEVR_LEFT,
    ensure_ab_shuffle,
    is_left_of,
    is_right_of,
    make_object,
    preferred_for_answer,
)


SAFE_SLOTS = [
    [-2.1, -1.8],
    [0.0, -2.0],
    [2.1, -1.8],
    [-2.2, 0.0],
    [0.0, 0.1],
    [2.2, 0.0],
    [-2.0, 1.8],
    [0.1, 1.9],
    [2.0, 1.8],
]

SHAPES = ["cube", "sphere", "cylinder"]
COLORS = ["gray", "red", "blue", "green", "brown", "purple", "cyan", "yellow"]
MATERIALS = ["rubber", "metal"]
SIZES = ["small", "large"]

ATTRIBUTE_COLOR_PAIRS = [
    ["red", "blue"],
    ["blue", "red"],
    ["green", "yellow"],
    ["yellow", "green"],
    ["purple", "cyan"],
    ["cyan", "purple"],
    ["brown", "gray"],
    ["gray", "brown"],
    ["red", "yellow"],
    ["blue", "green"],
]


def _slot_key(slot: list[float]) -> tuple[float, float]:
    return (round(float(slot[0]), 4), round(float(slot[1]), 4))


def _similar_depth_pairs(slots: list[list[float]], max_dy: float = 0.35) -> list[tuple[list[float], list[float]]]:
    pairs = []
    for i, a in enumerate(slots):
        for b in slots[i + 1 :]:
            if abs(float(a[1]) - float(b[1])) <= max_dy:
                pairs.append((list(a), list(b)))
    return pairs


def _unused(slots: list[list[float]], taken: list[list[float]]) -> list[list[float]]:
    taken_keys = {_slot_key(s) for s in taken}
    return [list(s) for s in slots if _slot_key(s) not in taken_keys]


def _clone_objects(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return deepcopy(objects)


def _recolor(objects: list[dict[str, Any]], object_id: str, color: str) -> list[dict[str, Any]]:
    out = _clone_objects(objects)
    found = False
    for obj in out:
        if obj["object_id"] == object_id:
            obj["color"] = color
            found = True
    if not found:
        raise RuntimeError("object_id not found: %s" % object_id)
    return out


def _remove(objects: list[dict[str, Any]], object_id: str) -> list[dict[str, Any]]:
    out = [obj for obj in _clone_objects(objects) if obj["object_id"] != object_id]
    if len(out) != len(objects) - 1:
        raise RuntimeError("failed to remove object_id=%s" % object_id)
    return out


def _move(objects: list[dict[str, Any]], object_id: str, dest: list[float]) -> list[dict[str, Any]]:
    out = _clone_objects(objects)
    found = False
    for obj in out:
        if obj["object_id"] == object_id:
            obj["x"] = float(dest[0])
            obj["y"] = float(dest[1])
            found = True
    if not found:
        raise RuntimeError("object_id not found: %s" % object_id)
    return out


def _count_unique_shape(objects: list[dict[str, Any]], shape: str) -> int:
    return sum(1 for obj in objects if obj["shape"] == shape)


def _count_color_shape(objects: list[dict[str, Any]], color: str, shape: str) -> int:
    return sum(1 for obj in objects if obj["color"] == color and obj["shape"] == shape)


def spec_to_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    triplet_id = spec["triplet_id"]
    factor = spec["factor"]
    return {
        "triplet_id": triplet_id,
        "factor": factor,
        "seed": spec["seed"],
        "render_seed": spec["render_seed"],
        "question": spec["question"],
        "candidate_a": spec["candidate_a"],
        "candidate_b": spec["candidate_b"],
        "query": spec.get("query"),
        "uniqueness": spec.get("uniqueness"),
        "magnitude": spec.get("magnitude"),
        "matching_contract": spec.get("matching_contract"),
        "base": {
            "preferred": spec["preferred"]["base"],
            "answer": spec["answers"]["base"],
            "image": "images/%s_base.png" % triplet_id,
            "scene": "scenes/%s_base.json" % triplet_id,
        },
        "relevant": {
            "operation": spec["operations"]["relevant"],
            "preferred": spec["preferred"]["relevant"],
            "answer": spec["answers"]["relevant"],
            "image": "images/%s_relevant.png" % triplet_id,
            "scene": "scenes/%s_relevant.json" % triplet_id,
        },
        "irrelevant": {
            "operation": spec["operations"]["irrelevant"],
            "preferred": spec["preferred"]["irrelevant"],
            "answer": spec["answers"]["irrelevant"],
            "image": "images/%s_irrelevant.png" % triplet_id,
            "scene": "scenes/%s_irrelevant.json" % triplet_id,
        },
    }


def build_attribute_triplet(index: int, rng: random.Random, prefix: str = "attr") -> dict[str, Any]:
    triplet_id = "%s_%06d" % (prefix, index)
    render_seed = rng.randint(1, 10**9)
    target_shape = SHAPES[index % len(SHAPES)]
    other_shapes = [s for s in SHAPES if s != target_shape]
    color_from, color_to = ATTRIBUTE_COLOR_PAIRS[index % len(ATTRIBUTE_COLOR_PAIRS)]
    size = rng.choice(SIZES)
    material = rng.choice(MATERIALS)
    matched_shape = rng.choice(other_shapes)

    slots = [list(s) for s in SAFE_SLOTS]
    pairs = _similar_depth_pairs(slots)
    if not pairs:
        raise RuntimeError("no similar-depth slot pairs")
    target_slot, matched_slot = rng.choice(pairs)
    remaining = _unused(slots, [target_slot, matched_slot])
    rng.shuffle(remaining)
    n_extra = 2
    extra_slots = remaining[:n_extra]

    target = make_object("target", target_shape, color_from, size, material, target_slot, rng.uniform(0, 360), "target")
    matched = make_object("matched", matched_shape, color_from, size, material, matched_slot, rng.uniform(0, 360), "matched")
    extras = []
    for i, slot in enumerate(extra_slots):
        extras.append(
            make_object(
                "distractor",
                rng.choice(other_shapes),
                rng.choice([c for c in COLORS if c != color_from or True]),
                rng.choice(SIZES),
                rng.choice(MATERIALS),
                slot,
                rng.uniform(0, 360),
                "distractor_%d" % i,
            )
        )
        if extras[-1]["shape"] == target_shape:
            extras[-1]["shape"] = rng.choice(other_shapes)

    base_objects = [target, matched] + extras
    if _count_unique_shape(base_objects, target_shape) != 1:
        raise RuntimeError("attribute uniqueness failed for %s" % triplet_id)

    a_is_to = rng.choice([True, False])
    if a_is_to:
        candidate_a, candidate_b = color_to, color_from
    else:
        candidate_a, candidate_b = color_from, color_to

    answers = {"base": color_from, "relevant": color_to, "irrelevant": color_from}
    preferred = {
        variant: preferred_for_answer(candidate_a, candidate_b, answers[variant])
        for variant in answers
    }

    return {
        "triplet_id": triplet_id,
        "factor": "attribute",
        "seed": render_seed,
        "render_seed": render_seed,
        "question": "What color is the %s?" % target_shape,
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "a_is_to": a_is_to,
        "answers": answers,
        "preferred": preferred,
        "operations": {
            "relevant": "recolor_target",
            "irrelevant": "recolor_matched_nontarget",
        },
        "query": {
            "target_shape": target_shape,
            "color_from": color_from,
            "color_to": color_to,
            "target_id": "target",
            "matched_id": "matched",
        },
        "uniqueness": {"rule": "exactly_one_object_with_target_shape", "target_shape": target_shape},
        "magnitude": {
            "attribute_edit_count": 1,
            "color_transition": [color_from, color_to],
            "matched_size": size,
            "matched_material": material,
            "scene_graph_edit_distance": 1,
        },
        "matching_contract": {
            "same_camera": True,
            "same_lighting": True,
            "same_render_seed": True,
            "same_color_transition": True,
            "same_size": True,
            "same_material": True,
            "similar_depth_slots": True,
            "only_semantic_difference": "which object receives the color edit; target uniqueness is shape",
        },
        "variants": {
            "base": {"objects": _clone_objects(base_objects)},
            "relevant": {"objects": _recolor(base_objects, "target", color_to)},
            "irrelevant": {"objects": _recolor(base_objects, "matched", color_to)},
        },
        "intervention": {
            "type": "recolor",
            "color_from": color_from,
            "color_to": color_to,
            "relevant_object_id": "target",
            "irrelevant_object_id": "matched",
            "matched_size": size,
            "matched_material": material,
        },
    }


def flip_attribute_ab(spec: dict[str, Any]) -> dict[str, Any]:
    spec["a_is_to"] = not bool(spec["a_is_to"])
    spec["candidate_a"], spec["candidate_b"] = spec["candidate_b"], spec["candidate_a"]
    spec["preferred"] = {
        variant: preferred_for_answer(spec["candidate_a"], spec["candidate_b"], spec["answers"][variant])
        for variant in spec["answers"]
    }
    return spec


def build_presence_triplet(index: int, rng: random.Random, prefix: str = "pres") -> dict[str, Any]:
    triplet_id = "%s_%06d" % (prefix, index)
    render_seed = rng.randint(1, 10**9)
    target_shape = SHAPES[index % len(SHAPES)]
    target_color = COLORS[index % len(COLORS)]
    other_colors = [c for c in COLORS if c != target_color]
    matched_color = rng.choice(other_colors)
    size = rng.choice(SIZES)
    material = rng.choice(MATERIALS)

    slots = [list(s) for s in SAFE_SLOTS]
    pairs = _similar_depth_pairs(slots)
    target_slot, matched_slot = rng.choice(pairs)
    remaining = _unused(slots, [target_slot, matched_slot])
    rng.shuffle(remaining)
    extra_slots = remaining[:2]

    # Front-row preference for the target so removal is visible.
    if target_slot[1] > matched_slot[1]:
        target_slot, matched_slot = matched_slot, target_slot

    target = make_object("target", target_shape, target_color, size, material, target_slot, rng.uniform(0, 360), "target")
    matched = make_object("matched", target_shape, matched_color, size, material, matched_slot, rng.uniform(0, 360), "matched")
    extras = []
    other_shapes = [s for s in SHAPES if s != target_shape]
    for i, slot in enumerate(extra_slots):
        extras.append(
            make_object(
                "distractor",
                rng.choice(other_shapes),
                rng.choice(COLORS),
                rng.choice(SIZES),
                rng.choice(MATERIALS),
                slot,
                rng.uniform(0, 360),
                "distractor_%d" % i,
            )
        )

    base_objects = [target, matched] + extras
    if _count_color_shape(base_objects, target_color, target_shape) != 1:
        raise RuntimeError("presence uniqueness failed for %s" % triplet_id)

    a_is_no = rng.choice([True, False])
    if a_is_no:
        candidate_a, candidate_b = "no", "yes"
    else:
        candidate_a, candidate_b = "yes", "no"
    answers = {"base": "yes", "relevant": "no", "irrelevant": "yes"}
    preferred = {
        variant: preferred_for_answer(candidate_a, candidate_b, answers[variant])
        for variant in answers
    }

    size_radius = 0.7 if size == "large" else 0.35
    area_proxy = math.pi * (size_radius ** 2)

    return {
        "triplet_id": triplet_id,
        "factor": "presence",
        "seed": render_seed,
        "render_seed": render_seed,
        "question": "Is there a %s %s?" % (target_color, target_shape),
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "a_is_no": a_is_no,
        "answers": answers,
        "preferred": preferred,
        "operations": {
            "relevant": "remove_target",
            "irrelevant": "remove_matched_nontarget",
        },
        "query": {
            "target_color": target_color,
            "target_shape": target_shape,
            "matched_color": matched_color,
            "target_id": "target",
            "matched_id": "matched",
        },
        "uniqueness": {
            "rule": "exactly_one_target_color_shape_in_base_and_irrelevant",
            "target_color": target_color,
            "target_shape": target_shape,
        },
        "magnitude": {
            "removed_size": size,
            "removed_shape": target_shape,
            "removed_material": material,
            "projected_area_proxy": area_proxy,
            "scene_graph_edit_distance": 1,
        },
        "matching_contract": {
            "same_camera": True,
            "same_lighting": True,
            "same_render_seed": True,
            "same_removed_shape": True,
            "same_removed_size": True,
            "same_removed_material": True,
            "similar_depth_slots": True,
            "only_semantic_difference": "which object is removed; only target color+shape answers the question",
        },
        "variants": {
            "base": {"objects": _clone_objects(base_objects)},
            "relevant": {"objects": _remove(base_objects, "target")},
            "irrelevant": {"objects": _remove(base_objects, "matched")},
        },
        "intervention": {
            "type": "remove",
            "relevant_object_id": "target",
            "irrelevant_object_id": "matched",
            "matched_shape": target_shape,
            "matched_size": size,
            "matched_material": material,
        },
    }


def flip_presence_ab(spec: dict[str, Any]) -> dict[str, Any]:
    spec["a_is_no"] = not bool(spec["a_is_no"])
    spec["candidate_a"], spec["candidate_b"] = spec["candidate_b"], spec["candidate_a"]
    spec["preferred"] = {
        variant: preferred_for_answer(spec["candidate_a"], spec["candidate_b"], spec["answers"][variant])
        for variant in spec["answers"]
    }
    return spec


SPATIAL_LAYOUTS = [
    {
        "anchor": [0.0, -0.2],
        "referent_from": [-2.4, -1.6],
        "referent_to": [2.4, -1.6],
        "distractor_from": [-2.4, 1.6],
        "distractor_to": [2.4, 1.6],
        "extras": [[0.0, 0.9]],
    },
    {
        "anchor": [0.2, 0.0],
        "referent_from": [-2.3, -1.7],
        "referent_to": [2.5, -1.7],
        "distractor_from": [-2.3, 1.7],
        "distractor_to": [2.5, 1.7],
        "extras": [[0.0, 0.8]],
    },
]


def build_spatial_triplet(index: int, rng: random.Random, prefix: str = "spat") -> dict[str, Any]:
    triplet_id = "%s_%06d" % (prefix, index)
    render_seed = rng.randint(1, 10**9)
    layout = SPATIAL_LAYOUTS[index % len(SPATIAL_LAYOUTS)]

    shape_pairs = [
        ("cube", "sphere"),
        ("cube", "cylinder"),
        ("sphere", "cylinder"),
        ("sphere", "cube"),
        ("cylinder", "cube"),
        ("cylinder", "sphere"),
    ]
    ref_shape, anc_shape = shape_pairs[index % len(shape_pairs)]
    color_pairs = [
        ("red", "blue"),
        ("blue", "red"),
        ("green", "purple"),
        ("yellow", "brown"),
        ("cyan", "gray"),
        ("purple", "yellow"),
        ("brown", "cyan"),
        ("gray", "green"),
        ("red", "yellow"),
        ("blue", "green"),
    ]
    ref_color, anc_color = color_pairs[index % len(color_pairs)]
    extra_shape = [s for s in SHAPES if s not in (ref_shape, anc_shape)][0]
    extra_colors = [c for c in COLORS if c not in (ref_color, anc_color)]

    size = rng.choice(SIZES)
    material = rng.choice(MATERIALS)
    # Keep moved objects the same size/material so displacement is the only geometric change of interest.
    ref_rot = rng.uniform(0, 360)
    dist_rot = rng.uniform(0, 360)

    referent = make_object(
        "target", ref_shape, ref_color, size, material, layout["referent_from"], ref_rot, "referent"
    )
    anchor = make_object(
        "anchor",
        anc_shape,
        anc_color,
        rng.choice(SIZES),
        rng.choice(MATERIALS),
        layout["anchor"],
        rng.uniform(0, 360),
        "anchor",
    )
    distractor = make_object(
        "matched", extra_shape, rng.choice(extra_colors), size, material, layout["distractor_from"], dist_rot, "distractor"
    )
    extras = []
    for i, slot in enumerate(layout["extras"]):
        extras.append(
            make_object(
                "distractor",
                extra_shape,
                rng.choice(extra_colors),
                "small",
                rng.choice(MATERIALS),
                slot,
                rng.uniform(0, 360),
                "extra_%d" % i,
            )
        )

    base_objects = [referent, anchor, distractor] + extras
    if not is_left_of(referent, anchor):
        raise RuntimeError("spatial base relation failed for %s" % triplet_id)
    moved_ref = dict(referent)
    moved_ref["x"], moved_ref["y"] = float(layout["referent_to"][0]), float(layout["referent_to"][1])
    if is_left_of(moved_ref, anchor) or not is_right_of(moved_ref, anchor):
        raise RuntimeError("spatial relevant relation failed for %s" % triplet_id)

    dx = float(layout["referent_to"][0]) - float(layout["referent_from"][0])
    dy = float(layout["referent_to"][1]) - float(layout["referent_from"][1])
    irr_dx = float(layout["distractor_to"][0]) - float(layout["distractor_from"][0])
    irr_dy = float(layout["distractor_to"][1]) - float(layout["distractor_from"][1])
    if abs(dx - irr_dx) > 1e-6 or abs(dy - irr_dy) > 1e-6:
        raise RuntimeError("spatial displacement mismatch for %s" % triplet_id)

    a_is_no = rng.choice([True, False])
    if a_is_no:
        candidate_a, candidate_b = "no", "yes"
    else:
        candidate_a, candidate_b = "yes", "no"
    answers = {"base": "yes", "relevant": "no", "irrelevant": "yes"}
    preferred = {
        variant: preferred_for_answer(candidate_a, candidate_b, answers[variant])
        for variant in answers
    }

    question = "Is the %s %s left of the %s %s?" % (ref_color, ref_shape, anc_color, anc_shape)
    euclid = math.sqrt(dx * dx + dy * dy)

    return {
        "triplet_id": triplet_id,
        "factor": "spatial",
        "seed": render_seed,
        "render_seed": render_seed,
        "question": question,
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "a_is_no": a_is_no,
        "answers": answers,
        "preferred": preferred,
        "operations": {
            "relevant": "move_referent_until_relation_flips",
            "irrelevant": "move_matched_distractor_same_displacement",
        },
        "query": {
            "relation": "left",
            "referent_id": "referent",
            "anchor_id": "anchor",
            "referent_color": ref_color,
            "referent_shape": ref_shape,
            "anchor_color": anc_color,
            "anchor_shape": anc_shape,
        },
        "uniqueness": {
            "rule": "unique_referent_and_anchor_color_shape",
            "referent": [ref_color, ref_shape],
            "anchor": [anc_color, anc_shape],
        },
        "magnitude": {
            "dx": dx,
            "dy": dy,
            "euclidean": euclid,
            "scene_graph_edit_distance": 1,
        },
        "matching_contract": {
            "same_camera": True,
            "same_lighting": True,
            "same_render_seed": True,
            "same_world_displacement": True,
            "same_moved_size": True,
            "same_moved_material": True,
            "only_semantic_difference": "which object moves; query left/right relation flips only in relevant",
        },
        "variants": {
            "base": {"objects": _clone_objects(base_objects)},
            "relevant": {"objects": _move(base_objects, "referent", layout["referent_to"])},
            "irrelevant": {"objects": _move(base_objects, "distractor", layout["distractor_to"])},
        },
        "intervention": {
            "type": "translate",
            "relevant_object_id": "referent",
            "irrelevant_object_id": "distractor",
            "dx": dx,
            "dy": dy,
            "euclidean": euclid,
            "left_vec": list(CLEVR_LEFT),
        },
    }


def flip_spatial_ab(spec: dict[str, Any]) -> dict[str, Any]:
    spec["a_is_no"] = not bool(spec["a_is_no"])
    spec["candidate_a"], spec["candidate_b"] = spec["candidate_b"], spec["candidate_a"]
    spec["preferred"] = {
        variant: preferred_for_answer(spec["candidate_a"], spec["candidate_b"], spec["answers"][variant])
        for variant in spec["answers"]
    }
    return spec


BUILDERS = {
    "attribute": (build_attribute_triplet, "a_is_to", flip_attribute_ab),
    "presence": (build_presence_triplet, "a_is_no", flip_presence_ab),
    "spatial": (build_spatial_triplet, "a_is_no", flip_spatial_ab),
}

PREFIX = {"attribute": "attr", "presence": "pres", "spatial": "spat"}


def generate_factor_specs(factor: str, num_triplets: int, master_seed: int) -> list[dict[str, Any]]:
    if factor not in BUILDERS:
        raise ValueError("unknown factor: %s" % factor)
    builder, flag_key, flip_fn = BUILDERS[factor]
    rng = random.Random(int(master_seed))
    prefix = PREFIX[factor]
    specs = []
    i = 0
    attempts = 0
    max_attempts = max(1000, num_triplets * 50)
    while i < num_triplets:
        attempts += 1
        if attempts > max_attempts:
            raise RuntimeError("failed to build %d %s specs after %d attempts" % (num_triplets, factor, attempts))
        try:
            spec = builder(i, rng, prefix=prefix)
        except RuntimeError:
            continue
        specs.append(spec)
        i += 1
    ensure_ab_shuffle(specs, flag_key, flip_fn)
    return specs
