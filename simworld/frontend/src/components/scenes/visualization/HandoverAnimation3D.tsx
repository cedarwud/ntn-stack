import React, { useState, useEffect, useRef } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Ring, Text } from '@react-three/drei'

interface HandoverAnimation3DProps {
    devices: any[]
    enabled: boolean
    satellitePositions?: Map<string, [number, number, number]>
}

// 🔄 換手階段定義
type HandoverPhase = 'stable' | 'preparing' | 'establishing' | 'switching' | 'completing'

interface HandoverState {
    phase: HandoverPhase
    currentSatelliteId: string | null
    targetSatelliteId: string | null
    progress: number // 0-1
    phaseStartTime: number
    totalElapsed: number
}

const HandoverAnimation3D: React.FC<HandoverAnimation3DProps> = ({
    devices,
    enabled,
    satellitePositions,
}) => {
    // 🔗 換手狀態管理
    const [handoverState, setHandoverState] = useState<HandoverState>({
        phase: 'stable',
        currentSatelliteId: null,
        targetSatelliteId: null,
        progress: 0,
        phaseStartTime: Date.now(),
        totalElapsed: 0
    })

    // 🔧 位置平滑處理
    const smoothedPositionsRef = useRef<Map<string, [number, number, number]>>(new Map())
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

    // 🔗 隨機選擇衛星（排除當前衛星）
    const selectRandomSatellite = (excludeId?: string): string | null => {
        const availableSatellites = getAvailableSatellites()
        if (availableSatellites.length === 0) return null
        
        const candidates = availableSatellites.filter(id => id !== excludeId)
        if (candidates.length === 0) return availableSatellites[0]
        
        const randomIndex = Math.floor(Math.random() * candidates.length)
        return candidates[randomIndex]
    }

    // 🔧 位置平滑插值
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

    // ⏰ 階段時間配置（按 handover.md）
    const PHASE_DURATIONS = {
        stable: 30000,      // 0-30秒：穩定期
        preparing: 5000,    // 30-35秒：準備期（倒數5秒）
        establishing: 3000, // 35-38秒：建立期（3秒）
        switching: 2000,    // 38-40秒：切換期（2秒）
        completing: 5000    // 40-45秒：完成期（5秒）
    }

    // 🔄 換手邏輯核心
    useFrame((state, delta) => {
        if (!enabled) return

        const now = Date.now()
        const phaseElapsed = now - handoverState.phaseStartTime
        const availableSatellites = getAvailableSatellites()

        // 🔧 位置平滑處理（50ms間隔）
        geometryUpdateIntervalRef.current += delta * 1000
        if (geometryUpdateIntervalRef.current >= 50 && satellitePositions) {
            geometryUpdateIntervalRef.current = 0
            const smoothingFactor = 0.15

            for (const [satId, targetPos] of satellitePositions.entries()) {
                const currentSmoothed = smoothedPositionsRef.current.get(satId)
                if (!currentSmoothed) {
                    smoothedPositionsRef.current.set(satId, targetPos)
                } else {
                    const smoothedPos = lerpPosition(currentSmoothed, targetPos, smoothingFactor)
                    smoothedPositionsRef.current.set(satId, smoothedPos)
                }
            }

            // 清理消失的衛星
            for (const satId of smoothedPositionsRef.current.keys()) {
                if (!satellitePositions.has(satId)) {
                    smoothedPositionsRef.current.delete(satId)
                }
            }
        }

        // 🚨 緊急換手：當前衛星消失
        if (handoverState.currentSatelliteId && 
            !availableSatellites.includes(handoverState.currentSatelliteId)) {
            const newSatellite = selectRandomSatellite(handoverState.currentSatelliteId)
            if (newSatellite) {
                console.log(`🚨 緊急換手（衛星消失）: ${handoverState.currentSatelliteId} -> ${newSatellite}`)
                setHandoverState({
                    phase: 'stable',
                    currentSatelliteId: newSatellite,
                    targetSatelliteId: null,
                    progress: 0,
                    phaseStartTime: now,
                    totalElapsed: 0
                })
                return
            }
        }

        // 📊 更新當前階段進度
        const currentPhaseDuration = PHASE_DURATIONS[handoverState.phase]
        const progress = Math.min(phaseElapsed / currentPhaseDuration, 1.0)

        // 🔄 階段轉換邏輯
        let newState = { ...handoverState, progress }

        if (progress >= 1.0) {
            switch (handoverState.phase) {
                case 'stable':
                    // 進入準備期，選擇目標衛星
                    const targetSatellite = selectRandomSatellite(handoverState.currentSatelliteId)
                    if (targetSatellite) {
                        console.log(`🔄 開始換手: ${handoverState.currentSatelliteId} -> ${targetSatellite}`)
                        newState = {
                            phase: 'preparing',
                            currentSatelliteId: handoverState.currentSatelliteId,
                            targetSatelliteId: targetSatellite,
                            progress: 0,
                            phaseStartTime: now,
                            totalElapsed: handoverState.totalElapsed + phaseElapsed
                        }
                    }
                    break

                case 'preparing':
                    console.log(`📡 建立新連接: ${handoverState.targetSatelliteId}`)
                    newState = {
                        ...handoverState,
                        phase: 'establishing',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed
                    }
                    break

                case 'establishing':
                    console.log(`⚡ 切換連接中...`)
                    newState = {
                        ...handoverState,
                        phase: 'switching',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed
                    }
                    break

                case 'switching':
                    console.log(`✅ 換手完成: ${handoverState.targetSatelliteId}`)
                    newState = {
                        ...handoverState,
                        phase: 'completing',
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: handoverState.totalElapsed + phaseElapsed
                    }
                    break

                case 'completing':
                    console.log(`📡 連接穩定: ${handoverState.targetSatelliteId}`)
                    newState = {
                        phase: 'stable',
                        currentSatelliteId: handoverState.targetSatelliteId,
                        targetSatelliteId: null,
                        progress: 0,
                        phaseStartTime: now,
                        totalElapsed: 0 // 重置週期
                    }
                    break
            }
            setHandoverState(newState)
        } else if (newState.progress !== handoverState.progress) {
            setHandoverState(newState)
        }
    })

    // 🎯 初始化第一個連接
    useEffect(() => {
        if (!handoverState.currentSatelliteId && enabled) {
            const firstSatellite = selectRandomSatellite()
            if (firstSatellite) {
                console.log(`🎯 初始連接: ${firstSatellite}`)
                setHandoverState(prev => ({
                    ...prev,
                    currentSatelliteId: firstSatellite,
                    phaseStartTime: Date.now()
                }))
            }
        }
    }, [enabled, satellitePositions])

    // 🔗 渲染連接線（支援雙線和動畫效果）
    const renderConnections = () => {
        if (!enabled || !handoverState.currentSatelliteId) return null

        const uavPositions = getUAVPositions()
        const connections = []

        // 🟢 當前連接線
        if (handoverState.currentSatelliteId) {
            const smoothedPos = smoothedPositionsRef.current.get(handoverState.currentSatelliteId)
            const satellitePos = smoothedPos || satellitePositions?.get(handoverState.currentSatelliteId)
            
            if (satellitePos) {
                const currentLineProps = getCurrentLineProperties()
                
                uavPositions.forEach((uavPos, index) => {
                    const curve = new THREE.CatmullRomCurve3([
                        new THREE.Vector3(...satellitePos),
                        new THREE.Vector3(...uavPos)
                    ])
                    
                    connections.push(
                        <mesh key={`current-${handoverState.currentSatelliteId}-${index}`}>
                            <tubeGeometry args={[curve, 20, currentLineProps.radius, 8, false]} />
                            <meshBasicMaterial 
                                color={currentLineProps.color}
                                transparent 
                                opacity={currentLineProps.opacity}
                            />
                        </mesh>
                    )
                })
            }
        }

        // 🔵 目標連接線（建立期和切換期）
        if (handoverState.targetSatelliteId && 
            (handoverState.phase === 'establishing' || handoverState.phase === 'switching')) {
            const smoothedPos = smoothedPositionsRef.current.get(handoverState.targetSatelliteId)
            const satellitePos = smoothedPos || satellitePositions?.get(handoverState.targetSatelliteId)
            
            if (satellitePos) {
                const targetLineProps = getTargetLineProperties()
                
                uavPositions.forEach((uavPos, index) => {
                    const curve = new THREE.CatmullRomCurve3([
                        new THREE.Vector3(...satellitePos),
                        new THREE.Vector3(...uavPos)
                    ])
                    
                    connections.push(
                        <mesh key={`target-${handoverState.targetSatelliteId}-${index}`}>
                            <tubeGeometry args={[curve, 20, targetLineProps.radius, 8, false]} />
                            <meshBasicMaterial 
                                color={targetLineProps.color}
                                transparent 
                                opacity={targetLineProps.opacity}
                            />
                        </mesh>
                    )
                })
            }
        }

        return connections
    }

    // 🎨 當前連接線屬性
    const getCurrentLineProperties = () => {
        switch (handoverState.phase) {
            case 'stable':
                return { color: '#00ff00', opacity: 0.8, radius: 0.5 } // 綠色實線
            case 'preparing':
                // 閃爍效果
                const flicker = Math.sin(Date.now() * 0.01) * 0.3 + 0.7
                return { color: '#ffff00', opacity: flicker, radius: 0.5 } // 黃色閃爍
            case 'establishing':
                return { color: '#ffff00', opacity: 0.6, radius: 0.4 } // 黃色變淡
            case 'switching':
                return { color: '#808080', opacity: 0.4, radius: 0.3 } // 灰色虛線
            case 'completing':
                return { color: '#808080', opacity: 0.2, radius: 0.2 } // 灰色淡出
            default:
                return { color: '#00ff00', opacity: 0.8, radius: 0.5 }
        }
    }

    // 🎨 目標連接線屬性
    const getTargetLineProperties = () => {
        switch (handoverState.phase) {
            case 'establishing':
                // 逐漸變實
                const establishOpacity = handoverState.progress * 0.6
                return { color: '#0080ff', opacity: establishOpacity, radius: 0.3 } // 藍色漸現
            case 'switching':
                return { color: '#00ff00', opacity: 0.8, radius: 0.5 } // 綠色實線
            default:
                return { color: '#0080ff', opacity: 0.3, radius: 0.3 }
        }
    }

    // 🌟 目標衛星光圈
    const renderTargetSatelliteRing = () => {
        if (!handoverState.targetSatelliteId || handoverState.phase === 'stable') return null

        const satellitePos = smoothedPositionsRef.current.get(handoverState.targetSatelliteId) ||
                           satellitePositions?.get(handoverState.targetSatelliteId)
        
        if (!satellitePos) return null

        const pulseScale = 1 + Math.sin(Date.now() * 0.008) * 0.3 // 脈衝效果
        
        return (
            <group position={satellitePos}>
                <Ring
                    args={[8 * pulseScale, 12 * pulseScale, 32]}
                    rotation={[Math.PI / 2, 0, 0]}
                >
                    <meshBasicMaterial 
                        color="#0080ff"
                        transparent
                        opacity={0.3}
                        side={THREE.DoubleSide}
                    />
                </Ring>
            </group>
        )
    }

    // 📱 狀態文字顯示
    const getStatusText = () => {
        const countdown = handoverState.phase === 'preparing' ? 
            Math.ceil((PHASE_DURATIONS.preparing - (Date.now() - handoverState.phaseStartTime)) / 1000) : 0

        switch (handoverState.phase) {
            case 'stable':
                return `📡 連接穩定 - ${handoverState.currentSatelliteId?.slice(-4) || '未知'}`
            case 'preparing':
                return `🔄 準備換手到 ${handoverState.targetSatelliteId?.slice(-4)} - ${countdown}秒`
            case 'establishing':
                return `🔗 建立新連接 - ${Math.round(handoverState.progress * 100)}%`
            case 'switching':
                return `⚡ 切換連接中 - ${Math.round(handoverState.progress * 100)}%`
            case 'completing':
                return `✅ 換手完成 - ${handoverState.targetSatelliteId?.slice(-4)}`
            default:
                return '🔍 等待連接...'
        }
    }

    if (!enabled) return null

    return (
        <group>
            {renderConnections()}
            {renderTargetSatelliteRing()}
            
            {/* 📱 狀態文字 */}
            <Text
                position={[0, 60, 0]}
                fontSize={8}
                color="white"
                anchorX="center"
                anchorY="middle"
            >
                {getStatusText()}
            </Text>
            
            {/* 🎯 調試信息 */}
            {handoverState.currentSatelliteId && (
                <mesh position={[0, 50, 0]}>
                    <boxGeometry args={[0.1, 0.1, 0.1]} />
                    <meshBasicMaterial color="yellow" />
                </mesh>
            )}
        </group>
    )
}

export default HandoverAnimation3D