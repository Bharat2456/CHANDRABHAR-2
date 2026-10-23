import { useEffect, useRef, type ReactNode } from 'react'

const P: Record<string, string> = {
  home: 'M3 11l9-8 9 8M5 10v10h5v-6h4v6h5V10', folder: 'M3 6a2 2 0 012-2h4l2 2h8a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2z', align: 'M4 7h10M4 12h16M4 17h10M18 5v4M18 15v4', lab: 'M9 3v6L4 19a2 2 0 002 3h12a2 2 0 002-3l-5-10V3M8 3h8', shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z', file: 'M6 3h8l4 4v14H6zM14 3v4h4M9 13h6M9 17h6', gear: 'M12 8a4 4 0 100 8 4 4 0 000-8zM3 12h3M18 12h3M12 3v3M12 18v3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1',
  check: 'M5 12l5 5 9-10', x: 'M6 6l12 12M18 6L6 18', warn: 'M12 3l10 18H2zM12 10v5M12 18v.01', info: 'M12 8v.01M11 12h1v5h1M12 2a10 10 0 100 20 10 10 0 000-20z', upload: 'M12 16V4M7 9l5-5 5 5M4 20h16', download: 'M12 4v12M7 11l5 5 5-5M4 20h16', trash: 'M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13', play: 'M7 4l13 8-13 8z', stop: 'M6 6h12v12H6z', lock: 'M6 11h12v10H6zM8 11V7a4 4 0 018 0v4', loader: 'M12 3a9 9 0 109 9', moon: 'M20 14a8 8 0 11-10-10 6 6 0 0010 10z', sun: 'M12 8a4 4 0 100 8 4 4 0 000-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19', eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12zM12 9a3 3 0 100 6 3 3 0 000-6z', chev: 'M9 6l6 6-6 6',
}
export function Icon({ n, className = '', spin = false }: { n: keyof typeof P | string; className?: string; spin?: boolean }) {
  return <svg className={`icon ${spin ? 'spin' : ''} ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={P[n] ?? P.info} /></svg>
}

export type Tone = 'ok' | 'warn' | 'bad' | 'info' | 'mute'
const SYMBOL: Record<Tone, string> = { ok: 'check', warn: 'warn', bad: 'x', info: 'info', mute: 'info' }
/** Status is always conveyed by icon + text, never colour alone. */
export function Badge({ tone, children, icon = true }: { tone: Tone; children: ReactNode; icon?: boolean }) {
  return <span className={`badge ${tone}`}>{icon && <Icon n={SYMBOL[tone]} />}{children}</span>
}
export function Notice({ tone = 'info', title, children }: { tone?: 'ok' | 'warn' | 'bad' | 'info'; title?: string; children: ReactNode }) {
  return <div className={`notice ${tone}`} role={tone === 'bad' ? 'alert' : 'status'}><Icon n={SYMBOL[tone]} /><div>{title && <p><b>{title}</b></p>}{children}</div></div>
}
export function Stat({ k, v, u, title }: { k: string; v: ReactNode; u?: string; title?: string }) {
  return <div className="stat" title={title}><span className="k">{k}</span><span className="v">{v}{u && <span className="u"> {u}</span>}</span></div>
}
export function Progress({ value, label }: { value: number | null; label: string }) {
  const det = value != null
  return <div className={`progress ${det ? '' : 'indet'}`} role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} {...(det ? { 'aria-valuenow': Math.round(value! * 100) } : {})}><i style={det ? { width: `${Math.max(2, value! * 100)}%` } : undefined} /></div>
}
export function PageHead({ kicker, title, children }: { kicker: string; title: string; children?: ReactNode }) {
  return <div className="page-head"><div><div className="kicker">{kicker}</div><h1 id="page-title" tabIndex={-1}>{title}</h1>{children}</div></div>
}

/** Accessible confirm dialog built on the native <dialog> (focus trap + Esc come from the platform). */
export function Confirm({ open, title, body, confirmLabel, onConfirm, onCancel, danger = true }: { open: boolean; title: string; body: ReactNode; confirmLabel: string; onConfirm: () => void; onCancel: () => void; danger?: boolean }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { const d = ref.current; if (!d) return; if (open && !d.open) d.showModal(); if (!open && d.open) d.close() }, [open])
  return (
    <dialog ref={ref} onCancel={(e) => { e.preventDefault(); onCancel() }} aria-labelledby="dlg-t">
      <h2 id="dlg-t">{title}</h2><div className="small">{body}</div>
      <div className="row"><button className="btn" onClick={onCancel} autoFocus>Cancel</button><button className={`btn ${danger ? 'danger' : 'primary'}`} onClick={onConfirm}>{confirmLabel}</button></div>
    </dialog>
  )
}
