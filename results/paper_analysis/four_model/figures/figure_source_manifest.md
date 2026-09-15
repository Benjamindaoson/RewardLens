# Four-model figure check (no redraw)

Checked 2026-09-15 on 017. Existing figures were left in place.

| Figure | PDF | PNG | Canonical source | Caption overclaim |
| --- | --- | --- | --- | --- |
| figure2_dependency_fingerprint | present | present | four_model_paper_checkpoint/four_model_factor_table.csv | no redraw; keep descriptive |
| figure3_accuracy_vs_pfc | present | present | four_model_main_table.csv (A vs PFC) | no redraw; Qwen/Skywork near-A contrast is descriptive |
| figure4_utility | present | present | four_model_main_table.csv (U@2/U@4/U@8) | no redraw |
| figure5_descriptive_predictors | present | present | rq2_four_model_descriptive.csv | filename already says descriptive; do not caption as significance |

Canonical macros used in paper and figures:

| Model | A | PFC | PSC | U2 | U4 | U8 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| qwen3_vl_4b_instruct | 0.8575 | 0.7875 | 0.99875 | 0.9025 | 0.805 | 0.6975 |
| gemma3_4b_it | 0.605 | 0.43 | 0.8125 | 0.810 | 0.64125 | 0.48375 |
| molmo_7b_d_0924 | 0.6875 | 0.52125 | 0.7925 | 0.755 | 0.57625 | 0.4725 |
| skywork_vl_reward_7b | 0.845 | 0.87 | 0.99125 | 0.9175 | 0.83625 | 0.75125 |

Pearson in rq2_four_model_descriptive.csv: A vs U8 = 0.9342, PFC vs U8 = 0.9779, PSC vs U8 = 0.9829.

Note: `figures/FIGURES_BLOCKED.txt` records that matplotlib is unavailable on this host. The PDF/PNG files already exist and were not regenerated.

Do not update expanded-model figures until InternVL and the 8-model canonical table exist.
