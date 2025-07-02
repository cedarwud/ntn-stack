/**
 * SimWorld API Client
 * 用於連接 SimWorld 後端的真實 TLE 和軌道數據
 */
import { BaseApiClient } from './base-api'
import * as React from 'react'

export interface SatellitePosition {
  id: number
  name: string
  norad_id: string
  position: {
    latitude: number
    longitude: number
    altitude: number
    elevation: number
    azimuth: number
    range: number
    velocity: number
    doppler_shift: number
  }
  timestamp: string
  signal_quality: {
    elevation_deg: number
    range_km: number
    estimated_signal_strength: number
    path_loss_db: number
  }
}

export interface VisibleSatellitesResponse {
  success: boolean
  observer: {
    latitude: number
    longitude: number
    altitude: number
  }
  search_criteria: {
    min_elevation: number
    constellation: string | null
    max_results: number
  }
  results: {
    total_visible: number
    satellites: SatellitePosition[]
  }
  timestamp: string
}

export interface SatelliteTrajectory {
  satellite_id: string
  norad_id: number
  name: string
  trajectory_points: Array<{
    timestamp: string
    position: {
      latitude: number
      longitude: number
      altitude_km: number
    }
    velocity: {
      x: number
      y: number
      z: number
    }
    orbital_elements: {
      semi_major_axis: number
      eccentricity: number
      inclination: number
      longitude_ascending_node: number
      argument_perigee: number
      mean_anomaly: number
    }
  }>
  prediction_duration_hours: number
  step_size_minutes: number
}

export interface SatelliteHandoverCandidates {
  current_satellite: SatellitePosition
  candidates: Array<{
    satellite: SatellitePosition
    handover_score: number
    predicted_handover_time: string
    signal_quality: {
      snr_db: number
      rssi_dbm: number
      estimated_throughput_mbps: number
    }
    geometric_factors: {
      elevation_advantage: number
      range_advantage: number
      velocity_compatibility: number
    }
  }>
  recommendation: {
    best_candidate_id: string
    confidence_score: number
    expected_handover_window_seconds: number
  }
}

export interface AIRANDecision {
  decision_id: string
  timestamp: string
  decision_type: 'beam_optimization' | 'power_control' | 'interference_mitigation'
  ai_model_version: string
  input_parameters: {
    current_snr: number
    interference_level: number
    user_load: number
    satellite_positions: SatellitePosition[]
  }
  decision_output: {
    action: string
    confidence: number
    expected_improvement_db: number
    implementation_time_ms: number
  }
  execution_status: 'analyzing' | 'executing' | 'completed' | 'failed'
  performance_metrics?: {
    actual_improvement_db: number
    execution_time_ms: number
    success_rate: number
  }
}

class SimWorldApiClient extends BaseApiClient {
  constructor() {
    let baseUrl = 'http://localhost:8888'  // 修正端口：對應 Docker 映射端口
    
    // 在瀏覽器環境中使用相對路徑，讓 Vite 代理處理
    if (typeof window !== 'undefined') {
      // 使用空字符串作為 baseUrl，讓所有請求變成相對路徑
      // 這樣 /api 路徑會被 Vite 代理到 simworld_backend:8000
      baseUrl = ''
      
      // 檢查環境變數是否有自定義的 SimWorld URL
      const envUrl = (window as unknown as { __SIMWORLD_API_URL__?: string }).__SIMWORLD_API_URL__
      if (envUrl) {
        baseUrl = envUrl
      }
    }
    
    
    super(baseUrl)
  }

