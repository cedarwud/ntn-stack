import React, { useState, useEffect } from 'react'
import { Text } from '@react-three/drei'

interface Device {
    id: string | number;
    role?: string;
    position_x?: number;
    position_y?: number;
    position_z?: number;
    name?: string;
    [key: string]: unknown;
}

interface RealTimeMetricsProps {
    devices: Device[]
    enabled: boolean
}

interface MetricData {
    timestamp: string
    throughput: number
    latency: number
    packetLoss: number
    signalStrength: number
    interferenceLevel: number
    energyConsumption: number
    spectralEfficiency: number
}

interface DeviceMetrics {
    deviceId: string | number
    deviceName: string
    role: string
    metrics: MetricData
    position: [number, number, number]
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({ devices, enabled }) => {
    const [deviceMetrics, setDeviceMetrics] = useState<DeviceMetrics[]>([])
    const [networkMetrics, setNetworkMetrics] = useState<MetricData | null>(null)

    // 生成即時設備性能指標
    useEffect(() => {
        if (!enabled) {
            setDeviceMetrics([])
            setNetworkMetrics(null)
            return
        }

        const updateMetrics = () => {
            const activeDevices = devices.filter(d => d.role !== 'jammer')
            
            const newDeviceMetrics: DeviceMetrics[] = activeDevices.map(device => {
                // 模擬基於設備角色的性能指標
                const baseMetrics = generateBaseMetrics(device.role)
                
                // 考慮干擾影響
                const jammerDevices = devices.filter(d => d.role === 'jammer')
                const interferenceImpact = calculateInterferenceImpact(device, jammerDevices)
                
                return {
                    deviceId: device.id,
                    deviceName: device.name || `${device.role}-${device.id}`,
                    role: device.role,
                    metrics: {
                        ...baseMetrics,
                        signalStrength: baseMetrics.signalStrength - interferenceImpact.signalDegradation,
                        interferenceLevel: interferenceImpact.interferenceLevel,
                        throughput: baseMetrics.throughput * (1 - interferenceImpact.throughputLoss),
                        latency: baseMetrics.latency * (1 + interferenceImpact.latencyIncrease),
                        timestamp: new Date().toISOString()
                    },
                    position: [
                        device.position_x || 0,
                        (device.position_z || 0) + 30,
                        device.position_y || 0
                    ]
                }
            })
            
            setDeviceMetrics(newDeviceMetrics)
            
            // 計算網路整體指標
            const overallMetrics = calculateNetworkMetrics(newDeviceMetrics)
            setNetworkMetrics(overallMetrics)
        }

        updateMetrics()
        const interval = setInterval(updateMetrics, 1500) // 每1.5秒更新

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 設備級指標顯示 */}
            {deviceMetrics.map((deviceMetric) => (
                <DeviceMetricDisplay
                    key={deviceMetric.deviceId}
                    deviceMetric={deviceMetric}
                />
            ))}
            
            {/* 網路級指標顯示 */}
            {networkMetrics && (
                <NetworkMetricDisplay metrics={networkMetrics} />
            )}
            
            {/* 性能指標圖例 */}
            <MetricsLegend />
        </>
    )
}

// 生成基於設備角色的基礎指標
const generateBaseMetrics = (role: string): MetricData => {
    const base = {
        timestamp: new Date().toISOString(),
        throughput: 0,
        latency: 0,
        packetLoss: 0,
        signalStrength: 0,
        interferenceLevel: 0,
        energyConsumption: 0,
        spectralEfficiency: 0
    }

    switch (role) {
        case 'receiver':
            return {
                ...base,
                throughput: 80 + Math.random() * 40, // 80-120 Mbps
                latency: 10 + Math.random() * 20, // 10-30 ms
                packetLoss: Math.random() * 2, // 0-2%
                signalStrength: -60 + Math.random() * 20, // -60 to -40 dBm
                energyConsumption: 2 + Math.random() * 3, // 2-5 W
                spectralEfficiency: 3 + Math.random() * 2 // 3-5 bit/s/Hz
            }
        case 'desired':
            return {
                ...base,
                throughput: 150 + Math.random() * 100, // 150-250 Mbps
                latency: 5 + Math.random() * 10, // 5-15 ms
                packetLoss: Math.random() * 1, // 0-1%
                signalStrength: -40 + Math.random() * 15, // -40 to -25 dBm
                energyConsumption: 10 + Math.random() * 20, // 10-30 W
                spectralEfficiency: 4 + Math.random() * 3 // 4-7 bit/s/Hz
            }
        default:
            return base
    }
}

// 計算干擾影響
const calculateInterferenceImpact = (device: Device, jammers: Device[]) => {
    let totalInterference = 0
    let signalDegradation = 0
    let throughputLoss = 0
    let latencyIncrease = 0

    jammers.forEach(jammer => {
        const distance = Math.sqrt(
            Math.pow((device.position_x || 0) - (jammer.position_x || 0), 2) +
            Math.pow((device.position_y || 0) - (jammer.position_y || 0), 2)
        )

        if (distance < 100) { // 100m 干擾範圍
            const interferenceStrength = Math.max(0, 1 - distance / 100)
            totalInterference += interferenceStrength * 30 // 最大30dB干擾
            signalDegradation += interferenceStrength * 10 // 信號衰減
            throughputLoss += interferenceStrength * 0.3 // 30% 吞吐量損失
            latencyIncrease += interferenceStrength * 0.5 // 50% 延遲增加
        }
    })

    return {
        interferenceLevel: Math.min(totalInterference, 50), // 最大50dB
        signalDegradation: Math.min(signalDegradation, 20),
        throughputLoss: Math.min(throughputLoss, 0.8), // 最大80%損失
        latencyIncrease: Math.min(latencyIncrease, 2.0) // 最大2倍延遲
    }
}

// 計算網路整體指標
const calculateNetworkMetrics = (deviceMetrics: DeviceMetrics[]): MetricData => {
    if (deviceMetrics.length === 0) {
        return {
            timestamp: new Date().toISOString(),
            throughput: 0,
            latency: 0,
            packetLoss: 0,
            signalStrength: 0,
            interferenceLevel: 0,
            energyConsumption: 0,
            spectralEfficiency: 0
        }
    }

    const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length
    const sum = (arr: number[]) => arr.reduce((a, b) => a + b, 0)

    return {
        timestamp: new Date().toISOString(),
        throughput: sum(deviceMetrics.map(d => d.metrics.throughput)),
        latency: avg(deviceMetrics.map(d => d.metrics.latency)),
        packetLoss: avg(deviceMetrics.map(d => d.metrics.packetLoss)),
        signalStrength: avg(deviceMetrics.map(d => d.metrics.signalStrength)),
        interferenceLevel: avg(deviceMetrics.map(d => d.metrics.interferenceLevel)),
        energyConsumption: sum(deviceMetrics.map(d => d.metrics.energyConsumption)),
        spectralEfficiency: avg(deviceMetrics.map(d => d.metrics.spectralEfficiency))
    }
}

const DeviceMetricDisplay: React.FC<{ deviceMetric: DeviceMetrics }> = ({ deviceMetric }) => {
    const { metrics, position, deviceName, role: _role } = deviceMetric
    
    // 根據性能指標決定顏色
    const getMetricColor = (value: number, type: string) => {
        switch (type) {
            case 'throughput':
                return value > 100 ? '#00ff00' : value > 50 ? '#ffff00' : '#ff0000'
            case 'latency':
                return value < 20 ? '#00ff00' : value < 50 ? '#ffff00' : '#ff0000'
            case 'signal':
                return value > -50 ? '#00ff00' : value > -70 ? '#ffff00' : '#ff0000'
            default:
                return '#ffffff'
        }
    }

    return (
        <group position={position}>
            {/* 設備名稱 */}
            <Text
                position={[0, 15, 0]}
                fontSize={4}
                color="#00aaff"
                anchorX="center"
                anchorY="middle"
            >
                📊 {deviceName}
            </Text>
            
            {/* 吞吐量 */}
            <Text
                position={[0, 10, 0]}
                fontSize={3}
                color={getMetricColor(metrics.throughput, 'throughput')}
                anchorX="center"
                anchorY="middle"
            >
                📈 {metrics.throughput.toFixed(1)} Mbps
            </Text>
            
            {/* 延遲 */}
            <Text
                position={[0, 6, 0]}
                fontSize={3}
                color={getMetricColor(metrics.latency, 'latency')}
                anchorX="center"
                anchorY="middle"
            >
                ⏱️ {metrics.latency.toFixed(1)} ms
            </Text>
            
            {/* 信號強度 */}
            <Text
                position={[0, 2, 0]}
                fontSize={3}
                color={getMetricColor(metrics.signalStrength, 'signal')}
                anchorX="center"
                anchorY="middle"
            >
                📶 {metrics.signalStrength.toFixed(1)} dBm
            </Text>
            
            {/* 干擾等級 */}
            {metrics.interferenceLevel > 5 && (
                <Text
                    position={[0, -2, 0]}
                    fontSize={3}
                    color="#ff4444"
                    anchorX="center"
                    anchorY="middle"
                >
                    ⚠️ 干擾: {metrics.interferenceLevel.toFixed(1)} dB
                </Text>
            )}
        </group>
    )
}

const NetworkMetricDisplay: React.FC<{ metrics: MetricData }> = ({ metrics }) => {
    return (
        <group position={[0, 80, 100]}>
            <Text
                position={[0, 20, 0]}
                fontSize={6}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                🌐 網路整體性能
            </Text>
            
            <Text
                position={[-30, 12, 0]}
                fontSize={4}
                color="#00ff88"
                anchorX="center"
                anchorY="middle"
            >
                總吞吐量: {metrics.throughput.toFixed(1)} Mbps
            </Text>
            
            <Text
                position={[30, 12, 0]}
                fontSize={4}
                color="#88ff00"
                anchorX="center"
                anchorY="middle"
            >
                平均延遲: {metrics.latency.toFixed(1)} ms
            </Text>
            
            <Text
                position={[-30, 6, 0]}
                fontSize={4}
                color="#0088ff"
                anchorX="center"
                anchorY="middle"
            >
                總功耗: {metrics.energyConsumption.toFixed(1)} W
            </Text>
            
            <Text
                position={[30, 6, 0]}
                fontSize={4}
                color="#ff8800"
                anchorX="center"
                anchorY="middle"
            >
                頻譜效率: {metrics.spectralEfficiency.toFixed(2)} bit/s/Hz
            </Text>
            
            <Text
                position={[0, 0, 0]}
                fontSize={3}
                color="#ff4444"
                anchorX="center"
                anchorY="middle"
            >
                平均干擾: {metrics.interferenceLevel.toFixed(1)} dB
            </Text>
        </group>
    )
}

const MetricsLegend: React.FC = () => {
    return (
        <group position={[-100, 20, -100]}>
            <Text
                position={[0, 15, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                📊 性能指標說明
            </Text>
            
            <Text
                position={[0, 10, 0]}
                fontSize={2.5}
                color="#00ff00"
                anchorX="center"
                anchorY="middle"
            >
                🟢 優秀 | 🟡 一般 | 🔴 需改善
            </Text>
            
            <Text
                position={[0, 6, 0]}
                fontSize={2}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                吞吐量: &gt;100Mbps 優秀
            </Text>
            
            <Text
                position={[0, 3, 0]}
                fontSize={2}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                延遲: &lt;20ms 優秀
            </Text>
            
            <Text
                position={[0, 0, 0]}
                fontSize={2}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                信號: &gt;-50dBm 優秀
            </Text>
        </group>
    )
}

export default RealTimeMetrics