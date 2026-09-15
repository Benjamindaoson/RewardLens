FOUR_MODEL_PAPER_CHECKPOINT = COMPLETE
RQ1_STATUS = SUPPORTED DESCRIPTIVELY
RQ2_STATUS = DESCRIPTIVE_ONLY / INSUFFICIENT_FOR_FORMAL_INFERENCE
RQ3_STATUS = INSUFFICIENT_EVIDENCE_NOT_IDENTIFIABLE_FOR_FOUR_MODELS
RQ3_IMPLEMENTATION_AUDIT = BUG_FOUND
STRONGEST_FINDING = Qwen and Skywork have similar macro A (0.8575 vs 0.8450) but PFC differs (0.7875 vs 0.8700).
STRONGEST_NUMERICAL_EVIDENCE = Similar-A pair delta A=0.0125, delta PFC=0.0825, delta PSC=0.0075, delta U8=0.0538.
MOST_IMPORTANT_COUNTEREXAMPLE = Factor-specific dependency patterns vary despite comparable static accuracy.
MOST_IMPORTANT_NULL_RESULT = Official four-model RQ3 is not identifiable; the unofficial 0.05725 diagonal/off-diagonal equality is an estimator identity, not a scientific null.
SAFE_ABSTRACT_CLAIM = Controlled dependency metrics reveal preliminary behavior differences not captured by static accuracy.
UNSAFE_CLAIM_DO_NOT_USE = PFC significantly predicts U@8 beyond A.
PAPER_STORY = Use RQ1 as the four-model result; use RQ2 as descriptive motivation; keep RQ3 pending expanded confirmation.

| Model | A | PFC | PSC | U2 | U4 | U8 |
|---|---:|---:|---:|---:|---:|---:|
| qwen3_vl_4b_instruct | 0.8575 | 0.7875 | 0.9988 | 0.9025 | 0.8050 | 0.6975 |
| gemma3_4b_it | 0.6050 | 0.4300 | 0.8125 | 0.8100 | 0.6413 | 0.4838 |
| molmo_7b_d_0924 | 0.6875 | 0.5213 | 0.7925 | 0.7550 | 0.5763 | 0.4725 |
| skywork_vl_reward_7b | 0.8450 | 0.8700 | 0.9913 | 0.9175 | 0.8363 | 0.7513 |
