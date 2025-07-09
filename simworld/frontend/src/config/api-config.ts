/**
 * 統一 API 配置管理
 * 解決 Docker 網路配置問題的核心解決方案
 */

interface ApiConfig {
  netstack: {
    baseUrl: string
    timeout: number
  }
  simworld: {
    baseUrl: string
    timeout: number
  }
  mode: 'development' | 'docker' | 'production'
}

/**
 * 檢測當前運行環境
 */
const detectEnvironment = (): 'development' | 'docker' | 'production' => {
  // 檢查是否在 Docker 容器中
  if (import.meta.env.VITE_ENV_MODE === 'docker') {
    return 'docker'
  }
  
  // 檢查是否為開發環境
  if (import.meta.env.DEV) {
    return 'development'
  }
  
  // 檢查主機名判斷環境
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'development'
    }
  }
  
  return 'production'
}

// 防止重複日誌的標誌
let configLogged = false

/**
 * 獲取環境特定的 API 配置
 */
export const getApiConfig = (): ApiConfig => {
  const environment = detectEnvironment()
  
  const configs = {
    development: {
      netstack: {
        baseUrl: import.meta.env.VITE_NETSTACK_URL || 'http://localhost:8080',
        timeout: 10000
      },
      simworld: {
        baseUrl: import.meta.env.VITE_SIMWORLD_URL || 'http://localhost:8000',
        timeout: 10000
      },
      mode: 'development' as const
    },
    
    docker: {
      netstack: {
        baseUrl: '/netstack', // 使用 Vite 代理
        timeout: 15000
      },
      simworld: {
        baseUrl: '/api', // 使用 Vite 代理
        timeout: 15000
      },
      mode: 'docker' as const
    },
    
    production: {
      netstack: {
        baseUrl: import.meta.env.VITE_NETSTACK_URL || '/netstack',
        timeout: 20000
      },
      simworld: {
        baseUrl: import.meta.env.VITE_SIMWORLD_URL || '/api',
        timeout: 20000
      },
      mode: 'production' as const
    }
  }
  
  const config = configs[environment]
  
  // 開發環境下輸出配置信息（只記錄一次）
  if (import.meta.env.DEV && !configLogged) {
    // console.log(`🔧 API 配置模式: ${environment}`, config)
    configLogged = true
  }
  
  return config
}

/**
 * 驗證 API 配置
 */
export const validateApiConfig = (): string[] => {
  const warnings: string[] = []
  const config = getApiConfig()
  
  // 檢查 NetStack 配置
  if (!config.netstack.baseUrl) {
    warnings.push('NetStack BaseURL 未配置')
  }
  
  // 檢查 SimWorld 配置
  if (!config.simworld.baseUrl) {
    warnings.push('SimWorld BaseURL 未配置')
  }
  
  // Docker 環境特定檢查
  if (config.mode === 'docker') {
    if (!config.netstack.baseUrl.startsWith('/')) {
      warnings.push('Docker 環境下 NetStack 應使用代理路徑')
    }
  }
  
  return warnings
}

/**
 * 獲取特定服務的完整 URL
 */
export const getServiceUrl = (service: 'netstack' | 'simworld', endpoint: string = ''): string => {
  const config = getApiConfig()
  const baseUrl = config[service].baseUrl
  
  // 確保端點以 / 開頭
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  
  // 如果是代理路徑，直接拼接
  if (baseUrl.startsWith('/')) {
    return `${baseUrl}${normalizedEndpoint}`
  }
  
  // 如果是完整 URL，使用 URL 構造器
  try {
    return new URL(normalizedEndpoint, baseUrl).toString()
  } catch (error) {
    console.error('無效的 URL 配置:', { baseUrl, endpoint, error })
    return `${baseUrl}${normalizedEndpoint}`
  }
}

/**
 * 創建帶有統一配置的 fetch 函數
 */
export const createConfiguredFetch = (service: 'netstack' | 'simworld') => {
  const config = getApiConfig()
  const serviceConfig = config[service]
  
  return async (endpoint: string, options: RequestInit = {}) => {
    const url = getServiceUrl(service, endpoint)
    
    const defaultOptions: RequestInit = {
      timeout: serviceConfig.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    }
    
    const mergedOptions = { ...defaultOptions, ...options }
    
    try {
      const response = await fetch(url, mergedOptions)
      
      if (!response.ok) {
        console.error(`${service.toUpperCase()} API 錯誤:`, {
          url,
          status: response.status,
          statusText: response.statusText
        })
      }
      
      return response
    } catch (error) {
      console.error(`${service.toUpperCase()} API 請求失敗:`, {
        url,
        error: error instanceof Error ? error.message : error
      })
      throw error
    }
  }
}

// 預設的服務特定 fetch 函數
export const netstackFetch = createConfiguredFetch('netstack')
export const simworldFetch = createConfiguredFetch('simworld')

// 導出當前配置供調試使用
export const currentApiConfig = getApiConfig()