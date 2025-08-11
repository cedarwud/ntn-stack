/**
 * LEO 衛星換手研究測試工具集
 * 提供專用的測試工具和模擬數據
 */

import React, { ReactElement } from 'react'
import { render, RenderResult } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'

// 測試上下文提供者
import { AppStateProvider } from '../contexts/AppStateContext'
import { DeviceProvider } from '../contexts/DeviceContext'
import { DataSyncProvider } from '../contexts/DataSyncContext'
import { StrategyProvider } from '../contexts/StrategyContext'

/**
 * 衛星數據模擬工具
 */
export const mockSatelliteData = {
  createSatellite: (id: string, overrides: Partial<any> = {}) => ({
    id,
    name: `STARLINK-${id}`,
    norad_id: id,
    elevation_deg: 45,
    azimuth_deg: 180,
    distance_km: 550,
    estimated_signal_strength: 85,
    latitude: 25.0,
    longitude: 121.0,
    altitude: 550,
    ...overrides
  }),

  createSatelliteList: (count: number = 6) => 
    Array.from({ length: count }, (_, i) => 
      mockSatelliteData.createSatellite((1000 + i).toString())
    ),

  createHandoverScenario: () => ({
    currentSatellite: mockSatelliteData.createSatellite('1001', {
      elevation_deg: 15, // 即將離開視野
      estimated_signal_strength: 60
    }),
    targetSatellite: mockSatelliteData.createSatellite('1002', {
      elevation_deg: 35, // 更好的位置
      estimated_signal_strength: 90
    }),
    candidateSatellites: mockSatelliteData.createSatelliteList(4)
  })
}

/**
 * 設備數據模擬工具
 */
export const mockDeviceData = {
  createDevice: (id: number, overrides: Partial<any> = {}) => ({
    id,
    name: `Device-${id}`,
    x: 0,
    y: 0,
    z: 5,
    device_type: 'UAV',
    status: 'active',
    ...overrides
  }),

  createDeviceList: (count: number = 3) =>
    Array.from({ length: count }, (_, i) =>
      mockDeviceData.createDevice(i + 1)
    )
}

/**
 * API 響應模擬工具
 */
export const mockApiResponses = {
  success: <T>(data: T) => ({
    success: true,
    data,
    timestamp: new Date().toISOString()
  }),

  error: (message: string) => ({
    success: false,
    error: message,
    timestamp: new Date().toISOString()
  }),

  healthCheck: () => mockApiResponses.success({
    status: 'healthy',
    services: {
      'satellite-api': 'up',
      'device-api': 'up',
      'handover-engine': 'up'
    }
  })
}

/**
 * 測試渲染器 - 包含所有必要的 Context
 */
export function renderWithProviders(
  ui: ReactElement,
  options: {
    initialEntries?: string[]
    [key: string]: any
  } = {}
): RenderResult {
  const { initialEntries = ['/'], ...renderOptions } = options

  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(MemoryRouter, { initialEntries },
      React.createElement(StrategyProvider, null,
        React.createElement(AppStateProvider, null,
          React.createElement(DeviceProvider, null,
            React.createElement(DataSyncProvider, null,
              children
            )
          )
        )
      )
    )
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

/**
 * 性能測試工具
 */
export const performanceUtils = {
  measureRenderTime: async (renderFn: () => void): Promise<number> => {
    const start = performance.now()
    renderFn()
    await new Promise(resolve => setTimeout(resolve, 0)) // 等待渲染完成
    const end = performance.now()
    return end - start
  },

  measureMemoryUsage: (): number => {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize
    }
    return 0
  },

  createLoadTest: (component: ReactElement, iterations: number = 100) => async () => {
    const renderTimes: number[] = []
    
    for (let i = 0; i < iterations; i++) {
      const time = await performanceUtils.measureRenderTime(() => {
        render(component)
      })
      renderTimes.push(time)
    }
    
    return {
      average: renderTimes.reduce((a, b) => a + b, 0) / renderTimes.length,
      min: Math.min(...renderTimes),
      max: Math.max(...renderTimes),
      total: renderTimes.reduce((a, b) => a + b, 0)
    }
  }
}

/**
 * 衛星換手測試場景
 */
export const handoverTestScenarios = {
  /**
   * 標準換手場景 - 當前衛星信號降低，需要切換
   */
  standardHandover: () => ({
    initialState: {
      currentSatellite: mockSatelliteData.createSatellite('1001', {
        elevation_deg: 20,
        estimated_signal_strength: 70
      }),
      availableSatellites: mockSatelliteData.createSatelliteList(6)
    },
    trigger: {
      type: 'signal_degradation',
      threshold: 60
    },
    expectedResult: {
      shouldTriggerHandover: true,
      preferredTarget: '1002'
    }
  }),

  /**
   * 緊急換手場景 - 當前衛星即將離開視野
   */
  emergencyHandover: () => ({
    initialState: {
      currentSatellite: mockSatelliteData.createSatellite('1001', {
        elevation_deg: 8, // 接近地平線
        estimated_signal_strength: 40
      }),
      availableSatellites: mockSatelliteData.createSatelliteList(5)
    },
    trigger: {
      type: 'elevation_threshold',
      threshold: 10
    },
    expectedResult: {
      shouldTriggerHandover: true,
      urgency: 'high'
    }
  }),

  /**
   * 多候選選擇場景 - 有多個可行的換手目標
   */
  multipleTargets: () => ({
    initialState: {
      currentSatellite: mockSatelliteData.createSatellite('1001', {
        elevation_deg: 15,
        estimated_signal_strength: 65
      }),
      availableSatellites: [
        mockSatelliteData.createSatellite('1002', { elevation_deg: 45, estimated_signal_strength: 90 }),
        mockSatelliteData.createSatellite('1003', { elevation_deg: 50, estimated_signal_strength: 85 }),
        mockSatelliteData.createSatellite('1004', { elevation_deg: 30, estimated_signal_strength: 80 })
      ]
    },
    expectedResult: {
      bestTarget: '1003', // 最高仰角
      alternativeTargets: ['1002', '1004']
    }
  })
}

/**
 * 模擬 fetch API
 */
export const mockFetch = {
  success: <T>(data: T, delay: number = 0) => {
    return vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: async () => {
          if (delay > 0) {
            await new Promise(resolve => setTimeout(resolve, delay))
          }
          return mockApiResponses.success(data)
        }
      })
    )
  },

  error: (status: number = 500, message: string = 'Server Error') => {
    return vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: false,
        status,
        statusText: message,
        json: async () => mockApiResponses.error(message)
      })
    )
  },

  timeout: () => {
    return vi.fn().mockImplementation(() =>
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 100)
      )
    )
  }
}

/**
 * 常用測試斷言
 */
export const assertions = {
  expectSatelliteVisible: (satellite: any) => {
    expect(satellite.elevation_deg).toBeGreaterThan(0)
    expect(satellite.estimated_signal_strength).toBeGreaterThan(0)
  },

  expectHandoverTriggered: (handoverState: any) => {
    expect(handoverState.phase).not.toBe('stable')
    expect(handoverState.targetSatelliteId).toBeTruthy()
  },

  expectPerformanceWithinLimits: (renderTime: number, memoryUsage: number) => {
    expect(renderTime).toBeLessThan(100) // 100ms 渲染時間限制
    expect(memoryUsage).toBeLessThan(50 * 1024 * 1024) // 50MB 內存限制
  }
}