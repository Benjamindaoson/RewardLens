"""Create explicitly SYNTHETIC demo input. Not suitable for publication."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def make_demo(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    observations = []
    models = [("demo_judge_1", "demo_family_1"), ("demo_judge_2", "demo_family_2")]
    for k in range(8):
        gold_b = "A" if k % 2 == 0 else "B"
        gold_r = "B" if gold_b == "A" else "A"
        for model, family in models:
            for variant, gold in (("base", gold_b), ("relevant", gold_r), ("irrelevant", gold_b)):
                pred = gold
                if model == "demo_judge_2" and variant == "relevant" and k < 4:
                    pred = gold_b
                observations.append({
                    "model_id": model, "model_family": family,
                    "triplet_id": f"synthetic_{k}", "source_id": f"synthetic_source_{k}",
                    "split": "development" if k < 4 else "test", "domain": "synthetic_clevr",
                    "factor": "count", "shift_type": "synthetic_color_change",
                    "edit_direction": "A_to_B" if k % 2 == 0 else "B_to_A",
                    "variant": variant, "gold": gold, "prediction": pred,
                    "image_id": f"synthetic_{k}_{variant}", "question": "Synthetic demo question",
                    "candidate_a": "synthetic answer A", "candidate_b": "synthetic answer B",
                    "semantic_validation_passed": True,
                })
    scores = [
        {"model_id": m, "split": split, "domain": "synthetic_clevr", "factor": "count",
         "accuracy": 0.75, "n_static": 100}
        for m, _ in models for split in ("development", "test")
    ]
    for name, items in (("audit_synthetic.jsonl", observations), ("static_synthetic.jsonl", scores)):
        (folder / name).write_text("".join(json.dumps(item) + "\n" for item in items), encoding="utf-8")
    (folder / "DO_NOT_CITE.txt").write_text("SYNTHETIC DEMO — NOT RESEARCH EVIDENCE\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", required=True)
    make_demo(Path(p.parse_args().out_dir))
