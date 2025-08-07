/**
 * 真實 UE-衛星連接狀態服務
 * 獲取真實的連接狀態和換手決策數據
 */
// import { netStackApi } from './netstack-api' // 暫時未使用

export interface RealConnectionInfo {
    ue_id: string
    satellite_id: number
    current_satellite_id: string
    signal_quality: number // dBm
    connection_duration: number // 秒
    status: 'connected' | 'handover_preparing' | 'handover_executing' | 'disconnected'
    last_update: string
}

export interface RealHandoverStatus {
    ue_id: string
    current_satellite: string
    target_satellite?: string
    satellite_id_current?: number
    satellite_id_target?: number
    handover_status: 'idle' | 'predicting' | 'preparing' | 'executing' | 'completing' | 'completed' | 'failed'
    prediction_confidence?: number
    estimated_handover_time?: string
    handover_reason?: string
    signal_quality_current?: number
    signal_quality_target?: number
}

// 單例實例 (空實現)
export const realConnectionManager = {
    subscribe: () => () => {},
    getLatestData: () => null,
}

// 導出空函數以避免錯誤
export function getConnectionLineColor(_signalQuality: number): string {
    return '#00ff00'
}

export function getConnectionLineOpacity(_signalQuality: number): number {
    return 0.8
}

export function getConnectionLineRadius(_signalQuality: number): number {
    return 0.3
}