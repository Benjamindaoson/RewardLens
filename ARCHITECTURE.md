# Architecture

RewardLens evaluates whether multimodal judges with similar static accuracy depend on visual evidence in the same way.

```mermaid
flowchart TD
    B["Base example"] --> C["Factor-controlled triplet"]
    C --> RE["Relevant edit"]
    C --> IE["Irrelevant edit"]
    RE --> J["Judge execution"]
    IE --> J
    J --> M["RA / II estimators"]
    M --> W["Within-factor matching"]
    W --> U["Uncertainty and failure analysis"]
```

## Measurement contract

- Factors are evaluated separately.
- Relevant and irrelevant edits form controlled interventions.
- Metrics are conditioned on base-correct examples.
- Within-factor matching compares judges at similar static accuracy.
- Reports preserve uncertainty, exclusions, and failed runs.

## Evidence boundary

The repository is a reproducible research workspace. Protocol notes and staged data manifests are not equivalent to completed model runs.
