"""GQA factor mapping from functional programs, types, and scene graphs.

Keyword fallback is last resort and is recorded as mapping_source=keyword.
"""

from __future__ import annotations

import json
import os
import random
import re
from collections import Counter
from typing import Any

COUNT_OPS = {"count"}
ATTR_OPS = {
    "queryattr",
    "verifyattr",
    "chooseattr",
    "sameattr",
    "differentattr",
    "filter",
    "querycolor",
    "choosecolor",
    "verifycolor",
    "querymaterial",
    "verifymaterial",
}
SPATIAL_OPS = {"relate", "verifyrel", "chooserel", "filterrel"}
PRESENCE_OPS = {"exist"}
LEFT_RIGHT = {"left", "right", "to the left of", "to the right of", "left of", "right of"}
ATTR_DETAILED = {
    "attrcolor",
    "attrmaterial",
    "chooseattr",
    "verifyattr",
    "queryattr",
    "sameattr",
    "diffattr",
}
COUNT_DETAILED = {"count"}
PRESENCE_DETAILED = {"exist", "existattr", "existrel", "existattrrel", "logical"}
SPATIAL_DETAILED = {"rel", "verifyrel", "chooserel", "existrel"}

COLOR_PALETTE = ["white", "black", "red", "green", "blue", "yellow", "brown", "gray", "grey", "pink", "orange", "purple"]
SPATIAL_INVERSE = {
    "left": "right",
    "right": "left",
    "to the left of": "to the right of",
    "to the right of": "to the left of",
    "left of": "right of",
    "right of": "left of",
    "yes": "no",
    "no": "yes",
}


def _ops_from_semantic(program: Any) -> list[dict[str, str]]:
    steps = []
    if not isinstance(program, list):
        return steps
    for step in program:
        if not isinstance(step, dict):
            continue
        op = str(step.get("operation") or step.get("func") or step.get("op") or "").lower()
        arg = str(step.get("argument") or step.get("arg") or "")
        steps.append({"operation": op, "argument": arg})
    return steps


def _types(item: dict[str, Any]) -> dict[str, str]:
    types = item.get("types") or {}
    return {
        "structural": str(types.get("structural") or "").lower(),
        "semantic": str(types.get("semantic") or "").lower(),
        "detailed": str(types.get("detailed") or "").lower(),
    }


def map_factor(item: dict[str, Any]) -> dict[str, Any] | None:
    question = str(item.get("question") or "")
    answer = str(item.get("answer") or "").strip()
    answer_l = answer.lower()
    types = _types(item)
    steps = _ops_from_semantic(item.get("semantic") or item.get("program") or [])
    ops = [s["operation"] for s in steps]
    args = " ".join(s["argument"].lower() for s in steps)
    source = []

    detailed = types["detailed"]
    semantic = types["semantic"]
    structural = types["structural"]

    if "count" in ops or detailed == "count" or (answer.isdigit() and semantic in {"obj", "object", "attr", "global"} and "how many" in question.lower()):
        if "count" in ops or detailed == "count" or (answer.isdigit() and structural == "query"):
            source.append("program:count" if "count" in ops else "types:count-or-numeric")
            return {
                "factor": "count",
                "mapping_source": "+".join(source) or "types+answer",
                "confidence": "high" if "count" in ops or detailed == "count" else "medium",
            }

    if detailed in ATTR_DETAILED or semantic in {"attr", "attribute"} or any(op in ATTR_OPS for op in ops):
        if "how many" in question.lower() or "count" in ops:
            return {
                "factor": "count",
                "mapping_source": "count-overrides-attr",
                "confidence": "high",
            }
        if any(tok in args for tok in LEFT_RIGHT) and semantic in {"rel", "relation"}:
            pass
        else:
            source.append("types:attr" if semantic in {"attr", "attribute"} or detailed in ATTR_DETAILED else "program:attr")
            return {
                "factor": "attribute",
                "mapping_source": "+".join(source),
                "confidence": "high",
            }

    spatial_arg = any(tok in args for tok in LEFT_RIGHT)
    spatial_op = any(op in SPATIAL_OPS for op in ops)
    if spatial_op and spatial_arg:
        return {
            "factor": "spatial",
            "mapping_source": "program:relate+left/right",
            "confidence": "high",
        }
    if detailed in SPATIAL_DETAILED and spatial_arg:
        return {
            "factor": "spatial",
            "mapping_source": "types:rel+left/right",
            "confidence": "high",
        }

    if any(op in PRESENCE_OPS for op in ops) or detailed in PRESENCE_DETAILED:
        if answer_l in {"yes", "no"}:
            if spatial_arg:
                return {
                    "factor": "spatial",
                    "mapping_source": "exist+spatial-rel",
                    "confidence": "medium",
                }
            return {
                "factor": "presence",
                "mapping_source": "program:exist" if "exist" in ops else "types:exist",
                "confidence": "high" if "exist" in ops else "medium",
            }

    q = question.lower()
    if answer.isdigit() and "how many" in q:
        return {"factor": "count", "mapping_source": "keyword", "confidence": "low"}
    if q.startswith("is there") or q.startswith("are there"):
        return {"factor": "presence", "mapping_source": "keyword", "confidence": "low"}
    if any(tok in q for tok in ("left of", "right of", "to the left", "to the right")):
        return {"factor": "spatial", "mapping_source": "keyword", "confidence": "low"}
    if "what color" in q or "what material" in q:
        return {"factor": "attribute", "mapping_source": "keyword", "confidence": "low"}
    return None


