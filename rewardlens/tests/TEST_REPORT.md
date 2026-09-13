# Confirmatory statistics fixture run

All tests: **13/13 PASS** (`python -m unittest rewardlens.tests.test_cpu_harness -v`).

Added coverage beyond the original 7:

- partial JSONL recovery + resume
- duplicate item_id protection
- parse failure / model error / missing image / invalid candidate count
- missing manifest
- 1/2/3-worker model sharding
- duplicate-output merge conflict detection
- GQA N=8 structured pool fill

Synthetic stats fixture written to `rewardlens/tests/fixtures/stats_run/stats_fixture_report.json` (not official outputs/). No scientific conclusion.
