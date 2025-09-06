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
  
  // 如果有設置代理路徑環境變量，強制使用 docker 模式
  if (import.meta.env.VITE_NETSTACK_URL?.startsWith('/')) {
    return 'docker'
  }
  
  // 檢查主機名 - 如果是通過 5173 端口訪問
  if (typeof window !== 'undefined') {
    const _hostname = window.location.hostname
    const port = window.location.port
    
    // 如果訪問端口是 5173，都使用 docker 模式（使用代理）
    // 因為不管是 localhost 還是外部 IP，都需要通過前端服务器代理到後端
    if (port === '5173') {
      return 'docker'
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
  
  // 環境檢測日誌（生產環境可註釋）
  // if (typeof window !== 'undefined') {
  //   console.log('🔍 [API Config] 環境檢測:', {
  //     hostname: window.location.hostname,
  //     port: window.location.port,
  //     detected: environment
  //   })
  // }
  
  const configs = {
    development: {
      netstack: {
        // 從外部 IP 訪問時，使用主機的 IP 地址
        baseUrl: typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
          ? `http://${window.location.hostname}:8080`
          : (import.meta.env.VITE_NETSTACK_URL || 'http://localhost:8080'),
        timeout: 10000
      },
      simworld: {
        // 從外部 IP 訪問時，使用主機的 IP 地址
        baseUrl: typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1'
          ? `http://${window.location.hostname}:8888`
          : (import.meta.env.VITE_SIMWORLD_URL || 'http://localhost:8000'),
        timeout: 10000
      },
      mode: 'development' as const
    },
    
    docker: {
      netstack: {
        baseUrl: '/netstack', // 使用 Vite 代理
        timeout: 120000 // 增加到 120 秒以匹配管道統計API響應時間
      },
      simworld: {
        baseUrl: '/api', // 使用 Vite 代理路徑，與 vite.config.ts 中的 '/api' 代理匹配
        timeout: 60000 // 增加到 60 秒
      },
      mode: 'docker' as const
    },
    
    production: {
      netstack: {
        baseUrl: import.meta.env.VITE_NETSTACK_URL || '/netstack',
        timeout: 120000 // 增加到 120 秒以匹配管道統計API響應時間
      },
      simworld: {
        baseUrl: import.meta.env.VITE_SIMWORLD_URL || '/api',
        timeout: 60000 // 增加到 60 秒
      },
      mode: 'production' as const
    }
  }
  
  const config = configs[environment]
  
  // 開發環境下輸出配置信息（只記錄一次） - 已禁用減少日誌噪音
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
  
  // Docker 環境特定檢查
  if (config.mode === 'docker') {
    if (!config.netstack.baseUrl.startsWith('/')) {
      warnings.push('Docker 環境下 NetStack 應使用代理路徑')
    }
    // SimWorld 在 Docker 環境下可以使用空字串或根路徑，不需要強制要求代理路徑前綴
  } else {
    // 非 Docker 環境下才檢查 SimWorld BaseURL
    if (!config.simworld.baseUrl) {
      warnings.push('SimWorld BaseURL 未配置')
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
  
  // URL 構建日誌（生產環境可註釋）
  // console.log(`🔍 [API Config] ${service} URL:`, {
  //   mode: config.mode,
  //   baseUrl: baseUrl,
  //   endpoint: endpoint
  // })
  
  // 確保端點以 / 開頭
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  
  // 處理空 baseUrl 的情況
  if (!baseUrl || baseUrl === '') {
    return normalizedEndpoint
  }
  
  // 如果是代理路徑，直接拼接
  if (baseUrl.startsWith('/')) {
    // 處理根路徑的特殊情況，避免雙斜線
    if (baseUrl === '/') {
      return normalizedEndpoint
    }
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
      } else if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        // 網路連接失敗的特殊處理
        console.error(`${service.toUpperCase()} 網路連接失敗:`, {
          url,
          endpoint,
          error: error.message,
          suggestion: '檢查網路連接和服務狀態'
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

/**
 * 創建帶有重試機制的 fetch 函數
 */
export const createRetryFetch = (service: 'netstack' | 'simworld', maxRetries = 3) => {
  const baseFetch = createConfiguredFetch(service)
  
  return async (endpoint: string, options: RequestInit = {}) => {
    let lastError: Error | null = null
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await baseFetch(endpoint, options)
        return response
      } catch (error) {
        lastError = error as Error
        
        // 如果是最後一次嘗試，直接拋出錯誤
        if (attempt === maxRetries) {
          console.error(`${service.toUpperCase()} API 重試 ${maxRetries} 次後仍然失敗:`, {
            endpoint,
            finalError: lastError.message
          })
          throw lastError
        }
        
        // 計算重試延遲 (exponential backoff)
        const delay = Math.min(1000 * Math.pow(2, attempt - 1), 5000)
        console.warn(`${service.toUpperCase()} API 請求失敗，${delay}ms 後重試 (${attempt}/${maxRetries}):`, {
          endpoint,
          error: lastError.message
        })
        
        // 等待後重試
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    // 不會到這裡，但 TypeScript 需要
    throw lastError
  }
}

// 預設的服務特定 fetch 函數
export const netstackFetch = createConfiguredFetch('netstack')
export const simworldFetch = createConfiguredFetch('simworld')

// 帶重試機制的 fetch 函數
export const netstackFetchWithRetry = createRetryFetch('netstack', 3)
export const simworldFetchWithRetry = createRetryFetch('simworld', 3)

// 導出當前配置供調試使用
export const currentApiConfig = getApiConfig()