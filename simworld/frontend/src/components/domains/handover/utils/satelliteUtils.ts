/**
 * 衛星數據處理工具函數
 * 統一衛星數據格式化、轉換和驗證邏輯
 */

import { VisibleSatelliteInfo } from '../../../../types/satellite'
import { SatelliteConnection } from '../../../../types/handover'
import { HANDOVER_CONFIG } from '../config/handoverConfig'

/**
 * 標準化衛星數據格式
 */
export const normalizeSatelliteData = (satellite: Record<string, unknown>): VisibleSatelliteInfo => {
  return {
    ...satellite,
    norad_id: typeof satellite.norad_id === 'string' 
      ? parseInt(satellite.norad_id) 
      : satellite.norad_id,
    name: (satellite.name as string)
      ?.replace(' [DTC]', '')
      ?.replace('[DTC]', '') || '',
  } as VisibleSatelliteInfo
}

/**
 * 批量標準化衛星數據
 */
export const normalizeSatelliteArray = (satellites: Record<string, unknown>[]): VisibleSatelliteInfo[] => {
  return satellites.map(normalizeSatelliteData)
}

/**
 * 生成模擬衛星連接對象
 */
export const generateMockSatelliteConnection = (
  satellite: VisibleSatelliteInfo,
  isConnected: boolean = false
): SatelliteConnection => {
  return {
    satelliteId: satellite.norad_id.toString(),
    satelliteName: satellite.name,
    elevation: satellite.elevation_deg,
    azimuth: satellite.azimuth_deg,
    distance: satellite.distance_km,
    signalStrength: HANDOVER_CONFIG.SIGNAL_QUALITY.SIGNAL_RANGE.MAX - 
                   Math.random() * (HANDOVER_CONFIG.SIGNAL_QUALITY.SIGNAL_RANGE.MAX - HANDOVER_CONFIG.SIGNAL_QUALITY.SIGNAL_RANGE.MIN),
    isConnected,
    isPredicted: !isConnected,
  }
}

/**
 * 生成模擬衛星數據（用於開發測試）
 */
export const generateMockSatellites = (count: number = HANDOVER_CONFIG.API.FALLBACK_SATELLITES_COUNT): VisibleSatelliteInfo[] => {
  return Array.from({ length: count }, (_, i) => ({
    norad_id: 1000 + i,
    name: `STARLINK-${1000 + i}`,
    elevation_deg: 30 + Math.random() * 60,
    azimuth_deg: Math.random() * 360,
    distance_km: 500 + Math.random() * 500,
    line1: `1 ${1000 + i}U 20001001.00000000  .00000000  00000-0  00000-0 0  9999`,
    line2: `2 ${1000 + i}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000`,
  }))
}

/**
 * 獲取衛星仰角（統一處理不同的數據格式）
 */
export const getSatelliteElevation = (satellite: VisibleSatelliteInfo): number => {
  return satellite.elevation_deg || 0
}

/**
 * 獲取衛星方位角
 */
export const getSatelliteAzimuth = (satellite: VisibleSatelliteInfo): number => {
  return satellite.azimuth_deg || 0
}

/**
 * 獲取衛星距離
 */
export const getSatelliteDistance = (satellite: VisibleSatelliteInfo): number => {
  return satellite.distance_km || 0
}

/**
 * 驗證衛星數據完整性
 */
export const validateSatelliteData = (satellite: Record<string, unknown>): boolean => {
  return !!(
    satellite &&
    satellite.norad_id &&
    satellite.name &&
    (satellite.elevation_deg !== undefined || (satellite.position as Record<string, unknown>)?.elevation !== undefined)
  )
}

/**
 * 過濾有效的衛星數據
 */
export const filterValidSatellites = (satellites: Record<string, unknown>[]): VisibleSatelliteInfo[] => {
  return satellites
    .filter(validateSatelliteData)
    .map(normalizeSatelliteData)
}

/**
 * 根據ID查找衛星
 */
export const findSatelliteById = (satellites: VisibleSatelliteInfo[], id: string | number): VisibleSatelliteInfo | undefined => {
  const targetId = typeof id === 'string' ? parseInt(id) : id
  return satellites.find(sat => sat.norad_id === targetId)
}

/**
 * 按信號品質排序衛星
 */
export const sortSatellitesByQuality = (satellites: VisibleSatelliteInfo[]): VisibleSatelliteInfo[] => {
  return [...satellites].sort((a, b) => {
    const elevationA = getSatelliteElevation(a)
    const elevationB = getSatelliteElevation(b)
    return elevationB - elevationA // 仰角越高，品質越好
  })
}

/**
 * 格式化衛星顯示信息
 */
export const formatSatelliteDisplayInfo = (satellite: VisibleSatelliteInfo) => {
  return {
    id: satellite.norad_id.toString(),
    name: satellite.name,
    elevation: `${getSatelliteElevation(satellite).toFixed(1)}°`,
    azimuth: `${getSatelliteAzimuth(satellite).toFixed(1)}°`,
    distance: `${getSatelliteDistance(satellite).toFixed(0)} km`,
  }
}