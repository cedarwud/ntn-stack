import React, { useState, useEffect, useRef } from 'react'
import './SatelliteConnectionPanel.scss'

/**
 * TODO: 此組件目前使用假數據維持UI功能
 * 
 * 原本的SatelliteUAVConnection組件已暫時移除進行重構
 * 此面板目前完全依賴模擬數據來顯示換手狀態
 * 
 * 重構完成後需要：
 * 1. 重新整合真實的衛星連線數據
 * 2. 連接新的連線狀態管理系統
 * 3. 移除假數據邏輯，恢復真實數據顯示
 */

// 對非技術人員友好的換手狀態指標
interface HandoverStatusMetrics {
    currentSatellite: string // 當前連接的衛星名稱
    nextSatellite: string // 即將換手的目標衛星
    handoverCountdown: number // 換手倒數計時（秒），-1 表示無換手
    signalQuality: 'excellent' | 'good' | 'weak' | 'lost' // 信號品質
    handoverReason: 'signal_weak' | 'better_option' | 'coverage_edge' | 'none' // 換手原因
    connectionStable: boolean // 連接是否穩定
    isHandoverInProgress: boolean
    handoverProgress: number // 0-100
}

interface SatelliteConnectionPanelProps {
    enabled: boolean
    connections: any[]
    isTransitioning?: boolean
    transitionProgress?: number
    currentConnection?: any // 當前連接資訊
    predictedConnection?: any // 預測連接資訊  
    handoverState?: any // 換手狀態資訊
}

// 配合新的持續軌道系統的模擬數據生成器
const generateStableMockData = () => {
    // 使用固定的衛星名稱，配合新的軌道系統
    const satelliteNames = [
        'STARLINK-1001', 'STARLINK-1002', 'STARLINK-1003', 
        'STARLINK-1004', 'STARLINK-1005'
    ]
    
    const reasons = ['signal_weak', 'better_option', 'coverage_edge'] as const
    const qualities = ['excellent', 'good', 'weak'] as const
    
    // 計算與3D場景同步的倒數時間（45秒週期）
    const handoverCycle = 45000
    const currentTime = Date.now()
    const cycleProgress = (currentTime % handoverCycle) / handoverCycle
    
    // 基於時間選擇當前和下一個衛星（模擬真實的最佳衛星選擇）
    const currentIndex = Math.floor(cycleProgress * 2) % satelliteNames.length
    const nextIndex = (currentIndex + 1) % satelliteNames.length
    
    let initialCountdown
    if (cycleProgress < 0.67) {
        initialCountdown = Math.floor((0.67 - cycleProgress) * handoverCycle / 1000)
    } else if (cycleProgress >= 0.67 && cycleProgress <= 0.78) {
        initialCountdown = Math.floor((0.78 - cycleProgress) * handoverCycle / 1000)
    } else {
        initialCountdown = Math.floor((1.67 - cycleProgress) * handoverCycle / 1000)
    }
    
    return {
        currentSat: satelliteNames[currentIndex],
        nextSat: satelliteNames[nextIndex], 
        signalQuality: qualities[Math.floor(cycleProgress * qualities.length)],
        reason: reasons[Math.floor(cycleProgress * reasons.length)],
        initialCountdown: Math.max(5, initialCountdown)
    }
}

