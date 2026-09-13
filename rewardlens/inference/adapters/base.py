from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class JudgeAdapter(ABC):
    """Unified adapter API for all RewardLens judges."""

    model_id: str = "unknown"

    @abstractmethod
    def load_model(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def prepare_inputs(
        self,
        *,
        image_path: str,
        question: str,
        candidate_a: str,
        candidate_b: str,
    ) -> Any:
        raise NotImplementedError

    @abstractmethod
    def judge(self, prepared: Any) -> dict[str, Any] | str:
        raise NotImplementedError

    def cleanup(self) -> None:
        return None
