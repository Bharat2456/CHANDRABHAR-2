# Privacy and security

## Data flow

| Item | Where it goes |
|---|---|
| Mission files (pixels, labels, geometry) | Read in place by the browser in 1) a TypeScript preflight (label head ≤200 KB, to find companion names) and 2) the worker via WORKERFS slices. **Never transmitted.** |
| Derived results | Memory of the tab; optionally IndexedDB (opt-in); exported to the user's disk on request |
| File names / metadata | Stay in the tab; not in any URL or request |
| Static assets | Downloaded once from the host (HTML/JS/CSS, fonts, Pyodide runtime, engine bundle) |
| Analytics, telemetry, session replay, third-party scripts, remote fonts, external AI/API | **None** |

Verified by `tests-e2e/run.mjs` in real Chromium: every request is same-origin; no non-GET request; no mission names in any URL; zero CSP violations; no console errors.

## Local persistence (all controllable in Settings)

* `localStorage["cb2.prefs"]` — theme, memory preset, motion, save-results opt-in.
* IndexedDB `cb2/runs` — only when "Save results in this browser" is on: metrics, correspondences and evidence PNGs. **Never mission files.**
* "Clear all local data" deletes both (confirmation first). Quota errors surface as a toast; results remain exportable. Data is per-browser-profile and not synchronised; private browsing may block or discard it.
* "Reset workspace" (confirmation first) drops file references and detected products.

## Threat model for untrusted inputs

| Risk | Mitigation | Test |
|---|---|---|
| Path traversal in browser paths | `cleanRelativePath` rejects `..`, absolute, drive-letter; control chars replaced | `paths.test.ts` |
| Path traversal in labels (`file_name`) | `clean_name` allows plain names only; resolution `confine`d to workspace root; search root clamped | `test_security_and_adapters.py`, parity test in WASM |
| XML entity expansion / DTD | `<!ENTITY`/DTD subset refused before parsing; label size ≤20 MB | tests (Python + TS) |
| Absurd dimensions / allocation | `checked_shape`; declared size must equal real file size (so allocation is bounded by the file) | adapter tests |
| Truncated / corrupt binaries | size mismatch error with fix hint; stream reads raise `EOFError` | adapter + E2E |
| Non-finite pixels | handled by the engine's NaN-aware representations and previews | existing + E2E |
| Metadata rendered as HTML | React text nodes only; no `dangerouslySetInnerHTML` | code review |
| Huge directory trees | 20,000-file / depth-32 limits | `paths.test.ts` |
| Secrets | none exist; no environment variables | — |

## Honest limits

This does not protect against a compromised device, malicious browser extensions or a malicious host that serves different code. The CSP prevents the *served* page from contacting other origins; it cannot constrain extensions. The Pyodide runtime is vendored and checksummed, which protects against CDN tampering at build time but not against a compromised GitHub/Vercel account.
