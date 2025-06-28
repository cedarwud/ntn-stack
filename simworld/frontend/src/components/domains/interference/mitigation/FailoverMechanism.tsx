import React, { useState, useEffect } from 'react'
import { Line } from '@react-three/drei'

interface Device {
    id: string | number;
    [key: string]: unknown;
}

interface FailoverMechanismProps {
    devices: Device[]
    enabled: boolean
}

interface NetworkConnection {
    id: string
    deviceId: string | number
    type: 'satellite_ntn' | 'mesh_backup' | 'dual_connection'
    status: 'active' | 'standby' | 'failed' | 'switching' | 'recovering'
    quality: {
        signalStrength: number
        latency: number
        bandwidth: number
        reliability: number
        packetLoss: number
    }
    switchCount: number
    lastSwitchTime: number
}


const FailoverMechanism: React.FC<FailoverMechanismProps> = ({
    devices,
    enabled,
}) => {
    const [connections, setConnections] = useState<NetworkConnection[]>([])

    // 監控網路連接和故障轉移
    useEffect(() => {
        if (!enabled) {
            setConnections([])
            return
        }

        const monitorConnections = () => {
            const uavs = devices.filter((d) => d.role === 'receiver')

            setConnections(() => {
                return analyzeConnections(uavs)
            })
        }

        monitorConnections()
        const interval = setInterval(monitorConnections, 2000) // 每2秒監控

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 移除所有文字顯示，只保留網路冗餘線路 */}
            <NetworkRedundancyVisualization
                connections={connections}
                devices={devices}
            />
        </>
    )
}

// 分析連接狀態
const analyzeConnections = (devices: Device[]): NetworkConnection[] => {
    return devices
        .map((device) => {
            // 主要衛星連接
            const satelliteConnection: NetworkConnection = {
                id: `sat_conn_${device.id}`,
                deviceId: device.id,
                type: 'satellite_ntn',
                status: generateConnectionStatus('satellite'),
                quality: generateConnectionQuality('satellite'),
                switchCount: Math.floor(Math.random() * 5),
                lastSwitchTime: Date.now() - Math.random() * 300000,
            }

            // 備用網狀網路連接
            const meshConnection: NetworkConnection = {
                id: `mesh_conn_${device.id}`,
                deviceId: device.id,
                type: 'mesh_backup',
                status: generateConnectionStatus('mesh'),
                quality: generateConnectionQuality('mesh'),
                switchCount: Math.floor(Math.random() * 3),
                lastSwitchTime: Date.now() - Math.random() * 600000,
            }

            return [satelliteConnection, meshConnection]
        })
        .flat()
}

// 生成連接狀態
const generateConnectionStatus = (
    type: 'satellite' | 'mesh'
): NetworkConnection['status'] => {
    const rand = Math.random()
    if (type === 'satellite') {
        if (rand < 0.7) return 'active'
        if (rand < 0.85) return 'standby'
        if (rand < 0.95) return 'switching'
        return 'failed'
    } else {
        if (rand < 0.3) return 'active'
        if (rand < 0.8) return 'standby'
        if (rand < 0.9) return 'switching'
        return 'failed'
    }
}

// 生成連接質量
const generateConnectionQuality = (type: 'satellite' | 'mesh') => {
    const base =
        type === 'satellite'
            ? {
                  signal: -65,
                  latency: 25,
                  bandwidth: 150,
                  reliability: 95,
                  loss: 1,
              }
            : {
                  signal: -75,
                  latency: 15,
                  bandwidth: 50,
                  reliability: 85,
                  loss: 3,
              }

    return {
        signalStrength: base.signal + (Math.random() - 0.5) * 20,
        latency: base.latency + (Math.random() - 0.5) * 10,
        bandwidth: base.bandwidth + (Math.random() - 0.5) * 50,
        reliability: base.reliability + (Math.random() - 0.5) * 10,
        packetLoss: Math.max(0, base.loss + (Math.random() - 0.5) * 4),
    }
}



// 網路冗餘可視化組件
const NetworkRedundancyVisualization: React.FC<{
    connections: NetworkConnection[]
    devices: Device[]
}> = ({ connections, devices }) => {
    return (
        <>
            {devices.map((device) => {
                const deviceConnections = connections.filter(
                    (c) => c.deviceId === device.id
                )
                const primaryConn = deviceConnections.find(
                    (c) => c.type === 'satellite_ntn'
                )
                const backupConn = deviceConnections.find(
                    (c) => c.type === 'mesh_backup'
                )

                if (!primaryConn || !backupConn) return null

                const primaryPos: [number, number, number] = [
                    device.position_x || 0,
                    (device.position_z || 0) + 25,
                    device.position_y || 0,
                ]

                const backupPos: [number, number, number] = [
                    device.position_x || 0,
                    (device.position_z || 0) + 15,
                    device.position_y || 0,
                ]

                return (
                    <Line
                        key={`redundancy_${device.id}`}
                        points={[primaryPos, backupPos]}
                        color={
                            primaryConn.status === 'active'
                                ? '#00ff88'
                                : '#888888'
                        }
                        lineWidth={2}
                        dashed={backupConn.status === 'standby'}
                        transparent
                        opacity={0.6}
                    />
                )
            })}
        </>
    )
}


export default FailoverMechanism
