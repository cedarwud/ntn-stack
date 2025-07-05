/**
 * 統一配置驗證系統
 * 用於在應用啟動時驗證所有配置項的正確性
 */

import { getApiConfig, validateApiConfig } from './api-config'

export interface ConfigValidationResult {
  isValid: boolean
  warnings: string[]
  errors: string[]
  recommendations: string[]
}

/**
 * 全面驗證應用配置
 */
export const validateFullConfiguration = (): ConfigValidationResult => {
  const result: ConfigValidationResult = {
    isValid: true,
    warnings: [],
    errors: [],
    recommendations: []
  }

  // 1. 驗證 API 配置
  const apiWarnings = validateApiConfig()
  result.warnings.push(...apiWarnings)

  // 2. 驗證環境變數
  const envValidation = validateEnvironmentVariables()
  result.warnings.push(...envValidation.warnings)
  result.errors.push(...envValidation.errors)

  // 3. 驗證 Docker 配置
  const dockerValidation = validateDockerConfiguration()
  result.warnings.push(...dockerValidation.warnings)
  result.errors.push(...dockerValidation.errors)

  // 4. 驗證網路配置
  const networkValidation = validateNetworkConfiguration()
  result.warnings.push(...networkValidation.warnings)
  result.errors.push(...networkValidation.errors)

  // 5. 生成建議
  result.recommendations = generateRecommendations(result)

  // 如果有錯誤，標記為無效
  result.isValid = result.errors.length === 0

  return result
}

/**
 * 驗證環境變數配置
 */
const validateEnvironmentVariables = (): { warnings: string[]; errors: string[] } => {
  const warnings: string[] = []
  const errors: string[] = []

  // 檢查關鍵環境變數
  const requiredEnvVars = [
    'VITE_ENV_MODE',
    'VITE_NETSTACK_URL',
    'VITE_SIMWORLD_URL'
  ]

  requiredEnvVars.forEach(envVar => {
    const value = import.meta.env[envVar]
    if (!value) {
      errors.push(`缺少必要環境變數: ${envVar}`)
    }
  })

  // 檢查 Docker 特定配置
  if (import.meta.env.VITE_ENV_MODE === 'docker') {
    const dockerEnvVars = [
      'VITE_NETSTACK_PROXY_TARGET',
      'VITE_SIMWORLD_PROXY_TARGET'
    ]

    dockerEnvVars.forEach(envVar => {
      const value = import.meta.env[envVar]
      if (!value) {
        warnings.push(`Docker 模式下建議設置: ${envVar}`)
      }
    })
  }

  return { warnings, errors }
}

/**
 * 驗證 Docker 配置
 */
const validateDockerConfiguration = (): { warnings: string[]; errors: string[] } => {
  const warnings: string[] = []
  const errors: string[] = []
  const config = getApiConfig()

  if (config.mode === 'docker') {
    // 檢查是否使用代理路徑
    if (!config.netstack.baseUrl.startsWith('/')) {
      errors.push('Docker 模式下 NetStack 必須使用代理路徑 (以 / 開頭)')
    }

    if (!config.simworld.baseUrl.startsWith('/')) {
      errors.push('Docker 模式下 SimWorld 必須使用代理路徑 (以 / 開頭)')
    }

    // 檢查超時配置
    if (config.netstack.timeout < 15000) {
      warnings.push('Docker 模式下建議增加 NetStack 超時時間至 15 秒以上')
    }
  }

  return { warnings, errors }
}

/**
 * 驗證網路配置
 */
