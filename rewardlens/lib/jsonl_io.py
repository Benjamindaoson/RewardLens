from __future__ import annotations

import json
import os
from typing import Any, Iterable


def read_jsonl(path: str, recover_partial: bool = True) -> list[dict[str, Any]]:
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                if not recover_partial:
                    raise
                continue
    return rows


def write_jsonl(path: str, rows: Iterable[dict[str, Any]]) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def append_jsonl(path: str, row: dict[str, Any], flush: bool = True) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True) + "\n")
        if flush:
            handle.flush()
            os.fsync(handle.fileno())


def repair_jsonl(path: str) -> int:
    """Drop a truncated last line so append resume cannot concatenate into garbage."""
    if not os.path.isfile(path):
        return 0
    rows = read_jsonl(path, recover_partial=True)
    write_jsonl(path, rows)
    return len(rows)


def completed_ids(path: str, key: str = "item_id") -> set[str]:
    ids: set[str] = set()
    for row in read_jsonl(path):
        value = row.get(key)
        if value is not None:
            ids.add(str(value))
    return ids
