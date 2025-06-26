import React, { useState, useEffect, useRef } from 'react'
import * as THREE from 'three'
import { useFrame } from '@react-three/fiber'
import { Line } from '@react-three/drei'

interface MeshNetworkTopologyProps {
    devices: unknown[]
    enabled: boolean
}

interface NetworkNode {
    id: string | number
    type: 'satellite_gw' | 'mesh_node' | 'uav_relay' | 'ground_station'
    position: [number, number, number]
    status: 'active' | 'inactive' | 'degraded' | 'offline'
    connections: string[]
    metrics: {
        bandwidth: number // Mbps
        latency: number // ms
        packetLoss: number // %
        signalStrength: number // dBm
        hopCount: number
    }
    role: 'primary' | 'backup' | 'relay' | 'edge'
}

interface NetworkLink {
    id: string
    source: string | number
    target: string | number
    type: 'satellite' | 'mesh' | 'backup' | 'direct'
    quality: number // 0-100
    bandwidth: number
    latency: number
    status: 'active' | 'degraded' | 'failed' | 'recovering'
    protocol: 'AODV' | 'OLSR' | 'BATMAN' | '5G_NR'
}

interface RoutingPath {
    id: string
    source: string | number
    destination: string | number
    hops: (string | number)[]
    totalLatency: number
    reliability: number
    load: number
}

const MeshNetworkTopology: React.FC<MeshNetworkTopologyProps> = ({
    devices,
    enabled,
}) => {
    const [networkNodes, setNetworkNodes] = useState<NetworkNode[]>([])
    const [networkLinks, setNetworkLinks] = useState<NetworkLink[]>([])
    const [routingPaths, setRoutingPaths] = useState<RoutingPath[]>([])
    const [_topologyMetrics, setTopologyMetrics] = useState({
        totalNodes: 0,
        activeLinks: 0,
        networkReliability: 0,
        averageLatency: 0,
        routingEfficiency: 0,
        redundancyLevel: 0,
    })

    // 分析網路拓撲
    useEffect(() => {
        if (!enabled) {
            setNetworkNodes([])
            setNetworkLinks([])
            setRoutingPaths([])
            return
        }

        const analyzeNetworkTopology = () => {
            const nodes = createNetworkNodes(devices)
            const links = generateNetworkLinks(nodes)
            const paths = calculateRoutingPaths(nodes, links)

            setNetworkNodes(nodes)
            setNetworkLinks(links)
            setRoutingPaths(paths)

            // 計算拓撲指標

            const _metrics = calculateTopologyMetrics(nodes, links, paths)
            setTopologyMetrics(metrics)
        }

        analyzeNetworkTopology()
        const interval = setInterval(analyzeNetworkTopology, 3000) // 每3秒更新

        return () => clearInterval(interval)
    }, [devices, enabled])

    if (!enabled) return null

    return (
        <>
            {/* 移除所有文字顯示，只保留幾何形狀和連接線 */}
            <SimpleNetworkNodesVisualization nodes={networkNodes} />
            <NetworkLinksVisualization
                links={networkLinks}
                nodes={networkNodes}
            />
            <RoutingPathVisualization
                paths={routingPaths}
                nodes={networkNodes}
            />
            <NetworkCoverageVisualization nodes={networkNodes} />
        </>
    )
}

// 簡化的網路節點可視化組件 - 移除所有文字

const SimpleNetworkNodesVisualization: React.FC<{ nodes: NetworkNode[] }> = ({
    nodes,
}) => {
    const getNodeColor = (type: string, status: string) => {
        if (status === 'failed') return '#ff0000'
        if (status === 'degraded') return '#ffaa00'

        switch (type) {
            case 'satellite_gw':
                return '#00aaff'
            case 'uav_relay':
                return '#00ff88'
            case 'ground_station':
                return '#ffaa00'
            case 'mesh_node':
                return '#ff6b35'
            default:
                return '#ffffff'
        }
    }

    return (
        <>
            {nodes.map((node) => (
                <group key={node.id} position={node.position}>
                    <mesh>
                        <octahedronGeometry args={[8, 0]} />
                        <meshStandardMaterial
                            color={getNodeColor(node.type, node.status)}
                            transparent
                            opacity={0.8}
                            emissive={getNodeColor(node.type, node.status)}
                            emissiveIntensity={0.3}
                        />
                    </mesh>
                </group>
            ))}
        </>
    )
}

