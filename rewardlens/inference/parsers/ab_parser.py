from __future__ import annotations

import re


_AB_RE = re.compile(r"\b([AB])\b")
_ANSWER_RE = re.compile(r"(?:answer|preference|choice)\s*[:\-]\s*([AB])", re.I)


def parse_ab(raw: str | None) -> str | None:
    if not raw:
        return None
    text = str(raw).strip()
    if text in {"A", "B"}:
        return text
    match = _ANSWER_RE.search(text)
    if match:
        return match.group(1).upper()
    # Prefer a standalone A/B near the start/end rather than letters inside words.
    compact = text.replace(" ", "")
    if compact[:1] in {"A", "B"} and (len(compact) == 1 or not compact[1].isalpha()):
        return compact[:1]
    found = _AB_RE.findall(text.upper())
    if len(found) == 1:
        return found[0]
    return None
