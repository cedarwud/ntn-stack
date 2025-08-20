/**
 * 衛星數據橋樑組件
 * 負責將 SatelliteDataContext 的數據同步到 AppStateContext
 * 解決衛星不顯示的問題
 */

import React, { useEffect } from 'react'
import { useSatelliteData } from '../contexts/SatelliteDataContext'
import { useAppState } from '../contexts/appStateHooks'
import { UnifiedSatelliteInfo } from '../services/satelliteDataService'
import { VisibleSatelliteInfo, StandardSatelliteData } from '../types/satellite'

/**
 * 將 UnifiedSatelliteInfo 轉換為 StandardSatelliteData (DynamicSatelliteRenderer期望的格式)
 */
const convertToStandardSatelliteData = (satellites: UnifiedSatelliteInfo[]): StandardSatelliteData[] => {
    return satellites.map(sat => ({
        id: sat.id,
        norad_id: sat.norad_id,
        name: sat.name,
        constellation: sat.constellation,
        elevation_deg: sat.elevation_deg,
        azimuth_deg: sat.azimuth_deg,
        distance_km: sat.distance_km,
        is_visible: sat.is_visible,
        position_timeseries: sat.position_timeseries?.map(point => ({
            time: point.time,
            time_offset_seconds: point.time_offset_seconds,
            elevation_deg: point.elevation_deg,
            azimuth_deg: point.azimuth_deg,
            range_km: point.range_km,
            is_visible: point.is_visible
        })) || [],
        signal_quality: {
            rsrp: sat.signal_quality?.rsrp || -85,
            rsrq: sat.signal_quality?.rsrq || -10,
            sinr: sat.signal_quality?.sinr || 15,
            estimated_signal_strength: sat.signal_quality?.estimated_signal_strength || sat.signal_strength || -85
        },
        position: sat.position || {
            latitude: sat.position?.latitude || 0,
            longitude: sat.position?.longitude || 0,
            altitude: sat.position?.altitude || 550000, // 默認LEO高度
            velocity: sat.position?.velocity || 7500,
            doppler_shift: sat.position?.doppler_shift || 0
        },
        last_updated: sat.last_updated,
        data_source: 'real_time' as const
    }))
}

/**
 * 為了向後兼容，同時轉換為 VisibleSatelliteInfo
 */
const convertToVisibleSatelliteInfo = (satellites: StandardSatelliteData[]): VisibleSatelliteInfo[] => {
    return satellites.map(sat => ({
        norad_id: parseInt(sat.norad_id) || 0,
        name: sat.name,
        elevation_deg: sat.elevation_deg,
        azimuth_deg: sat.azimuth_deg,
        distance_km: sat.distance_km,
        line1: '', // TLE數據，暫時留空
        line2: '', // TLE數據，暫時留空
        constellation: sat.constellation,
        // 🚀 擴展字段：添加完整的衛星數據
        ...sat
    } as any)) // 使用any暫時繞過類型檢查
}

/**
 * 衛星數據橋樑組件
 * 將 SatelliteDataContext 的衛星數據同步到 AppStateContext
 */
const SatelliteDataBridge: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { state: satelliteData, setConstellation } = useSatelliteData()
    const { setSkyfieldSatellites, setSelectedConstellation, satelliteState } = useAppState()
    
    // 🔄 同步衛星數據到 AppStateContext
    useEffect(() => {
        if (satelliteData.satellites && satelliteData.satellites.length > 0) {
            // 首先轉換為標準格式
            const standardSatellites = convertToStandardSatelliteData(satelliteData.satellites)
            // 然後轉換為AppState期望的格式
            const convertedSatellites = convertToVisibleSatelliteInfo(standardSatellites)
            
            setSkyfieldSatellites(convertedSatellites)
        } else if (satelliteData.error) {
            console.error('❌ 衛星數據獲取失敗:', satelliteData.error)
            setSkyfieldSatellites([])
        }
    }, [satelliteData.satellites, satelliteData.error, satelliteData.loading, setSkyfieldSatellites])
    
    // 🔄 同步星座選擇狀態
    useEffect(() => {
        if (satelliteState.selectedConstellation !== satelliteData.selectedConstellation) {
            setSelectedConstellation(satelliteData.selectedConstellation)
        }
    }, [satelliteData.selectedConstellation, satelliteState.selectedConstellation, setSelectedConstellation])
    
    // 🔄 反向同步：AppState 星座變更到 SatelliteDataContext
    useEffect(() => {
        if (satelliteState.selectedConstellation !== satelliteData.selectedConstellation) {
            setConstellation(satelliteState.selectedConstellation)
        }
    }, [satelliteState.selectedConstellation, satelliteData.selectedConstellation, setConstellation])
    
    return <>{children}</>
}

export default SatelliteDataBridge