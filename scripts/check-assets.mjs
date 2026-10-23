#!/usr/bin/env node
// Fails the build early if the vendored runtime is missing or corrupted (so a broken deploy cannot ship).
import { existsSync, readFileSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..'); const dir = join(ROOT, 'public', 'pyodide');
if (!existsSync(join(dir, 'VENDOR_MANIFEST.json'))) { console.error('public/pyodide is missing. Run: npm run vendor:pyodide'); process.exit(1); }
const m = JSON.parse(readFileSync(join(dir, 'VENDOR_MANIFEST.json'), 'utf8')); let bad = 0;
for (const [f, meta] of Object.entries(m.files)) {
  const p = join(dir, f); if (!existsSync(p) || statSync(p).size !== meta.bytes) { console.error('missing or wrong size:', f); bad++; continue; }
  const h = createHash('sha256').update(readFileSync(p)).digest('hex'); if (h !== meta.sha256) { console.error('checksum mismatch:', f); bad++; }
}
if (!existsSync(join(ROOT, 'public', 'engine', 'engine-bundle.json'))) { console.error('engine bundle missing'); bad++; }
if (bad) process.exit(1); console.log(`runtime assets verified (${Object.keys(m.files).length} files, Pyodide ${m.pyodide})`);
