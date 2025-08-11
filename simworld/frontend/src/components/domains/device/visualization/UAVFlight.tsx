import { useRef, useEffect, useState, useMemo } from 'react'
import { useGLTF } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
// @ts-expect-error SkeletonUtils has no TypeScript definitions
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js'
import { ApiRoutes } from '../../../../config/apiRoutes'

const UAV_MODEL_URL = ApiRoutes.simulations.getModel('uav')

// 🎯 簡化的飛行配置
const FLIGHT_CONFIG = {
    MOVE_DISTANCE: 60,        // 直線移動距離
    FLIGHT_SPEED: 15,         // 飛行速度（單位/秒）
    HEIGHT_VARIATION: 2,      // 高度變化幅度
    HEIGHT_SPEED: 0.01        // 高度變化速度
}

// 🎯 簡化的UAV屬性 - 只保留直線飛行需要的
export interface UAVFlightProps {
    position: [number, number, number]
    scale: [number, number, number]
    auto: boolean                    // 是否自動飛行
    uavAnimation: boolean           // 是否播放螺旋槳動畫
}

export default function UAVFlight({
    position,
    scale,
    auto,
    uavAnimation,
}: UAVFlightProps) {
    const group = useRef<THREE.Group>(null)
    const { scene, animations } = useGLTF(UAV_MODEL_URL) as {
        scene: THREE.Object3D
        animations: THREE.AnimationClip[]
    }
    const clonedScene = useMemo(() => SkeletonUtils.clone(scene), [scene])
    
    const [mixer, setMixer] = useState<THREE.AnimationMixer | null>(null)
    
    // 🎯 簡化的狀態 - 直線來回移動
    const flightTime = useRef(0)
    const basePosition = useRef(new THREE.Vector3(...position))  // 原始位置
    const currentPosition = useRef(new THREE.Vector3(...position))
    const flightDirection = useRef(1)                            // 1=向右移動, -1=向左移動
    
    // 🎯 初始化
    useEffect(() => {
        basePosition.current.set(...position)
        currentPosition.current.set(...position)
        console.log(`🛩️ UAV初始化 at (${position[0]}, ${position[1]}, ${position[2]})`)
    }, [position])

    // 🎯 簡化的動畫設置
    useEffect(() => {
        if (clonedScene && animations && animations.length > 0) {
            console.log('🛩️ UAV模型載入成功')
            const newMixer = new THREE.AnimationMixer(clonedScene)
            setMixer(newMixer)
            
            // 只播放第一個找到的動畫（通常是懸停）
            if (animations[0]) {
                const action = newMixer.clipAction(animations[0])
                action.setEffectiveWeight(1)
                action.setLoop(THREE.LoopRepeat, Infinity)
                if (uavAnimation) {
                    action.play()
                }
            }
        }
    }, [clonedScene, animations, uavAnimation])

    // 🎯 簡單的直線來回飛行邏輯
    useFrame((state, delta) => {
        // 更新動畫mixer
        if (mixer) {
            mixer.update(delta)
        }

        if (auto && group.current) {
            flightTime.current += delta

            // 計算基於時間的X軸偏移量
            const moveSpeed = FLIGHT_CONFIG.FLIGHT_SPEED * delta
            const maxDistance = FLIGHT_CONFIG.MOVE_DISTANCE / 2  // 左右各移動一半距離
            
            // 計算當前X偏移量（從basePosition開始）
            const currentXOffset = currentPosition.current.x - basePosition.current.x
            
            // 檢查是否到達邊界，需要轉向
            if (currentXOffset >= maxDistance) {
                flightDirection.current = -1  // 向左移動
            } else if (currentXOffset <= -maxDistance) {
                flightDirection.current = 1   // 向右移動
            }
            
            // 計算新位置
            const newXOffset = currentXOffset + (moveSpeed * flightDirection.current)
            const x = basePosition.current.x + newXOffset
            
            // Y軸：保持在基礎高度附近，小幅波動
            const heightWave = Math.sin(flightTime.current * FLIGHT_CONFIG.HEIGHT_SPEED) * FLIGHT_CONFIG.HEIGHT_VARIATION
            const y = basePosition.current.y + heightWave
            
            // Z軸：保持原位
            const z = basePosition.current.z
            
            // Debug信息（每3秒輸出一次）
            if (Math.floor(flightTime.current) % 3 === 0 && Math.floor(flightTime.current * 10) % 10 === 0) {
                console.log(`🛩️ UAV直線飛行: 
                  基礎位置: (${basePosition.current.x.toFixed(1)}, ${basePosition.current.y.toFixed(1)}, ${basePosition.current.z.toFixed(1)})
                  當前位置: (${x.toFixed(1)}, ${y.toFixed(1)}, ${z.toFixed(1)})
                  X偏移: ${newXOffset.toFixed(1)}, 方向: ${flightDirection.current > 0 ? '→' : '←'}`)
            }
            
            // 更新位置
            currentPosition.current.set(x, y, z)
            group.current.position.copy(currentPosition.current)
            
            // 讓UAV面向飛行方向
            const lookAtX = x + (flightDirection.current * 10)  // 朝著移動方向看
            group.current.lookAt(lookAtX, y, z)
            
        } else if (group.current) {
            // 🎯 停止飛行時立即回到原始位置
            console.log('🛩️ 停止飛行 - 回到原始位置')
            currentPosition.current.copy(basePosition.current)
            group.current.position.copy(basePosition.current)
            flightTime.current = 0      // 重置飛行時間
            flightDirection.current = 1 // 重置方向為向右
        }
    })

    return (
        <group ref={group} scale={scale}>
            <primitive object={clonedScene} />
            <pointLight
                intensity={0.3}
                distance={50}
                decay={2}
                color="#ffffff"
                position={[0, 2, 0]}
            />
        </group>
    )
}

// 預載入模型
useGLTF.preload(UAV_MODEL_URL)