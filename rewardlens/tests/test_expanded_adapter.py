from pathlib import Path
import tempfile
from PIL import Image
from inference.adapters.expanded import ExpandedAdapter
from inference.adapters.hf_vlm import load_prompt

def check_prompt():
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/"synthetic.png"
        Image.new("RGB",(32,32),"red").save(path)
        adapter=ExpandedAdapter("phi35_vision_instruct","/nonexistent")
        prepared=adapter.prepare_inputs(image_path=str(path),question="Color?",candidate_a="Red",candidate_b="Blue")
        assert prepared["prompt"]==load_prompt().format(question="Color?",candidate_a="Red",candidate_b="Blue")
        class Tokenizer:
            def apply_chat_template(self,messages,**kwargs):
                assert messages==[{"role":"user","content":"<|image_1|>\n"+prepared["prompt"]}]
                assert kwargs=={"tokenize":False,"add_generation_prompt":True}
                return "wrapped"
        class Processor:
            tokenizer=Tokenizer()
        adapter.processor=Processor()
        assert adapter.render_prompt(prepared)=="wrapped"
        assert not Path("/nonexistent").exists()
    print("EXPANDED_PROMPT_WRAPPER_PASS")

if __name__=="__main__":
    check_prompt()
