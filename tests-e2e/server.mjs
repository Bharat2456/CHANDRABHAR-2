// Minimal static server that reproduces Vercel behaviour using the project's own vercel.json header rules.
import { createServer } from 'node:http'; import { readFileSync, existsSync, statSync, createReadStream } from 'node:fs'; import { join, extname, dirname } from 'node:path'; import { fileURLToPath } from 'node:url'; import { brotliCompressSync } from 'node:zlib';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..'); const DIST = join(ROOT, 'dist'); const cfg = JSON.parse(readFileSync(join(ROOT, 'vercel.json'), 'utf8'));
const MIME = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.wasm': 'application/wasm', '.png': 'image/png', '.woff2': 'font/woff2', '.zip': 'application/zip', '.whl': 'application/octet-stream' };
const rules = cfg.headers.map((h) => ({ re: new RegExp('^' + h.source.replace(/\(\.\*\)/g, '.*').replace(/\\\\\./g, '\\.') + '$'), headers: h.headers }));
export function startServer(port = 0) {
  const log = [];
  const srv = createServer((req, res) => {
    const url = new URL(req.url, 'http://x'); let p = decodeURIComponent(url.pathname); log.push({ method: req.method, path: p });
    let file = join(DIST, p); if (!file.startsWith(DIST)) { res.writeHead(403).end(); return; }
    if (!existsSync(file) || statSync(file).isDirectory()) file = existsSync(join(file, 'index.html')) ? join(file, 'index.html') : join(DIST, 'index.html'); // SPA fallback
    const h = { 'Content-Type': MIME[extname(file)] ?? 'application/octet-stream' };
    for (const r of rules) if (r.re.test(p)) for (const x of r.headers) if (x.key.toLowerCase() !== 'content-type' || !MIME[extname(file)]) h[x.key] = x.value;
    res.writeHead(200, h); createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => srv.listen(port, '127.0.0.1', () => resolve({ srv, port: srv.address().port, log, close: () => new Promise((r) => srv.close(r)) })));
}
if (process.argv[1] === fileURLToPath(import.meta.url)) { const s = await startServer(4173); console.log('serving dist on http://127.0.0.1:' + s.port); }
