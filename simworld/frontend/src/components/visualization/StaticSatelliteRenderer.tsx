import React, { useMemo } from 'react'
import { Text } from '@react-three/drei'
import StaticModel from '../scenes/StaticModel'
import { ApiRoutes } from '../../config/apiRoutes'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { SATELLITE_CONFIG } from '../../config/satellite.config'

interface StaticSatelliteRendererProps {
    satellites: VisibleSatelliteInfo[]
    enabled: boolean
    currentConnection?: any
    predictedConnection?: any
    showLabels?: boolean
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

const StaticSatelliteRenderer: React.FC<StaticSatelliteRendererProps> = ({
    satellites,
    enabled,
    currentConnection,
    predictedConnection,
    showLabels = true
}) => {
    // 完全參考 MainScene 中 deviceMeshes 的邏輯
    const satelliteMeshes = useMemo(() => {
        if (!enabled || !satellites || satellites.length === 0) {
            return []
        }

        return satellites.map((satellite: VisibleSatelliteInfo, index: number) => {
            const isCurrent = currentConnection?.satelliteId === satellite.norad_id
            const isPredicted = predictedConnection?.satelliteId === satellite.norad_id
            
            // 計算衛星位置 - 與DynamicSatelliteRenderer保持一致
            const PI_DIV_180 = Math.PI / 180
            const GLB_SCENE_SIZE = 1200
            const MIN_SAT_HEIGHT = 200
            const MAX_SAT_HEIGHT = 600
            
            const elevationRad = satellite.elevation_deg * PI_DIV_180
            const azimuthRad = satellite.azimuth_deg * PI_DIV_180
            
            const range = GLB_SCENE_SIZE * 0.4
            const horizontalDist = range * Math.cos(elevationRad)
            
            const x = horizontalDist * Math.sin(azimuthRad)
            const z = horizontalDist * Math.cos(azimuthRad)  // 修正：z軸不是y軸
            const y = MIN_SAT_HEIGHT + (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.sin(elevationRad)

            const position: [number, number, number] = [x, y, z]  // 修正：[x, 高度, z]
            
            let statusColor = '#ffffff'
            if (isCurrent) {
                statusColor = '#00ff00'
            } else if (isPredicted) {
                statusColor = '#ffaa00'
            }

            return (
                <group key={satellite.norad_id || `sat-${index}`}>
                    {/* 衛星模型 - 完全參考 tower/jammer 的做法 */}
                    <StaticModel
                        url={SATELLITE_MODEL_URL}
                        position={position}
                        scale={[SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE]}
                        pivotOffset={[0, 0, 0]}
                    />
                    
                    {/* 狀態指示器 */}
                    <mesh position={[position[0], position[1] + 15, position[2]]}>
                        <sphereGeometry args={[3, 8, 8]} />
                        <meshBasicMaterial
                            color={statusColor}
                            transparent
                            opacity={0.8}
                        />
                    </mesh>
                    
                    {/* 衛星標籤 */}
                    {showLabels && (
                        <Text
                            position={[position[0], position[1] + 25, position[2]]}
                            fontSize={4}
                            color={statusColor}
                            anchorX="center"
                            anchorY="middle"
                        >
                            {satellite.name}
                        </Text>
                    )}
                    
                    {/* 仰角資訊 */}
                    {(isCurrent || isPredicted) && (
                        <Text
                            position={[position[0], position[1] + 20, position[2]]}
                            fontSize={3}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            {satellite.elevation_deg.toFixed(1)}°
                        </Text>
                    )}
                </group>
            )
        })
    }, [
        satellites,
        enabled,
        currentConnection,
        predictedConnection,
        showLabels
    ])

    if (!enabled) {
        return null
    }

    return <group>{satelliteMeshes}</group>
}

export default StaticSatelliteRenderer