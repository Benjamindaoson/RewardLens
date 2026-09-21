# Confirmatory Analysis Plan

**FROZEN BEFORE FULL MODEL RESULTS**

Frozen 2026-09-12 from the scientific source of truth, before any reward-model scores exist.

Deadline-first scale (operational, not an RQ change):

- Audit: FAST_TRACK_AUDIT_V1 = 200 PASS triplets / factor (800 total)
- Static A: 200 items / factor (800 total). Count = TallyQA; Attribute/Spatial/Presence = GQA
- Downstream U: 200 questions / factor (800 total), N=8. Same dataset assignment as static
- 500/factor CLEVR is P1 robustness if time allows

Later additions are exploratory unless this file is revised with a dated log entry.
Do not change endpoints after seeing model outputs.

## Primary RQs

### RQ1

Do similarly accurate multimodal reward models exhibit different factor-specific visual dependencies?

Test: accuracy-matched pairs with \(|\Delta A| \le 1, 2, 3\) percentage points. Look for material PFC/PSC gaps.

### RQ2 (most important)

Does factor-specific visual dependency add downstream predictive information beyond static preference accuracy?

RQ2 is **factor-wise**. Do not pool raw \(U\) across TallyQA Count and GQA Attribute/Spatial/Presence.

- Count outcome \(U_{\mathrm{count}}\): TallyQA
- Attribute outcome \(U_{\mathrm{attribute}}\): GQA
- Spatial outcome \(U_{\mathrm{spatial}}\): GQA
- Presence outcome \(U_{\mathrm{presence}}\): GQA

For each downstream-factor column \(f\):

- M0: \(U_f \sim A_f\)
- M1: \(U_f \sim A_f + \mathrm{PFC}_f + \mathrm{PSC}_f\)
- Confirmatory validation: leave-one-model-family-out (not in-sample \(R^2\))
- Uncertainty: family-level cluster bootstrap, 95% CI

### RQ3

Does dependency have factor-specific predictive validity?

Audit factor \(\times\) downstream factor matrix. Within each downstream-factor column \(f\), compare \(D_{\mathrm{count}}\), \(D_{\mathrm{attribute}}\), \(D_{\mathrm{spatial}}\), \(D_{\mathrm{presence}}\) as predictors of the **same** \(U_f\).

For the final diagonal-vs-off-diagonal summary, **standardize / normalize predictive contribution within each downstream-factor column** before aggregation. Do not compare raw TallyQA and GQA utility scales.

## Primary factors

Count, Attribute, Presence, Spatial.

If a factor cannot satisfy a clean matching/uniqueness contract, drop it from the primary 4-factor matrix and report why.

## Metric definitions (frozen)

Static \(A_f\) is computed on the factor-wise static set (Count: TallyQA-Static; Attribute/Spatial/Presence: GQA-Static). Never on RewardLens-CLEVR audit bases.

On controlled audit triplets:

\[
\mathrm{PFC}=P(\text{base correct}\land\text{relevant correct})
\]

\[
\mathrm{PSC}=P(\text{base correct}\land\text{irrelevant correct})
\]

\[
\mathrm{PFC_{cond}}=P(\text{relevant correct}\mid\text{base correct})
\]

\[
\mathrm{PSC_{cond}}=P(\text{irrelevant correct}\mid\text{base correct})
\]

Joint and conditional metrics are both retained.

## Primary downstream

- \(U(N=8)\) primary
- \(U(N=2), U(N=4)\) robustness (P1)

Same frozen N=8 candidate pools for all models.

## Data independence

\[
D_{\mathrm{audit}}\neq D_{\mathrm{static}}\neq D_{\mathrm{downstream}}
\]

Split static vs downstream by `image_id` **within each source**. GQA (Attribute/Spatial/Presence) intersection must be 0. TallyQA Count static ∩ downstream image ids must be 0. CLEVR audit is a third source.

## Bootstrap unit

Model family, not image instances.

## Decision rules

- RQ1 supported if accuracy-matched pairs show material PFC/PSC gaps at the pre-registered \(\Delta A\) bands.
- RQ2 supported / mixed / not supported from LOFO \(\Delta\) predictive performance and CI, not from a single p-value.
- RQ3 supported if diagonal \(>\) off-diagonal under the pre-registered matrix test.

