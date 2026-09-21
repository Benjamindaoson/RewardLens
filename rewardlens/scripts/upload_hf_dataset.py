#!/usr/bin/env python3
"""Upload RewardLens data and large artifacts to a Hugging Face dataset repo."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "1")

from huggingface_hub import HfApi


ROOT = Path(__file__).resolve().parents[2]
PAYLOADS = (
    ("datasets", "datasets"),
    ("gpu_bundle", "gpu_bundle"),
    ("gpu_bundle_fast_v1", "gpu_bundle_fast_v1"),
    ("gpu_bundle_signal_v1", "gpu_bundle_signal_v1"),
    ("outputs", "outputs"),
    ("tools", "tools"),
    ("artifacts", "artifacts"),
    ("gpu_bundle_fast_v1.zip", "gpu_bundle_fast_v1.zip"),
)
IGNORE_PATTERNS = [".git/**", ".cache/**", "**/*.crdownload"]
PAYLOAD_NAMES = tuple(local_name for local_name, _ in PAYLOADS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-id", default="Benjamindaoson/RewardLens-data")
    parser.add_argument("--public", action="store_true", help="Create a public dataset repository.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", action="append", choices=PAYLOAD_NAMES, help="Upload only this payload; repeat to select several.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api = HfApi()
    payloads = tuple(item for item in PAYLOADS if not args.only or item[0] in args.only)
    print(f"HF_AUTHENTICATED_AS={api.whoami()['name']}")
    for local_name, remote_name in payloads:
        path = ROOT / local_name
        if not path.exists():
            raise FileNotFoundError(path)
        print(f"PLAN {path} -> {remote_name}")
    if args.dry_run:
        return 0
    api.create_repo(args.repo_id, repo_type="dataset", private=not args.public, exist_ok=True)
    for local_name, remote_name in payloads:
        path = ROOT / local_name
        print(f"UPLOAD {path} -> {remote_name}", flush=True)
        if path.is_dir():
            api.upload_folder(
                repo_id=args.repo_id,
                repo_type="dataset",
                folder_path=str(path),
                path_in_repo=remote_name,
                ignore_patterns=IGNORE_PATTERNS,
            )
        else:
            api.upload_file(
                repo_id=args.repo_id,
                repo_type="dataset",
                path_or_fileobj=str(path),
                path_in_repo=remote_name,
            )
    print(f"HF_DATASET_URL=https://huggingface.co/datasets/{args.repo_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
