# Do Multimodal Reward Models Rely on the Right Visual Evidence?

## Factor-Specific Visual Dependencies Beyond Preference Accuracy

*ICLR 2027 draft (superseded as the active writing surface by `iclr2027_paper_v2.md`).*

**Status.** Notation below splits static accuracy \(A^S\) from audit-base accuracy \(A^B\). FAST_TRACK_AUDIT_V1 remains the primary audit scale.

---

## 1. Introduction

A multimodal reward model, or judge, is typically evaluated by whether it ranks the better response above the worse one. Preference accuracy is not a frivolous statistic: VL-RewardBench, RewardBench 2, and Multimodal RewardBench 2 all report that accuracy-style benchmarks track downstream selection utility, including Best-of-N. We do not dispute that association, and we do not claim that preference accuracy is useless.

The missing distinction is more elementary. Ranking the correct answer first is an *outcome*. It does not establish that the judge used the visual evidence that makes that answer true. A model can be right for the wrong reason: a text prior, a shallow visual shortcut, or a change that is visually large but semantically irrelevant to the question. Conversely, two models with nearly identical static accuracy \(A^S\) can differ in whether they flip when the queried evidence changes and stay when a matched irrelevant edit is applied. A further distinction is required inside the audit itself: **outcome correctness is not behavioral stability**. A judge can become wrong on a relevant image without ever changing its predicted preference, because the gold label typically flips while the letter the model emits does not.

We therefore separate two validity notions for a judge \(r_m(I,q,y)\), and we never identify static accuracy with audit-base accuracy:

1. **Outcome validity.** Does the judge prefer the correct candidate on ordinary static items? This is \(A^S\), measured on an independent static set.
2. **Evidence-dependence validity.** Does the preference move when the queried visual factor changes, and remain stable under a magnitude-matched irrelevant change? This is a profile \(D=(\mathrm{RA},\mathrm{II})\) computed on controlled audit triplets, not a second copy of \(A^S\).

The working hypothesis, which this paper treats as *to be tested rather than assumed*, is that reliable reward combines both:

\[
\text{Reliable reward} \stackrel{?}{=} \text{correct outcome} + \text{correct evidence dependence}.
\]

Shortcut learning (Geirhos et al.) and right-for-the-right-reasons (Ross et al.) developed this idea for task models. Recent multimodal reward work already shows related failure modes: text-only spurious correlations, perception bottlenecks, and perceptual judgment bias in which a model sees the image yet still prefers a fluent but visually wrong response. What is still missing is a confirmatory test that (i) measures factor-specific visual dependence with matched interventions, (ii) asks whether that dependence predicts downstream Best-of-N utility *beyond* static accuracy \(A^S\), and (iii) checks that the prediction is factor-specific rather than a second global quality score.

**Research questions.**

- **RQ1.** Do similarly accurate multimodal reward models exhibit different factor-specific visual dependencies? Accuracy-matched means \(|\Delta A^S|\le 1\) pp (predeclared).
- **RQ2.** Does factor-specific visual dependency add out-of-sample predictive information about downstream utility beyond static preference accuracy \(A^S\)?
- **RQ3.** Is that predictive validity factor-specific (diagonal stronger than off-diagonal in an audit-factor \(\times\) downstream-factor matrix)?

[TBD: RQ1 ACCURACY-MATCHED RESULT]

[TBD: DELTA LOFO PERFORMANCE]

[TBD: SPECIFICITY MATRIX RESULT]

---

## 2. Related Work

**Preference accuracy as a proxy for reward quality.** Text reward benchmarks, and their multimodal counterparts, primarily report pairwise accuracy and show correlations with Best-of-N, PPO, or related downstream use. This literature motivates treating \(A^S\) as an informative baseline, not as a quantity to be discarded.

**Shortcuts and right-for-the-right-reasons.** Geirhos et al. argue that high benchmark scores can rest on non-robust decision rules. Ross, Hughes, and Doshi-Velez argue that a predictor should be correct *because of* the right input features. Both lines of work target task models. Reward models evaluate *other* models' outputs; a spurious judge can launder shortcuts into selection, filtering, and RL.

**Multimodal judges and visual evidence.** VL-RewardBench highlights perception as a bottleneck. Work on multimodal reward shortcuts documents text-only correlations that hurt OOD generalization. Perception-Judge describes models that perceive the image yet still award higher scores to textually plausible errors. Complementary work on multimodal reasoning (including sensitivity/invariance formulations) shows that answer-level correctness does not imply correct visual grounding.

