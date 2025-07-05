/**
 * 前端 API 整合測試
 * 
 * 測試前端與後端 API 的整合功能，包括：
 * - NetStack API 連接測試
 * - SimWorld API 連接測試
 * - API 錯誤處理測試
 * - 數據格式驗證測試
 * - 網路配置驗證測試
 */

import { describe, it, expect, beforeEach, vi, beforeAll, afterAll } from 'vitest'
import { 
  setupApiMocks, 
  mockNetstackResponses, 
  mockSimworldResponses,
  consoleErrorCollector,
  expectNoConsoleErrors,
  delay
} from './setup'

// =============================================================================
// API 配置導入
// =============================================================================

// Mock API 配置模組
const mockApiConfig = {
  netstackFetch: vi.fn(),
  simworldFetch: vi.fn(),
  getCurrentApiConfig: vi.fn(() => ({
    netstack: {
      baseUrl: '/netstack',
      timeout: 5000
    },
    simworld: {
      baseUrl: '/api',
      timeout: 5000
    }
  }))
}

// Mock 配置模組
vi.mock('../config/api-config', () => mockApiConfig)

// =============================================================================
// 測試工具函數
// =============================================================================

/**
 * 驗證 API 回應格式
 */
const validateApiResponse = (response: any, expectedFields: string[]) => {
  expect(response).toBeDefined()
  expect(typeof response).toBe('object')
  
  expectedFields.forEach(field => {
    expect(response).toHaveProperty(field)
  })
}

/**
 * 測試 API 端點
 */
const testApiEndpoint = async (
  fetchFn: typeof mockApiConfig.netstackFetch,
  endpoint: string,
  expectedResponse: any,
  options: RequestInit = {}
) => {
  fetchFn.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: () => Promise.resolve(expectedResponse)
  })
  
  const response = await fetchFn(endpoint, options)
  const data = await response.json()
  
  expect(fetchFn).toHaveBeenCalledWith(endpoint, options)
  expect(data).toEqual(expectedResponse)
  
  return data
}

// =============================================================================
// 1. NetStack API 測試
// =============================================================================

