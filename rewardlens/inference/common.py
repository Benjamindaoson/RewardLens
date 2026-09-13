"""Shared inference I/O: resume, append JSONL, failure logs."""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from typing import Any, Callable, Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from lib.jsonl_io import append_jsonl, completed_ids, read_jsonl, repair_jsonl  # noqa: E402


def judgment_record(
    *,
    item_id: str,
    triplet_id: str,
    factor: str,
    variant: str,
    model_id: str,
    raw_output: str | None,
    parsed_preference: str | None,
    score_a: float | None = None,
    score_b: float | None = None,
    margin: float | None = None,
    latency_ms: float | None = None,
    status: str = "ok",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "item_id": item_id,
        "triplet_id": triplet_id,
        "factor": factor,
        "variant": variant,
        "model_id": model_id,
        "raw_output": raw_output,
        "parsed_preference": parsed_preference,
        "score_a": score_a,
        "score_b": score_b,
        "margin": margin,
        "latency_ms": latency_ms,
        "status": status,
    }
    if extra:
        row.update(extra)
    return row


def load_items(path: str) -> list[dict[str, Any]]:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    if path.endswith(".jsonl"):
        return read_jsonl(path)
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("items", "records", "triplets"):
            if key in payload:
                return list(payload[key])
    raise ValueError("unsupported manifest: %s" % path)


def resolve_image_path(item: dict[str, Any], images_root: str | None = None) -> str:
    """Return an existing path when possible. Remap Windows/GPU bundle absolute paths by basename."""
    path = str(item.get("image_path") or item.get("image") or "")
    if not path:
        return path
    candidates: list[str] = [path]
    base = os.path.basename(path.replace("\\", "/"))
    roots = []
    if images_root:
        roots.append(images_root)
    here = os.path.abspath(os.path.dirname(__file__))
    project = os.path.dirname(os.path.dirname(here))
    roots.extend(
        [
            os.path.join(project, "datasets", "gqa", "images"),
            os.path.join(project, "datasets", "tallyqa", "images"),
            os.path.join(project, "datasets", "tallyqa", "coco"),
            os.path.join(project, "gqa_images"),
            os.path.join(os.getcwd(), "gqa_images"),
            os.path.join(os.getcwd(), "images"),
        ]
    )
    for root in roots:
        candidates.append(os.path.join(root, base))
        if not os.path.isabs(path):
            candidates.append(os.path.join(root, path.replace("/", os.sep)))
    seen = set()
    for cand in candidates:
        norm = os.path.normpath(cand)
        if norm in seen:
            continue
        seen.add(norm)
        if os.path.isfile(norm):
            return norm
    if images_root and not os.path.isabs(path):
        return os.path.normpath(os.path.join(images_root, path))
    return path


def run_items(
    *,
    items: Iterable[dict[str, Any]],
    adapter,
    model_id: str,
    out_jsonl: str,
    fail_jsonl: str,
    parse_fn: Callable[[str], str | None],
    skip_completed: bool = True,
    flush_every: int = 1,
    images_root: str | None = None,
) -> dict[str, Any]:
    if skip_completed and os.path.isfile(out_jsonl):
        repair_jsonl(out_jsonl)
    done = completed_ids(out_jsonl) if skip_completed else set()
    n_skip = 0
    n_ok = 0
    n_fail = 0
    pending_flush = 0
    os.makedirs(os.path.dirname(os.path.abspath(out_jsonl)) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(fail_jsonl)) or ".", exist_ok=True)

    for item in items:
        item_id = str(item.get("item_id") or "%s:%s" % (item.get("triplet_id"), item.get("variant")))
        if item_id in done:
            n_skip += 1
            continue
        t0 = time.perf_counter()
        status = "ok"
        raw = None
        parsed = None
        scores = {"score_a": None, "score_b": None, "margin": None}
        try:
            image_path = resolve_image_path(item, images_root)
            if image_path and not os.path.isfile(image_path):
                raise FileNotFoundError("image missing: %s" % image_path)
            cands = item.get("candidates")
            if isinstance(cands, list):
                n_expected = int(item.get("n_pool") or item.get("n_candidates") or 0)
                n_filled = sum(1 for c in cands if (c.get("text") if isinstance(c, dict) else c))
                if n_expected and n_filled != n_expected:
                    raise ValueError("invalid candidate count: got %d expected %d" % (n_filled, n_expected))
            prepared = adapter.prepare_inputs(
                image_path=image_path,
                question=item.get("question"),
                candidate_a=item.get("candidate_a"),
                candidate_b=item.get("candidate_b"),
            )
            result = adapter.judge(prepared)
            if isinstance(result, dict):
                raw = result.get("raw_output")
                scores["score_a"] = result.get("score_a")
                scores["score_b"] = result.get("score_b")
                scores["margin"] = result.get("margin")
                if result.get("parsed_preference"):
                    parsed = result.get("parsed_preference")
            else:
                raw = str(result)
            if parsed is None:
                parsed = parse_fn(raw or "")
            if parsed not in {"A", "B"}:
                status = "parse_error"
        except MemoryError as exc:
            status = "oom"
            raw = str(exc)
        except TimeoutError as exc:
            status = "timeout"
            raw = str(exc)
        except Exception as exc:
            message = str(exc).lower()
            status = "oom" if "out of memory" in message or "oom" in message else "error"
            raw = "%s\n%s" % (exc, traceback.format_exc())
        latency_ms = (time.perf_counter() - t0) * 1000.0
        row = judgment_record(
            item_id=item_id,
            triplet_id=str(item.get("triplet_id", "")),
            factor=str(item.get("factor", "")),
            variant=str(item.get("variant", "")),
            model_id=model_id,
            raw_output=raw,
            parsed_preference=parsed if status == "ok" else None,
            score_a=scores["score_a"],
            score_b=scores["score_b"],
            margin=scores["margin"],
            latency_ms=latency_ms,
            status=status,
            extra={
                "candidate_a": item.get("candidate_a"),
                "candidate_b": item.get("candidate_b"),
            },
        )
        append_jsonl(out_jsonl, row, flush=True)
        done.add(item_id)
        pending_flush += 1
        if status != "ok":
            n_fail += 1
            append_jsonl(
                fail_jsonl,
                {
                    "item_id": item_id,
                    "status": status,
                    "error": raw,
                    "model_id": model_id,
                },
                flush=True,
            )
            if status == "parse_error":
                append_jsonl(fail_jsonl.replace("failures.jsonl", "parse_failures.jsonl"), row, flush=True)
            if status == "oom":
                append_jsonl(fail_jsonl.replace("failures.jsonl", "oom.jsonl"), row, flush=True)
            if status == "timeout":
                append_jsonl(fail_jsonl.replace("failures.jsonl", "timeout.jsonl"), row, flush=True)
        else:
            n_ok += 1
        if pending_flush >= flush_every:
            pending_flush = 0
    return {"ok": n_ok, "failed": n_fail, "skipped": n_skip, "out_jsonl": out_jsonl}
