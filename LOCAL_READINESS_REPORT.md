# LOCAL_READINESS_REPORT

Generated 2026-09-12 (SIGNAL_GATE_V1 frozen; TallyQA Count frozen). CPU Windows host. No CUDA. No model weights downloaded. No fabricated inference results.

**SIGNAL_READY is true.** Combined static/downstream manifests are complete. **FULL FAST_TRACK (200 PASS/factor) is not frozen yet**; 500-scale Blender is still running and was not stopped.

---

## 1. SIGNAL_GATE_V1 — FROZEN

`outputs/signal_gate_v1/` hashes present. 100 PASS triplets / factor, PASS-only, sorted triplet ids. BORDERLINE/FAIL retained in QC, not upgraded.

| Factor | generated complete at freeze | PASS | BORDERLINE | FAIL | frozen |
|---|---:|---:|---:|---:|---:|
| Count | 136 | 136 | 0 | 0 | 100 |
| Attribute | 103 | 101 | 2 | 0 | 100 |
| Presence | 106 | 106 | 0 | 0 | 100 |
| Spatial | 106 | 104 | 2 | 0 | 100 |

1200 items (400 triplets × 3). Probe: 50 judgments. Bundle: `gpu_bundle_signal_v1` (3564 images, verify PASS, SHA256SUMS written).

---

## 2. Natural-image static / downstream — COMPLETE

**PRE-RESULT DATA AVAILABILITY ADAPTATION.** GQA 1.2 Count N=0. Not invented.

| Factor | Static | Downstream N=8 | Dataset |
|---|---:|---:|---|
| Count | 200 (100 simple / 100 complex) | 200 (100 simple / 100 complex) | TallyQA |
| Attribute | 200 | 200 | GQA |
| Spatial | 200 | 200 | GQA |
| Presence | 200 | 200 | GQA |

- TallyQA image disjointness: intersection 0
- GQA image disjointness: intersection 0
- TallyQA images: 400/400, missing=0 (all reused VG/GQA)
- GQA images: 1182/1182, missing=0
- Combined: `datasets/processed/fast_eval/` 800 + 800

---

## 3. Controlled 500-scale (continues)

Four Blender jobs still running toward FAST_TRACK 200 and 500/factor robustness. Do not stop them.

---

## 4. Analysis contract

RQ2 factor-wise. Count \(U\) = TallyQA; other \(U_f\) = GQA. Do not pool raw utility.

RQ3 within-column \(D_* \to U_f\); diagonal-vs-off-diagonal uses column-standardized scores.

Logged as **PRE-RESULT DATA AVAILABILITY ADAPTATION** (not result-driven).

---

## 5. GPU remaining

Signal-gate GPU pass can start from `gpu_bundle_signal_v1`.

Still missing for **full** FAST_TRACK GPU:

1. FAST_TRACK_AUDIT_V1 freeze (200 PASS / factor)
2. This host has no GPU / no weights

P2: VQA-v2, MMVP, editing, LoRA.
