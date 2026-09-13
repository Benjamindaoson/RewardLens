from .hf_vlm import HuggingFaceVLMAdapter


class QwenVLAdapter(HuggingFaceVLMAdapter):
    """Qwen2.5-VL / Qwen3-VL. Default bf16 + SDPA, no FlashAttention2."""
