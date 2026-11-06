# RewardLens CVPR — Visual Counterfactual Grounding Protocol (V2 draft)

**Status (2026-11-06): IMPLEMENTATION PROTOTYPE.** This is an experimental design, not completed results, a ready-to-submit paper or a guarantee of acceptance. CVPR direction: **visual grounding and evidence-dependence of multimodal judges**, not relabeling the original ICLR paper.

## 0. Submission gate — decide before enrolling

- CVPR 2027 abstract/enrollment: **Nov 10 2026 AOE**; full paper **Nov 16 2026 AOE**; supplementary **Nov 23 2026 AOE**. Official: https://cvpr.thecvf.com/Conferences/2027/CallForPapers
- RewardLens is **under ICLR 2027 review**. Both venues prohibit simultaneous submissions of substantially similar manuscripts. Do **not** enroll a substantially overlapping CVPR paper while the ICLR version remains under review. Rewriting the title or adding a few experiments is insufficient.
- Withdrawal of ICLR is a decision for all authors, not undertaken by this branch. ICLR says withdrawals after the paper deadline remain visible and are de-anonymized: https://iclr.cc/Conferences/2027/AuthorGuidelines
- CVPR requires double-blind anonymity, an 8-page body, mandatory LLM usage statement and complete OpenReview enrollment. Do not link an identifying public GitHub profile in a blind CVPR paper.

## 1. CV-specific scientific question

**Candidate title:** *RewardLens: Counterfactual Visual Grounding for Reliable Multimodal Judges*.

**H1 (incremental visual shift prediction):** Independently measured, task-conditional visual evidence reliance adds out-of-sample information about multimodal judge failure under held-out visual shifts beyond strong static scores, in-distribution utility, domain/family controls and existing perturbation benchmarks.

**H2 (downstream decision value):** An independently calibrated shift-risk estimate improves judge-selection regret on unseen visual tasks at matched total audit plus inference cost, relative to static and existing-intervention metrics.

These are **hypotheses, not results**. Negative results must be reported. H1 is necessary for a credible strong H2 claim.

**Nontrivial difference vs ICLR:** The original static-score-matching observation is descriptive. The CVPR project must establish a visual-shift-focused, genuinely new predictive/decision contribution with human-validated visual controls and independent strong baselines. Substantial textual, experimental or method overlap is a policy issue, not solved automatically by this design document.

## 2. Mandatory prior-work boundary

