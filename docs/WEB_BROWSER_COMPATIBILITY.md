# Browser compatibility

## Requirements
Web Workers, WebAssembly, `Blob`/`File`, `<dialog>`, IndexedDB (only for opt-in saving), ES2022. Pyodide's WORKERFS needs synchronous `FileReaderSync`, available in dedicated workers of all current browsers. No `SharedArrayBuffer`, cross-origin isolation or WebGPU is required.

## Tested in this delivery

| Browser | Result |
|---|---|
| **Chromium 153 (headless, Linux)** | Full E2E suite (`tests-e2e/run.mjs`) |
| Firefox, Safari (macOS/iOS), Edge, Chrome on Android/iOS, real touch devices | **Not tested.** Expected to work for core functionality by capability, but unverified. |

## Feature support and fallbacks

| Feature | Chromium | Firefox / Safari | Fallback |
|---|---|---|---|
| Drag-drop of folders (`webkitGetAsEntry`) | yes | yes | files only via `dataTransfer.files` |
| `<input webkitdirectory>` | yes | yes (Safari recent) | "Select files" |
| `showDirectoryPicker` | yes | no | `webkitdirectory` input |
| `navigator.deviceMemory` | yes | no | assumes Standard unless mobile |
| `performance.memory` | yes | no | not shown |
| WebGPU | present/not used | — | CPU/WASM only |

Mobile: the UI is responsive (bottom navigation, no horizontal overflow at 390 px — tested with touch emulation) but registration is memory- and time-intensive; the *Conservative* preset is selected automatically on mobile-class devices. Tab suspension by the OS ends a run; restart it.
