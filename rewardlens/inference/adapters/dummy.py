"""CPU unit-test adapter. Does not load weights. Never used for official outputs."""

from __future__ import annotations

import hashlib
from typing import Any

from .base import JudgeAdapter


class DummyAdapter(JudgeAdapter):
    def __init__(self, model_id: str = "dummy_cpu", fail_mode: str | None = None):
        self.model_id = model_id
        self.fail_mode = fail_mode
        self.loaded = False

    def load_model(self) -> None:
        self.loaded = True

    def prepare_inputs(self, *, image_path: str, question: str, candidate_a: str, candidate_b: str) -> dict[str, Any]:
        if not self.loaded:
            raise RuntimeError("load_model() was not called")
        return {
            "image_path": image_path,
            "question": question,
            "candidate_a": candidate_a,
            "candidate_b": candidate_b,
        }

    def judge(self, prepared: Any) -> dict[str, Any]:
        item_hint = str(prepared.get("question", "")) + "|" + str(prepared.get("image_path", ""))
        if self.fail_mode == "oom" or "FORCE_OOM" in item_hint:
            raise MemoryError("simulated OOM")
        if self.fail_mode == "timeout" or "FORCE_TIMEOUT" in item_hint:
            raise TimeoutError("simulated timeout")
        if self.fail_mode == "error" or "FORCE_ERROR" in item_hint:
            raise RuntimeError("simulated inference error")
        digest = hashlib.sha256(item_hint.encode("utf-8")).hexdigest()
        pref = "A" if int(digest[:8], 16) % 2 == 0 else "B"
        raw = "UNPARSEABLE" if (self.fail_mode == "parse" or "FORCE_PARSE" in item_hint) else ("Answer: %s" % pref)
        return {
            "raw_output": raw,
            "parsed_preference": None if "UNPARSEABLE" in raw else pref,
            "score_a": 1.0 if pref == "A" else 0.0,
            "score_b": 1.0 if pref == "B" else 0.0,
            "margin": 1.0,
        }

    def cleanup(self) -> None:
        self.loaded = False
