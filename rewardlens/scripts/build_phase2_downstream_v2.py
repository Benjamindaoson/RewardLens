"""Phase II V2 physical-image downstream repair primitives."""

from __future__ import annotations

import hashlib
import os
from collections import defaultdict
from typing import Any

PHYSICAL_REPAIR_SALT = "RewardLens-Phase2-PhysicalRepair-v1"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def carrier_for(row: dict[str, Any]) -> str:
    factor = str(row.get("factor") or "")
    dataset = str(row.get("dataset") or "")
    if factor == "count":
        if dataset and dataset != "tallyqa":
            raise ValueError("Count replacement must be TallyQA")
        return "tallyqa"
    if factor not in {"attribute", "presence", "spatial"}:
        raise ValueError("unknown factor: %s" % factor)
    if dataset and dataset != "gqa":
        raise ValueError("%s replacement must be GQA" % factor)
    return "gqa"


def _physical_hash(row: dict[str, Any]) -> str:
    path = str(row.get("image_path") or "")
    if not path or not os.path.isfile(path):
        raise FileNotFoundError("image missing: %s" % path)
    return sha256_file(path)


def _repair_key(row: dict[str, Any], physical_sha256: str) -> str:
    factor = str(row["factor"])
    carrier = carrier_for(row)
    source_item_id = str(row.get("source_item_id") or row.get("item_id") or "")
    return hashlib.sha256(
        (
            PHYSICAL_REPAIR_SALT
            + "|"
            + factor
            + "|"
            + carrier
            + "|"
            + source_item_id
            + "|"
            + physical_sha256
        ).encode("utf-8")
    ).hexdigest()


def _hashes(rows: list[dict[str, Any]]) -> set[str]:
    return {_physical_hash(row) for row in rows}


def repair_downstream_rows(
    *,
    static_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    downstream_rows: list[dict[str, Any]],
    replacement_candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Repair only downstream rows colliding with the fixed static anchor."""
    static_hashes = _hashes(static_rows)
    audit_hashes = _hashes(audit_rows)
    if static_hashes & audit_hashes:
        raise ValueError("D_audit and D_static are not physically disjoint")

    downstream_hashes = [_physical_hash(row) for row in downstream_rows]
    audit_conflicts = [
        row["item_id"]
        for row, physical_sha256 in zip(downstream_rows, downstream_hashes)
        if physical_sha256 in audit_hashes
    ]
    if audit_conflicts:
        raise ValueError("original downstream overlaps D_audit: %s" % audit_conflicts[:3])

    conflict_indexes = [
        index
        for index, physical_sha256 in enumerate(downstream_hashes)
        if physical_sha256 in static_hashes
    ]
    retained_indexes = set(range(len(downstream_rows))) - set(conflict_indexes)
    selected_hashes = {downstream_hashes[index] for index in retained_indexes}

    candidates_by_group: dict[tuple[str, str], list[tuple[str, str, dict[str, Any]]]] = defaultdict(list)
    for row in replacement_candidates:
        physical_sha256 = _physical_hash(row)
        group = (str(row.get("factor") or ""), carrier_for(row))
        if physical_sha256 in static_hashes or physical_sha256 in audit_hashes or physical_sha256 in selected_hashes:
            continue
        candidates_by_group[group].append((_repair_key(row, physical_sha256), physical_sha256, row))
    for candidates in candidates_by_group.values():
        candidates.sort(key=lambda item: item[0])

    repaired = list(downstream_rows)
    replacements = []
    for index in conflict_indexes:
        original = downstream_rows[index]
        group = (str(original.get("factor") or ""), carrier_for(original))
        candidates = candidates_by_group.get(group) or []
        chosen = None
        while candidates:
            _key, physical_sha256, candidate = candidates.pop(0)
            if physical_sha256 not in selected_hashes:
                chosen = (physical_sha256, candidate)
                break
        if chosen is None:
            raise ValueError("insufficient eligible replacements for %s/%s" % group)
        physical_sha256, candidate = chosen
        repaired[index] = candidate
        selected_hashes.add(physical_sha256)
        replacements.append(
            {
                "original_item_id": original.get("item_id"),
                "replacement_item_id": candidate.get("item_id"),
                "source_item_id": candidate.get("source_item_id") or candidate.get("item_id"),
                "factor": group[0],
                "carrier": group[1],
                "replacement_physical_image_sha256": physical_sha256,
            }
        )

    repaired_hashes = _hashes(repaired)
    physical_intersections = {
        "audit_static": len(audit_hashes & static_hashes),
        "audit_downstream": len(audit_hashes & repaired_hashes),
        "static_downstream": len(static_hashes & repaired_hashes),
    }
    if any(physical_intersections.values()):
        raise ValueError("V2 physical disjointness failed: %s" % physical_intersections)
    return repaired, {
        "n_original": len(downstream_rows),
        "n_replaced": len(replacements),
        "replacements": replacements,
        "physical_intersections": physical_intersections,
    }
