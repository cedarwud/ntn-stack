import React, { useMemo } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import { Device } from '../../../../types/device'

interface InterferenceOverlayProps {
    devices: Device[]
    enabled: boolean
}

const InterferenceOverlay: React.FC<InterferenceOverlayProps> = React.memo(({
    devices,
    enabled,
}) => {
    // 篩選出干擾源設備 - 使用更穩定的依賴
    const jammerDevices = useMemo(() => {
        if (!devices || !Array.isArray(devices)) {
            return []
        }
        return devices.filter((device) => device && device.role === 'jammer')
    }, [devices])

    if (!enabled || jammerDevices.length === 0) {
        return null
    }

    return (
        <>
            {jammerDevices.map((jammer, index) => (
                <InterferenceZone
                    key={jammer.id || index}
                    position={[
                        jammer.position_x || 0,
                        (jammer.position_z || 0) + 20,
                        jammer.position_y || 0,
                    ]}
                    radius={60} // 干擾範圍半徑
                    intensity={0.8}
                    jammerId={jammer.id}
                    jammerName={jammer.name}
                />
            ))}
        </>
    )
})

interface InterferenceZoneProps {
    position: [number, number, number]
    radius: number
    intensity: number
    jammerId?: string | number
    jammerName?: string
}

const InterferenceZone: React.FC<InterferenceZoneProps> = React.memo(({
    position,
    radius,
    intensity,
     
    jammerId: _jammerId,
    jammerName,
}) => {
    const meshRef = React.useRef<THREE.Mesh>(null)

    // 動畫效果：脈動 - 優化性能
    useFrame((state) => {
        if (meshRef.current) {
            const time = state.clock.getElapsedTime()
            const scale = 1 + Math.sin(time * 2) * 0.1
            meshRef.current.scale.setScalar(scale)

            // 旋轉效果 - 減少更新頻率
            const rotation = time * 0.5
            if (Math.abs(meshRef.current.rotation.y - rotation) > 0.05) {
                meshRef.current.rotation.y = rotation
            }
        }
    })

    return (
        <group position={position}>
            {/* 內圈 - 高強度干擾區 */}
            <mesh ref={meshRef}>
                <sphereGeometry args={[radius * 0.3, 16, 16]} />
                <meshBasicMaterial
                    color="#ff4444"
                    transparent
                    opacity={intensity * 0.4}
                    side={THREE.DoubleSide}
                />
            </mesh>

            {/* 中圈 - 中強度干擾區 */}
            <mesh>
                <sphereGeometry args={[radius * 0.6, 24, 24]} />
                <meshBasicMaterial
                    color="#ff8844"
                    transparent
                    opacity={intensity * 0.25}
                    side={THREE.DoubleSide}
                />
            </mesh>

            {/* 外圈 - 低強度干擾區 */}
            <mesh>
                <sphereGeometry args={[radius, 32, 32]} />
                <meshBasicMaterial
                    color="#ffcc44"
                    transparent
                    opacity={intensity * 0.1}
                    side={THREE.DoubleSide}
                />
            </mesh>

            {/* 干擾波紋效果 */}
            <RippleEffect position={[0, 0, 0]} radius={radius} />

            {/* 干擾源標籤 */}
            {jammerName && (
                <Text
                    position={[0, radius + 15, 0]}
                    fontSize={6}
                    color="#ff4444"
                    anchorX="center"
                    anchorY="middle"
                >
                    🚫 {jammerName}
                </Text>
            )}

            <Text
                position={[0, radius + 8, 0]}
                fontSize={4}
                color="#ffcc44"
                anchorX="center"
                anchorY="middle"
            >
                干擾範圍: {radius}m
            </Text>
        </group>
    )
})

interface RippleEffectProps {
    position: [number, number, number]
    radius: number
}

const RippleEffect: React.FC<RippleEffectProps> = React.memo(({ position, radius }) => {
    const ringsRef = React.useRef<THREE.Group>(null)

    useFrame((state) => {
        if (ringsRef.current) {
            const time = state.clock.getElapsedTime()
            ringsRef.current.children.forEach((ring, index) => {
                const mesh = ring as THREE.Mesh
                const delay = index * 0.5
                const phase = (time + delay) % 3
                const scale = (phase / 3) * radius
                 
                const _opacity = Math.max(0, 1 - phase / 3)

                mesh.scale.setScalar(scale)
                // 避免每幀都修改材質，只在有實際變化時修改
                if (mesh.material instanceof THREE.MeshBasicMaterial) {
                    const newOpacity = _opacity * 0.3
                    if (Math.abs(mesh.material.opacity - newOpacity) > 0.01) {
                        mesh.material.opacity = newOpacity
                    }
                }
            })
        }
    })

    return (
        <group ref={ringsRef} position={position}>
            {[0, 1, 2].map((index) => (
                <mesh key={index}>
                    <ringGeometry args={[0.9, 1, 32]} />
                    <meshBasicMaterial
                        color="#ff6666"
                        transparent
                        opacity={0.3}
                        side={THREE.DoubleSide}
                    />
                </mesh>
            ))}
        </group>
    )
})

export default InterferenceOverlay
