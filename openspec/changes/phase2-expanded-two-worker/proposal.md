# Expanded two-worker experiment

Use both existing A800 workers without signaling active inference processes. Freeze a model-blind candidate order, prefetch one checkpoint at a time per worker into local storage, and verify pinned repository file hashes. Reuse frozen inference/prompt/BoN/metric implementations. New adapters may only bridge processor, image-wrapper and generation APIs.

Acceptance: immutable selection precedes expanded outcomes; resumable model-only downloads; isolated output directories; a synthetic single-pair compatibility gate before formal execution; every included model completes Static 800, downstream 800/22400 and frozen audit; existing valid results are referenced, not recomputed; factorwise confirmatory analyses and final integrity receipt require eight models or explicitly justified minimum six. No modifications to frozen manifests, existing four checkpoints, or active inference code.

Live observability: each worker gets a separate GNU screen dashboard that reads existing durable status only, shows stage/counts/throughput/elapsed/ETA/abstention/GPU/VRAM/checkpoint state, and writes only its own workers/<worker>/terminal_dashboard/ directory. Never signal or modify model processes; acquire a display lock to prevent duplicate writers. Validate rendering with synthetic counts and run a real one-shot sample before screen launch.

Figure QA: render clearly marked synthetic fixtures in an isolated project-local visualization venv while GPU jobs continue untouched. Published plots must have readable numeric axes, non-color-only model identity, metric/direction captions, and SVG text alternatives. Rendering changes must preserve every source CSV byte, every plotted observation coordinate, and all analysis/inference/metric source hashes. Recheck real final plots after all model outputs exist; synthetic QA is not scientific evidence.

Current-process handoff: 011 naturally fails closed at its externally delegated Skywork dispatch marker after Molmo. 017 finishes its isolated Skywork run. New worker controllers wait for GPU availability, then claim distinct ready models using durable exclusive model claims.
