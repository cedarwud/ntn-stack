import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { ViewerProps } from '../../types/viewer'
import { ApiRoutes } from '../../config/apiRoutes'
import { useWebSocket } from '../../hooks/useWebSocket'
import { WebSocketEvent } from '../../types/charts'

// Delay-Doppler 顯示組件 - 增強版實時更新
const DelayDopplerViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    currentScene,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [retryCount, setRetryCount] = useState(0)
    const maxRetries = 3
    
    // 實時更新相關狀態
    const [realTimeEnabled, setRealTimeEnabled] = useState(false)
    const [updateInterval, setUpdateInterval] = useState<number>(5000) // 5秒
    const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false)
    const [dopplerMetrics, setDopplerMetrics] = useState<any>(null)
    const [mobilityData, setMobilityData] = useState<any>(null)
    const [lastChannelUpdate, setLastChannelUpdate] = useState<string | null>(null)
    
    // 高級配置選項
    const [maxDelayNs, setMaxDelayNs] = useState<number>(500)
    const [maxDopplerHz, setMaxDopplerHz] = useState<number>(1000)
    const [resolutionLevel, setResolutionLevel] = useState<'low' | 'medium' | 'high'>('medium')
    const [enablePhaseInfo, setEnablePhaseInfo] = useState(false)
    
    // 性能監控
    const [updateCount, setUpdateCount] = useState(0)
    const [avgUpdateTime, setAvgUpdateTime] = useState(0)
    const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'fair' | 'poor'>('good')

    const imageUrlRef = useRef<string | null>(null)
    const updateTimeoutRef = useRef<number | null>(null)
    const performanceRef = useRef<{ startTime: number; updateTimes: number[] }>({
        startTime: 0,
        updateTimes: []
    })
    // 使用ApiRoutes中定義的路徑
    const API_PATH = ApiRoutes.simulations.getDopplerMap
    const DOPPLER_METRICS_API = '/api/v1/wireless/doppler-analysis-metrics'
    const MOBILITY_API = '/api/v1/device/mobility-status'

    // WebSocket 連接處理 Doppler 分析和移動性數據
    const { isConnected, connectionStatus, sendMessage } = useWebSocket({
        url: 'ws://localhost:8080/ws/doppler-metrics',
        enableReconnect: realTimeEnabled,
        onMessage: handleWebSocketMessage,
        onConnect: () => {
            console.log('Delay-Doppler Viewer WebSocket 已連接')
            if (realTimeEnabled) {
                // 訂閱 Doppler 相關指標
                sendMessage({
                    type: 'subscribe',
                    topics: ['doppler_analysis', 'mobility_updates', 'channel_state_information']
                })
            }
        },
        onError: (error) => {
            console.error('Delay-Doppler Viewer WebSocket 錯誤:', error)
            setConnectionQuality('poor')
        }
    })

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
        
        // 更新性能統計
        const updateTime = Date.now() - performanceRef.current.startTime
        performanceRef.current.updateTimes.push(updateTime)
        if (performanceRef.current.updateTimes.length > 10) {
            performanceRef.current.updateTimes.shift()
        }
        const avgTime = performanceRef.current.updateTimes.reduce((a, b) => a + b, 0) / performanceRef.current.updateTimes.length
        setAvgUpdateTime(avgTime)
        setUpdateCount(prev => prev + 1)
        
        // 根據更新時間調整連接品質
        if (avgTime < 1500) setConnectionQuality('excellent')
        else if (avgTime < 3000) setConnectionQuality('good')
        else if (avgTime < 6000) setConnectionQuality('fair')
        else setConnectionQuality('poor')
    }, [onReportLastUpdateToNavbar])

    // 處理 WebSocket 消息
    function handleWebSocketMessage(event: WebSocketEvent) {
        try {
            switch (event.type) {
                case 'doppler_analysis':
                    setDopplerMetrics(event.data)
                    setLastChannelUpdate(event.timestamp)
                    if (realTimeEnabled && autoRefreshEnabled) {
                        loadDopplerImage()
                    }
                    break
                    
                case 'mobility_updates':
                    setMobilityData(event.data)
                    // 移動性變化時立即更新 Doppler 圖
                    if (event.data.velocity_change_significant && realTimeEnabled) {
                        loadDopplerImage()
                    }
                    break
                    
                case 'channel_state_information':
                    // 通道狀態信息變化時更新
                    if (event.data.doppler_spread_changed && realTimeEnabled) {
                        setTimeout(() => loadDopplerImage(), 500)
                    }
                    break
            }
        } catch (error) {
            console.error('處理 WebSocket 消息失敗:', error)
        }
    }

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadDopplerImage = useCallback(async () => {
        performanceRef.current.startTime = Date.now()
        setIsLoading(true)
        setError(null)

        try {
            // 構建增強的 API 請求參數
            const timestamp = new Date().getTime()
            const resolutionMap = { low: 64, medium: 128, high: 256 }
            const apiUrl = `${API_PATH}?scene=${currentScene}&max_delay_ns=${maxDelayNs}&max_doppler_hz=${maxDopplerHz}&resolution=${resolutionMap[resolutionLevel]}&enable_phase=${enablePhaseInfo}&t=${timestamp}`
            
            // 並行獲取 Doppler 圖像和實時指標
            const [imageResponse, metricsResponse, mobilityResponse] = await Promise.allSettled([
                fetch(apiUrl),
                realTimeEnabled ? fetch(`${DOPPLER_METRICS_API}?scene=${currentScene}&t=${timestamp}`) : Promise.resolve(null),
                realTimeEnabled ? fetch(`${MOBILITY_API}?scene=${currentScene}&t=${timestamp}`) : Promise.resolve(null)
            ])

            // 處理圖像響應
            if (imageResponse.status === 'fulfilled' && imageResponse.value.ok) {
                const blob = await imageResponse.value.blob()
                if (blob.size === 0) {
                    throw new Error('接收到空的圖像數據')
                }

                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setRetryCount(0)
                
                // 處理實時指標響應
                if (realTimeEnabled) {
                    if (metricsResponse.status === 'fulfilled' && metricsResponse.value) {
                        try {
                            const metricsData = await metricsResponse.value.json()
                            setDopplerMetrics(metricsData)
                        } catch (error) {
                            console.warn('無法獲取 Doppler 指標:', error)
                        }
                    }
                    
                    if (mobilityResponse.status === 'fulfilled' && mobilityResponse.value) {
                        try {
                            const mobilityResponseData = await mobilityResponse.value.json()
                            setMobilityData(mobilityResponseData)
                        } catch (error) {
                            console.warn('無法獲取移動性數據:', error)
                        }
                    }
                }
                
                setIsLoading(false)
                updateTimestamp()
            } else {
                throw new Error(`API 請求失敗: ${imageResponse.status === 'fulfilled' ? imageResponse.value.status : '網路錯誤'}`)
            }
        } catch (err: any) {
            console.error('載入延遲多普勒圖失敗:', err)
            handleLoadError(err)
        }
    }, [
        currentScene,
        updateTimestamp,
        retryCount,
        maxDelayNs,
        maxDopplerHz,
        resolutionLevel,
        enablePhaseInfo,
        realTimeEnabled
    ])

    // 錯誤處理函數
    const handleLoadError = useCallback((err: any) => {
        if (err.message && err.message.includes('404')) {
            setError('圖像文件未找到: 後端可能正在生成圖像，請稍後重試')
        } else {
            setError('無法載入延遲多普勒圖: ' + err.message)
        }

        setIsLoading(false)

        const newRetryCount = retryCount + 1
        setRetryCount(newRetryCount)

        if (newRetryCount < maxRetries) {
            setTimeout(() => {
                loadDopplerImage()
            }, realTimeEnabled ? 1000 : 2000)
        }
    }, [retryCount, maxRetries, loadDopplerImage, realTimeEnabled])

    // 舊的載入函數（向後兼容）
    const legacyLoadDopplerImage = useCallback(() => {
        setIsLoading(true)
        setError(null)

        const apiUrl = `${API_PATH}?scene=${currentScene}&t=${new Date().getTime()}`

        fetch(apiUrl)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                if (blob.size === 0) {
                    throw new Error('接收到空的圖像數據')
                }

                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                setRetryCount(0)
                updateTimestamp()
            })
            .catch(handleLoadError)
    }, [updateTimestamp, retryCount, currentScene, handleLoadError])

    // 自動刷新機制
    const startAutoRefresh = useCallback(() => {
        if (updateTimeoutRef.current) {
            clearTimeout(updateTimeoutRef.current)
        }
        
        if (autoRefreshEnabled && realTimeEnabled) {
            updateTimeoutRef.current = window.setTimeout(() => {
                loadDopplerImage()
                startAutoRefresh() // 遞迴調用
            }, updateInterval)
        }
    }, [autoRefreshEnabled, realTimeEnabled, updateInterval, loadDopplerImage])

    const stopAutoRefresh = useCallback(() => {
        if (updateTimeoutRef.current) {
            clearTimeout(updateTimeoutRef.current)
            updateTimeoutRef.current = null
        }
    }, [])

    // 智能更新間隔調整
    const adjustUpdateInterval = useCallback(() => {
        if (avgUpdateTime > 4000 && updateInterval < 15000) {
            setUpdateInterval(prev => Math.min(prev + 1000, 15000))
        } else if (avgUpdateTime < 1500 && updateInterval > 3000) {
            setUpdateInterval(prev => Math.max(prev - 500, 3000))
        }
    }, [avgUpdateTime, updateInterval])

    // 連接狀態變化處理
    useEffect(() => {
        if (isConnected && realTimeEnabled) {
            startAutoRefresh()
        } else {
            stopAutoRefresh()
        }
        
        return () => stopAutoRefresh()
    }, [isConnected, realTimeEnabled, startAutoRefresh, stopAutoRefresh])

    // 調整更新間隔
    useEffect(() => {
        if (realTimeEnabled && updateCount > 5) {
            adjustUpdateInterval()
        }
    }, [updateCount, adjustUpdateInterval, realTimeEnabled])

    // 記憶化的連接狀態文字
    const connectionStatusText = useMemo(() => {
        if (!realTimeEnabled) return '離線模式'
        
        const statusMap = {
            connecting: '連接中...',
            connected: '已連接',
            disconnected: '已斷線',
            failed: '連接失敗'
        }
        
        const qualityMap = {
            excellent: '🟢',
            good: '🟡',
            fair: '🟠',
            poor: '🔴'
        }
        
        return `${statusMap[connectionStatus]} ${qualityMap[connectionQuality]}`
    }, [realTimeEnabled, connectionStatus, connectionQuality])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadDopplerImage)
    }, [loadDopplerImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadDopplerImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadDopplerImage])

    const handleRetryClick = () => {
        setRetryCount(0)
        loadDopplerImage()
    }

    const handleRealTimeToggle = () => {
        setRealTimeEnabled(prev => {
            const newValue = !prev
            if (newValue) {
                loadDopplerImage()
            } else {
                setAutoRefreshEnabled(false)
                stopAutoRefresh()
            }
            return newValue
        })
    }

    const handleAutoRefreshToggle = () => {
        setAutoRefreshEnabled(prev => {
            const newValue = !prev
            if (newValue && realTimeEnabled) {
                startAutoRefresh()
            } else {
                stopAutoRefresh()
            }
            return newValue
        })
    }

    const handleUpdateIntervalChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const newInterval = Number(e.target.value)
        setUpdateInterval(newInterval)
        if (autoRefreshEnabled && realTimeEnabled) {
            stopAutoRefresh()
            setTimeout(startAutoRefresh, 100)
        }
    }

    const handleMaxDelayChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setMaxDelayNs(Number(e.target.value))
    }

    const handleMaxDopplerChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setMaxDopplerHz(Number(e.target.value))
    }

    const handleResolutionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setResolutionLevel(e.target.value as 'low' | 'medium' | 'high')
    }

    const handlePhaseToggle = () => {
        setEnablePhaseInfo(prev => !prev)
    }

    return (
        <div className="image-viewer delay-doppler-container">
            {/* 實時控制面板 */}
            <div className="doppler-controls-panel" style={{
                background: '#f5f5f5',
                padding: '10px',
                marginBottom: '10px',
                borderRadius: '4px',
                border: '1px solid #ddd'
            }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'center' }}>
                    {/* 實時模式開關 */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <input
                            type="checkbox"
                            checked={realTimeEnabled}
                            onChange={handleRealTimeToggle}
                        />
                        實時模式
                    </label>
                    
                    {/* 自動刷新開關 */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <input
                            type="checkbox"
                            checked={autoRefreshEnabled}
                            onChange={handleAutoRefreshToggle}
                            disabled={!realTimeEnabled}
                        />
                        自動刷新
                    </label>
                    
                    {/* 更新間隔選擇 */}
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        更新間隔:
                        <select
                            value={updateInterval}
                            onChange={handleUpdateIntervalChange}
                            disabled={!realTimeEnabled}
                            style={{ padding: '2px' }}
                        >
                            <option value={3000}>3秒</option>
                            <option value={5000}>5秒</option>
                            <option value={10000}>10秒</option>
                            <option value={15000}>15秒</option>
                        </select>
                    </label>
                    
                    {/* 連接狀態 */}
                    <div style={{ fontSize: '12px', color: '#666' }}>
                        狀態: {connectionStatusText}
                    </div>
                    
                    {/* 性能指標 */}
                    {realTimeEnabled && (
                        <div style={{ fontSize: '12px', color: '#666' }}>
                            更新: {updateCount} | 平均: {avgUpdateTime.toFixed(0)}ms
                        </div>
                    )}
                </div>
                
                {/* 高級參數控制 */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginTop: '10px', alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        最大延遲 (ns):
                        <input
                            type="number"
                            value={maxDelayNs}
                            onChange={handleMaxDelayChange}
                            style={{ width: '70px', padding: '2px' }}
                            step="50"
                            min="100"
                            max="2000"
                        />
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        最大多普勒 (Hz):
                        <input
                            type="number"
                            value={maxDopplerHz}
                            onChange={handleMaxDopplerChange}
                            style={{ width: '70px', padding: '2px' }}
                            step="100"
                            min="200"
                            max="5000"
                        />
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        解析度:
                        <select
                            value={resolutionLevel}
                            onChange={handleResolutionChange}
                            style={{ padding: '2px' }}
                        >
                            <option value="low">低 (64x64)</option>
                            <option value="medium">中 (128x128)</option>
                            <option value="high">高 (256x256)</option>
                        </select>
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <input
                            type="checkbox"
                            checked={enablePhaseInfo}
                            onChange={handlePhaseToggle}
                        />
                        相位資訊
                    </label>
                </div>
            </div>
            
            {/* 實時指標顯示 */}
            {realTimeEnabled && (dopplerMetrics || mobilityData) && (
                <div className="real-time-doppler-metrics" style={{
                    background: '#e8f4fd',
                    padding: '8px',
                    marginBottom: '10px',
                    borderRadius: '4px',
                    fontSize: '12px'
                }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                        {dopplerMetrics && (
                            <>
                                <div>多普勒擴散: {dopplerMetrics.doppler_spread_hz?.toFixed(1)} Hz</div>
                                <div>延遲擴散: {dopplerMetrics.delay_spread_ns?.toFixed(1)} ns</div>
                                <div>相干帶寬: {(dopplerMetrics.coherence_bandwidth_hz / 1000)?.toFixed(1)} kHz</div>
                                <div>相干時間: {dopplerMetrics.coherence_time_ms?.toFixed(1)} ms</div>
                            </>
                        )}
                        {mobilityData && (
                            <>
                                <div>移動速度: {mobilityData.velocity_ms?.toFixed(1)} m/s</div>
                                <div>移動方向: {mobilityData.heading_deg?.toFixed(0)}°</div>
                                {mobilityData.acceleration_ms2 && (
                                    <div>加速度: {mobilityData.acceleration_ms2?.toFixed(2)} m/s²</div>
                                )}
                            </>
                        )}
                    </div>
                    {lastChannelUpdate && (
                        <div style={{ marginTop: '5px', color: '#666' }}>
                            最後更新: {new Date(lastChannelUpdate).toLocaleTimeString()}
                        </div>
                    )}
                </div>
            )}
            
            {/* 載入和錯誤狀態 */}
            {isLoading && (
                <div className="loading">
                    {realTimeEnabled ? '正在即時更新 Delay-Doppler...' : '正在即時運算並生成 Delay-Doppler...'}
                    {realTimeEnabled && autoRefreshEnabled && (
                        <div style={{ fontSize: '12px', marginTop: '5px', color: '#666' }}>
                            下次更新: {updateInterval / 1000}秒後 | 解析度: {resolutionLevel}
                        </div>
                    )}
                </div>
            )}
            
            {error && (
                <div className="error">
                    {error}
                    <button
                        onClick={handleRetryClick}
                        style={{
                            marginLeft: '10px',
                            padding: '5px 10px',
                            background: '#4285f4',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                        }}
                    >
                        重試
                    </button>
                    {realTimeEnabled && (
                        <button
                            onClick={() => {
                                setRealTimeEnabled(false)
                                setAutoRefreshEnabled(false)
                                handleRetryClick()
                            }}
                            style={{
                                marginLeft: '5px',
                                padding: '5px 10px',
                                background: '#ff9800',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                            }}
                        >
                            降級到離線模式
                        </button>
                    )}
                </div>
            )}
            
            {/* Delay-Doppler 圖像顯示 */}
            <div className="delay-doppler-image-container">
                {imageUrl && (
                    <div className="image-item doppler-image-v2" style={{ position: 'relative' }}>
                        <img
                            src={imageUrl}
                            alt="Delay-Doppler Plot"
                            className="view-image doppler-image-v2"
                            style={{
                                maxWidth: '100%',
                                height: 'auto',
                                border: realTimeEnabled ? '2px solid #4285f4' : '1px solid #ddd'
                            }}
                        />
                        
                        {/* 實時模式指示器 */}
                        {realTimeEnabled && (
                            <div style={{
                                position: 'absolute',
                                top: '10px',
                                right: '10px',
                                background: 'rgba(66, 133, 244, 0.9)',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '5px'
                            }}>
                                <div style={{
                                    width: '8px',
                                    height: '8px',
                                    borderRadius: '50%',
                                    background: isConnected ? '#4caf50' : '#f44336',
                                    animation: isConnected ? 'pulse 1.5s infinite' : 'none'
                                }} />
                                實時模式
                            </div>
                        )}
                        
                        {/* 高移動性指示器 */}
                        {mobilityData?.velocity_ms > 30 && (
                            <div style={{
                                position: 'absolute',
                                top: '10px',
                                left: '10px',
                                background: 'rgba(255, 152, 0, 0.9)',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px'
                            }}>
                                🚄 高速移動 ({mobilityData.velocity_ms.toFixed(0)} m/s)
                            </div>
                        )}
                        
                        {/* 解析度指示器 */}
                        <div style={{
                            position: 'absolute',
                            bottom: '10px',
                            right: '10px',
                            background: 'rgba(0, 0, 0, 0.7)',
                            color: 'white',
                            padding: '2px 6px',
                            borderRadius: '2px',
                            fontSize: '10px'
                        }}>
                            {resolutionLevel.toUpperCase()} | {enablePhaseInfo ? 'PHASE' : 'MAG'}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default DelayDopplerViewer
