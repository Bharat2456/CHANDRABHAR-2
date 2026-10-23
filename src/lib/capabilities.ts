import type { MemoryPreset } from './types'
export interface Capabilities { worker: boolean; wasm: boolean; workerfsLikely: boolean; fileSystemAccess: boolean; directoryInput: boolean; indexedDB: boolean; deviceMemoryGB: number | null; cores: number | null; webgpu: boolean; mobile: boolean; secure: boolean; jsHeapLimitMB: number | null }
export function detectCapabilities(): Capabilities {
  const nav = navigator as Navigator & { deviceMemory?: number; gpu?: unknown }
  const perf = performance as Performance & { memory?: { jsHeapSizeLimit: number } }
  const input = document.createElement('input')
  return {
    worker: typeof Worker !== 'undefined', wasm: typeof WebAssembly === 'object', workerfsLikely: typeof Worker !== 'undefined' && typeof Blob !== 'undefined',
    fileSystemAccess: typeof (window as unknown as { showDirectoryPicker?: unknown }).showDirectoryPicker === 'function', directoryInput: 'webkitdirectory' in input,
    indexedDB: typeof indexedDB !== 'undefined', deviceMemoryGB: nav.deviceMemory ?? null, cores: navigator.hardwareConcurrency ?? null, webgpu: !!nav.gpu,
    mobile: /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) || (navigator.maxTouchPoints > 1 && window.innerWidth < 900), secure: window.isSecureContext,
    jsHeapLimitMB: perf.memory ? Math.round(perf.memory.jsHeapSizeLimit / 1048576) : null,
  }
}
export const PRESETS: Record<MemoryPreset['name'], MemoryPreset> = {
  conservative: { name: 'conservative', max_geometry_csv_mb: 64, max_grid_pixels: 4_000_000, max_preview_dim: 512, canvas_px: 1000 },
  standard: { name: 'standard', max_geometry_csv_mb: 256, max_grid_pixels: 12_000_000, max_preview_dim: 768, canvas_px: 1400 },
  extended: { name: 'extended', max_geometry_csv_mb: 512, max_grid_pixels: 24_000_000, max_preview_dim: 1024, canvas_px: 1800 },
}
export function resolvePreset(pref: 'auto' | MemoryPreset['name'], c: Capabilities): MemoryPreset {
  if (pref !== 'auto') return PRESETS[pref]
  if (c.mobile || (c.deviceMemoryGB != null && c.deviceMemoryGB <= 4)) return PRESETS.conservative
  return PRESETS.standard
}
