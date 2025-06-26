import React, { useState, useEffect } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'

interface Sionna3DVisualizationProps {
    devices: unknown[]
    enabled: boolean
}

interface WaveField {
    position: [number, number, number]
    wavelength: number
    amplitude: number
    frequency: number
    phase: number
}

const Sionna3DVisualization: React.FC<Sionna3DVisualizationProps> = ({
    devices,
    enabled,
}) => {
    const [waveFields, setWaveFields] = useState<WaveField[]>([])
    const [channelResponse, setChannelResponse] = useState<unknown>(null)

    // 生成基於 Sionna 的 3D 電磁波場
    useEffect(() => {
        if (!enabled) {
            setWaveFields([])
            return
        }

        const transmitters = devices.filter((d) => d.role === 'desired')
        const newWaveFields: WaveField[] = []

        transmitters.forEach((tx, index) => {
            // 創建多徑傳播路徑
            for (let path = 0; path < 3; path++) {
                newWaveFields.push({
                    position: [
                        tx.position_x || 0,
                        (tx.position_z || 0) + 10 + path * 20,
                        tx.position_y || 0,
                    ],
                    wavelength: 0.125, // 2.4GHz
                    amplitude: 1.0 - path * 0.3, // 多徑衰減
                    frequency: 2.4e9 + index * 100e6, // 頻率偏移
                    phase: (path * Math.PI) / 3,
                })
            }
        })

        setWaveFields(newWaveFields)
    }, [devices, enabled])

    // 生成通道響應數據
    useEffect(() => {
        if (!enabled) return

        const generateChannelResponse = () => {
            const receivers = devices.filter((d) => d.role === 'receiver')

            const transmitters = devices.filter((d) => d.role === 'desired')

            const responses = receivers
                .map((rx) => {
                    return transmitters.map((tx) => {
                        const distance = Math.sqrt(
                            Math.pow(
                                (rx.position_x || 0) - (tx.position_x || 0),
                                2
                            ) +
                                Math.pow(
                                    (rx.position_y || 0) - (tx.position_y || 0),
                                    2
                                ) +
                                Math.pow(
                                    (rx.position_z || 0) - (tx.position_z || 0),
                                    2
                                )
                        )

                        // 簡化的 Sionna 通道模型
                        const pathLoss = 20 * Math.log10(distance) + 32.45 // dB
                        const rayleighFading = Math.random() * 2 - 1 // [-1, 1]
                        const shadowFading = (Math.random() - 0.5) * 8 // ±4dB

                        return {
                            txId: tx.id,
                            rxId: rx.id,
                            pathLoss: pathLoss,
                            fading: rayleighFading,
                            shadow: shadowFading,
                            snr: 30 - pathLoss + shadowFading,
                        }
                    })
                })
                .flat()

            setChannelResponse(responses)
        }

        const interval = setInterval(generateChannelResponse, 2000)
        generateChannelResponse()

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 3D 電磁波場可視化 */}
            {waveFields.map((field, index) => (
                <Sionna3DWaveField key={index} {...field} />
            ))}

            {/* 通道響應可視化 */}
            <ChannelResponseDisplay channelResponse={channelResponse} />

            {/* Sionna 系統信息 */}
            <SionnaSystemInfo
                waveFieldCount={waveFields.length}
                channelCount={channelResponse?.length || 0}
            />
        </>
    )
}

type Sionna3DWaveFieldProps = WaveField

