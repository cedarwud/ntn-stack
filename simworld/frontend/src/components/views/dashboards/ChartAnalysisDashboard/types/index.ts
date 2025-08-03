/**
 * Chart Analysis Dashboard 類型定義
 */

// 基礎介面
export interface ChartAnalysisDashboardProps {
  isOpen: boolean
  onClose: () => void
}

// 衛星和UAV數據類型
export interface SatellitePosition {
  latitude: number
  longitude: number
  altitude: number
  speed?: number
  heading?: number
  last_updated?: string
}

export interface SatelliteData {
  name?: string
  orbit_altitude_km?: number
  [key: string]: unknown
}

// 組件數據類型
export interface ComponentData {
  availability?: number
  accuracy_ms?: number
  latency_ms?: number
  throughput_mbps?: number
  error_rate?: number
  speed?: number
  altitude?: number
  [key: string]: number | string | boolean | undefined
}

// 數據集類型
export interface DatasetItem {
  label?: string
  data?: unknown
  borderColor?: string
  backgroundColor?: string
  yAxisID?: string
  tension?: number
  [key: string]: unknown
}

// 圖表數據項目
export interface ChartDataItem {
  label: string
  value: number | string
  dataset: string
  insights: string
}

// 系統指標
export interface SystemMetrics {
  cpu: number
  memory: number
  gpu: number
  networkLatency: number
}

// 核心同步數據
export interface CoreSyncData {
  component_states?: Record<string, {
    availability?: number
    latency_ms?: number
    throughput_mbps?: number
    error_rate?: number
    accuracy_ms?: number
  }>
  sync_performance?: {
    overall_accuracy_ms?: number
  }
}


// 策略歷史數據
export interface StrategyHistoryData {
  timestamps: string[]
  latency_reduction: number[]
  throughput_improvement: number[]
  success_rate: number[]
  computational_efficiency: number[]
}

// 標籤頁狀態
export type TabName = 
  | 'overview'
  | 'analysis'
  | 'algorithms'
  | 'performance'
  | 'monitoring'
  | 'strategy'
  | 'parameters'
  | 'system'

// Window 擴展（用於全域數據）
export interface WindowWithChartData extends Window {
  realComplexityData?: Record<string, unknown>
  realHandoverFailureData?: Record<string, unknown>
  realSystemResourceData?: Record<string, unknown>
  realTimeSyncData?: Record<string, unknown>
  realPerformanceRadarData?: Record<string, unknown>
  realProtocolStackData?: Record<string, unknown>
  realExceptionHandlingData?: Record<string, unknown>
  realQoETimeSeriesData?: Record<string, unknown>
  realGlobalCoverageData?: Record<string, unknown>
}

// API 響應類型
export interface ApiResponse<T = Record<string, unknown>> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// 圖表配置選項
export interface ChartOptions {
  responsive?: boolean
  maintainAspectRatio?: boolean
  plugins?: {
    legend?: {
      position?: 'top' | 'bottom' | 'left' | 'right'
      display?: boolean
    }
    title?: {
      display?: boolean
      text?: string
    }
    tooltip?: {
      enabled?: boolean
      callbacks?: Record<string, (...args: unknown[]) => unknown>
    }
  }
  scales?: Record<string, Record<string, unknown>>
}

// 錯誤類型
export interface ChartAnalysisError {
  type: 'fetch' | 'render' | 'validation'
  message: string
  details?: Record<string, unknown>
  timestamp: string
}