  /**
   * 獲取可見衛星列表 - 真實 TLE 數據（全球視野，無地域限制）
   */
  async getVisibleSatellites(
    minElevation: number = -10,     // 🌍 全球視野使用更寬鬆的仰角（地平線以下）
    maxSatellites: number = 100,    // 🚀 大幅增加衛星數量
    observerLat: number = 0.0,      // 保留參數但在全球模式下忽略
    observerLon: number = 0.0       // 保留參數但在全球模式下忽略
  ): Promise<VisibleSatellitesResponse> {
    // 🌍 為了獲得真正的全球視野，我們使用寬鬆的仰角限制和多個虛擬觀測點
    const params = {
      count: Math.min(maxSatellites, 150),  // 🚀 大幅提高到150顆衛星
      min_elevation_deg: -10,  // 🌍 使用-10度寬鬆仰角（包含地平線以下）
      global_view: 'true',  // 強制全球視野
      // 🌍 不傳遞觀測點座標，讓後端使用全球模式
      // observer_lat: observerLat,  // 註釋掉以啟用真正的全球模式
      // observer_lon: observerLon,  // 註釋掉以啟用真正的全球模式
    }
    const endpoint = '/api/v1/satellite-ops/visible_satellites'
    
    console.log(`🛰️ SimWorldApi: 調用全球視野模式 ${endpoint}，參數:`, params)
    console.log(`🌍 SimWorldApi: 請求全球範圍衛星，不限制地域觀測點`)
    
    try {
      // 🚀 使用內建的快取機制並設置超時（基於 BaseApiClient）
      const response = await this.get<{ 
        success?: boolean;
        satellites?: Array<{ 
          norad_id?: string; 
          name?: string; 
          orbit_altitude_km?: number; 
          elevation_deg?: number; 
          azimuth_deg?: number; 
          range_km?: number; 
          distance_km?: number;
          velocity?: number; 
          velocity_km_s?: number;
          doppler_shift?: number; 
          estimated_signal_strength?: number; 
          path_loss_db?: number; 
        }>;
        error?: string;
        message?: string;
        processed?: number;
        visible?: number;
        status?: string;
        performance?: Record<string, unknown>;
      }>(endpoint, params)
      
      console.log(`🛰️ SimWorldApi: API 原始響應:`, response)
      console.log(`🌍 SimWorldApi: 全球視野模式接收到 ${response.satellites?.length || 0} 顆衛星`)
      
      // 詳細分析 API 響應
      console.log(`🛰️ SimWorldApi: 響應分析:`, {
        hasResponse: !!response,
        responseKeys: response ? Object.keys(response) : [],
        hasSatellites: !!response.satellites,
        satellitesLength: response.satellites?.length,
        satellitesType: typeof response.satellites,
        isArray: Array.isArray(response.satellites),
        status: response.status,
        processed: response.processed,
        visible: response.visible,
        error: response.error,
        message: response.message
      })
      
      // 🌍 只在衛星數量非常少時警告（0-1顆才異常）
      if (response.satellites && response.satellites.length < 2) {
        console.warn(`🌍 SimWorldApi: 衛星數量偏少 (${response.satellites.length} 顆)`)
        console.warn(`🌍 建議: 檢查後端TLE數據或API配置`)
      }
      
      // 檢查 API 是否返回錯誤
      if (response.error) {
        console.error(`🛰️ SimWorldApi: API 返回錯誤: ${response.error}`)
        throw new Error(`API Error: ${response.error}`)
      }
      
      if (!response.satellites || response.satellites.length === 0) {
        console.warn(`🛰️ SimWorldApi: API 未返回衛星數據或返回空數組`)
        console.warn(`🛰️ SimWorldApi: 響應結構檢查:`, {
          hasSatellites: 'satellites' in response,
          satellitesType: typeof response.satellites,
          satellitesLength: response.satellites?.length,
          responseKeys: Object.keys(response)
        })
        
        // 如果後端處理了衛星但沒有找到可見的，記錄詳細信息
        if (response.processed !== undefined && response.visible !== undefined && response.visible === 0) {
          console.warn(`🛰️ SimWorldApi: 後端處理了 ${response.processed} 顆衛星，但沒有可見衛星`)
          console.warn(`🌍 全球視野模式下仍無可見衛星，可能原因:`)
          console.warn(`   1. 後端仍在使用地域限制邏輯`)
          console.warn(`   2. TLE數據庫衛星數量不足`)
          console.warn(`   3. 仰角限制仍然過嚴格`)
          console.warn(`   4. 需要後端實現真正的全球視野算法`)
        }
      }
      
      // 轉換響應格式以匹配原有接口
      const result = {
        success: true,
        observer: {
          latitude: observerLat,
          longitude: observerLon,
          altitude: 0.0
        },
        search_criteria: {
          min_elevation: minElevation,
          constellation: null,
          max_results: Math.min(maxSatellites, 20)
        },
        results: {
          total_visible: response.satellites?.length || 0,
          satellites: response.satellites?.map((sat: { 
            norad_id?: string; 
            name?: string; 
            orbit_altitude_km?: number; 
            elevation_deg?: number; 
            azimuth_deg?: number; 
            range_km?: number; 
            distance_km?: number;
            velocity?: number; 
            velocity_km_s?: number;
            doppler_shift?: number; 
            estimated_signal_strength?: number; 
            path_loss_db?: number; 
          }, _index: number) => {
            return {
              id: parseInt(sat.norad_id) || 0,
              name: sat.name,
              norad_id: sat.norad_id,
              position: {
                latitude: 0, // 舊端點沒提供這些信息
                longitude: 0,
                altitude: sat.orbit_altitude_km || 0,
                elevation: sat.elevation_deg,
                azimuth: sat.azimuth_deg,
                range: sat.distance_km,
                velocity: sat.velocity_km_s || 0,
                doppler_shift: 0
              },
              timestamp: new Date().toISOString(),
              signal_quality: {
                elevation_deg: sat.elevation_deg,
                range_km: sat.distance_km,
                estimated_signal_strength: Math.min(100, (sat.elevation_deg || 0) * 2),
                path_loss_db: 20 * Math.log10(Math.max(1, sat.distance_km || 1000)) + 92.45 + 20 * Math.log10(2.15)
              }
            }
          }) || []
        },
        timestamp: new Date().toISOString()
      } as VisibleSatellitesResponse
      
      console.log(`🛰️ SimWorldApi: 最終結果:`, result)
      return result
    } catch (error) {
      console.error(`🛰️ SimWorldApi: 獲取衛星數據時發生錯誤:`, error)
      console.error(`🛰️ SimWorldApi: 錯誤詳細信息:`, {
        errorName: error?.name,
        errorMessage: error?.message,
        endpoint,
        params
      })
      throw error
    }
  }

