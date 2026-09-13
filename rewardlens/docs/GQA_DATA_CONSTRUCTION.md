# GQA / TallyQA Data Construction

Static accuracy and downstream utility never use RewardLens-CLEVR audit images.

## Frozen dataset assignment (2026-09-12)

**PRE-RESULT DATA AVAILABILITY ADAPTATION.** Not result-driven.

GQA 1.2 public questions yielded **zero** valid Count items under the pre-specified structural mapping (`count` ops, numeric answers, “How many”). Count mappings were **not invented**. The paper is not blocked on GQA Count.

| Factor | Static \(A\) | Downstream \(U\) (N=8) |
|---|---|---|
| Count | TallyQA | TallyQA |
| Attribute | GQA | GQA |
| Spatial | GQA | GQA |
| Presence | GQA | GQA |

Do not pool raw downstream utility across TallyQA and GQA. RQ2/RQ3 stay factor-wise. See `CONFIRMATORY_ANALYSIS_PLAN.md` and `STATISTICAL_ANALYSIS.md`.

CLEVR audit remains independent by construction.

---

## GQA splits (Attribute / Spatial / Presence)

Freeze by **image ID**:

- `datasets/gqa/derived/static_image_ids.json`
- `datasets/gqa/derived/downstream_image_ids.json`
- intersection must be 0

Validate programmatically. Official GQA already keeps all questions of an image in one split; we additionally freeze our own static vs downstream image sets.

## GQA factor mapping

Do not keyword-match only. Use functional programs + answer types + scene graphs.

| Factor | Program / type signals | Hard negative | Status |
|---|---|---|---|
| Count | `count` / numeric answer | gold ± 1 | **N=0 on GQA 1.2 public questions. Not filled. Use TallyQA.** |
| Attribute | `queryAttr` / `chooseColor` / `verifyAttr` | alternative valid attribute | primary GQA |
| Spatial | `relate` / `verifyRel` with left/right (primary) | inverse relation | primary GQA |
| Presence | `exist` / yes-no existence of a queried object | yes ↔ no | primary GQA |

Human audit: ≥50 items / factor in `gqa_factor_mapping_report.json` (Attribute / Spatial / Presence).

## GQA items

- GQA-Static: 200 / factor pairwise `(I,q,y+,y-)` for Attribute, Spatial, Presence (FAST_TRACK). Count is TallyQA, not GQA.
- GQA-Best-of-N: same image-disjoint pool, N=8 frozen candidate pools

Candidate pools include gold, factor-specific structured negatives, and optional frozen natural distractors from one fixed VLM. All judges share the pool. Unfilled slots are queued, never fabricated.

## Text-only shortcut audit

Required before downstream claims. If a text-only judge exceeds a reasonable chance baseline, diagnose length/position/lexical shortcuts.

## Images

Download only required GQA images after freezing questions. Inventory must end with `missing = 0`.
