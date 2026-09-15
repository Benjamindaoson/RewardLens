# RewardLens: Auditing Visual Evidence Dependence in Multimodal Reward Models

## Abstract

Multimodal reward and judge models are usually evaluated by whether they choose the preferred answer. That accuracy does not reveal whether the model relied on the intended visual evidence. RewardLens introduces a controlled visual dependency audit: for each example, we compare model behavior under a base image, a relevant visual intervention, and an irrelevant visual intervention, producing preservation under faithful change (PFC) and preservation under spurious change (PSC). In a four-model preliminary checkpoint covering Qwen, Gemma, Molmo, and Skywork, conventional static accuracy fails to identify evidence dependence. Qwen and Skywork differ by only 1.25 percentage points in macro static accuracy (0.858 vs. 0.845), yet differ by 8.25 points in PFC (0.787 vs. 0.870) and 5.38 points in U@8 downstream Best-of-N utility (0.698 vs. 0.751). PFC and PSC show stronger descriptive association with downstream utility than static accuracy in this checkpoint, but four models are insufficient for confirmatory incremental-validity regression. Expanded 6-8 model experiments are reserved for confirmatory RQ2/RQ3 analysis.

## 1. Introduction

Preference accuracy is a blunt instrument for multimodal reward evaluation. A model can choose the preferred answer while relying on the wrong visual cue, or it can appear equally accurate to another model while using a very different evidence path. This matters because reward and judge models increasingly drive selection, reranking, and supervision pipelines: if the reward signal is right for the wrong reason, downstream optimization may amplify the wrong behavior.

RewardLens asks a narrower question than general VLM accuracy: does the model's judgment depend on the visual evidence that should matter for the preference? We evaluate this by freezing four visual factors in a fixed order: Count, Attribute, Spatial, and Presence. For each factor, controlled interventions distinguish changes that should affect the judgment from changes that should not.

The current four-model checkpoint supports the central claim that static preference accuracy is not sufficient to characterize visual evidence dependence. It does not yet support a formal claim that dependency adds independent predictive value beyond accuracy; that test is reserved for the expanded 6-8 model analysis.

## 2. Related Work

RewardLens sits at the intersection of multimodal reward modeling, controlled robustness evaluation, and causal-style behavioral audits. Prior reward-model evaluation often reports agreement with human or benchmark labels. VLM robustness work probes sensitivity to image perturbations or counterfactual changes. RewardLens differs by measuring factor-specific evidence dependence under a frozen preference protocol, then linking those dependency measurements to downstream Best-of-N selection utility.

The closest conceptual relatives are counterfactual evaluation and shortcut-learning audits. The key distinction is that RewardLens separates relevant and irrelevant visual interventions and reports both PFC and PSC, rather than treating all sensitivity as either good or bad.

## 3. Method

For each model m and factor f, RewardLens evaluates three judgments over matched examples: the base case, a relevant intervention, and an irrelevant intervention. Static accuracy A is measured independently on the frozen D_static set. Downstream utility U@N is measured by Best-of-N selection over frozen downstream pools, with N=8 primary and U@2/U@4 derived from the same N=8 graph.

PFC is the probability that the model is correct on the base case and remains correct under the relevant intervention. PSC is the probability that the model is correct on the base case and remains correct under the irrelevant intervention. Conditional variants PFC_cond and PSC_cond condition on base correctness. The frozen downstream protocol uses Copeland/scalar-equivalent selection, fixed pair orientation, fixed tie behavior, no semantic re-query, and no dropped pools.

## 4. Experimental Setup

The four-model preliminary checkpoint contains Qwen3-VL-4B-Instruct, Gemma-3-4B-it, Molmo-7B-D-0924, and Skywork-VL-Reward-7B. Each model is evaluated on 800 static examples, 2400 audit examples, and 800 downstream pools. Count uses TallyQA as carrier data; Attribute, Spatial, and Presence use GQA. All reported four-model cross-model conclusions are preliminary and descriptive.

Expanded models continue in the background. Their role is confirmatory: [EXPANDED RQ2 CONFIRMATORY RESULT], [EXPANDED RQ3 RESULT], [FAMILY BOOTSTRAP], and [LEAVE-ONE-FAMILY-OUT].