- [VisualFLIP (2026)](https://arxiv.org/abs/2606.07872): fixed-question, visual counterfactual evidence and answer updating. Do not claim these are new.
- [MM-JudgeBias (ACL 2026)](https://aclanthology.org/2026.acl-long.1162/): multimodal Judge perturbation sensitivity and stability. Two-branch evaluation alone is not new.
- VL-RewardBench (CVPR 2025): challenging, human-verified multimodal Judge benchmark.
- Multimodal RewardBench 2 (CVPR 2026): real multimodal judging and correlation to downstream Best-of-N. Such correlation alone is not new.
- Multi-Crit (CVPR 2026): criterion-level multimodal Judge benchmarking.
- ARM-Thinker (CVPR 2026): tool-grounded reward evaluation. Tool use alone is not new.

**Possible contribution to prove, not assert:** more reliable cross-family *out-of-distribution failure prediction* and *better cost-matched judge selection* than static and perturbation baselines. If this fails, do not claim it.

## 3. Data and visual perception validity

Target controlled CLEVR, natural-image, chart/document and open-ended visual-judging domains.

For each source image, design a base image, a relevant visual intervention that **reverses** gold pair preference, and an irrelevant matched intervention that **preserves** it. Exact question and A/B response texts must stay fixed. Counterbalance semantic yes/no, gold A/B, addition/removal, translation direction, candidate presentation order. Match edit intensity when possible.

**Human verification is separate from metadata validation.** Record the actual images, creation process, visual difference measures, original-image provenance/license, annotator instructions, direct answer-content labels, independent annotator votes, disagreements and ambiguous samples. Resolve the original Spatial annotation anomaly before making Spatial a headline claim.

**Leakage prevention:** group partitions by original source image, document/video, task template and shift family where appropriate; do not only split transformed filenames. The same triplet and gold labels must be identical for all Judges. Restrict OOD test data from feature engineering and model selection.

The current validator checks schema/metadata consistency only. A JSON flag is **not evidence of real-world perceptual validity**.

## 4. Experiment program

- **E0 — Reproduce and forensic-audit the old work.** Verify Count joint-correct sets, Skywork adapter semantics, Spatial label issue, paired matching, source leakage, RA/II, U@8 and prior Phase II regressions from immutable raw records. Note any unrecoverable result.
- **E1 — Perceptual controls.** Human response-content labels, edit direction balance, counterfactual visual evidence specificity, candidate order, artifact strength and fairness.
- **E2 — Strong static ceiling control.** Independently construct static sets matched on scene and answer difficulty, base-label prevalence, domain and annotation budget. Compare on the exact common base-correct support; do not mix base-correct denominators.
- **E3 — Direct existing-method baselines.** VisualFLIP-style paired accuracy, MM-JudgeBias-style sensitivity/stability, independent static accuracy, *extra-static-data with equal annotation budget*, in-distribution downstream utility, simple controls and oracle reference. Confirm metrics are comparable before using literature values.
- **E4 — Genuine judging.** Use real natural-image and open-ended response pairs with meaningful semantic preferences, including specialist reward-head models and ordinary VLMs, with faithful adapter inputs and scoring rules.
- **E5 — H1.** Let signed shift loss be D(j,d,s) = U_ID(j,d) - U_OOD(j,d,s). Compare M0=[static A, ID utility, shared nuisance controls] versus M1=M0+[RA,II,counterfactual features] under identical model class, budget and train-only standardization. Primary metric: family-macro held-out delta MAE > 0. Use held-out task, family and shift tests; report uncertainty and failures.
- **E6 — H2.** Select Judge via predicted OOD utility at **equal total cost**, including audit labeling and runtime, then compare selection regret U(oracle)-U(selected) on **unseen** tasks against static selection and perturbation baselines. Oracle is only retrospective.
- **E7 — Robustness.** Test Best-of-N pools N=2,4,8 (and 16 if budget permits), stronger models, independent seeds, abstentions, all shifts including negative results, leave-one-family-out and source-cluster confidence intervals.

Do not treat examples from the same model family as independent families. The old 8-Judge analysis is small-N descriptive evidence; it does not prove out-of-family prediction.

## 5. Gates for a defensible CVPR submission

- **G0:** severe annotation and leakage problems resolved with documented evidence.
- **G1:** at least one **genuine visual judge** use case where exact string matching is inadequate.
- **G2:** predictive improvement on truly unseen families/domains/shifts over strongest fair prior baselines; report effect sizes and CIs, not just in-sample R-squared.
- **G3:** actual improvement in **judge choice regret at equal total cost**, not only correlations or proxy metric optimization.
- **G4:** complete raw predictions and reproducibility receipts for independent verification.

If G2 fails, the predictive storyline fails. Reformulate the paper rather than enlarging the model list to search for significance.

## 6. Software platform milestone: what is implemented

Implemented in rewardlens/cvpr_v2:

1. Strict JSONL triplet validation: relevant flip, irrelevant invariance, fixed question/answers, duplicate detection, source/image split leakage, model-independent gold/visual metadata.
2. Conditional RA and II, A/B base counts and abstentions.
3. Independent static-score matching; shared-base-correct paired comparisons and overlap counts.
4. Family-held-out ridge evaluation of signed shift loss (descriptive evaluation harness, **not a trained final predictor**).
5. JSON and standalone HTML output; synthetic test data and 12 automated tests.
6. Budget-aware held-out Judge selection regret evaluator, scoring precomputed independent predictions.

**Not yet implemented:** real-image synthesis and validation, annotation platform, GPU judge inference at scale, faithful external benchmark reproduction, actual held-out OOD study, learned risk-based judge selector, full statistical inference, CVPR paper PDF.

## 7. CVPR figure plan

1. Verified, human-understandable relevant/irrelevant **visual counterfactual** triplets.
2. Ceiling-controlled static ties versus held-out visual shift failures.
3. Cross-family MAE comparisons with strong baselines and uncertainty.
4. Equal-cost Judge selection regret / Best-of-N outcomes on independent scenes.
5. Failure modes, A/B/candidate-order effects, human disagreement, negative shifts.

Never make plots from synthesized *outcomes* and present them as real research findings.
