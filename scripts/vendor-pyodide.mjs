#!/usr/bin/env node
// Vendors the minimal Pyodide runtime (core + numpy, scipy, opencv-python, shapely) into public/pyodide.
// Reproducible: the upstream release tarball is verified against a pinned SHA-256.
//   node scripts/vendor-pyodide.mjs                 # download from GitHub release, verify, extract, copy
//   node scripts/vendor-pyodide.mjs --from <dir>    # use an already extracted pyodide-0.29.5 directory
import { createHash } from 'node:crypto';
import { createReadStream, existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync, rmSync, statSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { tmpdir } from 'node:os';

const VERSION = '0.29.5';
const TARBALL_SHA256 = '7ae170fe06a68d11f15cbf77fc78488b4712cfbfade81c87e9b4010973cd67c8';
const URL_ = `https://github.com/pyodide/pyodide/releases/download/${VERSION}/pyodide-${VERSION}.tar.bz2`;
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'public', 'pyodide');
const WANT = ['numpy', 'scipy', 'opencv-python', 'shapely'];
const CORE = ['pyodide.mjs', 'pyodide.asm.js', 'pyodide.asm.wasm', 'python_stdlib.zip'];

const sha = (p) => new Promise((res, rej) => { const h = createHash('sha256'); createReadStream(p).on('data', (d) => h.update(d)).on('end', () => res(h.digest('hex'))).on('error', rej); });

let src = process.argv.includes('--from') ? process.argv[process.argv.indexOf('--from') + 1] : null;
if (!src) {
  const tmp = join(tmpdir(), `pyodide-${VERSION}`); mkdirSync(tmp, { recursive: true });
  const tar = join(tmp, 'pyodide.tar.bz2');
  if (!existsSync(tar)) { console.log('downloading', URL_); const r = await fetch(URL_); if (!r.ok) throw new Error('download failed ' + r.status); writeFileSync(tar, Buffer.from(await r.arrayBuffer())); }
  const got = await sha(tar); if (got !== TARBALL_SHA256) throw new Error(`tarball checksum mismatch: ${got}`);
  execFileSync('tar', ['-xjf', tar, '-C', tmp]); src = join(tmp, 'pyodide');
}
const lock = JSON.parse(readFileSync(join(src, 'pyodide-lock.json'), 'utf8'));
const need = new Set(); const stack = [...WANT];
while (stack.length) { const n = stack.pop(); if (need.has(n)) continue; if (!lock.packages[n]) throw new Error('missing package ' + n); need.add(n); stack.push(...(lock.packages[n].depends || [])); }
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });
const manifest = { pyodide: VERSION, tarball_sha256: TARBALL_SHA256, files: {}, packages: {} };
const files = [...CORE];
const reduced = { info: lock.info, packages: {} };
for (const n of [...need].sort()) { reduced.packages[n] = lock.packages[n]; files.push(lock.packages[n].file_name); manifest.packages[n] = lock.packages[n].version; }
writeFileSync(join(OUT, 'pyodide-lock.json'), JSON.stringify(reduced));
for (const f of files) { copyFileSync(join(src, f), join(OUT, f)); manifest.files[f] = { bytes: statSync(join(OUT, f)).size, sha256: await sha(join(OUT, f)) }; }
// lock integrity: wheel hashes in the lock must equal the copied files
for (const n of need) { const p = lock.packages[n]; if (p.sha256 && p.sha256 !== manifest.files[p.file_name].sha256) throw new Error('lock sha mismatch ' + n); }
writeFileSync(join(OUT, 'package.json'), '{"type":"commonjs"}\n'); // pyodide.asm.js is CommonJS-flavoured; keeps Node-based tests working
writeFileSync(join(OUT, 'VENDOR_MANIFEST.json'), JSON.stringify(manifest, null, 2));
console.log('vendored', files.length, 'files,', Object.values(manifest.files).reduce((a, f) => a + f.bytes, 0) / 1e6, 'MB ->', OUT);
