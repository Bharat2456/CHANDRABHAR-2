# System Architecture Diagram

```mermaid
flowchart TD
    A[Mission Data<br/>local folder] --> B[Data Discovery<br/>app/adapters]
    B --> C[Metadata / Geometry<br/>app/geo/mapper.py]
    C --> D[Geographic Overlap<br/>sampled swath intersection]
    D --> E[Common Lunar Grid<br/>app/core/physical.py]
    E --> F[Physical GSD Normalization<br/>app/core/geowarp.py]
    F --> G[Illumination-Aware Representation<br/>app/core/representation.py]
    G --> H[Correspondence<br/>app/core/matcher.py]
    H --> I[Geometric Verification<br/>RANSAC]
    I --> J{Evidence Gate<br/>app/core/evidence.py}
    J -->|thresholds met| K[VALIDATED]
    J -->|thresholds not met| L[INSUFFICIENT_EVIDENCE]
    K --> M[Results / Export<br/>JSON, CSV, PNG]
    L --> M
```

Rendered form of the pipeline described in
[`docs/03_SYSTEM_ARCHITECTURE.md`](../../03_SYSTEM_ARCHITECTURE.md). GitHub, GitLab and most
Markdown viewers with Mermaid support render this block directly; CHANDRABHAR-2's own published
documentation pages also render Mermaid natively.
