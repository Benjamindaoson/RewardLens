# Repository Guidelines

## Project Structure

`rewardlens/` contains the research implementation: `inference/` model runners
and adapters, `lib/` shared data utilities, `renderers/`, `models/` registries,
`scripts/` command-line workflows, `configs/`, and `tests/`. `manifests/`
records dataset splits and freeze metadata; `results/` and `reports/` contain
derived analyses and run records. Keep large datasets, GPU bundles, and runtime
outputs outside Git as configured by `.gitignore`. The paper source is in
`paper/`, with sections in `paper/sections/`; do not edit ICLR style files.

## Build, Test, and Development Commands

- `python -m unittest rewardlens.tests.test_cpu_harness -v` runs the documented
  synthetic CPU harness regression suite.
- `python rewardlens/scripts/generate_controlled_pilot.py --factor attribute`
  generates a controlled pilot; use `presence` or `spatial` as needed, then run
  the corresponding `validate_controlled_pilot.py` command.
- `bash rewardlens/scripts/run_gpu_preflight.sh` performs the GPU environment
  preflight. Follow `GPU_RUNBOOK.md` for staged/offline inference; do not use
  GPU commands to regenerate frozen evidence.
- After changing files under `paper/`, run `cd paper && latexmk -pdf main.tex`.

## Coding Style and Tests

Use Python 3, four-space indentation, `snake_case` functions and variables,
and `CapWords` test classes. Keep scripts executable as direct CLI entry points
and place reusable logic in the appropriate package module. Add focused,
synthetic `unittest` coverage under `rewardlens/tests/test_<area>.py`; tests
must not require model weights, network access, or official result files.

## Research and Paper Integrity

Do not invent results or alter frozen experimental numbers without repository
evidence. RewardLens evaluates Count, Attribute, Presence, and Spatial; static
evaluation and intervention audit are distinct environments. Preserve labels
and cross-references, use notation such as `A_{S,c}`, `RA_c`, and `II_c`, and
never claim causal grounding from behavioral interventions. In `.tex` files,
avoid Markdown bold and Chinese explanatory text.

## Commits and Pull Requests

Use concise, imperative commit subjects consistent with history, e.g. `Add GPU
preflight validation` or `Fix manifest hash check`. Keep commits scoped. PRs
should describe the affected protocol/code path, list validation commands and
outputs, link relevant issues, and include PDFs or screenshots for paper/figure
changes. Before requesting review, inspect `git diff`; never commit or push
without explicit approval.
