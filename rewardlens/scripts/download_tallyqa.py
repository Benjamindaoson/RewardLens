#!/usr/bin/env python3
"""Download TallyQA annotation zip only. Resume-capable. No full image dump."""

from __future__ import annotations

import argparse
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts.download_gqa import download_file  # noqa: E402

URL = "https://github.com/manoja328/tallyqa/raw/master/tallyqa.zip"
DEFAULT_DIR = os.path.join(PROJECT, "datasets", "tallyqa")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=DEFAULT_DIR)
    parser.add_argument("--no-extract", action="store_true")
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    dest = os.path.join(args.out_dir, "tallyqa.zip")
    download_file(URL, dest)
    if not args.no_extract:
        extract_dir = os.path.join(args.out_dir, "annotations")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(dest, "r") as zf:
            bad = zf.testzip()
            if bad:
                raise RuntimeError("zip integrity failed: %s" % bad)
            zf.extractall(extract_dir)
            print("EXTRACT_OK", extract_dir, "files", zf.namelist(), flush=True)
    print("TALLYQA_ANNOTATIONS_OK", dest, "size", os.path.getsize(dest), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
