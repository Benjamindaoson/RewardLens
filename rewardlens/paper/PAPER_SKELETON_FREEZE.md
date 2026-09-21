# Paper skeleton freeze — 2026-09-16

Superseded as source of truth by `PAPER_BLUEPRINT.md`. Keep this file only as a short pointer.

Active English draft: `iclr2027_paper_v2.md`
Chinese Section 3 母稿: `section3_measurement_framework_zh.md`
Formal proofs: `section3_theorems_and_proofs.md`

**Title.** RewardLens: Same Accuracy, Different Visual Evidence Dependence in Multimodal Judges

**Theory (2026-09-16 upgrade).** Theorem 1: \(D_f\) is identified by \(A^S_f\) iff \(D_f\) is constant on every accuracy fiber \(\mathcal F_f(a)\). Proposition 2: any accuracy-only reconstruction of RA errs \(\ge\delta/2\) on an exact tie (Attribute \(\delta=15.1\) pp \(\Rightarrow\) \(7.55\) pp). Proposition 3: sharp Fréchet bounds for \(q_{11}\) given \((RA,II)\). Lemma 4: \(\Delta C_X=\Delta Y_X\oplus\Delta G_X\). Full proofs: `section3_theorems_and_proofs.md`. Matching is within-factor. Equivalence class \(\mathcal E_{f,\epsilon}\) is a tolerance neighborhood of exact fibers. Predeclared band is \(\epsilon=1\) pp. Never write *preregistered*. Edits are **design-matched**, not claimed pixel-magnitude-matched.

**Primary RQs.** Identification; empirical equivalence; behavioral decomposition.

**Secondary.** Best-of-N diagnostic. Pair-graph exploratory.

**Do not collect.** Ninth model; new benchmark; new factor; regenerated main experiment; Audit↔BoN item join; new matching threshold; pair-graph as a main line; model-level RQ2 regression as the paper's life support.

**May still collect.** Human intervention-validity audit (P0). Orientation swap (P1, appendix). Hugging Face metadata corrections (this directory's sibling `artifact_metadata_correction/`).

**Human labels.** If the dual-annotator audit is incomplete, keep it a limitation. Do not fabricate. Do not substitute a model.
