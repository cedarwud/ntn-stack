import React, { useRef, useMemo, useEffect, useState } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import { Billboard, Text, Line } from '@react-three/drei'

interface HandoverAnomalyProps {
  enabled: boolean
  devices: any[]
  anomalies?: HandoverAnomaly[]
  fallbackPaths?: FallbackPath[]
}

interface HandoverAnomaly {
  id: string
  type: 'timeout' | 'signal_degradation' | 'target_unavailable' | 'interference_detected' | 'network_congestion'
  severity: 'low' | 'medium' | 'high' | 'critical'
  ue_id: string
  position: [number, number, number]
  affected_satellites: string[]
  timestamp: number
  status: 'active' | 'resolved' | 'escalated'
}

interface FallbackPath {
  id: string
  anomaly_id: string
  strategy: string
  originalPath: [number, number, number][]
  fallbackPath: [number, number, number][]
  status: 'pending' | 'executing' | 'completed' | 'failed'
  confidence: number
}

interface AnomalousUEIndicatorProps {
  position: [number, number, number]
  anomaly: HandoverAnomaly
}

const AnomalousUEIndicator: React.FC<AnomalousUEIndicatorProps> = ({ position, anomaly }) => {
  const meshRef = useRef<THREE.Mesh>(null)
  const [scale, setScale] = useState(1)
  
  // 根據異常嚴重程度確定顏色
  const getAnomalyColor = (severity: string, type: string) => {
    const severityColors = {
      'critical': '#ff0000',
      'high': '#ff4757',
      'medium': '#ffa502',
      'low': '#f1c40f'
    }
    
    const typeColors = {
      'timeout': '#e74c3c',
      'signal_degradation': '#e67e22',
      'target_unavailable': '#8e44ad',
      'interference_detected': '#2980b9',
      'network_congestion': '#27ae60'
    }
    
    return severityColors[severity as keyof typeof severityColors] || 
           typeColors[type as keyof typeof typeColors] || '#ff4757'
  }
  
  // 根據異常類型確定圖示符號
  const getAnomalyIcon = (type: string) => {
    const icons = {
      'timeout': '⏰',
      'signal_degradation': '📶',
      'target_unavailable': '🛑', 
      'interference_detected': '📡',
      'network_congestion': '🚦'
    }
    return icons[type as keyof typeof icons] || '⚠️'
  }
  
  useFrame((state) => {
    if (meshRef.current) {
      // 異常指示器脈衝動畫
      const pulseFactor = Math.sin(state.clock.elapsedTime * 3) * 0.3 + 1
      setScale(pulseFactor)
      
      // 旋轉動畫
      meshRef.current.rotation.y = state.clock.elapsedTime * 2
      
      // 浮動動畫
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.5
    }
  })
  
  const color = getAnomalyColor(anomaly.severity, anomaly.type)
  const icon = getAnomalyIcon(anomaly.type)
  
  return (
    <group position={position}>
      {/* 異常指示器 - 脈衝光圈 */}
      <mesh ref={meshRef} scale={scale}>
        <ringGeometry args={[2, 3, 16]} />
        <meshBasicMaterial 
          color={color} 
          transparent 
          opacity={0.6}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* 內部光圈 */}
      <mesh scale={scale * 0.7}>
        <ringGeometry args={[1, 2, 16]} />
        <meshBasicMaterial 
          color={color} 
          transparent 
          opacity={0.8}
          side={THREE.DoubleSide}
        />
      </mesh>
      
      {/* 中心警告標誌 */}
      <mesh position={[0, 0, 0.1]}>
        <cylinderGeometry args={[0.8, 0.8, 0.2, 8]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} />
      </mesh>
      
      {/* 警告圖示 */}
      <Billboard>
        <Text
          position={[0, 4, 0]}
          fontSize={2}
          color={color}
          anchorX="center"
          anchorY="middle"
          font="/fonts/inter-medium.woff"
        >
          {icon}
        </Text>
      </Billboard>
      
      {/* 異常信息標籤 */}
      <Billboard>
        <Text
          position={[0, -3, 0]}
          fontSize={0.8}
          color="#ffffff"
          anchorX="center"
          anchorY="middle"
          font="/fonts/inter-medium.woff"
          outlineWidth={0.1}
          outlineColor="#000000"
        >
          {`${anomaly.type.toUpperCase()}\n${anomaly.severity.toUpperCase()}\n${anomaly.ue_id}`}
        </Text>
      </Billboard>
      
      {/* 向上發射的警告光束 */}
      <mesh position={[0, 10, 0]}>
        <cylinderGeometry args={[0.1, 0.5, 20, 8]} />
        <meshBasicMaterial 
          color={color} 
          transparent 
          opacity={0.4}
        />
      </mesh>
    </group>
  )
}

interface FallbackPathVisualizationProps {
  originalPath: [number, number, number][]
  fallbackPath: [number, number, number][]
  status: string
  confidence: number
}

