# RewardLens CVPR V2 — Quickstart

This is a **working offline audit CLI**, not a full web service or a completed CVPR empirical study. It reads already-inferred, externally verified Judge prediction JSONL, validates the triplet structure, computes conditional metrics and writes a standalone HTML report.

From the repository root:

    python -m rewardlens.cvpr_v2.demo --out-dir ./cvpr_demo
    python -m rewardlens.cvpr_v2.cli \
      --audit-jsonl ./cvpr_demo/audit_synthetic.jsonl \
      --static-jsonl ./cvpr_demo/static_synthetic.jsonl \
      --out-json ./cvpr_demo/report.json \
      --out-html ./cvpr_demo/report.html
    python -m unittest rewardlens.tests.test_cvpr_v2 -v

**Never cite the synthetic demo as scientific evidence.** Open report.html in a browser after running the CLI.

## Audit JSONL schema

Every line is one model's prediction for **one variant of one triplet**. Required keys:

    {
      "model_id": "example_model",
      "model_family": "example_family",
      "triplet_id": "t001",
      "source_id": "source001",
      "split": "development",
      "domain": "controlled_clevr",
      "factor": "count",
      "shift_type": "color_change",
      "edit_direction": "A_to_B",
      "variant": "base",
      "gold": "A",
      "prediction": "A",
      "image_id": "sha256:base_image_hash",
      "question": "How many red objects?",
      "candidate_a": "Two red objects",
      "candidate_b": "Three red objects",
      "semantic_validation_passed": true
    }

For each (model_id, triplet_id), include base, relevant and irrelevant variants. Question and candidate texts must be identical. Relevant gold must flip; irrelevant gold must not; image IDs must be distinct. Use ABSTAIN for no preference prediction; also record inference failures separately.

The validation boolean is an **external receipt assertion**, not generated or independently verified by this tool. Human/image validation must be conducted separately.

Static JSONL comes from an **independent** evaluation and contains model_id, split, domain, factor, accuracy (0..1), n_static. The CLI cannot establish external dataset independence automatically: preserve the original manifests, source IDs and hashes.

Optional shift JSONL contains model_id, model_family, domain, shift_type, shift_loss, static_accuracy, in_distribution_utility, ra, ii derived from *independently scored* real outcomes. It runs a leave-one-family-out ridge comparison (NumPy required, at least 4 families). This is only a descriptive evaluation harness, not statistically validated evidence of utility.

Optional held-out selection JSONL contains task_id, domain, shift_type, split=test, model_id, static_accuracy, predicted_ood_utility, true_ood_utility, inference_cost, static_audit_cost and counterfactual_audit_cost. Run with --selection-jsonl path --selection-budget NUMBER to compare budget-constrained selection regrets. Only submit predictions generated without seeing these held-out targets; the software cannot verify provenance from scores alone.

## Implemented versus missing

**Implemented:** protocol validation, conditional RA/II, independent static matching, common base-correct comparison, shift-prediction sanity check, HTML/JSON reporting and regression tests.

**Not yet implemented:** full image/annotation platform, inference pipeline migration, visual perceptual validity, real external benchmark baselines, OOD scene generation, robust confidence intervals and a trained OOD prediction/selection algorithm. The selection evaluator itself is implemented, but does not learn predictions. See UPGRADE_PROTOCOL.md.
