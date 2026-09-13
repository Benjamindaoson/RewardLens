# FAST_TRACK factor freeze — spatial

- factor: `spatial`
- dataset source (audit): RewardLens-CLEVR
- dataset source (static/downstream): `gqa`
- PASS count: 201
- BORDERLINE count: 6
- FAIL count: 0
- source item count (QC complete): 207
- unique image count frozen: 600
- duplicate status: none
- static/downstream allocation: not this freeze (CLEVR audit only). Natural-image gqa static/downstream already frozen independently.
- manifest path: `D:\01_work\RewardLens\outputs\fast_track_audit_v1\factors\spatial\factor_audit_manifest.jsonl`
- SHA256: `04258a5d14a0ae682b925c7a2917598a28436dfa57e2e84db721d72d2bb18566`
- QC rules version: `controlled_qc.v1.20260912`
- freeze timestamp: `2026-09-12T14:56:24.001987+00:00`

## What this freeze can prove

This factor now has a deterministic PASS-only 200-triplet audit subset for FAST_TRACK. BORDERLINE/FAIL were not upgraded. Sample rule is sorted triplet_id, independent of model scores.

## What this freeze cannot prove

It cannot prove RQ1–RQ3. It is not a natural-image result. It does not authorize combining this factor with unfrozen factors into FAST_TRACK_AUDIT_V1. GPU scores must not be used to re-pick these 200 rows.

## Next dependency

Wait until all four factors have this freeze, then freeze FAST_TRACK_AUDIT_V1. Do not build the full P0 GPU bundle before that combined freeze.
