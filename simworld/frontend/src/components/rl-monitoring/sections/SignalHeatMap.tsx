import React, { useState, useEffect, useRef } from 'react'
import { simworldFetch } from '../../../config/api-config'
import './SignalHeatMap.scss'

interface SignalHeatMapProps {
    selectedSatellite?: string
    onSatelliteSelect?: (satelliteId: string) => void
}

interface HeatMapData {
    x: number
    y: number
    value: number
    satellite_id: string
    satellite_name: string
    signal_type: 'rsrp' | 'rsrq' | 'sinr'
}

interface SatellitePosition {
    id: string
    name: string
    x: number
    y: number
    signal_strength: number
    coverage_radius: number
    constellation: string
}

const SignalHeatMap: React.FC<SignalHeatMapProps> = ({
    selectedSatellite,
    onSatelliteSelect
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [heatMapData, setHeatMapData] = useState<HeatMapData[]>([])
    const [satellites, setSatellites] = useState<SatellitePosition[]>([])
    const [signalType, setSignalType] = useState<'rsrp' | 'rsrq' | 'sinr'>('rsrp')
    const [isLoading, setIsLoading] = useState(true)
    const [showContours, setShowContours] = useState(true)
    const [showSatellites, setShowSatellites] = useState(true)
    const [intensity, setIntensity] = useState(0.7)
    const [radius, setRadius] = useState(50)
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
    const [hoveredValue, setHoveredValue] = useState<number | null>(null)
    const animationRef = useRef<number>()

    // 獲取信號數據
    const fetchSignalData = async () => {
        try {
            const response = await simworldFetch('/v1/signals/heatmap', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    signal_type: signalType,
                    resolution: 50,
                    area: { width: 800, height: 600 }
                })
            })
            
            if (response.ok) {
                const data = await response.json()
                setHeatMapData(data.heat_map || [])
                setSatellites(data.satellites || [])
            } else {
                generateMockHeatMapData()
            }
        } catch (error) {
            console.error('獲取信號數據失敗:', error)
            generateMockHeatMapData()
        } finally {
            setIsLoading(false)
        }
    }

    // 生成模擬熱力圖數據
    const generateMockHeatMapData = () => {
        const mockSatellites: SatellitePosition[] = [
            {
                id: 'starlink-1234',
                name: 'Starlink-1234',
                x: 200,
                y: 150,
                signal_strength: 85,
                coverage_radius: 120,
                constellation: 'Starlink'
            },
            {
                id: 'starlink-5678',
                name: 'Starlink-5678',
                x: 450,
                y: 200,
                signal_strength: 78,
                coverage_radius: 100,
                constellation: 'Starlink'
            },
            {
                id: 'kuiper-1001',
                name: 'Kuiper-1001',
                x: 350,
                y: 400,
                signal_strength: 92,
                coverage_radius: 140,
                constellation: 'Kuiper'
            },
            {
                id: 'oneweb-2001',
                name: 'OneWeb-2001',
                x: 150,
                y: 350,
                signal_strength: 72,
                coverage_radius: 90,
                constellation: 'OneWeb'
            },
            {
                id: 'starlink-9012',
                name: 'Starlink-9012',
                x: 600,
                y: 300,
                signal_strength: 88,
                coverage_radius: 110,
                constellation: 'Starlink'
            }
        ]

        setSatellites(mockSatellites)

        // 生成熱力圖數據
        const heatData: HeatMapData[] = []
        const gridSize = 20
        const width = 800
        const height = 600

        for (let x = 0; x < width; x += gridSize) {
            for (let y = 0; y < height; y += gridSize) {
                let maxValue = 0
                let closestSatellite = mockSatellites[0]

                mockSatellites.forEach(satellite => {
                    const distance = Math.sqrt(
                        (x - satellite.x) ** 2 + (y - satellite.y) ** 2
                    )
                    
                    if (distance < satellite.coverage_radius) {
                        const value = calculateSignalValue(signalType, satellite.signal_strength, distance, satellite.coverage_radius)
                        if (value > maxValue) {
                            maxValue = value
                            closestSatellite = satellite
                        }
                    }
                })

                if (maxValue > 0) {
                    heatData.push({
                        x,
                        y,
                        value: maxValue,
                        satellite_id: closestSatellite.id,
                        satellite_name: closestSatellite.name,
                        signal_type: signalType
                    })
                }
            }
        }

        setHeatMapData(heatData)
    }

    // 計算信號值
    const calculateSignalValue = (
        type: 'rsrp' | 'rsrq' | 'sinr',
        baseStrength: number,
        distance: number,
        maxRadius: number
    ): number => {
        const normalizedDistance = distance / maxRadius
        const attenuationFactor = 1 - normalizedDistance * 0.8

        switch (type) {
            case 'rsrp':
                return Math.max(0, (baseStrength - 20) * attenuationFactor)
            case 'rsrq':
                return Math.max(0, (baseStrength - 10) * attenuationFactor)
            case 'sinr':
                return Math.max(0, (baseStrength - 30) * attenuationFactor)
            default:
                return 0
        }
    }

    // 獲取顏色
    const getHeatColor = (value: number): string => {
        const normalizedValue = Math.min(1, Math.max(0, value / 100))
        
        if (normalizedValue < 0.25) {
            // 藍色到青色
            const r = 0
            const g = Math.floor(normalizedValue * 4 * 255)
            const b = 255
            return `rgb(${r}, ${g}, ${b})`
        } else if (normalizedValue < 0.5) {
            // 青色到綠色
            const r = 0
            const g = 255
            const b = Math.floor((0.5 - normalizedValue) * 4 * 255)
            return `rgb(${r}, ${g}, ${b})`
        } else if (normalizedValue < 0.75) {
            // 綠色到黃色
            const r = Math.floor((normalizedValue - 0.5) * 4 * 255)
            const g = 255
            const b = 0
            return `rgb(${r}, ${g}, ${b})`
        } else {
            // 黃色到紅色
            const r = 255
            const g = Math.floor((1 - normalizedValue) * 4 * 255)
            const b = 0
            return `rgb(${r}, ${g}, ${b})`
        }
    }

    // 渲染熱力圖
    const renderHeatMap = () => {
        const canvas = canvasRef.current
        if (!canvas) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        // 設置畫布尺寸
        canvas.width = 800
        canvas.height = 600

        // 清空畫布
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        // 繪製背景
        ctx.fillStyle = '#0a0a0a'
        ctx.fillRect(0, 0, canvas.width, canvas.height)

        // 繪製熱力圖
        heatMapData.forEach(point => {
            const alpha = intensity * (point.value / 100)
            const color = getHeatColor(point.value)
            
            ctx.globalAlpha = alpha
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(point.x, point.y, radius, 0, Math.PI * 2)
            ctx.fill()
        })

        ctx.globalAlpha = 1

        // 繪製等值線
        if (showContours) {
            drawContours(ctx)
        }

        // 繪製衛星位置
        if (showSatellites) {
            drawSatellites(ctx)
        }

        // 繪製圖例
        drawLegend(ctx)
    }

    // 繪製等值線
    const drawContours = (ctx: CanvasRenderingContext2D) => {
        const contourLevels = [20, 40, 60, 80]
        
        contourLevels.forEach(level => {
            ctx.strokeStyle = `rgba(255, 255, 255, 0.3)`
            ctx.lineWidth = 1
            ctx.setLineDash([5, 5])
            
            // 簡化的等值線繪製
            heatMapData.forEach(point => {
                if (Math.abs(point.value - level) < 5) {
                    ctx.beginPath()
                    ctx.arc(point.x, point.y, 3, 0, Math.PI * 2)
                    ctx.stroke()
                }
            })
        })
        
        ctx.setLineDash([])
    }

    // 繪製衛星
    const drawSatellites = (ctx: CanvasRenderingContext2D) => {
        const constellationColors = {
            'Starlink': '#4FC3F7',
            'Kuiper': '#FF9800',
            'OneWeb': '#9C27B0'
        }

        satellites.forEach(satellite => {
            const color = constellationColors[satellite.constellation as keyof typeof constellationColors] || '#4FC3F7'
            const isSelected = satellite.id === selectedSatellite
            
            // 繪製覆蓋範圍
            ctx.globalAlpha = 0.1
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(satellite.x, satellite.y, satellite.coverage_radius, 0, Math.PI * 2)
            ctx.fill()
            
            ctx.globalAlpha = 1
            
            // 繪製衛星
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(satellite.x, satellite.y, isSelected ? 8 : 6, 0, Math.PI * 2)
            ctx.fill()
            
            // 繪製選中指示
            if (isSelected) {
                ctx.strokeStyle = '#FFFFFF'
                ctx.lineWidth = 2
                ctx.beginPath()
                ctx.arc(satellite.x, satellite.y, 12, 0, Math.PI * 2)
                ctx.stroke()
            }
            
            // 繪製名稱
            ctx.fillStyle = '#FFFFFF'
            ctx.font = '12px Arial'
            ctx.fillText(satellite.name, satellite.x + 10, satellite.y - 10)
        })
    }

    // 繪製圖例
    const drawLegend = (ctx: CanvasRenderingContext2D) => {
        const legendX = 650
        const legendY = 20
        const legendWidth = 140
        const legendHeight = 120
        
        // 背景
        ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
        ctx.fillRect(legendX, legendY, legendWidth, legendHeight)
        
        // 標題
        ctx.fillStyle = '#FFFFFF'
        ctx.font = '14px Arial'
        ctx.fillText('信號強度', legendX + 10, legendY + 20)
        
        // 顏色條
        const colorBarHeight = 60
        const colorBarWidth = 20
        const colorBarX = legendX + 10
        const colorBarY = legendY + 30
        
        for (let i = 0; i < colorBarHeight; i++) {
            const value = (1 - i / colorBarHeight) * 100
            const color = getHeatColor(value)
            ctx.fillStyle = color
            ctx.fillRect(colorBarX, colorBarY + i, colorBarWidth, 1)
        }
        
        // 數值標籤
        ctx.fillStyle = '#FFFFFF'
        ctx.font = '10px Arial'
        const labels = ['100', '75', '50', '25', '0']
        labels.forEach((label, index) => {
            const y = colorBarY + (index * colorBarHeight / (labels.length - 1))
            ctx.fillText(label, colorBarX + colorBarWidth + 5, y + 3)
        })
        
        // 單位
        const units = {
            rsrp: 'dBm',
            rsrq: 'dB',
            sinr: 'dB'
        }
        ctx.fillText(`(${units[signalType]})`, colorBarX + colorBarWidth + 5, colorBarY + colorBarHeight + 15)
    }

    // 鼠標事件處理
    const handleMouseMove = (e: React.MouseEvent) => {
        const canvas = canvasRef.current
        if (!canvas) return

        const rect = canvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        setMousePos({ x, y })

        // 查找最近的熱力圖點
        const closestPoint = heatMapData.reduce((closest, point) => {
            const distance = Math.sqrt((x - point.x) ** 2 + (y - point.y) ** 2)
            const closestDistance = Math.sqrt((x - closest.x) ** 2 + (y - closest.y) ** 2)
            return distance < closestDistance ? point : closest
        }, heatMapData[0])

        if (closestPoint) {
            setHoveredValue(closestPoint.value)
        }
    }

    const handleCanvasClick = (e: React.MouseEvent) => {
        const canvas = canvasRef.current
        if (!canvas) return

        const rect = canvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        // 檢查是否點擊了衛星
        satellites.forEach(satellite => {
            const distance = Math.sqrt((x - satellite.x) ** 2 + (y - satellite.y) ** 2)
            if (distance < 15) {
                onSatelliteSelect?.(satellite.id)
            }
        })
    }

    // 動畫循環
    useEffect(() => {
        const animate = () => {
            renderHeatMap()
            animationRef.current = requestAnimationFrame(animate)
        }

        animationRef.current = requestAnimationFrame(animate)
        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current)
            }
        }
    }, [heatMapData, satellites, signalType, showContours, showSatellites, intensity, radius, selectedSatellite])

    // 當信號類型改變時重新獲取數據
    useEffect(() => {
        fetchSignalData()
    }, [signalType])

    // 定期更新數據
    useEffect(() => {
        const interval = setInterval(fetchSignalData, 5000)
        return () => clearInterval(interval)
    }, [signalType])

    if (isLoading) {
        return (
            <div className="signal-heatmap-loading">
                <div className="loading-spinner">🔥</div>
                <div>正在生成信號熱力圖...</div>
            </div>
        )
    }

    return (
        <div className="signal-heatmap">
            <div className="heatmap-controls">
                <div className="signal-type-selector">
                    <label>信號類型:</label>
                    <select 
                        value={signalType} 
                        onChange={(e) => setSignalType(e.target.value as 'rsrp' | 'rsrq' | 'sinr')}
                    >
                        <option value="rsrp">RSRP (參考信號接收功率)</option>
                        <option value="rsrq">RSRQ (參考信號接收品質)</option>
                        <option value="sinr">SINR (信號干擾噪聲比)</option>
                    </select>
                </div>
                
                <div className="display-options">
                    <label>
                        <input
                            type="checkbox"
                            checked={showContours}
                            onChange={(e) => setShowContours(e.target.checked)}
                        />
                        顯示等值線
                    </label>
                    <label>
                        <input
                            type="checkbox"
                            checked={showSatellites}
                            onChange={(e) => setShowSatellites(e.target.checked)}
                        />
                        顯示衛星
                    </label>
                </div>
                
                <div className="intensity-control">
                    <label>強度:</label>
                    <input
                        type="range"
                        min="0.1"
                        max="1"
                        step="0.1"
                        value={intensity}
                        onChange={(e) => setIntensity(parseFloat(e.target.value))}
                    />
                    <span>{(intensity * 100).toFixed(0)}%</span>
                </div>
                
                <div className="radius-control">
                    <label>半徑:</label>
                    <input
                        type="range"
                        min="20"
                        max="100"
                        step="10"
                        value={radius}
                        onChange={(e) => setRadius(parseInt(e.target.value))}
                    />
                    <span>{radius}px</span>
                </div>
            </div>
            
            <div className="heatmap-container">
                <canvas
                    ref={canvasRef}
                    className="heatmap-canvas"
                    onMouseMove={handleMouseMove}
                    onClick={handleCanvasClick}
                />
                
                {hoveredValue !== null && (
                    <div 
                        className="heatmap-tooltip"
                        style={{
                            left: mousePos.x + 10,
                            top: mousePos.y - 30
                        }}
                    >
                        {signalType.toUpperCase()}: {hoveredValue.toFixed(1)}
                    </div>
                )}
            </div>
            
            <div className="heatmap-info">
                <div className="satellite-stats">
                    <h4>衛星統計</h4>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <span>總衛星數:</span>
                            <span>{satellites.length}</span>
                        </div>
                        <div className="stat-item">
                            <span>覆蓋率:</span>
                            <span>{((heatMapData.length / (800 * 600 / 400)) * 100).toFixed(1)}%</span>
                        </div>
                        <div className="stat-item">
                            <span>平均信號:</span>
                            <span>
                                {heatMapData.length > 0 
                                    ? (heatMapData.reduce((sum, point) => sum + point.value, 0) / heatMapData.length).toFixed(1)
                                    : '0'
                                }
                            </span>
                        </div>
                    </div>
                </div>
                
                <div className="constellation-info">
                    <h4>星座分布</h4>
                    <div className="constellation-list">
                        {Object.entries(
                            satellites.reduce((acc, sat) => {
                                acc[sat.constellation] = (acc[sat.constellation] || 0) + 1
                                return acc
                            }, {} as Record<string, number>)
                        ).map(([constellation, count]) => (
                            <div key={constellation} className="constellation-item">
                                <span className="constellation-name">{constellation}</span>
                                <span className="constellation-count">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default SignalHeatMap