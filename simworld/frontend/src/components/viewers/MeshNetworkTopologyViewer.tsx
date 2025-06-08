import React, { useEffect, useState, useCallback } from 'react'
import { ViewerProps } from '../../types/viewer'

interface NetworkNode {
  node_id: string
  node_type: string
  position: { x: number; y: number; z: number }
  capacity: number
  current_load: number
  energy_level: number
  reliability: number
  is_active: boolean
  connections: string[]
}

interface NetworkLink {
  link_id: string
  source_node: string
  target_node: string
  capacity: number
  current_utilization: number
  latency: number
  reliability: number
  is_active: boolean
}

interface TopologyMetrics {
  connectivity_index: number
  clustering_coefficient: number
  average_path_length: number
  network_diameter: number
  fault_tolerance: number
  energy_efficiency: number
  load_distribution_variance: number
}

interface MeshTopologyData {
  timestamp: string
  scene_id: string
  nodes: NetworkNode[]
  links: NetworkLink[]
  metrics: TopologyMetrics
  network_status: {
    total_nodes: number
    active_nodes: number
    total_links: number
    active_links: number
    overall_health: number
  }
}

const MeshNetworkTopologyViewer: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  const [topologyData, setTopologyData] = useState<MeshTopologyData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedNodeType, setSelectedNodeType] = useState<string>('all')

  const generateMockData = (): MeshTopologyData => {
    const nodes: NetworkNode[] = [
      {
        node_id: 'GW_001',
        node_type: 'gateway',
        position: { x: 0, y: 0, z: 0 },
        capacity: 1000,
        current_load: 650,
        energy_level: 1.0,
        reliability: 0.99,
        is_active: true,
        connections: ['UAV_001', 'SAT_001', 'BS_001']
      },
      {
        node_id: 'UAV_001',
        node_type: 'uav',
        position: { x: 50, y: 30, z: 100 },
        capacity: 500,
        current_load: 320,
        energy_level: 0.78,
        reliability: 0.92,
        is_active: true,
        connections: ['GW_001', 'UAV_002', 'UE_001']
      },
      {
        node_id: 'UAV_002',
        node_type: 'uav',
        position: { x: -30, y: 60, z: 120 },
        capacity: 500,
        current_load: 280,
        energy_level: 0.85,
        reliability: 0.95,
        is_active: true,
        connections: ['UAV_001', 'SAT_001', 'UE_002']
      },
      {
        node_id: 'SAT_001',
        node_type: 'satellite',
        position: { x: 0, y: 0, z: 500 },
        capacity: 2000,
        current_load: 1200,
        energy_level: 0.95,
        reliability: 0.97,
        is_active: true,
        connections: ['GW_001', 'UAV_002', 'BS_002']
      },
      {
        node_id: 'BS_001',
        node_type: 'base_station',
        position: { x: -80, y: -40, z: 30 },
        capacity: 800,
        current_load: 450,
        energy_level: 1.0,
        reliability: 0.98,
        is_active: true,
        connections: ['GW_001', 'UE_003']
      },
      {
        node_id: 'UE_001',
        node_type: 'user_equipment',
        position: { x: 40, y: 20, z: 5 },
        capacity: 100,
        current_load: 75,
        energy_level: 0.45,
        reliability: 0.88,
        is_active: true,
        connections: ['UAV_001']
      }
    ]

    const links: NetworkLink[] = [
      {
        link_id: 'LINK_001',
        source_node: 'GW_001',
        target_node: 'UAV_001',
        capacity: 500,
        current_utilization: 0.64,
        latency: 15,
        reliability: 0.94,
        is_active: true
      },
      {
        link_id: 'LINK_002',
        source_node: 'UAV_001',
        target_node: 'UAV_002',
        capacity: 300,
        current_utilization: 0.72,
        latency: 8,
        reliability: 0.91,
        is_active: true
      },
      {
        link_id: 'LINK_003',
        source_node: 'GW_001',
        target_node: 'SAT_001',
        capacity: 1000,
        current_utilization: 0.58,
        latency: 250,
        reliability: 0.96,
        is_active: true
      }
    ]

    return {
      timestamp: new Date().toISOString(),
      scene_id: currentScene || 'default',
      nodes,
      links,
      metrics: {
        connectivity_index: 0.87,
        clustering_coefficient: 0.76,
        average_path_length: 2.4,
        network_diameter: 4,
        fault_tolerance: 0.82,
        energy_efficiency: 0.73,
        load_distribution_variance: 0.15
      },
      network_status: {
        total_nodes: nodes.length,
        active_nodes: nodes.filter(n => n.is_active).length,
        total_links: links.length,
        active_links: links.filter(l => l.is_active).length,
        overall_health: 0.89
      }
    }
  }

  const refreshData = useCallback(() => {
    console.log('MeshNetworkTopologyViewer: Starting refresh...')
    setIsLoading(true)
    reportIsLoadingToNavbar(true)
    
    setTimeout(() => {
      console.log('MeshNetworkTopologyViewer: Generating data...')
      const newData = generateMockData()
      setTopologyData(newData)
      setIsLoading(false)
      reportIsLoadingToNavbar(false)
      
      if (onReportLastUpdateToNavbar) {
        onReportLastUpdateToNavbar(new Date().toISOString())
      }
      console.log('MeshNetworkTopologyViewer: Data loaded successfully')
    }, 1100)
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  useEffect(() => {
    console.log('MeshNetworkTopologyViewer: Component mounted, starting initial load...')
    refreshData()
    reportRefreshHandlerToNavbar(refreshData)
  }, [])

  const getNodeTypeColor = (nodeType: string) => {
    switch (nodeType) {
      case 'gateway': return '#ff6b35'
      case 'uav': return '#4ecdc4'
      case 'satellite': return '#45b7d1'
      case 'base_station': return '#96ceb4'
      case 'user_equipment': return '#feca57'
      default: return '#95a5a6'
    }
  }

  const getNodeTypeIcon = (nodeType: string) => {
    switch (nodeType) {
      case 'gateway': return '🌐'
      case 'uav': return '🚁'
      case 'satellite': return '🛰️'
      case 'base_station': return '📡'
      case 'user_equipment': return '📱'
      default: return '🔗'
    }
  }

  if (isLoading || !topologyData) {
    return (
      <div style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#1a1a1a',
        color: 'white',
        flexDirection: 'column'
      }}>
        <div style={{ fontSize: '18px', marginBottom: '16px' }}>載入中...</div>
        <div style={{ fontSize: '14px', opacity: 0.7 }}>正在分析網路拓撲</div>
      </div>
    )
  }

  const filteredNodes = selectedNodeType === 'all' 
    ? topologyData.nodes
    : topologyData.nodes.filter(n => n.node_type === selectedNodeType)

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      background: '#1a1a1a', 
      color: 'white',
      overflow: 'auto',
      padding: '20px'
    }}>
      {/* 頂部網路狀態 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: 'rgba(0,255,0,0.2)',
          border: '1px solid rgba(0,255,0,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🔗 節點</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {topologyData.network_status.active_nodes}/{topologyData.network_status.total_nodes}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(0,150,255,0.2)',
          border: '1px solid rgba(0,150,255,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🔗 連結</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {topologyData.network_status.active_links}/{topologyData.network_status.total_links}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,150,0,0.2)',
          border: '1px solid rgba(255,150,0,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>💚 健康度</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {(topologyData.network_status.overall_health * 100).toFixed(0)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,0,150,0.2)',
          border: '1px solid rgba(255,0,150,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🔗 連通性</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {(topologyData.metrics.connectivity_index * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* 拓撲指標 */}
      <div style={{
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0' }}>📊 網路拓撲指標</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>聚類係數</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {(topologyData.metrics.clustering_coefficient * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>平均路徑長度</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {topologyData.metrics.average_path_length.toFixed(1)}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>網路直徑</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {topologyData.metrics.network_diameter}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>容錯能力</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {(topologyData.metrics.fault_tolerance * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>能源效率</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {(topologyData.metrics.energy_efficiency * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div style={{ fontSize: '14px', opacity: 0.8 }}>負載分布</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
              {(topologyData.metrics.load_distribution_variance * 100).toFixed(1)}%
            </div>
          </div>
        </div>
      </div>

      {/* 節點類型過濾器 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '12px', fontSize: '16px' }}>節點類型篩選:</label>
        <select 
          value={selectedNodeType}
          onChange={(e) => setSelectedNodeType(e.target.value)}
          style={{
            background: '#333',
            color: 'white',
            border: '1px solid #555',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '14px'
          }}
        >
          <option value="all">全部節點</option>
          <option value="gateway">網關</option>
          <option value="uav">UAV</option>
          <option value="satellite">衛星</option>
          <option value="base_station">基站</option>
          <option value="user_equipment">用戶設備</option>
        </select>
      </div>

      {/* 節點詳情 */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '16px' }}>🔗 網路節點</h3>
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
          gap: '16px'
        }}>
          {filteredNodes.map((node) => (
            <div key={node.node_id} style={{
              background: 'rgba(255,255,255,0.05)',
              border: `2px solid ${getNodeTypeColor(node.node_type)}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '12px'
              }}>
                <h4 style={{ margin: 0, fontSize: '16px' }}>
                  {getNodeTypeIcon(node.node_type)} {node.node_id}
                </h4>
                <span style={{
                  background: node.is_active ? 'rgba(0,255,0,0.2)' : 'rgba(255,0,0,0.2)',
                  color: node.is_active ? '#00ff00' : '#ff0000',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  {node.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>

              <div style={{ fontSize: '14px', marginBottom: '12px' }}>
                <div>類型: {node.node_type.replace(/_/g, ' ')}</div>
                <div>位置: ({node.position.x}, {node.position.y}, {node.position.z})</div>
                <div>容量: {node.capacity} Mbps</div>
                <div>當前負載: {node.current_load} Mbps ({((node.current_load / node.capacity) * 100).toFixed(1)}%)</div>
                <div>能源等級: {(node.energy_level * 100).toFixed(1)}%</div>
                <div>可靠性: {(node.reliability * 100).toFixed(1)}%</div>
                <div>連接數: {node.connections.length}</div>
              </div>

              {/* 負載條 */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>負載使用率</div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  height: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: (node.current_load / node.capacity) > 0.8 ? '#ff0000' : 
                               (node.current_load / node.capacity) > 0.6 ? '#ffaa00' : '#00ff00',
                    height: '100%',
                    width: `${(node.current_load / node.capacity) * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              {/* 能源條 */}
              <div>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>能源等級</div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  height: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: node.energy_level > 0.6 ? '#00ff00' : 
                               node.energy_level > 0.3 ? '#ffaa00' : '#ff0000',
                    height: '100%',
                    width: `${node.energy_level * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              <div style={{ marginTop: '8px', fontSize: '12px', opacity: 0.8 }}>
                連接到: {node.connections.join(', ')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 連結狀態 */}
      <div>
        <h3 style={{ marginBottom: '16px' }}>🔗 網路連結</h3>
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '16px'
        }}>
          {topologyData.links.map((link) => (
            <div key={link.link_id} style={{
              background: 'rgba(255,255,255,0.05)',
              border: `1px solid ${link.is_active ? '#00ff00' : '#ff0000'}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: '12px'
              }}>
                <h4 style={{ margin: 0, fontSize: '16px' }}>{link.link_id}</h4>
                <span style={{
                  background: link.is_active ? 'rgba(0,255,0,0.2)' : 'rgba(255,0,0,0.2)',
                  color: link.is_active ? '#00ff00' : '#ff0000',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  {link.is_active ? 'ACTIVE' : 'INACTIVE'}
                </span>
              </div>

              <div style={{ fontSize: '14px' }}>
                <div>來源: {link.source_node}</div>
                <div>目標: {link.target_node}</div>
                <div>容量: {link.capacity} Mbps</div>
                <div>使用率: {(link.current_utilization * 100).toFixed(1)}%</div>
                <div>延遲: {link.latency} ms</div>
                <div>可靠性: {(link.reliability * 100).toFixed(1)}%</div>
              </div>

              {/* 使用率條 */}
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>頻寬使用率</div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  height: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: link.current_utilization > 0.8 ? '#ff0000' : 
                               link.current_utilization > 0.6 ? '#ffaa00' : '#00ff00',
                    height: '100%',
                    width: `${link.current_utilization * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 底部時間戳 */}
      <div style={{ 
        marginTop: '30px', 
        textAlign: 'center', 
        fontSize: '12px', 
        opacity: 0.7 
      }}>
        場景: {topologyData.scene_id} | 最後更新: {new Date(topologyData.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

export default MeshNetworkTopologyViewer