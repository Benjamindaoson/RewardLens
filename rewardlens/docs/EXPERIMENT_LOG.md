# Experiment Log

## 2026-09-12 — Scientific source of truth loaded

Read in full:

`d:\发表\ICLR\Multimodal Reward Model\Do Multimodal Reward Models Rely on the Right Visual Evidence_ — 完整研究方案.md`

Execution contract is the previous run-to-completion prompt. Research questions were not changed.

### Conflicts (logged, not used to rewrite RQs)

1. **Count question wording**
   - Plan §9.1 example: "How many red cubes are there?"
   - Count Pilot V1 (already generated, validation PASS): "How many \<COLOR\> objects are there?"
   - Decision: keep Count Pilot V1. This is operationalization of Count, not a change of RQ1–RQ3. Color-only membership avoids mixing size/material/shape into the tested variable. Existing 10-triplet data is frozen.

2. **Count matching strictness**
   - Plan table example: +1 target object vs +1 distractor object (illustrative +1 blue sphere).
   - Count Pilot V1: relevant/irrelevant objects match position, shape, size, material, rotation; only color (target membership) differs.
   - Decision: keep the stricter matching. This protects the intervention-matching principle.

3. **Pilot scale**
   - Plan: 300–500 / factor as pilot, then 1,000–2,000 / factor.
   - Execution: 10-triplet QC pilots per remaining factor, then 500 / factor first.
   - Decision: 10-triplet QC first, then 500. Do not jump to 1,000–2,000 before QC and resource check. This protects data quality, not the RQs.

4. **LPIPS**
   - Plan mentions LPIPS among magnitude checks.
   - Execution: scene-graph / factor-specific magnitude + RGB MAD diagnostics; RGB MAD is not the semantic matcher.
   - Decision: defer LPIPS (extra model). Factor-specific magnitude remains primary matching evidence.

### Protected principles in force

- Data independence: CLEVR audit vs GQA static vs GQA downstream; no audit-base A; image-disjoint static/downstream.
- Intervention matching: geometry-matched relevant/irrelevant edits.
- Confirmatory freeze before full model inference.
- No fabricated results, no silent drops, no prompt shopping after seeing model rankings.

### PHASE 0

Count Pilot V1 already PASS. Not re-rendered.

- 10 triplets, 30 images, validation 296/296, exit 0
- Output: `D:\01_work\RewardLens\outputs\count_pilot_v1`

### PHASE 1–4 — 2026-09-12 later

Attribute / Presence / Spatial 10-triplet pilots:

- Attribute: 293 checks, 0 failures, QC 10 PASS
- Presence: 273 checks, 0 failures, QC 10 PASS
- Spatial: 273 checks, 0 failures, QC 10 PASS

Visual contract holds on sampled contact sheets (unique target, matched irrelevant edit, spatial left→right flip with matched displacement).

Dataset gate: 4/4 factors clean.

500-triplet specs generated for all four factors (separate scale dirs, pilots frozen). Blender scale render started with resume.

### 2026-09-12 — Deadline-first FAST_TRACK (operational, not an RQ change)

Plan originally discussed 300–500 then 1,000–2,000 / factor. Execution now freezes **FAST_TRACK_AUDIT_V1** at 200 PASS / factor as soon as available, while 500/factor rendering continues as P1 robustness.

GQA primary scale is 200 items / factor (static) and 200 questions / factor (BoN, N=8), image-disjoint.

TallyQA / VQA / MMVP / editing / LoRA remain P2 until RQ1–RQ3 exist.

PFC/PSC definitions in code were aligned to the frozen plan:

- PFC = P(base correct AND relevant correct)
- PSC = P(base correct AND irrelevant correct)

Confirmatory plan marked **FROZEN BEFORE FULL MODEL RESULTS**.

## 2026-09-12 — GQA 1.2 has no Count questions

`questions1.2.zip` extracted (1,498,616,372 bytes, zip test OK). Scene graphs extracted (`sceneGraphs.zip` 44,824,862 bytes).

Program+type mapping of train+val balanced questions: Count=0, Attribute=358463, Presence=146790, Spatial=191085.

Byte scan of balanced, testdev_all, val_all, and train_all shard 0 found **zero** `How many` strings, **zero** numeric answers, **zero** `count` functional operations. Count GQA-Static and GQA-Downstream therefore have N=0. This is recorded, not filled with invented questions. CLEVR Count audit is unaffected.

## 2026-09-12 — PRE-RESULT DATA AVAILABILITY ADAPTATION

**Not result-driven.** No reward-model outputs exist.

GQA Count stays N=0. Frozen natural-image assignment:

| Factor | Static / Downstream |
|---|---|
| Count | TallyQA |
| Attribute | GQA |
| Spatial | GQA |
| Presence | GQA |

TallyQA annotations downloaded (`tallyqa.zip`, 5,691,198 bytes; `train.json` + `test.json`). Frozen 200 static + 200 downstream Count items, 100 simple / 100 complex each, image-disjoint (intersection 0). Hard negatives gold ± 1; downstream N=8 nearby nonnegative counts. Images: reuse VG/GQA files; do not download the full TallyQA dump. Inventory must end at missing=0.

RQ2 is factor-wise \(U_f\sim A_f\) vs \(U_f\sim A_f+\mathrm{PFC}_f+\mathrm{PSC}_f\). RQ3 compares the four \(D\) predictors within each \(U_f\) column; diagonal-vs-off-diagonal uses within-column standardization. Raw TallyQA and GQA utility are not pooled.

Documented in `CONFIRMATORY_ANALYSIS_PLAN.md`, `GQA_DATA_CONSTRUCTION.md`, `TALLYQA_DATA_CONSTRUCTION.md`, `STATISTICAL_ANALYSIS.md`, and the paper draft.

## 2026-09-12 — PRE-GPU CLOSURE

SIGNAL_GATE_V1 untouched. Per-factor FAST_TRACK freeze enabled (200 PASS each, do not wait for other factors). Combined FAST_TRACK_AUDIT_V1 still requires all four.

RQ2/RQ3 scripts frozen on synthetic fixtures. GQA-only 3-factor RQ3 sensitivity pre-registered as supplementary only. DATA_SOURCE_CONFOUND_NOTE recorded: Count=TallyQA co-varies with factor identity; within-column z-score does not remove that confound.

Full P0 bundle builder refuses unless FAST_TRACK_AUDIT_V1 is frozen.
