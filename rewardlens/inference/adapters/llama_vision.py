from .hf_vlm import HuggingFaceVLMAdapter


class LlamaVisionAdapter(HuggingFaceVLMAdapter):
    """Llama 3.2 Vision. CUDA-custom-op risk. Replace from backup pool if incompatible."""
