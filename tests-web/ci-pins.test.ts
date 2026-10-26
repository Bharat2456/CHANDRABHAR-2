import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'

describe('CI native-reference pins stay in sync with the vendored WebAssembly runtime', () => {
  const pins = Object.fromEntries(readFileSync('requirements-ci.txt', 'utf8').split('\n').filter((l) => /^[A-Za-z]/.test(l)).map((l) => l.split('==') as [string, string]))
  const vendored = JSON.parse(readFileSync('public/pyodide/VENDOR_MANIFEST.json', 'utf8')).packages as Record<string, string>
  it.each([['numpy', 'numpy'], ['scipy', 'scipy'], ['shapely', 'shapely'], ['opencv-python-headless', 'opencv-python']])('%s pin equals the runtime version', (pin, pkg) => { expect(pins[pin]).toBe(vendored[pkg]) })
})