def structured_hard_negative(factor: str, answer: str, item: dict[str, Any] | None = None, scene: dict[str, Any] | None = None) -> dict[str, Any]:
    a = answer.strip()
    al = a.lower()
    item = item or {}
    if factor == "count" and al.isdigit():
        n = int(al)
        plus = str(n + 1)
        minus = str(max(0, n - 1))
        chosen = plus if plus != a else minus
        return {
            "hard_negative": chosen,
            "hard_negative_type": "count_plus_minus_1",
            "count_plus": plus,
            "count_minus": minus if minus != a else None,
        }
    if factor == "presence" and al in {"yes", "no"}:
        return {"hard_negative": "no" if al == "yes" else "yes", "hard_negative_type": "yes_no_flip"}
    if factor == "spatial":
        inv = SPATIAL_INVERSE.get(al)
        if inv:
            return {"hard_negative": inv, "hard_negative_type": "spatial_inverse"}
        args = " ".join(
            str(step.get("argument") or "")
            for step in (item.get("semantic") or [])
            if isinstance(step, dict)
        ).lower()
        if "left" in args and al in {"yes", "no"}:
            return {"hard_negative": "no" if al == "yes" else "yes", "hard_negative_type": "spatial_verify_flip"}
        return {"hard_negative": None, "hard_negative_type": "unresolved"}
    if factor == "attribute":
        substitute = None
        if scene:
            substitute = _attribute_from_scene(item, scene, al)
        if substitute is None:
            if al in COLOR_PALETTE:
                others = [c for c in COLOR_PALETTE if c != al]
                substitute = others[0]
                return {
                    "hard_negative": substitute,
                    "hard_negative_type": "attribute_palette_substitution",
                    "note": "palette fallback; prefer scene-graph attribute when available",
                }
        if substitute:
            return {"hard_negative": substitute, "hard_negative_type": "attribute_scene_substitution"}
        return {"hard_negative": None, "hard_negative_type": "unresolved"}
    return {"hard_negative": None, "hard_negative_type": "unresolved"}


def _attribute_from_scene(item: dict[str, Any], scene: dict[str, Any], gold: str) -> str | None:
    objects = scene.get("objects") or {}
    if not isinstance(objects, dict):
        return None
    annotations = ((item.get("annotations") or {}).get("question") or {})
    obj_ids = list(annotations.values()) if isinstance(annotations, dict) else []
    candidates = []
    for oid in obj_ids:
        obj = objects.get(str(oid)) or objects.get(oid)
        if not obj:
            continue
        for attr in obj.get("attributes") or []:
            if str(attr).lower() != gold:
                candidates.append(str(attr))
    if candidates:
        return candidates[0]
    for obj in objects.values():
        for attr in obj.get("attributes") or []:
            if str(attr).lower() != gold:
                candidates.append(str(attr))
    return candidates[0] if candidates else None


