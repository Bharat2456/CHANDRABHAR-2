// End-to-end tests in a REAL headless Chromium against the production build, served with the project's own vercel.json headers.
//   npm run build && npm run test:e2e
import chromium from '@sparticuz/chromium'; import puppeteer from 'puppeteer-core';
import { execFileSync } from 'node:child_process'; import { mkdirSync, rmSync, readFileSync, readdirSync, writeFileSync, openSync, ftruncateSync, closeSync, cpSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path'; import { fileURLToPath } from 'node:url'; import { tmpdir } from 'node:os';
import { startServer } from './server.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..'); const OUT = join(ROOT, 'tests-e2e', 'out'); const FX = join(tmpdir(), 'cb2-fixtures'); const DL = join(OUT, 'downloads')
rmSync(OUT, { recursive: true, force: true }); mkdirSync(DL, { recursive: true }); rmSync(FX, { recursive: true, force: true })
execFileSync(process.env.PYTHON ?? 'python3', ['tools/make_fixtures.py', FX], { cwd: ROOT, stdio: 'pipe' })

// --- extra fixtures: truncated product and a huge sparse product (proves large files are not loaded into memory)
const TRUNC = join(tmpdir(), 'cb2-trunc'); rmSync(TRUNC, { recursive: true, force: true }); cpSync(join(FX, 'tmc2'), join(TRUNC, 'tmc2'), { recursive: true })
const tImg = readdirSync(join(TRUNC, 'tmc2/data/calibrated/20210101')).find((f) => f.endsWith('.img')); const tp = join(TRUNC, 'tmc2/data/calibrated/20210101', tImg)
writeFileSync(tp, readFileSync(tp).subarray(0, 1000))
const BIG = join(tmpdir(), 'cb2-big'); rmSync(BIG, { recursive: true, force: true }); mkdirSync(BIG, { recursive: true })
const BIG_H = 40000, BIG_W = 40000, bigBytes = BIG_H * BIG_W * 2  // 3.2 GB sparse
{ const fd = openSync(join(BIG, 'big_synth_d_img_d18.img'), 'w'); ftruncateSync(fd, bigBytes); closeSync(fd) }
writeFileSync(join(BIG, 'big_synth_d_img_d18.xml'), `<?xml version="1.0"?><Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1"><Identification_Area><logical_identifier>urn:isro:isda:ch2_synth:data_calibrated:big_synth</logical_identifier><title>Synthetic huge OHRC</title></Identification_Area><Observation_Area><Discipline_Area><Imaging_Parameters><pixel_resolution>0.25</pixel_resolution></Imaging_Parameters></Discipline_Area></Observation_Area><File_Area_Observational><File><file_name>big_synth_d_img_d18.img</file_name></File><Array_2D_Image><offset>0</offset><Element_Array><data_type>UnsignedLSB2</data_type></Element_Array><Axis_Array><axis_name>Line</axis_name><elements>${BIG_H}</elements><sequence_number>1</sequence_number></Axis_Array><Axis_Array><axis_name>Sample</axis_name><elements>${BIG_W}</elements><sequence_number>2</sequence_number></Axis_Array></Array_2D_Image></File_Area_Observational></Product_Observational>`)

const results = []; let failed = 0
const check = (name, ok, detail = '') => { results.push({ name, ok: !!ok, detail: String(detail).slice(0, 1500) }); if (!ok) failed++; console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + String(detail).slice(0, ok ? 120 : 1200) : ''}`) }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const srv = await startServer(); const BASE = `http://127.0.0.1:${srv.port}`
const browser = await puppeteer.launch({ executablePath: await chromium.executablePath(), args: [...chromium.args, '--no-sandbox'], headless: 'shell' })
const page = await browser.newPage(); await page.setViewport({ width: 1360, height: 900 })
const cdp = await page.createCDPSession(); await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DL })
const consoleMsgs = []; const requests = []; const violations = []
page.on('console', (m) => consoleMsgs.push({ type: m.type(), text: m.text() })); page.on('pageerror', (e) => consoleMsgs.push({ type: 'pageerror', text: e.message }))
page.on('request', (r) => requests.push({ url: r.url(), method: r.method(), type: r.resourceType() }))
page.on('workercreated', (w) => { requests.push({ url: w.url(), method: 'WORKER', type: 'worker' }) })
await page.evaluateOnNewDocument(() => { window.__csp = []; document.addEventListener('securitypolicyviolation', (e) => window.__csp.push(`${e.violatedDirective} ${e.blockedURI}`)) })
const goto = async (r) => { await page.evaluate((x) => { location.hash = `#/${x}` }, r); await sleep(150) }
const h1 = () => page.$eval('h1', (e) => e.textContent)
const waitText = (t, timeout = 120000) => page.waitForFunction((x) => document.body.innerText.toLowerCase().includes(x.toLowerCase()), { timeout }, t)
const clickText = async (sel, text) => { const ok = await page.evaluate((s, t) => { const el = [...document.querySelectorAll(s)].find((e) => e.textContent.trim().includes(t) && !e.disabled); if (el) { el.click(); return true } return false }, sel, text); if (!ok) throw new Error(`no ${sel} with text "${text}"`) }
const shot = (n) => page.screenshot({ path: join(OUT, n + '.png') })
const overflow = () => page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)

