/**
 * Phase 2: 換手事件視覺化組件
 * 
 * 顯示衛星間的切換動畫和換手事件
 * 整合 Phase 0 預計算的換手分析數據
 */

import React, { useRef, useEffect, useState, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'
import * as THREE from 'three'
import type { HandoverEvent } from '../../../../types/satellite'

export interface HandoverEventVisualizerProps {
  enabled: boolean
  handoverEvents: HandoverEvent[]
  currentTime: number
  satellitePositions: Map<string, [number, number, number]>
  onHandoverComplete?: (event: HandoverEvent) => void
  showTrails?: boolean
  animationDuration?: number
}

interface ActiveHandover {
  event: HandoverEvent
  startTime: number
  progress: number
  isActive: boolean
  connectionLine?: THREE.BufferGeometry
  effectParticles?: THREE.Points
}

export const HandoverEventVisualizer: React.FC<HandoverEventVisualizerProps> = ({
  enabled,
  handoverEvents,
  currentTime,
  satellitePositions,
  onHandoverComplete,
  showTrails = true,
  animationDuration = 3.0
}) => {
  const [activeHandovers, setActiveHandovers] = useState<Map<string, ActiveHandover>>(new Map())
  const [completedHandovers, setCompletedHandovers] = useState<Set<string>>(new Set())
  const groupRef = useRef<THREE.Group>(null)

  // 檢查新的換手事件
  useEffect(() => {
    if (!enabled) return

    handoverEvents.forEach((event) => {
      const eventKey = `${event.fromSatelliteId}-${event.toSatelliteId}-${event.timestamp}`
      
      // 檢查是否應該觸發換手動畫
      const timeDiff = Math.abs(currentTime - event.timestamp)
      const shouldTrigger = timeDiff <= 0.5 && !completedHandovers.has(eventKey)

      if (shouldTrigger) {
        console.log(`🔄 觸發換手事件: ${event.fromSatelliteId} -> ${event.toSatelliteId}`)
        
        const activeHandover: ActiveHandover = {
          event,
          startTime: currentTime,
          progress: 0,
          isActive: true
        }

        setActiveHandovers(prev => new Map(prev).set(eventKey, activeHandover))
      }
    })
  }, [enabled, handoverEvents, currentTime, completedHandovers])

  // 更新活躍的換手動畫
  useFrame((state, delta) => {
    if (!enabled || activeHandovers.size === 0) return

    const updatedHandovers = new Map(activeHandovers)
    const newCompletedHandovers = new Set(completedHandovers)

    updatedHandovers.forEach((handover, key) => {
      if (!handover.isActive) return

      // 更新進度
      const elapsed = currentTime - handover.startTime
      const progress = Math.min(elapsed / animationDuration, 1.0)
      
      handover.progress = progress

      // 檢查是否完成
      if (progress >= 1.0) {
        handover.isActive = false
        newCompletedHandovers.add(key)
        
        if (onHandoverComplete) {
          onHandoverComplete(handover.event)
        }
        
        console.log(`✅ 換手事件完成: ${handover.event.fromSatelliteId} -> ${handover.event.toSatelliteId}`)
      }
    })

    setActiveHandovers(updatedHandovers)
    setCompletedHandovers(newCompletedHandovers)
  })

  // 創建連接線幾何體
  const createConnectionLine = useCallback((
    fromPos: [number, number, number],
    toPos: [number, number, number],
    progress: number
  ): THREE.BufferGeometry => {
    const geometry = new THREE.BufferGeometry()
    
    // 創建貝塞爾曲線路徑
    const start = new THREE.Vector3(...fromPos)
    const end = new THREE.Vector3(...toPos)
    const mid = start.clone().lerp(end, 0.5)
    mid.y += 50 // 弧形高度
    
    const curve = new THREE.QuadraticBezierCurve3(start, mid, end)
    const points = curve.getPoints(50)
    
    // 根據進度截取路徑
    const visiblePoints = points.slice(0, Math.floor(points.length * progress))
    const positions = new Float32Array(visiblePoints.length * 3)
    
    visiblePoints.forEach((point, i) => {
      positions[i * 3] = point.x
      positions[i * 3 + 1] = point.y
      positions[i * 3 + 2] = point.z
    })
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    return geometry
  }, [])

  // 創建粒子效果
  const createParticleEffect = useCallback((
    fromPos: [number, number, number],
    toPos: [number, number, number],
    progress: number
  ): THREE.Points => {
    const particleCount = 20
    const geometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)
    const colors = new Float32Array(particleCount * 3)
    
    const start = new THREE.Vector3(...fromPos)
    const end = new THREE.Vector3(...toPos)
    
    for (let i = 0; i < particleCount; i++) {
      const t = (i / particleCount) * progress
      const pos = start.clone().lerp(end, t)
      
      // 添加隨機偏移
      pos.x += (Math.random() - 0.5) * 10
      pos.y += (Math.random() - 0.5) * 10
      pos.z += (Math.random() - 0.5) * 10
      
      positions[i * 3] = pos.x
      positions[i * 3 + 1] = pos.y
      positions[i * 3 + 2] = pos.z
      
      // 顏色從藍色到綠色漸變
      colors[i * 3] = 0.2 + t * 0.3     // R
      colors[i * 3 + 1] = 0.5 + t * 0.5 // G
      colors[i * 3 + 2] = 1.0 - t * 0.3 // B
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    
    const material = new THREE.PointsMaterial({
      size: 2,
      vertexColors: true,
      transparent: true,
      opacity: 0.8
    })
    
    return new THREE.Points(geometry, material)
  }, [])

  // 渲染換手視覺效果
  const renderHandoverEffects = () => {
    const effects: JSX.Element[] = []

    activeHandovers.forEach((handover, key) => {
      if (!handover.isActive) return

      const fromPos = satellitePositions.get(handover.event.fromSatelliteId)
      const toPos = satellitePositions.get(handover.event.toSatelliteId)

      if (!fromPos || !toPos) return

      const progress = handover.progress
      const opacity = Math.sin(progress * Math.PI) // 淡入淡出效果

      effects.push(
        <group key={key}>
          {/* 連接線 */}
          <Line
            points={[fromPos, toPos]}
            color="#00ff88"
            lineWidth={3}
            transparent
            opacity={opacity * 0.8}
            dashed
            dashSize={5}
            gapSize={2}
          />
          
          {/* 進度指示器 */}
          <mesh position={[
            fromPos[0] + (toPos[0] - fromPos[0]) * progress,
            fromPos[1] + (toPos[1] - fromPos[1]) * progress + 10,
            fromPos[2] + (toPos[2] - fromPos[2]) * progress
          ]}>
            <sphereGeometry args={[3, 8, 8]} />
            <meshBasicMaterial 
              color="#ffff00" 
              transparent 
              opacity={opacity}
            />
          </mesh>
          
          {/* 源衛星高亮 */}
          <mesh position={fromPos}>
            <sphereGeometry args={[5, 8, 8]} />
            <meshBasicMaterial 
              color="#ff4444" 
              transparent 
              opacity={opacity * 0.5}
            />
          </mesh>
          
          {/* 目標衛星高亮 */}
          <mesh position={toPos}>
            <sphereGeometry args={[5, 8, 8]} />
            <meshBasicMaterial 
              color="#44ff44" 
              transparent 
              opacity={opacity * 0.5}
            />
          </mesh>
          
          {/* 換手信息標籤 */}
          <group position={[
            (fromPos[0] + toPos[0]) / 2,
            (fromPos[1] + toPos[1]) / 2 + 20,
            (fromPos[2] + toPos[2]) / 2
          ]}>
            <mesh>
              <planeGeometry args={[40, 8]} />
              <meshBasicMaterial 
                color="#000000" 
                transparent 
                opacity={opacity * 0.8}
              />
            </mesh>
            {/* 這裡可以添加 Text 組件顯示換手信息 */}
          </group>
        </group>
      )
    })

    return effects
  }

  // 渲染換手軌跡
  const renderHandoverTrails = () => {
    if (!showTrails) return null

    const trails: JSX.Element[] = []

    completedHandovers.forEach((eventKey) => {
      const handover = activeHandovers.get(eventKey)
      if (!handover) return

      const fromPos = satellitePositions.get(handover.event.fromSatelliteId)
      const toPos = satellitePositions.get(handover.event.toSatelliteId)

      if (!fromPos || !toPos) return

      trails.push(
        <Line
          key={`trail-${eventKey}`}
          points={[fromPos, toPos]}
          color="#888888"
          lineWidth={1}
          transparent
          opacity={0.3}
          dashed
          dashSize={2}
          gapSize={1}
        />
      )
    })

    return trails
  }

  if (!enabled) {
    return null
  }

  return (
    <group ref={groupRef}>
      {renderHandoverEffects()}
      {renderHandoverTrails()}
    </group>
  )
}

export default HandoverEventVisualizer
