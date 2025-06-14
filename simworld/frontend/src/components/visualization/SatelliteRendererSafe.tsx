import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { useGLTF, Text, Line } from '@react-three/drei'
import * as THREE from 'three'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { SATELLITE_CONFIG, SIMULATION_MODE, getTimeMultiplier } from '../../config/satellite.config'
import { ApiRoutes } from '../../config/apiRoutes'

interface SatelliteRendererProps {
    satellites: VisibleSatelliteInfo[]
    enabled: boolean
    simulationMode?: string
    showOrbits?: boolean
    showLabels?: boolean
    onSatelliteSelect?: (satellite: VisibleSatelliteInfo) => void
    selectedSatelliteId?: string
    currentConnection?: any
    predictedConnection?: any
}

interface SatellitePosition {
    id: string
    position: [number, number, number]
    velocity: [number, number, number]
    lastUpdate: number
}

const SATELLITE_MODEL_URL = ApiRoutes.simulations.getModel('sat')

// SafeSatelliteModel: A simple component that handles GLB loading like StaticModel
const SafeSatelliteModel: React.FC<{
    position: [number, number, number]
    scale: [number, number, number]
    color: string
    emissive: string
    emissiveIntensity: number
}> = ({ position, scale, color, emissive, emissiveIntensity }) => {
    const { scene } = useGLTF(SATELLITE_MODEL_URL) as any
    
    const clonedScene = useMemo(() => {
        const clone = scene.clone(true)
        clone.traverse((node: THREE.Object3D) => {
            if ((node as THREE.Mesh).isMesh) {
                const mesh = node as THREE.Mesh
                if (mesh.material) {
                    if (Array.isArray(mesh.material)) {
                        mesh.material = mesh.material.map((mat) => {
                            const clonedMat = mat.clone()
                            // Apply color modifications safely
                            if ('color' in clonedMat) {
                                (clonedMat as any).color = new THREE.Color(color)
                            }
                            if ('emissive' in clonedMat) {
                                (clonedMat as any).emissive = new THREE.Color(emissive)
                            }
                            if ('emissiveIntensity' in clonedMat) {
                                (clonedMat as any).emissiveIntensity = emissiveIntensity
                            }
                            return clonedMat
                        })
                    } else {
                        const clonedMat = mesh.material.clone()
                        // Apply color modifications safely
                        if ('color' in clonedMat) {
                            (clonedMat as any).color = new THREE.Color(color)
                        }
                        if ('emissive' in clonedMat) {
                            (clonedMat as any).emissive = new THREE.Color(emissive)
                        }
                        if ('emissiveIntensity' in clonedMat) {
                            (clonedMat as any).emissiveIntensity = emissiveIntensity
                        }
                        mesh.material = clonedMat
                    }
                }
            }
        })
        return clone
    }, [scene, color, emissive, emissiveIntensity])
    
    return (
        <group position={position} scale={scale}>
            <primitive
                object={clonedScene}
                onUpdate={(self: THREE.Object3D) =>
                    self.traverse((child: THREE.Object3D) => {
                        if ((child as THREE.Mesh).isMesh) {
                            child.castShadow = true
                            child.receiveShadow = true
                        }
                    })
                }
            />
        </group>
    )
}

