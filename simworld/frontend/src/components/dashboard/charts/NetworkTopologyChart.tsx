import React, { useState } from 'react'
import '../panels/PanelCommon.scss'

interface NetworkTopologyChartProps {
    data: any
    loading: boolean
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
    onNodeClick?: (nodeId: string) => void
    currentScene: string
}

interface SimpleNode {
    id: string
    name: string
    type: string
    status: string
    x: number
    y: number
}

const NetworkTopologyChart: React.FC<NetworkTopologyChartProps> = ({
    data,
    loading,
    style,
    isFullscreen,
    onFullscreen,
    onNodeClick,
    currentScene,
}) => {
    const [selectedNode, setSelectedNode] = useState<string | null>(null)

    // 簡化的節點數據處理
    const nodes: SimpleNode[] =
        data?.topology?.nodes?.map((node: any, index: number) => ({
            id: node.node_id || node.id || `node-${index}`,
            name: node.name || node.node_id || `Node ${index + 1}`,
            type: node.node_type || 'unknown',
            status: node.status?.is_active ? 'active' : 'inactive',
            x: 100 + (index % 4) * 80, // 簡單的網格佈局
            y: 100 + Math.floor(index / 4) * 80,
        })) || []

    const links = data?.topology?.links || []

    const getNodeColor = (node: SimpleNode) => {
        if (node.status !== 'active') return '#9E9E9E'

        switch (node.type) {
            case 'gateway':
                return '#2196F3'
            case 'mesh_node':
                return '#4CAF50'
            case 'uav':
                return '#FF9800'
            case 'satellite':
                return '#9C27B0'
            default:
                return '#607D8B'
        }
    }

    const handleNodeClick = (node: SimpleNode) => {
        setSelectedNode(selectedNode === node.id ? null : node.id)
        onNodeClick?.(node.id)
    }

    return (
        <div
            className={`panel network-topology ${
                isFullscreen ? 'fullscreen' : ''
            }`}
            style={style}
        >
            <div className="panel-header">
                <h3>網絡拓撲</h3>
                <div className="panel-controls">
                    <span className="node-count">節點: {nodes.length}</span>
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                {loading && (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>載入網絡拓撲中...</p>
                    </div>
                )}

                {!loading && (
                    <div className="topology-container">
                        <div
                            className="simple-topology"
                            style={{
                                position: 'relative',
                                height: '300px',
                                background: '#fafafa',
                            }}
                        >
                            {/* 簡單的連線 */}
                            {links.map((link: any, index: number) => {
                                const sourceNode = nodes.find(
                                    (n) =>
                                        n.id ===
                                        (link.source_node || link.source)
                                )
                                const targetNode = nodes.find(
                                    (n) =>
                                        n.id ===
                                        (link.target_node || link.target)
                                )

                                if (!sourceNode || !targetNode) return null

                                const quality =
                                    link.quality?.link_quality || 0.5
                                const color =
                                    quality > 0.8
                                        ? '#4CAF50'
                                        : quality > 0.5
                                        ? '#FF9800'
                                        : '#F44336'

                                return (
                                    <div
                                        key={index}
                                        className="topology-link"
                                        style={{
                                            position: 'absolute',
                                            left: `${Math.min(
                                                sourceNode.x,
                                                targetNode.x
                                            )}px`,
                                            top: `${
                                                Math.min(
                                                    sourceNode.y,
                                                    targetNode.y
                                                ) + 15
                                            }px`,
                                            width: `${
                                                Math.abs(
                                                    targetNode.x - sourceNode.x
                                                ) || 2
                                            }px`,
                                            height: `${
                                                Math.abs(
                                                    targetNode.y - sourceNode.y
                                                ) || 2
                                            }px`,
                                            background: color,
                                            opacity: 0.6,
                                            pointerEvents: 'none',
                                        }}
                                    />
                                )
                            })}

                            {/* 節點 */}
                            {nodes.map((node) => (
                                <div
                                    key={node.id}
                                    className={`topology-node ${
                                        selectedNode === node.id
                                            ? 'selected'
                                            : ''
                                    }`}
                                    style={{
                                        position: 'absolute',
                                        left: `${node.x}px`,
                                        top: `${node.y}px`,
                                        width: '30px',
                                        height: '30px',
                                        borderRadius: '50%',
                                        background: getNodeColor(node),
                                        border:
                                            selectedNode === node.id
                                                ? '3px solid #000'
                                                : '2px solid #fff',
                                        cursor: 'pointer',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '10px',
                                        color: 'white',
                                        fontWeight: 'bold',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                        transition: 'all 0.2s ease',
                                    }}
                                    onClick={() => handleNodeClick(node)}
                                    title={`${node.name} (${node.type}) - ${node.status}`}
                                >
                                    {node.name.substring(0, 2).toUpperCase()}
                                </div>
                            ))}
                        </div>

                        {/* 圖例 */}
                        <div className="topology-legend">
                            <div className="legend-item">
                                <div
                                    className="legend-color"
                                    style={{ backgroundColor: '#2196F3' }}
                                ></div>
                                <span>網關</span>
                            </div>
                            <div className="legend-item">
                                <div
                                    className="legend-color"
                                    style={{ backgroundColor: '#4CAF50' }}
                                ></div>
                                <span>Mesh 節點</span>
                            </div>
                            <div className="legend-item">
                                <div
                                    className="legend-color"
                                    style={{ backgroundColor: '#FF9800' }}
                                ></div>
                                <span>UAV</span>
                            </div>
                            <div className="legend-item">
                                <div
                                    className="legend-color"
                                    style={{ backgroundColor: '#9C27B0' }}
                                ></div>
                                <span>衛星</span>
                            </div>
                        </div>

                        {/* 選中節點的詳細信息 */}
                        {selectedNode && (
                            <div className="node-details">
                                <h4>節點詳情</h4>
                                {(() => {
                                    const node = nodes.find(
                                        (n) => n.id === selectedNode
                                    )
                                    return node ? (
                                        <div>
                                            <p>
                                                <strong>名稱:</strong>{' '}
                                                {node.name}
                                            </p>
                                            <p>
                                                <strong>類型:</strong>{' '}
                                                {node.type}
                                            </p>
                                            <p>
                                                <strong>狀態:</strong>{' '}
                                                {node.status}
                                            </p>
                                        </div>
                                    ) : null
                                })()}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}

export default NetworkTopologyChart
