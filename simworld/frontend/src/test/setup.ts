/**
 * 前端測試環境設定
 * 
 * 為 Vitest 設定全域測試環境，包括：
 * - DOM 環境配置
 * - 全域 Mock 設定
 * - Console 錯誤收集
 * - API Mock 配置
 */

import '@testing-library/jest-dom'
import { vi } from 'vitest'

// =============================================================================
// 全域 Mock 設定
// =============================================================================

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}))

// Mock Canvas API for 3D 仿真
Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {
  value: vi.fn().mockImplementation((contextType: string) => {
    if (contextType === 'webgl' || contextType === 'webgl2') {
      return {
        // WebGL context mock for 3D satellite visualization
        createShader: vi.fn(),
        shaderSource: vi.fn(),
        compileShader: vi.fn(),
        createProgram: vi.fn(),
        attachShader: vi.fn(),
        linkProgram: vi.fn(),
        useProgram: vi.fn(),
        clearColor: vi.fn(),
        clear: vi.fn(),
        drawElements: vi.fn(),
        drawArrays: vi.fn(),
        uniform1f: vi.fn(),
        uniform2f: vi.fn(),
        uniform3f: vi.fn(),
        uniform4f: vi.fn(),
        uniformMatrix4fv: vi.fn(),
        bindBuffer: vi.fn(),
        bufferData: vi.fn(),
        createBuffer: vi.fn(),
        deleteBuffer: vi.fn(),
        viewport: vi.fn(),
        enable: vi.fn(),
        disable: vi.fn(),
        blendFunc: vi.fn(),
        depthFunc: vi.fn()
      }
    }
    if (contextType === '2d') {
      return {
        // 2D context mock for charts
        beginPath: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        stroke: vi.fn(),
        fill: vi.fn(),
        arc: vi.fn(),
        fillText: vi.fn(),
        measureText: vi.fn().mockReturnValue({ width: 100 }),
        clearRect: vi.fn(),
        save: vi.fn(),
        restore: vi.fn(),
        translate: vi.fn(),
        rotate: vi.fn(),
        scale: vi.fn()
      }
    }
    return null
  })
})

// =============================================================================
// Console 錯誤收集系統
// =============================================================================

interface ConsoleError {
  type: 'error' | 'warn' | 'info'
  message: string
  timestamp: number
  stack?: string
}

class ConsoleErrorCollector {
  private errors: ConsoleError[] = []
  private originalConsole: {
    error: typeof console.error
    warn: typeof console.warn
    info: typeof console.info
  }

  constructor() {
    this.originalConsole = {
      error: console.error,
      warn: console.warn,
      info: console.info
    }
    
    this.setupInterceptors()
  }

  private setupInterceptors() {
    // 攔截 console.error
    console.error = (...args: any[]) => {
      const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ')
      
      this.errors.push({
        type: 'error',
        message,
        timestamp: Date.now(),
        stack: new Error().stack
      })
      
      // 仍然輸出到原本的 console
      this.originalConsole.error(...args)
    }

    // 攔截 console.warn
    console.warn = (...args: any[]) => {
      const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ')
      
      this.errors.push({
        type: 'warn',
        message,
        timestamp: Date.now()
      })
      
      this.originalConsole.warn(...args)
    }
  }

  getErrors(type?: 'error' | 'warn' | 'info'): ConsoleError[] {
    return type ? this.errors.filter(e => e.type === type) : this.errors
  }

  clearErrors(): void {
    this.errors = []
  }

  hasErrors(): boolean {
    return this.errors.some(e => e.type === 'error')
  }

  hasWarnings(): boolean {
    return this.errors.some(e => e.type === 'warn')
  }

  restore(): void {
    console.error = this.originalConsole.error
    console.warn = this.originalConsole.warn
    console.info = this.originalConsole.info
  }
}

// 全域錯誤收集器
export const consoleErrorCollector = new ConsoleErrorCollector()

// =============================================================================
// API Mock 設定
// =============================================================================

// Mock fetch for API calls
global.fetch = vi.fn()

