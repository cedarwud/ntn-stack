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
  // 強制檢查是否在 Docker 容器中
  if (import.meta.env.VITE_ENV_MODE === 'docker') {
    return 'docker'
  }
  
  // 檢查主機名 - 如果是通過 5173 端口訪問，則使用 docker
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    const port = window.location.port
    if (port === '5173') {
      // 如果有設置 VITE_NETSTACK_URL 為代理路徑，則為 docker 環境
      if (import.meta.env.VITE_NETSTACK_URL?.startsWith('/')) {
        return 'docker'
      }
      // 如果通過 IP 地址訪問且端口為 5173，很可能是 Docker 環境
      if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
        return 'docker'
      }
    }
  }
  
  // 檢查是否為開發環境
  if (import.meta.env.DEV && !import.meta.env.VITE_ENV_MODE) {
    return 'development'
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
        timeout: 30000
      },
      simworld: {
        baseUrl: '', // 直接使用相對路徑，不需要 /api 前綴
        timeout: 30000
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
    console.log(`🔧 API 配置模式: ${environment}`, config)
    console.log(`🔧 環境檢測信息:`, {
      'VITE_ENV_MODE': import.meta.env.VITE_ENV_MODE,
      'VITE_NETSTACK_URL': import.meta.env.VITE_NETSTACK_URL,
      'VITE_SIMWORLD_URL': import.meta.env.VITE_SIMWORLD_URL,
      'hostname': typeof window !== 'undefined' ? window.location.hostname : 'N/A',
      'port': typeof window !== 'undefined' ? window.location.port : 'N/A',
      'DEV': import.meta.env.DEV
    })
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
    
    // 創建超時控制器
    const timeoutController = new AbortController()
    const timeoutId = setTimeout(() => {
      console.warn(`${service.toUpperCase()} API 請求超時 (${serviceConfig.timeout}ms):`, endpoint)
      timeoutController.abort()
    }, serviceConfig.timeout)
    
    // 合併 AbortController signals
    const existingSignal = options.signal
    let finalSignal = timeoutController.signal
    
    if (existingSignal) {
      // 如果已存在信號，創建組合信號
      const combinedController = new AbortController()
      const abortBoth = () => {
        console.log(`${service.toUpperCase()} API 請求被取消:`, endpoint)
        combinedController.abort()
      }
      
      existingSignal.addEventListener('abort', abortBoth)
      timeoutController.signal.addEventListener('abort', abortBoth)
      
      finalSignal = combinedController.signal
    }
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      signal: finalSignal
    }
    
    const mergedOptions = { ...defaultOptions, ...options }
    
    try {
      const response = await fetch(url, mergedOptions)
      clearTimeout(timeoutId)
      
      if (!response.ok) {
        console.error(`${service.toUpperCase()} API 錯誤:`, {
          url,
          status: response.status,
          statusText: response.statusText
        })
      }
      
      return response
    } catch (error) {
      clearTimeout(timeoutId)
      
      // 針對 AbortError 提供更詳細的日誌
      if (error instanceof Error && error.name === 'AbortError') {
        console.warn(`${service.toUpperCase()} API 請求被中斷:`, {
          url,
          endpoint,
          reason: error.message,
          timeout: serviceConfig.timeout
        })
      } else {
        console.error(`${service.toUpperCase()} API 請求失敗:`, {
          url,
          error: error instanceof Error ? error.message : error
        })
      }
      throw error
    }
  }
}

// 預設的服務特定 fetch 函數
export const netstackFetch = createConfiguredFetch('netstack')
export const simworldFetch = createConfiguredFetch('simworld')


// 導出當前配置供調試使用
export const currentApiConfig = getApiConfig()