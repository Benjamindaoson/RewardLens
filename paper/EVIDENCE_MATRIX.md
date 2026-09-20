# Submission Evidence Matrix

This ledger maps manuscript claims to the frozen artifacts used to verify them.
It is an audit aid, not part of the anonymized main text.

| Claim | Evidence artifact | Denominator / check | Manuscript location |
| --- | --- | --- | --- |
| Attribute static exact tie (80.5% / 80.5%) | `results/paper_analysis/v1/accuracy_matched_1pp.csv` | 200 independent Attribute items per judge | Results, Eq. `exact_static_tie` |
| Attribute RA gap (15.05 pp) | `results/paper_analysis/v1/accuracy_matched_1pp.csv` | Phi base-correct support 186; paired bootstrap, 10,000 resamples, seed 20270915 | Results; `tab:paired-bootstrap` |
| Seven within-factor pairs at <=1 pp | `results/paper_analysis/v1/accuracy_matched_1pp.csv` | Seven descriptive pair rows; pairs may share judges | Results; `tab:matched_pairs_1pp` |
| Qwen Count 166/200 retention failures | `results/paper_analysis/canonical_model_factor_metrics.csv` | Count base-correct n=200; RA=0.17; 34 relevant-correct | Abstract; Results |
| Full 32 model-factor ledger | `results/paper_analysis/canonical_model_factor_metrics.csv` | 8 judges x 4 factors; 200 static items and 200 audit triplets per cell | Appendix; `tab:all_32_results` |
| Shared-base-correct robustness | `paper/appendix/additional_results.tex` plus triplet ledgers | Pairwise intersection support reported as `n_cap` | Appendix; `tab:shared-base-correct-full` |
| 1/2/3 pp sensitivity | `results/paper_analysis/v1/accuracy_matched_{1,2,3}pp.csv` and `matched_bands.json` | Within-factor census; no independence inference | Analysis; `tab:threshold_sensitivity-full` |
| Paired-bootstrap uncertainty | `results/paper_analysis/v1/paired_bootstrap_accuracy_matched.json` | Joint resampling of shared item/triplet keys; 10,000 replicates; seed 20270915 | Appendix; `tab:paired-bootstrap` |
| Edit-magnitude controls | `results/paper_analysis/eight_model_raii/edit_magnitude.json` | Pixel fraction/SSIM diagnostics; 0.05 subset marked post-hoc | Analysis; `tab:edit-magnitude-full` |
| Audit construction validity | `rewardlens/renderers/clevr_controlled_renderer.py`, validators, FAST_TRACK manifest | Post-render semantic contracts, shared rendering conditions, 200 PASS triplets/factor | Audit Construction; Appendix |
| Dataset provenance and disjointness | `rewardlens/docs/TALLYQA_DATA_CONSTRUCTION.md`, `GQA_DATA_CONSTRUCTION.md`, split receipts | 800 static items; zero static/audit natural-image overlap | Experimental Setup; Appendix |
| Model/prompt/adapter reproducibility | `rewardlens/models/model_registry.yaml`, `rewardlens/inference/prompts/pairwise_ab.txt`, adapter modules | Eight public checkpoint identifiers; deterministic decoding | Appendix; `tab:checkpoints` |
| Analysis-plan timing | repository commits `4c144364...` and `21e27cd...` | Plan commit precedes paper-analysis commit; not claimed as preregistration | Appendix provenance |

The final PDF is rebuilt with `cd paper && latexmk -pdf main.tex`. Claims that
depend on human perceptual agreement are intentionally not asserted because no
human-validity agreement rate is included in the current evidence package.