const validateNetworkConfiguration = (): { warnings: string[]; errors: string[] } => {
  const warnings: string[] = []
  const errors: string[] = []

  // 檢查硬編碼 IP 地址
  // const hardcodedIpPattern = /\b(?:\d{1,3}\.){3}\d{1,3}\b/
  
  // 這裡可以擴展來檢查配置文件中的硬編碼 IP
  // 目前先檢查常見的硬編碼模式
  const commonHardcodedIps = ['172.20.0.40', '120.126.151.101']
  
  commonHardcodedIps.forEach(ip => {
    // 檢查環境變數中是否包含硬編碼 IP
    Object.keys(import.meta.env).forEach(key => {
      const value = import.meta.env[key]
      if (typeof value === 'string' && value.includes(ip)) {
        warnings.push(`環境變數 ${key} 包含硬編碼 IP: ${ip}`)
      }
    })
  })

  return { warnings, errors }
}

/**
 * 生成配置建議
 */
const generateRecommendations = (result: ConfigValidationResult): string[] => {
  const recommendations: string[] = []

  if (result.errors.length > 0) {
    recommendations.push('🚨 立即修復所有配置錯誤以確保系統正常運行')
  }

  if (result.warnings.length > 0) {
    recommendations.push('⚠️ 檢查並解決配置警告以提升系統穩定性')
  }

  // 基於配置模式的建議
  const config = getApiConfig()
  if (config.mode === 'development') {
    recommendations.push('🔧 開發模式下確保 NetStack 和 SimWorld 服務正在運行')
  } else if (config.mode === 'docker') {
    recommendations.push('🐳 Docker 模式下確保所有容器都在同一網路中')
  }

  return recommendations
}

/**
 * 在控制台輸出配置驗證結果
 */
export const logConfigurationStatus = (result: ConfigValidationResult): void => {
  console.group('🔧 配置驗證結果')
  
  if (result.isValid) {
    console.log('✅ 配置驗證通過')
  } else {
    console.error('❌ 配置驗證失敗')
  }

  if (result.errors.length > 0) {
    console.group('🚨 配置錯誤')
    result.errors.forEach(error => console.error(`❌ ${error}`))
    console.groupEnd()
  }

  if (result.warnings.length > 0) {
    console.group('⚠️ 配置警告')
    result.warnings.forEach(warning => console.warn(`⚠️ ${warning}`))
    console.groupEnd()
  }

  if (result.recommendations.length > 0) {
    console.group('💡 配置建議')
    result.recommendations.forEach(rec => console.info(`💡 ${rec}`))
    console.groupEnd()
  }

  // 輸出當前配置信息
  const config = getApiConfig()
  console.group('📋 當前配置')
  console.log('環境模式:', config.mode)
  console.log('NetStack URL:', config.netstack.baseUrl)
  console.log('SimWorld URL:', config.simworld.baseUrl)
  console.groupEnd()

  console.groupEnd()
}

/**
 * 檢查端點可訪問性（異步）
 */
export const validateEndpointAccessibility = async (): Promise<{
  netstack: boolean
  simworld: boolean
  errors: string[]
}> => {
  const result = {
    netstack: false,
    simworld: false,
    errors: [] as string[]
  }

  try {
    // 測試 NetStack 連接
    const { netstackFetch } = await import('./api-config')
    const netstackResponse = await netstackFetch('/health', { 
      method: 'GET',
      signal: AbortSignal.timeout(5000) // 5 秒超時
    })
    result.netstack = netstackResponse.ok
    if (!netstackResponse.ok) {
      result.errors.push(`NetStack 健康檢查失敗: ${netstackResponse.status}`)
    }
  } catch (error) {
    result.errors.push(`NetStack 連接失敗: ${error instanceof Error ? error.message : error}`)
  }

  try {
    // 測試 SimWorld 連接
    const { simworldFetch } = await import('./api-config')
    const simworldResponse = await simworldFetch('/health', {
      method: 'GET',
      signal: AbortSignal.timeout(5000) // 5 秒超時
    })
    result.simworld = simworldResponse.ok
    if (!simworldResponse.ok) {
      result.errors.push(`SimWorld 健康檢查失敗: ${simworldResponse.status}`)
    }
  } catch (error) {
    result.errors.push(`SimWorld 連接失敗: ${error instanceof Error ? error.message : error}`)
  }

  return result
}