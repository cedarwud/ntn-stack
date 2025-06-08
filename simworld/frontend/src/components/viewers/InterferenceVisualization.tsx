import React, { useEffect, useState, useCallback } from 'react'
import { ViewerProps } from '../../types/viewer'

interface InterferenceSource {
  source_id: string
  position: { x: number; y: number; z: number }
  frequency_mhz: number
  power_dbm: number
  interference_type: 'intentional' | 'unintentional' | 'natural'
  coverage_radius: number
  is_active: boolean
}

interface AffectedDevice {
  device_id: string
  device_type: 'ue' | 'gnb' | 'satellite' | 'uav'
  position: { x: number; y: number; z: number }
  interference_level: number
  sinr_db: number
  is_critical: boolean
  mitigation_active: boolean
}

interface InterferenceData {
  timestamp: string
  scene_id: string
  sources: InterferenceSource[]
  affected_devices: AffectedDevice[]
  ai_ran_status: {
    is_active: boolean
    interference_detected: number
    mitigation_success_rate: number
    response_time_ms: number
  }
}

const InterferenceVisualization: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  const [interferenceData, setInterferenceData] = useState<InterferenceData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const generateMockData = (): InterferenceData => {
    const sources: InterferenceSource[] = [
      {
        source_id: 'JAMMER_001',
        position: { x: -20, y: 5, z: -10 },
        frequency_mhz: 2400,
        power_dbm: 30,
        interference_type: 'intentional',
        coverage_radius: 15,
        is_active: true
      },
      {
        source_id: 'EMI_002',
        position: { x: 15, y: 8, z: 12 },
        frequency_mhz: 3500,
        power_dbm: 20,
        interference_type: 'unintentional',
        coverage_radius: 10,
        is_active: true
      }
    ]

    const affected_devices: AffectedDevice[] = [
      {
        device_id: 'UE_001',
        device_type: 'ue',
        position: { x: -15, y: 2, z: -5 },
        interference_level: 0.8,
        sinr_db: -2.5,
        is_critical: true,
        mitigation_active: true
      },
      {
        device_id: 'GNB_001',
        device_type: 'gnb',
        position: { x: 0, y: 10, z: 0 },
        interference_level: 0.3,
        sinr_db: 12.8,
        is_critical: false,
        mitigation_active: false
      }
    ]

    return {
      timestamp: new Date().toISOString(),
      scene_id: currentScene || 'default',
      sources,
      affected_devices,
      ai_ran_status: {
        is_active: true,
        interference_detected: sources.filter(s => s.is_active).length,
        mitigation_success_rate: 0.87,
        response_time_ms: 45
      }
    }
  }

  const refreshData = useCallback(() => {
    console.log('InterferenceVisualization: Starting refresh...')
    setIsLoading(true)
    reportIsLoadingToNavbar(true)
    
    setTimeout(() => {
      console.log('InterferenceVisualization: Generating data...')
      const newData = generateMockData()
      setInterferenceData(newData)
      setIsLoading(false)
      reportIsLoadingToNavbar(false)
      
      if (onReportLastUpdateToNavbar) {
        onReportLastUpdateToNavbar(new Date().toISOString())
      }
      console.log('InterferenceVisualization: Data loaded successfully')
    }, 800)
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  useEffect(() => {
    console.log('InterferenceVisualization: Component mounted, starting initial load...')
    refreshData()
    reportRefreshHandlerToNavbar(refreshData)
  }, [])

  if (isLoading || !interferenceData) {
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
        <div style={{ fontSize: '14px', opacity: 0.7 }}>正在計算干擾模式</div>
      </div>
    )
  }

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      background: '#1a1a1a', 
      color: 'white',
      overflow: 'auto',
      padding: '20px'
    }}>
      {/* 頂部資訊 */}
      <div style={{
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px'
      }}>
        <h2 style={{ margin: '0 0 16px 0', fontSize: '24px' }}>🔬 3D 干擾可視化</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', color: '#ff6b6b' }}>場景</div>
            <div style={{ fontSize: '16px' }}>{interferenceData.scene_id}</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', color: '#4ecdc4' }}>干擾源</div>
            <div style={{ fontSize: '16px' }}>{interferenceData.sources.length} 個</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', color: '#45b7d1' }}>受影響設備</div>
            <div style={{ fontSize: '16px' }}>{interferenceData.affected_devices.length} 個</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '20px', color: '#96ceb4' }}>AI-RAN 狀態</div>
            <div style={{ fontSize: '16px' }}>
              {interferenceData.ai_ran_status.is_active ? '🟢 運行中' : '🔴 停止'}
            </div>
          </div>
        </div>
      </div>

      {/* 干擾源詳情 */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '16px' }}>📡 干擾源詳情</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {interferenceData.sources.map((source) => (
            <div key={source.source_id} style={{
              background: source.interference_type === 'intentional' ? 'rgba(255,68,68,0.2)' :
                         source.interference_type === 'unintentional' ? 'rgba(255,170,68,0.2)' : 
                         'rgba(68,255,68,0.2)',
              border: `1px solid ${source.interference_type === 'intentional' ? '#ff4444' :
                                  source.interference_type === 'unintentional' ? '#ffaa44' : '#44ff44'}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              <h4 style={{ margin: '0 0 8px 0', color: 'white' }}>{source.source_id}</h4>
              <div style={{ fontSize: '14px' }}>
                <div>類型: {source.interference_type === 'intentional' ? '🔴 故意干擾' :
                           source.interference_type === 'unintentional' ? '🟠 非故意干擾' : '🟢 自然干擾'}</div>
                <div>頻率: {source.frequency_mhz} MHz</div>
                <div>功率: {source.power_dbm} dBm</div>
                <div>位置: ({source.position.x}, {source.position.y}, {source.position.z})</div>
                <div>覆蓋範圍: {source.coverage_radius} m</div>
                <div>狀態: {source.is_active ? '🟢 活躍' : '🔴 非活躍'}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 受影響設備 */}
      <div style={{ marginBottom: '20px' }}>
        <h3 style={{ marginBottom: '16px' }}>📱 受影響設備</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
          {interferenceData.affected_devices.map((device) => (
            <div key={device.device_id} style={{
              background: device.interference_level > 0.7 ? 'rgba(255,0,0,0.2)' :
                         device.interference_level > 0.4 ? 'rgba(255,165,0,0.2)' : 'rgba(0,255,0,0.2)',
              border: `1px solid ${device.interference_level > 0.7 ? '#ff0000' :
                                  device.interference_level > 0.4 ? '#ffa500' : '#00ff00'}`,
              borderRadius: '8px',
              padding: '16px'
            }}>
              <h4 style={{ margin: '0 0 8px 0', color: 'white' }}>
                {device.device_type === 'ue' ? '📱' :
                 device.device_type === 'gnb' ? '📡' :
                 device.device_type === 'satellite' ? '🛰️' : '🚁'} {device.device_id}
              </h4>
              <div style={{ fontSize: '14px' }}>
                <div>設備類型: {device.device_type.toUpperCase()}</div>
                <div>干擾等級: {(device.interference_level * 100).toFixed(1)}%</div>
                <div>SINR: {device.sinr_db.toFixed(1)} dB</div>
                <div>位置: ({device.position.x}, {device.position.y}, {device.position.z})</div>
                <div>狀態: {device.is_critical ? '🔴 嚴重' : '🟢 正常'}</div>
                <div>緩解措施: {device.mitigation_active ? '🟢 啟動' : '🔴 未啟動'}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI-RAN 狀態 */}
      <div style={{
        background: 'rgba(0,150,255,0.2)',
        border: '1px solid rgba(0,150,255,0.5)',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0' }}>🤖 AI-RAN 抗干擾系統</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '18px', color: '#4ecdc4' }}>系統狀態</div>
            <div style={{ fontSize: '16px' }}>
              {interferenceData.ai_ran_status.is_active ? '🟢 運行中' : '🔴 停止'}
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '18px', color: '#4ecdc4' }}>檢測到干擾</div>
            <div style={{ fontSize: '16px' }}>{interferenceData.ai_ran_status.interference_detected} 個</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '18px', color: '#4ecdc4' }}>緩解成功率</div>
            <div style={{ fontSize: '16px' }}>
              {(interferenceData.ai_ran_status.mitigation_success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '18px', color: '#4ecdc4' }}>響應時間</div>
            <div style={{ fontSize: '16px' }}>{interferenceData.ai_ran_status.response_time_ms} ms</div>
          </div>
        </div>
      </div>

      {/* 底部時間戳 */}
      <div style={{ 
        marginTop: '20px', 
        textAlign: 'center', 
        fontSize: '12px', 
        opacity: 0.7 
      }}>
        最後更新: {new Date(interferenceData.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

export default InterferenceVisualization