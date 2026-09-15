"""Expanded local-only adapters; reuse the exact frozen preference prompt."""
import os
from pathlib import Path
from .hf_vlm import HuggingFaceVLMAdapter

class ExpandedAdapter(HuggingFaceVLMAdapter):
    def load_model(self):
        if self.model is not None:
            return
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor
        if not Path(self.checkpoint).is_dir():
            raise ValueError("existing local checkpoint required")
        if os.environ.get("HF_HUB_OFFLINE")!="1" or os.environ.get("TRANSFORMERS_OFFLINE")!="1":
            raise ValueError("offline environment required")
        phi=self.model_id=="phi35_vision_instruct"
        self.processor=AutoProcessor.from_pretrained(self.checkpoint,trust_remote_code=phi,local_files_only=True)
        if phi:
            cls=AutoModelForCausalLM
        else:
            from transformers import AutoModelForImageTextToText
            cls=AutoModelForImageTextToText
        attention={"_attn_implementation":"eager"} if phi else {"attn_implementation":"sdpa"}
        self.model=cls.from_pretrained(self.checkpoint,trust_remote_code=phi,local_files_only=True,
            torch_dtype=torch.bfloat16,device_map="cuda:0",low_cpu_mem_usage=True,**attention)
        self.model.eval()
        self.device="cuda:0"

    def render_prompt(self,prepared):
        if self.model_id=="phi35_vision_instruct":
            # Required model image delimiter only; preference prompt text is unchanged.
            messages=[{"role":"user","content":"<|image_1|>\n"+prepared["prompt"]}]
            return self.processor.tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        messages=[{"role":"user","content":[{"type":"image"},{"type":"text","text":prepared["prompt"]}]}]
        return self.processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)

    def judge(self,prepared):
        import torch
        if self.model is None:
            raise RuntimeError("load_model was not called")
        text=self.render_prompt(prepared)
        inputs=self.processor(text=text,images=[prepared["image"]],return_tensors="pt")
        inputs={k:(v.to(device=self.device,dtype=self.model.dtype) if v.is_floating_point()
                    else v.to(self.device)) if hasattr(v,"is_floating_point") else v for k,v in inputs.items()}
        with torch.inference_mode():
            outputs=self.model.generate(**inputs,max_new_tokens=self.max_new_tokens,do_sample=False,temperature=None)
        raw=self.processor.batch_decode(outputs[:,inputs["input_ids"].shape[1]:],skip_special_tokens=True)[0]
        return {"raw_output":raw,"score_a":None,"score_b":None,"margin":None}
