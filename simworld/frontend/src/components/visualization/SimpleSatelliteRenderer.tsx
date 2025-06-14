import React, { useState, useEffect, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import * as THREE from 'three'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { SATELLITE_CONFIG } from '../../config/satellite.config'

interface SimpleSatelliteRendererProps {
    satellites: VisibleSatelliteInfo[]
    enabled: boolean
    currentConnection?: any
    predictedConnection?: any
}

const SimpleSatelliteRenderer: React.FC<SimpleSatelliteRendererProps> = ({
    satellites,
    enabled,
    currentConnection,
    predictedConnection
}) => {
    const [time, setTime] = useState(0)
    
    useFrame((_, delta) => {
        setTime(t => t + delta)
    })
    
    const satelliteElements = useMemo(() => {
        if (!enabled || satellites.length === 0) return null
        
        return satellites.map((satellite, index) => {
            const position = calculateSatellitePosition(satellite, time)
            const isCurrent = currentConnection?.satelliteId === satellite.norad_id
            const isPredicted = predictedConnection?.satelliteId === satellite.norad_id
            
            let color = '#cccccc'
            if (isCurrent) color = '#00ff00'
            else if (isPredicted) color = '#ffaa00'
            
            return (
                <group key={satellite.norad_id} position={position}>
                    {/* 簡單的衛星形狀 */}
                    <mesh>
                        <boxGeometry args={[6, 3, 4]} />
                        <meshStandardMaterial color={color} />
                    </mesh>
                    
                    {/* 太陽能板 */}
                    <mesh position={[-4, 0, 0]}>
                        <boxGeometry args={[0.3, 8, 6]} />
                        <meshStandardMaterial color="#1a1a3a" />
                    </mesh>
                    <mesh position={[4, 0, 0]}>
                        <boxGeometry args={[0.3, 8, 6]} />
                        <meshStandardMaterial color="#1a1a3a" />
                    </mesh>
                    
                    {/* 衛星名稱 */}
                    <Text
                        position={[0, 8, 0]}
                        fontSize={3}
                        color={color}
                        anchorX="center"
                        anchorY="middle"
                    >
                        {satellite.name}
                    </Text>
                    
                    {/* 仰角資訊 */}
                    <Text
                        position={[0, 5, 0]}
                        fontSize={2}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        {satellite.elevation_deg.toFixed(1)}°
                    </Text>
                </group>
            )
        })
    }, [satellites, enabled, time, currentConnection, predictedConnection])
    
    if (!enabled) {
        console.log('SimpleSatelliteRenderer: disabled')
        return null
    }
    
    console.log('SimpleSatelliteRenderer: rendering', satellites.length, 'satellites')
    
    return <group>{satelliteElements}</group>
}

// 計算衛星位置
function calculateSatellitePosition(
    satellite: VisibleSatelliteInfo, 
    time: number
): [number, number, number] {
    const PI_DIV_180 = Math.PI / 180
    const GLB_SCENE_SIZE = 1200
    const MIN_SAT_HEIGHT = 200
    const MAX_SAT_HEIGHT = 400
    
    // 添加時間偏移來模擬軌道運動
    const timeOffset = time * 0.1 // 緩慢的軌道運動
    const elevationDeg = satellite.elevation_deg + Math.sin(timeOffset * 0.1) * 2
    const azimuthDeg = satellite.azimuth_deg + timeOffset
    
    const elevationRad = elevationDeg * PI_DIV_180
    const azimuthRad = azimuthDeg * PI_DIV_180
    
    const range = GLB_SCENE_SIZE * 0.45
    const horizontalDist = range * Math.cos(elevationRad)
    
    const x = horizontalDist * Math.sin(azimuthRad)
    const y = horizontalDist * Math.cos(azimuthRad)
    const height = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * 
                   Math.pow(Math.sin(elevationRad), 0.8)
    
    return [x, height, y]
}

export default SimpleSatelliteRenderer