/**
 * Handover API Service
 * 換手相關 API 服務
 */

import api from './api'

// API 請求/響應類型定義
export interface SatelliteSelectionRequest {
  ue_id: string
  ue_latitude: number
  ue_longitude: number
  ue_altitude?: number
  consider_future?: boolean
  scenario_type?: string
}

export interface SatelliteSelectionResponse {
  success: boolean
  selected_satellite?: {
    satellite_id: string
    satellite_name: string
    elevation_deg: number
    azimuth_deg: number
    distance_km: number
    signal_strength_dbm: number
    orbital_velocity_km_s: number
    coverage_duration_sec: number
    load_ratio: number
    overall_score: number
  }
  total_candidates: number
  filtered_candidates: number
  selection_time_ms: number
  constraint_scores: Record<string, number>
  recommendation_confidence: number
}

export interface WeatherPredictionRequest {
  ue_id: string
  ue_latitude: number
  ue_longitude: number
  ue_altitude?: number
  satellite_candidates: Array<{
    satellite_id: string
    base_score: number
    elevation_deg: number
    signal_strength_dbm: number
  }>
  future_time_horizon_sec?: number
}

export interface WeatherPredictionResponse {
  success: boolean
  selected_satellite?: {
    satellite_id: string
    base_score: number
    weather_adjusted_score: number
    adjusted_signal_strength_dbm: number
    weather_risk_factor: number
  }
  atmospheric_conditions: {
    total_loss_db: number
    rain_attenuation_db: number
    cloud_attenuation_db: number
    atmospheric_absorption_db: number
    scintillation_db: number
    confidence_factor: number
  }
  prediction_confidence: number
  future_weather_outlook: {
    stability_forecast: string
    estimated_signal_variation_db: number
    risk_of_severe_weather: number
    recommended_backup_satellites: number
  }
  weather_impact_analysis: {
    processing_time_ms: number
    weather_adjustment_applied: boolean
    satellite_candidates_count: number
  }
  timestamp: number
}

export interface FineGrainedSyncRequest {
  ue_id: string
  ue_latitude: number
  ue_longitude: number
  ue_altitude?: number
  delta_t?: number
}

export interface TwoPointPredictionResponse {
  success: boolean
  current_satellite: string
  predicted_satellite: string
  current_time: number
  future_time: number
  handover_needed: boolean
  confidence: number
  delta_t_used: number
}

export interface BinarySearchResponse {
  success: boolean
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
  total_iterations: number
  final_precision: number
}

export interface AccuracyMetrics {
  current_accuracy: number
  rolling_accuracy: number
  accuracy_trend: string
  predictions_evaluated: number
  target_achievement: boolean
  confidence_interval: [number, number]
  accuracy_by_context: Record<string, number>
}

// API 服務類
export class HandoverAPIService {
  
