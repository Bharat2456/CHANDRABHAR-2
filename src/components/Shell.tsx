import { useEffect, useRef, useState, type ReactNode } from 'react'
import { store, useStore } from '../state/store'
import { Icon, Badge, Confirm } from './ui'
import { PRIVACY_STATEMENT } from '../lib/copy'

export const ROUTES = [
  { id: 'overview', label: 'Mission Overview', short: 'Overview', icon: 'home', grp: 'Orient' },
  { id: 'workspace', label: 'Data Workspace', short: 'Data', icon: 'folder', grp: 'Workflow' },
  { id: 'registration', label: 'Image Registration', short: 'Register', icon: 'align', grp: 'Workflow' },
  { id: 'lab', label: 'Correspondence Lab', short: 'Lab', icon: 'lab', grp: 'Workflow' },
  { id: 'evidence', label: 'Evidence & Results', short: 'Evidence', icon: 'shield', grp: 'Workflow' },
  { id: 'reports', label: 'Reports & Export', short: 'Export', icon: 'file', grp: 'Workflow' },
  { id: 'settings', label: 'Settings & About', short: 'Settings', icon: 'gear', grp: 'System' },
] as const
export type RouteId = (typeof ROUTES)[number]['id']

export function useRoute(): [RouteId, (r: RouteId) => void] {
  const parse = (): RouteId => { const h = location.hash.replace(/^#\/?/, '').split(/[/?]/)[0]; return (ROUTES.find((r) => r.id === h)?.id ?? 'overview') as RouteId }
  const [r, setR] = useState<RouteId>(parse)
  useEffect(() => { const f = () => setR(parse()); window.addEventListener('hashchange', f); return () => window.removeEventListener('hashchange', f) }, [])
  return [r, (x) => { location.hash = `#/${x}` }]
}

function EnginePill() {
  const e = useStore((s) => s.engine); const run = useStore((s) => s.run)
  const txt = run.status === 'running' ? 'Processing' : e.status === 'ready' ? 'Engine ready' : e.status === 'loading' ? `Loading engine${e.stage ? ' · ' + e.stage : ''}` : e.status === 'error' ? 'Engine error' : 'Engine idle'
  const tone = run.status === 'running' ? 'info' : e.status === 'ready' ? 'ok' : e.status === 'error' ? 'bad' : e.status === 'loading' ? 'warn' : 'mute'
  return <span className="engine-pill" role="status" aria-live="polite"><Badge tone={tone as 'ok'} icon={false}><Icon n={e.status === 'loading' || run.status === 'running' ? 'loader' : tone === 'ok' ? 'check' : tone === 'bad' ? 'x' : 'info'} spin={e.status === 'loading' || run.status === 'running'} /><span className="txt">{txt}</span></Badge></span>
}

export function Shell({ route, go, children }: { route: RouteId; go: (r: RouteId) => void; children: ReactNode }) {
  const theme = useStore((s) => s.prefs.theme); const toasts = useStore((s) => s.toasts); const inspection = useStore((s) => s.inspection); const result = useStore((s) => s.results.length); const running = useStore((s) => s.run.status === 'running')
  const [priv, setPriv] = useState(false); const main = useRef<HTMLElement>(null)
  const first = useRef(true)
  // Move focus to the page heading on route *changes* only (not on first load, so the skip link stays the first Tab stop).
  useEffect(() => { if (first.current) { first.current = false; return } document.getElementById('page-title')?.focus({ preventScroll: true }); window.scrollTo({ top: 0 }) }, [route])
  useEffect(() => { if (!running) return; const f = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = '' }; window.addEventListener('beforeunload', f); return () => window.removeEventListener('beforeunload', f) }, [running])
  const state = (id: string) => id === 'workspace' ? (inspection?.products.length ? `${inspection.products.length}` : '') : id === 'evidence' || id === 'lab' ? (result ? '●' : '') : ''
  const nextTheme = () => store.setPrefs({ theme: theme === 'dark' ? 'light' : theme === 'light' ? 'system' : 'dark' })
  let lastGrp = ''
  return (
    <div className="app">
      <a href="#main" className="skip" onClick={(e) => { e.preventDefault(); main.current?.focus() }}>Skip to content</a>
      <header className="topbar">
        <a className="brand" href="#/overview" aria-label="CHANDRABHAR-2 home"><img src="brand/logo-96.png" alt="" width="32" height="32" /><span><b>CHANDRABHAR-2</b><small>Lunar image registration</small></span></a>
        <div className="top-spacer" />
        <EnginePill />
        <button className="privacy" onClick={() => setPriv(true)} aria-haspopup="dialog"><span className="dot" aria-hidden="true" /><Icon n="lock" /><span><span className="long">Processed locally · </span>no upload</span></button>
        <button className="btn small ghost" onClick={nextTheme} aria-label={`Theme: ${theme}. Activate to change.`} title={`Theme: ${theme}`}><Icon n={theme === 'light' ? 'sun' : 'moon'} /><span className="sr-only">Change theme</span></button>
      </header>
      <nav className="nav" aria-label="Primary">
        <ol>{ROUTES.map((r) => { const g = r.grp !== lastGrp ? r.grp : ''; lastGrp = r.grp; return (
          <li key={r.id}>{g && <div className="grp" aria-hidden="true">{g}</div>}<a href={`#/${r.id}`} aria-current={route === r.id ? 'page' : undefined}><Icon n={r.icon} />{r.label}<span className="state faint">{state(r.id)}</span></a></li>) })}</ol>
        <div className="tricolor" style={{ marginTop: 24 }} aria-hidden="true" />
        <p className="xs faint" style={{ marginTop: 12 }}>Evidence language is deliberate: “validated” here means the configured gate passed, not that ground truth was established.</p>
      </nav>
      <main id="main" ref={main} tabIndex={-1} className="main" style={{ outline: 'none' }}>{children}</main>
      <nav className="bottom-nav" aria-label="Primary (mobile)">{ROUTES.map((r) => <a key={r.id} href={`#/${r.id}`} aria-current={route === r.id ? 'page' : undefined}><Icon n={r.icon} />{r.short}</a>)}</nav>
      <div className="toasts" aria-live="polite">{toasts.map((t) => <div key={t.id} className={`toast ${t.tone}`}><Icon n={t.tone === 'ok' ? 'check' : t.tone === 'bad' ? 'x' : t.tone === 'warn' ? 'warn' : 'info'} /><span>{t.text}</span><button aria-label="Dismiss" onClick={() => store.dismissToast(t.id)}>×</button></div>)}</div>
      <Confirm open={priv} title="Local processing" body={<><p>{PRIVACY_STATEMENT}</p><p className="muted">This does not protect against a compromised device or malicious browser extensions.</p></>} confirmLabel="Close" danger={false} onConfirm={() => setPriv(false)} onCancel={() => setPriv(false)} />
      <button hidden onClick={() => go('overview')} />
    </div>
  )
}
