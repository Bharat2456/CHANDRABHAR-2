import { describe, it, expect } from 'vitest'
import { maxDisplacement, applyH, coefficientDeltas } from './transformMetric'

const I = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
describe('transform-equivalence metric', () => {
  it('is zero for identical transforms and symmetric', () => { const H = [[1.002, -0.003, 0.5], [0.001, 0.999, -0.2], [1e-6, -4e-6, 1]]; expect(maxDisplacement(H, H, 199, 191)).toBe(0); expect(maxDisplacement(H, I, 199, 191)).toBeCloseTo(maxDisplacement(I, H, 199, 191), 9) })
  it('equals the translation for a pure shift', () => { expect(maxDisplacement(I, [[1, 0, 0.3], [0, 1, -0.4], [0, 0, 1]], 100, 100)).toBeCloseTo(0.5, 12) })
  it('makes grid-size dependence of coefficient errors explicit (0.002 ≈ 0.4 px on a 199×191 grid, 2 px on 1000×1000)', () => {
    const E = [[1.002, 0, 0], [0, 1, 0], [0, 0, 1]]
    expect(maxDisplacement(I, E, 199, 191)).toBeCloseTo(0.398, 3); expect(maxDisplacement(I, E, 1000, 1000)).toBeCloseTo(2.0, 9)
  })
  it('handles perspective terms', () => { const P = [[1, 0, 0], [0, 1, 0], [1e-3, 0, 1]]; const [x, y] = applyH(P, 100, 0); expect(x).toBeCloseTo(100 / 1.1, 9); expect(y).toBe(0); expect(maxDisplacement(I, P, 100, 100)).toBeGreaterThan(5) })
  it('reports per-coefficient deltas for diagnostics', () => { expect(coefficientDeltas([[1.1, 0, 0], [0, 1, 0], [0, 0, 1]], I)['H[0][0]']).toBeCloseTo(0.1, 12) })
})