  /**
   * 約束式衛星選擇
   */
  static async selectOptimalSatellite(request: SatelliteSelectionRequest): Promise<SatelliteSelectionResponse> {
    try {
      const response = await api.post('/handover/constrained-access/select-satellite', request)
      return response.data
    } catch (error) {
      console.error('衛星選擇 API 錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取約束配置
   */
  static async getConstraintConfiguration() {
    try {
      const response = await api.get('/handover/constrained-access/constraints')
      return response.data
    } catch (error) {
      console.error('獲取約束配置錯誤:', error)
      throw error
    }
  }

  /**
   * 更新約束配置
   */
  static async updateConstraintConfiguration(constraint: {
    constraint_type: string
    threshold_value?: number
    weight?: number
    is_hard_constraint?: boolean
  }) {
    try {
      const response = await api.put('/handover/constrained-access/constraints', constraint)
      return response.data
    } catch (error) {
      console.error('更新約束配置錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取約束式接入統計
   */
  static async getConstrainedAccessStatistics() {
    try {
      const response = await api.get('/handover/constrained-access/statistics')
      return response.data
    } catch (error) {
      console.error('獲取約束統計錯誤:', error)
      throw error
    }
  }

  /**
   * 天氣整合預測
   */
  static async predictWithWeatherIntegration(request: WeatherPredictionRequest): Promise<WeatherPredictionResponse> {
    try {
      const response = await api.post('/handover/weather-prediction/predict', request)
      return response.data
    } catch (error) {
      console.error('天氣整合預測錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取天氣條件
   */
  static async getWeatherConditions(latitude: number, longitude: number, altitude: number = 0) {
    try {
      const response = await api.get('/handover/weather-prediction/weather-conditions', {
        params: { latitude, longitude, altitude }
      })
      return response.data
    } catch (error) {
      console.error('獲取天氣條件錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取天氣預測統計
   */
  static async getWeatherPredictionStatistics() {
    try {
      const response = await api.get('/handover/weather-prediction/statistics')
      return response.data
    } catch (error) {
      console.error('獲取天氣統計錯誤:', error)
      throw error
    }
  }

  /**
   * 啟用/禁用天氣調整
   */
  static async toggleWeatherAdjustment(enabled: boolean) {
    try {
      const response = await api.post('/handover/weather-prediction/weather-adjustment/toggle', null, {
        params: { enabled }
      })
      return response.data
    } catch (error) {
      console.error('換手天氣調整錯誤:', error)
      throw error
    }
  }

  /**
   * 二點預測
   */
  static async twoPointPrediction(request: FineGrainedSyncRequest): Promise<TwoPointPredictionResponse> {
    try {
      const response = await api.post('/handover/fine-grained-sync/two-point-prediction', request)
      return response.data
    } catch (error) {
      console.error('二點預測錯誤:', error)
      throw error
    }
  }

  /**
   * Binary Search Refinement
   */
  static async binarySearchRefinement(
    ue_id: string,
    ue_latitude: number,
    ue_longitude: number,
    start_time: number,
    end_time: number,
    ue_altitude: number = 0
  ): Promise<BinarySearchResponse> {
    try {
      const response = await api.post('/handover/fine-grained-sync/binary-search-refinement', {
        ue_id,
        ue_latitude,
        ue_longitude,
        ue_altitude,
        start_time,
        end_time
      })
      return response.data
    } catch (error) {
      console.error('Binary Search 錯誤:', error)
      throw error
    }
  }

  /**
   * 更新預測記錄
   */
  static async updatePredictionRecord(request: FineGrainedSyncRequest) {
    try {
      const response = await api.post('/handover/fine-grained-sync/update-prediction', request)
      return response.data
    } catch (error) {
      console.error('更新預測記錄錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取預測記錄
   */
  static async getPredictionRecord(ue_id: string) {
    try {
      const response = await api.get(`/handover/fine-grained-sync/prediction/${ue_id}`)
      return response.data
    } catch (error) {
      console.error('獲取預測記錄錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取 Fine-Grained Sync 統計
   */
  static async getFineGrainedSyncStatistics() {
    try {
      const response = await api.get('/handover/fine-grained-sync/statistics')
      return response.data
    } catch (error) {
      console.error('獲取 Fine-Grained Sync 統計錯誤:', error)
      throw error
    }
  }

  /**
   * 記錄預測準確率
   */
  static async recordPredictionAccuracy(data: {
    ue_id: string
    predicted_satellite: string
    actual_satellite: string
    prediction_timestamp: number
    context?: Record<string, unknown>
  }) {
    try {
      const response = await api.post('/handover/fine-grained-sync/accuracy/record', data)
      return response.data
    } catch (error) {
      console.error('記錄預測準確率錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取準確率指標
   */
  static async getAccuracyMetrics(): Promise<AccuracyMetrics> {
    try {
      const response = await api.get('/handover/fine-grained-sync/accuracy/metrics')
      return response.data
    } catch (error) {
      console.error('獲取準確率指標錯誤:', error)
      throw error
    }
  }

  /**
   * 啟用/禁用準確率優化
   */
  static async toggleAccuracyOptimization(enabled: boolean) {
    try {
      const response = await api.post('/handover/fine-grained-sync/accuracy/toggle', null, {
        params: { enabled }
      })
      return response.data
    } catch (error) {
      console.error('換手準確率優化錯誤:', error)
      throw error
    }
  }

  /**
   * 獲取優化建議
   */
  static async getOptimizationRecommendations() {
    try {
      const response = await api.get('/handover/fine-grained-sync/accuracy/recommendations')
      return response.data
    } catch (error) {
      console.error('獲取優化建議錯誤:', error)
      throw error
    }
  }
}

export default HandoverAPIService