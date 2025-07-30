/**
 * SimWorld API Client
 * 用於連接 SimWorld 後端的真實 TLE 和軌道數據
 */
import { simworldFetch, netstackFetch } from '../config/api-config';
import React, { useState, useEffect } from 'react';

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

class SimWorldApiClient {
  // 使用統一的 API 配置系統，不再繼承 BaseApiClient
  private pendingRequests: Map<string, Promise<any>> = new Map()
  
  private async fetchWithConfig(endpoint: string, options: RequestInit = {}) {
    return simworldFetch(endpoint, options);
  }

  /**
   * 獲取可見衛星列表 - 真實 TLE 數據（精確仰角過濾，適合LEO換手研究）
   */
  async getVisibleSatellites(
    minElevation: number = 5,       // 📡 適合換手研究的最小仰角（5度以上可進行換手）
    maxSatellites: number = 10,     // 🎯 適量衛星數量，符合3GPP NTN標準（6-8顆）
    observerLat: number = 24.9441667,    // 🇹🇼 NTPU觀測點緯度
    observerLon: number = 121.3713889,   // 🇹🇼 NTPU觀測點經度
    constellation: string = 'starlink'   // 🛰️ 星座選擇 (starlink, oneweb)
  ): Promise<VisibleSatellitesResponse> {
    // 創建請求去重鍵
    const requestKey = 'satellites-' + minElevation + '-' + maxSatellites + '-' + observerLat + '-' + observerLon + '-' + constellation;
    
    // 如果同樣的請求正在進行中，返回該 Promise
    if (this.pendingRequests.has(requestKey)) {
      console.log('🛰️ SimWorldApi: 重複請求被去重:', requestKey);
      return this.pendingRequests.get(requestKey)!;
    }
    
    // console.log('🆕 SimWorldApi: 新請求開始:', requestKey);
    
    // 創建並執行請求
    const executeRequest = async () => {
      try {
        // 📍 使用精確仰角過濾，適合換手研究（返回5-6顆可見衛星）
        const params = {
          count: Math.min(maxSatellites, 150),  // 保持最大衛星數量限制
          min_elevation_deg: minElevation,  // 使用傳入的仰角參數 (通常是5度)
          global_view: 'false',  // ✅ 修復：使用精確仰角過濾，而非全球視野
          observer_lat: observerLat,  // NTPU座標 (24.9441667°N)
          observer_lon: observerLon,  // NTPU座標 (121.3713889°E)
          observer_alt: 0.0,  // 觀測點高度
          constellation: constellation,  // 🛰️ 星座選擇
        };

        // 🔧 構建查詢參數字符串
        const queryParams = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
          queryParams.append(key, value.toString());
        });
        
        // 使用 NetStack API 的預計算端點 (修正路徑)
        const endpoint = `/api/v1/satellites/precomputed/ntpu?${queryParams.toString()}`;

        // 只在首次調用時記錄 API 端點
        // console.log(`🛰️ SimWorldApi: 調用 NetStack 衛星API ${endpoint}`);

        // 🚀 使用 NetStack API 配置調用預計算端點
        const response = await netstackFetch(endpoint);
        if (!response.ok) {
          throw new Error('API request failed: ' + response.statusText);
        }
        const data = await response.json() as {
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
          data_source?: {
            type: string;
            description: string;
            is_simulation: boolean;
          };
          computation_metadata?: {
            constellation?: string;
            elevation_threshold?: number;
            use_layered?: boolean;
            environment_factor?: string;
            computation_date?: string;
            total_satellites_input?: number;
            filtered_satellites_count?: number;
            filtering_efficiency?: string;
            computation_type?: string;
            data_source?: string;
          };
        };
        
        // 簡化的數據來源檢測和日誌
        const satelliteCount = data.filtered_satellites?.length || 0;
        const dataSource = data.computation_metadata?.data_source || 'unknown';
        const responseConstellation = data.computation_metadata?.constellation || 'unknown';

        // 只在衛星數量為 0 或有問題時記錄日誌
        if (satelliteCount === 0 || satelliteCount > 15) {
          console.log(`🛰️ [${responseConstellation.toUpperCase()}] ${satelliteCount}顆衛星 | 來源: ${dataSource}`);
        }

        // 只在有問題時顯示詳細信息
        if (satelliteCount === 0) {
          console.warn(`⚠️ 無衛星數據:`, data);
        }
        
        // 📡 檢查衛星數量是否符合換手研究需求（5-6顆為理想）
        if (data.filtered_satellites && data.filtered_satellites.length < 2) {
          console.warn(`📡 SimWorldApi: 衛星數量偏少 (${data.filtered_satellites.length} 顆)`);
          console.warn(`📡 建議: 檢查後端TLE數據或仰角設定`);
        }
        
        // 檢查 API 是否返回錯誤
        if (data.error) {
          console.error(`🛰️ SimWorldApi: API 返回錯誤: ${data.error}`);
          throw new Error('API Error: ' + data.error);
        }
        
        if (!data.filtered_satellites || data.filtered_satellites.length === 0) {
          console.warn(`🛰️ SimWorldApi: API 未返回衛星數據或返回空數組`);
          console.warn(`🛰️ SimWorldApi: 響應結構檢查:`, {
            hasSatellites: 'filtered_satellites' in data,
            satellitesType: typeof data.filtered_satellites,
            satellitesLength: data.filtered_satellites?.length,
            responseKeys: Object.keys(data)
          });
          
          // 如果後端處理了衛星但沒有找到可見的，記錄詳細信息
          if (data.processed !== undefined && data.visible !== undefined && data.visible === 0) {
            console.warn(`🛰️ SimWorldApi: 後端處理了 ${data.processed} 顆衛星，但沒有可見衛星`);
            console.warn(`📡 仰角過濾模式下無可見衛星，可能原因:`);
            console.warn(`   1. 仰角閾值設定過高 (當前: ${minElevation}°)`);
            console.warn(`   2. NTPU觀測點位置沒有適合的衛星通過`);
            console.warn(`   3. TLE數據需要更新`);
            console.warn(`   4. 時間點沒有衛星在可見區域內`);
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
            total_visible: data.filtered_satellites?.length || 0,
            satellites: (data.filtered_satellites || data.results?.satellites || [])
              // 🛰️ 暫時移除仰角過濾，因為後端軌道計算返回的 elevation 都是 0
              // TODO: 修復後端軌道計算後，恢復仰角過濾邏輯
              // ?.filter((sat: any) => {
              //   const elevation = sat.position?.elevation || sat.elevation_deg || sat.elevation || 0;
              //   return elevation >= 5;
              // })
              ?.map((sat: any) => {
              // 🔄 支援多種後端響應格式，適應新舊API
              // 📍 優先使用 position 物件內的數據（新API格式），然後是 NetStack 直接字段
              const elevation = sat.position?.elevation || sat.elevation_deg || sat.elevation || 0;
              const azimuth = sat.position?.azimuth || sat.azimuth_deg || sat.azimuth || 0;
              const range = sat.position?.range || sat.range_km || sat.distance_km || sat.range || 0;
              
              // 🐛 Debug: 檢查數據映射
              if (sat.name && sat.name.includes('31879')) {
                console.log(`🔍 Debug ${sat.name}:`, {
                  rawSat: sat,
                  elevation: elevation,
                  azimuth: azimuth,
                  range: range,
                  positionObject: sat.position
                });
              }
              const altitude = sat.position?.altitude || sat.orbit_altitude_km || sat.altitude || 0;
              const latitude = sat.position?.latitude || sat.latitude || 0;
              const longitude = sat.position?.longitude || sat.longitude || 0;
              
              return {
                id: parseInt(sat.norad_id || sat.id || '0') || 0,
                name: sat.name || '',
                norad_id: sat.norad_id || sat.id || '',
                // 🔧 DeviceListPanel期望的頂層字段格式
                elevation_deg: elevation,
                azimuth_deg: azimuth,
                distance_km: range,
                // 🔧 保持position物件以向後兼容
                position: {
                  latitude: latitude,
                  longitude: longitude, 
                  altitude: altitude,
                  elevation: elevation,
                  azimuth: azimuth,
                  range: range,
                  velocity: sat.velocity_km_s || sat.velocity || 7.5,
                  doppler_shift: sat.doppler_shift || 0
                },
                timestamp: new Date().toISOString(),
                signal_quality: {
                  elevation_deg: elevation,
                  range_km: range,
                  estimated_signal_strength: sat.estimated_signal_strength || Math.min(100, Math.max(0, elevation * 2 + 50)),
                  path_loss_db: sat.path_loss_db || (20 * Math.log10(Math.max(1, range)) + 92.45 + 20 * Math.log10(2.15))
                }
              };
            }) || []
          },
          timestamp: new Date().toISOString()
        } as VisibleSatellitesResponse;
        
        // console.log(`🛰️ SimWorldApi: 最終結果:`, result)
        return result;
      } catch (error) {
        console.error(`🛰️ SimWorldApi: 獲取衛星數據時發生錯誤:`, error);
        console.error(`🛰️ SimWorldApi: 錯誤詳細信息:`, {
          errorName: (error as any)?.name,
          errorMessage: (error as any)?.message,
          endpoint: '/api/v1/satellites/precomputed/ntpu'
        });
        throw error;
      } finally {
        // 清理去重 Map
        this.pendingRequests.delete(requestKey);
      }
    };

    // 執行請求並加入去重 Map
    const requestPromise = executeRequest();
    this.pendingRequests.set(requestKey, requestPromise);

    return requestPromise;
  }

  // Get satellite position
  async getSatellitePosition(satelliteId: string): Promise<SatellitePosition> {
    const response = await this.fetchWithConfig('/v1/satellites/' + satelliteId + '/position');
    if (!response.ok) {
      throw new Error('Failed to get satellite position: ' + response.statusText);
    }
    return response.json();
  }

  /**
   * 獲取衛星軌跡預測 - 使用 Skyfield 計算
   */
  async getSatelliteTrajectory(
    satelliteId: string,
    durationHours: number = 2,
    stepMinutes: number = 5
  ): Promise<SatelliteTrajectory> {
    const response = await this.fetchWithConfig(
      '/v1/satellites/' + satelliteId + '/trajectory-cqrs?duration_hours=' + durationHours + '&step_minutes=' + stepMinutes
    );
    if (!response.ok) {
      throw new Error('Failed to get satellite trajectory: ' + response.statusText);
    }
    return response.json();
  }
  /**
   * 獲取換手候選衛星 - 基於真實軌道計算
   */
  async getHandoverCandidates(
    currentSatelliteId: string,
    ueLocation?: { lat: number; lon: number }
  ): Promise<SatelliteHandoverCandidates> {
    const params = new URLSearchParams();
    if (ueLocation) {
      params.append('ue_lat', ueLocation.lat.toString());
      params.append('ue_lon', ueLocation.lon.toString());
    }
    const response = await this.fetchWithConfig(
      '/v1/satellites/handover/candidates?current_satellite=' + currentSatelliteId + '&' + params
    );
    if (!response.ok) {
      throw new Error('Failed to get handover candidates: ' + response.statusText);
    }
    return response.json();
  }
  /**
   * 批量獲取多個衛星位置 - 優化性能
   */
  async getBatchSatellitePositions(
    satelliteIds: string[]
  ): Promise<SatellitePosition[]> {
    const response = await this.fetchWithConfig(
      `/v1/satellites/batch-positions`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ satellite_ids: satelliteIds }),
      }
    );
    if (!response.ok) {
      throw new Error('Failed to get batch satellite positions: ' + response.statusText);
    }
    return response.json();
  }
  /**
   * 更新所有衛星的 TLE 數據
   */
  async updateAllTLEs(): Promise<{ updated_count: number; status: string }> {
    const response = await this.fetchWithConfig(
      `/v1/satellites/update-all-tles`,
      {
        method: 'POST',
      }
    );
    if (!response.ok) {
      throw new Error('Failed to update TLEs: ' + response.statusText);
    }
    return response.json();
  }
  /**
   * 獲取 AI-RAN 決策數據
   */
  async getAIRANDecisions(limit: number = 10): Promise<AIRANDecision[]> {
    // 注意：這個端點可能需要根據實際 API 調整
    const response = await this.fetchWithConfig(
      '/v1/ai-ran/decisions?limit=' + limit
    );
    if (!response.ok) {
      // 如果端點不存在，返回模擬數據以保持兼容性
      console.warn('AI-RAN endpoint not available, using fallback data')
      return this.generateMockAIRANDecisions(limit);
    }
    return response.json();
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
    const params = new URLSearchParams({ satellite_id: satelliteId });
    if (ueLocation) {
      params.append('ue_lat', ueLocation.lat.toString());
      params.append('ue_lon', ueLocation.lon.toString());
    }
    const response = await this.fetchWithConfig(
      `/v1/wireless/satellite-ntn-simulation?${params}`
    );
    if (!response.ok) {
      throw new Error('Failed to get communication quality: ' + response.statusText);
    }
    return response.json();
  }

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
  minElevation: number = 5,       // 📡 換手研究預設5度仰角
  maxSatellites: number = 10,     // 🎯 適量衛星數量，符合3GPP NTN標準
  observerLat: number = 24.9441667,    // 🇹🇼 NTPU觀測點緯度
  observerLon: number = 121.3713889,   // 🇹🇼 NTPU觀測點經度
  constellation: string = 'starlink'   // 🛰️ 星座選擇 (starlink, oneweb)
) => {
  const [satellites, setSatellites] = useState<SatellitePosition[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log(`🪝 [${constellation.toUpperCase()}] 載入衛星數據...`);

    const fetchSatellites = async () => {
      try {
        setLoading(true);
        const data = await simWorldApi.getVisibleSatellites(minElevation, maxSatellites, observerLat, observerLon, constellation);
        setSatellites(data.results?.satellites || []);
        setError(null);
      } catch (err) {
        console.error(`❌ [${constellation.toUpperCase()}] 載入失敗:`, err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    }

    fetchSatellites();
    // 定期更新衛星位置 - 已根據用戶要求移除
    // const interval = setInterval(fetchSatellites, refreshInterval)
    // return () => clearInterval(interval)
  }, [minElevation, maxSatellites, observerLat, observerLon, constellation])

  return { satellites, loading, error, refetch: () => simWorldApi.getVisibleSatellites(minElevation, maxSatellites, observerLat, observerLon) };
}

export default SimWorldApiClient