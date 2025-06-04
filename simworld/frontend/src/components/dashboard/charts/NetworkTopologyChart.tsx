/**
 * 網路拓撲圖表組件
 * 使用 D3.js 顯示網路節點和連接關係
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { getMeshTopology, getMeshNodes } from '../../../services/netstackApi'

interface NetworkTopologyChartProps {
    className?: string
    width?: number
    height?: number
    refreshInterval?: number
}

interface Node {
    id: string
    name: string
    type: string
    status: string
    x?: number
    y?: number
    fx?: number | null
    fy?: number | null
}

interface Link {
    source: string | Node
    target: string | Node
    type: string
    status: string
}

const NetworkTopologyChart: React.FC<NetworkTopologyChartProps> = ({
    className = '',
    width = 800,
    height = 600,
    refreshInterval = 10000,
}) => {
    const svgRef = useRef<SVGSVGElement>(null)
    const [nodes, setNodes] = useState<Node[]>([])
    const [links, setLinks] = useState<Link[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedNode, setSelectedNode] = useState<Node | null>(null)

    // 使用 useCallback 避免函數重新創建
    const loadNetworkData = useCallback(async () => {
        try {
            setLoading(true)
            const [topologyData] = await Promise.all([
                getMeshTopology(),
                getMeshNodes(),
            ])

            if (topologyData && topologyData.nodes) {
                setNodes(topologyData.nodes)
                setLinks(topologyData.links || [])
            }

            setError(null)
        } catch (err) {
            console.error('載入網路拓撲失敗:', err)
            setError('無法載入網路拓撲數據')
        } finally {
            setLoading(false)
        }
    }, [])

    // 組件掛載時載入數據
    useEffect(() => {
        loadNetworkData()
    }, [loadNetworkData])

    // 設置定時刷新
    useEffect(() => {
        if (refreshInterval > 0) {
            const interval = setInterval(loadNetworkData, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [refreshInterval, loadNetworkData])

    // 獲取節點顏色
    const getNodeColor = (type: string, status: string): string => {
        const baseColors = {
            gateway: '#8b5cf6',
            mesh: '#06b6d4',
            uav: '#10b981',
            unknown: '#6b7280',
        }

        const statusModifier =
            status === 'active' ? 1 : status === 'degraded' ? 0.6 : 0.3
        const baseColor =
            baseColors[type as keyof typeof baseColors] || baseColors.unknown

        return baseColor
    }

    // 獲取連接顏色
    const getLinkColor = (type: string, status: string): string => {
        const baseColors = {
            mesh: '#06b6d4',
            wireless: '#10b981',
            unknown: '#6b7280',
        }

        const opacity =
            status === 'active' ? '1' : status === 'degraded' ? '0.6' : '0.3'
        const baseColor =
            baseColors[type as keyof typeof baseColors] || baseColors.unknown

        return baseColor + opacity.replace('.', '').padEnd(2, '0')
    }

    // 處理節點點擊
    const handleNodeClick = (node: Node) => {
        setSelectedNode(node)
    }

    // 使用簡單的力導向布局
    useEffect(() => {
        if (!svgRef.current || nodes.length === 0) return

        const svg = svgRef.current
        const svgRect = svg.getBoundingClientRect()
        const centerX = svgRect.width / 2
        const centerY = svgRect.height / 2

        // 清除現有內容
        while (svg.firstChild) {
            svg.removeChild(svg.firstChild)
        }

        // 創建 defs 元素用於定義箭頭標記
        const defs = document.createElementNS(
            'http://www.w3.org/2000/svg',
            'defs'
        )
        const marker = document.createElementNS(
            'http://www.w3.org/2000/svg',
            'marker'
        )
        marker.setAttribute('id', 'arrowhead')
        marker.setAttribute('markerWidth', '10')
        marker.setAttribute('markerHeight', '7')
        marker.setAttribute('refX', '9')
        marker.setAttribute('refY', '3.5')
        marker.setAttribute('orient', 'auto')

        const polygon = document.createElementNS(
            'http://www.w3.org/2000/svg',
            'polygon'
        )
        polygon.setAttribute('points', '0 0, 10 3.5, 0 7')
        polygon.setAttribute('fill', '#666')

        marker.appendChild(polygon)
        defs.appendChild(marker)
        svg.appendChild(defs)

        // 簡單的圓形布局
        const angleStep = (2 * Math.PI) / nodes.length
        const radius = Math.min(centerX, centerY) * 0.6

        // 繪製連接線
        links.forEach((link, index) => {
            const sourceNode = nodes.find((n) => n.id === link.source)
            const targetNode = nodes.find((n) => n.id === link.target)

            if (sourceNode && targetNode) {
                const sourceAngle = nodes.indexOf(sourceNode) * angleStep
                const targetAngle = nodes.indexOf(targetNode) * angleStep

                const sourceX = centerX + radius * Math.cos(sourceAngle)
                const sourceY = centerY + radius * Math.sin(sourceAngle)
                const targetX = centerX + radius * Math.cos(targetAngle)
                const targetY = centerY + radius * Math.sin(targetAngle)

                const line = document.createElementNS(
                    'http://www.w3.org/2000/svg',
                    'line'
                )
                line.setAttribute('x1', sourceX.toString())
                line.setAttribute('y1', sourceY.toString())
                line.setAttribute('x2', targetX.toString())
                line.setAttribute('y2', targetY.toString())
                line.setAttribute(
                    'stroke',
                    getLinkColor(link.type, link.status)
                )
                line.setAttribute('stroke-width', '2')
                line.setAttribute('marker-end', 'url(#arrowhead)')

                svg.appendChild(line)
            }
        })

        // 繪製節點
        nodes.forEach((node, index) => {
            const angle = index * angleStep
            const x = centerX + radius * Math.cos(angle)
            const y = centerY + radius * Math.sin(angle)

            // 節點圓圈
            const circle = document.createElementNS(
                'http://www.w3.org/2000/svg',
                'circle'
            )
            circle.setAttribute('cx', x.toString())
            circle.setAttribute('cy', y.toString())
            circle.setAttribute('r', '20')
            circle.setAttribute('fill', getNodeColor(node.type, node.status))
            circle.setAttribute('stroke', '#fff')
            circle.setAttribute('stroke-width', '2')
            circle.style.cursor = 'pointer'

            circle.addEventListener('click', () => handleNodeClick(node))

            svg.appendChild(circle)

            // 節點標籤
            const text = document.createElementNS(
                'http://www.w3.org/2000/svg',
                'text'
            )
            text.setAttribute('x', x.toString())
            text.setAttribute('y', (y + 35).toString())
            text.setAttribute('text-anchor', 'middle')
            text.setAttribute('fill', '#fff')
            text.setAttribute('font-size', '12')
            text.textContent = node.name

            svg.appendChild(text)
        })
    }, [nodes, links])

    if (loading) {
        return (
            <div className={`network-topology-chart ${className}`}>
                <div className="loading">
                    <div className="loading-spinner"></div>
                    <span>載入網路拓撲中...</span>
                </div>
            </div>
        )
    }

    return (
        <div className={`network-topology-chart ${className}`}>
            <div className="chart-header">
                <h3>網路拓撲圖</h3>
                <div className="legend">
                    <div className="legend-item">
                        <span
                            className="legend-dot"
                            style={{ backgroundColor: '#8b5cf6' }}
                        ></span>
                        <span>網關</span>
                    </div>
                    <div className="legend-item">
                        <span
                            className="legend-dot"
                            style={{ backgroundColor: '#06b6d4' }}
                        ></span>
                        <span>Mesh 節點</span>
                    </div>
                    <div className="legend-item">
                        <span
                            className="legend-dot"
                            style={{ backgroundColor: '#10b981' }}
                        ></span>
                        <span>UAV</span>
                    </div>
                </div>
            </div>

            <div className="chart-content">
                <svg
                    ref={svgRef}
                    width={width}
                    height={height}
                    style={{ border: '1px solid #333', borderRadius: '8px' }}
                ></svg>

                {selectedNode && (
                    <div className="node-details">
                        <h4>節點詳情</h4>
                        <div className="detail-item">
                            <span className="label">ID:</span>
                            <span className="value">{selectedNode.id}</span>
                        </div>
                        <div className="detail-item">
                            <span className="label">名稱:</span>
                            <span className="value">{selectedNode.name}</span>
                        </div>
                        <div className="detail-item">
                            <span className="label">類型:</span>
                            <span className="value">{selectedNode.type}</span>
                        </div>
                        <div className="detail-item">
                            <span className="label">狀態:</span>
                            <span
                                className="value"
                                style={{
                                    color: getNodeColor(
                                        selectedNode.type,
                                        selectedNode.status
                                    ),
                                }}
                            >
                                {selectedNode.status}
                            </span>
                        </div>
                        <button
                            onClick={() => setSelectedNode(null)}
                            className="close-button"
                        >
                            關閉
                        </button>
                    </div>
                )}
            </div>

            {error && (
                <div className="error-notice">
                    <span>⚠️ {error} (顯示模擬數據)</span>
                    <button onClick={loadNetworkData} className="retry-button">
                        重試
                    </button>
                </div>
            )}

            <div className="chart-footer">
                <span className="node-count">節點數: {nodes.length}</span>
                <span className="link-count">連接數: {links.length}</span>
            </div>
        </div>
    )
}

export default NetworkTopologyChart
