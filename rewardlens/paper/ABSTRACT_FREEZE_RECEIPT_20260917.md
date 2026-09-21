# RewardLens — Abstract Freeze Receipt

**Status:** Abstract v1 story frozen; evidence wording may change only in response to newly completed validation evidence.  
**Receipt date:** 2026-09-17 (UTC+08:00)  
**Repository target:** `Benjamindaoson/RewardLens`  
**Intended path:** `rewardlens/paper/ABSTRACT_FREEZE_RECEIPT_20260917.md`

> This receipt records the manuscript story and submission-facing metadata at the current freeze point.  
> It is **not** evidence that the 1 percentage-point matching rule was preregistered or predeclared before results were observed.

---

## 1. Frozen Title

**RewardLens: Same Static Accuracy, Different Intervention Behavior in Multimodal Judges**

Chinese working title:

**RewardLens：相同静态准确率下，多模态评判模型呈现不同干预行为**

---

## 2. Frozen TL;DR

> **Static preference accuracy can fail to distinguish multimodal judges that behave differently under controlled visual changes; RewardLens exposes this gap through relevant and irrelevant interventions.**

---

## 3. Abstract v1 — Story Frozen

Static preference accuracy can fail to distinguish multimodal judges that behave differently under controlled changes in visual evidence. We introduce **RewardLens**, a behavioral audit that evaluates each judge on an independent static preference set and on a separate controlled intervention audit while holding the question and candidate responses fixed. Relevant edits are constructed to change the correct choice, whereas irrelevant edits are constructed to preserve it. Among audit cases judged correctly on the base image, RewardLens measures **Relevant Adaptation (RA)**, correctness after a relevant edit, and **Irrelevant Invariance (II)**, correctness after an irrelevant edit.

RewardLens asks whether an independent static score is sufficient to distinguish factor-specific intervention behavior. Across eight multimodal judges and four visual factors, equal or near-equal measured static accuracies can coexist with substantial differences in relevant adaptation. On Attribute, Phi-3.5-Vision and LLaVA-OneVision both achieve 80.5% measured static accuracy, yet differ in RA by 15.1 percentage points. Under our primary within-factor matching rule of static accuracies within one percentage point, seven qualifying within-factor model-pair comparisons have a median RA gap of 15.1 points.

The difference is concrete: in Qwen’s Count audit, 166 of 200 base-correct triplets (83.0%) become incorrect after a relevant edit because the correct choice changes while the judge retains its original prediction. In these cases, **invariance is the failure**. RewardLens complements static preference accuracy by revealing differences in measured intervention behavior that conventional static evaluation can fail to distinguish.

---

## 4. Submission-Facing Metadata Freeze

### Keywords

- multimodal judge evaluation
- reward model evaluation
- preference evaluation
- interventional evaluation
- behavioral auditing

### Primary Area

**applications to computer vision, audio, language, and other modalities**

### AI Assistance selections

Current intended disclosure selections:

- Yes, to aid or polish writing.
- Yes, for retrieval and discovery (e.g., finding related work).
- Yes, for research ideation or execution.
- Yes, to draft sections of the paper.
- Yes, for proving mathematical claims.

Not selected unless independently verified as applicable:

- Yes, for generating synthetic datasets.
- Yes, but for none of the above purposes.
- No, not at all.

### License

**CC BY 4.0**

### Reciprocal reviewing

Current form state:

- No author has a qualifying publication on the approved venue list.
- Reciprocal-review exemption path: **all authors are unqualified**.
- Recent Qualifying Paper checkbox: **not selected**.

### LLM feedback

- Google PAT / “Ready for LLM Feedback”: **not requested at this freeze point**.
- PDF status at freeze point: **not yet uploaded**.

---

## 5. Evidence Status at Freeze

### 5.1 Exact measured static-accuracy tie

Attribute:

- Phi-3.5-Vision measured static accuracy: **80.5%**
- LLaVA-OneVision measured static accuracy: **80.5%**
- Primary RA gap, Phi − LLaVA: **−15.05 percentage points**
- Displayed abstract value: **15.1 percentage points**

Interpretation:

> The independent static evaluation score fails to distinguish these two evaluated judges, while the intervention audit does.

### 5.2 Shared-base-correct sensitivity

Phi–LLaVA, Attribute:

- Shared complete audit triplets: **200 / 200**
- Shared base-correct support: **186 triplets**
- Shared-support RA, Phi: **84.95%**
- Shared-support RA, LLaVA: **100.00%**
- Shared-support RA gap, Phi − LLaVA: **−15.05 percentage points**
- Paired-bootstrap 95% CI: **[−20.43, −10.22] percentage points**

Interpretation:

> The headline RA gap is unchanged on exactly the same base-correct support and is not explained by different judge-specific base-correct subsets.

### 5.3 Primary within-factor 1 percentage-point census

- Qualifying within-factor model-pair comparisons: **7**
- Primary median absolute RA gap: **15.05 percentage points**
- Abstract display value: **15.1 percentage points**

**Wording restriction:** the rule may be called **primary**, but not **predeclared** or **preregistered**. No results-before immutable provenance receipt has been found.

