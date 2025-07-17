import React, { useEffect, useRef, useState } from 'react'
import { simworldFetch } from '../../../config/api-config'
import './Satellite3DVisualization.scss'

interface Satellite3DVisualizationProps {
    onSatelliteSelect?: (satellite: SatelliteData) => void
    selectedSatellite?: string
}

interface SatelliteData {
    id: string
    name: string
    position: {
        x: number
        y: number
        z: number
        latitude: number
        longitude: number
        altitude: number
        elevation: number
        azimuth: number
    }
    signal_quality: {
        rsrp: number
        rsrq: number
        sinr: number
        signal_strength: number
    }
    load_factor: number
    data_quality: 'real' | 'historical' | 'simulated'
    constellation: string
    status: 'active' | 'inactive' | 'maintenance'
}

const Satellite3DVisualization: React.FC<Satellite3DVisualizationProps> = ({
    onSatelliteSelect,
    selectedSatellite
}) => {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [satellites, setSatellites] = useState<SatelliteData[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [viewMode, setViewMode] = useState<'orbit' | 'earth' | 'signal'>('orbit')
    const [rotationSpeed, setRotationSpeed] = useState(1)
    const [showOrbits, setShowOrbits] = useState(true)
    const [showSignals, setShowSignals] = useState(false)
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
    const [isDragging, setIsDragging] = useState(false)
    const [rotation, setRotation] = useState({ x: 0, y: 0 })
    const [zoom, setZoom] = useState(1)
    const animationRef = useRef<number>()

    // 獲取衛星數據
    const fetchSatellites = async () => {
        try {
            const response = await simworldFetch('/v1/satellites/constellation?global_view=true')
            if (response.ok) {
                const data = await response.json()
                const satelliteData = data.satellites?.map((sat: Record<string, unknown>) => ({
                    id: (sat.id as string) || 'unknown',
                    name: (sat.name as string) || 'Unknown',
                    position: {
                        x: ((sat.position as Record<string, unknown>)?.x as number) || 0,
                        y: ((sat.position as Record<string, unknown>)?.y as number) || 0,
                        z: ((sat.position as Record<string, unknown>)?.z as number) || 0,
                        latitude: ((sat.position as Record<string, unknown>)?.latitude as number) || 0,
                        longitude: ((sat.position as Record<string, unknown>)?.longitude as number) || 0,
                        altitude: ((sat.position as Record<string, unknown>)?.altitude as number) || 550,
                        elevation: ((sat.position as Record<string, unknown>)?.elevation as number) || 0,
                        azimuth: ((sat.position as Record<string, unknown>)?.azimuth as number) || 0,
                    },
                    signal_quality: {
                        rsrp: ((sat.signal_quality as Record<string, unknown>)?.rsrp as number) || -85,
                        rsrq: ((sat.signal_quality as Record<string, unknown>)?.rsrq as number) || -12,
                        sinr: ((sat.signal_quality as Record<string, unknown>)?.sinr as number) || 15,
                        signal_strength: ((sat.signal_quality as Record<string, unknown>)?.signal_strength as number) || 80,
                    },
                    load_factor: (sat.load_factor as number) || 0.3,
                    data_quality: (sat.data_quality as 'real' | 'historical' | 'simulated') || 'simulated',
                    constellation: (sat.constellation as string) || 'Starlink',
                    status: (sat.status as 'active' | 'inactive' | 'maintenance') || 'active',
                })) || []
                
                setSatellites(satelliteData)
            } else {
                // 使用模擬數據
                generateMockSatellites()
            }
        } catch (error) {
            console.error('獲取衛星數據失敗:', error)
            generateMockSatellites()
        } finally {
            setIsLoading(false)
        }
    }

    // 生成模擬的 LEO 衛星星座數據
    const generateMockSatellites = () => {
        const mockSatellites: SatelliteData[] = []
        const constellations = ['Starlink', 'Kuiper', 'OneWeb']
        const altitudes = [550, 600, 1200] // km
        
        constellations.forEach((constellation, constIndex) => {
            const altitude = altitudes[constIndex]
            const numSatellites = constellation === 'Starlink' ? 40 : 20
            
            for (let i = 0; i < numSatellites; i++) {
                const longitude = (i * 360 / numSatellites) + (constIndex * 30)
                const latitude = (Math.sin(i * 0.5) * 60) + (constIndex * 10)
                
                // 轉換為 3D 笛卡爾坐標
                const earthRadius = 6371 // km
                const radius = earthRadius + altitude
                const latRad = (latitude * Math.PI) / 180
                const lonRad = (longitude * Math.PI) / 180
                
                const x = radius * Math.cos(latRad) * Math.cos(lonRad)
                const y = radius * Math.cos(latRad) * Math.sin(lonRad)
                const z = radius * Math.sin(latRad)
                
                // 計算仰角和方位角（相對於地面站點）
                const elevation = Math.max(0, 90 - Math.abs(latitude))
                const azimuth = longitude
                
                // 基於距離和仰角計算信號質量
                const distance = Math.sqrt(x * x + y * y + z * z)
                const rsrp = -60 - (distance - 6900) / 50
                const rsrq = -8 - (90 - elevation) / 10
                const sinr = 5 + elevation / 6
                
                mockSatellites.push({
                    id: `${constellation.toLowerCase()}-${i + 1}`,
                    name: `${constellation}-${i + 1}`,
                    position: {
                        x: x / 100, // 縮放用於顯示
                        y: y / 100,
                        z: z / 100,
                        latitude,
                        longitude,
                        altitude,
                        elevation,
                        azimuth,
                    },
                    signal_quality: {
                        rsrp,
                        rsrq,
                        sinr,
                        signal_strength: Math.max(0, 100 + rsrp),
                    },
                    load_factor: 0.2 + Math.random() * 0.6,
                    data_quality: 'simulated',
                    constellation,
                    status: Math.random() > 0.05 ? 'active' : 'maintenance',
                })
            }
        })
        
        setSatellites(mockSatellites)
    }

    // 3D 渲染邏輯
    const render3D = () => {
        const canvas = canvasRef.current
        if (!canvas) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        // 清空畫布
        ctx.clearRect(0, 0, canvas.width, canvas.height)
        
        // 設置畫布尺寸
        canvas.width = canvas.offsetWidth
        canvas.height = canvas.offsetHeight
        
        const centerX = canvas.width / 2
        const centerY = canvas.height / 2
        const baseRadius = Math.min(canvas.width, canvas.height) * 0.3 * zoom

        // 繪製地球
        ctx.beginPath()
        ctx.arc(centerX, centerY, baseRadius * 0.8, 0, Math.PI * 2)
        ctx.fillStyle = '#2E7D32'
        ctx.fill()
        ctx.strokeStyle = '#1B5E20'
        ctx.lineWidth = 2
        ctx.stroke()

        // 繪製軌道圈
        if (showOrbits) {
            [0.9, 1.0, 1.8].forEach((orbitRatio, index) => {
                ctx.beginPath()
                ctx.arc(centerX, centerY, baseRadius * orbitRatio, 0, Math.PI * 2)
                ctx.strokeStyle = `rgba(79, 195, 247, ${0.3 - index * 0.1})`
                ctx.lineWidth = 1
                ctx.stroke()
            })
        }

        // 繪製衛星
        satellites.forEach((satellite) => {
            const { x, y, z } = satellite.position
            
            // 應用旋轉和透視投影
            const rotatedX = x * Math.cos(rotation.y) - z * Math.sin(rotation.y)
            const rotatedZ = x * Math.sin(rotation.y) + z * Math.cos(rotation.y)
            const rotatedY = y * Math.cos(rotation.x) - rotatedZ * Math.sin(rotation.x)
            
            // 簡單的透視投影
            const perspective = 1000
            const scale = perspective / (perspective + rotatedZ)
            const screenX = centerX + rotatedX * scale * 5
            const screenY = centerY + rotatedY * scale * 5

            // 跳過不在視野內的衛星
            if (screenX < 0 || screenX > canvas.width || screenY < 0 || screenY > canvas.height) {
                return
            }

            // 根據信號質量選擇顏色
            let color = '#4FC3F7'
            if (viewMode === 'signal') {
                const rsrp = satellite.signal_quality.rsrp
                if (rsrp > -80) color = '#4CAF50'
                else if (rsrp > -90) color = '#FFC107'
                else if (rsrp > -100) color = '#FF9800'
                else color = '#F44336'
            } else if (viewMode === 'orbit') {
                const constellationColors: Record<string, string> = {
                    'Starlink': '#4FC3F7',
                    'Kuiper': '#FF9800',
                    'OneWeb': '#9C27B0'
                }
                color = constellationColors[satellite.constellation] || '#4FC3F7'
            }

            // 數據品質指示
            const qualityColors = {
                'real': '#4CAF50',
                'historical': '#FFC107',
                'simulated': '#F44336'
            }
            const qualityColor = qualityColors[satellite.data_quality]

            // 繪製衛星
            const radius = satellite.id === selectedSatellite ? 6 : 4
            ctx.beginPath()
            ctx.arc(screenX, screenY, radius, 0, Math.PI * 2)
            ctx.fillStyle = color
            ctx.fill()
            
            // 繪製數據品質指示環
            ctx.beginPath()
            ctx.arc(screenX, screenY, radius + 2, 0, Math.PI * 2)
            ctx.strokeStyle = qualityColor
            ctx.lineWidth = 2
            ctx.stroke()

            // 繪製選中指示
            if (satellite.id === selectedSatellite) {
                ctx.beginPath()
                ctx.arc(screenX, screenY, radius + 5, 0, Math.PI * 2)
                ctx.strokeStyle = '#FFFFFF'
                ctx.lineWidth = 2
                ctx.stroke()
            }

            // 繪製信號強度
            if (showSignals && satellite.signal_quality.signal_strength > 50) {
                const signalRadius = (satellite.signal_quality.signal_strength / 100) * 20
                ctx.beginPath()
                ctx.arc(screenX, screenY, signalRadius, 0, Math.PI * 2)
                ctx.strokeStyle = `rgba(79, 195, 247, 0.3)`
                ctx.lineWidth = 1
                ctx.stroke()
            }

            // 繪製衛星名稱（僅對選中的衛星）
            if (satellite.id === selectedSatellite) {
                ctx.fillStyle = '#FFFFFF'
                ctx.font = '12px Arial'
                ctx.fillText(satellite.name, screenX + 10, screenY - 10)
            }
        })

        // 繪製圖例
        drawLegend(ctx, canvas.width, canvas.height)
    }

    // 繪製圖例
    const drawLegend = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
        const legendX = width - 200
        const legendY = 20
        
        // 背景
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
        ctx.fillRect(legendX, legendY, 180, 120)
        
        // 標題
        ctx.fillStyle = '#FFFFFF'
        ctx.font = '14px Arial'
        ctx.fillText('圖例', legendX + 10, legendY + 20)
        
        // 數據品質
        ctx.font = '10px Arial'
        ctx.fillText('數據品質:', legendX + 10, legendY + 40)
        
        const qualityItems = [
            { color: '#4CAF50', label: '真實數據' },
            { color: '#FFC107', label: '歷史數據' },
            { color: '#F44336', label: '模擬數據' }
        ]
        
        qualityItems.forEach((item, index) => {
            const y = legendY + 55 + index * 15
            ctx.beginPath()
            ctx.arc(legendX + 15, y, 4, 0, Math.PI * 2)
            ctx.fillStyle = item.color
            ctx.fill()
            ctx.fillStyle = '#FFFFFF'
            ctx.fillText(item.label, legendX + 25, y + 3)
        })
    }

    // 鼠標事件處理
    const handleMouseDown = (e: React.MouseEvent) => {
        setIsDragging(true)
        setMousePosition({ x: e.clientX, y: e.clientY })
    }

    const handleMouseMove = (e: React.MouseEvent) => {
        if (!isDragging) return
        
        const deltaX = e.clientX - mousePosition.x
        const deltaY = e.clientY - mousePosition.y
        
        setRotation(prev => ({
            x: prev.x + deltaY * 0.01,
            y: prev.y + deltaX * 0.01
        }))
        
        setMousePosition({ x: e.clientX, y: e.clientY })
    }

    const handleMouseUp = () => {
        setIsDragging(false)
    }

    const handleWheel = (e: React.WheelEvent) => {
        e.preventDefault()
        const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
        setZoom(prev => Math.max(0.5, Math.min(3, prev * zoomFactor)))
    }

    const handleCanvasClick = (e: React.MouseEvent) => {
        const canvas = canvasRef.current
        if (!canvas) return

        const rect = canvas.getBoundingClientRect()
        const clickX = e.clientX - rect.left
        const clickY = e.clientY - rect.top

        // 檢查是否點擊了衛星
        const centerX = canvas.width / 2
        const centerY = canvas.height / 2
        
        satellites.forEach((satellite) => {
            const { x, y, z } = satellite.position
            
            // 應用相同的變換
            const rotatedX = x * Math.cos(rotation.y) - z * Math.sin(rotation.y)
            const rotatedZ = x * Math.sin(rotation.y) + z * Math.cos(rotation.y)
            const rotatedY = y * Math.cos(rotation.x) - rotatedZ * Math.sin(rotation.x)
            
            const perspective = 1000
            const scale = perspective / (perspective + rotatedZ)
            const screenX = centerX + rotatedX * scale * 5
            const screenY = centerY + rotatedY * scale * 5

            const distance = Math.sqrt((clickX - screenX) ** 2 + (clickY - screenY) ** 2)
            if (distance < 10) {
                onSatelliteSelect?.(satellite)
            }
        })
    }

    // 動畫循環
    useEffect(() => {
        const animate = () => {
            if (rotationSpeed > 0) {
                setRotation(prev => ({
                    ...prev,
                    y: prev.y + rotationSpeed * 0.01
                }))
            }
            render3D()
            animationRef.current = requestAnimationFrame(animate)
        }

        animationRef.current = requestAnimationFrame(animate)
        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current)
            }
        }
    }, [satellites, rotation, zoom, viewMode, showOrbits, showSignals, selectedSatellite, rotationSpeed])

    // 初始化
    useEffect(() => {
        fetchSatellites()
        const interval = setInterval(fetchSatellites, 5000)
        return () => clearInterval(interval)
    }, [])

    if (isLoading) {
        return (
            <div className="satellite-3d-loading">
                <div className="loading-spinner">🛰️</div>
                <div>正在加載衛星數據...</div>
            </div>
        )
    }

    return (
        <div className="satellite-3d-visualization">
            <div className="controls">
                <div className="view-controls">
                    <button 
                        className={viewMode === 'orbit' ? 'active' : ''}
                        onClick={() => setViewMode('orbit')}
                    >
                        軌道視圖
                    </button>
                    <button 
                        className={viewMode === 'earth' ? 'active' : ''}
                        onClick={() => setViewMode('earth')}
                    >
                        地球視圖
                    </button>
                    <button 
                        className={viewMode === 'signal' ? 'active' : ''}
                        onClick={() => setViewMode('signal')}
                    >
                        信號視圖
                    </button>
                </div>
                
                <div className="display-controls">
                    <label>
                        <input
                            type="checkbox"
                            checked={showOrbits}
                            onChange={(e) => setShowOrbits(e.target.checked)}
                        />
                        顯示軌道
                    </label>
                    <label>
                        <input
                            type="checkbox"
                            checked={showSignals}
                            onChange={(e) => setShowSignals(e.target.checked)}
                        />
                        顯示信號
                    </label>
                </div>
                
                <div className="rotation-control">
                    <label>旋轉速度:</label>
                    <input
                        type="range"
                        min="0"
                        max="5"
                        step="0.1"
                        value={rotationSpeed}
                        onChange={(e) => setRotationSpeed(parseFloat(e.target.value))}
                    />
                </div>
            </div>
            
            <canvas
                ref={canvasRef}
                className="satellite-canvas"
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
                onClick={handleCanvasClick}
            />
            
            <div className="info-panel">
                <div className="satellite-count">
                    可見衛星: {satellites.filter(s => s.status === 'active').length}
                </div>
                <div className="constellation-breakdown">
                    {Object.entries(
                        satellites.reduce((acc, sat) => {
                            acc[sat.constellation] = (acc[sat.constellation] || 0) + 1
                            return acc
                        }, {} as Record<string, number>)
                    ).map(([constellation, count]) => (
                        <div key={constellation} className="constellation-item">
                            {constellation}: {count}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default Satellite3DVisualization