from .hf_vlm import HuggingFaceVLMAdapter


class MolmoAdapter(HuggingFaceVLMAdapter):
    """AllenAI Molmo. May need trust_remote_code; still UNTESTED."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("trust_remote_code", True)
        super().__init__(*args, **kwargs)