// NetStack API Mock 回應
export const mockNetstackResponses = {
  '/api/v1/health': {
    status: 'healthy',
    timestamp: Date.now(),
    services: {
      netstack_api: 'up',
      database: 'up',
      simworld_bridge: 'up'
    }
  },
  '/api/v1/satellites': {
    satellites: [
      { id: 'sat_001', name: 'StarLink-1', latitude: 45.0, longitude: -120.0, altitude: 550000 },
      { id: 'sat_002', name: 'StarLink-2', latitude: 50.0, longitude: -115.0, altitude: 560000 }
    ],
    count: 2,
    timestamp: Date.now()
  },
  '/api/v1/handover/strategy/switch': {
    success: true,
    switch_time: 25.5,
    target_satellite: 'sat_002',
    handover_reason: 'signal_quality_improvement'
  },
  '/api/v1/devices': {
    devices: [
      { id: 'ue_001', type: 'smartphone', connected_satellite: 'sat_001' },
      { id: 'ue_002', type: 'iot_sensor', connected_satellite: 'sat_002' }
    ]
  }
}

// SimWorld API Mock 回應
export const mockSimworldResponses = {
  '/api/satellites': {
    satellites: [
      { 
        id: 'sat_001', 
        position: { x: 1000000, y: 2000000, z: 550000 },
        velocity: { x: 7500, y: 0, z: 0 },
        coverage_radius: 500000
      }
    ]
  },
  '/api/devices': {
    devices: [
      { id: 'ue_001', position: { lat: 25.0, lng: 121.5 }, signal_strength: -75 }
    ]
  },
  '/api/measurements': {
    measurements: [
      { 
        event_type: 'A4', 
        rsrp: -85, 
        rsrq: -12, 
        sinr: 15, 
        timestamp: Date.now() 
      }
    ]
  }
}

// 設定 Mock fetch 行為
export function setupApiMocks() {
  (global.fetch as any).mockImplementation((url: string, options?: RequestInit) => {
    const urlObj = new URL(url, 'http://localhost')
    const path = urlObj.pathname
    
    // NetStack API Mock
    if (url.includes('netstack') || url.includes(':8080')) {
      const response = mockNetstackResponses[path as keyof typeof mockNetstackResponses]
      if (response) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(response),
          text: () => Promise.resolve(JSON.stringify(response))
        })
      }
    }
    
    // SimWorld API Mock
    if (url.includes('simworld') || url.includes(':8888')) {
      const response = mockSimworldResponses[path as keyof typeof mockSimworldResponses]
      if (response) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: () => Promise.resolve(response),
          text: () => Promise.resolve(JSON.stringify(response))
        })
      }
    }
    
    // 預設 404 回應
    return Promise.resolve({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ error: 'Not Found' }),
      text: () => Promise.resolve('Not Found')
    })
  })
}

// =============================================================================
// 測試工具函數
// =============================================================================

/**
 * 等待 DOM 更新完成
 */
export const waitForDOMUpdate = () => new Promise(resolve => setTimeout(resolve, 0))

/**
 * 模擬延遲
 */
export const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * 檢查是否有 console 錯誤
 */
export function expectNoConsoleErrors() {
  const errors = consoleErrorCollector.getErrors('error')
  if (errors.length > 0) {
    throw new Error(`發現 console 錯誤: ${errors.map(e => e.message).join(', ')}`)
  }
}

/**
 * 檢查是否有 console 警告
 */
export function expectNoConsoleWarnings() {
  const warnings = consoleErrorCollector.getErrors('warn')
  if (warnings.length > 0) {
    throw new Error(`發現 console 警告: ${warnings.map(w => w.message).join(', ')}`)
  }
}

// =============================================================================
// 測試生命週期設定
// =============================================================================

// 每個測試前的設定
beforeEach(() => {
  // 清除 console 錯誤記錄
  consoleErrorCollector.clearErrors()
  
  // 設定 API Mock
  setupApiMocks()
  
  // 清除所有 Mock 狀態
  vi.clearAllMocks()
})

// 每個測試後的清理
afterEach(() => {
  // 檢查是否有未處理的 console 錯誤（除非測試明確允許）
  const errors = consoleErrorCollector.getErrors('error')
  if (errors.length > 0) {
    console.warn(`測試結束時發現 ${errors.length} 個 console 錯誤：`, errors)
  }
})

// 所有測試結束後的清理
afterAll(() => {
  consoleErrorCollector.restore()
})

console.log('🧪 前端測試環境已初始化完成')