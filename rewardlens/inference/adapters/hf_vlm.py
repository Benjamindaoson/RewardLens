"""Standard Transformers VLM adapter.

Default: bf16, SDPA/eager. flash-attn / bitsandbytes are opt-in only.
Works on CUDA and ROCm (both expose torch.cuda).
"""

from __future__ import annotations

import os
from typing import Any

from .base import JudgeAdapter

PROMPT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts", "pairwise_ab.txt")


def load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as handle:
        return handle.read()


class HuggingFaceVLMAdapter(JudgeAdapter):
    def __init__(
        self,
        model_id: str,
        checkpoint: str,
        *,
        dtype: str = "bfloat16",
        attn_implementation: str = "sdpa",
        max_new_tokens: int = 16,
        prompt_adapter: str = "pairwise_ab",
        trust_remote_code: bool = False,
        requires_flash_attention: bool = False,
        requires_quantization: bool = False,
    ):
        self.model_id = model_id
        self.checkpoint = checkpoint
        self.dtype_name = dtype
        self.attn_implementation = attn_implementation
        self.max_new_tokens = max_new_tokens
        self.prompt_adapter = prompt_adapter
        self.trust_remote_code = trust_remote_code
        self.requires_flash_attention = requires_flash_attention
        self.requires_quantization = requires_quantization
        self.model = None
        self.processor = None
        self.prompt_template = load_prompt()

    def load_model(self) -> None:
        if self.requires_flash_attention and self.attn_implementation == "sdpa":
            raise RuntimeError(
                "%s is marked requires_flash_attention; refuse silent CUDA-kernel fallback. Set attn explicitly."
                % self.model_id
            )
        if self.requires_quantization:
            raise RuntimeError("%s requires quantization; bitsandbytes is not a default backend." % self.model_id)

        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        dtype_map = {
            "bfloat16": torch.bfloat16,
            "bf16": torch.bfloat16,
            "float16": torch.float16,
            "fp16": torch.float16,
            "float32": torch.float32,
        }
        dtype = dtype_map.get(self.dtype_name, torch.bfloat16)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        attn = self.attn_implementation
        if attn == "sdpa_or_eager":
            attn = "sdpa"
        kwargs = {
            "torch_dtype": dtype,
            "trust_remote_code": self.trust_remote_code,
        }
        if attn and attn != "auto":
            kwargs["attn_implementation"] = attn
        try:
            self.model = AutoModelForImageTextToText.from_pretrained(self.checkpoint, **kwargs)
        except Exception:
            from transformers import AutoModelForCausalLM

            self.model = AutoModelForCausalLM.from_pretrained(self.checkpoint, **kwargs)
        self.model.to(device)
        self.model.eval()
        self.processor = AutoProcessor.from_pretrained(self.checkpoint, trust_remote_code=self.trust_remote_code)
        self.device = device

    def prepare_inputs(self, *, image_path: str, question: str, candidate_a: str, candidate_b: str) -> dict[str, Any]:
        from PIL import Image

        prompt = self.prompt_template.format(
            question=question,
            candidate_a=candidate_a,
            candidate_b=candidate_b,
        )
        image = Image.open(image_path).convert("RGB")
        return {"image": image, "prompt": prompt, "image_path": image_path}

    def judge(self, prepared: Any) -> dict[str, Any]:
        import torch

        if self.model is None or self.processor is None:
            raise RuntimeError("load_model() was not called")
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": prepared["prompt"]},
                ],
            }
        ]
        text = self.processor.apply_chat_template(messages, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[prepared["image"]], return_tensors="pt")
        inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                temperature=None,
            )
        trimmed = output_ids[:, inputs["input_ids"].shape[1] :]
        raw = self.processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        return {"raw_output": raw, "score_a": None, "score_b": None, "margin": None}

    def cleanup(self) -> None:
        self.model = None
        self.processor = None
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
