import React, { useState, useEffect } from 'react'
import { Line } from '@react-three/drei'

interface FailoverMechanismProps {
    devices: unknown[]
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

interface FailoverEvent {
    id: string
    deviceId: string | number
    trigger:
        | 'signal_degradation'
        | 'connection_loss'
        | 'high_packet_loss'
        | 'interference'
        | 'manual'
    fromConnection: 'satellite_ntn' | 'mesh_backup'
    toConnection: 'satellite_ntn' | 'mesh_backup'
    startTime: number
    duration: number
    status: 'detecting' | 'switching' | 'verifying' | 'completed' | 'failed'
    severity: 'low' | 'medium' | 'high' | 'critical'
    progress: number // 0-100
    reason: string
}

interface RecoveryAction {
    id: string
    deviceId: string | number
    action:
        | 'auto_recovery'
        | 'manual_intervention'
        | 'reconfiguration'
        | 'rerouting'
    target: string
    progress: number
    estimatedTime: number
    success: boolean
}

interface FailoverMetrics {
    totalSwitches: number
    successfulSwitches: number
    averageSwitchTime: number
    connectionReliability: number
    networkRedundancy: number
    recoveryRate: number
}

const FailoverMechanism: React.FC<FailoverMechanismProps> = ({
    devices,
    enabled,
}) => {
    const [connections, setConnections] = useState<NetworkConnection[]>([])
     
    const [_failoverEvents, setFailoverEvents] = useState<FailoverEvent[]>([])
     
    const [_recoveryActions, setRecoveryActions] = useState<RecoveryAction[]>(
        []
    )
     
    const [_failoverMetrics, setFailoverMetrics] = useState<FailoverMetrics>({
        totalSwitches: 0,
        successfulSwitches: 0,
        averageSwitchTime: 0,
        connectionReliability: 0,
        networkRedundancy: 0,
        recoveryRate: 0,
    })

    // 監控網路連接和故障轉移
    useEffect(() => {
        if (!enabled) {
            setConnections([])
            setFailoverEvents([])
            setRecoveryActions([])
            return
        }

        const monitorConnections = () => {
            const uavs = devices.filter((d) => d.role === 'receiver')

            setConnections((prevConnections) => {
                const newConnections = analyzeConnections(uavs)
                const newEvents = detectFailoverTriggers(
                    newConnections,
                    prevConnections
                )
                const newActions = executeRecoveryActions(newEvents)

                // 只有在有新事件時才更新
                if (newEvents.length > 0) {
                    setFailoverEvents((prev) => {
                        const updatedEvents = [...prev.slice(-5), ...newEvents]
                        // 計算故障轉移指標
                        const metrics = calculateFailoverMetrics(
                            newConnections,
                            updatedEvents
                        )
                        setFailoverMetrics(metrics)
                        return updatedEvents
                    })
                    setRecoveryActions(newActions)
                } else {
                    // 即使沒有新事件，也要更新指標
                    setFailoverEvents((prev) => {
                        const metrics = calculateFailoverMetrics(
                            newConnections,
                            prev
                        )
                        setFailoverMetrics(metrics)
                        return prev
                    })
                }

                return newConnections
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

const analyzeConnections = (devices: unknown[]): NetworkConnection[] => {
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

// 檢測故障轉移觸發器
const detectFailoverTriggers = (
    currentConnections: NetworkConnection[],
    previousConnections: NetworkConnection[]
): FailoverEvent[] => {
    const events: FailoverEvent[] = []

    currentConnections.forEach((connection) => {
        const previous = previousConnections.find((p) => p.id === connection.id)

        if (shouldTriggerFailover(connection, previous)) {
            const trigger = determineTriggerType(connection, previous)
            const event: FailoverEvent = {
                id: `failover_${connection.deviceId}_${Date.now()}`,
                deviceId: connection.deviceId,
                trigger,
                fromConnection:
                    connection.type === 'satellite_ntn'
                        ? 'satellite_ntn'
                        : 'mesh_backup',
                toConnection:
                    connection.type === 'satellite_ntn'
                        ? 'mesh_backup'
                        : 'satellite_ntn',
                startTime: Date.now(),
                duration: 2000 + Math.random() * 5000, // 2-7秒
                status: 'detecting',
                severity: determineSeverity(trigger, connection),
                progress: 0,
                reason: generateFailoverReason(trigger, connection),
            }

            events.push(event)
        }
    })

    return events
}

// 判斷是否觸發故障轉移
const shouldTriggerFailover = (
    current: NetworkConnection,
    previous?: NetworkConnection
): boolean => {
    if (!previous) return false

    // 信號強度顯著下降
    if (
        current.quality.signalStrength < -85 &&
        previous.quality.signalStrength > -75
    )
        return true

    // 延遲急劇增加
    if (current.quality.latency > 100 && previous.quality.latency < 50)
        return true

    // 丟包率過高
    if (current.quality.packetLoss > 10) return true

    // 連接失敗
    if (current.status === 'failed' && previous.status === 'active') return true

    // 隨機觸發（模擬真實環境）
    return Math.random() < 0.05
}

// 確定觸發類型
const determineTriggerType = (
    current: NetworkConnection,
    previous?: NetworkConnection
): FailoverEvent['trigger'] => {
    if (!previous) return 'manual'

    if (current.quality.signalStrength < -85) return 'signal_degradation'
    if (current.status === 'failed') return 'connection_loss'
    if (current.quality.packetLoss > 10) return 'high_packet_loss'
    if (current.quality.signalStrength < previous.quality.signalStrength - 15)
        return 'interference'

    return 'manual'
}

// 確定嚴重程度
const determineSeverity = (
    trigger: FailoverEvent['trigger'],
    connection: NetworkConnection
): FailoverEvent['severity'] => {
    switch (trigger) {
        case 'connection_loss':
            return 'critical'
        case 'signal_degradation':
            return connection.quality.signalStrength < -90 ? 'high' : 'medium'
        case 'high_packet_loss':
            return connection.quality.packetLoss > 20 ? 'high' : 'medium'
        case 'interference':
            return 'medium'
        default:
            return 'low'
    }
}

// 生成故障轉移原因
const generateFailoverReason = (
    trigger: FailoverEvent['trigger'],
    connection: NetworkConnection
): string => {
    const reasons = {
        signal_degradation: `信號強度下降至 ${connection.quality.signalStrength.toFixed(
            1
        )} dBm`,
        connection_loss: '連接完全中斷，無法恢復',
        high_packet_loss: `丟包率過高 (${connection.quality.packetLoss.toFixed(
            1
        )}%)`,
        interference: '檢測到嚴重干擾源影響',
        manual: '手動觸發故障轉移',
    }

    return reasons[trigger] || '未知原因'
}

// 執行恢復動作
const executeRecoveryActions = (events: FailoverEvent[]): RecoveryAction[] => {
    return events.map((event) => ({
        id: `recovery_${event.id}`,
        deviceId: event.deviceId,
        action: determineRecoveryAction(event),
        target: event.toConnection,
        progress: Math.random() * 100,
        estimatedTime: 3000 + Math.random() * 7000,
        success: Math.random() > 0.1, // 90% 成功率
    }))
}

// 確定恢復動作
const determineRecoveryAction = (
    event: FailoverEvent
): RecoveryAction['action'] => {
    switch (event.severity) {
        case 'critical':
            return 'manual_intervention'
        case 'high':
            return 'reconfiguration'
        case 'medium':
            return 'rerouting'
        default:
            return 'auto_recovery'
    }
}

// 計算故障轉移指標
const calculateFailoverMetrics = (
    connections: NetworkConnection[],
    events: FailoverEvent[]
): FailoverMetrics => {
    const totalSwitches = events.length
    const successfulSwitches = events.filter(
        (e) => e.status === 'completed'
    ).length
    const avgSwitchTime =
        events.reduce((sum, e) => sum + e.duration, 0) / (events.length || 1)

    const activeConnections = connections.filter((c) => c.status === 'active')
    const reliability =
        activeConnections.reduce((sum, c) => sum + c.quality.reliability, 0) /
        (activeConnections.length || 1)

    // 計算設備數量（每個設備有兩個連接：主要和備用）
    const deviceCount = Math.max(1, connections.length / 2)

    return {
        totalSwitches,
        successfulSwitches,
        averageSwitchTime: avgSwitchTime / 1000, // 轉換為秒
        connectionReliability: reliability,
        networkRedundancy: Math.min(
            100,
            (connections.length / deviceCount) * 50
        ),
        recoveryRate:
            totalSwitches > 0
                ? (successfulSwitches / totalSwitches) * 100
                : 100,
    }
}

// 連接狀態可視化組件 (備用)

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const ConnectionStatusVisualization: React.FC<{
    connection: NetworkConnection
    devices: unknown[]
}> = ({ connection, devices }) => {
    const device = devices.find((d) => d.id === connection.deviceId)
    if (!device) return null

    const getStatusColor = (status: NetworkConnection['status']) => {
        switch (status) {
            case 'active':
                return '#00ff00'
            case 'standby':
                return '#ffaa00'
            case 'failed':
                return '#ff0000'
            case 'switching':
                return '#0088ff'
            case 'recovering':
                return '#ff8800'
            default:
                return '#ffffff'
        }
    }

     
    const _getConnectionIcon = (type: NetworkConnection['type']) => {
        switch (type) {
            case 'satellite_ntn':
                return '🛰️'
            case 'mesh_backup':
                return '🕸️'
            case 'dual_connection':
                return '🔗'
            default:
                return '📡'
        }
    }

    const offset = connection.type === 'satellite_ntn' ? 25 : 15

    return (
        <group
            position={[
                device.position_x || 0,
                (device.position_z || 0) + offset,
                device.position_y || 0,
            ]}
        >
            <mesh>
                <boxGeometry args={[8, 4, 8]} />
                <meshStandardMaterial
                    color={getStatusColor(connection.status)}
                    transparent
                    opacity={0.7}
                    emissive={getStatusColor(connection.status)}
                    emissiveIntensity={0.3}
                />
            </mesh>
        </group>
    )
}

// 故障轉移事件可視化組件

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const FailoverEventsVisualization: React.FC<{
    events: FailoverEvent[]
    devices: unknown[]
}> = ({ events, devices }) => {
     
    const _getSeverityColor = (severity: FailoverEvent['severity']) => {
        switch (severity) {
            case 'low':
                return '#88ff88'
            case 'medium':
                return '#ffaa00'
            case 'high':
                return '#ff6600'
            case 'critical':
                return '#ff0000'
            default:
                return '#ffffff'
        }
    }

     
    const _getTriggerIcon = (trigger: FailoverEvent['trigger']) => {
        switch (trigger) {
            case 'signal_degradation':
                return '📶'
            case 'connection_loss':
                return '❌'
            case 'high_packet_loss':
                return '📉'
            case 'interference':
                return '⚡'
            case 'manual':
                return '👤'
            default:
                return '🔄'
        }
    }

    return (
        <>
            {events.map((event) => {
                const device = devices.find((d) => d.id === event.deviceId)
                if (!device) return null

                return (
                    <group
                        key={event.id}
                        position={[
                            device.position_x || 0,
                            (device.position_z || 0) + 45,
                            device.position_y || 0,
                        ]}
                    ></group>
                )
            })}
        </>
    )
}

// 網路冗餘可視化組件

const NetworkRedundancyVisualization: React.FC<{
    connections: NetworkConnection[]
    devices: unknown[]
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

// 恢復動作可視化組件

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const RecoveryActionsVisualization: React.FC<{
    actions: RecoveryAction[]
    devices: unknown[]
}> = ({ actions, devices }) => {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const getActionIcon = (action: RecoveryAction['action']) => {
        switch (action) {
            case 'auto_recovery':
                return '🔄'
            case 'manual_intervention':
                return '👤'
            case 'reconfiguration':
                return '⚙️'
            case 'rerouting':
                return '🛤️'
            default:
                return '🔧'
        }
    }

    return (
        <>
            {actions.map((action) => {
                const device = devices.find((d) => d.id === action.deviceId)
                if (!device) return null

                return (
                    <group
                        key={action.id}
                        position={[
                            device.position_x || 0,
                            (device.position_z || 0) + 35,
                            device.position_y || 0,
                        ]}
                    ></group>
                )
            })}
        </>
    )
}

// 故障轉移指標顯示組件
const FailoverMetricsDisplay: React.FC<{ metrics: FailoverMetrics }> = ({
    metrics,
}) => {
    // This component could display metrics in a future version
    console.log('Metrics:', metrics)
    return <group position={[80, 60, 80]}></group>
}

// Export for potential future use
export { FailoverMetricsDisplay }

// 網路健康狀態組件
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const NetworkHealthStatus: React.FC<{ connections: NetworkConnection[] }> = ({
    connections,
}) => {
    const activeConnections = connections.filter((c) => c.status === 'active')
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const healthScore = (activeConnections.length / connections.length) * 100

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const getHealthColor = (score: number) => {
        if (score > 80) return '#00ff00'
        if (score > 60) return '#ffaa00'
        if (score > 40) return '#ff6600'
        return '#ff0000'
    }

    return <group position={[-80, 60, 80]}></group>
}

// 自動化決策邏輯組件
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const AutomatedDecisionLogic: React.FC<{ events: FailoverEvent[] }> = ({
    events,
}) => {
    const recentEvents = events.slice(-3)

    return (
        <group position={[-80, 60, -80]}>
            {recentEvents.map((event, index) => (
                <group key={event.id} position={[0, 8 - index * 6, 0]}></group>
            ))}
        </group>
    )
}

export default FailoverMechanism