**Controlled visual interventions.** Synthetic scenes such as CLEVR support precise edits to count, attributes, presence, and spatial relations while holding camera, lighting, and unmatched objects fixed. We use this controllability for *audit* interventions, not as a substitute for natural-image utility.

**This paper.** We connect matched relevant/irrelevant visual interventions to factor-wise Best-of-N utility through pre-registered incremental validity and a factor-specificity matrix. Count static/downstream use TallyQA; Attribute, Spatial, and Presence use GQA. VQA-v2, MMVP, image editing, and extra TallyQA beyond the frozen Count split are deferred external checks, not additional primary evidence for RQ1–RQ3.

---

## 3. Problem Formulation

Let \(J\) be a judge with pairwise preference \(\hat Y\in\{A,B\}\) over candidates \(y_A,y_B\) given \((I,q)\). A visual factor \(f\) belongs to \(\{\text{Count},\text{Attribute},\text{Presence},\text{Spatial}\}\).

**Static accuracy.** \(A^S_{J,f}\) is pairwise preference accuracy on the factor-wise *independent static set*: TallyQA-Static for Count, GQA-Static for Attribute, Presence, and Spatial. Audit base images are never used to compute \(A^S\). The symbol \(A\) in the frozen confirmatory plan is this quantity.

**Audit-base accuracy.** On a complete controlled triplet, write binary correctness bits \(B,R,I\in\{0,1\}\) for base, relevant, and irrelevant. The eight-state object is

\[
\pi_{bri}=P(B=b,R=r,I=i),\qquad b,r,i\in\{0,1\}.
\]

Audit-base accuracy is the \(B=1\) margin, never called static accuracy:

\[
A^B_{J,f}=P(B=1)=\sum_{r,i}\pi_{1ri}.
\]

**Evidence-dependence profile.** Relevant sensitivity and irrelevant invariance are *conditional on a correct base decision*:

\[
\mathrm{RA}=P(R=1\mid B=1)=\mathrm{PFC_{cond}},\qquad
\mathrm{II}=P(I=1\mid B=1)=\mathrm{PSC_{cond}}.
\]

Write \(D(J,f)=(\mathrm{RA}_{J,f},\mathrm{II}_{J,f})\). Joint metrics remain the frozen confirmatory endpoints

\[
\mathrm{PFC}=P(B=1\land R=1)=A^B\cdot\mathrm{RA},\qquad
\mathrm{PSC}=P(B=1\land I=1)=A^B\cdot\mathrm{II}.
\]

RA and II are projections of \(\pi\). In particular \(\pi_{101}=P(B=1,R=0,I=1)\) is mass that is counted as base-correct and irrelevant-correct, hence inflates II, while contributing 0 to RA. Reporting only \((\mathrm{RA},\mathrm{II})\) therefore hides structure that the eight-state recovers.

**Prediction versus correctness.** Let \(\hat Y_B,\hat Y_R,\hat Y_I\) be the judged letters. Behavioral flip rates are

\[
F_R=P(\hat Y_R\neq\hat Y_B),\qquad F_I=P(\hat Y_I\neq\hat Y_B).
\]

On a relevant intervention the gold label typically flips, so \(R=0\) can occur with \(\hat Y_R=\hat Y_B\): correctness changes while the prediction does not. \(F_R\) is not interchangeable with \(1-\mathrm{RA}\).

**Identification.** The scientific object is that \(A^S\) does not determine \(D\). Accuracy-equivalence classes are defined on the static set only:

\[
\mathcal E_\epsilon(J)=\bigl\{J':\bigl|A^S(J')-A^S(J)\bigr|\le\epsilon\bigr\}.
\]

The predeclared matching band remains \(\epsilon=1\) percentage point. Other \(\epsilon\) (including \(0\), \(0.5\), \(5\)) are post-hoc sensitivity. Behavioral diameter

\[
\mathrm{Diam}_D(\mathcal E_\epsilon)=\sup_{J',J''\in\mathcal E_\epsilon}\bigl\|D(J')-D(J'')\bigr\|
\]

asks whether tightening the accuracy gap collapses evidence-dependence dispersion. A non-zero \(\mathrm{Diam}_D(\mathcal E_0)\) is already an identification result.

