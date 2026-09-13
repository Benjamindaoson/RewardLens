#!/usr/bin/env python3
"""Assemble a GPU-only transfer bundle. No Blender, no CLEVR source, no paper plots."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)

CODE_GLOBS = [
    "inference",
    "models",
    "lib",
    "stats",
    "configs",
    "scripts",
]


def copy_tree(src: str, dst: str) -> None:
    if os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif os.path.isfile(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=os.path.join(PROJECT, "gpu_bundle"))
    parser.add_argument("--manifest-root", default=None)
    parser.add_argument("--copy-manifest-images", action="store_true", default=True)
    parser.add_argument("--no-copy-images", action="store_true")
    parser.add_argument("--include-scale-images", action="store_true")
    return parser.parse_args()


def copy_manifests(src_dir: str, dst_dir: str) -> list[str]:
    os.makedirs(dst_dir, exist_ok=True)
    copied = []
    if not os.path.isdir(src_dir):
        return copied
    for name in os.listdir(src_dir):
        if name.endswith((".jsonl", ".json", ".csv")):
            shutil.copy2(os.path.join(src_dir, name), os.path.join(dst_dir, name))
            copied.append(name)
    return copied


def collect_image_paths(manifest_dir: str) -> list[str]:
    paths = []
    if not os.path.isdir(manifest_dir):
        return paths
    for name in os.listdir(manifest_dir):
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(manifest_dir, name), "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                rec = json.loads(line)
                p = rec.get("image_path")
                if p:
                    paths.append(p)
    return paths


def main() -> int:
    args = parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    code_dst = os.path.join(out, "rewardlens")
    os.makedirs(code_dst, exist_ok=True)
    for rel in CODE_GLOBS:
        copy_tree(os.path.join(ROOT, rel), os.path.join(code_dst, rel))

    manifest_src = args.manifest_root or os.environ.get("REWARDLENS_BUNDLE_MANIFEST_ROOT")
    if not manifest_src:
        fast = os.path.join(PROJECT, "outputs", "fast_track_audit_v1")
        signal = os.path.join(PROJECT, "outputs", "signal_gate_v1")
        manifest_src = fast if os.path.isfile(os.path.join(fast, "audit_manifest.jsonl")) else signal
    manifest_dst = os.path.join(out, "manifests")
    copied_manifests = copy_manifests(manifest_src, manifest_dst)
    factors_src = os.path.join(manifest_src, "factors")
    if os.path.isdir(factors_src):
        copy_tree(factors_src, os.path.join(manifest_dst, "factors"))
        copied_manifests.append("factors/")
    signal_src = os.path.join(PROJECT, "outputs", "signal_gate_v1")
    if os.path.isdir(signal_src) and os.path.abspath(manifest_src) != os.path.abspath(signal_src):
        copied_manifests.extend(copy_manifests(signal_src, os.path.join(manifest_dst, "signal_gate_v1")))

    gqa_derived = os.path.join(PROJECT, "datasets", "gqa", "derived")
    if os.path.isdir(gqa_derived):
        for name in (
            "gqa_static_manifest.jsonl",
            "gqa_downstream_manifest.jsonl",
            "gqa_downstream_partial_manifest.jsonl",
            "gqa_factor_mapping_report.json",
            "static_image_ids.json",
            "downstream_image_ids.json",
            "split_validation.json",
            "required_gqa_image_ids.json",
            "gqa_image_inventory.json",
            "candidate_pool_qc.json",
        ):
            src = os.path.join(gqa_derived, name)
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(manifest_dst, name))
                copied_manifests.append(name)

    for extra_dir, sub in (
        (os.path.join(PROJECT, "datasets", "tallyqa", "derived"), "tallyqa"),
        (os.path.join(PROJECT, "datasets", "processed", "fast_eval"), "fast_eval"),
    ):
        copied_manifests.extend(copy_manifests(extra_dir, os.path.join(manifest_dst, sub)))

    img_dst = os.path.join(out, "images")
    os.makedirs(img_dst, exist_ok=True)
    n_images = 0
    image_paths = collect_image_paths(manifest_src)
    image_paths.extend(collect_image_paths(os.path.join(PROJECT, "datasets", "processed", "fast_eval")))
    image_paths.extend(collect_image_paths(os.path.join(PROJECT, "datasets", "tallyqa", "derived")))
    image_paths.extend(collect_image_paths(os.path.join(PROJECT, "datasets", "gqa", "derived")))
    if args.include_scale_images or (not args.no_copy_images and args.copy_manifest_images):
        if not image_paths:
            for factor_dir in ("count_pilot_v1", "attribute_pilot_v1", "presence_pilot_v1", "spatial_pilot_v1"):
                img_dir = os.path.join(PROJECT, "outputs", factor_dir, "images")
                if os.path.isdir(img_dir):
                    for name in os.listdir(img_dir):
                        if name.endswith(".png"):
                            image_paths.append(os.path.join(img_dir, name))
        for path in sorted(set(image_paths)):
            if not os.path.isfile(path):
                continue
            rel = os.path.relpath(path, PROJECT)
            dest = os.path.join(img_dst, rel.replace("\\", "/").replace("/", os.sep))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(path, dest)
            n_images += 1

    gqa_img = os.path.join(PROJECT, "datasets", "gqa", "images")
    if os.path.isdir(gqa_img) and not args.no_copy_images:
        dest_gqa = os.path.join(out, "gqa_images")
        os.makedirs(dest_gqa, exist_ok=True)
        for name in os.listdir(gqa_img):
            if name.lower().endswith((".jpg", ".png")):
                shutil.copy2(os.path.join(gqa_img, name), os.path.join(dest_gqa, name))
                n_images += 1

    for extra in (
        os.path.join(ROOT, "docs", "GPU_RUNBOOK.md"),
        os.path.join(PROJECT, "GPU_RUNBOOK.md"),
        os.path.join(PROJECT, "cloud_staging"),
    ):
        if os.path.isfile(extra):
            shutil.copy2(extra, os.path.join(out, os.path.basename(extra)))
        elif os.path.isdir(extra):
            copy_tree(extra, os.path.join(out, os.path.basename(extra)))

    req = """# GPU host. Do not install flash-attn / bitsandbytes unless a registry flag requires it.
torch>=2.4
transformers>=4.51
accelerate
pillow
pyyaml
sentencepiece
protobuf
"""
    with open(os.path.join(out, "requirements-gpu.txt"), "w", encoding="utf-8") as handle:
        handle.write(req)
    lock_src = os.path.join(ROOT, "requirements-gpu.lock")
    if os.path.isfile(lock_src):
        shutil.copy2(lock_src, os.path.join(out, "requirements-gpu.lock"))
    meta = {
        "out": out,
        "n_images": n_images,
        "manifest_root": manifest_src,
        "manifests": copied_manifests,
        "excluded": ["Blender", "CLEVR source", "plots", "GQA raw zips", "paper figures"],
    }
    with open(os.path.join(out, "bundle_meta.json"), "w", encoding="utf-8") as handle:
        json.dump(meta, handle, indent=2)
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