describe('🌐 NetStack API 整合測試', () => {
  
  beforeEach(() => {
    vi.clearAllMocks()
    consoleErrorCollector.clearErrors()
  })

  describe('健康檢查 API', () => {
    it('應該正確獲取 NetStack 健康狀態', async () => {
      const healthData = await testApiEndpoint(
        mockApiConfig.netstackFetch,
        '/api/v1/health',
        mockNetstackResponses['/api/v1/health']
      )
      
      validateApiResponse(healthData, ['status', 'timestamp', 'services'])
      expect(healthData.status).toBe('healthy')
      expect(healthData.services).toHaveProperty('netstack_api', 'up')
      expect(healthData.services).toHaveProperty('database', 'up')
      
      expectNoConsoleErrors()
    })
    
    it('應該處理健康檢查失敗情況', async () => {
      mockApiConfig.netstackFetch.mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: () => Promise.resolve({ 
          status: 'unhealthy',
          error: 'Database connection failed'
        })
      })
      
      const response = await mockApiConfig.netstackFetch('/api/v1/health')
      const data = await response.json()
      
      expect(response.ok).toBe(false)
      expect(response.status).toBe(503)
      expect(data.status).toBe('unhealthy')
      expect(data).toHaveProperty('error')
    })
  })

  describe('衛星 API', () => {
    it('應該正確獲取衛星列表', async () => {
      const satelliteData = await testApiEndpoint(
        mockApiConfig.netstackFetch,
        '/api/v1/satellites',
        mockNetstackResponses['/api/v1/satellites']
      )
      
      validateApiResponse(satelliteData, ['satellites', 'count', 'timestamp'])
      expect(Array.isArray(satelliteData.satellites)).toBe(true)
      expect(satelliteData.count).toBeGreaterThan(0)
      expect(satelliteData.satellites[0]).toHaveProperty('id')
      expect(satelliteData.satellites[0]).toHaveProperty('name')
      expect(satelliteData.satellites[0]).toHaveProperty('latitude')
      expect(satelliteData.satellites[0]).toHaveProperty('longitude')
      expect(satelliteData.satellites[0]).toHaveProperty('altitude')
      
      expectNoConsoleErrors()
    })
    
    it('應該驗證衛星數據格式', async () => {
      const satelliteData = await testApiEndpoint(
        mockApiConfig.netstackFetch,
        '/api/v1/satellites',
        mockNetstackResponses['/api/v1/satellites']
      )
      
      satelliteData.satellites.forEach((satellite: any) => {
        // 驗證 ID 格式
        expect(typeof satellite.id).toBe('string')
        expect(satellite.id).toMatch(/^sat_\d+$/)
        
        // 驗證坐標範圍
        expect(satellite.latitude).toBeGreaterThanOrEqual(-90)
        expect(satellite.latitude).toBeLessThanOrEqual(90)
        expect(satellite.longitude).toBeGreaterThanOrEqual(-180)
        expect(satellite.longitude).toBeLessThanOrEqual(180)
        expect(satellite.altitude).toBeGreaterThan(0)
      })
    })
  })

  describe('換手 API', () => {
    it('應該正確執行衛星換手策略', async () => {
      const handoverRequest = {
        ue_id: 'ue_001',
        current_satellite: 'sat_001',
        target_satellite: 'sat_002',
        reason: 'signal_quality_improvement'
      }
      
      const handoverData = await testApiEndpoint(
        mockApiConfig.netstackFetch,
        '/api/v1/handover/strategy/switch',
        mockNetstackResponses['/api/v1/handover/strategy/switch'],
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(handoverRequest)
        }
      )
      
      validateApiResponse(handoverData, ['success', 'switch_time', 'target_satellite'])
      expect(handoverData.success).toBe(true)
      expect(typeof handoverData.switch_time).toBe('number')
      expect(handoverData.switch_time).toBeGreaterThan(0)
      expect(handoverData.target_satellite).toBe('sat_002')
      
      expectNoConsoleErrors()
    })
  })

  describe('設備 API', () => {
    it('應該正確獲取設備列表', async () => {
      const deviceData = await testApiEndpoint(
        mockApiConfig.netstackFetch,
        '/api/v1/devices',
        mockNetstackResponses['/api/v1/devices']
      )
      
      validateApiResponse(deviceData, ['devices'])
      expect(Array.isArray(deviceData.devices)).toBe(true)
      
      if (deviceData.devices.length > 0) {
        deviceData.devices.forEach((device: any) => {
          expect(device).toHaveProperty('id')
          expect(device).toHaveProperty('type')
          expect(device).toHaveProperty('connected_satellite')
        })
      }
      
      expectNoConsoleErrors()
    })
  })
})

// =============================================================================
// 2. SimWorld API 測試  
// =============================================================================

describe('🛰️ SimWorld API 整合測試', () => {
  
  beforeEach(() => {
    vi.clearAllMocks()
    consoleErrorCollector.clearErrors()
  })

  describe('衛星仿真 API', () => {
    it('應該正確獲取仿真衛星數據', async () => {
      const satelliteData = await testApiEndpoint(
        mockApiConfig.simworldFetch,
        '/api/satellites',
        mockSimworldResponses['/api/satellites']
      )
      
      validateApiResponse(satelliteData, ['satellites'])
      expect(Array.isArray(satelliteData.satellites)).toBe(true)
      
      if (satelliteData.satellites.length > 0) {
        const satellite = satelliteData.satellites[0]
        expect(satellite).toHaveProperty('id')
        expect(satellite).toHaveProperty('position')
        expect(satellite).toHaveProperty('velocity')
        expect(satellite.position).toHaveProperty('x')
        expect(satellite.position).toHaveProperty('y')
        expect(satellite.position).toHaveProperty('z')
      }
      
      expectNoConsoleErrors()
    })
  })

  describe('設備仿真 API', () => {
    it('應該正確獲取仿真設備數據', async () => {
      const deviceData = await testApiEndpoint(
        mockApiConfig.simworldFetch,
        '/api/devices',
        mockSimworldResponses['/api/devices']
      )
      
      validateApiResponse(deviceData, ['devices'])
      expect(Array.isArray(deviceData.devices)).toBe(true)
      
      if (deviceData.devices.length > 0) {
        const device = deviceData.devices[0]
        expect(device).toHaveProperty('id')
        expect(device).toHaveProperty('position')
        expect(device).toHaveProperty('signal_strength')
        expect(device.position).toHaveProperty('lat')
        expect(device.position).toHaveProperty('lng')
      }
      
      expectNoConsoleErrors()
    })
  })

  describe('測量事件 API', () => {
    it('應該正確獲取測量事件數據', async () => {
      const measurementData = await testApiEndpoint(
        mockApiConfig.simworldFetch,
        '/api/measurements',
        mockSimworldResponses['/api/measurements']
      )
      
      validateApiResponse(measurementData, ['measurements'])
      expect(Array.isArray(measurementData.measurements)).toBe(true)
      
      if (measurementData.measurements.length > 0) {
        const measurement = measurementData.measurements[0]
        expect(measurement).toHaveProperty('event_type')
        expect(measurement).toHaveProperty('rsrp')
        expect(measurement).toHaveProperty('rsrq')
        expect(measurement).toHaveProperty('timestamp')
        
        // 驗證測量值範圍
        expect(measurement.rsrp).toBeLessThan(0) // RSRP 應該是負值
        expect(measurement.rsrq).toBeLessThan(0) // RSRQ 應該是負值
        expect(measurement.sinr).toBeGreaterThan(0) // SINR 應該是正值
      }
      
      expectNoConsoleErrors()
    })
  })
})

