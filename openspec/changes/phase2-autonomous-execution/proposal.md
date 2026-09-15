# Remote Phase II autonomous execution

Use GNU screen phase2_gpu on autodl-container-47bb4a8b0c-371e5795.
Only READY_FOR_PHASE2_GPU.json with boolean ready_for_phase2_gpu=true authorizes formal execution.
Require downstream hash 0afb6dfefd7a47e3dc47fd05127e82d5fd260943d04e5c5cc3117ae11055133c and static hash 6e4a23fc54d4704e70587b177586152e6e63b7a4dac5964e7e16f56395e682e3.
No downloads; local checkpoints; HF_HUB_OFFLINE=1 and TRANSFORMERS_OFFLINE=1.
Reuse existing static run_items and accuracy_from_static without changing status filtering. Report parse-error denominator separately.
Reuse frozen pool_candidates, evaluate_pairwise_graph, scalar_pair_graph and derive_subset_selections without changes.
Use durable journals, immutable per-model completion receipts, fingerprint-bound resume, and per-model subprocesses.
Results belong under shared results/phase2/gpu_4model_v1 because the final READY gate has passed.
Do not overwrite existing audit results. Read contract_metrics.json PFC/PSC; never substitute audit base accuracy for static A.
RQ2: per-factor U~A versus U~A+PFC+PSC, leave-one-model-family-out, no pooled raw U.
RQ3 matrix: per target factor, contribution of the source factor's PFC/PSC block is M0 MAE minus M1 MAE under the same family folds. Standardize within target column using existing factor_specificity only when estimable. This reporting construction is declared before Phase II outcomes; it adds no alternative estimator.
Four-model M1 LOFO fits have three training observations and four parameters: all such contributions are unidentifiable. Emit null cells with reasons and explanatory plots; no significance testing or outcome-tuned estimator.
Decision: BORDERLINE when insufficient/underidentified evidence, NO-GO for invalid data/protocol, GO only after adequate family/model coverage and independently interpretable positive evidence. Four-model data cannot meet confirmatory minimum 6, target 8, >=4 families.
Acceptance: successful remote test suite, preflight, screen process, and independently observed durable judgments. Full scientific completion is separate from launch.
