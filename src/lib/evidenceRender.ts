import type { RunPayload } from './types'
import { fmtNum, fmtPct, sensorLabel } from './format'

export interface Panels { ref: CanvasImageSource | null; src: CanvasImageSource | null; aligned: CanvasImageSource | null }
export interface RenderOpts {
  showInliers: boolean; showOutliers: boolean; showLines: boolean
  /** view transform in *preview-pixel* coordinates: screen = (p*scale + offset) */
  scale: number; ox: number; oy: number
  mode: 'side' | 'overlay'; overlayAlpha: number; overlaySource: 'before' | 'after'
  theme: { bg: string; text: string; muted: string; border: string; ok: string; bad: string; accent: string }
}

const mark = (ctx: CanvasRenderingContext2D, x: number, y: number, inlier: boolean, t: RenderOpts['theme']) => {
  ctx.lineWidth = 1.6
  if (inlier) { ctx.strokeStyle = t.ok; ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2); ctx.stroke() }          // inlier = ring
  else { ctx.strokeStyle = t.bad; ctx.beginPath(); ctx.moveTo(x - 3.5, y - 3.5); ctx.lineTo(x + 3.5, y + 3.5); ctx.moveTo(x + 3.5, y - 3.5); ctx.lineTo(x - 3.5, y + 3.5); ctx.stroke() } // outlier = cross
}

/** Draws the evidence view into any 2-D context (screen canvas or offscreen export canvas). */
export function renderEvidence(ctx: CanvasRenderingContext2D, W: number, H: number, p: RunPayload, panels: Panels, o: RenderOpts) {
  const t = o.theme; ctx.save(); ctx.fillStyle = t.bg; ctx.fillRect(0, 0, W, H)
  const g = p.grid; if (!g) { ctx.fillStyle = t.muted; ctx.fillText('No common-grid evidence available.', 20, 30); ctx.restore(); return }
  const s = g.preview_scale; const pw = g.preview_w, ph = g.preview_h
  const gap = 12; const headH = 0
  const panelsN = o.mode === 'side' ? 2 : 1; const pwScreen = (W - gap * (panelsN - 1)) / panelsN
  const drawPanel = (idx: number, img: CanvasImageSource | null, title: string, which: 'ref' | 'src' | 'overlay') => {
    const x0 = idx * (pwScreen + gap)
    ctx.save(); ctx.beginPath(); ctx.rect(x0, headH, pwScreen, H - headH); ctx.clip()
    ctx.fillStyle = t.bg; ctx.fillRect(x0, headH, pwScreen, H - headH)
    ctx.translate(x0 + o.ox, headH + o.oy); ctx.scale(o.scale, o.scale)
    ctx.imageSmoothingEnabled = o.scale < 3
    if (which === 'overlay') {
      if (panels.ref) ctx.drawImage(panels.ref, 0, 0, pw, ph)
      const top = o.overlaySource === 'after' ? panels.aligned : panels.src
      if (top) { ctx.globalAlpha = o.overlayAlpha; ctx.drawImage(top, 0, 0, pw, ph); ctx.globalAlpha = 1 }
    } else if (img) ctx.drawImage(img, 0, 0, pw, ph)
    ctx.strokeStyle = t.border; ctx.lineWidth = 1 / o.scale; ctx.strokeRect(0, 0, pw, ph)
    // points (drawn in screen space for constant marker size)
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    const pts = p.points; const useSrc = which === 'src'
    for (let i = 0; i < pts.ref.length; i++) {
      const inl = pts.inlier[i] === 1; if ((inl && !o.showInliers) || (!inl && !o.showOutliers)) continue
      let q = useSrc ? pts.src[i] : pts.ref[i]
      if (which === 'overlay') q = o.overlaySource === 'after' ? pts.ref[i] : pts.src[i]
      const sx = x0 + o.ox + (q[0] / s) * o.scale, sy = headH + o.oy + (q[1] / s) * o.scale
      if (sx < x0 - 6 || sx > x0 + pwScreen + 6 || sy < -6 || sy > H + 6) continue
      mark(ctx, sx, sy, inl, t)
    }
    ctx.restore()
    ctx.save(); ctx.font = '600 12px Inter, system-ui, sans-serif'; ctx.fillStyle = t.bg; ctx.globalAlpha = 0.72; const tw = ctx.measureText(title).width + 14; ctx.fillRect(x0 + 6, 6, tw, 22); ctx.globalAlpha = 1; ctx.fillStyle = t.text; ctx.fillText(title, x0 + 13, 21); ctx.restore()
  }
  if (o.mode === 'side') {
    drawPanel(0, panels.ref, `Reference · ${sensorLabel(p.ref.sensor)}`, 'ref'); drawPanel(1, panels.src, `Source · ${sensorLabel(p.src.sensor)}`, 'src')
    if (o.showLines) {
      ctx.save(); ctx.lineWidth = 1; const x1 = pwScreen + gap; const pts = p.points
      for (let i = 0; i < pts.ref.length; i += Math.max(1, Math.floor(pts.ref.length / 400))) {
        const inl = pts.inlier[i] === 1; if ((inl && !o.showInliers) || (!inl && !o.showOutliers)) continue
        const a = pts.ref[i], b = pts.src[i]
        const ax = o.ox + (a[0] / s) * o.scale, ay = o.oy + (a[1] / s) * o.scale, bx = x1 + o.ox + (b[0] / s) * o.scale, by = o.oy + (b[1] / s) * o.scale
        if (ax < 0 || ax > pwScreen || bx < x1 || bx > x1 + pwScreen) continue
        ctx.strokeStyle = inl ? t.ok : t.bad; ctx.globalAlpha = inl ? 0.55 : 0.8; ctx.setLineDash(inl ? [] : [4, 3]); ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke()
      }
      ctx.restore()
    }
  } else drawPanel(0, null, o.overlaySource === 'after' ? 'Reference + aligned source' : 'Reference + source (before alignment)', 'overlay')
  ctx.restore()
}

