# RewardLens Scientific Contract

Source of truth:

`d:\发表\ICLR\Multimodal Reward Model\Do Multimodal Reward Models Rely on the Right Visual Evidence_ — 完整研究方案.md`

The execution prompt is an execution contract, not a license to change the research questions.

If the two documents conflict: log the conflict in `EXPERIMENT_LOG.md`. Do not rewrite RQs. Prefer:

1. data independence
2. intervention matching
3. confirmatory analysis freeze
4. no fabricated results

## Mother question

Do Multimodal Reward Models Rely on the Right Visual Evidence?

Carrier: multimodal reasoning reward / judge

\[
r_m(I, q, y)
\]

Image editing is secondary external validation only. OCR and video are not primary.

## Research questions

- **RQ1.** Do similarly accurate models exhibit different factor-specific visual dependencies?
- **RQ2.** Does factor-specific visual dependency add downstream predictive information beyond static preference accuracy?
- **RQ3.** Is that predictive validity factor-specific (diagonal > off-diagonal)?
- **RQ4.** Optional intervention-aware training, only if RQ1–RQ3 support it.

## Primary factors

Count, Attribute, Spatial, Presence.

## Data independence

\[
D_{\text{static}} \neq D_{\text{audit}} \neq D_{\text{downstream}}
\]

- Audit: RewardLens-CLEVR controlled triplets. Not ordinary CLEVR benchmark items.
- Static accuracy \(A^S\): independent factor-wise static pairwise items (Count: TallyQA; Attribute/Spatial/Presence: GQA). Not audit base images.
- Downstream U: factor-wise Best-of-N, image-disjoint from static within source. Count is TallyQA; others are GQA.
- Prefer different sources when possible (CLEVR audit vs natural-image static/downstream).

## Metrics

Keep joint and conditional, do not collapse early:

- \(A^S_{mf}\) (written \(A_{mf}\) in the original freeze)
- \(A^B_{mf}=P(B=1)\) on audit triplets (diagnostic; not a matching variable)
- PFC, PSC
- RA \(=\) PFC_cond, II \(=\) PSC_cond

Primary incremental model:

\[
U \sim A^S \quad\text{vs}\quad U \sim A^S + \mathrm{PFC} + \mathrm{PSC}
\]

Notation: \(A^S\) is independent static accuracy (the \(A\) of the frozen confirmatory plan). \(A^B=P(B=1)\) is audit-base accuracy and is never used for matching. \(\mathrm{RA}=\mathrm{PFC_{cond}}\), \(\mathrm{II}=\mathrm{PSC_{cond}}\), \(D=(\mathrm{RA},\mathrm{II})\).

Primary downstream N = 8; N = 2, 4 robustness.

Bootstrap unit: model family, not image instances.

## Matching

Relevant and irrelevant interventions must be magnitude-matched. Magnitude metadata does not define semantic relevance; it only checks \(\Delta_{rel} \approx \Delta_{irr}\).

## Claims policy

Do not claim preference accuracy is useless. The hypothesis is that it is informative but incomplete.

Do not fabricate PASS, missing numbers, or model scores. Null results are valid outcomes.
