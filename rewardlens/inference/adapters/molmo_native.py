from __future__ import annotations

from typing import Any

from .base import JudgeAdapter
from .hf_vlm import load_prompt


class MolmoNativeAdapter(JudgeAdapter):
    def __init__(
        self,
        model_id: str,
        checkpoint: str,
        *,
        dtype: str = "bfloat16",
        attn_implementation: str = "sdpa",
        max_new_tokens: int = 16,
        prompt_adapter: str = "pairwise_ab",
        trust_remote_code: bool = True,
        requires_flash_attention: bool = False,
        requires_quantization: bool = False,
    ):
        self.model_id = model_id
        self.checkpoint = checkpoint
        self.dtype_name = dtype
        self.max_new_tokens = max_new_tokens

        self.model = None
        self.processor = None
        self.device = None

        self.prompt_template = load_prompt()

    def load_model(self) -> None:
        import torch

        from transformers import (
            AutoModelForCausalLM,
            AutoProcessor,
        )

        dtype = (
            torch.bfloat16
            if self.dtype_name in ("bf16", "bfloat16")
            else torch.float16
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = AutoProcessor.from_pretrained(
            self.checkpoint,
            trust_remote_code=True,
            local_files_only=True,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.checkpoint,
            trust_remote_code=True,
            torch_dtype=dtype,
            local_files_only=True,
        )

        self.model.to(self.device)
        self.model.eval()

        # transformers 4.57+ injects an empty DynamicCache by default, while
        # Molmo's remote code expects its legacy (key, value) cache tuples.
        self.model._supports_default_dynamic_cache = lambda: False

        self.dtype = dtype

    def prepare_inputs(
        self,
        *,
        image_path: str,
        question: str,
        candidate_a: str,
        candidate_b: str,
    ) -> dict[str, Any]:

        from PIL import Image

        prompt = self.prompt_template.format(
            question=question,
            candidate_a=candidate_a,
            candidate_b=candidate_b,
        )

        image = Image.open(image_path).convert("RGB")

        return {
            "image": image,
            "prompt": prompt,
            "image_path": image_path,
        }

    def judge(self, prepared: Any) -> dict[str, Any]:
        import torch

        from transformers import GenerationConfig

        if self.model is None or self.processor is None:
            raise RuntimeError("load_model() was not called")

        raw_inputs = self.processor.process(
            images=[prepared["image"]],
            text=prepared["prompt"],
        )

        inputs = {}

        for key, value in raw_inputs.items():
            if hasattr(value, "to"):
                value = value.to(self.device)

                # Official Molmo inference treats processor output
                # as an unbatched example.
                value = value.unsqueeze(0)

                if (
                    key == "images"
                    and hasattr(value, "is_floating_point")
                    and value.is_floating_point()
                ):
                    value = value.to(self.dtype)

            inputs[key] = value

        generation_config = GenerationConfig(
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
            stop_strings="<|endoftext|>",
        )

        input_len = inputs["input_ids"].size(1)

        with torch.no_grad():
            if self.device == "cuda":
                with torch.autocast(
                    device_type="cuda",
                    dtype=torch.bfloat16,
                    enabled=True,
                ):
                    output = self.model.generate_from_batch(
                        inputs,
                        generation_config,
                        tokenizer=self.processor.tokenizer,
                    )
            else:
                output = self.model.generate_from_batch(
                    inputs,
                    generation_config,
                    tokenizer=self.processor.tokenizer,
                )

        generated = output[0, input_len:]

        raw = self.processor.tokenizer.decode(
            generated,
            skip_special_tokens=True,
        ).strip()

        return {
            "raw_output": raw,
            "score_a": None,
            "score_b": None,
            "margin": None,
        }

    def cleanup(self) -> None:
        self.model = None
        self.processor = None

        try:
            import gc
            import torch

            gc.collect()

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

        except Exception:
            pass