// 創建網路節點

const createNetworkNodes = (devices: unknown[]): NetworkNode[] => {
    const nodes: NetworkNode[] = []

    devices.forEach((device) => {
        let nodeType: NetworkNode['type'] = 'mesh_node'
        let role: NetworkNode['role'] = 'edge'

        switch (device.role) {
            case 'desired':
                nodeType = 'satellite_gw'
                role = 'primary'
                break
            case 'receiver':
                nodeType = 'uav_relay'
                role = 'relay'
                break
            case 'jammer':
                // 干擾器不作為網路節點
                return
        }

        const node: NetworkNode = {
            id: device.id,
            type: nodeType,
            position: [
                device.position_x || 0,
                (device.position_z || 0) + 20,
                device.position_y || 0,
            ],
            status: device.enabled ? 'active' : 'inactive',
            connections: [],
            metrics: {
                bandwidth: generateRandomMetric(50, 200),
                latency: generateRandomMetric(10, 100),
                packetLoss: generateRandomMetric(0, 5),
                signalStrength: generateRandomMetric(-70, -30),
                hopCount: generateRandomMetric(1, 4),
            },
            role,
        }

        nodes.push(node)
    })

    return nodes
}

// 生成網路連接
const generateNetworkLinks = (nodes: NetworkNode[]): NetworkLink[] => {
    const links: NetworkLink[] = []

    for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
            const nodeA = nodes[i]
            const nodeB = nodes[j]

            const distance = Math.sqrt(
                Math.pow(nodeA.position[0] - nodeB.position[0], 2) +
                    Math.pow(nodeA.position[2] - nodeB.position[2], 2)
            )

            // 根據距離決定是否建立連接
            if (distance < 100) {
                const linkType = determineLinkType(nodeA, nodeB, distance)
                const quality = Math.max(
                    0,
                    100 - distance * 0.8 + Math.random() * 20
                )

                const link: NetworkLink = {
                    id: `link_${nodeA.id}_${nodeB.id}`,
                    source: nodeA.id,
                    target: nodeB.id,
                    type: linkType,
                    quality,
                    bandwidth: generateRandomMetric(10, 100),
                    latency: Math.max(1, distance * 0.1 + Math.random() * 10),
                    status:
                        quality > 70
                            ? 'active'
                            : quality > 40
                            ? 'degraded'
                            : 'failed',
                    protocol: selectProtocol(linkType, nodeA, nodeB),
                }

                links.push(link)

                // 更新節點連接
                nodeA.connections.push(nodeB.id.toString())
                nodeB.connections.push(nodeA.id.toString())
            }
        }
    }

    return links
}

// 確定連接類型
const determineLinkType = (
    nodeA: NetworkNode,
    nodeB: NetworkNode,
    distance: number
): NetworkLink['type'] => {
    if (nodeA.type === 'satellite_gw' || nodeB.type === 'satellite_gw') {
        return 'satellite'
    }
    if (distance > 60) {
        return 'backup'
    }
    if (nodeA.type === 'uav_relay' && nodeB.type === 'uav_relay') {
        return 'mesh'
    }
    return 'direct'
}

// 選擇協議
const selectProtocol = (
    linkType: NetworkLink['type'],
    _nodeA: NetworkNode,
    _nodeB: NetworkNode
): NetworkLink['protocol'] => {
    switch (linkType) {
        case 'satellite':
            return '5G_NR'
        case 'mesh':
            return 'BATMAN'
        case 'backup':
            return 'AODV'
        case 'direct':
            return 'OLSR'
        default:
            return 'BATMAN'
    }
}

