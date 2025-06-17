/**
 * NetStack API Client
 * 用於連接 NetStack 後端的真實 API 數據
 */

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
  ieee_infocom_2024_features: {
    fine_grained_sync_active: boolean
    two_point_prediction: boolean
    signaling_free_coordination: boolean
    binary_search_refinement: number
  }
}

export interface SatelliteAccessPredictionResponse {
  prediction_id: string
  ue_id: string
  satellite_id: string
  current_time: number
  future_time: number
  delta_t_seconds: number
  handover_required: boolean
  handover_trigger_time?: number
  current_satellite: {
    satellite_id: string
    name: string
    signal_strength: number
    elevation: number
    azimuth: number
    distance_km: number
  }
  future_satellite: {
    satellite_id: string
    name: string
    signal_strength: number
    elevation: number
    azimuth: number
    distance_km: number
  }
  binary_search_result?: {
    handover_time: number
    iterations: Array<{
      iteration: number
      start_time: number
      end_time: number
      mid_time: number
      satellite: string
      precision: number
      completed: boolean
    }>
    iteration_count: number
    final_precision: number
  }
  // 實際 API 響應的新屬性
  predicted_access_time: string
  confidence_score: number
  error_bound_ms: number
  binary_search_iterations: number
  convergence_achieved: boolean
  access_probability: number
  algorithm_details: {
    two_point_prediction: {
      time_t: string
      time_t_delta: string
    }
    binary_search_refinement: {
      iterations: number
      converged: boolean
    }
  }
  timestamp: string
  
  // 保留舊屬性以兼容組件代碼
  prediction_confidence?: number
  accuracy_percentage?: number
  algorithm_metadata: {
    execution_time_ms: number
    algorithm_version: string
    ieee_infocom_2024_compliance: boolean
  }
}

export interface HandoverMeasurementData {
  measurement_id: string
  timestamp: number
  latency_ms: number
  success_rate: number
  handover_type: 'NTN' | 'NTN-GS' | 'NTN-SMN' | 'Proposed'
  ue_id: string
  source_satellite: string
  target_satellite: string
  additional_metrics: {
    signaling_overhead: number
    interruption_time_ms: number
    qos_impact_score: number
  }
}

export interface HandoverPredictionRequest {
  ue_id: string
  ue_lat: number
  ue_lon: number
  ue_alt?: number
  current_satellite: string
  candidate_satellites: string[]
  search_range_seconds?: number
}

export interface HandoverPredictionResponse {
  prediction_id: string
  ue_id: string
  current_satellite: string
  predicted_handovers: Array<{
    target_satellite: string
    handover_time: number
    confidence_score: number
    signal_quality_prediction: {
      current_snr: number
      predicted_snr: number
      signal_threshold: number
    }
    elevation_prediction: {
      current_elevation: number
      predicted_elevation: number
      min_elevation_threshold: number
    }
    geometric_factors: {
      distance_km: number
      velocity_match: number
      orbit_compatibility: number
    }
    reason: 'signal_degradation' | 'satellite_elevation' | 'orbital_transition' | 'load_balancing'
    success_probability: number
  }>
  search_window: {
    start_time: number
    end_time: number
    duration_seconds: number
  }
  algorithm_metadata: {
    algorithm_type: 'fast_prediction'
    execution_time_ms: number
    prediction_accuracy: number
    geographic_block_id?: string
    ue_strategy: 'flexible' | 'consistent'
  }
}

class NetStackApiClient {
  private baseUrl = '/netstack'  // 使用代理路徑
  
  constructor() {
    // 檢查環境變數是否有自定義的 NetStack URL
    if (typeof window !== 'undefined') {
      const envUrl = (window as any).__NETSTACK_API_URL__
      if (envUrl) {
        this.baseUrl = envUrl
      }
    }
  }

  /**
   * 獲取核心同步狀態
   */
  async getCoreSync(): Promise<CoreSyncStatus> {
    const response = await fetch(`${this.baseUrl}/api/v1/core-sync/status`)
    if (!response.ok) {
      throw new Error(`Failed to get core sync status: ${response.statusText}`)
    }
    return response.json()
  }

  /**
   * 預測衛星存取 - 基於真實的 IEEE INFOCOM 2024 演算法
   */
  async predictSatelliteAccess(
    request: SatelliteAccessPredictionRequest
  ): Promise<SatelliteAccessPredictionResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/core-sync/prediction/satellite-access`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to predict satellite access: ${response.statusText}`)
    }
    
    return response.json()
  }

  /**
   * 快速換手預測 - 基於地理區塊劃分的 Algorithm 2
   */
  async predictHandover(
    request: HandoverPredictionRequest
  ): Promise<HandoverPredictionResponse> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/satellite-tle/handover/predict`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to predict handover: ${response.statusText}`)
    }
    
    return response.json()
  }

  /**
   * 啟動核心同步服務
   */
  async startCoreSync(): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/core-sync/service/start`,
      {
        method: 'POST',
      }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to start core sync: ${response.statusText}`)
    }
  }

  /**
   * 停止核心同步服務
   */
  async stopCoreSync(): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/core-sync/service/stop`,
      {
        method: 'POST',
      }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to stop core sync: ${response.statusText}`)
    }
  }

  /**
   * 獲取效能指標 - 換手延遲數據
   */
  async getHandoverLatencyMetrics(): Promise<HandoverMeasurementData[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/core-sync/metrics/performance`
    )
    
    if (!response.ok) {
      throw new Error(`Failed to get handover metrics: ${response.statusText}`)
    }
    
    const data = await response.json()
    // 假設 API 返回的數據結構需要轉換
    return data.handover_measurements || []
  }

  /**
   * 獲取最近的同步事件
   */
  async getRecentSyncEvents(): Promise<any[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/core-sync/events/recent`
    )
    
    if (!response.ok) {
      throw new Error(`Failed to get recent sync events: ${response.statusText}`)
    }
    
    return response.json()
  }

  /**
   * 觸發緊急重新同步
   */
  async triggerEmergencyResync(): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/core-sync/emergency/resync`,
      {
        method: 'POST',
      }
    )
    
    if (!response.ok) {
      throw new Error(`Failed to trigger emergency resync: ${response.statusText}`)
    }
  }

  /**
   * 獲取健康檢查狀態
   */
  async getHealthStatus(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/core-sync/health`)
    
    if (!response.ok) {
      throw new Error(`Failed to get health status: ${response.statusText}`)
    }
    
    return response.json()
  }
}

// 創建全局實例
export const netStackApi = new NetStackApiClient()

/**
 * React Hook 用於獲取核心同步狀態
 */
export const useCoreSync = () => {
  const [status, setStatus] = React.useState<CoreSyncStatus | null>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true)
        const data = await netStackApi.getCoreSync()
        setStatus(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()
    
    // 每 5 秒更新一次狀態
    const interval = setInterval(fetchStatus, 5000)
    
    return () => clearInterval(interval)
  }, [])

  return { status, loading, error, refetch: () => netStackApi.getCoreSync() }
}

// 需要 React 導入
import * as React from 'react'

export default NetStackApiClient