const FallbackPathVisualization: React.FC<FallbackPathVisualizationProps> = ({
  originalPath,
  fallbackPath,
  status,
  confidence
}) => {
  const originalLineRef = useRef<THREE.Line>(null)
  const fallbackLineRef = useRef<THREE.Line>(null)
  
  useFrame((state) => {
    // 原始路徑淡化效果
    if (originalLineRef.current) {
      const material = originalLineRef.current.material as THREE.LineBasicMaterial
      material.opacity = 0.3 + Math.sin(state.clock.elapsedTime) * 0.1
    }
    
    // 回退路徑動畫
    if (fallbackLineRef.current) {
      const material = fallbackLineRef.current.material as THREE.LineBasicMaterial
      if (status === 'executing') {
        material.opacity = 0.7 + Math.sin(state.clock.elapsedTime * 3) * 0.3
      }
    }
  })
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return '#ffa502'
      case 'executing': return '#74b9ff'
      case 'completed': return '#00b894'
      case 'failed': return '#e17055'
      default: return '#ddd'
    }
  }
  
  return (
    <group>
      {/* 原始換手路徑 - 顯示為虛線 */}
      <Line
        ref={originalLineRef}
        points={originalPath}
        color="#ff4757"
        lineWidth={2}
        dashed
        dashScale={0.5}
        transparent
        opacity={0.4}
      />
      
      {/* 回退路徑 - 實線 */}
      <Line
        ref={fallbackLineRef}
        points={fallbackPath}
        color={getStatusColor(status)}
        lineWidth={3}
        transparent
        opacity={0.8}
      />
      
      {/* 路徑上的控制點 */}
      {fallbackPath.map((point, index) => (
        <mesh key={index} position={point}>
          <sphereGeometry args={[0.3, 8, 8]} />
          <meshStandardMaterial 
            color={getStatusColor(status)} 
            emissive={getStatusColor(status)} 
            emissiveIntensity={0.2}
          />
        </mesh>
      ))}
      
      {/* 信心度指示器 */}
      <Billboard>
        <Text
          position={[fallbackPath[Math.floor(fallbackPath.length / 2)][0], fallbackPath[Math.floor(fallbackPath.length / 2)][1] + 2, fallbackPath[Math.floor(fallbackPath.length / 2)][2]]}
          fontSize={1}
          color={getStatusColor(status)}
          anchorX="center"
          anchorY="middle"
          font="/fonts/inter-medium.woff"
          outlineWidth={0.05}
          outlineColor="#000000"
        >
          {`信心度: ${(confidence * 100).toFixed(0)}%`}
        </Text>
      </Billboard>
    </group>
  )
}

interface AlternativeSatelliteHighlightProps {
  satellites: { id: string; position: [number, number, number]; selected: boolean }[]
}

const AlternativeSatelliteHighlight: React.FC<AlternativeSatelliteHighlightProps> = ({ satellites }) => {
  return (
    <group>
      {satellites.map((satellite) => (
        <group key={satellite.id} position={satellite.position}>
          {/* 替代衛星高亮圈 */}
          <mesh>
            <torusGeometry args={[3, 0.2, 16, 32]} />
            <meshStandardMaterial 
              color={satellite.selected ? '#00b894' : '#74b9ff'} 
              emissive={satellite.selected ? '#00b894' : '#74b9ff'} 
              emissiveIntensity={0.5}
            />
          </mesh>
          
          {/* 選中指示器 */}
          {satellite.selected && (
            <>
              <Billboard>
                <Text
                  position={[0, 5, 0]}
                  fontSize={1.5}
                  color="#00b894"
                  anchorX="center"
                  anchorY="middle"
                  font="/fonts/inter-medium.woff"
                >
                  ✓ 已選擇
                </Text>
              </Billboard>
              
              {/* 選中衛星的額外光效 */}
              <mesh>
                <sphereGeometry args={[1, 16, 16]} />
                <meshStandardMaterial 
                  color="#00b894" 
                  transparent 
                  opacity={0.3}
                  emissive="#00b894" 
                  emissiveIntensity={0.4}
                />
              </mesh>
            </>
          )}
          
          {/* 衛星ID標籤 */}
          <Billboard>
            <Text
              position={[0, -4, 0]}
              fontSize={0.8}
              color="#ffffff"
              anchorX="center"
              anchorY="middle"
              font="/fonts/inter-medium.woff"
              outlineWidth={0.05}
              outlineColor="#000000"
            >
              {satellite.id}
            </Text>
          </Billboard>
        </group>
      ))}
    </group>
  )
}

