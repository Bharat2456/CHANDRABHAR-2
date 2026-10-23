export const fmtBytes = (n: number | null | undefined) => {
  if (n == null || !Number.isFinite(n)) return '—'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']; let i = 0; let v = n
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++ }
  return `${v >= 100 || i === 0 ? v.toFixed(0) : v.toFixed(1)} ${u[i]}`
}
export const fmtNum = (v: number | null | undefined, d = 3, unit = '') => (v == null || !Number.isFinite(v) ? '—' : `${v.toFixed(d)}${unit ? ' ' + unit : ''}`)
export const fmtInt = (v: number | null | undefined) => (v == null || !Number.isFinite(v) ? '—' : Math.round(v).toLocaleString('en-US'))
export const fmtPct = (v: number | null | undefined, d = 1) => (v == null || !Number.isFinite(v) ? '—' : `${(v * 100).toFixed(d)}%`)
export const fmtSec = (s: number | null | undefined) => (s == null ? '—' : s < 60 ? `${s.toFixed(1)} s` : `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`)
export const sensorLabel = (s: string) => (s === 'TMC2' || s === 'TMC' ? 'TMC-2' : s)
export const sensorKey = (s: string) => ({ OHRC: 'ohrc', TMC2: 'tmc2', TMC: 'tmc2', IIRS: 'iirs' } as Record<string, string>)[s] ?? 'other'
