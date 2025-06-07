import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useWebSocket } from '../../hooks/useWebSocket'
import { WebSocketEvent } from '../../types/charts'

// 頻譜數據類型
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
  signal_quality: number // 0-1
  interference_level: number // 0-1
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

interface FrequencySpectrumVisualizationProps {
  height?: number
  frequencyRange?: { start: number; end: number }
  realTimeEnabled?: boolean
  showPowerSpectrum?: boolean
  showInterference?: boolean
  showAllocations?: boolean
  onBandClick?: (band: FrequencyBand) => void
  onFrequencyHover?: (frequency: number, power: number) => void
}

const FrequencySpectrumVisualization: React.FC<FrequencySpectrumVisualizationProps> = ({
  height = 400,
  frequencyRange = { start: 2000, end: 2600 }, // MHz
  realTimeEnabled = true,
  showPowerSpectrum = true,
  showInterference = true,
  showAllocations = true,
  onBandClick,
  onFrequencyHover
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  const spectrumHistoryRef = useRef<SpectrumScan[]>([])
  
  // 狀態管理
  const [currentScan, setCurrentScan] = useState<SpectrumScan | null>(null)
  const [frequencyBands, setFrequencyBands] = useState<FrequencyBand[]>([])
  const [hoveredFrequency, setHoveredFrequency] = useState<number | null>(null)
  const [selectedBand, setSelectedBand] = useState<FrequencyBand | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  
  // 可視化配置
  const [displayMode, setDisplayMode] = useState<'spectrum' | 'waterfall' | 'allocation'>('spectrum')
  const [timeWindow, setTimeWindow] = useState(60) // 秒
  const [powerRange, setPowerRange] = useState({ min: -120, max: -40 }) // dBm
  const [resolutionBandwidth, setResolutionBandwidth] = useState(100) // kHz
  const [averagingEnabled, setAveragingEnabled] = useState(true)
  const [peakHoldEnabled, setPeakHoldEnabled] = useState(false)
  
  // 分析數據
  const [occupancyRate, setOccupancyRate] = useState(0)
  const [interferenceCount, setInterferenceCount] = useState(0)
  const [spectrumEfficiency, setSpectrumEfficiency] = useState(0)
  const [lastUpdate, setLastUpdate] = useState<string | null>(null)

  // WebSocket 連接處理頻譜數據
  const { isConnected, sendMessage } = useWebSocket({
    url: 'ws://localhost:8080/ws/spectrum-monitor',
    enableReconnect: realTimeEnabled,
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log('Frequency Spectrum Visualization WebSocket 已連接')
      if (realTimeEnabled) {
        sendMessage({
          type: 'subscribe',
          topics: ['spectrum_scans', 'frequency_allocations', 'interference_reports']
        })
        
        // 請求頻譜掃描
        sendMessage({
          type: 'request_spectrum_scan',
          frequency_range: frequencyRange,
          resolution_khz: resolutionBandwidth
        })
      }
    }
  })

  // 處理 WebSocket 消息
  function handleWebSocketMessage(event: WebSocketEvent) {
    try {
      switch (event.type) {
        case 'spectrum_scan_result':
          const scanData = event.data as SpectrumScan
          setCurrentScan(scanData)
          setFrequencyBands(scanData.bands)
          
          // 更新歷史記錄
          spectrumHistoryRef.current = [scanData, ...spectrumHistoryRef.current].slice(0, 100)
          
          // 計算統計指標
          updateSpectrumAnalytics(scanData)
          setLastUpdate(event.timestamp)
          break
          
        case 'frequency_allocation_update':
          // 更新頻率分配信息
          if (event.data.allocations) {
            updateFrequencyAllocations(event.data.allocations)
          }
          break
          
        case 'interference_detection':
          // 更新干擾檢測結果
          if (event.data.interference_bands) {
            updateInterferenceBands(event.data.interference_bands)
          }
          break
      }
    } catch (error) {
      console.error('處理頻譜 WebSocket 消息失敗:', error)
    }
  }

  // 更新頻譜分析指標
  const updateSpectrumAnalytics = useCallback((scan: SpectrumScan) => {
    const totalBandwidth = frequencyRange.end - frequencyRange.start
    const occupiedBandwidth = scan.bands
      .filter(band => band.usage_type !== 'vacant')
      .reduce((sum, band) => sum + band.bandwidth_mhz, 0)
    
    const interferingBands = scan.bands.filter(band => 
      band.usage_type === 'interference' || band.interference_level > 0.3
    )
    
    const averageSignalQuality = scan.bands
      .filter(band => band.usage_type !== 'vacant')
      .reduce((sum, band) => sum + band.signal_quality, 0) / 
      Math.max(1, scan.bands.filter(band => band.usage_type !== 'vacant').length)
    
    setOccupancyRate((occupiedBandwidth / totalBandwidth) * 100)
    setInterferenceCount(interferingBands.length)
    setSpectrumEfficiency(averageSignalQuality * 100)
  }, [frequencyRange])

  // 更新頻率分配
  const updateFrequencyAllocations = useCallback((allocations: any[]) => {
    setFrequencyBands(prev => {
      const updated = [...prev]
      allocations.forEach(allocation => {
        const existingIndex = updated.findIndex(band => 
          band.center_frequency_mhz === allocation.center_frequency_mhz
        )
        if (existingIndex >= 0) {
          updated[existingIndex] = { ...updated[existingIndex], ...allocation }
        } else {
          updated.push(allocation)
        }
      })
      return updated
    })
  }, [])

  // 更新干擾頻段
  const updateInterferenceBands = useCallback((interferenceBands: any[]) => {
    setFrequencyBands(prev => {
      const updated = [...prev]
      interferenceBands.forEach(interference => {
        const existingIndex = updated.findIndex(band => 
          Math.abs(band.center_frequency_mhz - interference.frequency_mhz) < interference.bandwidth_mhz / 2
        )
        if (existingIndex >= 0) {
          updated[existingIndex] = {
            ...updated[existingIndex],
            interference_level: Math.max(updated[existingIndex].interference_level, interference.level),
            usage_type: interference.level > 0.5 ? 'interference' : updated[existingIndex].usage_type
          }
        }
      })
      return updated
    })
    setInterferenceCount(interferenceBands.length)
  }, [])

  // 繪製頻譜圖
  const drawSpectrum = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 設置畫布大小
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width
    canvas.height = rect.height

    const width = canvas.width
    const height = canvas.height
    const margin = { top: 20, right: 60, bottom: 60, left: 80 }
    const plotWidth = width - margin.left - margin.right
    const plotHeight = height - margin.top - margin.bottom

    // 清除畫布
    ctx.fillStyle = '#1a1a1a'
    ctx.fillRect(0, 0, width, height)

    // 根據顯示模式繪製
    switch (displayMode) {
      case 'spectrum':
        drawSpectrumPlot(ctx, margin, plotWidth, plotHeight)
        break
      case 'waterfall':
        drawWaterfallPlot(ctx, margin, plotWidth, plotHeight)
        break
      case 'allocation':
        drawAllocationPlot(ctx, margin, plotWidth, plotHeight)
        break
    }

    // 繪製坐標軸
    drawAxes(ctx, margin, plotWidth, plotHeight)

    // 繪製標籤和圖例
    drawLabelsAndLegend(ctx, width, height, margin)

  }, [displayMode, frequencyBands, frequencyRange, powerRange, hoveredFrequency])

  // 繪製功率頻譜圖
  const drawSpectrumPlot = (
    ctx: CanvasRenderingContext2D, 
    margin: any, 
    plotWidth: number, 
    plotHeight: number
  ) => {
    if (frequencyBands.length === 0) return

    ctx.save()
    ctx.translate(margin.left, margin.top)

    // 創建頻率到像素的映射函數
    const freqToX = (freq: number) => 
      ((freq - frequencyRange.start) / (frequencyRange.end - frequencyRange.start)) * plotWidth

    const powerToY = (power: number) => 
      plotHeight - ((power - powerRange.min) / (powerRange.max - powerRange.min)) * plotHeight

    if (showPowerSpectrum) {
      // 繪製功率頻譜曲線
      ctx.strokeStyle = '#00ff00'
      ctx.lineWidth = 2
      ctx.beginPath()

      let firstPoint = true
      frequencyBands
        .sort((a, b) => a.center_frequency_mhz - b.center_frequency_mhz)
        .forEach(band => {
          const x = freqToX(band.center_frequency_mhz)
          const y = powerToY(band.power_dbm)
          
          if (firstPoint) {
            ctx.moveTo(x, y)
            firstPoint = false
          } else {
            ctx.lineTo(x, y)
          }
        })
      ctx.stroke()

      // 填充區域
      if (averagingEnabled) {
        ctx.fillStyle = 'rgba(0, 255, 0, 0.1)'
        ctx.fill()
      }
    }

    // 繪製頻段分配
    if (showAllocations) {
      frequencyBands.forEach(band => {
        const x1 = freqToX(band.frequency_start_mhz)
        const x2 = freqToX(band.frequency_end_mhz)
        const y = powerToY(band.power_dbm)
        const width = x2 - x1
        const height = plotHeight - y

        // 根據使用類型選擇顏色
        const colors = {
          primary: 'rgba(0, 150, 255, 0.6)',
          secondary: 'rgba(255, 165, 0, 0.6)',
          interference: 'rgba(255, 0, 0, 0.8)',
          vacant: 'rgba(128, 128, 128, 0.3)',
          protected: 'rgba(128, 0, 128, 0.6)'
        }

        ctx.fillStyle = colors[band.usage_type] || colors.vacant
        ctx.fillRect(x1, y, width, height)

        // 繪製頻段邊框
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 1
        ctx.strokeRect(x1, y, width, height)

        // 顯示用戶信息
        if (band.user_name && width > 30) {
          ctx.fillStyle = '#fff'
          ctx.font = '10px Arial'
          ctx.textAlign = 'center'
          ctx.fillText(
            band.user_name.substring(0, 8),
            x1 + width / 2,
            y + 15
          )
        }
      })
    }

    // 繪製干擾標記
    if (showInterference) {
      frequencyBands
        .filter(band => band.interference_level > 0.2)
        .forEach(band => {
          const x = freqToX(band.center_frequency_mhz)
          const y = powerToY(band.power_dbm)
          
          // 干擾警告圖標
          ctx.fillStyle = '#ff0000'
          ctx.beginPath()
          ctx.arc(x, y - 10, 5, 0, 2 * Math.PI)
          ctx.fill()
          
          // 脈衝效果
          const time = Date.now() * 0.01
          const pulseRadius = 5 + Math.sin(time + x * 0.1) * 3
          ctx.strokeStyle = '#ff0000'
          ctx.lineWidth = 2
          ctx.beginPath()
          ctx.arc(x, y - 10, pulseRadius, 0, 2 * Math.PI)
          ctx.stroke()
        })
    }

    // 繪製懸停指示器
    if (hoveredFrequency !== null) {
      const x = freqToX(hoveredFrequency)
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 1
      ctx.setLineDash([5, 5])
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, plotHeight)
      ctx.stroke()
      ctx.setLineDash([])
    }

    ctx.restore()
  }

  // 繪製瀑布圖
  const drawWaterfallPlot = (
    ctx: CanvasRenderingContext2D,
    margin: any,
    plotWidth: number,
    plotHeight: number
  ) => {
    ctx.save()
    ctx.translate(margin.left, margin.top)

    const scans = spectrumHistoryRef.current.slice(0, 50)
    if (scans.length === 0) return

    const scanHeight = plotHeight / scans.length
    
    scans.forEach((scan, scanIndex) => {
      const y = scanIndex * scanHeight
      
      scan.bands
        .sort((a, b) => a.center_frequency_mhz - b.center_frequency_mhz)
        .forEach(band => {
          const x1 = ((band.frequency_start_mhz - frequencyRange.start) / 
                      (frequencyRange.end - frequencyRange.start)) * plotWidth
          const x2 = ((band.frequency_end_mhz - frequencyRange.start) / 
                      (frequencyRange.end - frequencyRange.start)) * plotWidth
          
          // 根據功率強度著色
          const intensity = (band.power_dbm - powerRange.min) / (powerRange.max - powerRange.min)
          const hue = (1 - intensity) * 240 // 藍色到紅色
          ctx.fillStyle = `hsl(${hue}, 100%, ${50 + intensity * 30}%)`
          
          ctx.fillRect(x1, y, x2 - x1, scanHeight)
        })
    })

    ctx.restore()
  }

  // 繪製分配圖
  const drawAllocationPlot = (
    ctx: CanvasRenderingContext2D,
    margin: any,
    plotWidth: number,
    plotHeight: number
  ) => {
    ctx.save()
    ctx.translate(margin.left, margin.top)

    const allocatedBands = frequencyBands.filter(band => band.usage_type !== 'vacant')
    const rowHeight = plotHeight / Math.max(1, allocatedBands.length)

    allocatedBands.forEach((band, index) => {
      const y = index * rowHeight
      const x1 = ((band.frequency_start_mhz - frequencyRange.start) / 
                  (frequencyRange.end - frequencyRange.start)) * plotWidth
      const x2 = ((band.frequency_end_mhz - frequencyRange.start) / 
                  (frequencyRange.end - frequencyRange.start)) * plotWidth

      // 背景
      const colors = {
        primary: '#0066cc',
        secondary: '#ff8800',
        interference: '#cc0000',
        protected: '#8800cc'
      }
      
      ctx.fillStyle = colors[band.usage_type as keyof typeof colors] || '#666666'
      ctx.fillRect(x1, y + 2, x2 - x1, rowHeight - 4)

      // 邊框
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 1
      ctx.strokeRect(x1, y + 2, x2 - x1, rowHeight - 4)

      // 文字標籤
      ctx.fillStyle = '#ffffff'
      ctx.font = '12px Arial'
      ctx.textAlign = 'left'
      const text = `${band.user_name || band.usage_type} (${band.center_frequency_mhz.toFixed(1)} MHz)`
      ctx.fillText(text, x1 + 5, y + rowHeight / 2 + 4)

      // 質量指示器
      const qualityX = x2 - 20
      const qualityY = y + 5
      const qualitySize = 10
      const qualityColor = band.signal_quality > 0.7 ? '#00ff00' : 
                          band.signal_quality > 0.4 ? '#ffff00' : '#ff0000'
      
      ctx.fillStyle = qualityColor
      ctx.fillRect(qualityX, qualityY, qualitySize, qualitySize)
    })

    ctx.restore()
  }

  // 繪製坐標軸
  const drawAxes = (
    ctx: CanvasRenderingContext2D,
    margin: any,
    plotWidth: number,
    plotHeight: number
  ) => {
    ctx.strokeStyle = '#666666'
    ctx.lineWidth = 1
    ctx.fillStyle = '#cccccc'
    ctx.font = '12px Arial'

    // X軸（頻率）
    ctx.beginPath()
    ctx.moveTo(margin.left, margin.top + plotHeight)
    ctx.lineTo(margin.left + plotWidth, margin.top + plotHeight)
    ctx.stroke()

    // X軸刻度
    const freqStep = (frequencyRange.end - frequencyRange.start) / 10
    for (let i = 0; i <= 10; i++) {
      const freq = frequencyRange.start + i * freqStep
      const x = margin.left + (i / 10) * plotWidth
      
      ctx.beginPath()
      ctx.moveTo(x, margin.top + plotHeight)
      ctx.lineTo(x, margin.top + plotHeight + 5)
      ctx.stroke()
      
      ctx.textAlign = 'center'
      ctx.fillText(freq.toFixed(0), x, margin.top + plotHeight + 20)
    }

    // Y軸（功率）
    if (displayMode === 'spectrum') {
      ctx.beginPath()
      ctx.moveTo(margin.left, margin.top)
      ctx.lineTo(margin.left, margin.top + plotHeight)
      ctx.stroke()

      // Y軸刻度
      const powerStep = (powerRange.max - powerRange.min) / 8
      for (let i = 0; i <= 8; i++) {
        const power = powerRange.min + i * powerStep
        const y = margin.top + plotHeight - (i / 8) * plotHeight
        
        ctx.beginPath()
        ctx.moveTo(margin.left - 5, y)
        ctx.lineTo(margin.left, y)
        ctx.stroke()
        
        ctx.textAlign = 'right'
        ctx.fillText(power.toFixed(0), margin.left - 10, y + 4)
      }
    }
  }

  // 繪製標籤和圖例
  const drawLabelsAndLegend = (
    ctx: CanvasRenderingContext2D,
    width: number,
    height: number,
    margin: any
  ) => {
    ctx.fillStyle = '#ffffff'
    ctx.font = '14px Arial'

    // X軸標籤
    ctx.textAlign = 'center'
    ctx.fillText('頻率 (MHz)', width / 2, height - 10)

    // Y軸標籤
    if (displayMode === 'spectrum') {
      ctx.save()
      ctx.translate(15, height / 2)
      ctx.rotate(-Math.PI / 2)
      ctx.textAlign = 'center'
      ctx.fillText('功率 (dBm)', 0, 0)
      ctx.restore()
    }

    // 圖例
    if (showAllocations && displayMode !== 'waterfall') {
      const legendItems = [
        { color: 'rgba(0, 150, 255, 0.6)', label: '主要用戶' },
        { color: 'rgba(255, 165, 0, 0.6)', label: '次要用戶' },
        { color: 'rgba(255, 0, 0, 0.8)', label: '干擾' },
        { color: 'rgba(128, 128, 128, 0.3)', label: '空閒' },
        { color: 'rgba(128, 0, 128, 0.6)', label: '保護頻段' }
      ]

      const legendX = width - 150
      const legendY = 30
      
      legendItems.forEach((item, index) => {
        const y = legendY + index * 20
        
        ctx.fillStyle = item.color
        ctx.fillRect(legendX, y, 15, 15)
        
        ctx.fillStyle = '#ffffff'
        ctx.font = '12px Arial'
        ctx.textAlign = 'left'
        ctx.fillText(item.label, legendX + 20, y + 12)
      })
    }
  }

  // 鼠標移動處理
  const handleMouseMove = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return

    const rect = canvas.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    const margin = { top: 20, right: 60, bottom: 60, left: 80 }
    const plotWidth = canvas.width - margin.left - margin.right

    if (x >= margin.left && x <= margin.left + plotWidth) {
      const relativeX = (x - margin.left) / plotWidth
      const frequency = frequencyRange.start + relativeX * (frequencyRange.end - frequencyRange.start)
      
      setHoveredFrequency(frequency)
      
      // 查找對應的功率值
      const nearestBand = frequencyBands
        .sort((a, b) => 
          Math.abs(a.center_frequency_mhz - frequency) - Math.abs(b.center_frequency_mhz - frequency)
        )[0]
      
      if (nearestBand && onFrequencyHover) {
        onFrequencyHover(frequency, nearestBand.power_dbm)
      }
    } else {
      setHoveredFrequency(null)
    }
  }, [frequencyBands, frequencyRange, onFrequencyHover])

  // 鼠標點擊處理
  const handleMouseClick = useCallback((event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!hoveredFrequency) return

    const clickedBand = frequencyBands.find(band => 
      hoveredFrequency >= band.frequency_start_mhz && 
      hoveredFrequency <= band.frequency_end_mhz
    )

    if (clickedBand) {
      setSelectedBand(clickedBand)
      if (onBandClick) {
        onBandClick(clickedBand)
      }
    }
  }, [hoveredFrequency, frequencyBands, onBandClick])

  // 渲染循環
  useEffect(() => {
    const animate = () => {
      drawSpectrum()
      if (realTimeEnabled && isConnected) {
        animationFrameRef.current = requestAnimationFrame(animate)
      }
    }
    
    if (realTimeEnabled && isConnected) {
      animate()
    } else {
      drawSpectrum()
    }
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [drawSpectrum, realTimeEnabled, isConnected])

  // 模擬數據（開發測試用）
  useEffect(() => {
    if (!realTimeEnabled && frequencyBands.length === 0) {
      const mockBands: FrequencyBand[] = [
        {
          frequency_start_mhz: 2100,
          frequency_end_mhz: 2120,
          center_frequency_mhz: 2110,
          bandwidth_mhz: 20,
          power_dbm: -65,
          usage_type: 'primary',
          user_name: 'UE-001',
          modulation: 'OFDM',
          signal_quality: 0.85,
          interference_level: 0.1,
          last_updated: new Date().toISOString()
        },
        {
          frequency_start_mhz: 2140,
          frequency_end_mhz: 2160,
          center_frequency_mhz: 2150,
          bandwidth_mhz: 20,
          power_dbm: -70,
          usage_type: 'interference',
          user_name: 'Jammer-1',
          signal_quality: 0.0,
          interference_level: 0.8,
          last_updated: new Date().toISOString()
        },
        {
          frequency_start_mhz: 2300,
          frequency_end_mhz: 2320,
          center_frequency_mhz: 2310,
          bandwidth_mhz: 20,
          power_dbm: -60,
          usage_type: 'secondary',
          user_name: 'UE-002',
          modulation: 'QPSK',
          signal_quality: 0.65,
          interference_level: 0.3,
          last_updated: new Date().toISOString()
        }
      ]
      
      setFrequencyBands(mockBands)
      setOccupancyRate(12)
      setInterferenceCount(1)
      setSpectrumEfficiency(75)
    }
  }, [realTimeEnabled, frequencyBands.length])

  // 記憶化的統計數據
  const spectrumStats = useMemo(() => {
    const totalBands = frequencyBands.length
    const activeBands = frequencyBands.filter(band => band.usage_type !== 'vacant').length
    const interferingBands = frequencyBands.filter(band => band.interference_level > 0.3).length
    const averagePower = frequencyBands.reduce((sum, band) => sum + band.power_dbm, 0) / Math.max(1, totalBands)
    
    return {
      total_bands: totalBands,
      active_bands: activeBands,
      interfering_bands: interferingBands,
      average_power: averagePower,
      occupancy_rate: occupancyRate,
      spectrum_efficiency: spectrumEfficiency
    }
  }, [frequencyBands, occupancyRate, spectrumEfficiency])

  return (
    <div className="frequency-spectrum-visualization" style={{
      width: '100%',
      height: `${height}px`,
      background: '#1a1a1a',
      position: 'relative',
      borderRadius: '4px',
      border: '1px solid #333'
    }}>
      {/* 控制面板 */}
      <div style={{
        position: 'absolute',
        top: '10px',
        left: '10px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '4px',
        zIndex: 100,
        minWidth: '250px'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>頻譜監控</h4>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label>
            顯示模式:
            <select
              value={displayMode}
              onChange={(e) => setDisplayMode(e.target.value as any)}
              style={{ marginLeft: '5px', padding: '2px' }}
            >
              <option value="spectrum">功率頻譜</option>
              <option value="waterfall">瀑布圖</option>
              <option value="allocation">頻率分配</option>
            </select>
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={realTimeEnabled}
              onChange={(e) => setRealTimeEnabled(e.target.checked)}
            />
            實時模式 {isConnected ? '🟢' : '🔴'}
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={showPowerSpectrum}
              onChange={(e) => setShowPowerSpectrum(e.target.checked)}
            />
            功率頻譜
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={showInterference}
              onChange={(e) => setShowInterference(e.target.checked)}
            />
            干擾標記
          </label>
          
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <input
              type="checkbox"
              checked={showAllocations}
              onChange={(e) => setShowAllocations(e.target.checked)}
            />
            頻率分配
          </label>
        </div>
      </div>
      
      {/* 統計面板 */}
      <div style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '4px',
        zIndex: 100,
        minWidth: '200px'
      }}>
        <h4 style={{ margin: '0 0 10px 0' }}>頻譜統計</h4>
        <div style={{ fontSize: '12px', lineHeight: '1.4' }}>
          <div>佔用率: {occupancyRate.toFixed(1)}%</div>
          <div>干擾源: {interferenceCount}</div>
          <div>頻譜效率: {spectrumEfficiency.toFixed(1)}%</div>
          <div>活躍頻段: {spectrumStats.active_bands}/{spectrumStats.total_bands}</div>
          <div>平均功率: {spectrumStats.average_power.toFixed(1)} dBm</div>
        </div>
        
        {lastUpdate && (
          <div style={{ fontSize: '10px', marginTop: '10px', color: '#aaa' }}>
            最後更新: {new Date(lastUpdate).toLocaleTimeString()}
          </div>
        )}
      </div>
      
      {/* 懸停信息 */}
      {hoveredFrequency && (
        <div style={{
          position: 'absolute',
          bottom: '80px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(0, 0, 0, 0.9)',
          color: 'white',
          padding: '8px',
          borderRadius: '4px',
          fontSize: '12px',
          zIndex: 100,
          whiteSpace: 'nowrap'
        }}>
          頻率: {hoveredFrequency.toFixed(1)} MHz
          {selectedBand && (
            <>
              <br />功率: {selectedBand.power_dbm.toFixed(1)} dBm
              <br />用戶: {selectedBand.user_name || '未知'}
              <br />類型: {selectedBand.usage_type}
            </>
          )}
        </div>
      )}
      
      {/* 主畫布 */}
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouseMove}
        onClick={handleMouseClick}
        style={{
          width: '100%',
          height: '100%',
          cursor: 'crosshair'
        }}
      />
    </div>
  )
}

export default FrequencySpectrumVisualization