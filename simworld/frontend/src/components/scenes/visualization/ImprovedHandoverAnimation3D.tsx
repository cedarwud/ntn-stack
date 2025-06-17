import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface ImprovedHandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellitePositions?: Map<string, [number, number, number]>
}

interface SmoothConnection {
    id: string
    satelliteId: string
    uavIndex: number
    startPosition: [number, number, number]
    endPosition: [number, number, number]
    currentStartPosition: [number, number, number]
    currentEndPosition: [number, number, number]
    opacity: number
    width: number
}

const ImprovedHandoverAnimation3D: React.FC<ImprovedHandoverAnimation3DProps> = ({
    devices,
    enabled,
    satellitePositions,
}) => {
    const [currentSatelliteId, setCurrentSatelliteId] = useState<string | null>(null)
    const [connections, setConnections] = useState<SmoothConnection[]>([])
    const lastHandoverTime = useRef<number>(Date.now())
    
    // 🔧 改進的平滑處理 - 使用更精確的插值
    const smoothedPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())
    const targetPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())
    const velocityRef = useRef<Map<string, [number, number, number]>>(new Map())
    
    // 🎯 配置參數
    const SMOOTHING_FACTOR = 0.15 // 降低平滑因子，增加穩定性
    const POSITION_THRESHOLD = 0.3 // 位置變化閾值
    const CONNECTION_WIDTH = 0.8 // 連接線寬度
    const UPDATE_INTERVAL = 50 // 50ms 更新間隔，降低頻率

    // 🔗 獲取UAV位置
    const getUAVPositions = (): Array<[number, number, number]> => {
        return devices
            .filter((d) => d.role === 'receiver')
            .map((uav) => [
                uav.position_x || 0,
                uav.position_z || 0,
                uav.position_y || 0,
            ])
    }

    // 🔗 獲取可用衛星列表
    const getAvailableSatellites = (): string[] => {
        if (!satellitePositions) return []
        return Array.from(satellitePositions.keys())
    }

    // 🔗 隨機選擇下一個衛星
    const selectRandomSatellite = (): string | null => {
        const availableSatellites = getAvailableSatellites()
        if (availableSatellites.length === 0) return null
        
        const otherSatellites = availableSatellites.filter(id => id !== currentSatelliteId)
        if (otherSatellites.length === 0) return availableSatellites[0]
        
        const randomIndex = Math.floor(Math.random() * otherSatellites.length)
        return otherSatellites[randomIndex]
    }

    // 🔧 改進的插值函數 - 使用速度感知插值
    const velocityAwareLerp = (
        current: [number, number, number],
        target: [number, number, number],
        velocity: [number, number, number],
        deltaTime: number
    ): { position: [number, number, number], velocity: [number, number, number] } => {
        const diff = [
            target[0] - current[0],
            target[1] - current[1],
            target[2] - current[2]
        ] as [number, number, number]

        // 計算距離
        const distance = Math.sqrt(diff[0] * diff[0] + diff[1] * diff[1] + diff[2] * diff[2])
        
        // 動態調整平滑因子
        const dynamicSmoothingFactor = distance > POSITION_THRESHOLD 
            ? SMOOTHING_FACTOR * 2 // 距離大時加快收斂
            : SMOOTHING_FACTOR * 0.5 // 距離小時放慢，增加穩定性

        // 更新速度
        const newVelocity: [number, number, number] = [
            velocity[0] + diff[0] * dynamicSmoothingFactor * deltaTime,
            velocity[1] + diff[1] * dynamicSmoothingFactor * deltaTime,
            velocity[2] + diff[2] * dynamicSmoothingFactor * deltaTime,
        ]

        // 速度衰減
        const damping = 0.8
        newVelocity[0] *= damping
        newVelocity[1] *= damping
        newVelocity[2] *= damping

        // 更新位置
        const newPosition: [number, number, number] = [
            current[0] + newVelocity[0] * deltaTime,
            current[1] + newVelocity[1] * deltaTime,
            current[2] + newVelocity[2] * deltaTime,
        ]

        return { position: newPosition, velocity: newVelocity }
    }

    // 🔧 位置更新邏輯 - 使用定時器而非 useFrame，降低頻率
    useEffect(() => {
        if (!enabled) return

        const updatePositions = () => {
            if (!satellitePositions) return

            const deltaTime = UPDATE_INTERVAL / 1000 // 轉換為秒

            for (const [satId, targetPos] of satellitePositions.entries()) {
                targetPositionsRef.current.set(satId, targetPos)
                
                const currentSmoothed = smoothedPositionsRef.current.get(satId)
                const velocity = velocityRef.current.get(satId) || [0, 0, 0] as [number, number, number]
                
                if (!currentSmoothed) {
                    smoothedPositionsRef.current.set(satId, targetPos)
                    velocityRef.current.set(satId, [0, 0, 0])
                } else {
                    const { position, velocity: newVelocity } = velocityAwareLerp(
                        currentSmoothed, 
                        targetPos, 
                        velocity, 
                        deltaTime
                    )
                    smoothedPositionsRef.current.set(satId, position)
                    velocityRef.current.set(satId, newVelocity)
                }
            }

            // 清理已消失的衛星
            for (const satId of smoothedPositionsRef.current.keys()) {
                if (!satellitePositions.has(satId)) {
                    smoothedPositionsRef.current.delete(satId)
                    targetPositionsRef.current.delete(satId)
                    velocityRef.current.delete(satId)
                }
            }
        }

        const interval = setInterval(updatePositions, UPDATE_INTERVAL)
        return () => clearInterval(interval)
    }, [enabled, satellitePositions])

    // 🔄 換手邏輯 - 簡化並降低頻率
    useFrame(() => {
        if (!enabled) return
        
        const now = Date.now()
        const timeSinceLastHandover = now - lastHandoverTime.current
        const availableSatellites = getAvailableSatellites()
        
        // 🚨 緊急換手：當前衛星消失
        if (currentSatelliteId && !availableSatellites.includes(currentSatelliteId)) {
            const newSatellite = selectRandomSatellite()
            if (newSatellite) {
                console.log(`🚨 緊急換手: ${currentSatelliteId} -> ${newSatellite}`)
                setCurrentSatelliteId(newSatellite)
                lastHandoverTime.current = now
            }
        }
        
        // 🔄 定期換手：每6秒換手一次（增加間隔，減少抖動）
        if (timeSinceLastHandover >= 6000) {
            const newSatellite = selectRandomSatellite()
            if (newSatellite && newSatellite !== currentSatelliteId) {
                console.log(`🔄 定期換手: ${currentSatelliteId || '無'} -> ${newSatellite}`)
                setCurrentSatelliteId(newSatellite)
                lastHandoverTime.current = now
            }
        }
    })

    // 🎯 初始化連接
    useEffect(() => {
        if (!currentSatelliteId && enabled) {
            const firstSatellite = selectRandomSatellite()
            if (firstSatellite) {
                console.log(`🎯 初始連接: ${firstSatellite}`)
                setCurrentSatelliteId(firstSatellite)
                lastHandoverTime.current = Date.now()
            }
        }
    }, [enabled, satellitePositions])

    // 📐 生成連接線的曲線路徑
    const generateConnectionCurve = (
        startPos: [number, number, number], 
        endPos: [number, number, number]
    ): THREE.CatmullRomCurve3 => {
        const start = new THREE.Vector3(...startPos)
        const end = new THREE.Vector3(...endPos)
        
        // 創建輕微彎曲的連接線，避免完全直線
        const midPoint = start.clone().lerp(end, 0.5)
        const distance = start.distanceTo(end)
        
        // 添加輕微的弧形，高度基於距離
        const arcHeight = Math.min(distance * 0.1, 20)
        midPoint.y += arcHeight
        
        // 創建平滑曲線
        const curve = new THREE.CatmullRomCurve3([
            start,
            midPoint,
            end
        ])
        
        return curve
    }

    // 🎨 渲染連接管道
    const renderConnections = () => {
        if (!enabled || !currentSatelliteId) return null

        const uavPositions = getUAVPositions()
        const smoothedPosition = smoothedPositionsRef.current.get(currentSatelliteId)
        const satellitePosition = smoothedPosition || satellitePositions?.get(currentSatelliteId)
        
        if (!satellitePosition) {
            return null
        }

        return uavPositions.map((uavPos, index) => {
            const curve = generateConnectionCurve(satellitePosition, uavPos)
            
            return (
                <mesh key={`tube-connection-${currentSatelliteId}-${index}`}>
                    <tubeGeometry 
                        args={[
                            curve,        // 路徑曲線
                            32,           // 管道段數（提高平滑度）
                            CONNECTION_WIDTH,  // 管道半徑
                            8,            // 徑向段數
                            false         // 不封閉
                        ]} 
                    />
                    <meshBasicMaterial
                        color="#00ff00"
                        transparent
                        opacity={0.7}
                        emissive="#004400"
                        emissiveIntensity={0.2}
                    />
                </mesh>
            )
        })
    }

    if (!enabled) return null

    return (
        <group>
            {renderConnections()}
            
            {/* 🎯 調試用衛星位置指示器 */}
            {currentSatelliteId && satellitePositions?.get(currentSatelliteId) && (
                <mesh position={satellitePositions.get(currentSatelliteId)}>
                    <sphereGeometry args={[2, 16, 16]} />
                    <meshBasicMaterial 
                        color="#ffff00" 
                        transparent 
                        opacity={0.3}
                        wireframe
                    />
                </mesh>
            )}
        </group>
    )
}

export default ImprovedHandoverAnimation3D