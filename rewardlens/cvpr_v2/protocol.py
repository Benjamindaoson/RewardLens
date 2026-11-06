"""Strict, model-agnostic validation of RewardLens-CVPR observation rows.

Inputs are *predictions* from an external inference job, never fabricated by this module.
The validator checks record consistency; it cannot establish that visual edits are
perceptually valid. Those require independent semantic/human validation receipts.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

VARIANTS = ("base", "relevant", "irrelevant")
LABELS = {"A", "B"}
PREDICTIONS = LABELS | {"ABSTAIN"}
SPLITS = {"development", "test"}
REQUIRED = (
    "model_id", "model_family", "triplet_id", "source_id", "split",
    "domain", "factor", "shift_type", "edit_direction", "variant",
    "gold", "prediction", "image_id", "question", "candidate_a",
    "candidate_b", "semantic_validation_passed",
)


class ProtocolError(ValueError):
    """A record violates the frozen audit protocol."""


def _nonempty(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ProtocolError(f"{key} must be a nonempty string: {row!r}")
    return value


def validate_records(raw_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return validated rows; reject incomplete or inconsistent triplets.

    Reuses the *same* visual triplet across models, but never allows a source
    image to appear in both development and test splits. Deliberately does not
    deduplicate or silently drop malformed observations.
    """
    rows = list(raw_rows)
    if not rows:
        raise ProtocolError("no observation records")
    by_model_triplet: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    source_splits: dict[str, str] = {}
    image_splits: dict[str, str] = {}
    dataset_contracts: dict[tuple[str, str], tuple[Any, ...]] = {}
    model_families: dict[str, str] = {}

    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ProtocolError(f"record {index} is not an object")
        for key in REQUIRED:
            if key == "semantic_validation_passed":
                if row.get(key) is not True:
                    raise ProtocolError(f"record {index}: semantic validation receipt required")
            else:
                _nonempty(row, key)
        if row["split"] not in SPLITS:
            raise ProtocolError(f"record {index}: split must be development or test")
        if row["variant"] not in VARIANTS:
            raise ProtocolError(f"record {index}: invalid variant {row['variant']}")
        if row["gold"] not in LABELS or row["prediction"] not in PREDICTIONS:
            raise ProtocolError(f"record {index}: invalid gold/prediction")
        if row["candidate_a"].strip() == row["candidate_b"].strip():
            raise ProtocolError(f"record {index}: indistinguishable candidates")

        source = row["source_id"]
        split = row["split"]
        image = row["image_id"]
        if source in source_splits and source_splits[source] != split:
            raise ProtocolError(f"source_id leakage across development/test: {source}")
        source_splits[source] = split
        if image in image_splits and image_splits[image] != split:
            raise ProtocolError(f"image_id leakage across development/test: {image}")
        image_splits[image] = split
        model = row["model_id"]
        family = row["model_family"]
        if model in model_families and model_families[model] != family:
            raise ProtocolError(f"model_family changes for {model}")
        model_families[model] = family

        k = model, row["triplet_id"]
        variant = row["variant"]
        if variant in by_model_triplet[k]:
            raise ProtocolError(f"duplicate model/triplet/variant: {k}, {variant}")
        by_model_triplet[k][variant] = row

        # Gold labels, images, candidate content and metadata must be exactly
        # identical across models for the *same* underlying triplet.
        dk = row["triplet_id"], variant
        signature = tuple(row[field] for field in (
            "source_id", "split", "domain", "factor", "shift_type",
            "edit_direction", "gold", "image_id", "question",
            "candidate_a", "candidate_b",
        ))
        if dk in dataset_contracts and dataset_contracts[dk] != signature:
            raise ProtocolError(f"dataset changes between models: {dk}")
        dataset_contracts[dk] = signature

    for (model, tid), variants in by_model_triplet.items():
        if set(variants) != set(VARIANTS):
            raise ProtocolError(f"incomplete triplet for {model}/{tid}: {sorted(variants)}")
        b, r, i = (variants[v] for v in VARIANTS)
        fixed_fields = (
            "source_id", "split", "domain", "factor", "shift_type",
            "edit_direction", "question", "candidate_a", "candidate_b",
        )
        for field in fixed_fields:
            if not (b[field] == r[field] == i[field]):
                raise ProtocolError(f"changed {field} within {model}/{tid}")
        if b["gold"] == r["gold"] or b["gold"] != i["gold"]:
            raise ProtocolError(f"relevant/irrelevant gold contract broken: {model}/{tid}")
        if len({b["image_id"], r["image_id"], i["image_id"]}) != 3:
            raise ProtocolError(f"all three variants need distinct image_id: {model}/{tid}")
    return rows


def assemble_triplets(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, dict[str, Any]]]:
    """Requires a previously validated sequence."""
    out: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        out[(row["model_id"], row["triplet_id"])][row["variant"]] = row
    return dict(out)