const SatelliteConnectionPanel: React.FC<SatelliteConnectionPanelProps> = ({
    enabled,
    connections,
    isTransitioning = false,
    transitionProgress = 0,
    currentConnection,
    predictedConnection,
    handoverState
}) => {
    // 主要顯示狀態
    const [metrics, setMetrics] = useState<HandoverStatusMetrics>({
        currentSatellite: '未連接',
        nextSatellite: '',
        handoverCountdown: -1,
        signalQuality: 'lost',
        handoverReason: 'none',
        connectionStable: false,
        isHandoverInProgress: false,
        handoverProgress: 0
    })
    
    // 倒數計時器 - 獨立管理，不影響其他狀態
    const [countdown, setCountdown] = useState<number>(-1)
    
    // 穩定的基礎數據 - 只在週期重置時更新
    const stableDataRef = useRef<{
        currentSat: string,
        nextSat: string,
        signalQuality: HandoverStatusMetrics['signalQuality'],
        reason: HandoverStatusMetrics['handoverReason']
    } | null>(null)
    
    // 當前階段 - 避免使用 useState 防止不必要的重渲染
    const phaseRef = useRef<'preparing' | 'stable' | 'need_restart'>('stable')
    
    // 倒數計時器效果 - 完全獨立，不依賴其他狀態
    useEffect(() => {
        if (!enabled || countdown <= 0) return
        
        const timer = setTimeout(() => {
            setCountdown(prev => {
                const newCount = prev - 1
                if (newCount <= 0) {
                    // 倒數結束，切換到穩定階段
                    phaseRef.current = 'stable'
                    // 4秒後準備重新開始
                    setTimeout(() => {
                        phaseRef.current = 'need_restart'
                        stableDataRef.current = null // 清除舊數據
                    }, 4000)
                }
                return newCount
            })
        }, 1000)
        
        return () => clearTimeout(timer)
    }, [enabled, countdown])
    
    // 主要狀態管理效果 - 只在關鍵狀態變化時觸發
    useEffect(() => {
        if (!enabled) {
            setMetrics({
                currentSatellite: '未連接',
                nextSatellite: '',
                handoverCountdown: -1,
                signalQuality: 'lost',
                handoverReason: 'none',
                connectionStable: false,
                isHandoverInProgress: false,
                handoverProgress: 0
            })
            setCountdown(-1)
            stableDataRef.current = null
            phaseRef.current = 'stable'
            return
        }
        
        // TODO: 暫時停用真實連線數據，使用假數據維持UI功能
        // 等待重構完成後將重新整合真實的連線數據
        // 原始邏輯：優先使用真實連線數據  
        if (false && connections && connections.length > 0) {
            // 分析雙連線狀態
            const currentConnection = connections.find(c => c.status === 'active' || c.status === 'disconnecting')
            const targetConnection = connections.find(c => c.status === 'establishing')
            const isHandoverActive = connections.some(c => c.status === 'disconnecting' || c.status === 'establishing')
            
            if (currentConnection) {
                const currentSat = `STARLINK-${currentConnection.satelliteId}`
                const targetSat = targetConnection ? `STARLINK-${targetConnection.satelliteId}` : '評估中'
                const elevation = currentConnection.quality?.elevation || 0
                
                // 基於仰角判斷信號質量
                let signalQuality: HandoverStatusMetrics['signalQuality']
                if (elevation > 60) signalQuality = 'excellent'
                else if (elevation > 45) signalQuality = 'good'  
                else if (elevation > 15) signalQuality = 'weak'
                else signalQuality = 'lost'
                
                // 換手原因
                let handoverReason: HandoverStatusMetrics['handoverReason'] = 'none'
                if (isHandoverActive) {
                    if (elevation < 30) handoverReason = 'signal_weak'
                    else handoverReason = 'better_option'
                }
                
                // 計算換手進度
                let handoverProgress = 0
                if (isHandoverActive) {
                    if (targetConnection?.status === 'establishing') {
                        handoverProgress = 60 // 建立新連線階段
                    }
                    if (currentConnection?.status === 'disconnecting') {
                        handoverProgress = 80 // 斷開舊連線階段
                    }
                }
                
                setMetrics({
                    currentSatellite: currentSat,
                    nextSatellite: targetSat,
                    handoverCountdown: -1,
                    signalQuality,
                    handoverReason,
                    connectionStable: !isHandoverActive && elevation > 30,
                    isHandoverInProgress: isHandoverActive,
                    handoverProgress
                })
            }
        } else {
            // 使用模擬數據 - 只在需要重新開始時生成
            if (phaseRef.current === 'need_restart' || !stableDataRef.current) {
                stableDataRef.current = generateStableMockData()
                phaseRef.current = 'preparing'
                setCountdown(stableDataRef.current.initialCountdown)
            }
            
            if (stableDataRef.current) {
                const data = stableDataRef.current
                
                // 檢查當前換手狀態 - 與3D場景同步（45秒週期）
                const handoverCycle = 45000
                const currentTime = Date.now()
                const cycleProgress = (currentTime % handoverCycle) / handoverCycle
                
                // 時間階段定義（與3D場景一致）
                const isStablePhase = cycleProgress >= 0 && cycleProgress <= 0.67     // 0-30秒：穩定期
                const isPreparePhase = cycleProgress > 0.67 && cycleProgress <= 0.78  // 30-35秒：準備期
                const isEstablishPhase = cycleProgress > 0.78 && cycleProgress <= 0.84 // 35-38秒：建立期
                const isSwitchPhase = cycleProgress > 0.84 && cycleProgress <= 0.89   // 38-40秒：切換期
                const isCompletePhase = cycleProgress > 0.89                          // 40-45秒：完成期
                
                if (isStablePhase) {
                    // 穩定期：顯示當前衛星和下一個目標衛星（始終有數據）
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,  // 始終顯示下個目標
                        handoverCountdown: countdown > 5 ? countdown : -1, 
                        signalQuality: 'good',
                        handoverReason: data.reason, // 預期的換手原因
                        connectionStable: true,
                        isHandoverInProgress: false,
                        handoverProgress: 0
                    })
                } else if (isPreparePhase) {
                    // 準備期：顯示即將換手的倒數計時（5秒倒數）
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,
                        handoverCountdown: Math.max(1, Math.floor((0.78 - cycleProgress) * handoverCycle / 1000)),
                        signalQuality: data.signalQuality,
                        handoverReason: data.reason,
                        connectionStable: false,
                        isHandoverInProgress: false,
                        handoverProgress: 0
                    })
                } else if (isEstablishPhase) {
                    // 建立期：正在建立新連接（35-38秒，3秒建立期）
                    const establishProgress = ((cycleProgress - 0.78) / 0.06) * 100
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,
                        handoverCountdown: -1,
                        signalQuality: 'weak',
                        handoverReason: data.reason,
                        connectionStable: false,
                        isHandoverInProgress: true,
                        handoverProgress: Math.min(50, establishProgress) // 0-50%
                    })
                } else if (isSwitchPhase) {
                    // 切換期：雙連接期，正在切換（38-40秒，2秒切換期）
                    const switchProgress = ((cycleProgress - 0.84) / 0.05) * 100
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,
                        handoverCountdown: -1,
                        signalQuality: 'weak',
                        handoverReason: data.reason,
                        connectionStable: false,
                        isHandoverInProgress: true,
                        handoverProgress: Math.min(100, 50 + switchProgress / 2) // 50-100%
                    })
                } else if (isCompletePhase) {
                    // 完成期：換手完成，穩定在新衛星（40-45秒，5秒穩定期）
                    setMetrics({
                        currentSatellite: data.nextSat, // 現在連接到新衛星
                        nextSatellite: data.currentSat, // 下次換手目標
                        handoverCountdown: -1, // 完成期不顯示倒數
                        signalQuality: 'excellent', // 換手完成，信號優秀
                        handoverReason: data.reason, // 顯示下次換手原因
                        connectionStable: true,
                        isHandoverInProgress: false,
                        handoverProgress: 0
                    })
                }
            }
        }
    }, [enabled, currentConnection, predictedConnection, handoverState, isTransitioning, transitionProgress])
    
    // 當計時器狀態變化時，更新顯示的倒數計時 - 不觸發其他邏輯
    useEffect(() => {
        if (phaseRef.current === 'preparing' && countdown > 0) {
            setMetrics(prev => ({
                ...prev,
                handoverCountdown: countdown
            }))
        }
    }, [countdown])

    if (!enabled) {
        return null
    }

    // TODO: 目前強制使用假數據，重構完成後恢復真實連線數據檢查
    const hasRealConnections = false // 原本：connections && connections.length > 0

    // 信號品質指示器顏色
    const getSignalColor = (quality: string) => {
        switch (quality) {
            case 'excellent': return '#00ff00'
            case 'good': return '#90EE90'  
            case 'weak': return '#ffaa00'
            case 'lost': return '#ff0000'
            default: return '#666666'
        }
    }

    // 信號品質文字
    const getSignalText = (quality: string) => {
        switch (quality) {
            case 'excellent': return '優秀'
            case 'good': return '良好'
            case 'weak': return '微弱' 
            case 'lost': return '斷線'
            default: return '未知'
        }
    }
    
    // 換手原因文字（基於距離邏輯）
    const getHandoverReasonText = (reason: string) => {
        switch (reason) {
            case 'signal_weak': return '當前衛星距離過遠'
            case 'better_option': return '發現更近的衛星'
            case 'coverage_edge': return '衛星移動至邊緣'
            case 'none': return ''
            default: return ''
        }
    }

    return (
        <div className="satellite-connection-panel compact">
            <div className="panel-header">
                <span className="panel-icon">🛰️</span>
                <h3>換手監控</h3>
                <div 
                    className="signal-indicator" 
                    style={{ backgroundColor: getSignalColor(metrics.signalQuality) }}
                    title={`信號品質: ${getSignalText(metrics.signalQuality)}`}
                ></div>
            </div>
            
            <div className="compact-metrics">
                {/* 換手狀態 - 最重要的資訊 */}
                <div className="metric-item status-primary">
                    <div className="metric-main">
                        <div className="metric-label large">📶 連線狀態</div>
                        <div className={`metric-value large ${metrics.isHandoverInProgress ? 'handover-active' : 'stable'}`}>
                            {metrics.isHandoverInProgress ? '🔄 換手進行中' : '✅ 連線穩定'}
                        </div>
                    </div>
                    {metrics.isHandoverInProgress && (
                        <div className="handover-progress">
                            <div 
                                className="progress-bar"
                                style={{ width: `${metrics.handoverProgress}%` }}
                            ></div>
                            <span className="progress-text large">
                                {metrics.handoverProgress.toFixed(0)}%
                            </span>
                        </div>
                    )}
                </div>
                
                {/* 雙連線狀態顯示 */}
                <div className="metric-item dual-connections">
                    <div className="metric-main">
                        <div className="metric-label medium">📡 當前連線</div>
                        <div className={`metric-value medium quality-${metrics.signalQuality}`}>
                            {metrics.currentSatellite}
                        </div>
                    </div>
                    <div className="metric-sub-label">
                        信號: {getSignalText(metrics.signalQuality)}
                    </div>
                    
                    {metrics.isHandoverInProgress && (
                        <>
                            <div className="metric-main" style={{ marginTop: '8px' }}>
                                <div className="metric-label medium">🎯 目標連線</div>
                                <div className="metric-value medium target-satellite">
                                    {metrics.nextSatellite}
                                </div>
                            </div>
                            <div className="metric-sub-label">
                                建立中...
                            </div>
                        </>
                    )}
                </div>

                {/* 換手原因 */}
                {metrics.handoverReason && metrics.handoverReason !== 'none' && (
                    <div className="metric-item reason-item">
                        <div className="metric-main">
                            <div className="metric-label medium">⚠️ 換手原因</div>
                            <div className="metric-value medium reason">
                                {getHandoverReasonText(metrics.handoverReason)}
                            </div>
                        </div>
                    </div>
                )}
                
                {/* TODO: 連線參數暫時使用假數據 */}
                {enabled && (
                    <div className="metric-item params-item">
                        <div className="metric-params">
                            <div className="param">
                                <span className="param-label">仰角:</span>
                                <span className="param-value">45.0°</span> {/* TODO: 假數據 */}
                            </div>
                            <div className="param">
                                <span className="param-label">距離:</span>
                                <span className="param-value">580km</span> {/* TODO: 假數據 */}
                            </div>
                            <div className="param">
                                <span className="param-label">信號:</span>
                                <span className="param-value">-85.2dBm</span> {/* TODO: 假數據 */}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default SatelliteConnectionPanel