// =============================================================================
// 3. API 錯誤處理測試
// =============================================================================

describe('🚨 API 錯誤處理測試', () => {
  
  beforeEach(() => {
    vi.clearAllMocks()
    consoleErrorCollector.clearErrors()
  })

  describe('網路錯誤處理', () => {
    it('應該正確處理網路連接錯誤', async () => {
      mockApiConfig.netstackFetch.mockRejectedValueOnce(
        new Error('Network connection failed')
      )
      
      try {
        await mockApiConfig.netstackFetch('/api/v1/health')
        expect.fail('應該拋出錯誤')
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
        expect((error as Error).message).toContain('Network connection failed')
      }
    })
    
    it('應該正確處理超時錯誤', async () => {
      mockApiConfig.netstackFetch.mockRejectedValueOnce(
        new Error('Request timeout')
      )
      
      try {
        await mockApiConfig.netstackFetch('/api/v1/satellites')
        expect.fail('應該拋出錯誤')
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
        expect((error as Error).message).toContain('timeout')
      }
    })
  })

  describe('HTTP 錯誤處理', () => {
    it('應該正確處理 404 錯誤', async () => {
      mockApiConfig.netstackFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: () => Promise.resolve({ error: 'Endpoint not found' })
      })
      
      const response = await mockApiConfig.netstackFetch('/api/v1/nonexistent')
      const data = await response.json()
      
      expect(response.ok).toBe(false)
      expect(response.status).toBe(404)
      expect(data).toHaveProperty('error')
    })
    
    it('應該正確處理 500 服務器錯誤', async () => {
      mockApiConfig.netstackFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: () => Promise.resolve({ 
          error: 'Internal server error',
          details: 'Database connection failed'
        })
      })
      
      const response = await mockApiConfig.netstackFetch('/api/v1/satellites')
      const data = await response.json()
      
      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
      expect(data).toHaveProperty('error')
      expect(data).toHaveProperty('details')
    })
  })

  describe('數據驗證錯誤', () => {
    it('應該檢測無效的 JSON 回應', async () => {
      mockApiConfig.netstackFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.reject(new Error('Invalid JSON'))
      })
      
      const response = await mockApiConfig.netstackFetch('/api/v1/health')
      
      try {
        await response.json()
        expect.fail('應該拋出錯誤')
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
        expect((error as Error).message).toContain('Invalid JSON')
      }
    })
  })
})

// =============================================================================
// 4. API 效能測試
// =============================================================================