**Downstream utility.** \(U_{J,f}(N)\) is Best-of-N selection accuracy on the factor-wise downstream set (TallyQA Count; GQA otherwise), with a frozen candidate pool of size \(N\). Primary \(N=8\); \(N=2,4\) are robustness. Raw \(U\) is not pooled across TallyQA and GQA.

**RQ1.** Among pairs with \(|A^S_{J,f}-A^S_{J',f}|\le 1\) pp, is \(D(J,f)\) substantially different from \(D(J',f)\)?

**RQ2.** Compare \(U_f\sim A^S_f\) against \(U_f\sim A^S_f+\mathrm{PFC}_f+\mathrm{PSC}_f\) under leave-one-family-out, separately per downstream factor.

**RQ3.** Within each downstream factor column, test \(D_{J,f}\to U_{J,f}\) versus \(D_{J,f'}\to U_{J,f}\) for \(f'\neq f\). Aggregate diagonal vs off-diagonal only after within-column standardization.

Data independence:

\[
D_{\mathrm{audit}}\neq D_{\mathrm{static}}\neq D_{\mathrm{downstream}}.
\]

Audit is RewardLens-CLEVR. Count static/downstream are TallyQA, image-disjoint. Attribute/Spatial/Presence static/downstream are GQA, image-disjoint. Physical identity is SHA256 of raw image bytes; logical `example_id` is not a physical unit. The source-identity gate is \(\mathcal I_{\text{Audit-source}}\cap\mathcal I_{\text{Downstream}}=\varnothing\): audit scenes are procedural CLEVR renders from a blank `base_scene.blend`, not re-rendered GQA/TallyQA photographs.

---

## 4. Method: Evidence-Dependence Validity

Fix the question and the two candidates. Apply two interventions of matched visual magnitude:

- **Relevant.** Change only the queried factor (count membership, queried attribute, target presence, queried left/right relation) so the correct preference *flips*.
- **Irrelevant.** Apply a geometry-matched edit that does *not* change the queried answer, so the correct preference *stays*.

A judge with correct evidence dependence should flip on the relevant image and stay on the irrelevant image, given a correct base decision. Magnitude matching (same slot, shape, size, material, displacement, render seed, camera, and lights) is a *check* that the two edits are comparable; it does not itself define semantic relevance.

This is an audit of the judge, not a new CLEVR VQA leaderboard.

---

## 5. RewardLens-CLEVR Construction

We render 320\(\times\)240 CLEVR-style scenes with Blender 2.79b, 128 Cycles samples, no camera or light jitter, and a fixed seed within each triplet.

**Count.** Question: “How many \(\langle\)COLOR\(\rangle\) objects are there?” Relevant: add one object whose color is the target color. Irrelevant: add one object in the same slot with the same shape, size, material, and rotation, but a non-target color. Only target membership changes.

**Attribute.** Question: “What color is the \(\langle\)SHAPE\(\rangle\)?” The queried shape is unique. Relevant: recolor that object. Irrelevant: apply the same color transition to a matched non-target of equal size and material at similar depth.

**Presence.** Question: “Is there a \(\langle\)COLOR SHAPE\(\rangle\)?” Relevant: remove the target. Irrelevant: remove a matched non-target of the same shape, size, and material; the target remains.

**Spatial.** Question: “Is X left of Y?” Relevant: move the referent until left becomes right. Irrelevant: apply the identical world displacement to a distractor; the queried relation is unchanged.

FAST_TRACK_AUDIT_V1 uses the first 200 programmatic PASS triplets per factor (800 triplets, 2400 images), sampled by sorted triplet id from PASS only. FAIL and BORDERLINE rows are retained in QC and are not deleted to hit a quota. A 500/factor render continues as P1 scale-up.

[TBD: FAST_TRACK PASS/FAIL COUNTS AFTER FREEZE]

---

## 6. Metrics

**Static \(A^S\).** Pairwise accuracy on the factor-wise static set (TallyQA Count; GQA otherwise). Not computed on audit bases. Matching, incremental validity, and the equivalence class \(\mathcal E_\epsilon\) use \(A^S\) only.

**Audit (frozen definitions, reconstructed from \(\pi\)).** Completeness is the triplet: all three variants must parse. Denominator for joint metrics is complete triplets; RA/II additionally condition on \(B=1\).

\[
\mathrm{PFC}=P(B=1\land R=1),\quad
\mathrm{PSC}=P(B=1\land I=1).
\]

\[
\mathrm{RA}=\mathrm{PFC_{cond}}=P(R=1\mid B=1),\quad
\mathrm{II}=\mathrm{PSC_{cond}}=P(I=1\mid B=1).
\]

\[
A^B=P(B=1)=\sum_{r,i}\pi_{1ri}.
\]

On the same audit population, \(\mathrm{PFC}=A^B\cdot\mathrm{RA}\) and \(\mathrm{PSC}=A^B\cdot\mathrm{II}\). Eight-state reconstruction of these four quantities is a machine check against canonical metrics, not a new endpoint.

**Downstream \(U\).** Best-of-N accuracy with frozen pools. Primary \(N=8\).

---

## 7. Experimental Setup

**Models.** Target eight systems, minimum six, covering at least four families (Qwen-VL, Gemma, Llama Vision, Molmo, plus specialized VL reward). All registry rows start UNTESTED. Compatibility debugging that exceeds about 40 minutes marks a checkpoint INCOMPATIBLE and substitutes a pre-listed backup. Default inference: bf16, Transformers, SDPA/eager. FlashAttention2, bitsandbytes, and CUDA custom kernels are not defaults.

**Hardware for the first GPU pass.** Two independent NVIDIA A800 80GB workers. Model-level parallelism only: worker 0 and worker 1 each run a disjoint model list and write separate resumable JSONL files.

**Protocol.** (1) Environment probe. (2) ~50-item compatibility probe covering four factors, three variants, and mixed candidate order. (3) Signal gate: 100 PASS triplets / factor (400 triplets, 1200 images). Diagnose floor, ceiling, or collapsed discrimination before full audit. (4) If the signal gate passes, full FAST_TRACK audit. (5) Factor-wise static, 200 items / factor (Count: TallyQA; others: GQA). (6) Factor-wise Best-of-N, 200 questions / factor, \(N=8\), shared pools.

**Natural-image construction.** GQA mapping (Attribute / Spatial / Presence) uses functional programs, type fields, and scene graphs; keyword fallback is recorded as low confidence. GQA Count is **not** invented: public GQA 1.2 questions yielded zero valid Count items under that mapping (**PRE-RESULT DATA AVAILABILITY ADAPTATION**). Count static and downstream therefore use TallyQA, image-disjoint subset A vs B, with gold \(\pm 1\) pairwise hard negatives and structured nearby-count N=8 pools. GQA and TallyQA splits are hashed by image id with asserted empty intersections. Natural distractors needed to fill GQA \(N=8\) are queued, never fabricated.

**Deferred.** VQA-v2, MMVP, image editing, and intervention-aware LoRA until P0 is complete. Extra TallyQA beyond the frozen Count 200+200 is not required for P0.

---

## 8. Statistical Analysis Plan

Independent variation is model \(\times\) factor, not image count. The bootstrap unit is the **model family**.

**RQ1.** Scatter \(A^S\) against RA/II (equivalently PFC/PSC). The **predeclared** accuracy-matched band is \(|\Delta A^S|\le 1\) pp. The confirmatory plan also logs \(2\) and \(3\) pp bands. Bands at \(0\), \(0.5\), and \(5\) pp are post-hoc sensitivity and do not replace the 1 pp rule. Report mean/median/max absolute RA/II/PFC gaps inside each band. Do not match on \(A^B\).

**RQ2.** Fit, **per downstream factor**, M0: \(U_f\sim A^S_f\) and M1: \(U_f\sim A^S_f+\mathrm{PFC}_f+\mathrm{PSC}_f\). Count \(U\) is TallyQA; Attribute/Spatial/Presence \(U\) is GQA. Do not pool raw utility. Confirmatory scores are leave-one-family-out MAE, RMSE, explained variance, and rank correlation, with family-clustered 95% CIs on \(\Delta\). In-sample \(R^2\) is diagnostic only.

**RQ3.** 4\(\times\)4 matrix of audit factor versus downstream factor. Within each column, the four \(D\) profiles predict the same \(U_f\). The published diagonal-versus-off-diagonal summary standardizes predictive contribution within each column before aggregation.

Null results are reported as such. Endpoints are not revised after seeing model rankings.

[TBD: RQ1 ACCURACY-MATCHED RESULT]

[TBD: Δ LOFO PERFORMANCE]

[TBD: BEST-OF-N TABLE]

[TBD: SPECIFICITY MATRIX RESULT]

---

## 9. Results

The confirmatory RQ2/RQ3 tables remain to be written from the frozen incremental-validity and specificity artifacts. The eight-state, flip, and \(A^S\)-equivalence displays below are post-hoc forensics of frozen Phase II audit triplets. They do not modify manifests, thresholds, or the predeclared 1 pp matching rule.

**Figure (candidate main empirical panel).** `rewardlens/paper/figures/fig_eight_state_sankey.pdf`

*Caption.* Eight-state structure of evidence dependence. (a) The object is \(\pi_{bri}=P(B=b,R=r,I=i)\). \(A^S\) is independent static accuracy; \(A^B=P(B=1)\) is audit-base accuracy; matching uses \(A^S\), never \(A^B\). RA collapses the \(R=1\) column of the \(B=1\) slice; II collapses the \(I=1\) row; \(\pi_{101}\) is the mass those two margins hide. (b) Qwen Attribute is a pure 111 flow: the judge adapts when gold flips and stays under the matched irrelevant edit. (c) Qwen Count has the same \(A^B=1\) and the same \(\mathrm{II}=1\), but \(\mathrm{RA}=0.17\): 166 of 200 triplets sit in 101. (d) \(\pi_{101}\) across eight models and four factors. Count (and Spatial for several models) is where RA/II as a pair lose the most structure. Predeclared matching remains \(|\Delta A^S|\le 1\) pp.

**Eight-state vs RA/II.** On Qwen Count, \(\pi_{101}=166/200\) and \(\pi_{111}=34/200\). RA reports only \(34/200=0.17\). InternVL Count is almost the same map (\(\pi_{101}=164\), \(\pi_{111}=36\)). Gemma Spatial is more extreme: \(\pi_{111}=\pi_{110}=0\), so \(\mathrm{RA}=0\), while \(\pi_{101}=143\). Attribute, by contrast, is near-pure 111 for several models. The eight-state is therefore not a cosmetic expansion of RA/II; it is the object those metrics project.

**Outcome correctness \(\neq\) behavioral stability.** On Qwen Count the relevant gold label flips on every triplet, yet the predicted letter is unchanged on 166 of 200 items (83%): correctness changes because gold moved, not because the judge updated. That is why \(\mathrm{RA}=0.17\) cannot be read as a 17% behavioral update rate; it is a correctness rate, and \(F_R=0.17\) happens to coincide with it only because every base decision was already correct. Gemma Spatial splits the two: \(\mathrm{RA}=0\) because all 146 base-correct items keep their letter, while \(F_R=0.27\) is entirely already-wrong items switching to the other wrong letter.

**Predeclared 1 pp matching (unchanged).** Accuracy-matched pairs are defined by \(|\Delta A^S|\le 1\) pp on the independent static set. That band contains 7 pairs, with median \(|\Delta\mathrm{RA}|=15.1\) pp and max \(38.6\) pp (Skywork vs Phi Spatial). Exact-zero \(|\Delta A^S|=0\) is a post-hoc slice: Phi vs LLaVA Attribute, \(|\Delta\mathrm{RA}|=15.1\) pp, so \(\mathrm{Diam}_D(\mathcal E_0)\) is already not zero. Other \(\epsilon\) are sensitivity only; they are not a new matching threshold.

[TBD: RQ1 ACCURACY-MATCHED PAIR TABLE]

[TBD: MODEL COMPATIBILITY TABLE]

[TBD: SIGNAL GATE DYNAMIC RANGE]

[TBD: CONTROLLED AUDIT TABLE]

[TBD: GQA STATIC A]

[TBD: GQA BON U]

---

## 4.1 Magnitude Matching

Relevant and irrelevant edits are constructed to have comparable visual magnitude: the same added or recolored object slot, matched shape/size/material (Count, Attribute, Presence), or the same world-space displacement (Spatial). Camera, lights, and unmatched objects are frozen inside a triplet. RGB mean-absolute difference is logged as a diagnostic, not as the definition of relevance. Semantic relevance is defined by whether the gold preference flips.

## 5.1 Factor-wise Static Construction

**PRE-RESULT DATA AVAILABILITY ADAPTATION.** GQA 1.2 public questions contain no usable Count programs under the pre-specified mapping. Count static items are TallyQA (200; prefer 100 simple / 100 complex), not invented GQA Count. Attribute, Presence, and Spatial static items are GQA.

GQA questions are mapped to Attribute, Presence, and Spatial using functional programs, GQA type fields, and scene graphs. Keyword fallback is recorded as low confidence and is not the primary mapping. Static items are pairwise preference examples: gold answer versus a structured hard negative (TallyQA count \(\pm 1\); GQA attribute substitution from the scene or palette; spatial inverse or yes/no flip; presence yes/no flip). Candidate order is deterministically shuffled. \(A^S_f\) is measured only on this factor-wise static set.

FAST-TRACK target: 200 items / factor (800 total). If a factor cannot reach 200 clean items, we report the maximum clean \(N\) and the reason. We do not fabricate questions.

## 5.2 Factor-wise Best-of-N Construction

Downstream questions are image-disjoint from static items **within source**. TallyQA Count subset B is disjoint from TallyQA Count subset A. GQA downstream is disjoint from GQA static. Split is hashed at `image_id`; any within-source intersection is a hard failure. Each question has a frozen \(N=8\) pool shared by all judges: one verified gold plus structured distractors (TallyQA: nearby nonnegative counts; GQA: factor-specific structured negatives and scene-graph alternatives). Natural-language distractors for GQA are queued in `natural_distractor_jobs.jsonl` and are never invented. Primary utility is Best-of-N accuracy at \(N=8\), analyzed factor-wise.

## 7.1 Model Evaluation Protocol

Every checkpoint starts UNTESTED. The first GPU wave is four families (a general MLLM, a second family, a third architecture, and a specialized VL reward model when compatible). Compatibility debugging that exceeds about 40 minutes marks the checkpoint INCOMPATIBLE and substitutes a listed backup. Default decoding: bf16, Transformers, SDPA or eager. FlashAttention2 is not required. Workers partition **by model** (`--num-workers N --worker-index K`), write independent JSONL, and merge by `item_id` with duplicate/conflict detection. Inference is append-only and resumable. Official runs set `HF_HUB_OFFLINE=1` after staging.

Signal Gate (100 PASS triplets / factor) is an engineering usability check: parse rate, no all-model floor or ceiling. It is **not** a requirement that RQ1–RQ3 be supported before FAST_TRACK proceeds.

## 10. Limitations (outcome-independent)

These limitations do not depend on GPU numbers and are stated now.

**Synthetic audit.** RewardLens-CLEVR isolates factor edits; it is not a natural-image VQA leaderboard. Transfer to TallyQA Count and GQA Attribute/Spatial/Presence is an empirical question (RQ2–RQ3), not an assumption.

**Matched but not photorealistic magnitude.** Slot/shape/size/material matching and a shared render seed constrain low-level change; they do not make the two edits identical in every pixel statistic.

**FAST_TRACK scale.** 200 PASS triplets / factor is the deadline-critical confirmatory audit. 500/factor is a robustness expansion and is not required to freeze P0 conclusions, but smaller \(N\) reduces precision of family-level bootstrap.

**Dataset split.** Count natural-image items are TallyQA because GQA 1.2 public questions yielded zero valid Count programs. Attribute/Spatial/Presence remain GQA. RQ2/RQ3 therefore treat \(U_f\) factor-wise and standardize within downstream-factor columns before aggregating specificity.

**GQA mapping residual error.** Program- and type-based mapping still admits ambiguous questions. We keep 50-per-factor human-QC lists; we do not silently upgrade low-confidence keyword rows.

**Candidate pools.** Presence admits few canonical answers (yes/no). Extra \(N=8\) slots use scene-graph names and same-factor vocabulary. Unfilled slots are queued, not hallucinated. Format-heterogeneous distractors can change the difficulty of Best-of-N relative to a yes/no-only pool.

**Model universe.** Eight systems and four-plus families are still a small cluster-bootstrap unit. Incompatible checkpoints are replaced rather than forced, which can shift the realized family set.

**No closed APIs / no paid GPU in this preparation.** Results will come from locally staged open checkpoints on A800-class GPUs.

Discussion of whether evidence dependence is an independent quality axis will be written after P0 numbers exist. It will not be filled with invented effect sizes.

[TBD: DISCUSSION AFTER RESULTS]
