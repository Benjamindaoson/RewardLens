# Phase II autonomous A800 execution

Goal: Execute Qwen, Gemma, Molmo, Skywork sequentially on remote 011, followed by preliminary analysis.
Spec: openspec/changes/phase2-autonomous-execution/proposal.md.
Implementation is inline in the authoritative remote bundle; no Windows mirror or new dependencies.

- [ ] Add failing CPU-only tests for explicit READY/hash validation, journal conflict detection, interrupted pair/scalar/selection resume, static parse preservation, and underdetermined analysis.
- [ ] Add rewardlens/scripts/phase2_autonomous.py: gate, append-only execution, per-model subprocess isolation, durable receipts, dashboard.
- [ ] Add rewardlens/scripts/phase2_report.py: frozen metrics/table assembly, factorwise preliminary RQ2/RQ3, JSON/CSV/SVG/Markdown.
- [ ] Add scripts/run_phase2_4model_autonomous.sh, offline environment and lock.
- [ ] Run Phase II V2 plus orchestration tests, CLI help, structural preflight, and shell syntax check.
- [ ] Start screen phase2_gpu and independently verify process, durable progress and GPU activity.

No inference in tests. No changes to existing protocol, adapters, prompts, manifests, or metrics.
Durability: append and fsync each judgment/score; preserve complete records; quarantine only a torn final record.
Partial selections are derived from saved complete N=8 graphs and appended only when missing.
Failure: preserve partial model results, record failure and continue to the next model. No automatic semantic retries.
Model completion requires 800 static records, 800 complete N=8 graphs, and 2400 derived selections.
Analysis is preliminary only. Four-model LOFO M1 is underdetermined; report null and a reason, never stabilize with a new estimator.
