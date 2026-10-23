#!/usr/bin/env node
// Packs the unchanged Python engine (app/**/*.py) into one static JSON asset loaded by the worker.
import { readdirSync, readFileSync, writeFileSync, mkdirSync, statSync } from 'node:fs';
import { join, dirname, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const walk = (d) => readdirSync(d).flatMap((n) => { if (n === '__pycache__') return []; const p = join(d, n); return statSync(p).isDirectory() ? walk(p) : p.endsWith('.py') ? [p] : []; });
const files = {};
for (const p of walk(join(ROOT, 'app')).sort()) files[relative(ROOT, p).split(sep).join('/')] = readFileSync(p, 'utf8');
const h = createHash('sha256'); for (const k of Object.keys(files)) { h.update(k); h.update('\0'); h.update(files[k]); h.update('\0'); }
const bundle = { engineVersion: readFileSync(join(ROOT, 'VERSION.txt'), 'utf8').trim(), platformVersion: readFileSync(join(ROOT, 'PLATFORM_VERSION.txt'), 'utf8').trim(), sha256: h.digest('hex'), fileCount: Object.keys(files).length, files };
mkdirSync(join(ROOT, 'public', 'engine'), { recursive: true });
writeFileSync(join(ROOT, 'public', 'engine', 'engine-bundle.json'), JSON.stringify(bundle));
console.log(`engine bundle: ${bundle.fileCount} files, sha256 ${bundle.sha256.slice(0, 12)}…`);