### 5.4 Matching-band sensitivity

Completed as a descriptive robustness analysis across examined static-accuracy tolerances.

This analysis supports the statement that closely matched measured static accuracies can coexist with nontrivial dispersion in relevant adaptation.

It does **not** authorize:
- IID significance tests over comparison rows;
- an asymptotic claim as tolerance approaches zero;
- retrospective use of “predeclared”.

### 5.5 Qwen Count concrete failure mode

- Base-correct Count triplets: **200**
- Relevant-edit failures with retained original prediction: **166 / 200**
- Rate: **83.0%**

Permitted interpretation:

> When the correct choice changes under a relevant edit but the judge retains its original prediction, invariance itself constitutes failure.

### 5.6 Shared-support negative / sensitivity result to retain

Molmo–Phi, Count:

- Primary RA gap, Molmo − Phi: **−1.37 percentage points**
- Shared-support RA gap, Molmo − Phi: **+13.00 percentage points**
- Shared support: **100 triplets**
- Paired-bootstrap 95% CI: **[+5.00, +21.00] percentage points**

Required reporting principle:

> Primary judge-specific RA and common-support pairwise sensitivity are complementary estimands and must be reported side by side; shared-support analysis does not replace the frozen primary RA definition.

### 5.7 Human intervention validity

**Status: P0 pending**

No completed dual-human intervention-validity audit was available at this freeze point.

Therefore the manuscript must continue to say:

> **Relevant edits are constructed to change the correct choice, whereas irrelevant edits are constructed to preserve it.**

Do not upgrade this to an externally validated factual claim until real human annotation results exist.

---

## 6. Scientific Claim Boundary

### Frozen core claim

> **Independent static preference evaluation can fail to distinguish multimodal judges with different factor-specific intervention behavior.**

### Permitted formal statement

> Static preference accuracy does not, by itself, identify factor-specific intervention behavior on the evaluated judge class without additional assumptions connecting the static and intervention environments.

### Not claimed

RewardLens does **not** claim that:

- it directly identifies internal visual grounding;
- it proves which pixels, objects, representations, or attention mechanisms caused a judgment;
- RA or II universally outperform static accuracy for downstream Best-of-N prediction;
- all accuracy-matched model pairs exhibit large RA gaps;
- the 1 percentage-point rule was preregistered or predeclared;
- human intervention validity has already been established;
- static and intervention evaluations arise from the same data distribution;
- shared-support RA replaces the primary judge-specific RA estimand.

---

## 7. Allowed Changes After This Freeze

The **story, title, TL;DR, and contribution hierarchy are frozen**.

The Abstract may change only locally in response to:

1. completed real human intervention-validity evidence;
2. newly discovered results-before provenance for the 1 percentage-point primary matching rule;
3. correction of a verified numerical or experimental-integrity error.

The following are **not** valid reasons to rewrite the story:

- stylistic preference;
- desire for a more dramatic title;
- a new exploratory result;
- restoring downstream predictive-superiority framing;
- restoring internal-grounding or mechanism claims;
- replacing independent static accuracy with audit-base accuracy.

---

## 8. Provenance Notes

Current derived robustness artifacts reported by the experiment-side audit:

```text
/root/autodl-fs/RewardLens/results/phase2/final_data_forensics/
├── shared_support/
│   ├── shared_base_correct_sensitivity.csv
│   └── shared_base_correct_sensitivity.json
└── equivalence/
    └── accuracy_equivalence_curve.csv
```

Reported SHA256 values at this freeze point:

```text
shared_base_correct_sensitivity.csv
d3d2d9c0608e0fa726e6a529aabf3779afef3ff52e480853c160f981e22635d4

accuracy_equivalence_curve.csv
063264cda2a8310dfc4448cf8c1755641b8a96a3a92f66760f2ea370ebef0e67

rewardlens_final_data_forensics.py
df591f5e7c0c35b1c3709f314e5fa184c485fd304e9cd1cd2cc07654927c49b5
```

These are derived-only forensic artifacts. No GPU inference was rerun, and frozen main experiment outputs/manifests were not modified according to the experiment-side verification.

---

## 9. Anonymity / Submission Note

This repository must **not** be linked from the anonymous ICLR submission if the link reveals author identity. ICLR 2027 requires the paper and supplementary material to remain anonymous. Use an anonymous repository or anonymized supplementary code for reviewer-facing artifacts.

---

## 10. Freeze Status

```text
TITLE = FROZEN
TLDR = FROZEN
ABSTRACT_V1_STORY = FROZEN

PHI_LLAVA_EXACT_TIE = VERIFIED
PHI_LLAVA_COMMON_SUPPORT = VERIFIED
SHARED_BASE_SENSITIVITY = COMPLETE
MATCHING_BAND_SENSITIVITY = COMPLETE
PHI_LLAVA_PAIRED_UNCERTAINTY = COMPLETE

PRIMARY_1PP_RULE = VERIFIED_AS_ANALYSIS_RULE
PREDECLARED_WORDING = NOT_AUTHORIZED

HUMAN_INTERVENTION_VALIDITY = P0_PENDING
```

---

**End of receipt.**