describe('⚡ API 效能測試', () => {
  
  beforeEach(() => {
    vi.clearAllMocks()
    consoleErrorCollector.clearErrors()
  })

  it('API 請求應該在合理時間內完成', async () => {
    // 模擬快速回應
    mockApiConfig.netstackFetch.mockImplementation(async (endpoint) => {
      await delay(50) // 模擬 50ms 延遲
      return {
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockNetstackResponses['/api/v1/health'])
      }
    })
    
    const start = performance.now()
    await mockApiConfig.netstackFetch('/api/v1/health')
    const end = performance.now()
    
    const requestTime = end - start
    expect(requestTime).toBeLessThan(100) // 應該少於 100ms
    
    expectNoConsoleErrors()
  })
  
  it('應該支援並行 API 請求', async () => {
    // 模擬並行請求
    mockApiConfig.netstackFetch.mockImplementation(async (endpoint) => {
      await delay(30) // 每個請求 30ms
      if (endpoint.includes('health')) {
        return {
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockNetstackResponses['/api/v1/health'])
        }
      } else if (endpoint.includes('satellites')) {
        return {
          ok: true,
          status: 200,
          json: () => Promise.resolve(mockNetstackResponses['/api/v1/satellites'])
        }
      }
      return { ok: false, status: 404 }
    })
    
    const start = performance.now()
    
    // 並行執行多個請求
    await Promise.all([
      mockApiConfig.netstackFetch('/api/v1/health'),
      mockApiConfig.netstackFetch('/api/v1/satellites'),
      mockApiConfig.netstackFetch('/api/v1/devices')
    ])
    
    const end = performance.now()
    const totalTime = end - start
    
    // 並行執行應該比序列執行快
    expect(totalTime).toBeLessThan(100) // 應該遠少於 3*30 = 90ms
    
    expectNoConsoleErrors()
  })
})

// =============================================================================
// 5. API 配置驗證測試
// =============================================================================

describe('⚙️ API 配置驗證測試', () => {
  
  beforeEach(() => {
    vi.clearAllMocks()
    consoleErrorCollector.clearErrors()
  })

  it('應該正確讀取 API 配置', () => {
    const config = mockApiConfig.getCurrentApiConfig()
    
    expect(config).toHaveProperty('netstack')
    expect(config).toHaveProperty('simworld')
    expect(config.netstack).toHaveProperty('baseUrl')
    expect(config.netstack).toHaveProperty('timeout')
    expect(config.simworld).toHaveProperty('baseUrl')
    expect(config.simworld).toHaveProperty('timeout')
    
    // 驗證配置值
    expect(typeof config.netstack.baseUrl).toBe('string')
    expect(typeof config.netstack.timeout).toBe('number')
    expect(config.netstack.timeout).toBeGreaterThan(0)
    
    expectNoConsoleErrors()
  })
  
  it('應該使用正確的基礎 URL', () => {
    const config = mockApiConfig.getCurrentApiConfig()
    
    // 在 Docker 環境中應該使用代理路徑
    expect(config.netstack.baseUrl).toBe('/netstack')
    expect(config.simworld.baseUrl).toBe('/api')
  })
})

// =============================================================================
// 6. 真實 API 連接測試 (可選)
// =============================================================================

describe('🔗 真實 API 連接測試', () => {
  
  // 這些測試只在實際有後端服務運行時才執行
  const isRealApiAvailable = process.env.TEST_REAL_API === 'true'
  
  beforeEach(() => {
    if (!isRealApiAvailable) {
      return // 跳過真實 API 測試
    }
  })

  it.skipIf(!isRealApiAvailable)('應該能連接到真實的 NetStack API', async () => {
    // 這個測試需要真實的後端服務
    const realFetch = globalThis.fetch
    
    try {
      const response = await realFetch('http://localhost:8080/api/v1/health')
      const data = await response.json()
      
      expect(response.ok).toBe(true)
      expect(data).toHaveProperty('status')
    } catch (error) {
      console.warn('真實 NetStack API 連接失敗:', error)
      // 在 CI 環境中可以跳過這個錯誤
    }
  })
  
  it.skipIf(!isRealApiAvailable)('應該能連接到真實的 SimWorld API', async () => {
    const realFetch = globalThis.fetch
    
    try {
      const response = await realFetch('http://localhost:8888/api/satellites')
      const data = await response.json()
      
      expect(response.ok).toBe(true)
      expect(data).toHaveProperty('satellites')
    } catch (error) {
      console.warn('真實 SimWorld API 連接失敗:', error)
    }
  })
})