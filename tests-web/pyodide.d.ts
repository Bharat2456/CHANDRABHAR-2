declare module '*/pyodide.mjs' {
  export function loadPyodide(options: Record<string, unknown>): Promise<any> // eslint-disable-line @typescript-eslint/no-explicit-any
}
