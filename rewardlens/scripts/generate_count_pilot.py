#!/usr/bin/env python3
"""Generate COUNT PILOT V1: 10 controlled count intervention triplets."""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from copy import deepcopy
from typing import Any

from PIL import Image, ImageDraw, ImageFont


VARIANTS = ("base", "relevant", "irrelevant")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=True) + "\n")


def detect_roots(config_path: str) -> tuple[str, str]:
    config_path = os.path.abspath(config_path)
    rewardlens_root = os.path.dirname(os.path.dirname(config_path))
    project_root = os.path.dirname(rewardlens_root)
    return project_root, rewardlens_root


def resolve_path(project_root: str, maybe_relative: str) -> str:
    if os.path.isabs(maybe_relative):
        return os.path.normpath(maybe_relative)
    return os.path.normpath(os.path.join(project_root, maybe_relative))


def matching_contract() -> dict[str, Any]:
    return {
        "same_camera": True,
        "same_lighting": True,
        "same_render_seed": True,
        "same_base_objects": True,
        "same_intervention_position": True,
        "same_intervention_shape": True,
        "same_intervention_size": True,
        "same_intervention_material": True,
        "same_intervention_rotation": True,
        "only_semantic_difference": "intervention color changes target membership",
    }


def object_attrs(
    rng: random.Random,
    color: str,
    slot: list[float],
    role: str,
    shapes: list[str],
    sizes: list[str],
    materials: list[str],
) -> dict[str, Any]:
    return {
        "role": role,
        "shape": rng.choice(shapes),
        "color": color,
        "size": rng.choice(sizes),
        "material": rng.choice(materials),
        "x": float(slot[0]),
        "y": float(slot[1]),
        "rotation": float(rng.uniform(0.0, 360.0)),
    }


def preferred_from_candidates(candidate_a: str, candidate_b: str, count: int) -> str:
    count_s = str(count)
    if candidate_a == count_s:
        return "A"
    if candidate_b == count_s:
        return "B"
    raise ValueError("count %s is not among candidates %s/%s" % (count, candidate_a, candidate_b))


def build_triplet(
    index: int,
    rng: random.Random,
    config: dict[str, Any],
    base_count: int,
    target_color: str,
    force_a_is_plus_one: bool | None = None,
) -> dict[str, Any]:
    triplet_id = "count_%06d" % index
    render_seed = rng.randint(1, 10**9)
    colors = list(config["colors"])
    shapes = list(config["shapes"])
    sizes = list(config["sizes"])
    materials = list(config["materials"])
    slots = [list(slot) for slot in config["safe_slots"]]
    other_colors = [c for c in colors if c != target_color]
    irrelevant_color = rng.choice(other_colors)
    n_distractors = rng.randint(config["num_distractors_min"], config["num_distractors_max"])

    front_y_max = float(config["intervention_front_y_max"])
    front_slots = [s for s in slots if s[1] < front_y_max]
    if not front_slots:
        raise RuntimeError("no front slots available for intervention placement")
    intervention_slot = list(rng.choice(front_slots))
    remaining = [s for s in slots if not (s[0] == intervention_slot[0] and s[1] == intervention_slot[1])]
    rng.shuffle(remaining)
    needed = base_count + n_distractors
    if needed > len(remaining):
        raise RuntimeError("not enough safe slots for triplet %s" % triplet_id)

    target_slots = remaining[:base_count]
    distractor_slots = remaining[base_count:needed]

    base_objects: list[dict[str, Any]] = []
    for slot in target_slots:
        base_objects.append(object_attrs(rng, target_color, slot, "base", shapes, sizes, materials))
    for slot in distractor_slots:
        base_objects.append(
            object_attrs(rng, rng.choice(other_colors), slot, "base", shapes, sizes, materials)
        )

    intervention_common = {
        "role": "intervention",
        "shape": rng.choice(shapes),
        "size": rng.choice(sizes),
        "material": rng.choice(materials),
        "x": float(intervention_slot[0]),
        "y": float(intervention_slot[1]),
        "rotation": float(rng.uniform(0.0, 360.0)),
    }
    relevant_obj = dict(intervention_common)
    relevant_obj["color"] = target_color
    irrelevant_obj = dict(intervention_common)
    irrelevant_obj["color"] = irrelevant_color

    a_is_plus_one = rng.choice([True, False]) if force_a_is_plus_one is None else force_a_is_plus_one
    n = int(base_count)
    n1 = n + 1
    if a_is_plus_one:
        candidate_a, candidate_b = str(n1), str(n)
    else:
        candidate_a, candidate_b = str(n), str(n1)

    question = str(config["question_template"]).format(color=target_color)
    preferred = {
        "base": preferred_from_candidates(candidate_a, candidate_b, n),
        "relevant": preferred_from_candidates(candidate_a, candidate_b, n1),
        "irrelevant": preferred_from_candidates(candidate_a, candidate_b, n),
    }

    variants = {
        "base": {
            "objects": deepcopy(base_objects),
            "target_count": n,
        },
        "relevant": {
            "objects": deepcopy(base_objects) + [relevant_obj],
            "target_count": n1,
        },
        "irrelevant": {
            "objects": deepcopy(base_objects) + [irrelevant_obj],
            "target_count": n,
        },
    }

    return {
        "triplet_id": triplet_id,
        "factor": "count",
        "seed": render_seed,
        "render_seed": render_seed,
        "question": question,
        "candidate_a": candidate_a,
        "candidate_b": candidate_b,
        "a_is_plus_one": a_is_plus_one,
        "target_color": target_color,
        "base_count": n,
        "irrelevant_color": irrelevant_color,
        "preferred": preferred,
        "variants": variants,
        "intervention": {
            "x": intervention_common["x"],
            "y": intervention_common["y"],
            "shape": intervention_common["shape"],
            "size": intervention_common["size"],
            "material": intervention_common["material"],
            "rotation": intervention_common["rotation"],
            "relevant_color": target_color,
            "irrelevant_color": irrelevant_color,
        },
    }