## 5. Results

### 5.1 Controlled interventions expose heterogeneous visual dependencies

Table 1 shows the four-model macro results. Static accuracy and visual dependency do not move in lockstep.

| Model | A | PFC | PSC | U@2 | U@4 | U@8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen | 0.858 | 0.787 | 0.999 | 0.902 | 0.805 | 0.698 |
| Gemma | 0.605 | 0.430 | 0.812 | 0.810 | 0.641 | 0.484 |
| Molmo | 0.688 | 0.521 | 0.792 | 0.755 | 0.576 | 0.473 |
| Skywork | 0.845 | 0.870 | 0.991 | 0.917 | 0.836 | 0.751 |

The cleanest current example is Qwen versus Skywork. Qwen has A=0.858 and Skywork has A=0.845, a difference of 0.0125. Yet Skywork has PFC=0.870 versus Qwen's PFC=0.787, a difference of 0.0825. Their downstream U@8 also differs: 0.751 for Skywork versus 0.698 for Qwen. The safe interpretation is association, not causality: near-equal static accuracy can conceal materially different relevant-evidence dependence.

### 5.2 Factor-specific results

Table 2 gives the full factor-level checkpoint. The strongest visual result is not a single global ordering; it is a profile. Qwen is extremely high on Attribute, Spatial, and Presence PFC, but low on Count PFC. Gemma and Molmo show larger factor variation, especially on Spatial. Skywork is consistently high across Attribute, Spatial, and Presence and stronger than Qwen on Count PFC.

| Model | Factor | A | PFC | PSC | PFC_cond | PSC_cond | U@8 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen | Count | 0.915 | 0.170 | 1.000 | 0.170 | 1.000 | 0.665 |
| Qwen | Attribute | 0.820 | 1.000 | 1.000 | 1.000 | 1.000 | 0.745 |
| Qwen | Spatial | 0.800 | 0.985 | 1.000 | 0.985 | 1.000 | 0.680 |
| Qwen | Presence | 0.895 | 0.995 | 0.995 | 1.000 | 1.000 | 0.700 |
| Gemma | Count | 0.385 | 0.235 | 0.635 | 0.324 | 0.876 | 0.335 |
| Gemma | Attribute | 0.725 | 0.890 | 0.910 | 0.952 | 0.973 | 0.575 |
| Gemma | Spatial | 0.560 | 0.000 | 0.715 | 0.000 | 0.979 | 0.525 |
| Gemma | Presence | 0.750 | 0.595 | 0.990 | 0.601 | 1.000 | 0.500 |
| Molmo | Count | 0.625 | 0.095 | 0.495 | 0.186 | 0.971 | 0.525 |
| Molmo | Attribute | 0.670 | 0.955 | 0.955 | 0.990 | 0.990 | 0.500 |
| Molmo | Spatial | 0.660 | 0.295 | 0.735 | 0.399 | 0.993 | 0.340 |
| Molmo | Presence | 0.795 | 0.740 | 0.985 | 0.744 | 0.990 | 0.525 |
| Skywork | Count | 0.760 | 0.625 | 0.985 | 0.628 | 0.990 | 0.610 |
| Skywork | Attribute | 0.930 | 1.000 | 1.000 | 1.000 | 1.000 | 0.865 |
| Skywork | Spatial | 0.845 | 0.860 | 1.000 | 0.860 | 1.000 | 0.695 |
| Skywork | Presence | 0.845 | 0.995 | 0.980 | 1.000 | 0.985 | 0.835 |

### 5.3 Visual dependency and downstream Best-of-N utility

Four-model RQ2 is descriptive only. The saturated model U ~ A + PFC + PSC has no meaningful residual degrees of freedom with four observations, so we do not report it as evidence. Descriptively, PFC and PSC are more strongly associated with U@8 than static accuracy in this checkpoint: Pearson correlations are A vs U@8 = 0.934, PFC vs U@8 = 0.978, and PSC vs U@8 = 0.983. Spearman correlations are 0.600, 0.800, and 0.800, respectively.

