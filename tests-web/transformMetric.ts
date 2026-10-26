/**
 * Transform-equivalence metric for parity tests.
 *
 * Two homographies are compared by the worst-case displacement they impose on the common grid (corners + centre), in grid
 * pixels, rather than coefficient by coefficient: coefficients have grid-size-dependent physical meaning (a 0.002 error in
 * a linear term moves points by 0.002 x extent pixels) and a RANSAC fit is only resolvable to about its own sampling
 * uncertainty (see tools/parity_estimator_uncertainty.py).
 */
export type Mat3 = number[][]

export function applyH(H: Mat3, x: number, y: number): [number, number] {
  const w = H[2][0] * x + H[2][1] * y + H[2][2]
  return [(H[0][0] * x + H[0][1] * y + H[0][2]) / w, (H[1][0] * x + H[1][1] * y + H[1][2]) / w]
}

export function maxDisplacement(A: Mat3, B: Mat3, width: number, height: number): number {
  const pts: [number, number][] = [[0, 0], [width, 0], [0, height], [width, height], [width / 2, height / 2]]
  return Math.max(...pts.map(([x, y]) => { const [ax, ay] = applyH(A, x, y); const [bx, by] = applyH(B, x, y); return Math.hypot(ax - bx, ay - by) }))
}

/** Largest single-coefficient difference of the affine block / translation (for diagnostics only). */
export function coefficientDeltas(A: Mat3, B: Mat3) {
  const out: Record<string, number> = {}
  for (const [i, j] of [[0, 0], [0, 1], [1, 0], [1, 1], [0, 2], [1, 2], [2, 0], [2, 1]]) out[`H[${i}][${j}]`] = A[i][j] - B[i][j]
  return out
}
