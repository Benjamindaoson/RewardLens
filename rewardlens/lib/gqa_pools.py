"""Fill frozen N=8 GQA downstream pools from structured sources. Never invent natural language."""

from __future__ import annotations

from collections import Counter
from typing import Any

COLOR_PALETTE = [
    "white",
    "black",
    "red",
    "green",
    "blue",
    "yellow",
    "brown",
    "gray",
    "pink",
    "orange",
    "purple",
]
SPATIAL_WORDS = [
    "yes",
    "no",
    "left",
    "right",
    "to the left of",
    "to the right of",
    "in front of",
    "behind",
    "above",
    "below",
]
N_POOL = 8


def _norm(text: str) -> str:
    return str(text).strip().lower()


def scene_object_names(scene: dict[str, Any] | None) -> list[str]:
    if not scene:
        return []
    objects = scene.get("objects") or {}
    names = []
    if isinstance(objects, dict):
        values = objects.values()
    elif isinstance(objects, list):
        values = objects
    else:
        return []
    for obj in values:
        if not isinstance(obj, dict):
            continue
        name = obj.get("name") or obj.get("label")
        if name:
            names.append(str(name))
        for attr in obj.get("attributes") or []:
            names.append(str(attr))
    return names


def structured_candidates(
    factor: str,
    row: dict[str, Any],
    *,
    vocab: list[str],
    scene: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    gold = str(row.get("answer") or row.get("gold_answer") or "")
    out: list[dict[str, Any]] = [{"text": gold, "source": "gold", "type": "gold"}]
    seen = {_norm(gold)}

    def add(text: str | None, source: str, typ: str) -> None:
        if text is None:
            return
        t = str(text).strip()
        if not t or _norm(t) in seen:
            return
        seen.add(_norm(t))
        out.append({"text": t, "source": source, "type": typ})

    hard = row.get("hard_negative")
    add(hard, "structured_hard_negative", str(row.get("hard_negative_type") or "hard_negative"))

    if factor == "count":
        al = gold.strip()
        if al.isdigit():
            n = int(al)
            for val, typ in (
                (str(n + 1), "count_plus_1"),
                (str(max(0, n - 1)), "count_minus_1"),
                (str(n + 2), "count_plus_2"),
                (str(max(0, n - 2)), "count_minus_2"),
                (str(n + 3), "count_plus_3"),
                ("0", "count_zero"),
                ("1", "count_one"),
                ("10", "count_ten"),
            ):
                add(val, "structured_hard_negative", typ)
        for i in range(0, 12):
            add(str(i), "factor_vocab", "count_domain")

    elif factor == "attribute":
        for color in COLOR_PALETTE:
            add(color, "factor_vocab", "attribute_palette")
        for name in scene_object_names(scene):
            add(name, "scene_graph", "scene_attribute_or_name")

    elif factor == "spatial":
        for word in SPATIAL_WORDS:
            add(word, "factor_vocab", "spatial_relation")

    elif factor == "presence":
        flip = "no" if gold.lower() == "yes" else "yes" if gold.lower() == "no" else None
        add(flip, "structured_hard_negative", "yes_no_flip")
        for name in scene_object_names(scene):
            add(name, "scene_graph", "scene_object")

    for text in vocab:
        if len(out) >= N_POOL:
            break
        add(text, "same_factor_answer_vocab", "corpus_alternative")

    return out[:N_POOL]


def factor_vocab(rows: list[dict[str, Any]], factor: str) -> list[str]:
    counts = Counter(str(r.get("answer") or "") for r in rows if r.get("factor") == factor and r.get("answer"))
    return [text for text, _n in counts.most_common()]
