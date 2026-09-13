from .base import JudgeAdapter
from .dummy import DummyAdapter
from .gemma import GemmaAdapter
from .hf_vlm import HuggingFaceVLMAdapter
from .llama_vision import LlamaVisionAdapter
from .molmo import MolmoAdapter
from .qwen_vl import QwenVLAdapter
from .specialized_reward import SpecializedRewardAdapter

ADAPTERS = {
    "dummy": DummyAdapter,
    "hf": HuggingFaceVLMAdapter,
    "qwen_vl": QwenVLAdapter,
    "gemma": GemmaAdapter,
    "llama_vision": LlamaVisionAdapter,
    "molmo": MolmoAdapter,
    "specialized_reward": SpecializedRewardAdapter,
}

__all__ = [
    "ADAPTERS",
    "JudgeAdapter",
    "DummyAdapter",
    "HuggingFaceVLMAdapter",
    "QwenVLAdapter",
    "GemmaAdapter",
    "LlamaVisionAdapter",
    "MolmoAdapter",
    "SpecializedRewardAdapter",
]
