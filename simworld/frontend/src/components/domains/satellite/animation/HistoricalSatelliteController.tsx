/**
 * 基於真實歷史軌跡的3D衛星動畫控制器
 * 
 * 使用預處理的真實衛星歷史數據驅動3D動畫，支援：
 * - 2054顆 Starlink 衛星的真實軌跡
 * - 223顆 OneWeb 衛星的真實軌跡  
 * - 真實的仰角、方位角、距離變化
 * - 為換手動畫和觸發事件同步準備
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import * as THREE from 'three'
import { 
  historicalTrajectoryService,
  type SatelliteTrajectory,
  type TrajectoryPoint,
  type HistoricalAnimationConfig
} from '../../../../services/HistoricalTrajectoryService'

interface HistoricalSatelliteControllerProps {
  constellation: 'starlink' | 'oneweb' | 'both'
  maxSatellites?: number
  minElevation?: number
  animationSpeed?: number
  onSatelliteUpdate?: (satellites: Map<string, TrajectoryPoint>) => void
  onHandoverCandidate?: (sourceId: string, targetId: string, context: HandoverContext) => void
}

interface HandoverContext {
  sourceElevation: number
  targetElevation: number
  sourceSignalStrength: number
  targetSignalStrength: number
  timestamp: string
}

interface AnimationState {
  isPlaying: boolean
  currentTime: number
  startTime: number
  endTime: number
  totalDuration: number
  trajectories: Map<string, TrajectoryPoint[]>
  currentPositions: Map<string, TrajectoryPoint>
}

const HistoricalSatelliteController: React.FC<HistoricalSatelliteControllerProps> = ({
  constellation = 'both',
  maxSatellites = 10,
  minElevation = 10,
  animationSpeed = 60,
  onSatelliteUpdate,
  onHandoverCandidate
}) => {
  const [animationState, setAnimationState] = useState<AnimationState>({
    isPlaying: false,
    currentTime: 0,
    startTime: 0,
    endTime: 0,
    totalDuration: 0,
    trajectories: new Map(),
    currentPositions: new Map()
  })

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const animationRef = useRef<{ lastUpdateTime: number }>({ lastUpdateTime: 0 })

  /**
   * 載入真實歷史軌跡數據
   */
  const loadHistoricalData = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      console.log('🚀 載入真實歷史衛星軌跡數據...')
      
      const config: HistoricalAnimationConfig = {
        constellation,
        min_elevation_deg: minElevation,
        max_satellites: maxSatellites,
        animation_speed: animationSpeed,
        time_step_seconds: 30
      }

      const trajectories = await historicalTrajectoryService.generateAnimationTrajectories(config)
      const timeline = historicalTrajectoryService.calculateAnimationTimeline(trajectories)

      setAnimationState(prev => ({
        ...prev,
        trajectories,
        startTime: timeline.startTime,
        endTime: timeline.endTime,
        totalDuration: timeline.totalDuration,
        currentTime: timeline.startTime
      }))

      console.log(`✅ 載入完成: ${trajectories.size} 顆衛星，時長 ${(timeline.totalDuration/3600).toFixed(1)} 小時`)

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '載入歷史數據失敗'
      setError(errorMsg)
      console.error('❌ 載入歷史軌跡失敗:', err)
    } finally {
      setIsLoading(false)
    }
  }, [constellation, maxSatellites, minElevation, animationSpeed])

  /**
   * 播放控制
   */
  const togglePlayback = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying
    }))
  }, [])

  const resetAnimation = useCallback(() => {
    setAnimationState(prev => ({
      ...prev,
      isPlaying: false,
      currentTime: prev.startTime
    }))
  }, [])

  /**
   * 檢測換手候選衛星
   */
  const detectHandoverCandidates = useCallback((currentPositions: Map<string, TrajectoryPoint>) => {
    if (!onHandoverCandidate) return

    const satellites = Array.from(currentPositions.entries())
    
    // 找出信號強度下降的衛星（需要換手的源衛星）
    satellites.forEach(([sourceId, sourcePos]) => {
      if (sourcePos.elevation_deg < 15) { // 低於15度開始考慮換手
        
        // 找出信號更強的目標衛星
        satellites.forEach(([targetId, targetPos]) => {
          if (targetId !== sourceId && targetPos.elevation_deg > sourcePos.elevation_deg + 5) {
            
            // 計算信號強度 (簡化模型：基於仰角和距離)
            const sourceSignal = Math.max(0, sourcePos.elevation_deg - 5) / sourcePos.range_km * 1000
            const targetSignal = Math.max(0, targetPos.elevation_deg - 5) / targetPos.range_km * 1000
            
            if (targetSignal > sourceSignal * 1.2) { // 目標信號強20%以上
              onHandoverCandidate(sourceId, targetId, {
                sourceElevation: sourcePos.elevation_deg,
                targetElevation: targetPos.elevation_deg,
                sourceSignalStrength: sourceSignal,
                targetSignalStrength: targetSignal,
                timestamp: sourcePos.time
              })
            }
          }
        })
      }
    })
  }, [onHandoverCandidate])

  /**
   * 更新動畫時間和位置
   */
  useFrame((state, delta) => {
    if (!animationState.isPlaying || animationState.trajectories.size === 0) return

    const now = performance.now()
    if (now - animationRef.current.lastUpdateTime < 33) return // ~30fps

    setAnimationState(prev => {
      let newTime = prev.currentTime + (delta * 1000 * animationSpeed)
      
      // 循環播放
      if (newTime > prev.endTime) {
        newTime = prev.startTime
      }

      // 更新所有衛星的當前位置
      const newPositions = historicalTrajectoryService.getSatellitePositionsAtTime(
        prev.trajectories,
        newTime
      )

      // 檢測換手候選
      detectHandoverCandidates(newPositions)

      // 通知父組件衛星位置更新
      if (onSatelliteUpdate) {
        onSatelliteUpdate(newPositions)
      }

      animationRef.current.lastUpdateTime = now

      return {
        ...prev,
        currentTime: newTime,
        currentPositions: newPositions
      }
    })
  })

  /**
   * 初始化載入數據
   */
  useEffect(() => {
    loadHistoricalData()
  }, [loadHistoricalData])

  /**
   * 渲染3D衛星
   */
  const renderHistoricalSatellites = () => {
    return Array.from(animationState.currentPositions.entries()).map(([satelliteId, position]) => {
      // 將仰角、方位角轉換為3D座標
      const elevation = position.elevation_deg * Math.PI / 180
      const azimuth = position.azimuth_deg * Math.PI / 180
      
      // 距離縮放 (1000km = 1單位)
      const distance = position.range_km / 1000 * 0.8 // 適合3D場景的縮放
      
      const x = distance * Math.cos(elevation) * Math.sin(azimuth)
      const y = distance * Math.sin(elevation)
      const z = distance * Math.cos(elevation) * Math.cos(azimuth)

      // 根據仰角決定衛星顏色 (仰角越高越亮)
      const elevationNormalized = Math.max(0, position.elevation_deg) / 90
      const color = new THREE.Color().setHSL(0.6, 0.8, 0.3 + elevationNormalized * 0.5)

      return (
        <group key={satelliteId} position={[x, y, z]}>
          {/* 衛星本體 */}
          <mesh>
            <sphereGeometry args={[0.02, 16, 16]} />
            <meshBasicMaterial color={color} />
          </mesh>
          
          {/* 衛星名稱標籤 */}
          <Html distanceFactor={10} position={[0, 0.05, 0]}>
            <div style={{
              background: 'rgba(0,0,0,0.7)',
              color: 'white',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '10px',
              fontFamily: 'monospace',
              pointerEvents: 'none'
            }}>
              {/* 使用正確的屬性名稱 */}
              {satelliteId}
              <br />
              {position.elevation_deg.toFixed(1)}° / {position.azimuth_deg.toFixed(1)}°
              <br />
              {position.range_km.toFixed(0)}km
            </div>
          </Html>

          {/* 軌跡路徑 (顯示歷史軌跡) */}
          {animationState.trajectories.has(satelliteId) && (
            <TrajectoryPath 
              trajectory={animationState.trajectories.get(satelliteId)!}
              currentTime={animationState.currentTime}
            />
          )}
        </group>
      )
    })
  }

  if (isLoading) {
    return (
      <Html center>
        <div style={{ color: 'white', textAlign: 'center' }}>
          🛰️ 載入真實歷史衛星軌跡...
          <br />
          {constellation === 'both' ? '2277顆衛星' : constellation === 'starlink' ? '2054顆 Starlink' : '223顆 OneWeb'}
        </div>
      </Html>
    )
  }

  if (error) {
    return (
      <Html center>
        <div style={{ color: 'red', textAlign: 'center' }}>
          ❌ 載入失敗: {error}
          <br />
          <button onClick={loadHistoricalData} style={{ marginTop: '10px' }}>
            重新載入
          </button>
        </div>
      </Html>
    )
  }

  return (
    <>
      {renderHistoricalSatellites()}
      
      {/* 動畫控制 UI */}
      <Html position={[-2, 2, 0]}>
        <div style={{
          background: 'rgba(0,0,0,0.8)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontFamily: 'monospace'
        }}>
          <div>🛰️ 真實歷史軌跡動畫</div>
          <div>衛星數: {animationState.currentPositions.size}</div>
          <div>時間: {((animationState.currentTime - animationState.startTime) / 60).toFixed(1)} 分鐘</div>
          <div>進度: {((animationState.currentTime - animationState.startTime) / animationState.totalDuration * 100).toFixed(1)}%</div>
          
          <div style={{ marginTop: '10px' }}>
            <button onClick={togglePlayback} style={{ marginRight: '5px' }}>
              {animationState.isPlaying ? '⏸️ 暫停' : '▶️ 播放'}
            </button>
            <button onClick={resetAnimation}>
              🔄 重置
            </button>
          </div>
        </div>
      </Html>
    </>
  )
}

