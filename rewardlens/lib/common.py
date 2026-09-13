from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from PIL import Image, ImageDraw, ImageFont


VARIANTS = ("base", "relevant", "irrelevant")
CLEVR_LEFT = (-0.6563112735748291, -0.7544902563095093, 0.0)
CLEVR_RIGHT = (0.6563112735748291, 0.7544902563095093, 0.0)
REL_EPS = 0.2


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, payload: Any) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def write_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
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


def make_object(
    role: str,
    shape: str,
    color: str,
    size: str,
    material: str,
    slot: list[float],
    rotation: float,
    object_id: str,
) -> dict[str, Any]:
    return {
        "role": role,
        "object_id": object_id,
        "shape": shape,
        "color": color,
        "size": size,
        "material": material,
        "x": float(slot[0]),
        "y": float(slot[1]),
        "rotation": float(rotation),
    }


def preferred_for_answer(candidate_a: str, candidate_b: str, answer: str) -> str:
    if candidate_a == answer:
        return "A"
    if candidate_b == answer:
        return "B"
    raise ValueError("answer %s is not among candidates %s/%s" % (answer, candidate_a, candidate_b))


def ensure_ab_shuffle(specs: list[dict[str, Any]], flag_key: str, flip_fn) -> None:
    flags = [bool(spec[flag_key]) for spec in specs]
    if flags and (all(flags) or not any(flags)):
        flip_fn(specs[-1])


def vec_dot(a: list[float], b: tuple[float, float, float] | list[float]) -> float:
    return float(a[0]) * float(b[0]) + float(a[1]) * float(b[1]) + float(a[2]) * float(b[2])


def is_left_of(obj_a: dict[str, Any], obj_b: dict[str, Any], left_vec=CLEVR_LEFT, eps: float = REL_EPS) -> bool:
    diff = [
        float(obj_a["x"]) - float(obj_b["x"]),
        float(obj_a["y"]) - float(obj_b["y"]),
        0.0,
    ]
    return vec_dot(diff, left_vec) > eps


def is_right_of(obj_a: dict[str, Any], obj_b: dict[str, Any], right_vec=CLEVR_RIGHT, eps: float = REL_EPS) -> bool:
    diff = [
        float(obj_a["x"]) - float(obj_b["x"]),
        float(obj_a["y"]) - float(obj_b["y"]),
        0.0,
    ]
    return vec_dot(diff, right_vec) > eps


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


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ):
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_contact_sheet(output_dir: str, spec: dict[str, Any], manifest: dict[str, Any]) -> str:
    images = []
    for variant in VARIANTS:
        path = os.path.join(output_dir, "images", "%s_%s.png" % (spec["triplet_id"], variant))
        images.append(Image.open(path).convert("RGB"))

    pad = 16
    header_h = 128
    label_h = 58
    img_w, _img_h = images[0].size
    width = pad + 3 * (img_w + pad)
    height = pad + header_h + label_h + images[0].size[1] + pad
    canvas = Image.new("RGB", (width, height), (24, 24, 28))
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(22)
    body_font = load_font(16)
    small_font = load_font(15)

    header_lines = [
        "%s   |   factor=%s   |   seed=%s" % (spec["triplet_id"], spec["factor"], spec["seed"]),
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
        ("Base", "pref=%s" % manifest["base"]["preferred"]),
        ("Relevant", "pref=%s" % manifest["relevant"]["preferred"]),
        ("Irrelevant", "pref=%s" % manifest["irrelevant"]["preferred"]),
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