  /**
   * 獲取特定衛星的即時位置
   */
  async getSatellitePosition(satelliteId: string): Promise<SatellitePosition> {
    return this.get<SatellitePosition>(`/api/v1/satellites/${satelliteId}/position`)
  }

  /**
   * 獲取衛星軌跡預測 - 使用 Skyfield 計算
   */
  async getSatelliteTrajectory(
    satelliteId: string,
    durationHours: number = 2,
    stepMinutes: number = 5
  ): Promise<SatelliteTrajectory> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/satellites/${satelliteId}/trajectory-cqrs?duration_hours=${durationHours}&step_minutes=${stepMinutes}`
    )
    if (!response.ok) {
      throw new Error(`Failed to get satellite trajectory: ${response.statusText}`)
    }
    return response.json()
  }
  /**
   * 獲取換手候選衛星 - 基於真實軌道計算
   */
  async getHandoverCandidates(
    currentSatelliteId: string,
    ueLocation?: { lat: number; lon: number }
  ): Promise<SatelliteHandoverCandidates> {
    const params = new URLSearchParams()
    if (ueLocation) {
      params.append('ue_lat', ueLocation.lat.toString())
      params.append('ue_lon', ueLocation.lon.toString())
    }
    const response = await fetch(
      `${this.baseUrl}/api/v1/satellites/handover/candidates?current_satellite=${currentSatelliteId}&${params}`
    )
    if (!response.ok) {
      throw new Error(`Failed to get handover candidates: ${response.statusText}`)
    }
    return response.json()
  }
  /**
   * 批量獲取多個衛星位置 - 優化性能
   */
  async getBatchSatellitePositions(
    satelliteIds: string[]
  ): Promise<SatellitePosition[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/satellites/batch-positions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ satellite_ids: satelliteIds }),
      }
    )
    if (!response.ok) {
      throw new Error(`Failed to get batch satellite positions: ${response.statusText}`)
    }
    return response.json()
  }
  /**
   * 更新所有衛星的 TLE 數據
   */
  async updateAllTLEs(): Promise<{ updated_count: number; status: string }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/satellites/update-all-tles`,
      {
        method: 'POST',
      }
    )
    if (!response.ok) {
      throw new Error(`Failed to update TLEs: ${response.statusText}`)
    }
    return response.json()
  }
  /**
   * 獲取 AI-RAN 決策數據
   */
  async getAIRANDecisions(limit: number = 10): Promise<AIRANDecision[]> {
    // 注意：這個端點可能需要根據實際 API 調整
    const response = await fetch(
      `${this.baseUrl}/api/v1/ai-ran/decisions?limit=${limit}`
    )
    if (!response.ok) {
      // 如果端點不存在，返回模擬數據以保持兼容性
      console.warn('AI-RAN endpoint not available, using fallback data')
      return this.generateMockAIRANDecisions(limit)
    }
    return response.json()
  }
  /**
   * 獲取通信品質數據 - SINR, 干擾等
   */
  async getCommunicationQuality(
    satelliteId: string,
    ueLocation?: { lat: number; lon: number }
  ): Promise<{
    snr_db: number
    rssi_dbm: number
    sinr_db: number
    interference_level: number
    signal_quality: 'excellent' | 'good' | 'fair' | 'poor'
    estimated_throughput_mbps: number
  }> {
    const params = new URLSearchParams({ satellite_id: satelliteId })
    if (ueLocation) {
      params.append('ue_lat', ueLocation.lat.toString())
      params.append('ue_lon', ueLocation.lon.toString())
    }
    const response = await fetch(
      `${this.baseUrl}/api/v1/wireless/satellite-ntn-simulation?${params}`
    )
    if (!response.ok) {
      throw new Error(`Failed to get communication quality: ${response.statusText}`)
    }
    return response.json()
  }
  /**
  /**模擬 AI-RAN 決策數據 (fallback)
  /**
   * 模擬 AI-RAN 決策數據 (fallback)
   */
  private generateMockAIRANDecisions(limit: number): AIRANDecision[] {
    return Array.from({ length: limit }, (_, i) => ({
      decision_id: `ai_decision_${Date.now()}_${i}`,
      timestamp: new Date(Date.now() - i * 30000).toISOString(),
      decision_type: ['beam_optimization', 'power_control', 'interference_mitigation'][
        i % 3
      ] as AIRANDecision['decision_type'],
      ai_model_version: 'v2.1.0',
      input_parameters: {
        current_snr: 15 + Math.random() * 10,
        interference_level: Math.random() * 5,
        user_load: Math.random() * 100,
        satellite_positions: [],
      },
      decision_output: {
        action: `AI優化動作 ${i + 1}`,
        confidence: 0.85 + Math.random() * 0.1,
        expected_improvement_db: 2 + Math.random() * 3,
        implementation_time_ms: 100 + Math.random() * 200,
      },
      execution_status: ['completed', 'executing', 'analyzing'][
        Math.floor(Math.random() * 3)
      ] as AIRANDecision['execution_status'],
      performance_metrics: {
        actual_improvement_db: 2 + Math.random() * 2.5,
        execution_time_ms: 150 + Math.random() * 100,
        success_rate: 0.9 + Math.random() * 0.1,
      },
    }))
  }
}

