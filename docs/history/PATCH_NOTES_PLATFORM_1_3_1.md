# LunaMatch Platform 1.3.1

## Final workflow synchronization fix

- Correspondence Lab is the only execution page.
- Evidence & Metrics is read-only verification; it no longer starts experiments.
- Products & Export is read-only handoff; it no longer starts experiments.
- Completed workflow state is persisted to `LunaMatch_Platform_Outputs/workflow_state.json`.
- Mission Overview reads the persisted state and reflects completed stages immediately after a Correspondence Lab run.
- The Correspondence Lab triggers a Streamlit rerun after completion so the Overview is refreshed from the same run without a second execution.
- A fresh mission-data scan resets stale workflow state to stages 1–2 only.
- The scientific engine and its 18-test baseline are unchanged.
