#!/usr/bin/env python3
"""Write SHA256SUMS.txt for a directory tree."""

from __future__ import annotations

import argparse
import hashlib
import os


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = os.path.abspath(args.root)
    lines = []
    for dirpath, _dirs, files in os.walk(root):
        for name in sorted(files):
            if name == "SHA256SUMS.txt":
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace("\\", "/")
            lines.append("%s  %s" % (sha256_file(path), rel))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + ("\n" if lines else ""))
    print("WROTE", args.out, "n", len(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
