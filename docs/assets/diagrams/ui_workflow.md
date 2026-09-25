# UI Workflow Diagram

```mermaid
stateDiagram-v2
    [*] --> MissionOverview
    MissionOverview: Mission Overview (read-only)
    MissionOverview --> CorrespondenceLab: select pair / run

    CorrespondenceLab: Correspondence Lab (only execution surface)
    state CorrespondenceLab {
        [*] --> Waiting
        Waiting --> PrepareAlign : Run clicked
        PrepareAlign --> NormalizeRepresent
        NormalizeRepresent --> MatchVerify
        MatchVerify --> Complete
        MatchVerify --> InsufficientEvidence
        MatchVerify --> Failed
    }

    CorrespondenceLab --> EvidenceMetrics: view result
    EvidenceMetrics: Evidence & Metrics (reads results only)
    EvidenceMetrics --> ProductsExport: export
    ProductsExport: Products & Export (reads outputs only)
    ProductsExport --> MissionOverview: reflects latest run
```

Rendered form of the navigation structure in
[`docs/14_USER_GUIDE.md`](../../14_USER_GUIDE.md). Only **Correspondence Lab** executes
computation; the other three tabs are read-only views over its output, per the platform's
single-execution-surface design.