// 計算路由路徑
const calculateRoutingPaths = (
    nodes: NetworkNode[],
    links: NetworkLink[]
): RoutingPath[] => {
    const paths: RoutingPath[] = []
    const activeLinks = links.filter((l) => l.status === 'active')

    // 找到所有源和目標節點對
    const primaryNodes = nodes.filter((n) => n.role === 'primary')
    const relayNodes = nodes.filter((n) => n.role === 'relay')

    primaryNodes.forEach((source) => {
        relayNodes.forEach((target) => {
            const path = findShortestPath(source.id, target.id, activeLinks)
            if (path) {
                paths.push(path)
            }
        })
    })

    return paths.slice(0, 10) // 限制顯示的路徑數量
}

// 最短路徑算法 (簡化版 Dijkstra)
const findShortestPath = (
    sourceId: string | number,
    targetId: string | number,
    links: NetworkLink[]
): RoutingPath | null => {
    // 簡化實現 - 實際應用中會使用完整的 Dijkstra 算法
    const directLink = links.find(
        (l) =>
            (l.source === sourceId && l.target === targetId) ||
            (l.source === targetId && l.target === sourceId)
    )

    if (directLink) {
        return {
            id: `path_${sourceId}_${targetId}`,
            source: sourceId,
            destination: targetId,
            hops: [sourceId, targetId],
            totalLatency: directLink.latency,
            reliability: directLink.quality / 100,
            load: generateRandomMetric(20, 80),
        }
    }

    return null
}

// 計算拓撲指標
const calculateTopologyMetrics = (
    nodes: NetworkNode[],
    links: NetworkLink[],
    paths: RoutingPath[]
) => {
    const activeNodes = nodes.filter((n) => n.status === 'active').length
    const activeLinks = links.filter((l) => l.status === 'active').length
    const avgQuality =
        links.reduce((sum, l) => sum + l.quality, 0) / (links.length || 1)
    const avgLatency =
        links.reduce((sum, l) => sum + l.latency, 0) / (links.length || 1)

    return {
        totalNodes: nodes.length,
        activeLinks,
        networkReliability: avgQuality,
        averageLatency: avgLatency,
        routingEfficiency: Math.min(100, paths.length * 10),
        redundancyLevel: Math.min(100, (activeLinks / activeNodes) * 50),
    }
}

// 生成隨機指標
const generateRandomMetric = (min: number, max: number): number => {
    return min + Math.random() * (max - min)
}

