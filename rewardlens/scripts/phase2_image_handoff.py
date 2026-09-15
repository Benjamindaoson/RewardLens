#!/usr/bin/env python3
"""Raw-byte GQA/VG/COCO image delivery handoff; no network or image decoding."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, TextIO


def _format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    value = max(0, int(round(seconds)))
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "%02d:%02d:%02d" % (hours, minutes, seconds) if hours else "%02d:%02d" % (minutes, seconds)


def _progress_stats(completed: int, total: int, elapsed: float) -> tuple[float, float, float | None]:
    if total == 0:
        return 100.0, 0.0, None
    percent = min(100.0, max(0.0, 100.0 * completed / total))
    rate = completed / elapsed if elapsed > 0 else 0.0
    eta = (total - completed) / rate if rate > 0 else None
    return percent, rate, eta


def _display_width(value: str) -> int:
    return sum(2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1 for char in value)


def _truncate(value: str, width: int) -> str:
    if _display_width(value) <= width:
        return value
    suffix = "..."
    kept = ""
    for char in value:
        if _display_width(kept + char + suffix) > width:
            break
        kept += char
    return kept + suffix


class ProgressUI:
    """TTY renderer with a throttled plain-text fallback. Receipt data never enters it."""

    def __init__(
        self,
        mode: str,
        *,
        source: str,
        target: int,
        stream: TextIO | None = None,
        is_tty: bool | None = None,
        clock: Any = time.monotonic,
        title: str = "Phase II Image Handoff",
    ) -> None:
        if mode not in {"auto", "on", "off"}:
            raise ValueError("progress mode must be auto, on, or off")
        self.stream = stream or sys.stderr
        self.clock = clock
        self.source = source
        self.target = target
        self.title = title
        self.is_tty = bool(sys.stdout.isatty()) if is_tty is None else bool(is_tty)
        self.enabled = mode != "off"
        self.tty = self.enabled and self.is_tty
        self.plain = self.enabled and not self.tty
        encoding = (getattr(self.stream, "encoding", None) or "").lower()
        self.unicode = self.tty and ("utf" in encoding or not encoding)
        self.colors = self.tty and not os.environ.get("NO_COLOR")
        self.started = self.clock()
        self.rows: list[dict[str, Any]] = []
        self.last_lines = 0
        self.last_plain_percent = -5.0
        self.last_plain_time = self.started
        self.cursor_hidden = False
        if self.tty:
            self._write("\x1b[?25l")
            self.cursor_hidden = True

    def _write(self, value: str) -> None:
        self.stream.write(value)
        self.stream.flush()

    def _color(self, value: str, code: str) -> str:
        return "\x1b[%sm%s\x1b[0m" % (code, value) if self.colors else value

    def _glyphs(self) -> dict[str, str]:
        if not self.unicode:
            return {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|", "fill": "#", "empty": "-"}
        return {
            "tl": chr(0x256D), "tr": chr(0x256E), "bl": chr(0x2570), "br": chr(0x256F),
            "h": chr(0x2500), "v": chr(0x2502), "fill": chr(0x2588), "empty": chr(0x2591),
        }

    def _width(self) -> int:
        return max(56, shutil.get_terminal_size(fallback=(100, 24)).columns)

    def _box(self, title: str, rows: list[tuple[str, str]]) -> list[str]:
        glyph = self._glyphs()
        inner = self._width() - 2
        title_text = _truncate(" " + title + " ", inner - 2)
        top = glyph["tl"] + glyph["h"] + title_text.center(inner - 2, glyph["h"]) + glyph["h"] + glyph["tr"]
        lines = [top]
        for label, value in rows:
            content = _truncate(" %s %-9s %s" % (glyph["v"], label, value), inner)
            lines.append(content.ljust(inner + 1) + glyph["v"])
        lines.append(glyph["bl"] + glyph["h"] * inner + glyph["br"])
        return lines

    def stage(self, name: str, total: int, *, detail: str = "") -> None:
        if not self.enabled:
            return
        now = self.clock()
        if self.rows:
            self.rows[-1]["complete"] = True
        self.rows.append(
            {
                "name": name, "total": max(0, total), "completed": 0, "detail": detail,
                "counters": "", "started": now, "complete": total == 0,
            }
        )
        self._render(force=True)

    def update(self, completed: int, *, detail: str = "", counters: str = "", force: bool = False) -> None:
        if not self.enabled or not self.rows:
            return
        row = self.rows[-1]
        row["completed"] = min(max(0, completed), row["total"])
        if detail:
            row["detail"] = detail
        if counters:
            row["counters"] = counters
        if row["completed"] >= row["total"]:
            row["complete"] = True
        self._render(force=force or row["complete"])

    def _should_plain_log(self, row: dict[str, Any], now: float, force: bool) -> bool:
        percent, _rate, _eta = _progress_stats(row["completed"], row["total"], now - row["started"])
        if force or row["complete"]:
            return True
        return percent >= self.last_plain_percent + 5.0 or now - self.last_plain_time >= 30.0

    def _render(self, *, force: bool = False) -> None:
        if not self.enabled or not self.rows:
            return
        now = self.clock()
        row = self.rows[-1]
        if self.plain:
            if not self._should_plain_log(row, now, force):
                return
            percent, rate, eta = _progress_stats(row["completed"], row["total"], now - row["started"])
            suffix = (" " + row["counters"]) if row["counters"] else ""
            self._write(
                "[%s] %d/%d %.1f%% %.1f img/s ETA=%s%s\n"
                % (row["name"].lower(), row["completed"], row["total"], percent, rate, _format_duration(eta), suffix)
            )
            self.last_plain_percent = percent
            self.last_plain_time = now
            return
        if not self.tty:
            return

        glyph = self._glyphs()
        width = self._width()
        bar_width = max(16, min(54, width - 28))
        lines = self._box(
            "RewardLens %s %s" % (chr(0x00B7), self.title),
            [("Source", self.source), ("Target", "%d required images" % self.target)],
        )
        for index, item in enumerate(self.rows, 1):
            elapsed = now - item["started"]
            percent, rate, eta = _progress_stats(item["completed"], item["total"], elapsed)
            filled = int(round(bar_width * percent / 100.0))
            bar = glyph["fill"] * filled + glyph["empty"] * (bar_width - filled)
            label = "%d. %s" % (index, item["name"])
            lines.append("")
            lines.append("  " + self._color(_truncate(label, width - 4), "36" if not item["complete"] else "32"))
            lines.append("  %s %5.1f%%" % (bar, percent))
            metric = "%d / %d" % (item["completed"], item["total"])
            if rate:
                metric += "    %.1f img/s" % rate
            metric += "    elapsed %s" % _format_duration(elapsed)
            if eta is not None and not item["complete"]:
                metric += "    ETA %s" % _format_duration(eta)
            if item["counters"]:
                metric += "    " + item["counters"]
            elif item["detail"]:
                metric += "    " + _truncate(item["detail"], max(12, width - len(metric) - 4))
            lines.append("  " + _truncate(metric, width - 4))
            if item["complete"]:
                lines.append("  " + self._color("PASS", "32"))
        self._replace_lines(lines)

    def _replace_lines(self, lines: list[str], *, title_color: str | None = None) -> None:
        if self.last_lines:
            self._write("\x1b[%dA" % self.last_lines)
        rendered = []
        width = self._width()
        for number, line in enumerate(lines):
            line = _truncate(line, width)
            if number == 0 and title_color:
                line = self._color(line, title_color)
            rendered.append("\x1b[2K" + line)
        self._write("\n".join(rendered) + "\n")
        self.last_lines = len(rendered)

    def finish(self, *, required: int, found: int, missing: int, receipt: str, status: str = "PASS") -> None:
        if not self.enabled:
            return
        runtime = self.clock() - self.started
        if self.plain:
            self._write(
                "[%s] Required=%d Found=%d Missing=%d Receipt=%s Runtime=%s\n"
                % (status, required, found, missing, receipt, _format_duration(runtime))
            )
            return
        if not self.tty:
            return
        title = status if not missing else "PASS WITH EXPECTED MISSING"
        lines = self._box(
            title,
            [
                ("Required", str(required)), ("Found", str(found)), ("Missing", str(missing)),
                ("Raw bytes", "preserved"), ("Receipt", Path(receipt).name),
                ("Runtime", _format_duration(runtime)),
            ],
        )
        self._replace_lines(lines, title_color="32" if not missing else "33")
        self.last_lines = 0
        self._write("\n")

    def fail(self, message: str) -> None:
        if self.plain:
            self._write("[FAIL] %s\n" % message)
        elif self.tty:
            self._replace_lines(self._box("FAIL", [("Reason", message)]), title_color="31")
            self.last_lines = 0
            self._write("\n")

    def close(self) -> None:
        if self.cursor_hidden:
            self._write("\x1b[?25h")
            self.cursor_hidden = False


def _required(path: str) -> list[str]:
    with open(path, encoding="utf-8") as handle:
        ids = [line.strip() for line in handle if line.strip()]
    if len(ids) != len(set(ids)) or not all(value.isdigit() for value in ids):
        raise ValueError("required image IDs must be unique numeric lines")
    return sorted(ids, key=int)


def _expected_filenames(required_path: str, filename_manifest: str | None = None) -> tuple[list[str], dict[str, str]]:
    ids = _required(required_path)
    if filename_manifest is None:
        return ids, {image_id: "%s.jpg" % image_id for image_id in ids}
    with open(filename_manifest, encoding="utf-8") as handle:
        payload = json.load(handle)
    mapping = payload.get("expected_canonical_filename_by_id")
    if not isinstance(mapping, dict) or set(mapping) != set(ids):
        raise ValueError("filename manifest must map exactly the required IDs")
    names = {str(image_id): str(filename) for image_id, filename in mapping.items()}
    if len(set(names.values())) != len(names) or any(
        Path(filename).name != filename or Path(filename).suffix.lower() != ".jpg"
        for filename in names.values()
    ):
        raise ValueError("filename manifest contains invalid canonical JPEG names")
    return ids, names


def _sha(path: Path) -> str:
    with path.open("rb") as handle:
        return _sha_stream(handle)


def _sha_stream(handle: Any) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()

def _zip_index(path: str, progress: ProgressUI | None = None) -> dict[str, zipfile.ZipInfo]:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if progress:
            progress.stage("Scan archive", len(infos), detail=Path(path).name)
        matches = defaultdict(list)
        for number, info in enumerate(infos, 1):
            filename = os.path.basename(info.filename)
            _stem, ext = os.path.splitext(filename)
            if not info.is_dir() and ext.lower() == ".jpg":
                matches[filename].append(info)
            if progress and (number == len(infos) or number % 256 == 0):
                progress.update(number, detail=Path(path).name)
        duplicate = sorted(key for key, rows in matches.items() if len(rows) > 1)
        if duplicate:
            raise ValueError("ambiguous image filenames in ZIP: %s" % duplicate[:5])
        return {key: rows[0] for key, rows in matches.items()}


def _dir_index(path: str, progress: ProgressUI | None = None) -> dict[str, Path]:
    candidates = list(Path(path).rglob("*"))
    if progress:
        progress.stage("Discover files", len(candidates), detail=Path(path).name)
    matches = defaultdict(list)
    for number, candidate in enumerate(candidates, 1):
        if candidate.is_file() and candidate.suffix.lower() == ".jpg":
            matches[candidate.name].append(candidate)
        if progress and (number == len(candidates) or number % 256 == 0):
            progress.update(number, detail=Path(path).name)
    duplicate = sorted(key for key, rows in matches.items() if len(rows) > 1)
    if duplicate:
        raise ValueError("ambiguous image filenames in directory: %s" % duplicate[:5])
    return {key: rows[0] for key, rows in matches.items()}


def materialize_required_images(
    required_path: str, source: str, output_dir: str, *, filename_manifest: str | None = None,
    progress: ProgressUI | None = None,
) -> dict:
    """Copy requested raw bytes from an official ZIP or extracted directory."""
    required, filenames = _expected_filenames(required_path, filename_manifest)
    source_path = Path(source)
    if source_path.suffix.lower() == ".zip" and not zipfile.is_zipfile(source):
        raise ValueError("invalid ZIP archive: %s" % source)
    if not zipfile.is_zipfile(source) and not source_path.is_dir():
        raise ValueError("source must be a ZIP archive or image directory: %s" % source)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    found, missing = [], []
    if zipfile.is_zipfile(source):
        if progress:
            progress.stage("Validate archive integrity", 1, detail=Path(source).name)
        with zipfile.ZipFile(source) as archive:
            corrupt_member = archive.testzip()
        if corrupt_member:
            raise ValueError("corrupt ZIP member: %s" % corrupt_member)
        if progress:
            progress.update(1, counters="PASS")
        index = _zip_index(source, progress)
        matched = [image_id for image_id in required if filenames[image_id] in index]
        missing = [image_id for image_id in required if filenames[image_id] not in index]
        if progress:
            progress.stage("Match frozen IDs", len(required), detail=Path(source).name)
            for number in range(1, len(required) + 1):
                if number == len(required) or number % 256 == 0:
                    progress.update(number, counters="matched %d" % len(matched))
            progress.stage("Extract raw bytes", len(matched), detail=Path(source).name)
        with zipfile.ZipFile(source) as archive:
            for number, image_id in enumerate(matched, 1):
                info = index[filenames[image_id]]
                dest = out / filenames[image_id]
                if dest.exists():
                    with archive.open(info) as raw:
                        if _sha(dest) != _sha_stream(raw):
                            raise ValueError("existing output differs: %s" % dest)
                else:
                    with archive.open(info) as raw, dest.open("xb") as handle:
                        shutil.copyfileobj(raw, handle, length=1024 * 1024)
                found.append(image_id)
                if progress and (number == len(matched) or number % 8 == 0):
                    progress.update(number, detail=filenames[image_id])
    else:
        index = _dir_index(source, progress)
        if progress:
            progress.stage("Match frozen IDs", len(required), detail=Path(source).name)
        matched = []
        for number, image_id in enumerate(required, 1):
            if filenames[image_id] in index:
                matched.append(image_id)
            else:
                missing.append(image_id)
            if progress and (number == len(required) or number % 256 == 0):
                progress.update(number, counters="matched %d" % len(matched))
        if progress:
            progress.stage("Extract raw bytes", len(matched), detail=Path(source).name)
        for number, image_id in enumerate(matched, 1):
            raw = index[filenames[image_id]]
            dest = out / filenames[image_id]
            if dest.exists() and _sha(dest) != _sha(raw):
                raise ValueError("existing output differs: %s" % dest)
            if not dest.exists():
                shutil.copyfile(raw, dest)
            found.append(image_id)
            if progress and (number == len(matched) or number % 8 == 0):
                progress.update(number, detail=filenames[image_id])
    receipt = verify_required_images(required_path, str(out), filename_manifest=filename_manifest, progress=progress)
    receipt.update({"source": source, "output_dir": str(out)})
    return receipt

def verify_required_images(
    required_path: str, image_dir: str, *, filename_manifest: str | None = None,
    progress: ProgressUI | None = None,
) -> dict:
    required, filenames = _expected_filenames(required_path, filename_manifest)
    root = Path(image_dir)
    index = _dir_index(image_dir, progress)
    found, missing = [], []
    if progress:
        progress.stage("Match frozen IDs", len(required), detail=Path(image_dir).name)
    for number, image_id in enumerate(required, 1):
        (found if filenames[image_id] in index else missing).append(image_id)
        if progress and (number == len(required) or number % 256 == 0):
            progress.update(number, counters="found %d missing %d" % (len(found), len(missing)))
    manifest = []
    by_hash = defaultdict(list)
    if progress:
        progress.stage("SHA-256 raw bytes", len(found), detail=Path(image_dir).name)
    for number, image_id in enumerate(found, 1):
        path = index[filenames[image_id]]
        digest = _sha(path)
        manifest.append({
            "image_id": image_id, "canonical_filename": filenames[image_id],
            "relative_path": str(path.relative_to(root)), "bytes": path.stat().st_size,
            "sha256": digest,
        })
        by_hash[digest].append(image_id)
        if progress and (number == len(found) or number % 8 == 0):
            duplicates = sum(1 for values in by_hash.values() if len(values) > 1)
            progress.update(number, detail=filenames[image_id], counters="duplicate groups %d" % duplicates)
    unexpected_names = set(filenames.values())
    unexpected = sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and (path.suffix.lower() != ".jpg" or path.name not in unexpected_names)
    )
    return {
        "required_ids": required,
        "found_ids": found,
        "missing_ids": missing,
        "duplicate_physical_sha256": {key: value for key, value in sorted(by_hash.items()) if len(value) > 1},
        "unexpected_files": unexpected,
        "byte_hash_manifest": manifest,
    }


def _write_receipt(path: str, result: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(temporary, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("extract", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--required-ids", required=True)
        p.add_argument("--images", required=True)
        p.add_argument("--receipt", required=True)
        p.add_argument("--filename-manifest")
        p.add_argument("--progress", choices=("auto", "on", "off"), default="auto")
        if name == "extract":
            p.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    ui = ProgressUI(
        args.progress, source=Path(args.images).name, target=len(_required(args.required_ids)),
        title="Physical Image Verification" if args.command == "verify" else "Phase II Image Handoff",
    )
    try:
        result = materialize_required_images(
            args.required_ids, args.images, args.output_dir,
            filename_manifest=args.filename_manifest, progress=ui,
        ) if args.command == "extract" else verify_required_images(
            args.required_ids, args.images,
            filename_manifest=args.filename_manifest, progress=ui,
        )
        ui.stage("Publish receipt", 1, detail=Path(args.receipt).name)
        _write_receipt(args.receipt, result)
        ui.update(1, counters="atomic write PASS")
        ui.finish(
            required=len(result["required_ids"]), found=len(result["found_ids"]),
            missing=len(result["missing_ids"]), receipt=args.receipt, status="PASS",
        )
    except KeyboardInterrupt:
        ui.fail("INTERRUPTED")
        raise
    except Exception as error:
        ui.fail(str(error))
        raise
    finally:
        ui.close()
    print(json.dumps({
        "required": len(result["required_ids"]), "found": len(result["found_ids"]),
        "missing": len(result["missing_ids"]), "receipt": args.receipt,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
