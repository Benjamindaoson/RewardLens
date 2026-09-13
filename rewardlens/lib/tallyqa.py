"""TallyQA Count construction helpers. Numeric answers only. No fabricated questions."""

from __future__ import annotations

import hashlib
import os
import random
import re
from typing import Any

from .common import preferred_for_answer


def parse_int_answer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    text = str(value).strip().lower()
    if re.fullmatch(r"\d+", text):
        return int(text)
    return None


def image_key(row: dict[str, Any]) -> tuple[str, str, str]:
    """Return (source, source_id, relative_path)."""
    rel = str(row.get("image") or "").replace("\\", "/").lstrip("./")
    base = os.path.basename(rel)
    stem, ext = os.path.splitext(base)
    low = rel.lower()
    if "vg_100k" in low or rel.startswith("VG_"):
        return "vg", stem, rel
    if "train2014" in low or "val2014" in low or "coco" in low:
        split = "train2014" if "train2014" in low else "val2014" if "val2014" in low else "train2014"
        return "coco", stem, rel
    return "other", stem, rel


def split_bucket(image_id: str, seed: int = 20260912) -> str:
    digest = hashlib.sha256(("%s:%s" % (seed, image_id)).encode("utf-8")).hexdigest()
    return "static" if int(digest[:8], 16) % 2 == 0 else "downstream"


def hard_negative(gold: int) -> int:
    plus = gold + 1
    minus = gold - 1
    if minus >= 0:
        return plus
    return plus


def nearby_fallback(gold: int, used: set[int]) -> int | None:
    for delta in range(1, 16):
        for val in (gold - delta, gold + delta):
            if val >= 0 and val not in used:
                return val
    return None


def pairwise_candidates(gold: int, rng: random.Random) -> tuple[str, str, str, str]:
    hard = hard_negative(gold)
    gold_s, hard_s = str(gold), str(hard)
    if gold_s == hard_s:
        alt = nearby_fallback(gold, {gold})
        if alt is None:
            raise ValueError("cannot build hard negative for gold=%s" % gold)
        hard_s = str(alt)
    a_first = bool(rng.randrange(2))
    if a_first:
        ca, cb = gold_s, hard_s
    else:
        ca, cb = hard_s, gold_s
    pref = preferred_for_answer(ca, cb, gold_s)
    return ca, cb, pref, hard_s


def n8_pool(gold: int, rng: random.Random) -> tuple[list[dict[str, Any]], int]:
    texts = [gold]
    for delta in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        for val in (gold - delta, gold + delta):
            if val >= 0 and val not in texts:
                texts.append(val)
            if len(texts) >= 8:
                break
        if len(texts) >= 8:
            break
    texts = texts[:8]
    cands = [{"text": str(v), "source": "gold" if v == gold else "structured_count", "type": "gold" if v == gold else "near_count"} for v in texts]
    rng.shuffle(cands)
    gold_index = next(i for i, c in enumerate(cands) if c["text"] == str(gold))
    return cands, gold_index


def resolve_local_image(source: str, source_id: str, rel: str, *, gqa_images: str, tally_images: str, coco_images: str) -> str | None:
    candidates = []
    if source == "vg":
        candidates.append(os.path.join(gqa_images, "%s.jpg" % source_id))
        candidates.append(os.path.join(tally_images, "%s.jpg" % source_id))
        candidates.append(os.path.join(tally_images, rel.replace("/", os.sep)))
    elif source == "coco":
        candidates.append(os.path.join(coco_images, os.path.basename(rel)))
        candidates.append(os.path.join(tally_images, rel.replace("/", os.sep)))
        candidates.append(os.path.join(tally_images, os.path.basename(rel)))
    for path in candidates:
        if path and os.path.isfile(path) and os.path.getsize(path) > 0:
            return path
    return None


def vg_urls(source_id: str) -> list[str]:
    return [
        "https://cs.stanford.edu/people/rak248/VG_100K/%s.jpg" % source_id,
        "https://cs.stanford.edu/people/rak248/VG_100K_2/%s.jpg" % source_id,
    ]


def coco_urls(rel: str) -> list[str]:
    name = os.path.basename(rel)
    split = "train2014" if "train2014" in rel.replace("\\", "/") else "val2014" if "val2014" in rel.replace("\\", "/") else "train2014"
    return ["http://images.cocodataset.org/%s/%s" % (split, name)]
