import { vi, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
vi.mock('cytoscape', () => {
  const chain: any = new Proxy(function () {}, { get: (_t, p) => p === 'then' ? undefined : (p === 'zoom' ? () => 1 : () => chain), apply: () => chain })
  return { default: () => chain }
})
window.matchMedia = window.matchMedia || ((q: string) => ({ matches: false, media: q, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, onchange: null, dispatchEvent: () => false }) as any)
afterEach(() => { cleanup(); localStorage.clear(); document.documentElement.dataset.theme = 'dark' })

;(globalThis as any).ResizeObserver = (globalThis as any).ResizeObserver || class { observe() {} unobserve() {} disconnect() {} }