const HandoverAnomalyVisualization: React.FC<HandoverAnomalyProps> = ({
  enabled,
  devices,
  anomalies = [],
  fallbackPaths = []
}) => {
  // 模擬異常數據
  const [mockAnomalies, setMockAnomalies] = useState<HandoverAnomaly[]>([])
  const [mockFallbackPaths, setMockFallbackPaths] = useState<FallbackPath[]>([])
  const [alternativeSatellites, setAlternativeSatellites] = useState<any[]>([])
  
  useEffect(() => {
    if (!enabled) return
    
    // 生成模擬異常數據
    const generateMockAnomalies = () => {
      const types: HandoverAnomaly['type'][] = ['timeout', 'signal_degradation', 'target_unavailable', 'interference_detected', 'network_congestion']
      const severities: HandoverAnomaly['severity'][] = ['low', 'medium', 'high', 'critical']
      
      const newAnomalies: HandoverAnomaly[] = []
      const newFallbackPaths: FallbackPath[] = []
      
      // 為前幾個設備生成異常
      devices.slice(0, Math.min(3, devices.length)).forEach((device, index) => {
        if (Math.random() < 0.7) { // 70% 機率生成異常
          const anomaly: HandoverAnomaly = {
            id: `anomaly_${index}`,
            type: types[Math.floor(Math.random() * types.length)],
            severity: severities[Math.floor(Math.random() * severities.length)],
            ue_id: `UE_${device.id || index}`,
            position: [device.x || 0, device.y || 0, device.z || 5],
            affected_satellites: [`SAT_${index + 1}`, `SAT_${index + 2}`],
            timestamp: Date.now(),
            status: Math.random() > 0.3 ? 'active' : 'resolved'
          }
          
          newAnomalies.push(anomaly)
          
          // 為每個異常生成回退路徑
          if (anomaly.status === 'active') {
            const originalPath: [number, number, number][] = [
              [device.x || 0, device.y || 0, device.z || 5],
              [device.x + 10 || 10, device.y + 10 || 10, device.z + 20 || 25],
              [device.x + 20 || 20, device.y + 5 || 5, device.z + 30 || 35]
            ]
            
            const fallbackPathPoints: [number, number, number][] = [
              [device.x || 0, device.y || 0, device.z || 5],
              [device.x - 5 || -5, device.y + 15 || 15, device.z + 15 || 20],
              [device.x + 15 || 15, device.y + 20 || 20, device.z + 25 || 30]
            ]
            
            const fallbackPathObj: FallbackPath = {
              id: `fallback_${index}`,
              anomaly_id: anomaly.id,
              strategy: 'SELECT_ALTERNATIVE_SATELLITE',
              originalPath,
              fallbackPath: fallbackPathPoints,
              status: ['pending', 'executing', 'completed'][Math.floor(Math.random() * 3)] as any,
              confidence: 0.6 + Math.random() * 0.3
            }
            
            newFallbackPaths.push(fallbackPathObj)
          }
        }
      })
      
      setMockAnomalies(newAnomalies)
      setMockFallbackPaths(newFallbackPaths)
      
      // 生成替代衛星
      const satellites = [
        { id: 'SAT_A1', position: [30, 30, 40] as [number, number, number], selected: false },
        { id: 'SAT_B2', position: [-20, 40, 45] as [number, number, number], selected: true },
        { id: 'SAT_C3', position: [40, -30, 35] as [number, number, number], selected: false }
      ]
      setAlternativeSatellites(satellites)
    }
    
    generateMockAnomalies()
    
    // 定期更新異常狀態
    const interval = setInterval(() => {
      setMockAnomalies(prev => prev.map(anomaly => ({
        ...anomaly,
        status: Math.random() > 0.8 ? 'resolved' : anomaly.status
      })))
      
      setMockFallbackPaths(prev => prev.map(path => ({
        ...path,
        status: path.status === 'pending' && Math.random() > 0.7 ? 'executing' :
                path.status === 'executing' && Math.random() > 0.6 ? 'completed' : path.status
      })))
    }, 3000)
    
    return () => clearInterval(interval)
  }, [enabled, devices])
  
  if (!enabled) return null
  
  const activeAnomalies = mockAnomalies.filter(a => a.status === 'active')
  const activeFallbackPaths = mockFallbackPaths.filter(p => p.status !== 'completed')
  
  return (
    <group>
      {/* 異常 UE 指示器 */}
      {activeAnomalies.map(anomaly => (
        <AnomalousUEIndicator
          key={anomaly.id}
          position={anomaly.position}
          anomaly={anomaly}
        />
      ))}
      
      {/* 回退路徑可視化 */}
      {activeFallbackPaths.map(path => (
        <FallbackPathVisualization
          key={path.id}
          originalPath={path.originalPath}
          fallbackPath={path.fallbackPath}
          status={path.status}
          confidence={path.confidence}
        />
      ))}
      
      {/* 替代衛星高亮 */}
      {activeAnomalies.length > 0 && (
        <AlternativeSatelliteHighlight satellites={alternativeSatellites} />
      )}
      
      {/* 環境光增強 - 異常時增加紅色環境光 */}
      {activeAnomalies.some(a => a.severity === 'critical') && (
        <ambientLight color="#ff4757" intensity={0.1} />
      )}
    </group>
  )
}

export default HandoverAnomalyVisualization