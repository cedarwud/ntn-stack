import React, { useState, useEffect, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

interface HandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellitePositions?: Map<string, [number, number, number]>
}

const HandoverAnimation3D: React.FC<HandoverAnimation3DProps> = ({
    devices,
    enabled,
    satellitePositions,
}) => {
    // 🔗 簡化狀態：只需要當前連接的衛星ID
    const [currentSatelliteId, setCurrentSatelliteId] = useState<string | null>(null)
    const lastHandoverTime = useRef<number>(Date.now())
    
    // 🔧 添加位置平滑處理
    const smoothedPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())
    const targetPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())
    const lastUpdateTimeRef = useRef<number>(Date.now())
    const geometryUpdateIntervalRef = useRef<number>(0)
    
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
        
        // 排除當前衛星，確保會換手
        const otherSatellites = availableSatellites.filter(id => id !== currentSatelliteId)
        if (otherSatellites.length === 0) return availableSatellites[0] // 如果只有一個衛星
        
        const randomIndex = Math.floor(Math.random() * otherSatellites.length)
        return otherSatellites[randomIndex]
    }

    // 🔧 位置平滑插值函數
    const lerpPosition = (
        current: [number, number, number],
        target: [number, number, number],
        factor: number
    ): [number, number, number] => {
        return [
            current[0] + (target[0] - current[0]) * factor,
            current[1] + (target[1] - current[1]) * factor,
            current[2] + (target[2] - current[2]) * factor,
        ]
    }

    // 🔗 換手邏輯：5秒定期換手 + 衛星消失時立即換手 + 位置平滑處理
    useFrame((state, delta) => {
        if (!enabled) return
        
        const now = Date.now()
        const timeSinceLastHandover = now - lastHandoverTime.current
        const availableSatellites = getAvailableSatellites()
        
        // 🔧 更新位置平滑處理（降低更新頻率，減少幾何體重建）
        geometryUpdateIntervalRef.current += delta * 1000
        const shouldUpdateGeometry = geometryUpdateIntervalRef.current >= 50 // 50ms 間隔
        
        if (satellitePositions && shouldUpdateGeometry) {
            geometryUpdateIntervalRef.current = 0
            const smoothingFactor = 0.15 // 固定平滑因子，更穩定
            
            for (const [satId, targetPos] of satellitePositions.entries()) {
                // 更新目標位置
                targetPositionsRef.current.set(satId, targetPos)
                
                // 獲取當前平滑位置
                const currentSmoothed = smoothedPositionsRef.current.get(satId)
                
                if (!currentSmoothed) {
                    // 首次出現，直接設定為目標位置
                    smoothedPositionsRef.current.set(satId, targetPos)
                } else {
                    // 平滑插值到目標位置
                    const smoothedPos = lerpPosition(currentSmoothed, targetPos, smoothingFactor)
                    smoothedPositionsRef.current.set(satId, smoothedPos)
                }
            }
            
            // 清理已消失的衛星
            for (const satId of smoothedPositionsRef.current.keys()) {
                if (!satellitePositions.has(satId)) {
                    smoothedPositionsRef.current.delete(satId)
                    targetPositionsRef.current.delete(satId)
                }
            }
        }
        
        // 🚨 緊急換手：當前衛星從場景中消失時立即切換
        if (currentSatelliteId && !availableSatellites.includes(currentSatelliteId)) {
            const newSatellite = selectRandomSatellite()
            if (newSatellite) {
                console.log(`🚨 緊急換手（衛星消失）: ${currentSatelliteId} -> ${newSatellite}`)
                setCurrentSatelliteId(newSatellite)
                lastHandoverTime.current = now
                return // 立即返回，避免重複處理
            }
        }
        
        // 🔄 定期換手：每5秒換手一次
        if (timeSinceLastHandover >= 5000) {
            const newSatellite = selectRandomSatellite()
            if (newSatellite && newSatellite !== currentSatelliteId) {
                console.log(`🔄 定期換手: ${currentSatelliteId || '無'} -> ${newSatellite}`)
                setCurrentSatelliteId(newSatellite)
                lastHandoverTime.current = now
            }
        }
    })

    // 🔗 初始化第一個連接
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

    // 🔗 渲染連線（使用平滑位置）
    const renderConnections = () => {
        if (!enabled || !currentSatelliteId) return null

        const uavPositions = getUAVPositions()
        // 🔧 使用平滑處理後的位置，如果沒有則回退到原始位置
        const smoothedPosition = smoothedPositionsRef.current.get(currentSatelliteId)
        const satellitePosition = smoothedPosition || satellitePositions?.get(currentSatelliteId)
        
        if (!satellitePosition) {
            console.warn(`❌ 找不到衛星位置: ${currentSatelliteId}`)
            return null
        }

        return uavPositions.map((uavPos, index) => {
            // 🔧 使用 TubeGeometry 替代 Line，解決抖動問題
            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(...satellitePosition),
                new THREE.Vector3(...uavPos)
            ])
            
            return (
                <mesh key={`connection-${currentSatelliteId}-${index}`}>
                    <tubeGeometry 
                        args={[curve, 20, 0.5, 8, false]} 
                    />
                    <meshBasicMaterial 
                        color="#00ff00" 
                        transparent 
                        opacity={0.8}
                    />
                </mesh>
            )
        })
    }

    if (!enabled) return null

    return (
        <group>
            {renderConnections()}
            
            {/* 🔗 調試信息 */}
            {currentSatelliteId && (
                <mesh position={[0, 50, 0]}>
                    <boxGeometry args={[0.1, 0.1, 0.1]} />
                    <meshBasicMaterial color="yellow" />
                </mesh>
            )}
        </group>
    )
}

export default HandoverAnimation3D