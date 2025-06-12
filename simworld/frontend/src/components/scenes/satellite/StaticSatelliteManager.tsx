import React, { useMemo } from 'react'
import { useGLTF } from '@react-three/drei'
import SimplifiedSatellite from './SimplifiedSatellite'
import { satellitePassTemplates } from '../../../utils/satellite/satellitePassTemplates'
import { SAT_MODEL_URL } from '../../../utils/satellite/satelliteConstants'

// 真實的 Starlink 衛星配置：基於實際軌道參數，覆蓋各種仰角
const STATIC_SATELLITES = [
    // 高仰角衛星（換手目標）
    { norad_id: 45417, name: 'STARLINK-1318', elevation_deg: 75, azimuth_deg: 45, distance_km: 550, max_elevation_deg: 85 },
    { norad_id: 46045, name: 'STARLINK-1297', elevation_deg: 68, azimuth_deg: 120, distance_km: 580, max_elevation_deg: 78 },
    { norad_id: 46059, name: 'STARLINK-1326', elevation_deg: 72, azimuth_deg: 200, distance_km: 560, max_elevation_deg: 80 },
    
    // 中等仰角衛星
    { norad_id: 44720, name: 'STARLINK-1089', elevation_deg: 45, azimuth_deg: 90, distance_km: 650, max_elevation_deg: 55 },
    { norad_id: 45074, name: 'STARLINK-1245', elevation_deg: 52, azimuth_deg: 180, distance_km: 620, max_elevation_deg: 62 },
    { norad_id: 45395, name: 'STARLINK-1432', elevation_deg: 38, azimuth_deg: 270, distance_km: 680, max_elevation_deg: 48 },
    
    // 低仰角衛星（即將升起或落下）
    { norad_id: 45778, name: 'STARLINK-1567', elevation_deg: 25, azimuth_deg: 30, distance_km: 750, max_elevation_deg: 65 },
    { norad_id: 46060, name: 'STARLINK-1612', elevation_deg: 18, azimuth_deg: 300, distance_km: 800, max_elevation_deg: 70 },
    { norad_id: 45416, name: 'STARLINK-1401', elevation_deg: 32, azimuth_deg: 150, distance_km: 720, max_elevation_deg: 58 },
    { norad_id: 45057, name: 'STARLINK-1234', elevation_deg: 28, azimuth_deg: 240, distance_km: 780, max_elevation_deg: 62 },
].map((sat, index) => ({
    ...sat,
    velocity_ms: 7800,
    visible: true,
    pass_start_time: new Date().toISOString(),
    pass_end_time: new Date(Date.now() + 600000).toISOString(), // 10分鐘後
}))

interface StaticSatelliteManagerProps {
    enabled: boolean
}

// 預加載衛星模型
useGLTF.preload(SAT_MODEL_URL)

const StaticSatelliteManager: React.FC<StaticSatelliteManagerProps> = ({ enabled }) => {
    // 靜態衛星：永不重新渲染，只創建一次
    const staticSatellites = useMemo(() => {
        if (!enabled) return []
        
        return STATIC_SATELLITES.map((satellite, index) => {
            const passTemplate = satellitePassTemplates[index % satellitePassTemplates.length]
            
            return (
                <SimplifiedSatellite
                    key={`static-satellite-${satellite.norad_id}`} // 永久穩定的key
                    satellite={satellite}
                    index={index}
                    passTemplate={passTemplate}
                />
            )
        })
    }, [enabled]) // 只依賴enabled狀態

    console.log(`🛰️ StaticSatelliteManager: 渲染 ${staticSatellites.length} 個靜態衛星 (enabled: ${enabled})`)

    return <>{staticSatellites}</>
}

export default StaticSatelliteManager