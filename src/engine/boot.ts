/** Environment-agnostic engine bootstrap, shared by the Web Worker and the Node test harness. */
export interface EngineBundle { engineVersion: string; platformVersion: string; sha256: string; fileCount: number; files: Record<string, string> }
export type BootStage = 'runtime' | 'packages' | 'engine' | 'ready'
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Py = any

/**
 * Slice reader exposed to Python as `js.cb2ReadSlice(path, position, length)`.
 * Python's file seek() is 32-bit in wasm32 (max 2 GiB); the Emscripten FS API accepts JS numbers (exact to 2^53),
 * so rasters of any realistic size can be sliced without loading them.
 */
export function installSliceReader(py: Py, target: Record<string, unknown>) {
  const FS = py.FS; const streams = new Map<string, unknown>()
  target.cb2ReadSlice = (path: string, position: number, length: number): Uint8Array => {
    let st = streams.get(path); if (!st) { st = FS.open(path, 'r'); streams.set(path, st) }
    const buf = new Uint8Array(length); const n = FS.read(st, buf, 0, length, position)
    return n === length ? buf : buf.subarray(0, n)
  }
  target.cb2CloseSlices = () => { for (const s of streams.values()) { try { FS.close(s) } catch { /* already closed */ } } streams.clear() }
}

export const PYTHON_PACKAGES = ['numpy', 'scipy', 'opencv-python', 'shapely'] as const

export async function bootEngine(opts: {
  loadPyodide: (o: Record<string, unknown>) => Promise<Py>
  indexURL: string
  bundle: EngineBundle
  onStage?: (s: BootStage) => void
  hostGlobal?: Record<string, unknown>
}): Promise<Py> {
  const { loadPyodide, indexURL, bundle, onStage } = opts
  onStage?.('runtime')
  const py = await loadPyodide({ indexURL, fullStdLib: false })
  onStage?.('packages')
  await py.loadPackage([...PYTHON_PACKAGES])
  onStage?.('engine')
  const FS = py.FS
  const mk = (p: string) => { try { FS.mkdir(p) } catch { /* exists */ } }
  mk('/engine'); mk('/ws'); mk('/demo')
  for (const [path, text] of Object.entries(bundle.files)) {
    const parts = path.split('/'); let cur = '/engine'
    for (const d of parts.slice(0, -1)) { cur += '/' + d; mk(cur) }
    FS.writeFile('/engine/' + path, text)
  }
  installSliceReader(py, opts.hostGlobal ?? (globalThis as unknown as Record<string, unknown>))
  py.runPython("import sys\nif '/engine' not in sys.path: sys.path.insert(0, '/engine')\nimport app.web.bridge")
  onStage?.('ready')
  return py
}
