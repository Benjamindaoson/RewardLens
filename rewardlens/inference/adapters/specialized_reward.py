from .hf_vlm import HuggingFaceVLMAdapter


class SpecializedRewardAdapter(HuggingFaceVLMAdapter):
    """Dedicated VL reward / critic checkpoints (Skywork, IXC-Reward, ...).

    If the checkpoint exposes a value head, scalar scores are stored when present.
    Pairwise A/B remains the common interface. Skip after 40 minutes.
    """
