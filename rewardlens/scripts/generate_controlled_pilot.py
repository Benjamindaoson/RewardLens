#!/usr/bin/env python3
"""Generate a 10-triplet controlled pilot for attribute / presence / spatial."""

from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.common import (  # noqa: E402
    build_run_config,
    detect_roots,
    load_json,
    make_contact_sheet,
    resolve_path,
    run_blender,
    write_json,
    write_jsonl,
)
from lib.factor_specs import generate_factor_specs, spec_to_manifest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--factor", required=True, choices=["attribute", "presence", "spatial"])
    parser.add_argument("--config", default=None)
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.config is None:
        args.config = os.path.join(ROOT, "configs", "%s_pilot_v1.json" % args.factor)
    config_path = os.path.abspath(args.config)
    config = load_json(config_path)
    factor = config.get("factor", args.factor)
    project_root, rewardlens_root = detect_roots(config_path)
    output_dir = resolve_path(project_root, config["paths"]["output_dir"])
    blender = resolve_path(project_root, config["paths"]["blender"])
    renderer = os.path.join(rewardlens_root, "renderers", "clevr_controlled_renderer.py")

    for sub in ("images", "scenes", "manifests", "contact_sheets"):
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)

    specs = generate_factor_specs(factor, int(config["num_triplets"]), int(config["master_seed"]))
    manifests = [spec_to_manifest(spec) for spec in specs]
    specs_path = os.path.join(output_dir, "triplet_specs.json")
    run_config_path = os.path.join(output_dir, "run_config.json")
    write_json(
        specs_path,
        {"name": config["name"], "factor": factor, "master_seed": config["master_seed"], "triplets": specs},
    )
    write_json(run_config_path, build_run_config(config, project_root, output_dir, skip_existing=not args.no_resume))
    for manifest in manifests:
        write_json(os.path.join(output_dir, "manifests", "%s.json" % manifest["triplet_id"]), manifest)
    write_jsonl(os.path.join(output_dir, "pilot_manifest.jsonl"), manifests)

    print("Wrote %d %s specs to %s" % (len(specs), factor, specs_path), flush=True)
    print("Questions:", [spec["question"] for spec in specs], flush=True)
    print("A/B:", [(spec["candidate_a"], spec["candidate_b"]) for spec in specs], flush=True)

    if not args.skip_render:
        if not os.path.isfile(blender):
            raise FileNotFoundError(blender)
        run_blender(blender, renderer, run_config_path, specs_path)
        for spec, manifest in zip(specs, manifests):
            path = make_contact_sheet(output_dir, spec, manifest)
            print("WROTE CONTACT SHEET:", path, flush=True)

    print("%s_PILOT_GENERATE_OK" % factor.upper(), flush=True)
    print("OUTPUT_DIR:", output_dir, flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("GENERATE_FAILED:", exc, file=sys.stderr, flush=True)
        raise