// 創建全局實例
export const simWorldApi = new SimWorldApiClient()

/**
 * React Hook 用於獲取可見衛星
 */
export const useVisibleSatellites = (
  minElevation: number = -10,     // 全球視野預設-10度
  maxSatellites: number = 100,    // 增加預設衛星數量
  refreshInterval: number = 30000,
  observerLat: number = 0.0,      // 全球視野預設赤道位置
  observerLon: number = 0.0       // 全球視野預設本初子午線
) => {
  const [satellites, setSatellites] = React.useState<SatellitePosition[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    const fetchSatellites = async () => {
      try {
        setLoading(true)
        const data = await simWorldApi.getVisibleSatellites(minElevation, maxSatellites, observerLat, observerLon)
        setSatellites(data.results?.satellites || [])
        setError(null)
      } catch (err) {
        console.error('useVisibleSatellites: Error fetching satellites:', err)
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchSatellites()
    // 定期更新衛星位置
    const interval = setInterval(fetchSatellites, refreshInterval)
    return () => clearInterval(interval)
  }, [minElevation, maxSatellites, refreshInterval, observerLat, observerLon])

  return { satellites, loading, error, refetch: () => simWorldApi.getVisibleSatellites(minElevation, maxSatellites, observerLat, observerLon) }
}

export default SimWorldApiClient