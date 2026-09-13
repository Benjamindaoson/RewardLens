from .hf_vlm import HuggingFaceVLMAdapter


class GemmaAdapter(HuggingFaceVLMAdapter):
    """Gemma 3 instruction VLMs. Gated license. Skip after 40 minutes if load fails."""
