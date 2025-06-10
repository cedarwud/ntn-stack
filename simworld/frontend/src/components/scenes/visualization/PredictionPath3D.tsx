import React, { useRef, useMemo, useEffect, useState } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import { Line, Text, Sphere, Ring, Cylinder, Cone } from '@react-three/drei'
import * as THREE from 'three'

interface PredictionPath3DProps {
  enabled: boolean
  satellites: any[]
  selectedUAV?: any
  predictionTimeHorizon?: number // 預測時間範圍（秒）
}

interface PredictionPoint {
  position: [number, number, number]
  timestamp: number
  confidence: number
  handoverProbability: number
}

interface SatellitePrediction {
  satelliteId: string
  currentPosition: [number, number, number]
  predictedPath: PredictionPoint[]
  visibility: {
    start: number
    end: number
    maxElevation: number
  }
}

interface UAVPrediction {
  currentPosition: [number, number, number]
  predictedPath: PredictionPoint[]
  plannedRoute: [number, number, number][]
}

interface HandoverPoint {
  position: [number, number, number]
  timestamp: number
  fromSatellite: string
  toSatellite: string
  confidence: number
  type: 'predicted' | 'optimal' | 'critical'
}

const PredictionPath3D: React.FC<PredictionPath3DProps> = ({
  enabled,
  satellites,
  selectedUAV,
  predictionTimeHorizon = 300 // 預設5分鐘
}) => {
  const groupRef = useRef<THREE.Group>(null)
  const { scene } = useThree()
  
  // 狀態管理
  const [satellitePredictions, setSatellitePredictions] = useState<SatellitePrediction[]>([])
  const [uavPrediction, setUAVPrediction] = useState<UAVPrediction | null>(null)
  const [handoverPoints, setHandoverPoints] = useState<HandoverPoint[]>([])
  const [animationTime, setAnimationTime] = useState(0)

  // 生成衛星預測軌道
  const generateSatellitePrediction = (satellite: any): SatellitePrediction => {
    const currentPos: [number, number, number] = [
      satellite.position?.x || Math.cos(satellite.azimuth_deg * Math.PI / 180) * satellite.distance_km / 10,
      satellite.position?.z || satellite.distance_km / 10,
      satellite.position?.y || Math.sin(satellite.azimuth_deg * Math.PI / 180) * satellite.distance_km / 10
    ]

    // 生成預測路徑點
    const predictedPath: PredictionPoint[] = []
    const steps = 60 // 60個時間步長
    const timeStep = predictionTimeHorizon / steps

    for (let i = 0; i < steps; i++) {
      const t = i * timeStep
      // 模擬衛星軌道運動（簡化的圓形軌道）
      const angle = t * 0.001 // 軌道角速度
      const radius = satellite.distance_km / 10
      
      const position: [number, number, number] = [
        currentPos[0] * Math.cos(angle) - currentPos[2] * Math.sin(angle),
        currentPos[1] + t * 0.01, // 輕微的高度變化
        currentPos[0] * Math.sin(angle) + currentPos[2] * Math.cos(angle)
      ]

      // 計算信號強度和可見性
      const distance = Math.sqrt(position[0]**2 + position[1]**2 + position[2]**2)
      const confidence = Math.max(0.3, 1 - distance / 100)
      const handoverProbability = confidence < 0.6 ? Math.random() * 0.8 : Math.random() * 0.3

      predictedPath.push({
        position,
        timestamp: Date.now() + t * 1000,
        confidence,
        handoverProbability
      })
    }

    return {
      satelliteId: satellite.norad_id || satellite.id,
      currentPosition: currentPos,
      predictedPath,
      visibility: {
        start: Date.now(),
        end: Date.now() + predictionTimeHorizon * 1000,
        maxElevation: satellite.elevation_deg
      }
    }
  }

  // 生成UAV預測路徑
  const generateUAVPrediction = (uav: any): UAVPrediction => {
    const currentPos: [number, number, number] = [
      uav.position_x || 0,
      uav.position_z || 10,
      uav.position_y || 0
    ]

    // 生成UAV預測移動路徑
    const predictedPath: PredictionPoint[] = []
    const plannedRoute: [number, number, number][] = []
    const steps = 30

    for (let i = 0; i < steps; i++) {
      const t = i * (predictionTimeHorizon / steps)
      // 模擬UAV的預定航線（可能是圓形巡邏或直線飛行）
      const angle = t * 0.002
      const radius = 20
      
      const position: [number, number, number] = [
        currentPos[0] + radius * Math.cos(angle),
        currentPos[1] + Math.sin(t * 0.001) * 5, // 高度變化
        currentPos[2] + radius * Math.sin(angle)
      ]

      plannedRoute.push(position)

      // 計算每個位置的預測信心度
      const confidence = Math.max(0.7, 1 - i * 0.01)
      const handoverProbability = Math.random() * 0.4

      predictedPath.push({
        position,
        timestamp: Date.now() + t * 1000,
        confidence,
        handoverProbability
      })
    }

    return {
      currentPosition: currentPos,
      predictedPath,
      plannedRoute
    }
  }

  // 生成換手點預測
  const generateHandoverPoints = (
    satPredictions: SatellitePrediction[],
    uavPred: UAVPrediction
  ): HandoverPoint[] => {
    const points: HandoverPoint[] = []
    
    // 分析衛星對之間的潛在換手點
    for (let i = 0; i < satPredictions.length; i++) {
      for (let j = i + 1; j < satPredictions.length; j++) {
        const sat1 = satPredictions[i]
        const sat2 = satPredictions[j]
        
        // 找到兩顆衛星軌道的交叉點或最適換手點
        for (let k = 0; k < Math.min(sat1.predictedPath.length, sat2.predictedPath.length); k += 5) {
          const point1 = sat1.predictedPath[k]
          const point2 = sat2.predictedPath[k]
          const uavPoint = uavPred.predictedPath[Math.floor(k * uavPred.predictedPath.length / sat1.predictedPath.length)]
          
          if (!uavPoint) continue
          
          // 計算換手的可行性
          const dist1 = calculateDistance(point1.position, uavPoint.position)
          const dist2 = calculateDistance(point2.position, uavPoint.position)
          
          // 如果距離合適且信號強度變化明顯，則為潛在換手點
          if (dist1 > 30 && dist2 < 25 && Math.abs(point1.confidence - point2.confidence) > 0.2) {
            points.push({
              position: uavPoint.position,
              timestamp: point1.timestamp,
              fromSatellite: sat1.satelliteId,
              toSatellite: sat2.satelliteId,
              confidence: (point1.confidence + point2.confidence) / 2,
              type: point2.confidence > point1.confidence ? 'optimal' : 'predicted'
            })
          }
        }
      }
    }
    
    return points
  }

  // 距離計算輔助函數
  const calculateDistance = (pos1: [number, number, number], pos2: [number, number, number]): number => {
    return Math.sqrt(
      (pos1[0] - pos2[0])**2 + 
      (pos1[1] - pos2[1])**2 + 
      (pos1[2] - pos2[2])**2
    )
  }

  // 更新預測數據
  useEffect(() => {
    if (!enabled || !satellites.length) return

    console.log('生成3D預測路徑數據')
    
    // 生成衛星預測
    const satPredictions = satellites.slice(0, 8).map(generateSatellitePrediction)
    setSatellitePredictions(satPredictions)
    
    // 生成UAV預測（如果有選中的UAV）
    if (selectedUAV) {
      const uavPred = generateUAVPrediction(selectedUAV)
      setUAVPrediction(uavPred)
      
      // 生成換手點
      const handoverPts = generateHandoverPoints(satPredictions, uavPred)
      setHandoverPoints(handoverPts)
    }
  }, [enabled, satellites, selectedUAV, predictionTimeHorizon])

  // 動畫更新
  useFrame((state) => {
    if (!enabled) return
    
    setAnimationTime(state.clock.getElapsedTime())
    
    // 更新預測路徑的動畫效果
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.getElapsedTime() * 0.05
    }
  })

  // 生成增強的衛星預測路徑
  const enhancedSatelliteVisualization = useMemo(() => {
    return satellitePredictions.map((satPred, index) => {
      const points = satPred.predictedPath.map(p => new THREE.Vector3(...p.position))
      
      // 動態顏色基於信號強度和時間
      const colors = satPred.predictedPath.map((p, i) => {
        const confidence = p.confidence
        const timeProgress = i / satPred.predictedPath.length
        
        // 強信號：亮藍色到綠色，弱信號：黃色到紅色
        if (confidence > 0.8) {
          return new THREE.Color().setHSL(0.6 - timeProgress * 0.2, 0.8, 0.6) // 藍綠漸變
        } else if (confidence > 0.6) {
          return new THREE.Color().setHSL(0.16, 0.9, 0.6) // 金黃色
        } else {
          return new THREE.Color().setHSL(0.02 + timeProgress * 0.1, 0.9, 0.5) // 橙紅漸變
        }
      })

      const currentPos = satPred.currentPosition
      const futurePos = satPred.predictedPath[Math.floor(satPred.predictedPath.length * 0.3)]?.position || currentPos

      return (
        <group key={`enhanced-sat-${index}`}>
          {/* 主軌道線 */}
          <Line
            points={points}
            color={colors}
            lineWidth={6}
            dashed={false}
          />
          
          {/* 衛星當前位置標記 */}
          <group position={currentPos}>
            <Sphere args={[3, 16, 16]}>
              <meshStandardMaterial 
                color="#00aaff" 
                emissive="#0066cc"
                emissiveIntensity={0.4}
              />
            </Sphere>
            <Ring args={[4, 8, 32]} rotation={[Math.PI/2, 0, 0]}>
              <meshBasicMaterial 
                color="#00aaff" 
                transparent 
                opacity={0.3 + Math.sin(animationTime * 2) * 0.2} 
              />
            </Ring>
          </group>

          {/* 信號覆蓋範圍可視化 */}
          <group position={currentPos}>
            <Sphere args={[20, 16, 16]}>
              <meshBasicMaterial 
                color="#00aaff" 
                transparent 
                opacity={0.1}
                wireframe={true}
              />
            </Sphere>
            <Sphere args={[35, 16, 16]}>
              <meshBasicMaterial 
                color="#ffaa00" 
                transparent 
                opacity={0.05}
                wireframe={true}
              />
            </Sphere>
          </group>

          {/* 未來位置指示器 */}
          {futurePos && (
            <group position={futurePos}>
              <Cone args={[2, 6, 8]}>
                <meshStandardMaterial 
                  color="#ffaa00" 
                  emissive="#ff6600"
                  emissiveIntensity={0.3}
                />
              </Cone>
              <Text
                position={[0, 10, 0]}
                fontSize={2}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
              >
                {`衛星${index + 1} +90s`}
              </Text>
            </group>
          )}

          {/* 衛星ID標籤 */}
          <Text
            position={[currentPos[0], currentPos[1] + 8, currentPos[2]]}
            fontSize={2.5}
            color="#ffffff"
            anchorX="center"
            anchorY="middle"
          >
            🛰️ {satPred.satelliteId}
          </Text>
        </group>
      )
    })
  }, [satellitePredictions, animationTime])

  // 增強的UAV預測路徑
  const enhancedUAVVisualization = useMemo(() => {
    if (!uavPrediction) return null

    const points = uavPrediction.predictedPath.map(p => new THREE.Vector3(...p.position))
    
    // UAV路徑顏色：基於時間和信心度變化
    const colors = uavPrediction.predictedPath.map((p, i) => {
      const timeProgress = i / uavPrediction.predictedPath.length
      const confidence = p.confidence
      
      // 近期預測：高亮綠色，遠期預測：漸變到橙色
      return new THREE.Color().setHSL(
        0.3 - timeProgress * 0.2, // 綠色到橙色
        0.8, 
        0.5 + confidence * 0.3
      )
    })

    const currentPos = uavPrediction.currentPosition
    const nearFuturePos = uavPrediction.predictedPath[5]?.position || currentPos
    const farFuturePos = uavPrediction.predictedPath[15]?.position || currentPos

    return (
      <group>
        {/* UAV預測路徑主線 */}
        <Line
          points={points}
          color={colors}
          lineWidth={5}
          dashed={true}
          dashSize={3}
          gapSize={1}
        />
        
        {/* UAV當前位置強化標記 */}
        <group position={currentPos}>
          <Sphere args={[2.5, 12, 12]}>
            <meshStandardMaterial 
              color="#00ff80" 
              emissive="#00cc60"
              emissiveIntensity={0.5}
            />
          </Sphere>
          
          {/* 旋轉光環 */}
          <Ring args={[3, 5, 16]} rotation={[Math.PI/2, animationTime, 0]}>
            <meshBasicMaterial 
              color="#00ff80" 
              transparent 
              opacity={0.6}
            />
          </Ring>
          <Ring args={[5, 7, 16]} rotation={[Math.PI/2, -animationTime * 1.5, 0]}>
            <meshBasicMaterial 
              color="#80ff00" 
              transparent 
              opacity={0.4}
            />
          </Ring>

          {/* UAV標籤 */}
          <Text
            position={[0, 8, 0]}
            fontSize={2.5}
            color="#00ff80"
            anchorX="center"
            anchorY="middle"
          >
            🚁 UAV 當前位置
          </Text>
        </group>

        {/* 近期位置預測（30秒後） */}
        <group position={nearFuturePos}>
          <Cylinder args={[1.5, 3, 4, 8]}>
            <meshStandardMaterial 
              color="#ffcc00" 
              emissive="#ff9900"
              emissiveIntensity={0.3}
            />
          </Cylinder>
          <Text
            position={[0, 6, 0]}
            fontSize={2}
            color="#ffcc00"
            anchorX="center"
            anchorY="middle"
          >
            +30s
          </Text>
        </group>

        {/* 遠期位置預測（90秒後） */}
        <group position={farFuturePos}>
          <Cone args={[2, 5, 6]}>
            <meshStandardMaterial 
              color="#ff6600" 
              emissive="#ff3300"
              emissiveIntensity={0.4}
            />
          </Cone>
          <Text
            position={[0, 8, 0]}
            fontSize={2}
            color="#ff6600"
            anchorX="center"
            anchorY="middle"
          >
            +90s
          </Text>
        </group>

        {/* UAV預測範圍圓圈 */}
        {uavPrediction.predictedPath.slice(0, 20).map((point, i) => (
          <Ring 
            key={`uav-range-${i}`}
            args={[8, 10, 16]} 
            position={point.position}
            rotation={[Math.PI/2, 0, 0]}
          >
            <meshBasicMaterial 
              color="#00ff80" 
              transparent 
              opacity={0.05 * (1 - i / 20)}
            />
          </Ring>
        ))}
      </group>
    )
  }, [uavPrediction, animationTime])

  // 增強的換手點標記
  const enhancedHandoverMarkers = useMemo(() => {
    return handoverPoints.map((point, index) => {
      const color = point.type === 'optimal' ? '#00ff88' : 
                   point.type === 'critical' ? '#ff4444' : '#ffaa00'
      
      const timeToHandover = (point.timestamp - Date.now()) / 1000
      const urgency = Math.max(0, 1 - timeToHandover / 30) // 30秒內的緊急度
      
      return (
        <group key={`enhanced-handover-${index}`} position={point.position}>
          {/* 主要換手標記 */}
          <Sphere args={[3, 20, 20]}>
            <meshStandardMaterial 
              color={color} 
              emissive={color}
              emissiveIntensity={0.4 + urgency * 0.4}
              transparent
              opacity={0.8}
            />
          </Sphere>
          
          {/* 脈衝效果 */}
          <Sphere args={[3 + Math.sin(animationTime * 4) * 2, 16, 16]}>
            <meshBasicMaterial 
              color={color} 
              transparent
              opacity={0.2 + urgency * 0.3}
              wireframe={true}
            />
          </Sphere>
          
          {/* 倒計時環 */}
          <Ring args={[5, 8, 32]} rotation={[Math.PI/2, 0, 0]}>
            <meshBasicMaterial 
              color={timeToHandover < 10 ? '#ff0000' : color} 
              transparent
              opacity={0.6}
            />
          </Ring>
          
          {/* 換手信息面板 */}
          <group position={[0, 12, 0]}>
            <Text
              fontSize={2.5}
              color={color}
              anchorX="center"
              anchorY="middle"
            >
              🔄 換手點 #{index + 1}
            </Text>
            <Text
              position={[0, -3, 0]}
              fontSize={2}
              color="#ffffff"
              anchorX="center"
              anchorY="middle"
            >
              {`${point.fromSatellite} → ${point.toSatellite}`}
            </Text>
            <Text
              position={[0, -6, 0]}
              fontSize={1.8}
              color={timeToHandover < 10 ? '#ff4444' : '#ffcc00'}
              anchorX="center"
              anchorY="middle"
            >
              ⏰ T-{Math.max(0, Math.floor(timeToHandover))}s
            </Text>
            <Text
              position={[0, -9, 0]}
              fontSize={1.5}
              color="#cccccc"
              anchorX="center"
              anchorY="middle"
            >
              信心度: {(point.confidence * 100).toFixed(0)}%
            </Text>
          </group>
          
          {/* 連接線到相關衛星 */}
          {satellitePredictions.map((sat, satIndex) => {
            if (sat.satelliteId === point.fromSatellite || sat.satelliteId === point.toSatellite) {
              const isFrom = sat.satelliteId === point.fromSatellite
              const lineColor = isFrom ? '#ff6600' : '#00ff66'
              const satPos = sat.currentPosition
              
              return (
                <Line
                  key={`handover-line-${index}-${satIndex}`}
                  points={[new THREE.Vector3(...point.position), new THREE.Vector3(...satPos)]}
                  color={lineColor}
                  lineWidth={2}
                  dashed={true}
                  dashSize={2}
                  gapSize={1}
                />
              )
            }
            return null
          })}
        </group>
      )
    })
  }, [handoverPoints, animationTime, satellitePredictions])

  if (!enabled) return null

  return (
    <group ref={groupRef}>
      {/* 增強的衛星預測路徑 */}
      {enhancedSatelliteVisualization}
      
      {/* 增強的UAV預測路徑 */}
      {enhancedUAVVisualization}
      
      {/* 增強的換手點標記 */}
      {enhancedHandoverMarkers}
      
      {/* 主標題 */}
      <group position={[0, 80, 0]}>
        <Text
          fontSize={4}
          color="#40e0ff"
          anchorX="center"
          anchorY="middle"
        >
          🔮 IEEE INFOCOM 2024 預測系統
        </Text>
        <Text
          position={[0, -6, 0]}
          fontSize={2.5}
          color="#ffffff"
          anchorX="center"
          anchorY="middle"
        >
          衛星軌道 & UAV 路徑實時預測
        </Text>
      </group>
      
      {/* 增強圖例面板 */}
      <group position={[-60, 60, 0]}>
        <Text
          position={[0, 15, 0]}
          fontSize={3}
          color="#ffcc00"
          anchorX="left"
          anchorY="middle"
        >
          📊 圖例說明
        </Text>
        
        <Text
          position={[0, 10, 0]}
          fontSize={2.2}
          color="#00aaff"
          anchorX="left"
          anchorY="middle"
        >
          🛰️ 藍色軌道 - 衛星預測路徑
        </Text>
        <Text
          position={[2, 7, 0]}
          fontSize={1.8}
          color="#cccccc"
          anchorX="left"
          anchorY="middle"
        >
          • 實心球: 當前位置  • 錐形: 90秒後位置
        </Text>
        
        <Text
          position={[0, 3, 0]}
          fontSize={2.2}
          color="#00ff80"
          anchorX="left"
          anchorY="middle"
        >
          🚁 綠色虛線 - UAV 預測航線
        </Text>
        <Text
          position={[2, 0, 0]}
          fontSize={1.8}
          color="#cccccc"
          anchorX="left"
          anchorY="middle"
        >
          • 圓柱: 30秒後位置  • 錐形: 90秒後位置
        </Text>
        
        <Text
          position={[0, -4, 0]}
          fontSize={2.2}
          color="#00ff88"
          anchorX="left"
          anchorY="middle"
        >
          🔄 換手預測點
        </Text>
        <Text
          position={[2, -7, 0]}
          fontSize={1.8}
          color="#cccccc"
          anchorX="left"
          anchorY="middle"
        >
          • 綠色: 最佳  • 黃色: 一般  • 紅色: 緊急
        </Text>
        
        <Text
          position={[0, -11, 0]}
          fontSize={2}
          color="#ffaa00"
          anchorX="left"
          anchorY="middle"
        >
          📡 信號覆蓋範圍 (透明球體)
        </Text>
      </group>
      
      {/* 性能統計面板 */}
      <group position={[40, 60, 0]}>
        <Text
          position={[0, 15, 0]}
          fontSize={3}
          color="#ff88aa"
          anchorX="left"
          anchorY="middle"
        >
          📈 預測統計
        </Text>
        
        <Text
          position={[0, 10, 0]}
          fontSize={2}
          color="#ffffff"
          anchorX="left"
          anchorY="middle"
        >
          活躍衛星: {satellitePredictions.length}
        </Text>
        
        <Text
          position={[0, 7, 0]}
          fontSize={2}
          color="#ffffff"
          anchorX="left"
          anchorY="middle"
        >
          預測換手點: {handoverPoints.length}
        </Text>
        
        <Text
          position={[0, 4, 0]}
          fontSize={2}
          color="#ffffff"
          anchorX="left"
          anchorY="middle"
        >
          預測時間範圍: {predictionTimeHorizon}秒
        </Text>
        
        <Text
          position={[0, 1, 0]}
          fontSize={2}
          color={handoverPoints.some(p => (p.timestamp - Date.now()) / 1000 < 10) ? '#ff4444' : '#00ff88'}
          anchorX="left"
          anchorY="middle"
        >
          {handoverPoints.some(p => (p.timestamp - Date.now()) / 1000 < 10) 
            ? '⚠️ 緊急換手預警' 
            : '✅ 系統運行正常'}
        </Text>
      </group>
    </group>
  )
}

export default PredictionPath3D