def load_questions_file(path: str) -> dict[str, dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and "questions" in payload:
        payload = payload["questions"]
    if isinstance(payload, list):
        out = {}
        for item in payload:
            qid = str(item.get("questionId") or item.get("question_id") or item.get("id"))
            out[qid] = item
        return out
    return {str(k): v for k, v in payload.items()}


def find_gqa_question_files(gqa_dir: str) -> list[str]:
    hits = []
    for root, _dirs, files in os.walk(gqa_dir):
        for name in files:
            low = name.lower()
            if "question" in low and low.endswith(".json") and "test" not in low:
                if "balanced" in low or "all" in low or low.endswith("questions.json"):
                    hits.append(os.path.join(root, name))
    preferred = [p for p in hits if "balanced" in os.path.basename(p).lower() and "train" in os.path.basename(p).lower()]
    preferred += [p for p in hits if "balanced" in os.path.basename(p).lower() and "val" in os.path.basename(p).lower()]
    if preferred:
        return preferred
    return sorted(hits)


def find_scene_graph_files(gqa_dir: str) -> list[str]:
    hits = []
    for root, _dirs, files in os.walk(gqa_dir):
        for name in files:
            if "scenegraph" in name.lower().replace("_", "") and name.endswith(".json"):
                hits.append(os.path.join(root, name))
    return sorted(hits)


def load_scene_graphs(paths: list[str]) -> dict[str, Any]:
    graphs: dict[str, Any] = {}
    for path in paths:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            graphs.update({str(k): v for k, v in payload.items()})
    return graphs


def map_corpus(
    questions: dict[str, dict[str, Any]],
    scenes: dict[str, Any] | None = None,
    *,
    split_name: str = "unknown",
    max_items: int = 0,
    seed: int = 20260912,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scenes = scenes or {}
    mapped = []
    counts: Counter[str] = Counter()
    sources: Counter[str] = Counter()
    unmapped = 0
    keyword_n = 0
    for i, (qid, item) in enumerate(questions.items()):
        if max_items and i >= max_items:
            break
        if not isinstance(item, dict):
            unmapped += 1
            continue
        item = dict(item)
        item.setdefault("questionId", qid)
        mapped_factor = map_factor(item)
        if mapped_factor is None:
            unmapped += 1
            continue
        image_id = str(item.get("imageId") or item.get("image_id") or "")
        scene = scenes.get(image_id)
        hn = structured_hard_negative(mapped_factor["factor"], str(item.get("answer") or ""), item, scene)
        row = {
            "question_id": str(qid),
            "image_id": image_id,
            "split": split_name,
            "question": item.get("question"),
            "answer": item.get("answer"),
            "full_answer": item.get("fullAnswer"),
            "types": item.get("types"),
            "factor": mapped_factor["factor"],
            "mapping_source": mapped_factor["mapping_source"],
            "mapping_confidence": mapped_factor["confidence"],
            **hn,
        }
        mapped.append(row)
        counts[row["factor"]] += 1
        sources[row["mapping_source"]] += 1
        if row["mapping_source"] == "keyword":
            keyword_n += 1

    rng = random.Random(seed)
    qc_samples = {}
    by_factor: dict[str, list[dict[str, Any]]] = {}
    for row in mapped:
        by_factor.setdefault(row["factor"], []).append(row)
    for factor, rows in by_factor.items():
        high = [r for r in rows if r["mapping_confidence"] == "high"]
        pool = high or rows
        rng.shuffle(pool)
        qc_samples[factor] = [
            {
                "question_id": r["question_id"],
                "image_id": r["image_id"],
                "question": r["question"],
                "answer": r["answer"],
                "factor": r["factor"],
                "mapping_source": r["mapping_source"],
                "hard_negative": r.get("hard_negative"),
            }
            for r in pool[:50]
        ]

    report = {
        "n_questions_seen": min(len(questions), max_items) if max_items else len(questions),
        "n_mapped": len(mapped),
        "n_unmapped": unmapped,
        "counts": dict(counts),
        "mapping_sources": dict(sources),
        "keyword_fallback_n": keyword_n,
        "human_qc_candidates": qc_samples,
    }
    return mapped, report
