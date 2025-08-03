/**
 * 測量事件 API 配置
 * 統一管理測量事件相關的 API 調用
 */

import { netstackFetch } from './api-config'

// 類型定義
export interface Position {
    latitude: number
    longitude: number
    altitude?: number
}

export interface EventParameters {
    event_type: 'A4' | 'D1' | 'D2' | 'T1'
    time_to_trigger?: number
}

export interface A4Parameters extends EventParameters {
    event_type: 'A4'
    a4_threshold: number      // dBm
    hysteresis: number        // dB
}

export interface D1Parameters extends EventParameters {
    event_type: 'D1'
    thresh1: number          // meters
    thresh2: number          // meters
    hysteresis: number       // meters
}

export interface D2Parameters extends EventParameters {
    event_type: 'D2'
    thresh1: number          // meters - satellite distance
    thresh2: number          // meters - ground distance
    hysteresis: number       // meters
}

export interface T1Parameters extends EventParameters {
    event_type: 'T1'
    t1_threshold: number     // seconds
    duration: number         // seconds
}

export interface MeasurementResult {
    event_type: string
    timestamp: string
    trigger_state: 'idle' | 'approaching' | 'triggered' | 'hysteresis'
    trigger_condition_met: boolean
    measurement_values: Record<string, number>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    trigger_details: Record<string, any>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    sib19_data?: Record<string, any>
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    satellite_positions?: Record<string, any>
}

export interface SimulationScenario {
    scenario_name: string
    ue_position: Position
    duration_minutes: number
    sample_interval_seconds: number
    target_satellites?: string[]
}

export interface SIB19Status {
    status: string
    broadcast_id: string
    broadcast_time: string
    validity_hours: number
    time_to_expiry_hours: number
    satellites_count: number
    neighbor_cells_count: number
    time_sync_accuracy_ms: number
    reference_location?: {
        type: string
        latitude: number
        longitude: number
    }
}

export interface SatelliteInfo {
    satellite_id: string
    satellite_name: string
    epoch: string
    last_updated: string
}

export interface ConstellationInfo {
    satellite_count: number
    active_satellites: number
    operator: string
    coverage_area: string
    last_updated: string
}

export interface SatellitePosition {
    satellite_id: string
    timestamp: string
    position: {
        x: number
        y: number
        z: number
        latitude: number
        longitude: number
        altitude: number
    }
    velocity: {
        x: number
        y: number
        z: number
    }
    orbital_period_minutes: number
}

// API 函數

/**
 * 獲取實時測量數據
 */
