#!/usr/bin/env python3
"""Download GQA questions, scene graphs, and optionally images. Resume-capable.

Does not download official precomputed ResNet/Faster-RCNN feature dumps.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(ROOT)
DEFAULT_DIR = os.path.join(PROJECT, "datasets", "gqa")

SOURCES = {
    "questions": {
        "url": "https://nlp.stanford.edu/data/gqa/questions1.2.zip",
        "filename": "questions1.2.zip",
        "extract_dir": "questions",
    },
    "scene_graphs": {
        "url": "https://nlp.stanford.edu/data/gqa/sceneGraphs.zip",
        "filename": "sceneGraphs.zip",
        "extract_dir": "sceneGraphs",
    },
    "images": {
        "url": "https://nlp.stanford.edu/data/gqa/images.zip",
        "filename": "images.zip",
        "extract_dir": "images",
    },
}


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, dest: str, retries: int = 8, expected_bytes: int | None = None) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    existing = os.path.getsize(dest) if os.path.isfile(dest) else 0
    if expected_bytes and existing >= expected_bytes:
        print("DOWNLOAD_SKIP_COMPLETE", dest, existing, flush=True)
        return
    if existing and not expected_bytes:
        # If a previous complete download exists, a Range request can 416.
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "RewardLens/gqa-downloader"})
            with urllib.request.urlopen(req, timeout=60) as response:
                total = int(response.headers.get("Content-Length") or 0)
            if total and existing >= total:
                print("DOWNLOAD_SKIP_COMPLETE", dest, existing, flush=True)
                return
        except Exception:
            pass
    headers = {"User-Agent": "RewardLens/gqa-downloader"}
    if existing:
        headers["Range"] = "bytes=%d-" % existing
    attempt = 0
    while attempt < retries:
        attempt += 1
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                mode = "ab" if existing and response.getcode() in (206, 200) and "Range" in headers else "wb"
                if response.getcode() == 200 and existing and "Range" not in response.headers:
                    mode = "wb"
                    existing = 0
                total = response.headers.get("Content-Length")
                print("DOWNLOAD", url, "mode", mode, "existing", existing, "content-length", total, flush=True)
                last = time.time()
                written = existing
                with open(dest, mode) as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        written += len(chunk)
                        now = time.time()
                        if now - last >= 5:
                            print("  bytes", written, flush=True)
                            last = now
            print("DOWNLOAD_OK", dest, "size", os.path.getsize(dest), flush=True)
            return
        except Exception as exc:
            print("DOWNLOAD_RETRY", attempt, url, exc, flush=True)
            time.sleep(min(30, 2 ** attempt))
            existing = os.path.getsize(dest) if os.path.isfile(dest) else 0
            headers = {"User-Agent": "RewardLens/gqa-downloader"}
            if existing:
                headers["Range"] = "bytes=%d-" % existing
    raise RuntimeError("failed to download %s" % url)


def extract_zip(zip_path: str, dest_dir: str) -> None:
    os.makedirs(dest_dir, exist_ok=True)
    print("EXTRACT", zip_path, "->", dest_dir, flush=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)
    print("EXTRACT_OK", dest_dir, flush=True)


def write_status(out_dir: str, payload: dict) -> None:
    path = os.path.join(out_dir, "download_status.json")
    import json

    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print("WROTE", path, flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=DEFAULT_DIR)
    parser.add_argument("--skip-images", action="store_true")
    parser.add_argument("--images-only", action="store_true")
    parser.add_argument("--only", choices=["questions", "scene_graphs", "images"], default=None)
    parser.add_argument("--no-extract", action="store_true")
    args = parser.parse_args()
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if args.only:
        wanted = [args.only]
    else:
        wanted = ["images"] if args.images_only else ["questions", "scene_graphs"]
        if not args.skip_images and not args.images_only:
            wanted.append("images")

    status = {"out_dir": out_dir, "files": {}, "note": "precomputed CNN features are intentionally not downloaded"}
    for key in wanted:
        spec = SOURCES[key]
        dest = os.path.join(out_dir, spec["filename"])
        try:
            download_file(spec["url"], dest)
            info = {
                "url": spec["url"],
                "path": dest,
                "bytes": os.path.getsize(dest),
                "sha256": sha256_file(dest),
                "status": "downloaded",
            }
            if not args.no_extract:
                extract_zip(dest, os.path.join(out_dir, spec["extract_dir"]))
                info["extracted_to"] = os.path.join(out_dir, spec["extract_dir"])
            status["files"][key] = info
        except Exception as exc:
            status["files"][key] = {"url": spec["url"], "status": "FAILED", "error": str(exc)}
            write_status(out_dir, status)
            print("FAILED", key, exc, file=sys.stderr, flush=True)
            return 1
    write_status(out_dir, status)
    print("GQA_DOWNLOAD_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