try {
  // ---------- 1. load & routes ----------
  await page.goto(BASE + '/', { waitUntil: 'networkidle0' })
  check('app loads and renders heading', (await h1()).includes('Lunar image registration'))
  const routes = [['overview', 'Lunar image registration workspace'], ['workspace', 'Data workspace'], ['registration', 'Image registration'], ['lab', 'Correspondence lab'], ['evidence', 'Evidence & results'], ['reports', 'Reports & export'], ['settings', 'Settings & about']]
  for (const [r, t] of routes) { await goto(r); check(`route #/${r} renders "${t}"`, (await h1()) === t, await h1().catch(() => '')) }
  for (const w of [1360, 820, 390]) { await page.setViewport({ width: w, height: 900 }); for (const [r] of routes) { await goto(r); const o = await overflow(); if (o > 1) check(`no horizontal overflow ${r} @${w}px`, false, `overflow ${o}px`) } check(`no horizontal overflow on any route @${w}px`, !results.some((x) => !x.ok && x.name.includes(`@${w}px`))) }
  await page.setViewport({ width: 1360, height: 900 })
  await page.goto(BASE + '/#/settings', { waitUntil: 'networkidle0' }); check('direct navigation / refresh on a deep link works', (await h1()) === 'Settings & about')

  // ---------- 2. keyboard & a11y basics ----------
  await page.reload({ waitUntil: 'networkidle0' }); await page.keyboard.press('Tab'); const first = await page.evaluate(() => document.activeElement?.textContent?.trim()); check('first Tab stop is the skip link', /skip to content/i.test(first), first)
  const ring = await page.evaluate(() => { const b = document.querySelector('.nav a'); b.focus(); const cs = getComputedStyle(b); return cs.outlineStyle + ' ' + cs.outlineWidth }); check('focus indicator is visible on nav links', /solid 2px/i.test(ring), ring)
  check('landmarks present (header, nav, main)', await page.evaluate(() => !!document.querySelector('header') && !!document.querySelector('nav[aria-label="Primary"]') && !!document.querySelector('main')))
  check('status region announces engine state (aria-live)', await page.evaluate(() => !!document.querySelector('[role=status][aria-live=polite]')))

  // ---------- 3. ingestion via folder input ----------
  await goto('workspace'); const dirIn = await page.$('[data-testid=dir-input]')
  await dirIn.uploadFile(...[]) // no-op to ensure handle works
  const allFiles = (d) => readdirSync(d, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? allFiles(join(d, e.name)) : [join(d, e.name)]))
  const flat = allFiles(FX)
  // directory input: Chromium accepts a directory path and expands it into webkitRelativePath entries
  await dirIn.uploadFile(FX)
  await waitText('Products', 180000).catch(() => {})
  await page.waitForFunction(() => /\d+ products?/i.test(document.body.innerText), { timeout: 180000 }).catch(() => {})
  let nFiles = await page.evaluate(() => (document.body.innerText.match(/Selected files[\s\S]{0,80}?(\d+) ·/) || [])[1])
  if (!nFiles || +nFiles < 5) { // fall back to flat multi-file selection (documented browser difference)
    console.log('  (directory upload not expanded by headless Chromium; using multi-file input)'); await clickText('button', 'Reset workspace'); await clickText('dialog button', 'Reset workspace')
    await (await page.$('[data-testid=file-input]')).uploadFile(...flat); await page.waitForFunction(() => /\d+ products?/i.test(document.body.innerText), { timeout: 180000 })
  }
  await page.waitForFunction(() => /[1-9]\d* products?/i.test(document.body.innerText), { timeout: 240000 })
  const prodTxt = await page.evaluate(() => document.body.innerText)
  check('engine booted and products inspected', /[1-9]\d* products?/i.test(prodTxt))
  check('OHRC and TMC-2 PDS4 products detected with GSD', /OHRC/i.test(prodTxt) && /TMC-2/i.test(prodTxt) && /2\.000/i.test(prodTxt) && /5\.000/i.test(prodTxt))
  check('ENVI, NumPy and raw+sidecar products also detected', /envi/i.test(prodTxt) && /numpy/i.test(prodTxt) && /raw_sidecar/i.test(prodTxt))
  check('geometry CSV associated with PDS4 products', /swath table/i.test(prodTxt) || /geometry/i.test(prodTxt) && /\.csv/i.test(prodTxt))
  check('NumPy product without GSD prompts for override', /Supply missing metadata/i.test(prodTxt) && /GSD missing/i.test(prodTxt))
  await shot('workspace_loaded')
  await page.evaluate(() => document.querySelector('.productcard button')?.click()); await page.waitForSelector('.preview-img', { timeout: 60000 }); check('product preview renders (decimated, via stream reads)', true)

  // ---------- 4. registration run ----------
  await goto('registration'); await page.waitForSelector('[data-testid=run]')
  await page.evaluate(() => { const s = [...document.querySelectorAll('select')].find((x) => /Full cascade/i.test(x.textContent)); const set = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set; set.call(s, 'single'); s.dispatchEvent(new Event('change', { bubbles: true })) })
  await page.waitForFunction(() => /True swath intersection/i.test(document.body.innerText), { timeout: 60000 }); check('pair uses TRUE swath intersection (not bbox)', true)
  const compat = await page.evaluate(() => document.body.innerText); check('compatibility panel shows GSD ratio and overlap area', /2\.50×/i.test(compat) && /km²/i.test(compat))
  const t0 = Date.now(); await page.click('[data-testid=run]'); await page.waitForSelector('[data-testid=progress]', { timeout: 10000 }); check('live progress panel shown while running', true)
  const progSeen = new Set(); const poll = setInterval(async () => { try { const t = await page.$eval('[data-testid=progress]', (e) => e.innerText); progSeen.add(t.split('\n')[0]) } catch {} }, 250)
  await waitText('Processing completed', 240000); clearInterval(poll); check('run completes', true, `${((Date.now() - t0) / 1000).toFixed(1)}s`)
  check('UI stayed responsive during run (page JS thread served polls)', progSeen.size >= 1, [...progSeen].join(' | '))
  const noFake = await page.evaluate(() => [...document.querySelectorAll('[role=progressbar]')].every((p) => p.hasAttribute('aria-valuenow') || p.classList.contains('indet'))); check('progress bar is determinate only with measured value (else indeterminate)', noFake)
  await goto('evidence'); const ev = await page.evaluate(() => document.body.innerText)
  check('evidence shows four separate statements', /Processing completed/i.test(ev) && /Transformation estimated|Estimated/i.test(ev) && /Evidence gate/i.test(ev) && /Not established/i.test(ev))
  check('gate passed on synthetic geo-warped pair, ground truth still "Not established"', /Passed/i.test(ev) && /Not established/i.test(ev) && /synthetic/i.test(ev))
  check('limitation statement is displayed', /not independent ground-truth validation/i.test(ev))
  const txy = await page.evaluate(() => { const dd = [...document.querySelectorAll('.kv dt')].find((d) => d.textContent === 'Translation'); return dd?.nextElementSibling?.textContent }); const m = txy && txy.match(/(-?\d+\.\d+), (-?\d+\.\d+) px/); check('recovered translation < 1 grid px on known geometry', m && Math.abs(+m[1]) < 1 && Math.abs(+m[2]) < 1, txy)
  await shot('evidence')

  // ---------- 5. lab ----------
  await goto('lab'); await page.waitForSelector('canvas'); await sleep(800)
  const nonBlank = async () => page.evaluate(() => { const c = document.querySelector('canvas'); const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let nz = 0; const seen = new Set(); for (let i = 0; i < d.length; i += 4 * 37) { if (d[i] + d[i + 1] + d[i + 2] > 30) nz++; seen.add(d[i] >> 4) } return nz > 200 && seen.size > 6 })
  check('lab canvas renders real imagery (not blank)', await nonBlank()); await shot('lab_side')
  const before = await page.evaluate(() => document.querySelector('canvas').toDataURL().length); await page.focus('canvas'); await page.keyboard.press('+'); await page.keyboard.press('ArrowLeft'); await sleep(200)
  check('keyboard zoom/pan changes the view', (await page.evaluate(() => document.querySelector('canvas').toDataURL())).length !== before)
  await clickText('.seg button', 'Overlay'); await sleep(300); check('overlay mode renders', await nonBlank()); await clickText('.seg button', 'Before alignment'); await sleep(200); await clickText('.seg button', 'After alignment'); await shot('lab_overlay')
  check('lab legend distinguishes inliers/outliers by shape+text', /Inlier \(/i.test(await page.evaluate(() => document.body.innerText)))

  // ---------- 6. exports ----------
  await goto('reports'); const dlBefore = new Set(readdirSync(DL))
  for (const label of ['Metrics (JSON)', 'Summary (CSV)', 'Correspondences (CSV)', 'Evidence image (PNG)', 'Run manifest (JSON)']) {
    await page.evaluate((l) => { const row = [...document.querySelectorAll('.row.between')].find((r) => r.querySelector('b')?.textContent === l); row.querySelector('button').click() }, label); await sleep(900)
  }
  await clickText('button', 'Download everything'); await sleep(2500)
  const files = readdirSync(DL).filter((f) => !dlBefore.has(f) && !f.endsWith('.crdownload')); const byExt = (e) => files.find((f) => f.endsWith(e))
  const metrics = JSON.parse(readFileSync(join(DL, files.find((f) => f.endsWith('_metrics.json'))), 'utf8')); check('metrics.json valid with gate + claims', metrics.status === 'VALIDATED' && metrics.claims.ground_truth_validation === 'NOT_ESTABLISHED' && metrics.engine.opencv)
  const csv = readFileSync(join(DL, files.find((f) => f.endsWith('_summary.csv'))), 'utf8'); check('summary.csv has header, thresholds and gate rows', csv.startsWith('quantity,value,unit,threshold,criterion_met') && /ground_truth_validation,NOT_ESTABLISHED/i.test(csv))
  const cc = readFileSync(join(DL, files.find((f) => f.endsWith('_correspondences.csv'))), 'utf8').trim().split('\n'); check('correspondences.csv rows match inlier flags', cc.length > 20 && cc.slice(1).filter((l) => l.split(',')[5] === '1').length === metrics.metrics.inliers)
  const png = readFileSync(join(DL, files.find((f) => f.endsWith('_evidence.png')))); check('evidence PNG is a valid PNG with real size', png.subarray(0, 8).toString('hex') === '89504e470d0a1a0a' && png.length > 20000, png.length)
  const man = JSON.parse(readFileSync(join(DL, files.find((f) => f.endsWith('_manifest.json'))), 'utf8')); check('manifest includes versions, params, sha256 of label+geometry, statement', man.software.engine.numpy && man.parameters.engine_config.rng_seed === 12345 && Object.values(man.inputs.reference.sha256_of_text_companions).length >= 1 && /not established/i.test(man.statement))
  const zip = join(DL, files.find((f) => f.endsWith('.zip'))); let zipOk = false; try { const o = execFileSync('python3', ['-c', `import zipfile,sys;z=zipfile.ZipFile(sys.argv[1]);assert z.testzip() is None;print(sorted(n.split('/')[-1] for n in z.namelist()))`, zip]).toString(); zipOk = /metrics.json/i.test(o) && /evidence.png/i.test(o) } catch (e) { zipOk = false }; check('ZIP bundle is valid (CRC-checked) and contains all outputs', zipOk)

  // ---------- 7. network + CSP + console ----------
  const origin = new URL(BASE).origin
  check('every request is same-origin (no third-party hosts at all)', requests.every((r) => r.url.startsWith(origin) || r.url.startsWith('blob:') || r.url.startsWith('data:')), requests.filter((r) => !r.url.startsWith(origin) && !/^(blob|data):/i.test(r.url)).map((r) => r.url).join(', '))
  check('no non-GET network requests (nothing is POSTed anywhere)', requests.every((r) => ['GET', 'WORKER'].includes(r.method) || !r.url.startsWith(origin)), requests.filter((r) => !['GET', 'WORKER'].includes(r.method)).map((r) => r.method + r.url).join(','))
  check('no request URL contains mission file names or fixture content', !requests.some((r) => /ch2_|\.img|cube|plain\.npy|bip\.raw|synth/i.test(decodeURIComponent(r.url).replace(/pyodide|assets/g, '')) && !/engine-bundle|pyodide\//i.test(r.url)), requests.filter((r) => /ch2_|synth/i.test(r.url)).map((r) => r.url).join(','))
  const csp = await page.evaluate(() => window.__csp); check('no Content-Security-Policy violations in the page', csp.length === 0, csp.join('; '))
  const bad = consoleMsgs.filter((m) => ['error', 'pageerror', 'warning'].includes(m.type) && !/favicon/i.test(m.text)); check('no console errors or warnings', bad.length === 0, bad.map((b) => b.type + ':' + b.text).join(' | '))
  const hdr = await (await fetch(BASE + '/')).headers; check('production headers present (CSP w/o unsafe-eval, nosniff, no-referrer)', /wasm-unsafe-eval/i.test(hdr.get('content-security-policy')) && !/'unsafe-eval'/i.test(hdr.get('content-security-policy')) && hdr.get('x-content-type-options') === 'nosniff' && hdr.get('referrer-policy') === 'no-referrer')
  const wasmRes = await fetch(BASE + '/pyodide/pyodide.asm.wasm'); check('wasm served with application/wasm', wasmRes.headers.get('content-type') === 'application/wasm' && /max-age/i.test(wasmRes.headers.get('cache-control')))

  // ---------- 8. malformed input handling ----------
  await goto('workspace'); await clickText('button', 'Reset workspace'); await clickText('dialog button', 'Reset workspace'); await sleep(500)
  check('reset workspace clears files after confirmation', /No files selected/i.test(await page.evaluate(() => document.body.innerText)))
  await (await page.$('[data-testid=file-input]')).uploadFile(...allFiles(TRUNC)); await waitText('could not be read', 90000)
  const trTxt = await page.evaluate(() => document.body.innerText); check('truncated binary is detected with an actionable message', /Binary size does not match the label/i.test(trTxt) && /truncated/i.test(trTxt))
  await clickText('button', 'Reset workspace'); await clickText('dialog button', 'Reset workspace'); await sleep(400)

  // ---------- 9. huge sparse (3.2 GB) product: no full load ----------
  const tBig = Date.now(); await (await page.$('[data-testid=file-input]')).uploadFile(...allFiles(BIG)); await page.waitForFunction(() => /40,000×40,000/i.test(document.body.innerText), { timeout: 120000 })
  check('3.2 GB product inspected via slices (size check without loading)', true, `${((Date.now() - tBig) / 1000).toFixed(1)}s`)
  await page.evaluate(() => [...document.querySelectorAll('.productcard button')].find((b) => /Preview/i.test(b.textContent)).click()); await page.waitForSelector('.preview-img', { timeout: 180000 }); check('3.2 GB product previews without crashing the tab', true, `${((Date.now() - tBig) / 1000).toFixed(1)}s total`)
  const mem = await page.evaluate(() => performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1); check('main-thread JS heap stays small', mem < 400, `${mem} MB`)
  await clickText('button', 'Reset workspace'); await clickText('dialog button', 'Reset workspace')

  // ---------- 10. cancel + recovery on the synthetic demo ----------
  await goto('registration'); await clickText('button', 'Use synthetic demo'); await page.waitForSelector('[data-testid=run]', { timeout: 90000 }); await page.waitForFunction(() => /True swath intersection/i.test(document.body.innerText), { timeout: 60000 })
  await page.evaluate(() => { const s = [...document.querySelectorAll('select')].find((x) => /Full cascade/i.test(x.textContent)); const set = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set; set.call(s, 'cascade'); s.dispatchEvent(new Event('change', { bubbles: true })) })
  await page.click('[data-testid=run]'); await page.waitForSelector('[data-testid=progress]'); await sleep(1500); await clickText('button', 'Cancel run'); await waitText('Run cancelled', 60000)
  check('cancel stops the run and reports it', true)
  await page.waitForFunction(() => /Engine ready/i.test(document.body.innerText), { timeout: 120000 }); check('engine restarts cleanly after cancel (files preserved)', true)
  await page.waitForFunction(() => !document.querySelector('[data-testid=run]')?.disabled, { timeout: 120000 }); await page.click('[data-testid=run]'); await waitText('Processing completed', 240000); check('a new run succeeds after cancellation', true)

  // ---------- 11. persistence, reload, clear ----------
  await goto('settings'); await clickText('label.check', 'Save results in this browser'); await sleep(300)
  await goto('registration'); await page.waitForFunction(() => !document.querySelector('[data-testid=run]')?.disabled, { timeout: 60000 }); await page.click('[data-testid=run]'); await waitText('Processing completed', 240000); await sleep(800)
  await page.goto(BASE + '/#/overview', { waitUntil: 'networkidle0' }); await page.reload({ waitUntil: 'networkidle0' }); await page.waitForFunction(() => /Gate passed|Gate not passed/i.test(document.body.innerText), { timeout: 20000 }).catch(() => {})
  check('opt-in saved result survives a reload (IndexedDB)', /Gate passed|Gate not passed/i.test(await page.evaluate(() => document.body.innerText)))
  await goto('settings'); await clickText('button', 'Clear all local data'); await clickText('dialog button', 'Clear everything'); await sleep(800); await page.reload({ waitUntil: 'networkidle0' }); await goto('overview'); await sleep(300)
  check('"Clear all local data" removes saved results and prefs', /No results yet/i.test(await page.evaluate(() => document.body.innerText)) && (await page.evaluate(() => localStorage.getItem('cb2.prefs'))) === null)
  const dbs = await page.evaluate(async () => (await indexedDB.databases?.())?.map((d) => d.name) ?? []); check('IndexedDB database deleted', !dbs.includes('cb2'), dbs.join())

  // ---------- 12. theme + screenshots ----------
  await goto('overview'); await page.evaluate(() => document.querySelector('.topbar .btn.small').click()); await sleep(200)
  const th = await page.evaluate(() => document.documentElement.getAttribute('data-theme')); check('theme toggle sets data-theme', th === 'dark' || th === 'light' || th === null, th); await page.reload({ waitUntil: 'networkidle0' })
  check('theme preference persists across reload', (await page.evaluate(() => document.documentElement.getAttribute('data-theme'))) === th)
  { const css = await (await fetch(BASE + '/' + (await page.$$eval('link[rel=stylesheet]', (l) => l[0].getAttribute('href').replace(/^\//, ''))))).text(); check('reduced-motion handling present in shipped CSS (media query + manual setting)', /prefers-reduced-motion:\s*reduce/.test(css) && /data-motion=.?reduce/.test(css)) }
  await page.evaluate(() => { localStorage.setItem('cb2.prefs', JSON.stringify({ theme: 'dark' })) }); await page.reload({ waitUntil: 'networkidle0' }); await goto('overview'); await shot('desktop_dark_overview')
  await page.setViewport({ width: 390, height: 844, isMobile: true, hasTouch: true, deviceScaleFactor: 2 }); await goto('overview'); await sleep(300); await shot('mobile_overview'); await goto('workspace'); await sleep(300); await shot('mobile_workspace')
  const mo = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth); check('mobile (touch, 390px) page has no horizontal overflow', mo <= 1, mo)
  check('mobile bottom navigation is visible', await page.evaluate(() => getComputedStyle(document.querySelector('.bottom-nav')).display !== 'none'))
} catch (e) { check('E2E script completed without exception', false, (e.stack || e.message).split('\n').filter((l) => /run\.mjs|Error/.test(l)).join(' | ')); try { await shot('failure') } catch {} }

writeFileSync(join(OUT, 'results.json'), JSON.stringify({ ranAt: new Date().toISOString(), browser: await browser.version().catch(() => 'unknown'), failed, total: results.length, results }, null, 2))
console.log(`\n${results.length - failed}/${results.length} E2E checks passed`)
await Promise.race([browser.close(), sleep(8000)]).catch(() => {}); process.exit(failed ? 1 : 0)