def generate_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    rng = random.Random(int(config["master_seed"]))
    n = int(config["num_triplets"])
    base_counts = list(config["base_counts"])
    if len(base_counts) != n:
        tiled = (base_counts * ((n // max(len(base_counts), 1)) + 1))[:n]
        base_counts = tiled
    rng.shuffle(base_counts)

    colors = list(config["colors"])
    rng.shuffle(colors)
    target_colors = [colors[i % len(colors)] for i in range(n)]

    specs = []
    for i in range(n):
        specs.append(build_triplet(i, rng, config, base_counts[i], target_colors[i]))

    a_flags = [bool(spec["a_is_plus_one"]) for spec in specs]
    if all(a_flags) or not any(a_flags):
        flip_candidate_order(specs[-1])
    return specs


def flip_candidate_order(spec: dict[str, Any]) -> dict[str, Any]:
    spec["a_is_plus_one"] = not bool(spec["a_is_plus_one"])
    n = int(spec["base_count"])
    n1 = n + 1
    if spec["a_is_plus_one"]:
        spec["candidate_a"], spec["candidate_b"] = str(n1), str(n)
    else:
        spec["candidate_a"], spec["candidate_b"] = str(n), str(n1)
    spec["preferred"] = {
        "base": preferred_from_candidates(spec["candidate_a"], spec["candidate_b"], n),
        "relevant": preferred_from_candidates(spec["candidate_a"], spec["candidate_b"], n1),
        "irrelevant": preferred_from_candidates(spec["candidate_a"], spec["candidate_b"], n),
    }
    return spec


def spec_to_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    triplet_id = spec["triplet_id"]
    n = spec["base_count"]
    n1 = n + 1
    return {
        "triplet_id": triplet_id,
        "factor": "count",
        "seed": spec["seed"],
        "render_seed": spec["render_seed"],
        "question": spec["question"],
        "candidate_a": spec["candidate_a"],
        "candidate_b": spec["candidate_b"],
        "base": {
            "target_count": n,
            "preferred": spec["preferred"]["base"],
            "image": "images/%s_base.png" % triplet_id,
            "scene": "scenes/%s_base.json" % triplet_id,
        },
        "relevant": {
            "operation": "add_target",
            "target_count_before": n,
            "target_count_after": n1,
            "preferred": spec["preferred"]["relevant"],
            "image": "images/%s_relevant.png" % triplet_id,
            "scene": "scenes/%s_relevant.json" % triplet_id,
        },
        "irrelevant": {
            "operation": "add_non_target",
            "target_count_before": n,
            "target_count_after": n,
            "preferred": spec["preferred"]["irrelevant"],
            "image": "images/%s_irrelevant.png" % triplet_id,
            "scene": "scenes/%s_irrelevant.json" % triplet_id,
        },
        "target_color": spec["target_color"],
        "irrelevant_color": spec["irrelevant_color"],
        "matching_contract": matching_contract(),
    }


def load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_wh(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    return draw.textsize(text, font=font)


def make_contact_sheet(output_dir: str, spec: dict[str, Any], manifest: dict[str, Any]) -> str:
    images = []
    for variant in VARIANTS:
        path = os.path.join(output_dir, "images", "%s_%s.png" % (spec["triplet_id"], variant))
        images.append(Image.open(path).convert("RGB"))

    pad = 16
    header_h = 128
    label_h = 58
    img_w, img_h = images[0].size
    width = pad + 3 * (img_w + pad)
    height = pad + header_h + label_h + img_h + pad
    canvas = Image.new("RGB", (width, height), (24, 24, 28))
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(22)
    body_font = load_font(16)
    small_font = load_font(15)

    header_lines = [
        "%s   |   factor=count   |   seed=%s" % (spec["triplet_id"], spec["seed"]),
        spec["question"],
        "Candidate A = %s     Candidate B = %s" % (spec["candidate_a"], spec["candidate_b"]),
        "Expected preference:  Base=%s   Relevant=%s   Irrelevant=%s"
        % (
            manifest["base"]["preferred"],
            manifest["relevant"]["preferred"],
            manifest["irrelevant"]["preferred"],
        ),
    ]
    y = pad
    for i, line in enumerate(header_lines):
        font = title_font if i <= 1 else body_font
        draw.text((pad, y), line, fill=(245, 245, 245), font=font)
        y += 28 if i <= 1 else 22

    labels = [
        ("Base", "count=%s  pref=%s" % (manifest["base"]["target_count"], manifest["base"]["preferred"])),
        (
            "Relevant",
            "count=%s  pref=%s" % (manifest["relevant"]["target_count_after"], manifest["relevant"]["preferred"]),
        ),
        (
            "Irrelevant",
            "count=%s  pref=%s" % (manifest["irrelevant"]["target_count_after"], manifest["irrelevant"]["preferred"]),
        ),
    ]
    label_colors = [(236, 236, 236), (120, 210, 140), (140, 180, 230)]

    for i, image in enumerate(images):
        x = pad + i * (img_w + pad)
        top = pad + header_h
        draw.text((x, top), labels[i][0], fill=label_colors[i], font=title_font)
        draw.text((x, top + 26), labels[i][1], fill=(200, 200, 200), font=small_font)
        canvas.paste(image, (x, top + label_h))

    out_path = os.path.join(output_dir, "contact_sheets", "%s.png" % spec["triplet_id"])
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path)
    return out_path


def build_run_config(config: dict[str, Any], project_root: str, output_dir: str, skip_existing: bool) -> dict[str, Any]:
    paths = config["paths"]
    render = config["render"]
    return {
        "output_dir": output_dir,
        "clevr_image_generation": resolve_path(project_root, paths["clevr_image_generation"]),
        "base_scene_blendfile": resolve_path(project_root, paths["base_scene"]),
        "properties_json": resolve_path(project_root, paths["properties"]),
        "shape_dir": resolve_path(project_root, paths["shape_dir"]),
        "material_dir": resolve_path(project_root, paths["material_dir"]),
        "width": int(render["width"]),
        "height": int(render["height"]),
        "samples": int(render["samples"]),
        "tile_size": int(render["tile_size"]),
        "use_gpu": int(render["use_gpu"]),
        "skip_existing": bool(skip_existing),
    }


def run_blender(blender: str, renderer: str, run_config_path: str, specs_path: str) -> None:
    cmd = [
        blender,
        "--background",
        "--factory-startup",
        "--python",
        renderer,
        "--",
        "--run_config",
        run_config_path,
        "--specs_file",
        specs_path,
    ]
    print("LAUNCH:", " ".join(cmd), flush=True)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.run(cmd, env=env)
    if proc.returncode != 0:
        raise RuntimeError("Blender render failed with exit code %s" % proc.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate COUNT PILOT V1")
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "..", "configs", "count_pilot_v1.json"),
    )
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--no-resume", action="store_true", help="Re-render even if outputs already exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = os.path.abspath(args.config)
    config = load_json(config_path)
    project_root, rewardlens_root = detect_roots(config_path)
    output_dir = resolve_path(project_root, config["paths"]["output_dir"])
    blender = resolve_path(project_root, config["paths"]["blender"])
    renderer = os.path.join(rewardlens_root, "renderers", "clevr_count_renderer.py")

    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "scenes"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "manifests"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "contact_sheets"), exist_ok=True)

    specs = generate_specs(config)
    manifests = [spec_to_manifest(spec) for spec in specs]

    specs_path = os.path.join(output_dir, "triplet_specs.json")
    run_config_path = os.path.join(output_dir, "run_config.json")
    write_json(
        specs_path,
        {
            "name": config["name"],
            "master_seed": config["master_seed"],
            "triplets": specs,
        },
    )
    write_json(run_config_path, build_run_config(config, project_root, output_dir, skip_existing=not args.no_resume))

    for manifest in manifests:
        write_json(os.path.join(output_dir, "manifests", "%s.json" % manifest["triplet_id"]), manifest)
    write_jsonl(os.path.join(output_dir, "pilot_manifest.jsonl"), manifests)

    print("Wrote %d triplet specs to %s" % (len(specs), specs_path), flush=True)
    print("Count transitions:", [spec["base_count"] for spec in specs], flush=True)
    print("Target colors:", [spec["target_color"] for spec in specs], flush=True)
    print("A is n+1:", [spec["a_is_plus_one"] for spec in specs], flush=True)

    if not args.skip_render:
        if not os.path.isfile(blender):
            raise FileNotFoundError("Blender not found: %s" % blender)
        if not os.path.isfile(renderer):
            raise FileNotFoundError("Renderer not found: %s" % renderer)
        run_blender(blender, renderer, run_config_path, specs_path)
        for spec, manifest in zip(specs, manifests):
            path = make_contact_sheet(output_dir, spec, manifest)
            print("WROTE CONTACT SHEET:", path, flush=True)

    print("COUNT_PILOT_V1_GENERATE_OK", flush=True)
    print("OUTPUT_DIR:", output_dir, flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("COUNT_PILOT_V1_GENERATE_FAILED:", exc, file=sys.stderr, flush=True)
        raise
