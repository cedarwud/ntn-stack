/// <reference types="vitest" />
import type { MockInstance } from 'vitest'

declare global {
  const vi: typeof import('vitest').vi
  
  interface Window {
    matchMedia: MockInstance
  }
  
  interface HTMLCanvasElement {
    getContext: MockInstance
    toDataURL: MockInstance
  }
} 