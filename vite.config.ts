import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'
import type { Plugin } from 'vite'

const pkg = JSON.parse(readFileSync('./package.json', 'utf8'))
const engine = readFileSync('./VERSION.txt', 'utf8').trim()

/**
 * Upstream's pyodide.mjs ends with a `sourceMappingURL=pyodide.mjs.map` comment, but the official release tarball ships no
 * map, so Vite logged "Failed to load source map" whenever a test imported the runtime. This drops only the dangling
 * comment from the in-memory copy; the vendored file on disk is untouched (its SHA-256 is verified by scripts/check-assets.mjs)
 * and no source map is fabricated. The browser build never processes these files (they are served statically from /pyodide/).
 */
const ignoreMissingPyodideSourceMap = (): Plugin => ({
  name: 'ignore-missing-pyodide-sourcemap', enforce: 'pre',
  load(id) { const f = id.split('?')[0]; if (/[\\/]public[\\/]pyodide[\\/][^\\/]+\.m?js$/.test(f)) return readFileSync(f, 'utf8').replace(/^\/\/# sourceMappingURL=.*$/gm, '').replace(/\/\/# sourceMappingURL=\S+\s*$/, '') },
})

export default defineConfig({
  plugins: [react(), ignoreMissingPyodideSourceMap()],
  define: { __APP_VERSION__: JSON.stringify(pkg.version), __ENGINE_VERSION__: JSON.stringify(engine) },
  worker: { format: 'es' },
  build: { assetsInlineLimit: 0, target: 'es2022', sourcemap: false, chunkSizeWarningLimit: 700 },
  server: { port: 5173 },
  test: {
    include: ['tests-web/**/*.test.ts'], environment: 'node', testTimeout: 300_000, hookTimeout: 300_000,
  },
})
