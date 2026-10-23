import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import { readFileSync } from 'node:fs'

const pkg = JSON.parse(readFileSync('./package.json', 'utf8'))
const engine = readFileSync('./VERSION.txt', 'utf8').trim()

export default defineConfig({
  plugins: [react()],
  define: { __APP_VERSION__: JSON.stringify(pkg.version), __ENGINE_VERSION__: JSON.stringify(engine) },
  worker: { format: 'es' },
  build: { assetsInlineLimit: 0, target: 'es2022', sourcemap: false, chunkSizeWarningLimit: 700 },
  server: { port: 5173 },
  test: { include: ['tests-web/**/*.test.ts'], environment: 'node', testTimeout: 300_000, hookTimeout: 300_000 },
})
