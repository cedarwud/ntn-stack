/**
 * 統一的 NetStack API 客戶端
 * 整合所有 NetStack API 功能，包含重試邏輯和預計算數據支援
 */
import { netstackFetch } from '../config/api-config'
import type { UAVData, SystemStatus } from '../types/charts'

// 重試配置
const RETRY_CONFIG = {
  maxRetries: 1,
  retryDelay: 3000,
  enableMockData: true,
}

// ================== 基礎介面定義 ==================

// 衛星存取預測相關
export interface SatelliteAccessPredictionRequest {
  ue_id: string
  satellite_id: string
  time_horizon_minutes?: number
}

export interface CoreSyncStatus {
  service_info: {
    is_running: boolean
    core_sync_state: string
    uptime_hours: number
    active_tasks: number
  }
  sync_performance: {
    overall_accuracy_ms: number
    max_achieved_accuracy_ms: number | null
    signaling_free_enabled: boolean
    binary_search_enabled: boolean
  }
  component_states: {
    [key: string]: {
      sync_state: string
      accuracy_ms: number
      last_sync: string
      availability: number
    }
  }
  statistics: {
    total_sync_operations: number
    successful_syncs: number
    failed_syncs: number
    average_sync_time_ms: number
    max_achieved_accuracy_ms: number | null
    uptime_percentage: number
    last_emergency_time: string | null
    signaling_free_operations: number
    binary_search_optimizations: number
  }
  configuration: {
    max_sync_error_ms: number
    sync_check_interval_s: number
    emergency_threshold_ms: number
    auto_resync_enabled: boolean
  }
}

// 換手分析相關
export interface HandoverAnalysisRequest {
  ue_id: string
  current_time: string
  future_time: string
  delta_t_seconds: number
}

export interface HandoverAnalysisResponse {
  handover_required: boolean
  timestamp: string
  latency_ms: number
  success_rate: number
  handover_type: string
  source_satellite: string
  target_satellite: string
  additional_metrics: Record<string, unknown>
  interruption_time_ms: number
  qos_impact_score: number
}

// 存取預測相關
export interface AccessPredictionRequest {
  ue_lat: number
  ue_lon: number
  current_satellite: string
  predicted_handovers: Array<Record<string, unknown>>
  handover_time: string
  confidence_score: number
}

export interface AccessPredictionResponse {
  signal_quality_prediction: {
    predicted_snr: number
    signal_threshold: number
  }
}

// 預計算數據相關
export interface PrecomputedOrbitRequest {
  constellation: 'starlink' | 'oneweb'
  start_time: string
  duration_minutes: number
  observer_location: {
    lat: number
    lon: number
    elevation_m?: number
  }
  elevation_threshold_deg?: number
}

export interface PrecomputedOrbitResponse {
  satellites: Array<{
    norad_id: string
    name: string
    positions: Array<{
      timestamp: string
      latitude: number
      longitude: number
      altitude: number
      elevation: number
      azimuth: number
      distance: number
      is_visible: boolean
    }>
  }>
  metadata: {
    generated_at: string
    observer_location: Record<string, unknown>
    duration_minutes: number
    time_step_seconds: number
  }
}

// ================== 重試邏輯 ==================

const isRetryableError = (error: unknown): boolean => {
  if (!error || typeof error !== 'object') {
    return true
  }
  
  const errorWithResponse = error as { response?: { status: number } }
  if (!errorWithResponse.response) {
    return true // 網路錯誤
  }
  
  const status = errorWithResponse.response.status
  return status >= 500 || status === 429 || status === 408
}

const retryRequest = async <T>(
  requestFn: () => Promise<T>,
  retries: number = RETRY_CONFIG.maxRetries
): Promise<T> => {
  try {
    return await requestFn()
  } catch (error) {
    if (retries > 0 && isRetryableError(error)) {
      console.log(`請求失敗，將在 ${RETRY_CONFIG.retryDelay}ms 後重試，剩餘重試次數: ${retries}`)
      await new Promise(resolve => setTimeout(resolve, RETRY_CONFIG.retryDelay))
      return retryRequest(requestFn, retries - 1)
    }
    throw error
  }
}

// ================== 統一 API 客戶端 ==================

export class UnifiedNetStackApi {
  
  // ========== 系統狀態 API ==========
  
  async getSystemStatus(): Promise<SystemStatus> {
    return retryRequest(() =>
      netstackFetch('/api/system/status').then(r => r.json())
    )
  }
  
  async getHealthStatus(): Promise<Record<string, unknown>> {
    return retryRequest(() =>
      netstackFetch('/health').then(r => r.json())
    )
  }
  
  async getCoreSync(): Promise<CoreSyncStatus> {
    return retryRequest(() =>
      netstackFetch('/api/v1/core-sync/status').then(r => r.json())
    )
  }
  
  // ========== UAV 數據 API ==========
  
  async getUAVData(): Promise<UAVData[]> {
    return retryRequest(() =>
      netstackFetch('/api/uav/data').then(r => r.json())
    )
  }
  
  // ========== 衛星存取預測 API ==========
  
  async getSatelliteAccessPrediction(request: SatelliteAccessPredictionRequest): Promise<Record<string, unknown>> {
    return retryRequest(() =>
      netstackFetch('/api/v1/satellite/access/prediction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }).then(r => r.json())
    )
  }
  
  // ========== 換手分析 API ==========
  
  async getHandoverAnalysis(request: HandoverAnalysisRequest): Promise<HandoverAnalysisResponse> {
    return retryRequest(() =>
      netstackFetch('/api/v1/handover/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }).then(r => r.json())
    )
  }
  
  async getAccessPrediction(request: AccessPredictionRequest): Promise<AccessPredictionResponse> {
    return retryRequest(() =>
      netstackFetch('/api/v1/access/prediction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }).then(r => r.json())
    )
  }
  
  // ========== 預計算數據 API ==========
  
  async getPrecomputedOrbitData(request: PrecomputedOrbitRequest): Promise<PrecomputedOrbitResponse> {
    return retryRequest(() =>
      netstackFetch('/api/v1/precomputed/orbit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }).then(r => r.json())
    )
  }
  
  async getVisibleSatellites(params: {
    count?: number
    min_elevation_deg?: number
    observer_lat?: number
    observer_lon?: number
    utc_timestamp?: string
    global_view?: boolean
  }): Promise<Record<string, unknown>> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, value.toString())
      }
    })
    
    return retryRequest(() =>
      netstackFetch(`/api/v1/satellite-ops/visible_satellites?${searchParams}`)
        .then(r => r.json())
    )
  }
  
  // ========== 星座資訊 API ==========
  
  async getConstellationInfo(): Promise<Record<string, unknown>> {
    return retryRequest(() =>
      netstackFetch('/api/v1/satellites/constellations/info').then(r => r.json())
    )
  }
  
  // ========== 性能指標 API ==========
  
  async getHandoverLatencyMetrics(): Promise<Array<Record<string, unknown>>> {
    return retryRequest(() =>
      netstackFetch('/api/v1/core-sync/metrics/performance').then(r => r.json())
    )
  }
}

// 單例導出
export const unifiedNetStackApi = new UnifiedNetStackApi()

// 向後兼容的導出
export default unifiedNetStackApi