/**
 * 軌跡路徑組件 - 顯示衛星的歷史和未來軌跡
 */
interface TrajectoryPathProps {
  trajectory: TrajectoryPoint[]
  currentTime: number
}

const TrajectoryPath: React.FC<TrajectoryPathProps> = ({ trajectory, currentTime }) => {
  const pathRef = useRef<THREE.BufferGeometry>(null)

  useEffect(() => {
    if (!pathRef.current || trajectory.length < 2) return

    // 將軌跡點轉換為3D座標
    const points: THREE.Vector3[] = trajectory.map(point => {
      const elevation = point.elevation_deg * Math.PI / 180
      const azimuth = point.azimuth_deg * Math.PI / 180
      const distance = point.range_km / 1000 * 0.8

      return new THREE.Vector3(
        distance * Math.cos(elevation) * Math.sin(azimuth),
        distance * Math.sin(elevation),
        distance * Math.cos(elevation) * Math.cos(azimuth)
      )
    })

    pathRef.current.setFromPoints(points)
  }, [trajectory])

  // 根據時間決定軌跡的顏色 (過去=暗，當前=亮，未來=半透明)
  const getTrajectoryColor = () => {
    return new THREE.Color(0x00ffff) // 青色軌跡
  }

  return (
    <line>
      <bufferGeometry ref={pathRef} />
      <lineBasicMaterial 
        color={getTrajectoryColor()}
        transparent
        opacity={0.4}
        linewidth={2}
      />
    </line>
  )
}

export default HistoricalSatelliteController