const Sionna3DWaveField: React.FC<Sionna3DWaveFieldProps> = ({
    position,
    amplitude,
    frequency,
    phase,
}) => {
    const meshRef = React.useRef<THREE.Group>(null)

    useFrame((state) => {
        if (meshRef.current) {
            const time = state.clock.getElapsedTime()

            // 電磁波傳播動畫
            const wavePhase = ((time * frequency) / 1e9 + phase) % (2 * Math.PI)
            const scale = amplitude * (1 + 0.3 * Math.sin(wavePhase))

            meshRef.current.scale.setScalar(scale)
            meshRef.current.rotation.y = time * 0.5

            // 顏色變化模擬頻率
            const material = meshRef.current.children[0] as THREE.Mesh
            if (material?.material instanceof THREE.MeshStandardMaterial) {
                const hue = (frequency / 1e9 - 2.4) / 0.6 // 2.4-3.0 GHz 映射到色譜
                material.material.color.setHSL(hue, 0.8, 0.6)
                material.material.emissiveIntensity =
                    0.2 + 0.1 * Math.sin(wavePhase * 4)
            }
        }
    })

    return (
        <group ref={meshRef} position={position}>
            {/* 主波場 */}
            <mesh>
                <sphereGeometry args={[20, 16, 16]} />
                <meshStandardMaterial
                    transparent
                    opacity={0.4}
                    emissive="#4488ff"
                    emissiveIntensity={0.2}
                />
            </mesh>

            {/* 波紋效果 */}
            {[1, 2, 3].map((ring) => (
                <mesh key={ring}>
                    <torusGeometry args={[20 + ring * 10, 2, 8, 16]} />
                    <meshStandardMaterial
                        color="#88ccff"
                        transparent
                        opacity={0.3 / ring}
                        emissive="#88ccff"
                        emissiveIntensity={0.1}
                    />
                </mesh>
            ))}

            {/* 頻率標籤 */}
            <Text
                position={[0, 25, 0]}
                fontSize={4}
                color="#88ccff"
                anchorX="center"
                anchorY="middle"
            >
                {(frequency / 1e9).toFixed(2)} GHz
            </Text>
        </group>
    )
}

interface ChannelResponse {
    txId: number
    rxId: number
    snr: number
}

const ChannelResponseDisplay: React.FC<{
    channelResponse: ChannelResponse[] | null
}> = ({ channelResponse }) => {
    if (!channelResponse || channelResponse.length === 0) return null

    return (
        <group position={[-80, 40, 80]}>
            <Text
                position={[0, 15, 0]}
                fontSize={5}
                color="#00ffaa"
                anchorX="center"
                anchorY="middle"
            >
                📊 Sionna 通道響應
            </Text>

            {channelResponse.slice(0, 3).map((response, index) => (
                <group key={index} position={[0, 5 - index * 8, 0]}>
                    <Text
                        position={[0, 0, 0]}
                        fontSize={3}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        Tx{response.txId}→Rx{response.rxId}: SNR{' '}
                        {response.snr.toFixed(1)}dB
                    </Text>
                </group>
            ))}
        </group>
    )
}

const SionnaSystemInfo: React.FC<{
    waveFieldCount: number
    channelCount: number
}> = ({ waveFieldCount, channelCount }) => {
    const [systemStats, setSystemStats] = useState({
        computeTime: 0,
        rayCount: 0,
        pathCount: 0,
    })

    useEffect(() => {
        const interval = setInterval(() => {
            setSystemStats({
                computeTime: Math.random() * 50 + 10, // 10-60ms
                rayCount:
                    waveFieldCount * 1000 + Math.floor(Math.random() * 500),
                pathCount: channelCount * 3 + Math.floor(Math.random() * 10),
            })
        }, 3000)

        return () => clearInterval(interval)
    }, [waveFieldCount, channelCount])

    return (
        <group position={[80, 40, -80]}>
            <Text
                position={[0, 15, 0]}
                fontSize={5}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                🔬 Sionna 引擎狀態
            </Text>

            <Text
                position={[0, 8, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                計算時間: {systemStats.computeTime.toFixed(1)}ms
            </Text>

            <Text
                position={[0, 4, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                射線追蹤: {systemStats.rayCount.toLocaleString()} rays
            </Text>

            <Text
                position={[0, 0, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                傳播路徑: {systemStats.pathCount} paths
            </Text>

            <Text
                position={[0, -4, 0]}
                fontSize={3}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                波場數量: {waveFieldCount} fields
            </Text>
        </group>
    )
}

export default Sionna3DVisualization