Null results are valid. Do not claim preference accuracy is useless. The hypothesis is that it is informative but incomplete.

## Deferred (P2)

VQA-v2, MMVP, image editing, intervention-aware LoRA. Extra TallyQA beyond the frozen Count 200+200 is not required for P0. Only after P0 (audit, static, BoN, RQ1–RQ3).

---

## Dated log — 2026-09-12 — PRE-RESULT DATA AVAILABILITY ADAPTATION

**This is not a result-driven change.** No reward-model scores exist.

**Reason.** GQA 1.2 public questions yielded zero valid Count items under the pre-specified structural mapping (`count` programs, numeric answers, “How many”). Count items were not fabricated. The paper is not blocked on GQA Count.

**Frozen source split.**

| Factor | Static / Downstream source |
|---|---|
| Count | TallyQA |
| Attribute | GQA |
| Spatial | GQA |
| Presence | GQA |

**Analysis implications (pre-results).** RQ2 remains \(U_f\sim A_f\) vs \(U_f\sim A_f+\mathrm{PFC}_f+\mathrm{PSC}_f\). RQ3 specificity remains a within-column comparison of the four \(D\) predictors of the same \(U_f\). Diagonal-vs-off-diagonal aggregation uses within-column standardized predictive contribution. Raw TallyQA and GQA utility are not pooled or compared on a shared scale.

Original freeze above still holds except where this log supersedes GQA-only Count static/downstream.

---

## Dated log — 2026-09-12 — supplementary GQA-only 3-factor sensitivity (pre-results)

**Not a change to the primary confirmatory plan.** Pre-registered before GPU results.

Because Count static/downstream are TallyQA while Attribute/Spatial/Presence are GQA, factor identity and dataset source co-vary on Count. Within-column standardization does **not** remove that confound.

Supplementary sensitivity (report always; does not replace primary 4-factor RQ3):

- Drop Count.
- 3×3 Attribute / Spatial / Presence only.
- Same within-column standardization, then diagonal vs off-diagonal.

See `reports/DATA_SOURCE_CONFOUND_NOTE.md`.

---

## Dated log — 2026-09-16 — notation clarification (not an endpoint change)

**This does not change confirmatory endpoints, thresholds, or matching bands.**

Paper notation now writes the frozen static accuracy as \(A^S\) to distinguish it from audit-base accuracy \(A^B=P(B=1)\). Every occurrence of \(A\) in this file is \(A^S\). Matching remains \(|\Delta A^S|\le 1\) pp as the predeclared primary band; the \(2\) and \(3\) pp bands already logged above are unchanged. Eight-state distributions \(\pi_{bri}\), prediction-flip decompositions, Sankey figures, and \(\varepsilon\in\{0,0.5,5\}\) pp slices are post-hoc forensics of frozen Phase II artifacts. They do not replace PFC/PSC confirmatory endpoints and they do not retarget RQ1 onto \(A^B\).

\(\mathrm{RA}=\mathrm{PFC_{cond}}\), \(\mathrm{II}=\mathrm{PSC_{cond}}\), \(D=(\mathrm{RA},\mathrm{II})\).

---

## Dated log — 2026-09-16 — paper_v2 RQ freeze (not a data collection change)

The **paper** primary questions are now:

1. Identification: does \(A^S_f\) identify \(D_f=(\mathrm{RA}_f,\mathrm{II}_f)\)?
2. Empirical equivalence: exact/near \(A^S\) ties with material \(\lvert\Delta\mathrm{RA}\rvert\).
3. Behavioral decomposition: eight-state \(\pi_{bri}\) and prediction flips \(F_R,F_I\).

Best-of-N incremental validity and the factor-specificity matrix remain available as **secondary / historical confirmatory analyses**. They are not the life of `iclr2027_paper_v2.md`. Pair-graph remains exploratory.

Matching language in the paper is **predeclared** \(|\Delta A^S|\le 1\) pp. Do not write *preregistered*.

No additional models, factors, or benchmarks. Human intervention-validity audit remains the only P0 data still worth collecting; if incomplete, it is a limitation. Do not fabricate labels.
