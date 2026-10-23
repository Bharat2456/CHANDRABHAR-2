declare const __APP_VERSION__: string
declare const __ENGINE_VERSION__: string
export const APP_VERSION: string = typeof __APP_VERSION__ === 'string' ? __APP_VERSION__ : '0.0.0-dev'
export const ENGINE_VERSION: string = typeof __ENGINE_VERSION__ === 'string' ? __ENGINE_VERSION__ : 'dev'
