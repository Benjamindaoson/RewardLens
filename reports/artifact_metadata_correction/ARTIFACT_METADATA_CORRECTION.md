# Artifact metadata correction — 2026-09-16

**Artifact metadata correction only; no experiment output, metric, manifest, or scientific result changed.**

This note is traceable. It does not silently overwrite Hugging Face files.

## 1. SHA-manifest `carrier` on audit rows

**Symptom.** Phase II SHA manifests label audit count rows `carrier=tallyqa` and other audit rows `carrier=gqa`.

**Fact.** Audit images are procedural RewardLens-CLEVR renders from a blank Blender `base_scene.blend`. They are not GQA, COCO, or TallyQA photographs. Audit `image_id` is null on all 2400 SHA-manifest rows. Physical identity is SHA256 of the rendered PNG. The source-identity gate is \(\mathcal I_{\text{Audit-source}}\cap\mathcal I_{\text{Downstream}}=\varnothing\).

**Correction.** On audit rows, `carrier` is a copied factor→dataset label from the static/downstream split. It is not a photograph pointer. Downstream and static Count remain TallyQA; Attribute/Presence/Spatial remain GQA. Those assignments are unchanged.

## 2. `canonical_model_artifacts.csv` audit pointer

**Symptom.** In the Phase II archive catalog, `audit_file` equals `static_file` on every model, including the original four. Example: Qwen `audit_file=results/qwen3_vl_4b_instruct/static.jsonl`.

**Fact.** Frozen `integrity_audit.json` records a 2400-row audit JSONL and an 800-row static JSONL as distinct objects, with distinct SHA256. Treating the 800-row static file as the audit file is an archive naming/pointer bug.

Frozen audit SHA256 (2400 judgments; `integrity_audit.json`):

| model_id | audit_sha256 |
|---|---|
| qwen3_vl_4b_instruct | `36c02585da47bdbf1bfa4f71e2ca339b146f6adc9fe86623e9fe42988bd0c48e` |
| gemma3_4b_it | `3a38334405de61793afe5e947eb05c7725e8951ce63f830e5a11eef7e4b90b21` |
| molmo_7b_d_0924 | `f6144834ef108523ef50fbc2c608df68cd0972b30c2d69c24444de63f9fd7115` |
| skywork_vl_reward_7b | `ba34dcc317ee395e36073454c1ee9e62f76d6205ae4f563e863292cb652fb0f2` |
| idefics3_8b_llama3 | `c8122e1c944014ce35bd64be3115e7095f8bb6a1a958c3fc8d1c43f1e1d7f880` |
| phi35_vision_instruct | `8e73f285e0da471b40195aab4bfdb97a3de9248adc971f0401b80907e63e9d99` |
| internvl3_8b_hf | `4aa3317ecaf3406e0e86e0c68d720afb8d676abb28b4c55b7b5afaaba3c6643c` |
| llava_onevision_qwen2_7b | `21370b2631b4d44938075b9c672ab1617768bd276bf22f29a5e62f844c34c1d7` |

**Correction.** Readers must resolve audit judgments by the SHA256 in `integrity_audit.json` (and, for the original four, the on-disk 2400-row `full_audit.jsonl`). Do not recompute RA/II from the 800-row static preference file. Canonical metrics, forensic reconstruction, and paper numbers are unchanged.

## What was not changed

- No GPU rerun.
- No metric recomputation besides the already-frozen forensic machine check (160/160 cells match).
- No manifest rewrite of image identities.
- No Hugging Face file overwritten in place.