This supports a hypothesis worth testing, not a confirmatory conclusion: PFC/PSC may contain downstream-relevant information beyond ordinary static accuracy.

### 5.4 RQ3 factor specificity

RQ3 is not yet estimable at the four-model checkpoint. An independent implementation audit found that the unofficial 0.05725 diagonal/off-diagonal equality is a bug in a saturated in-sample OLS path: M1 interpolates four observations with four parameters, so cell contributions collapse to column-only M0 RMSE and the two means agree by identity. That number is not a scientific null. Input construction is otherwise correct (factor-specific PFC/PSC on rows, factor-specific A/U@8 on columns, 4 diagonal and 12 off-diagonal cells). The frozen LOFO estimator cannot fit M1 with four families because each fold trains on only three observations for four parameters. Official status: INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS.

### 5.6 Expanded-model metrics checkpoint

Seven models currently have complete A/PFC/PSC/U@N. InternVL3 has complete static and audit metrics; U@2/U@4/U@8 remain pending until the live downstream job writes `completion.json`. These expanded numbers are recorded for the paper ledger only. They are not used for confirmatory RQ2/RQ3 until all eight receipts exist.

| Model | Status | A | PFC | PSC | U@2 | U@4 | U@8 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen | COMPLETE | 0.8575 | 0.7875 | 0.9988 | 0.9025 | 0.8050 | 0.6975 |
| Gemma | COMPLETE | 0.6050 | 0.4300 | 0.8125 | 0.8100 | 0.6413 | 0.4838 |
| Molmo | COMPLETE | 0.6875 | 0.5213 | 0.7925 | 0.7550 | 0.5763 | 0.4725 |
| Skywork | COMPLETE | 0.8450 | 0.8700 | 0.9913 | 0.9175 | 0.8363 | 0.7513 |
| Idefics3 | COMPLETE | 0.7525 | 0.8062 | 0.9750 | 0.8525 | 0.7438 | 0.5963 |
| Phi-3.5-Vision | COMPLETE | 0.8020 | 0.5188 | 0.8588 | 0.8725 | 0.7388 | 0.6050 |
| LLaVA-OneVision | COMPLETE | 0.8150 | 0.8088 | 0.9763 | 0.9138 | 0.7963 | 0.6475 |
| InternVL3 | RUNNING | 0.7575 | 0.7738 | 1.0000 | pending | pending | pending |

Do not interpret InternVL PFC/PSC against downstream utility until U@N is complete.

### 5.5 Robustness and diagnostics

U@2, U@4, and U@8 have the same broad ranking pattern: Skywork and Qwen lead, while Gemma and Molmo trail. No four-model p-value or saturated regression is used as a headline result. Abstention rates in the four-model checkpoint are zero in the current canonical summary.

## 6. Discussion

The strongest paper story today is simple: accuracy is not evidence dependence. RewardLens turns this from an intuition into a measurable audit. A reward model can look competitive on static preference accuracy while relying less on the relevant visual factor, and this difference coincides with downstream utility differences in the preliminary checkpoint.

The secondary story is promising but unresolved. PFC and PSC track U@8 descriptively better than static accuracy across four models, but the experiment needs 6-8 models to support an incremental-validity claim. RQ3 is even stricter: factor specificity should not be claimed until the expanded analysis makes the frozen matrix estimable.

## 7. Limitations

The four-model checkpoint is preliminary. It is enough to motivate the paper and support RQ1, but not enough for formal cross-model regression. Count also uses a different carrier dataset from the other factors, so column standardization is necessary and does not remove all source confounding. The expanded experiment is required before making confirmatory RQ2 or RQ3 claims.

## 8. Conclusion

RewardLens shows that conventional static preference accuracy is not sufficient to characterize multimodal reward-model visual evidence dependence. The four-model checkpoint reveals clear heterogeneity in PFC/PSC profiles, including near-accuracy-matched models with materially different relevant-evidence dependence. The downstream association is encouraging but remains descriptive. The expanded 6-8 model run will determine whether visual dependency provides independent predictive value and whether that relationship is factor-specific.
