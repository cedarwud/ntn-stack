import React, { useEffect, useState, useCallback } from 'react'
import { ViewerProps } from '../../types/viewer'

interface UAVMember {
  uav_id: string
  role: string
  position: { latitude: number; longitude: number; altitude: number }
  battery_level: number
  is_active: boolean
  formation_compliance: number
}

interface SwarmGroup {
  group_id: string
  name: string
  leader_id: string
  uavs: UAVMember[]
  formation_type: string
  coordination_quality: number
}

interface SwarmCoordinationData {
  timestamp: string
  scene_id: string
  swarm_groups: SwarmGroup[]
  network_status: {
    total_uavs: number
    active_uavs: number
    coordination_quality: number
    formation_efficiency: number
  }
}

const UAVSwarmCoordinationViewer: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  const [swarmData, setSwarmData] = useState<SwarmCoordinationData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedGroup, setSelectedGroup] = useState<string>('all')

  const generateMockData = (): SwarmCoordinationData => {
    const swarm_groups: SwarmGroup[] = [
      {
        group_id: 'ALPHA_SQUAD',
        name: 'Alpha 偵查群組',
        leader_id: 'UAV_A1',
        formation_type: 'V_formation',
        coordination_quality: 0.92,
        uavs: [
          {
            uav_id: 'UAV_A1',
            role: 'leader',
            position: { latitude: 25.0410, longitude: 121.5440, altitude: 150 },
            battery_level: 87,
            is_active: true,
            formation_compliance: 0.95
          },
          {
            uav_id: 'UAV_A2',
            role: 'wing_left',
            position: { latitude: 25.0405, longitude: 121.5435, altitude: 145 },
            battery_level: 92,
            is_active: true,
            formation_compliance: 0.88
          },
          {
            uav_id: 'UAV_A3',
            role: 'wing_right',
            position: { latitude: 25.0405, longitude: 121.5445, altitude: 145 },
            battery_level: 79,
            is_active: true,
            formation_compliance: 0.91
          }
        ]
      },
      {
        group_id: 'BRAVO_SQUAD',
        name: 'Bravo 中繼群組',
        leader_id: 'UAV_B1',
        formation_type: 'line_formation',
        coordination_quality: 0.85,
        uavs: [
          {
            uav_id: 'UAV_B1',
            role: 'relay_master',
            position: { latitude: 25.0420, longitude: 121.5460, altitude: 200 },
            battery_level: 95,
            is_active: true,
            formation_compliance: 0.97
          },
          {
            uav_id: 'UAV_B2',
            role: 'relay_node',
            position: { latitude: 25.0430, longitude: 121.5470, altitude: 180 },
            battery_level: 83,
            is_active: true,
            formation_compliance: 0.82
          }
        ]
      }
    ]

    return {
      timestamp: new Date().toISOString(),
      scene_id: currentScene || 'default',
      swarm_groups,
      network_status: {
        total_uavs: swarm_groups.reduce((sum, group) => sum + group.uavs.length, 0),
        active_uavs: swarm_groups.reduce((sum, group) => sum + group.uavs.filter(uav => uav.is_active).length, 0),
        coordination_quality: 0.89,
        formation_efficiency: 0.91
      }
    }
  }

  const refreshData = useCallback(() => {
    console.log('UAVSwarmCoordinationViewer: Starting refresh...')
    setIsLoading(true)
    reportIsLoadingToNavbar(true)
    
    setTimeout(() => {
      console.log('UAVSwarmCoordinationViewer: Generating data...')
      const newData = generateMockData()
      setSwarmData(newData)
      setIsLoading(false)
      reportIsLoadingToNavbar(false)
      
      if (onReportLastUpdateToNavbar) {
        onReportLastUpdateToNavbar(new Date().toISOString())
      }
      console.log('UAVSwarmCoordinationViewer: Data loaded successfully')
    }, 900)
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  useEffect(() => {
    console.log('UAVSwarmCoordinationViewer: Component mounted, starting initial load...')
    refreshData()
    reportRefreshHandlerToNavbar(refreshData)
  }, [])

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'leader': return '#ff6b35'
      case 'wing_left': return '#4ecdc4'
      case 'wing_right': return '#45b7d1'
      case 'relay_master': return '#feca57'
      case 'relay_node': return '#96ceb4'
      default: return '#95a5a6'
    }
  }

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'leader': return '👑'
      case 'wing_left': return '↙️'
      case 'wing_right': return '↘️'
      case 'relay_master': return '📡'
      case 'relay_node': return '🔗'
      default: return '🚁'
    }
  }

  if (isLoading || !swarmData) {
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
        <div style={{ fontSize: '14px', opacity: 0.7 }}>正在計算 UAV 群組協同</div>
      </div>
    )
  }

  const filteredGroups = selectedGroup === 'all' 
    ? swarmData.swarm_groups
    : swarmData.swarm_groups.filter(g => g.group_id === selectedGroup)

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      background: '#1a1a1a', 
      color: 'white',
      overflow: 'auto',
      padding: '20px'
    }}>
      {/* 頂部統計 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <div style={{
          background: 'rgba(0,255,0,0.2)',
          border: '1px solid rgba(0,255,0,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>🚁 總 UAV 數</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {swarmData.network_status.total_uavs}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(0,150,255,0.2)',
          border: '1px solid rgba(0,150,255,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>✅ 活躍 UAV</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {swarmData.network_status.active_uavs}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,150,0,0.2)',
          border: '1px solid rgba(255,150,0,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>🤝 協同品質</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {(swarmData.network_status.coordination_quality * 100).toFixed(1)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,0,150,0.2)',
          border: '1px solid rgba(255,0,150,0.5)',
          borderRadius: '8px',
          padding: '16px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>🎯 編隊效率</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {(swarmData.network_status.formation_efficiency * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* 群組過濾器 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '12px', fontSize: '16px' }}>群組篩選:</label>
        <select 
          value={selectedGroup}
          onChange={(e) => setSelectedGroup(e.target.value)}
          style={{
            background: '#333',
            color: 'white',
            border: '1px solid #555',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '14px'
          }}
        >
          <option value="all">全部群組</option>
          {swarmData.swarm_groups.map(group => (
            <option key={group.group_id} value={group.group_id}>
              {group.name} ({group.group_id})
            </option>
          ))}
        </select>
      </div>

      {/* 群組詳情 */}
      <div>
        <h3 style={{ marginBottom: '16px' }}>🚁 UAV 群組詳情</h3>
        {filteredGroups.map((group) => (
          <div key={group.group_id} style={{
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '16px'
            }}>
              <h4 style={{ margin: 0, fontSize: '18px' }}>{group.name}</h4>
              <div style={{
                background: 'rgba(0,150,255,0.3)',
                padding: '4px 12px',
                borderRadius: '6px',
                fontSize: '14px'
              }}>
                {group.formation_type.replace(/_/g, ' ')}
              </div>
            </div>

            <div style={{ marginBottom: '16px', fontSize: '14px' }}>
              <div>群組 ID: {group.group_id}</div>
              <div>領導者: {group.leader_id}</div>
              <div>協同品質: {(group.coordination_quality * 100).toFixed(1)}%</div>
              <div>UAV 數量: {group.uavs.length}</div>
            </div>

            {/* UAV 列表 */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '12px'
            }}>
              {group.uavs.map((uav) => (
                <div key={uav.uav_id} style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: `2px solid ${getRoleColor(uav.role)}`,
                  borderRadius: '6px',
                  padding: '12px'
                }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}>
                    <h5 style={{ margin: 0, fontSize: '14px' }}>
                      {getRoleIcon(uav.role)} {uav.uav_id}
                    </h5>
                    <span style={{
                      background: uav.is_active ? 'rgba(0,255,0,0.2)' : 'rgba(255,0,0,0.2)',
                      color: uav.is_active ? '#00ff00' : '#ff0000',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      fontSize: '10px'
                    }}>
                      {uav.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </div>

                  <div style={{ fontSize: '12px' }}>
                    <div>角色: {uav.role.replace(/_/g, ' ')}</div>
                    <div>位置: ({uav.position.latitude.toFixed(4)}, {uav.position.longitude.toFixed(4)})</div>
                    <div>高度: {uav.position.altitude} m</div>
                    <div>電池: {uav.battery_level}%</div>
                    <div>編隊符合度: {(uav.formation_compliance * 100).toFixed(1)}%</div>
                  </div>

                  {/* 電池電量條 */}
                  <div style={{ marginTop: '8px' }}>
                    <div style={{
                      background: 'rgba(255,255,255,0.2)',
                      borderRadius: '4px',
                      height: '6px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        background: uav.battery_level > 50 ? '#00ff00' : 
                                   uav.battery_level > 20 ? '#ffaa00' : '#ff0000',
                        height: '100%',
                        width: `${uav.battery_level}%`,
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* 底部時間戳 */}
      <div style={{ 
        marginTop: '20px', 
        textAlign: 'center', 
        fontSize: '12px', 
        opacity: 0.7 
      }}>
        場景: {swarmData.scene_id} | 最後更新: {new Date(swarmData.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

export default UAVSwarmCoordinationViewer