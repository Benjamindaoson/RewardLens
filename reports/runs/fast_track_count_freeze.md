# FAST_TRACK factor freeze — count

- factor: `count`
- dataset source (audit): RewardLens-CLEVR
- dataset source (static/downstream): `tallyqa`
- PASS count: 200
- BORDERLINE count: 0
- FAIL count: 0
- source item count (QC complete): 200
- unique image count frozen: 600
- duplicate status: none
- static/downstream allocation: not this freeze (CLEVR audit only). Natural-image tallyqa static/downstream already frozen independently.
- manifest path: `D:\01_work\RewardLens\outputs\fast_track_audit_v1\factors\count\factor_audit_manifest.jsonl`
- SHA256: `970cf6c3b385a262f7127187cc4468819fab583bcbe1855dfb043059050d79e9`
- QC rules version: `controlled_qc.v1.20260912`
- freeze timestamp: `2026-09-12T14:25:42.301077+00:00`

## What this freeze can prove

This factor now has a deterministic PASS-only 200-triplet audit subset for FAST_TRACK. BORDERLINE/FAIL were not upgraded. Sample rule is sorted triplet_id, independent of model scores.

## What this freeze cannot prove

It cannot prove RQ1–RQ3. It is not a natural-image result. It does not authorize combining this factor with unfrozen factors into FAST_TRACK_AUDIT_V1. GPU scores must not be used to re-pick these 200 rows.

## Next dependency

Wait until all four factors have this freeze, then freeze FAST_TRACK_AUDIT_V1. Do not build the full P0 GPU bundle before that combined freeze.
