/**
 * 統一衛星數據類型定義
 * 替代多個重複的接口定義，提供一致的數據結構
 */

// 🎯 時間序列數據點 - 從階段六產出獲取的真實SGP4數據
export interface TimeseriesPoint {
    time: string
    time_offset_seconds: number
    elevation_deg: number
    azimuth_deg: number
    range_km: number
    is_visible: boolean
}

// 🛰️ 標準衛星數據結構 - 統一所有衛星相關接口
export interface StandardSatelliteData {
    // 基本識別信息
    id: string
    norad_id: string
    name: string
    constellation: 'starlink' | 'oneweb'
    
    // 當前狀態
    elevation_deg: number
    azimuth_deg: number
    distance_km: number
    is_visible: boolean
    
    // 🎯 核心：真實SGP4軌道時間序列數據
    position_timeseries?: TimeseriesPoint[]
    
    // 信號質量
    signal_quality: {
        rsrp: number
        rsrq: number
        sinr: number
        estimated_signal_strength: number
        path_loss_db?: number
    }
    
    // 位置信息
    position: {
        latitude: number
        longitude: number
        altitude: number
        velocity: number
        doppler_shift: number
    }
    
    // 元數據
    last_updated: string
    data_source: 'real_time' | 'historical' | 'predicted'
}

// 🎮 3D渲染相關數據
export interface SatelliteRenderData {
    id: string
    name: string
    currentPosition: [number, number, number]
    isVisible: boolean
    progress: number
    signalStrength: number
    
    // 視覺狀態
    visualState: {
        color: string
        scale: number
        opacity: number
        isHighlighted: boolean
    }
    
    // 軌道數據
    orbitData: StandardSatelliteData
}

// 🔗 換手相關數據
export interface HandoverState {
    phase: 'stable' | 'preparing' | 'establishing' | 'switching' | 'completing'
    currentSatelliteId: string | null
    targetSatelliteId: string | null
    progress: number
    confidence: number
}

// 🎯 演算法結果
export interface AlgorithmResults {
    currentSatelliteId?: string
    predictedSatelliteId?: string
    handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
    binarySearchActive?: boolean
    predictionConfidence?: number
}

// 📊 服務配置
export interface SatelliteServiceConfig {
    minElevation: number
    maxCount: number
    observerLat: number
    observerLon: number
    constellation: 'starlink' | 'oneweb'
    updateInterval: number
    enableCache: boolean
    cacheTimeout: number
}

// 🎭 組件Props類型
export interface SatelliteRendererProps {
    enabled: boolean
    satellites: StandardSatelliteData[]
    currentConnection?: Record<string, unknown>
    predictedConnection?: Record<string, unknown>
    showLabels?: boolean
    speedMultiplier?: number
    algorithmResults?: AlgorithmResults
    handoverState?: HandoverState
    onSatelliteClick?: (satelliteId: string) => void
    onSatellitePositions?: (positions: Map<string, [number, number, number]>) => void
}

// 🔄 保留現有接口以向後兼容
export interface VisibleSatelliteInfo {
    norad_id: number;
    name: string;
    elevation_deg: number;
    azimuth_deg: number;
    distance_km: number;
    line1: string; // TLE line 1
    line2: string; // TLE line 2
    ecef_x_km?: number | null;
    ecef_y_km?: number | null;
    ecef_z_km?: number | null;
    constellation?: string; // 星座名稱 (STARLINK, ONEWEB, KUIPER 等)
}

export default StandardSatelliteData;