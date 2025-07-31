/**
 * SynchronizedD2Dashboard - D2事件與立體圖同步儀表板
 * 
 * 核心功能：
 * 1. 整合改進版D2圖表與立體圖的時間同步
 * 2. 實現雙向時間控制（圖表點擊 ↔ 立體圖時間軸）
 * 3. 提供換手觸發時機的可視化分析
 * 4. 支援多種數據源和配置選項
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { ImprovedD2Chart, ImprovedD2DataPoint } from './ImprovedD2Chart'
import { 
    improvedD2DataService, 
    createImprovedD2Data,
    DEFAULT_D2_TRIGGER_CONFIG,
    DEFAULT_SMOOTHING_CONFIG,
    RawSatelliteData,
    D2TriggerConfig,
    SmoothingConfig,
    DataQualityMetrics
} from '../../../services/improvedD2DataService'

// 時間同步控制接口
export interface TimeSync {
    currentTime: number // 當前時間（秒）
    isPlaying: boolean // 是否正在播放
    playbackSpeed: number // 播放速度倍數
    totalDuration: number // 總時長（秒）
}

// 立體圖控制接口（與現有立體圖組件整合）
export interface SceneControlInterface {
    setCurrentTime: (time: number) => void
    getCurrentTime: () => number
    play: () => void
    pause: () => void
    setPlaybackSpeed: (speed: number) => void
    onTimeUpdate?: (time: number) => void
}

// 換手事件詳情
export interface HandoverEvent {
    startTime: number
    endTime: number
    triggerStrength: number
    handoverLikelihood: 'high' | 'medium' | 'low'
    sourceSatellite: string
    targetSatellite: string
    triggerReason: string
}

// 儀表板配置
export interface DashboardConfig {
    // 布局選項
    layout: 'horizontal' | 'vertical' | 'overlay'
    chartHeight: number
    showControlPanel: boolean
    showDataQualityPanel: boolean
    
    // 數據處理選項
    triggerConfig: D2TriggerConfig
    smoothingConfig: SmoothingConfig
    
    // 視覺選項
    showRawData: boolean
    highlightTriggerPatterns: boolean
    showHandoverPrediction: boolean
    
    // 同步選項
    enableAutoSync: boolean
    syncTolerance: number // 同步容差（秒）
}

// 組件 Props
export interface SynchronizedD2DashboardProps {
    // 數據源
    rawData?: RawSatelliteData[]
    useTestData?: boolean
    
    // 立體圖控制（可選，用於整合現有立體圖）
    sceneControl?: SceneControlInterface
    
    // 配置
    config?: Partial<DashboardConfig>
    
    // 回調函數
    onHandoverEventDetected?: (event: HandoverEvent) => void
    onTimeSync?: (timeSync: TimeSync) => void
    onDataQualityChange?: (metrics: DataQualityMetrics) => void
    
    // 樣式
    className?: string
    style?: React.CSSProperties
}

// 預設配置
const DEFAULT_DASHBOARD_CONFIG: DashboardConfig = {
    layout: 'horizontal',
    chartHeight: 400,
    showControlPanel: true,
    showDataQualityPanel: true,
    triggerConfig: DEFAULT_D2_TRIGGER_CONFIG,
    smoothingConfig: DEFAULT_SMOOTHING_CONFIG,
    showRawData: false,
    highlightTriggerPatterns: true,
    showHandoverPrediction: true,
    enableAutoSync: true,
    syncTolerance: 1.0,
}

export const SynchronizedD2Dashboard: React.FC<SynchronizedD2DashboardProps> = ({
    rawData,
    useTestData = false,
    sceneControl,
    config: userConfig,
    onHandoverEventDetected,
    onTimeSync,
    onDataQualityChange,
    className = '',
    style,
}) => {
    // 合併配置
    const config = useMemo(() => ({
        ...DEFAULT_DASHBOARD_CONFIG,
        ...userConfig,
    }), [userConfig])

    // 狀態管理
    const [timeSync, setTimeSync] = useState<TimeSync>({
        currentTime: 0,
        isPlaying: false,
        playbackSpeed: 1,
        totalDuration: 300,
    })
    
    const [processedData, setProcessedData] = useState<ImprovedD2DataPoint[]>([])
    const [dataQualityMetrics, setDataQualityMetrics] = useState<DataQualityMetrics | null>(null)
    const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([])
    const [processingTime, setProcessingTime] = useState<number>(0)
    const [isLoading, setIsLoading] = useState<boolean>(true)

    // 數據處理
    useEffect(() => {
        const processData = async () => {
            setIsLoading(true)
            
            try {
                // 獲取原始數據
                let sourceData: RawSatelliteData[]
                if (useTestData || !rawData) {
                    console.log('🧪 使用測試數據生成D2事件模擬數據')
                    sourceData = improvedD2DataService.generateTestData(300, 10)
                } else {
                    sourceData = rawData
                }

                // 處理數據
                const result = createImprovedD2Data(
                    sourceData,
                    config.triggerConfig,
                    config.smoothingConfig
                )

                setProcessedData(result.processedData)
                setDataQualityMetrics(result.qualityMetrics)
                setProcessingTime(result.processingTime)
                
                // 更新總時長
                const totalDuration = result.processedData.length * 10 // 10秒間隔
                setTimeSync(prev => ({ ...prev, totalDuration }))

                // 提取換手事件
                const events = extractHandoverEvents(result.processedData)
                setHandoverEvents(events)

                // 觸發數據品質變化回調
                if (onDataQualityChange) {
                    onDataQualityChange(result.qualityMetrics)
                }

                console.log(`✅ D2數據處理完成: ${result.processedData.length}個數據點, ${events.length}個換手事件, 處理時間: ${result.processingTime.toFixed(2)}ms`)
                
            } catch (error) {
                console.error('❌ D2數據處理失敗:', error)
            } finally {
                setIsLoading(false)
            }
        }

        processData()
    }, [rawData, useTestData, config.triggerConfig, config.smoothingConfig, onDataQualityChange])

    // 提取換手事件
    const extractHandoverEvents = useCallback((data: ImprovedD2DataPoint[]): HandoverEvent[] => {
        const events: HandoverEvent[] = []
        let currentEvent: Partial<HandoverEvent> | null = null

        data.forEach((point, index) => {
            const time = index * 10 // 10秒間隔

            if (point.triggerConditionMet && !currentEvent) {
                // 開始新的換手事件
                currentEvent = {
                    startTime: time,
                    sourceSatellite: point.satelliteInfo.name,
                    triggerStrength: point.d2EventDetails.triggerProbability,
                }
            } else if (point.triggerConditionMet && currentEvent) {
                // 更新換手事件
                currentEvent.triggerStrength = Math.max(
                    currentEvent.triggerStrength || 0,
                    point.d2EventDetails.triggerProbability
                )
            } else if (!point.triggerConditionMet && currentEvent) {
                // 結束換手事件
                const event: HandoverEvent = {
                    startTime: currentEvent.startTime!,
                    endTime: time,
                    triggerStrength: currentEvent.triggerStrength!,
                    handoverLikelihood: currentEvent.triggerStrength! > 0.8 ? 'high' :
                                       currentEvent.triggerStrength! > 0.5 ? 'medium' : 'low',
                    sourceSatellite: currentEvent.sourceSatellite!,
                    targetSatellite: point.satelliteInfo.name,
                    triggerReason: 'D2距離觸發條件滿足',
                }

                events.push(event)
                
                // 觸發換手事件檢測回調
                if (onHandoverEventDetected) {
                    onHandoverEventDetected(event)
                }

                currentEvent = null
            }
        })

        return events
    }, [onHandoverEventDetected])

    // 時間同步處理
    const handleTimeChange = useCallback((newTime: number) => {
        setTimeSync(prev => {
            const updated = { ...prev, currentTime: newTime }
            
            // 同步到立體圖
            if (sceneControl && config.enableAutoSync) {
                const sceneTime = sceneControl.getCurrentTime()
                if (Math.abs(sceneTime - newTime) > config.syncTolerance) {
                    sceneControl.setCurrentTime(newTime)
                }
            }
            
            // 觸發時間同步回調
            if (onTimeSync) {
                onTimeSync(updated)
            }
            
            return updated
        })
    }, [sceneControl, config.enableAutoSync, config.syncTolerance, onTimeSync])

    // 播放控制
    const handlePlayPause = useCallback(() => {
        setTimeSync(prev => {
            const updated = { ...prev, isPlaying: !prev.isPlaying }
            
            if (sceneControl) {
                if (updated.isPlaying) {
                    sceneControl.play()
                } else {
                    sceneControl.pause()
                }
            }
            
            return updated
        })
    }, [sceneControl])

    // 播放速度控制
    const handleSpeedChange = useCallback((speed: number) => {
        setTimeSync(prev => {
            const updated = { ...prev, playbackSpeed: speed }
            
            if (sceneControl) {
                sceneControl.setPlaybackSpeed(speed)
            }
            
            return updated
        })
    }, [sceneControl])

    // 自動播放邏輯
    useEffect(() => {
        if (!timeSync.isPlaying) return

        const interval = setInterval(() => {
            setTimeSync(prev => {
                const nextTime = prev.currentTime + prev.playbackSpeed
                if (nextTime >= prev.totalDuration) {
                    return { ...prev, currentTime: 0, isPlaying: false }
                }
                return { ...prev, currentTime: nextTime }
            })
        }, 1000)

        return () => clearInterval(interval)
    }, [timeSync.isPlaying, timeSync.playbackSpeed])

    // 從立體圖接收時間更新
    useEffect(() => {
        if (sceneControl && sceneControl.onTimeUpdate) {
            sceneControl.onTimeUpdate = (time: number) => {
                if (config.enableAutoSync) {
                    handleTimeChange(time)
                }
            }
        }
    }, [sceneControl, config.enableAutoSync, handleTimeChange])

    // 渲染載入狀態
    if (isLoading) {
        return (
            <div 
                className={`synchronized-d2-dashboard loading ${className}`}
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '400px',
                    backgroundColor: '#1a1a1a',
                    color: '#ffffff',
                    borderRadius: '12px',
                    ...style,
                }}
            >
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '24px', marginBottom: '16px' }}>🛰️</div>
                    <div>正在處理 D2 事件數據...</div>
                    <div style={{ fontSize: '14px', opacity: 0.7, marginTop: '8px' }}>
                        應用 SGP4 精確軌道計算與智能平滑化
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div 
            className={`synchronized-d2-dashboard ${className}`}
            style={{
                backgroundColor: '#1a1a1a',
                borderRadius: '12px',
                padding: '16px',
                ...style,
            }}
        >
            {/* 控制面板 */}
            {config.showControlPanel && (
                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '16px',
                    padding: '12px',
                    backgroundColor: '#2d3748',
                    borderRadius: '8px',
                    color: '#ffffff',
                }}>
                    {/* 播放控制 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <button
                            onClick={handlePlayPause}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: timeSync.isPlaying ? '#dc3545' : '#28a745',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                cursor: 'pointer',
                                fontWeight: 'bold',
                            }}
                        >
                            {timeSync.isPlaying ? '⏸️ 暫停' : '▶️ 播放'}
                        </button>
                        
                        <select
                            value={timeSync.playbackSpeed}
                            onChange={(e) => handleSpeedChange(Number(e.target.value))}
                            style={{
                                padding: '6px 10px',
                                backgroundColor: '#4a5568',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                            }}
                        >
                            <option value={0.5}>0.5x</option>
                            <option value={1}>1x</option>
                            <option value={2}>2x</option>
                            <option value={5}>5x</option>
                        </select>
                    </div>

                    {/* 時間顯示 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div>
                            時間: {timeSync.currentTime.toFixed(1)}s / {timeSync.totalDuration}s
                        </div>
                        
                        {/* 換手事件統計 */}
                        <div style={{
                            padding: '4px 12px',
                            backgroundColor: '#28a745',
                            borderRadius: '4px',
                            fontSize: '12px',
                        }}>
                            換手事件: {handoverEvents.length} 個
                        </div>
                    </div>

                    {/* 同步狀態 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            backgroundColor: config.enableAutoSync ? '#28a745' : '#6c757d',
                        }} />
                        <span style={{ fontSize: '12px' }}>
                            {config.enableAutoSync ? '同步已啟用' : '同步已停用'}
                        </span>
                    </div>
                </div>
            )}

            {/* 數據品質面板 */}
            {config.showDataQualityPanel && dataQualityMetrics && (
                <div style={{
                    display: 'flex',
                    gap: '12px',
                    marginBottom: '16px',
                    flexWrap: 'wrap',
                }}>
                    <div style={{
                        flex: '1',
                        minWidth: '200px',
                        padding: '12px',
                        backgroundColor: '#2d3748',
                        borderRadius: '8px',
                        color: '#ffffff',
                    }}>
                        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>數據品質</div>
                        <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <div>總數據點: {dataQualityMetrics.totalPoints}</div>
                            <div>信噪比: {dataQualityMetrics.signalToNoiseRatio.toFixed(1)}</div>
                            <div>平滑效果: {(dataQualityMetrics.smoothingEffectiveness * 100).toFixed(1)}%</div>
                            <div>觸發準確度: {(dataQualityMetrics.triggerAccuracy * 100).toFixed(1)}%</div>
                        </div>
                    </div>
                    
                    <div style={{
                        flex: '1',
                        minWidth: '200px',
                        padding: '12px',
                        backgroundColor: '#2d3748',
                        borderRadius: '8px',
                        color: '#ffffff',
                    }}>
                        <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>處理性能</div>
                        <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <div>處理時間: {processingTime.toFixed(2)}ms</div>
                            <div>高可能性事件: {handoverEvents.filter(e => e.handoverLikelihood === 'high').length}</div>
                            <div>中等可能性事件: {handoverEvents.filter(e => e.handoverLikelihood === 'medium').length}</div>
                            <div>低可能性事件: {handoverEvents.filter(e => e.handoverLikelihood === 'low').length}</div>
                        </div>
                    </div>
                </div>
            )}

            {/* 改進版 D2 圖表 */}
            <ImprovedD2Chart
                data={processedData}
                thresh1={config.triggerConfig.thresh1}
                thresh2={config.triggerConfig.thresh2}
                hysteresis={config.triggerConfig.hysteresis}
                showThresholdLines={true}
                showRawData={config.showRawData}
                isDarkTheme={true}
                height={config.chartHeight}
                currentTime={timeSync.currentTime}
                onTimeChange={handleTimeChange}
                highlightTriggerPatterns={config.highlightTriggerPatterns}
                showHandoverPrediction={config.showHandoverPrediction}
                smoothingWindowSize={config.smoothingConfig.movingAverageWindow}
                smoothingAlpha={config.smoothingConfig.exponentialAlpha}
                onDataPointClick={(dataPoint, index) => {
                    const clickTime = index * 10
                    handleTimeChange(clickTime)
                }}
            />

            {/* 換手事件時間軸 */}
            {handoverEvents.length > 0 && (
                <div style={{
                    marginTop: '16px',
                    padding: '12px',
                    backgroundColor: '#2d3748',
                    borderRadius: '8px',
                    color: '#ffffff',
                }}>
                    <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>
                        換手事件時間軸 ({handoverEvents.length} 個事件)
                    </div>
                    <div style={{
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: '8px',
                    }}>
                        {handoverEvents.map((event, index) => (
                            <button
                                key={index}
                                onClick={() => handleTimeChange(event.startTime)}
                                style={{
                                    padding: '6px 12px',
                                    backgroundColor: 
                                        event.handoverLikelihood === 'high' ? '#dc3545' :
                                        event.handoverLikelihood === 'medium' ? '#fd7e14' : '#ffc107',
                                    color: 'white',
                                    border: 'none',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '12px',
                                    fontWeight: timeSync.currentTime >= event.startTime && 
                                               timeSync.currentTime <= event.endTime ? 'bold' : 'normal',
                                }}
                            >
                                {event.startTime}s-{event.endTime}s ({event.handoverLikelihood})
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default SynchronizedD2Dashboard