export async function getRealTimeMeasurementData(
    eventType: 'A4' | 'D1' | 'D2' | 'T1',
    uePosition: Position,
    eventParams: A4Parameters | D1Parameters | D2Parameters | T1Parameters
): Promise<MeasurementResult> {
    const requestBody = {
        ue_position: uePosition,
        [`${eventType.toLowerCase()}_params`]: eventParams
    }

    const response = await netstackFetch(`/api/measurement-events/${eventType}/data`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })

    if (!response.ok) {
        throw new Error(`測量數據獲取失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 模擬測量事件
 */
export async function simulateMeasurementEvent(
    eventType: 'A4' | 'D1' | 'D2' | 'T1',
    scenario: SimulationScenario
// eslint-disable-next-line @typescript-eslint/no-explicit-any
): Promise<any> {
    const response = await netstackFetch(`/api/measurement-events/${eventType}/simulate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(scenario)
    })

    if (!response.ok) {
        throw new Error(`模擬事件失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 獲取事件參數配置
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function getEventParametersConfig(): Promise<Record<string, any>> {
    const response = await netstackFetch('/api/measurement-events/config/parameters')

    if (!response.ok) {
        throw new Error(`參數配置獲取失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 獲取 SIB19 狀態
 */
export async function getSIB19Status(): Promise<SIB19Status> {
    const response = await netstackFetch('/api/measurement-events/sib19-status')

    if (!response.ok) {
        throw new Error(`SIB19 狀態獲取失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 獲取可用衛星列表
 */
export async function getAvailableSatellites(constellation?: string): Promise<{
    satellites: SatelliteInfo[]
    total_count: number
    constellation_filter?: string
    constellation_info: Record<string, ConstellationInfo>
}> {
    const url = constellation 
        ? `/api/measurement-events/orbit-data/satellites?constellation=${constellation}`
        : '/api/measurement-events/orbit-data/satellites'

    const response = await netstackFetch(url)

    if (!response.ok) {
        throw new Error(`衛星列表獲取失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 獲取衛星位置
 */
export async function getSatellitePosition(
    satelliteId: string,
    timestamp?: number
): Promise<SatellitePosition> {
    const url = timestamp 
        ? `/api/measurement-events/orbit-data/position/${satelliteId}?timestamp=${timestamp}`
        : `/api/measurement-events/orbit-data/position/${satelliteId}`

    const response = await netstackFetch(url)

    if (!response.ok) {
        throw new Error(`衛星位置獲取失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 強制更新 TLE 數據
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function forceUpdateTLEData(): Promise<any> {
    const response = await netstackFetch('/api/measurement-events/orbit-data/update-tle', {
        method: 'POST'
    })

    if (!response.ok) {
        throw new Error(`TLE 數據更新失敗: ${response.statusText}`)
    }

    return response.json()
}

/**
 * 健康檢查
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function checkMeasurementServiceHealth(): Promise<any> {
    const response = await netstackFetch('/api/measurement-events/health')

    if (!response.ok) {
        throw new Error(`健康檢查失敗: ${response.statusText}`)
    }

    return response.json()
}

// 默認參數配置
export const DEFAULT_PARAMETERS = {
    A4: {
        event_type: 'A4' as const,
        a4_threshold: -80.0,
        hysteresis: 3.0,
        time_to_trigger: 160
    },
    D1: {
        event_type: 'D1' as const,
        thresh1: 10000.0,
        thresh2: 5000.0,
        hysteresis: 500.0,
        time_to_trigger: 160
    },
    D2: {
        event_type: 'D2' as const,
        thresh1: 800000.0,
        thresh2: 30000.0,
        hysteresis: 500.0,
        time_to_trigger: 160
    },
    T1: {
        event_type: 'T1' as const,
        t1_threshold: 300.0,
        duration: 60.0,
        time_to_trigger: 160
    }
}

// 參數約束
export const PARAMETER_CONSTRAINTS = {
    A4: {
        a4_threshold: { min: -100, max: -40, unit: 'dBm' },
        hysteresis: { min: 0, max: 10, unit: 'dB' },
        time_to_trigger: {
            values: [0, 40, 64, 80, 100, 128, 160, 256, 320, 480, 512, 640],
            unit: 'ms'
        }
    },
    D1: {
        thresh1: { min: 50, max: 50000, unit: 'meters' },
        thresh2: { min: 10, max: 10000, unit: 'meters' },
        hysteresis: { min: 1, max: 1000, unit: 'meters' }
    },
    D2: {
        thresh1: { min: 400000, max: 2000000, unit: 'meters' },
        thresh2: { min: 100, max: 50000, unit: 'meters' },
        hysteresis: { min: 100, max: 5000, unit: 'meters' }
    },
    T1: {
        t1_threshold: { min: 1, max: 3600, unit: 'seconds' },
        duration: { min: 1, max: 300, unit: 'seconds' }
    }
}

// 輔助函數

/**
 * 驗證事件參數
 */
export function validateEventParameters(
    eventType: 'A4' | 'D1' | 'D2' | 'T1',
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    params: any
): { valid: boolean; errors: string[] } {
    const errors: string[] = []
    const constraints = PARAMETER_CONSTRAINTS[eventType]

    for (const [key, constraint] of Object.entries(constraints)) {
        const value = params[key]
        
        if (value === undefined || value === null) {
            errors.push(`參數 ${key} 為必填項`)
            continue
        }

        if ('min' in constraint && 'max' in constraint) {
            if (value < constraint.min || value > constraint.max) {
                errors.push(`參數 ${key} 應在 ${constraint.min} 到 ${constraint.max} ${constraint.unit} 之間`)
            }
        }

        if ('values' in constraint) {
            if (!constraint.values.includes(value)) {
                errors.push(`參數 ${key} 必須是以下值之一: ${constraint.values.join(', ')}`)
            }
        }
    }

    return { valid: errors.length === 0, errors }
}

/**
 * 格式化測量值
 */
export function formatMeasurementValue(key: string, value: number): string {
    const formatters: Record<string, (v: number) => string> = {
        'serving_rsrp': (v) => `${v.toFixed(1)} dBm`,
        'best_neighbor_rsrp': (v) => `${v.toFixed(1)} dBm`,
        'serving_distance': (v) => `${(v/1000).toFixed(2)} km`,
        'ml1_distance': (v) => `${(v/1000).toFixed(2)} km`,
        'ml2_distance': (v) => `${(v/1000).toFixed(2)} km`,
        'satellite_distance': (v) => `${(v/1000).toFixed(2)} km`,
        'ground_distance': (v) => `${(v/1000).toFixed(2)} km`,
        'elapsed_time': (v) => `${v.toFixed(1)} s`,
        'position_compensation': (v) => `${v.toFixed(1)} m`,
        'time_compensation': (v) => `${v.toFixed(2)} ms`
    }

    const formatter = formatters[key]
    return formatter ? formatter(value) : value.toFixed(2)
}

/**
 * 獲取觸發狀態顏色
 */
export function getTriggerStateColor(state: string): string {
    const colors: Record<string, string> = {
        'idle': 'text-gray-500',
        'approaching': 'text-yellow-500', 
        'triggered': 'text-green-500',
        'hysteresis': 'text-blue-500'
    }
    return colors[state] || 'text-gray-500'
}

/**
 * 獲取觸發狀態標籤
 */
export function getTriggerStateLabel(state: string): string {
    const labels: Record<string, string> = {
        'idle': '空閒',
        'approaching': '接近',
        'triggered': '已觸發',
        'hysteresis': '遲滯'
    }
    return labels[state] || state
}