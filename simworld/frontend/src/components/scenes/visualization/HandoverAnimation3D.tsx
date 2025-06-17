import React, { useState, useEffect, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'

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

    // 🔗 換手邏輯：5秒定期換手 + 衛星消失時立即換手
    useFrame(() => {
        if (!enabled) return
        
        const now = Date.now()
        const timeSinceLastHandover = now - lastHandoverTime.current
        const availableSatellites = getAvailableSatellites()
        
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

    // 🔗 渲染連線
    const renderConnections = () => {
        if (!enabled || !currentSatelliteId || !satellitePositions) return null

        const uavPositions = getUAVPositions()
        const satellitePosition = satellitePositions.get(currentSatelliteId)
        
        if (!satellitePosition) {
            console.warn(`❌ 找不到衛星位置: ${currentSatelliteId}`)
            return null
        }

        return uavPositions.map((uavPos, index) => (
            <Line
                key={`connection-${currentSatelliteId}-${index}`}
                points={[satellitePosition, uavPos]}
                color="#00ff00"
                lineWidth={3}
                transparent
                opacity={0.8}
            />
        ))
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