/** Full export composition with a header and a text legend (no information is conveyed by colour alone). */
export async function renderEvidencePng(p: RunPayload, panels: Panels, theme: RenderOpts['theme'], title: string): Promise<Blob> {
  const g = p.grid; const pw = g?.preview_w ?? 600, ph = g?.preview_h ?? 400
  const scale = Math.min(1, 900 / pw); const panelW = Math.round(pw * scale), panelH = Math.round(ph * scale)
  const W = panelW * 2 + 12 + 40, headH = 110, footH = 70, H = headH + panelH + footH + 20
  const c = document.createElement('canvas'); c.width = W; c.height = H; const ctx = c.getContext('2d')!
  ctx.fillStyle = theme.bg; ctx.fillRect(0, 0, W, H)
  ctx.fillStyle = theme.text; ctx.font = '700 20px Inter, system-ui, sans-serif'; ctx.fillText(title, 20, 32)
  ctx.font = '500 13px Inter, system-ui, sans-serif'; ctx.fillStyle = theme.muted
  const m = p.metrics
  ctx.fillText(`Evidence gate: ${p.status === 'VALIDATED' ? 'PASSED' : 'NOT PASSED (insufficient evidence)'}   ·   Independent ground-truth validation: NOT ESTABLISHED`, 20, 54)
  ctx.fillText(`Inliers ${m.inliers}/${m.tentative_matches} (${fmtPct(m.inlier_ratio)})   ·   coverage ${fmtPct(m.coverage, 0)}   ·   RMSE ${fmtNum(m.rmse_px, 3, 'px')}${m.rmse_m != null ? ' = ' + fmtNum(m.rmse_m, 2, 'm') : ''}   ·   common-grid GSD ${fmtNum(m.target_gsd_m, 2, 'm')}`, 20, 74)
  ctx.fillText('Common-grid evidence view (not a raw-image overlay). Ring = RANSAC inlier · Cross = outlier. Solid lines = inliers, dashed = outliers.', 20, 94)
  const sub = document.createElement('canvas'); sub.width = W - 40; sub.height = panelH; const sctx = sub.getContext('2d')!
  renderEvidence(sctx, sub.width, sub.height, p, panels, { showInliers: true, showOutliers: true, showLines: true, scale, ox: 0, oy: 0, mode: 'side', overlayAlpha: 0.5, overlaySource: 'after', theme })
  ctx.drawImage(sub, 20, headH)
  ctx.fillStyle = theme.muted; ctx.font = '500 12px "JetBrains Mono", monospace'
  ctx.fillText(`CHANDRABHAR-2 · ${p.engine.python}/numpy ${p.engine.numpy}/OpenCV ${p.engine.opencv} · ${p.finished_utc}`, 20, H - 30)
  ctx.fillText('Synthetic or mission data are processed locally. This image is evidence of internal consistency only.', 20, H - 12)
  return await new Promise<Blob>((res, rej) => c.toBlob((b) => (b ? res(b) : rej(new Error('PNG encode failed'))), 'image/png'))
}
