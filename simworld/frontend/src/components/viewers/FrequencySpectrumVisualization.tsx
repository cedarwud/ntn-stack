import React, { useEffect, useState, useCallback } from 'react'
import { ViewerProps } from '../../types/viewer'

interface FrequencyBand {
  frequency_start_mhz: number
  frequency_end_mhz: number
  center_frequency_mhz: number
  bandwidth_mhz: number
  power_dbm: number
  usage_type: 'primary' | 'secondary' | 'interference' | 'vacant' | 'protected'
  user_id?: string
  user_name?: string
  modulation?: string
  signal_quality: number
  interference_level: number
  last_updated: string
}

interface SpectrumScan {
  scan_id: string
  timestamp: string
  frequency_range: {
    start_mhz: number
    end_mhz: number
    resolution_khz: number
  }
  bands: FrequencyBand[]
  scan_duration_ms: number
  environment: string
  location?: {
    latitude: number
    longitude: number
    altitude: number
  }
}

interface FrequencySpectrumData {
  timestamp: string
  scene_id: string
  spectrum_scans: SpectrumScan[]
  summary: {
    total_bands: number
    occupied_bands: number
    interference_bands: number
    vacant_bands: number
    spectrum_efficiency: number
    interference_ratio: number
  }
}

const FrequencySpectrumVisualization: React.FC<ViewerProps> = ({
  currentScene,
  onReportLastUpdateToNavbar,
  reportRefreshHandlerToNavbar,
  reportIsLoadingToNavbar
}) => {
  const [spectrumData, setSpectrumData] = useState<FrequencySpectrumData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedBandType, setSelectedBandType] = useState<string>('all')

  const generateMockData = (): FrequencySpectrumData => {
    const bands: FrequencyBand[] = [
      {
        frequency_start_mhz: 2400,
        frequency_end_mhz: 2420,
        center_frequency_mhz: 2410,
        bandwidth_mhz: 20,
        power_dbm: 15,
        usage_type: 'primary',
        user_id: 'GNB_001',
        user_name: '5G NR Base Station',
        modulation: 'OFDM',
        signal_quality: 0.85,
        interference_level: 0.2,
        last_updated: new Date().toISOString()
      },
      {
        frequency_start_mhz: 2420,
        frequency_end_mhz: 2440,
        center_frequency_mhz: 2430,
        bandwidth_mhz: 20,
        power_dbm: -10,
        usage_type: 'interference',
        user_id: 'JAMMER_001',
        user_name: 'Unknown Interferer',
        modulation: 'CW',
        signal_quality: 0.1,
        interference_level: 0.9,
        last_updated: new Date().toISOString()
      },
      {
        frequency_start_mhz: 3400,
        frequency_end_mhz: 3500,
        center_frequency_mhz: 3450,
        bandwidth_mhz: 100,
        power_dbm: 20,
        usage_type: 'primary',
        user_id: 'SAT_001',
        user_name: 'OneWeb Satellite',
        modulation: '5G NR',
        signal_quality: 0.92,
        interference_level: 0.05,
        last_updated: new Date().toISOString()
      },
      {
        frequency_start_mhz: 3500,
        frequency_end_mhz: 3600,
        center_frequency_mhz: 3550,
        bandwidth_mhz: 100,
        power_dbm: 0,
        usage_type: 'vacant',
        signal_quality: 1.0,
        interference_level: 0.0,
        last_updated: new Date().toISOString()
      },
      {
        frequency_start_mhz: 28000,
        frequency_end_mhz: 28200,
        center_frequency_mhz: 28100,
        bandwidth_mhz: 200,
        power_dbm: 25,
        usage_type: 'secondary',
        user_id: 'UAV_001',
        user_name: 'UAV Relay',
        modulation: 'mmWave',
        signal_quality: 0.78,
        interference_level: 0.15,
        last_updated: new Date().toISOString()
      },
      {
        frequency_start_mhz: 28200,
        frequency_end_mhz: 28400,
        center_frequency_mhz: 28300,
        bandwidth_mhz: 200,
        power_dbm: 0,
        usage_type: 'protected',
        user_name: 'Radio Astronomy',
        signal_quality: 1.0,
        interference_level: 0.0,
        last_updated: new Date().toISOString()
      }
    ]

    const spectrum_scans: SpectrumScan[] = [
      {
        scan_id: 'SCAN_2_4_GHZ',
        timestamp: new Date().toISOString(),
        frequency_range: {
          start_mhz: 2400,
          end_mhz: 2500,
          resolution_khz: 100
        },
        bands: bands.filter(b => b.center_frequency_mhz >= 2400 && b.center_frequency_mhz <= 2500),
        scan_duration_ms: 250,
        environment: 'Urban',
        location: {
          latitude: 25.0410,
          longitude: 121.5440,
          altitude: 50
        }
      },
      {
        scan_id: 'SCAN_3_5_GHZ',
        timestamp: new Date().toISOString(),
        frequency_range: {
          start_mhz: 3400,
          end_mhz: 3800,
          resolution_khz: 500
        },
        bands: bands.filter(b => b.center_frequency_mhz >= 3400 && b.center_frequency_mhz <= 3800),
        scan_duration_ms: 500,
        environment: 'Urban',
        location: {
          latitude: 25.0410,
          longitude: 121.5440,
          altitude: 50
        }
      },
      {
        scan_id: 'SCAN_28_GHZ',
        timestamp: new Date().toISOString(),
        frequency_range: {
          start_mhz: 28000,
          end_mhz: 28500,
          resolution_khz: 1000
        },
        bands: bands.filter(b => b.center_frequency_mhz >= 28000 && b.center_frequency_mhz <= 28500),
        scan_duration_ms: 100,
        environment: 'Urban',
        location: {
          latitude: 25.0410,
          longitude: 121.5440,
          altitude: 50
        }
      }
    ]

    return {
      timestamp: new Date().toISOString(),
      scene_id: currentScene || 'default',
      spectrum_scans,
      summary: {
        total_bands: bands.length,
        occupied_bands: bands.filter(b => b.usage_type === 'primary' || b.usage_type === 'secondary').length,
        interference_bands: bands.filter(b => b.usage_type === 'interference').length,
        vacant_bands: bands.filter(b => b.usage_type === 'vacant').length,
        spectrum_efficiency: 0.67,
        interference_ratio: 0.12
      }
    }
  }

  const refreshData = useCallback(() => {
    console.log('FrequencySpectrumVisualization: Starting refresh...')
    setIsLoading(true)
    reportIsLoadingToNavbar(true)
    
    setTimeout(() => {
      console.log('FrequencySpectrumVisualization: Generating data...')
      const newData = generateMockData()
      setSpectrumData(newData)
      setIsLoading(false)
      reportIsLoadingToNavbar(false)
      
      if (onReportLastUpdateToNavbar) {
        onReportLastUpdateToNavbar(new Date().toISOString())
      }
      console.log('FrequencySpectrumVisualization: Data loaded successfully')
    }, 1200)
  }, [onReportLastUpdateToNavbar, reportIsLoadingToNavbar])

  useEffect(() => {
    console.log('FrequencySpectrumVisualization: Component mounted, starting initial load...')
    refreshData()
    reportRefreshHandlerToNavbar(refreshData)
  }, [])

  const getUsageTypeColor = (usageType: string) => {
    switch (usageType) {
      case 'primary': return '#00ff00'
      case 'secondary': return '#ffaa00'
      case 'interference': return '#ff0000'
      case 'vacant': return '#888888'
      case 'protected': return '#0088ff'
      default: return '#666666'
    }
  }

  const getUsageTypeIcon = (usageType: string) => {
    switch (usageType) {
      case 'primary': return '🟢'
      case 'secondary': return '🟡'
      case 'interference': return '🔴'
      case 'vacant': return '⚫'
      case 'protected': return '🔵'
      default: return '⚪'
    }
  }

  if (isLoading || !spectrumData) {
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
        <div style={{ fontSize: '14px', opacity: 0.7 }}>正在掃描頻譜</div>
      </div>
    )
  }

  const allBands = spectrumData.spectrum_scans.flatMap(scan => scan.bands)
  const filteredBands = selectedBandType === 'all' 
    ? allBands
    : allBands.filter(b => b.usage_type === selectedBandType)

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      background: '#1a1a1a', 
      color: 'white',
      overflow: 'auto',
      padding: '20px'
    }}>
      {/* 頂部頻譜總覽 */}
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
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>📊 總頻段</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {spectrumData.summary.total_bands}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(0,150,255,0.2)',
          border: '1px solid rgba(0,150,255,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>📡 占用頻段</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {spectrumData.summary.occupied_bands}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,0,0,0.2)',
          border: '1px solid rgba(255,0,0,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>⚠️ 干擾頻段</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {spectrumData.summary.interference_bands}
          </div>
        </div>
        
        <div style={{
          background: 'rgba(255,150,0,0.2)',
          border: '1px solid rgba(255,150,0,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>📈 頻譜效率</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {(spectrumData.summary.spectrum_efficiency * 100).toFixed(1)}%
          </div>
        </div>

        <div style={{
          background: 'rgba(255,0,150,0.2)',
          border: '1px solid rgba(255,0,150,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>🔺 干擾比例</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {(spectrumData.summary.interference_ratio * 100).toFixed(1)}%
          </div>
        </div>
        
        <div style={{
          background: 'rgba(128,128,128,0.2)',
          border: '1px solid rgba(128,128,128,0.5)',
          borderRadius: '8px',
          padding: '12px',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>⚫ 空閒頻段</h3>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
            {spectrumData.summary.vacant_bands}
          </div>
        </div>
      </div>

      {/* 頻譜掃描資訊 */}
      <div style={{
        background: 'rgba(255,255,255,0.1)',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0' }}>📡 頻譜掃描狀況</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
          {spectrumData.spectrum_scans.map((scan) => (
            <div key={scan.scan_id} style={{
              background: 'rgba(255,255,255,0.05)',
              borderRadius: '6px',
              padding: '12px'
            }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>{scan.scan_id}</h4>
              <div style={{ fontSize: '14px' }}>
                <div>頻率範圍: {scan.frequency_range.start_mhz} - {scan.frequency_range.end_mhz} MHz</div>
                <div>解析度: {scan.frequency_range.resolution_khz} kHz</div>
                <div>掃描時間: {scan.scan_duration_ms} ms</div>
                <div>環境: {scan.environment}</div>
                <div>檢測頻段: {scan.bands.length} 個</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 頻段類型過濾器 */}
      <div style={{ marginBottom: '20px' }}>
        <label style={{ marginRight: '12px', fontSize: '16px' }}>頻段類型篩選:</label>
        <select 
          value={selectedBandType}
          onChange={(e) => setSelectedBandType(e.target.value)}
          style={{
            background: '#333',
            color: 'white',
            border: '1px solid #555',
            borderRadius: '4px',
            padding: '8px 12px',
            fontSize: '14px'
          }}
        >
          <option value="all">全部頻段</option>
          <option value="primary">主要用戶</option>
          <option value="secondary">次要用戶</option>
          <option value="interference">干擾源</option>
          <option value="vacant">空閒頻段</option>
          <option value="protected">保護頻段</option>
        </select>
      </div>

      {/* 頻段詳情 */}
      <div>
        <h3 style={{ marginBottom: '16px' }}>📻 頻段詳細資訊</h3>
        <div style={{ 
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
          gap: '16px'
        }}>
          {filteredBands.map((band, index) => (
            <div key={index} style={{
              background: 'rgba(255,255,255,0.05)',
              border: `2px solid ${getUsageTypeColor(band.usage_type)}`,
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
                  {getUsageTypeIcon(band.usage_type)} {band.center_frequency_mhz} MHz
                </h4>
                <span style={{
                  background: `${getUsageTypeColor(band.usage_type)}30`,
                  color: getUsageTypeColor(band.usage_type),
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  textTransform: 'uppercase'
                }}>
                  {band.usage_type}
                </span>
              </div>

              <div style={{ fontSize: '14px', marginBottom: '12px' }}>
                <div>頻率範圍: {band.frequency_start_mhz} - {band.frequency_end_mhz} MHz</div>
                <div>頻寬: {band.bandwidth_mhz} MHz</div>
                <div>功率: {band.power_dbm} dBm</div>
                {band.user_name && <div>用戶: {band.user_name}</div>}
                {band.modulation && <div>調變: {band.modulation}</div>}
                <div>信號品質: {(band.signal_quality * 100).toFixed(1)}%</div>
                <div>干擾等級: {(band.interference_level * 100).toFixed(1)}%</div>
              </div>

              {/* 信號品質條 */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>信號品質</div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  height: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: band.signal_quality > 0.8 ? '#00ff00' : 
                               band.signal_quality > 0.5 ? '#ffaa00' : '#ff0000',
                    height: '100%',
                    width: `${band.signal_quality * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              {/* 干擾等級條 */}
              <div style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '12px', marginBottom: '4px' }}>干擾等級</div>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: '4px',
                  height: '6px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    background: band.interference_level > 0.7 ? '#ff0000' : 
                               band.interference_level > 0.3 ? '#ffaa00' : '#00ff00',
                    height: '100%',
                    width: `${band.interference_level * 100}%`,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '8px' }}>
                最後更新: {new Date(band.last_updated).toLocaleTimeString()}
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
        場景: {spectrumData.scene_id} | 最後更新: {new Date(spectrumData.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

export default FrequencySpectrumVisualization