const SatelliteRendererSafe: React.FC<SatelliteRendererProps> = ({
    satellites,
    enabled,
    simulationMode = SIMULATION_MODE.DEMO,
    showOrbits = true,
    showLabels = true,
    onSatelliteSelect,
    selectedSatelliteId,
    currentConnection,
    predictedConnection
}) => {
    const [satellitePositions, setSatellitePositions] = useState<{ [id: string]: SatellitePosition }>({})
    const [currentTime, setCurrentTime] = useState(Date.now())
    const satelliteRefs = useRef<{ [id: string]: THREE.Group }>({})
    
    // 計算時間倍數
    const timeMultiplier = getTimeMultiplier(simulationMode as any)
    
    // 初始化衛星位置
    useEffect(() => {
        if (!enabled || satellites.length === 0) {
            setSatellitePositions({})
            return
        }
        
        const initialPositions: { [id: string]: SatellitePosition } = {}
        
        satellites.forEach(satellite => {
            const position = calculateSatellitePosition(satellite)
            const velocity = calculateOrbitalVelocity(satellite)
            
            initialPositions[satellite.norad_id] = {
                id: satellite.norad_id,
                position,
                velocity,
                lastUpdate: Date.now()
            }
        })
        
        setSatellitePositions(initialPositions)
    }, [satellites, enabled])
    
    // 更新衛星軌道位置
    useFrame((_, delta) => {
        if (!enabled || timeMultiplier === 0) return
        
        const now = Date.now()
        setCurrentTime(now)
        
        setSatellitePositions(prev => {
            const updated = { ...prev }
            
            Object.keys(updated).forEach(id => {
                const satellite = updated[id]
                const deltaTime = delta * timeMultiplier
                
                // 更新位置（簡化的軌道運動）
                const newPosition: [number, number, number] = [
                    satellite.position[0] + satellite.velocity[0] * deltaTime,
                    satellite.position[1] + satellite.velocity[1] * deltaTime,
                    satellite.position[2] + satellite.velocity[2] * deltaTime
                ]
                
                // 檢查是否需要軌道修正（保持軌道高度）
                const distance = Math.sqrt(
                    newPosition[0] ** 2 + 
                    newPosition[1] ** 2 + 
                    newPosition[2] ** 2
                )
                
                const targetDistance = SATELLITE_CONFIG.ONEWEB_ALTITUDE_KM / 10 // 縮放比例
                if (Math.abs(distance - targetDistance) > targetDistance * 0.1) {
                    // 重新計算正確的軌道位置
                    const satelliteData = satellites.find(s => s.norad_id === id)
                    if (satelliteData) {
                        const correctedPosition = calculateSatellitePosition(satelliteData, now)
                        const correctedVelocity = calculateOrbitalVelocity(satelliteData)
                        
                        updated[id] = {
                            ...satellite,
                            position: correctedPosition,
                            velocity: correctedVelocity,
                            lastUpdate: now
                        }
                    }
                } else {
                    updated[id] = {
                        ...satellite,
                        position: newPosition,
                        lastUpdate: now
                    }
                }
            })
            
            return updated
        })
    })
    
    const satelliteMeshes = useMemo(() => {
        if (!enabled) return null
        
        return Object.entries(satellitePositions).map(([id, satPos]) => {
            const satelliteData = satellites.find(s => s.norad_id === id)
            if (!satelliteData) return null
            
            const isSelected = selectedSatelliteId === id
            const isCurrent = currentConnection?.satelliteId === id
            const isPredicted = predictedConnection?.satelliteId === id
            
            let color = '#ffffff'
            let emissive = '#000000'
            let emissiveIntensity = 0
            
            if (isCurrent) {
                color = '#00ff00'
                emissive = '#004400'
                emissiveIntensity = 0.3
            } else if (isPredicted) {
                color = '#ffaa00'
                emissive = '#442200'
                emissiveIntensity = 0.2
            } else if (isSelected) {
                color = '#0088ff'
                emissive = '#002244'
                emissiveIntensity = 0.1
            }
            
            return (
                <group
                    key={id}
                    ref={(ref) => { if (ref) satelliteRefs.current[id] = ref }}
                    position={satPos.position}
                    onClick={() => onSatelliteSelect?.(satelliteData)}
                >
                    {/* 衛星模型 - 使用 StaticModel 方式 */}
                    <SafeSatelliteModel
                        position={[0, 0, 0]}
                        scale={[SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE, SATELLITE_CONFIG.SAT_SCALE]}
                        color={color}
                        emissive={emissive}
                        emissiveIntensity={emissiveIntensity}
                    />
                    
                    {/* 狀態指示器 */}
                    <mesh position={[0, 15, 0]}>
                        <sphereGeometry args={[3, 8, 8]} />
                        <meshBasicMaterial
                            color={color}
                            emissive={emissive}
                            emissiveIntensity={emissiveIntensity}
                            transparent
                            opacity={0.8}
                        />
                    </mesh>
                    
                    {/* 衛星標籤 */}
                    {showLabels && (
                        <Text
                            position={[0, 25, 0]}
                            fontSize={4}
                            color={color}
                            anchorX="center"
                            anchorY="middle"
                        >
                            {satelliteData.name}
                        </Text>
                    )}
                    
                    {/* 仰角資訊 */}
                    {(isSelected || isCurrent || isPredicted) && (
                        <Text
                            position={[0, 20, 0]}
                            fontSize={3}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                        >
                            {satelliteData.elevation_deg.toFixed(1)}°
                        </Text>
                    )}
                    
                    {/* 連接線（連接到地面或UAV） */}
                    {(isCurrent || isPredicted) && (
                        <Line
                            points={[satPos.position, [0, 0, 0]]}
                            color={isCurrent ? '#00ff00' : '#ffaa00'}
                            lineWidth={2}
                            transparent
                            opacity={0.6}
                            dashed={isPredicted}
                        />
                    )}
                </group>
            )
        }).filter(Boolean)
    }, [
        satellitePositions, 
        satellites, 
        enabled, 
        selectedSatelliteId, 
        currentConnection, 
        predictedConnection,
        showLabels,
        onSatelliteSelect
    ])
    
    // 軌道軌跡
    const orbitTrails = useMemo(() => {
        if (!enabled || !showOrbits) return null
        
        return Object.entries(satellitePositions).map(([id, satPos]) => {
            const satelliteData = satellites.find(s => s.norad_id === id)
            if (!satelliteData) return null
            
            // 生成軌道軌跡點
            const orbitPoints = generateOrbitTrail(satelliteData, currentTime)
            
            return (
                <Line
                    key={`orbit_${id}`}
                    points={orbitPoints}
                    color="#4488ff"
                    lineWidth={1}
                    transparent
                    opacity={0.3}
                />
            )
        }).filter(Boolean)
    }, [satellitePositions, satellites, enabled, showOrbits, currentTime])
    
    if (!enabled) {
        return null
    }
    
    return (
        <group>
            {satelliteMeshes}
            {orbitTrails}
        </group>
    )
}

