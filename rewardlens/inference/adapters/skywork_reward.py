from __future__ import annotations

import os
from typing import Any

from .base import JudgeAdapter


class SkyworkRewardAdapter(JudgeAdapter):
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

        self.model = None
        self.processor = None
        self.device = None

        self.v_weight = None
        self.v_bias = None

    def load_model(self) -> None:
        import torch

        from safetensors import safe_open
        from transformers import (
            AutoProcessor,
            Qwen2_5_VLForConditionalGeneration,
        )

        dtype = (
            torch.bfloat16
            if self.dtype_name in ("bf16", "bfloat16")
            else torch.float16
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = AutoProcessor.from_pretrained(
            self.checkpoint,
            local_files_only=True,
        )

        kwargs = {
            "torch_dtype": dtype,
            "local_files_only": True,
        }

        if self.attn_implementation:
            kwargs["attn_implementation"] = self.attn_implementation

        self.model = (
            Qwen2_5_VLForConditionalGeneration
            .from_pretrained(
                self.checkpoint,
                **kwargs,
            )
        )

        self.model.to(self.device)
        self.model.eval()

        vhead = os.path.join(
            self.checkpoint,
            "value_head.safetensors",
        )

        if not os.path.isfile(vhead):
            raise FileNotFoundError(
                "Skywork value_head.safetensors missing: %s"
                % vhead
            )

        tensors = {}

        with safe_open(
            vhead,
            framework="pt",
            device="cpu",
        ) as f:
            for key in f.keys():
                tensors[key] = f.get_tensor(key)

        weight = None
        bias = None

        for key, tensor in tensors.items():

            if (
                tensor.ndim == 2
                and tensor.shape[0] == 1
                and (
                    key.endswith("summary.weight")
                    or key.endswith("v_head.weight")
                    or key.endswith("weight")
                )
            ):
                weight = tensor

            elif (
                tensor.ndim == 1
                and tensor.numel() == 1
                and (
                    key.endswith("summary.bias")
                    or key.endswith("v_head.bias")
                    or key.endswith("bias")
                )
            ):
                bias = tensor

        if weight is None:
            raise RuntimeError(
                "Could not identify Skywork value-head weight. "
                "Available keys: %s"
                % sorted(tensors.keys())
            )

        if bias is None:
            bias = torch.zeros(
                weight.shape[0],
                dtype=weight.dtype,
            )

        self.v_weight = weight
        self.v_bias = bias
        self.dtype = dtype

        print(
            "Skywork value head:",
            tuple(weight.shape),
            tuple(bias.shape),
        )

    def prepare_inputs(
        self,
        *,
        image_path: str,
        question: str,
        candidate_a: str,
        candidate_b: str,
    ) -> dict[str, Any]:

        return {
            "image_path": image_path,
            "question": question,
            "candidate_a": candidate_a,
            "candidate_b": candidate_b,
        }

    def _score(
        self,
        *,
        image_path: str,
        question: str,
        answer: str,
    ) -> float:

        import torch
        import torch.nn.functional as F

        from qwen_vl_utils import process_vision_info

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image": image_path,
                    },
                    {
                        "type": "text",
                        "text": question,
                    },
                ],
            },
            {
                "role": "assistant",
                "content": str(answer),
            },
        ]

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )

        image_inputs, video_inputs = process_vision_info(
            messages
        )

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        moved = {}

        for key, value in inputs.items():

            if hasattr(value, "to"):
                value = value.to(self.device)

                if (
                    hasattr(value, "is_floating_point")
                    and value.is_floating_point()
                    and key in (
                        "pixel_values",
                        "pixel_values_videos",
                    )
                ):
                    value = value.to(self.dtype)

            moved[key] = value

        inputs = moved

        with torch.no_grad():

            if self.device == "cuda":
                context = torch.autocast(
                    device_type="cuda",
                    dtype=torch.bfloat16,
                    enabled=True,
                )
            else:
                from contextlib import nullcontext
                context = nullcontext()

            with context:
                outputs = self.model(
                    **inputs,
                    return_dict=True,
                    use_cache=False,
                    output_hidden_states=True,
                )

        hidden_states = outputs.hidden_states

        if not hidden_states:
            raise RuntimeError(
                "Skywork/Qwen output did not expose hidden states"
            )

        hidden = hidden_states[-1]

        attention_mask = inputs["attention_mask"]

        last_idx = (
            attention_mask.sum(dim=-1) - 1
        ).long()

        batch = torch.arange(
            hidden.shape[0],
            device=hidden.device,
        )

        # Only the final attended token is required.
        # Equivalent to applying the linear value head
        # to all tokens then gathering the last valid token.
        last_hidden = hidden[
            batch,
            last_idx,
            :
        ].float()

        weight = self.v_weight.to(
            hidden.device,
            dtype=torch.float32,
        )

        bias = self.v_bias.to(
            hidden.device,
            dtype=torch.float32,
        )

        score = F.linear(
            last_hidden,
            weight,
            bias,
        ).squeeze(-1)

        return float(score[0].item())

    def score_candidate(
        self,
        *,
        image_path: str,
        question: str,
        candidate: str,
    ) -> float:
        return self._score(image_path=image_path, question=question, answer=candidate)

    def judge(self, prepared: Any) -> dict[str, Any]:

        score_a = self._score(
            image_path=prepared["image_path"],
            question=prepared["question"],
            answer=prepared["candidate_a"],
        )

        score_b = self._score(
            image_path=prepared["image_path"],
            question=prepared["question"],
            answer=prepared["candidate_b"],
        )

        margin = score_a - score_b

        preference = "A" if margin >= 0 else "B"

        return {
            "raw_output": preference,
            "score_a": score_a,
            "score_b": score_b,
            "margin": margin,
        }

    def cleanup(self) -> None:
        self.model = None
        self.processor = None
        self.v_weight = None
        self.v_bias = None

        try:
            import gc
            import torch

            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

        except Exception:
            pass