// 網路節點可視化組件

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const NetworkNodeVisualization: React.FC<{ node: NetworkNode }> = ({
    node,
}) => {
    const meshRef = useRef<THREE.Group>(null)

    const getNodeColor = (
        type: NetworkNode['type'],
        status: NetworkNode['status']
    ) => {
        if (status !== 'active') return '#666666'

        switch (type) {
            case 'satellite_gw':
                return '#00ff00'
            case 'mesh_node':
                return '#0088ff'
            case 'uav_relay':
                return '#ff8800'
            case 'ground_station':
                return '#8800ff'
            default:
                return '#ffffff'
        }
    }

    const getNodeIcon = (type: NetworkNode['type']) => {
        switch (type) {
            case 'satellite_gw':
                return '🛰️'
            case 'mesh_node':
                return '📡'
            case 'uav_relay':
                return '🚁'
            case 'ground_station':
                return '🏢'
            default:
                return '📶'
        }
    }

    const getStatusIcon = (status: NetworkNode['status']) => {
        switch (status) {
            case 'active':
                return '🟢'
            case 'inactive':
                return '⚫'
            case 'degraded':
                return '🟡'
            case 'offline':
                return '🔴'
            default:
                return '⚪'
        }
    }

    useFrame((state) => {
        if (meshRef.current && node.status === 'active') {
            const time = state.clock.getElapsedTime()
            const pulse = 1 + Math.sin(time * 3) * 0.2
            meshRef.current.scale.setScalar(pulse)
        }
    })

    return (
        <group ref={meshRef} position={node.position}>
            {/* 節點核心 */}
            <mesh>
                <octahedronGeometry args={[8, 0]} />
                <meshStandardMaterial
                    color={getNodeColor(node.type, node.status)}
                    transparent
                    opacity={0.8}
                    emissive={getNodeColor(node.type, node.status)}
                    emissiveIntensity={0.3}
                />
            </mesh>

            {/* 節點類型標籤 */}
            <Text
                position={[0, 20, 0]}
                fontSize={5}
                color={getNodeColor(node.type, node.status)}
                anchorX="center"
                anchorY="middle"
            >
                {getNodeIcon(node.type)}{' '}
                {node.type.replace('_', ' ').toUpperCase()}
            </Text>

            {/* 狀態指示器 */}
            <Text
                position={[0, 14, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                {getStatusIcon(node.status)} {node.status.toUpperCase()}
            </Text>

            {/* 節點指標 */}
            <Text
                position={[0, 8, 0]}
                fontSize={3}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                BW: {node.metrics.bandwidth.toFixed(0)} Mbps
            </Text>

            <Text
                position={[0, 4, 0]}
                fontSize={3}
                color="#cccccc"
                anchorX="center"
                anchorY="middle"
            >
                延遲: {node.metrics.latency.toFixed(1)} ms
            </Text>
        </group>
    )
}

// 網路連接線可視化組件

const NetworkLinksVisualization: React.FC<{
    links: NetworkLink[]
    nodes: NetworkNode[]
}> = ({ links, nodes }) => {
    const getLinkColor = (
        type: NetworkLink['type'],
        status: NetworkLink['status']
    ) => {
        if (status === 'failed') return '#ff0000'
        if (status === 'degraded') return '#ffaa00'

        switch (type) {
            case 'satellite':
                return '#00ff88'
            case 'mesh':
                return '#0088ff'
            case 'backup':
                return '#ff8800'
            case 'direct':
                return '#88ff00'
            default:
                return '#ffffff'
        }
    }

    const getLinkWidth = (quality: number) => {
        return Math.max(1, quality / 25)
    }

    return (
        <>
            {links.map((link) => {
                const sourceNode = nodes.find((n) => n.id === link.source)
                const targetNode = nodes.find((n) => n.id === link.target)

                if (!sourceNode || !targetNode) return null

                const points = [sourceNode.position, targetNode.position]

                return (
                    <Line
                        key={link.id}
                        points={points}
                        color={getLinkColor(link.type, link.status)}
                        lineWidth={getLinkWidth(link.quality)}
                        dashed={link.status === 'degraded'}
                        transparent
                        opacity={0.8}
                    />
                )
            })}
        </>
    )
}

// 路由路徑可視化組件

const RoutingPathVisualization: React.FC<{
    paths: RoutingPath[]
    nodes: NetworkNode[]
}> = ({ paths, nodes }) => {
    return (
        <>
            {paths.slice(0, 3).map((path, index) => {
                const pathNodes = path.hops
                    .map((hopId) => nodes.find((n) => n.id === hopId))
                    .filter(Boolean)
                if (pathNodes.length < 2) return null

                const points = pathNodes.map((node) => [
                    node!.position[0],
                    node!.position[1] + 5 + index * 2,
                    node!.position[2],
                ])

                return (
                    <Line
                        key={path.id}
                        points={points}
                        color={`hsl(${120 + index * 60}, 80%, 60%)`}
                        lineWidth={3}
                        dashed={false}
                        transparent
                        opacity={0.6}
                    />
                )
            })}
        </>
    )
}

// 拓撲狀態顯示組件

// eslint-disable-next-line @typescript-eslint/no-unused-vars
const TopologyStatusDisplay: React.FC<{ metrics: Record<string, unknown> }> = ({
    metrics,
}) => {
    return (
        <group position={[80, 60, 80]}>
            <Text
                position={[0, 25, 0]}
                fontSize={6}
                color="#00aaff"
                anchorX="center"
                anchorY="middle"
            >
                🕸️ 網狀網路拓撲狀態
            </Text>

            <Text
                position={[0, 18, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                總節點數: {metrics.totalNodes}
            </Text>

            <Text
                position={[0, 13, 0]}
                fontSize={4}
                color="#ffffff"
                anchorX="center"
                anchorY="middle"
            >
                活躍連接: {metrics.activeLinks}
            </Text>

            <Text
                position={[0, 8, 0]}
                fontSize={3.5}
                color="#88ff88"
                anchorX="center"
                anchorY="middle"
            >
                網路可靠性: {metrics.networkReliability.toFixed(1)}%
            </Text>

            <Text
                position={[0, 3, 0]}
                fontSize={3.5}
                color="#ffaa88"
                anchorX="center"
                anchorY="middle"
            >
                平均延遲: {metrics.averageLatency.toFixed(1)} ms
            </Text>

            <Text
                position={[0, -2, 0]}
                fontSize={3.5}
                color="#aaffff"
                anchorX="center"
                anchorY="middle"
            >
                路由效率: {metrics.routingEfficiency.toFixed(1)}%
            </Text>

            <Text
                position={[0, -7, 0]}
                fontSize={3.5}
                color="#ffaaff"
                anchorX="center"
                anchorY="middle"
            >
                冗餘級別: {metrics.redundancyLevel.toFixed(1)}%
            </Text>
        </group>
    )
}

// 網路覆蓋範圍可視化組件

const NetworkCoverageVisualization: React.FC<{ nodes: NetworkNode[] }> = ({
    nodes,
}) => {
    return (
        <>
            {nodes.map((node) => {
                if (node.status !== 'active') return null

                const coverageRadius =
                    node.type === 'satellite_gw'
                        ? 80
                        : node.type === 'uav_relay'
                        ? 50
                        : 30

                return (
                    <mesh
                        key={`coverage_${node.id}`}
                        position={[node.position[0], 1, node.position[2]]}
                    >
                        <circleGeometry args={[coverageRadius, 32]} />
                        <meshBasicMaterial
                            color={getNodeColor(node.type, node.status)}
                            transparent
                            opacity={0.1}
                        />
                    </mesh>
                )
            })}
        </>
    )
}

// 動態路由表組件
const _DynamicRoutingTable: React.FC<{ paths: RoutingPath[] }> = ({
    paths,
}) => {
    return (
        <group position={[-80, 60, -80]}>
            <Text
                position={[0, 20, 0]}
                fontSize={5}
                color="#ffaa00"
                anchorX="center"
                anchorY="middle"
            >
                📋 動態路由表
            </Text>

            {paths.slice(0, 5).map((path, index) => (
                <group key={path.id} position={[0, 12 - index * 6, 0]}>
                    <Text
                        position={[0, 2, 0]}
                        fontSize={2.5}
                        color="#ffffff"
                        anchorX="center"
                        anchorY="middle"
                    >
                        {path.source} → {path.destination}
                    </Text>

                    <Text
                        position={[0, -1, 0]}
                        fontSize={2}
                        color="#cccccc"
                        anchorX="center"
                        anchorY="middle"
                    >
                        跳數: {path.hops.length - 1} | 延遲:{' '}
                        {path.totalLatency.toFixed(1)}ms
                    </Text>
                </group>
            ))}
        </group>
    )
}

// 獲取節點顏色 (重用函數)

const getNodeColor = (
    type: NetworkNode['type'],
    status: NetworkNode['status']
) => {
    if (status !== 'active') return '#666666'

    switch (type) {
        case 'satellite_gw':
            return '#00ff00'
        case 'mesh_node':
            return '#0088ff'
        case 'uav_relay':
            return '#ff8800'
        case 'ground_station':
            return '#8800ff'
        default:
            return '#ffffff'
    }
}

export default MeshNetworkTopology
