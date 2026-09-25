# CHANDRABHAR-2 — Typography

The logo wordmark uses a bold, geometric, slightly angular sans-serif (mission-patch style),
so the interface pairs it with a clean, highly-legible system sans rather than trying to
reproduce a display face at small sizes.

## Type stack

```css
--font-display: "Inter", "Segoe UI", system-ui, sans-serif;   /* headings, hero title */
--font-body:    "Inter", "Segoe UI", system-ui, sans-serif;   /* body copy, tables */
--font-mono:    "JetBrains Mono", "Consolas", monospace;      /* metrics, IDs, terminal log, product IDs */
```

Streamlit ships its own font stack; the dashboard does not attempt to load an external
webfont (keeping it fully offline-safe for a laptop demo). System sans-serif fallback is
intentional and acceptable for a CPU-first, offline-first tool.

## Scale

| Role | Size | Weight | Notes |
|---|---|---|---|
| Hero title (CHANDRABHAR-2) | 2.2–2.4rem | 800 | One line, never wraps |
| Section header | 1.3–1.5rem | 700 | Tab/subheader level |
| Card value (metric) | 1.4–1.6rem | 800 | Monospace for numeric IDs/GSD |
| Body | 0.95–1rem | 400–500 | |
| Caption / muted | 0.78–0.85rem | 500 | Neutral Grey |
| Status badge | 0.8rem | 700 | Uppercase, letter-spacing |

## Rules

- Numeric/scientific values (GSD, RMSE, inlier counts, product IDs, timestamps) are set in
  monospace so digits align in tables and metric cards.
- Uppercase is reserved for short status words (`VALIDATED`, `RUNNING`, `WAITING`) and section
  kickers — not for full sentences.
- Line length in help text / tooltips is kept short (informational, not a manual) to preserve
  the mission-console density the platform aims for.