// 計算衛星在3D場景中的位置
function calculateSatellitePosition(
    satellite: VisibleSatelliteInfo, 
    currentTime?: number
): [number, number, number] {
    const PI_DIV_180 = Math.PI / 180
    const GLB_SCENE_SIZE = 1200
    const MIN_SAT_HEIGHT = 200
    const MAX_SAT_HEIGHT = 400
    
    // 添加時間偏移來模擬軌道運動
    let elevationDeg = satellite.elevation_deg
    let azimuthDeg = satellite.azimuth_deg
    
    if (currentTime) {
        const timeOffset = (currentTime / 1000) * 0.1 // 緩慢的軌道運動
        azimuthDeg += timeOffset
        elevationDeg += Math.sin(timeOffset * 0.1) * 2 // 小幅度的仰角變化
    }
    
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

// 計算軌道速度向量
function calculateOrbitalVelocity(satellite: VisibleSatelliteInfo): [number, number, number] {
    const PI_DIV_180 = Math.PI / 180
    const orbitalSpeed = 0.5 // 調整軌道速度
    
    // 基於軌道方向計算速度向量
    const azimuthRad = (satellite.azimuth_deg + 90) * PI_DIV_180 // 垂直於徑向
    const elevationRad = satellite.elevation_deg * PI_DIV_180
    
    const vx = orbitalSpeed * Math.cos(azimuthRad) * Math.cos(elevationRad)
    const vy = orbitalSpeed * Math.sin(elevationRad) * 0.1 // 高度變化較小
    const vz = orbitalSpeed * Math.sin(azimuthRad) * Math.cos(elevationRad)
    
    return [vx, vy, vz]
}

// 生成軌道軌跡
function generateOrbitTrail(
    satellite: VisibleSatelliteInfo, 
    currentTime: number
): [number, number, number][] {
    const points: [number, number, number][] = []
    const trailDuration = SATELLITE_CONFIG.TRAIL_LENGTH * 60 * 1000 // 轉換為毫秒
    const pointCount = 32
    
    for (let i = 0; i < pointCount; i++) {
        const timeOffset = (i / pointCount) * trailDuration
        const pastTime = currentTime - timeOffset
        const position = calculateSatellitePosition(satellite, pastTime)
        points.push(position)
    }
    
    return points
}

export default SatelliteRendererSafe