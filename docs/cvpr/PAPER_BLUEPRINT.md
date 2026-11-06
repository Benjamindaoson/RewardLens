# CVPR-oriented RewardLens — falsifiable paper blueprint

**Do not submit this as a finished manuscript.** All main results below are open hypotheses, not confirmed experiments.

## Working title

RewardLens: Counterfactual Visual Grounding for Reliable Multimodal Judges

## Candidate abstract (research *proposal*, NOT result claims)

Current multimodal reward benchmarks largely score judges on fixed input-response pairs, while a judge's practical reliability also depends on whether its preference changes appropriately when task-critical visual evidence changes. Existing perturbation benchmarks have shown related failures, yet it remains unclear whether evidence-reliance measurements can predict which judges will fail under visual distribution shift beyond conventional held-out accuracy and existing sensitivity/stability metrics. We propose RewardLens-VG, a visual-grounding audit that combines matched relevant and irrelevant image interventions with bidirectional preference controls, independent semantic validation, and out-of-family downstream evaluation. Our study will test two falsifiable hypotheses: (i) task-conditional counterfactual behavior offers incremental predictive information about held-out multimodal judging failures, and (ii) using this information for judge selection reduces downstream choice regret under matched evaluation costs. The proposed experiments span controlled visual reasoning, natural-image judging and open-ended visual preferences, with direct comparisons against static, pairwise counterfactual and multimodal bias baselines. The paper's conclusions will depend on independent empirical validation; no improvement is asserted by this proposal.

## Eight-page narrative budget (preliminary)

1. Introduction / specific visual failure and central falsifiable hypothesis (0.9 p).
2. Closest prior work and novelty boundary (0.5 p).
3. Problem definition: visual evidence reliance, shift loss, cost-adjusted regret (1.0 p).
4. Verified intervention protocol and human-quality control (1.4 p).
5. Cross-family OOD prediction and fair comparisons (1.1 p).
6. Best-of-N and selection-regret validation (1.0 p).
7. Controlled results, ablations, negative results (1.5 p).
8. Limitations and conclusion (0.6 p).

Do not use artificial figures to imply completed experiments. Potential figures: paired real visual edits; perceptual label validation; out-of-family delta MAE; matched-cost selection regret; failure analysis.

## Required controls before making contribution claims

- VisualFLIP pair accuracy and fixed-question evidence change.
- MM-JudgeBias sensitivity/stability under comparable perturbations.
- Multimodal RewardBench 2 test-to-utility connection.
- Difficultly- and annotation-budget-matched static baselines.
- Real visual-human labels, edit artifact controls, label-direction controls.
- No source-level leakage, no test-guided feature engineering.
- Equal *total* cost includes audit set annotation, model inference, and selection.

## Clear stop condition

If independent, family-held-out predictive advantage is absent, remove H1/H2 and do not claim that more intervention score measurements constitute a new CVPR methodology. Disclose all negative and ambiguous results.

## Submission integrity

The ICLR 2027 RewardLens manuscript is under concurrent review; a substantially similar CVPR 2027 submission is prohibited. CVPR 2027 deadline: Nov 10 abstract/enrollment and Nov 16 full paper, AOE. Coordinate a venue choice with all authors; no submission or withdrawal has been performed.
