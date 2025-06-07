import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { ViewerProps } from '../../types/viewer'
import { ApiRoutes } from '../../config/apiRoutes'
import { useWebSocket } from '../../hooks/useWebSocket'
import { WebSocketEvent } from '../../types/charts'

// SINR Map 顯示組件 - 增強版實時更新
const SINRViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
    currentScene,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [sinrVmin, setSinrVmin] = useState<number>(-40)
    const [sinrVmax, setSinrVmax] = useState<number>(0)
    const [cellSize, setCellSize] = useState<number>(1.0)
    const [samplesPerTx, setSamplesPerTx] = useState<number>(10 ** 7)
    const [retryCount, setRetryCount] = useState(0)
    const maxRetries = 3
    
    // 實時更新相關狀態
    const [realTimeEnabled, setRealTimeEnabled] = useState(false)
    const [updateInterval, setUpdateInterval] = useState<number>(5000) // 5秒
    const [lastSionnaUpdate, setLastSionnaUpdate] = useState<string | null>(null)
    const [channelMetrics, setChannelMetrics] = useState<any>(null)
    const [interferenceData, setInterferenceData] = useState<any>(null)
    const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false)
    
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
    const API_PATH = ApiRoutes.simulations.getSINRMap
    const METRICS_API_PATH = '/api/v1/wireless/sionna-real-time-metrics'
    const INTERFERENCE_API_PATH = '/api/v1/interference/current-status'

    // WebSocket 連接處理 Sionna 和干擾控制實時數據
    const { isConnected, connectionStatus, sendMessage } = useWebSocket({
        url: 'ws://localhost:8080/ws/sionna-metrics',
        enableReconnect: realTimeEnabled,
        onMessage: handleWebSocketMessage,
        onConnect: () => {
            console.log('SINR Viewer WebSocket 已連接')
            if (realTimeEnabled) {
                // 訂閱 Sionna 通道指標
                sendMessage({
                    type: 'subscribe',
                    topics: ['sionna_channel_metrics', 'interference_updates', 'ai_ran_decisions']
                })
            }
        },
        onError: (error) => {
            console.error('SINR Viewer WebSocket 錯誤:', error)
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
        if (avgTime < 1000) setConnectionQuality('excellent')
        else if (avgTime < 2000) setConnectionQuality('good')
        else if (avgTime < 5000) setConnectionQuality('fair')
        else setConnectionQuality('poor')
    }, [onReportLastUpdateToNavbar])

    // 處理 WebSocket 消息
    function handleWebSocketMessage(event: WebSocketEvent) {
        try {
            switch (event.type) {
                case 'sionna_channel_metrics':
                    setChannelMetrics(event.data)
                    setLastSionnaUpdate(event.timestamp)
                    if (realTimeEnabled && autoRefreshEnabled) {
                        loadSINRMapImage()
                    }
                    break
                    
                case 'interference_updates':
                    setInterferenceData(event.data)
                    if (event.data.interference_detected && realTimeEnabled) {
                        // 干擾檢測到時立即更新
                        loadSINRMapImage()
                    }
                    break
                    
                case 'ai_ran_decisions':
                    console.log('收到 AI-RAN 決策更新:', event.data)
                    // AI 決策後更新 SINR 圖
                    if (event.data.strategy === 'frequency_hopping' && realTimeEnabled) {
                        setTimeout(() => loadSINRMapImage(), 1000) // 等待頻率切換完成
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

    const loadSINRMapImage = useCallback(async () => {
        performanceRef.current.startTime = Date.now()
        setIsLoading(true)
        setError(null)

        try {
            // 並行獲取 SINR 圖像和實時指標
            const timestamp = new Date().getTime()
            const apiUrl = `${API_PATH}?scene=${currentScene}&sinr_vmin=${sinrVmin}&sinr_vmax=${sinrVmax}&cell_size=${cellSize}&samples_per_tx=${samplesPerTx}&t=${timestamp}&enable_interference_overlay=${interferenceData?.interference_detected || false}`
            
            const [imageResponse, metricsResponse] = await Promise.allSettled([
                fetch(apiUrl),
                realTimeEnabled ? fetch(`${METRICS_API_PATH}?scene=${currentScene}&t=${timestamp}`) : Promise.resolve(null)
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
                if (realTimeEnabled && metricsResponse.status === 'fulfilled' && metricsResponse.value) {
                    try {
                        const metricsData = await metricsResponse.value.json()
                        setChannelMetrics(metricsData)
                    } catch (metricsError) {
                        console.warn('無法獲取實時指標:', metricsError)
                    }
                }
                
                setIsLoading(false)
                updateTimestamp()
            } else {
                throw new Error(`API 請求失敗: ${imageResponse.status === 'fulfilled' ? imageResponse.value.status : '網路錯誤'}`)
            }
        } catch (err: any) {
            console.error('載入 SINR Map 失敗:', err)
            handleLoadError(err)
        }
    }, [
        currentScene,
        sinrVmin,
        sinrVmax,
        cellSize,
        samplesPerTx,
        updateTimestamp,
        retryCount,
        realTimeEnabled,
        interferenceData
    ])

    // 錯誤處理函數
    const handleLoadError = useCallback((err: any) => {
        if (err.message && err.message.includes('404')) {
            setError('圖像文件未找到: 後端可能正在生成圖像，請稍後重試')
        } else {
            setError('無法載入 SINR Map: ' + err.message)
        }

        setIsLoading(false)

        const newRetryCount = retryCount + 1
        setRetryCount(newRetryCount)

        if (newRetryCount < maxRetries) {
            setTimeout(() => {
                loadSINRMapImage()
            }, realTimeEnabled ? 1000 : 2000)
        }
    }, [retryCount, maxRetries, loadSINRMapImage, realTimeEnabled])

    // 舊的 loadSINRMapImage 函數體移到上面的新函數中
    const legacyLoadSINRMapImage = useCallback(() => {
        setIsLoading(true)
        setError(null)

        const apiUrl = `${API_PATH}?scene=${currentScene}&sinr_vmin=${sinrVmin}&sinr_vmax=${sinrVmax}&cell_size=${cellSize}&samples_per_tx=${samplesPerTx}&t=${new Date().getTime()}`

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
    }, [
        currentScene,
        sinrVmin,
        sinrVmax,
        cellSize,
        samplesPerTx,
        updateTimestamp,
        retryCount,
        handleLoadError,
    ])

    // 自動刷新機制
    const startAutoRefresh = useCallback(() => {
        if (updateTimeoutRef.current) {
            clearTimeout(updateTimeoutRef.current)
        }
        
        if (autoRefreshEnabled && realTimeEnabled) {
            updateTimeoutRef.current = window.setTimeout(() => {
                loadSINRMapImage()
                startAutoRefresh() // 遞迴調用
            }, updateInterval)
        }
    }, [autoRefreshEnabled, realTimeEnabled, updateInterval, loadSINRMapImage])

    const stopAutoRefresh = useCallback(() => {
        if (updateTimeoutRef.current) {
            clearTimeout(updateTimeoutRef.current)
            updateTimeoutRef.current = null
        }
    }, [])

    // 智能更新間隔調整
    const adjustUpdateInterval = useCallback(() => {
        if (avgUpdateTime > 3000 && updateInterval < 10000) {
            setUpdateInterval(prev => Math.min(prev + 1000, 10000))
        } else if (avgUpdateTime < 1000 && updateInterval > 2000) {
            setUpdateInterval(prev => Math.max(prev - 500, 2000))
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
        reportRefreshHandlerToNavbar(loadSINRMapImage)
    }, [loadSINRMapImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadSINRMapImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadSINRMapImage])

    const handleSinrVminChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSinrVmin(Number(e.target.value))
    }
    const handleSinrVmaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSinrVmax(Number(e.target.value))
    }
    const handleCellSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setCellSize(Number(e.target.value))
    }
    const handleSamplesChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSamplesPerTx(Number(e.target.value))
    }

    const handleRetryClick = () => {
        setRetryCount(0)
        loadSINRMapImage()
    }

    const handleRealTimeToggle = () => {
        setRealTimeEnabled(prev => {
            const newValue = !prev
            if (newValue) {
                // 啟用實時模式時重新載入
                loadSINRMapImage()
            } else {
                // 停用實時模式時停止自動刷新
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

    return (
        <div className="image-viewer sinr-image-container">
            {/* 實時控制面板 */}
            <div className="sinr-controls-panel" style={{
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
                            <option value={2000}>2秒</option>
                            <option value={5000}>5秒</option>
                            <option value={10000}>10秒</option>
                            <option value={30000}>30秒</option>
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
                
                {/* 參數控制 */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', marginTop: '10px', alignItems: 'center' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        SINR 最小值 (dB):
                        <input
                            type="number"
                            value={sinrVmin}
                            onChange={handleSinrVminChange}
                            style={{ width: '60px', padding: '2px' }}
                            step="5"
                        />
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        SINR 最大值 (dB):
                        <input
                            type="number"
                            value={sinrVmax}
                            onChange={handleSinrVmaxChange}
                            style={{ width: '60px', padding: '2px' }}
                            step="5"
                        />
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        格點大小:
                        <input
                            type="number"
                            value={cellSize}
                            onChange={handleCellSizeChange}
                            style={{ width: '60px', padding: '2px' }}
                            step="0.1"
                            min="0.1"
                        />
                    </label>
                    
                    <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        採樣數:
                        <select
                            value={samplesPerTx}
                            onChange={handleSamplesChange}
                            style={{ padding: '2px' }}
                        >
                            <option value={10**6}>1M</option>
                            <option value={10**7}>10M</option>
                            <option value={10**8}>100M</option>
                        </select>
                    </label>
                </div>
            </div>
            
            {/* 實時指標顯示 */}
            {realTimeEnabled && channelMetrics && (
                <div className="real-time-metrics" style={{
                    background: '#e8f4fd',
                    padding: '8px',
                    marginBottom: '10px',
                    borderRadius: '4px',
                    fontSize: '12px'
                }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px' }}>
                        <div>平均 SINR: {channelMetrics.average_sinr_db?.toFixed(1)} dB</div>
                        <div>通道容量: {(channelMetrics.channel_capacity_bps / 1e6)?.toFixed(1)} Mbps</div>
                        <div>路徑損耗: {channelMetrics.path_loss_db?.toFixed(1)} dB</div>
                        <div>多普勒頻移: {channelMetrics.doppler_shift_hz?.toFixed(0)} Hz</div>
                        {interferenceData?.interference_detected && (
                            <div style={{ color: '#d32f2f' }}>
                                ⚠️ 干擾檢測: {interferenceData.interference_level_db?.toFixed(1)} dB
                            </div>
                        )}
                    </div>
                    {lastSionnaUpdate && (
                        <div style={{ marginTop: '5px', color: '#666' }}>
                            最後更新: {new Date(lastSionnaUpdate).toLocaleTimeString()}
                        </div>
                    )}
                </div>
            )}
            
            {/* 載入和錯誤狀態 */}
            {isLoading && (
                <div className="loading">
                    {realTimeEnabled ? '正在即時更新 SINR Map...' : '正在即時運算並生成 SINR Map...'}
                    {realTimeEnabled && autoRefreshEnabled && (
                        <div style={{ fontSize: '12px', marginTop: '5px', color: '#666' }}>
                            下次更新: {updateInterval / 1000}秒後
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
            
            {/* SINR 圖像顯示 */}
            {imageUrl && (
                <div className="sinr-image-display" style={{ position: 'relative' }}>
                    <img
                        src={imageUrl}
                        alt="SINR Map"
                        className="view-image sinr-view-image"
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
                    
                    {/* 干擾指示器 */}
                    {interferenceData?.interference_detected && (
                        <div style={{
                            position: 'absolute',
                            top: '10px',
                            left: '10px',
                            background: 'rgba(211, 47, 47, 0.9)',
                            color: 'white',
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            animation: 'pulse 1s infinite'
                        }}>
                            ⚠️ 干擾檢測
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default SINRViewer
