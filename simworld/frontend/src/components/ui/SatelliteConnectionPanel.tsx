import React, { useState, useEffect, useRef } from 'react'
import './SatelliteConnectionPanel.scss'

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

// 穩定的模擬數據生成器 - 與3D場景換手週期同步
const generateStableMockData = () => {
    const generateSatName = () => `STARLINK-${Math.floor(1000 + Math.random() * 8999)}`
    const reasons = ['signal_weak', 'better_option', 'coverage_edge'] as const
    const qualities = ['excellent', 'good', 'weak'] as const
    
    // 計算與3D場景同步的倒數時間（45秒週期）
    const handoverCycle = 45000 // 45秒週期，與3D場景一致
    const currentTime = Date.now()
    const cycleProgress = (currentTime % handoverCycle) / handoverCycle
    
    // 準備期在週期的67%開始（30秒），倒數5秒
    let initialCountdown
    if (cycleProgress < 0.67) {
        // 還沒到準備期，計算剩餘時間
        initialCountdown = Math.floor((0.67 - cycleProgress) * handoverCycle / 1000)
    } else if (cycleProgress >= 0.67 && cycleProgress <= 0.78) {
        // 準備期：倒數5秒
        initialCountdown = Math.floor((0.78 - cycleProgress) * handoverCycle / 1000)
    } else {
        // 已經在換手過程中或完成，計算到下一個週期
        initialCountdown = Math.floor((1.67 - cycleProgress) * handoverCycle / 1000)
    }
    
    return {
        currentSat: generateSatName(),
        nextSat: generateSatName(), 
        signalQuality: qualities[Math.floor(Math.random() * qualities.length)],
        reason: reasons[Math.floor(Math.random() * reasons.length)],
        initialCountdown: Math.max(5, initialCountdown) // 最少5秒
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
        
        // 檢查是否有真實數據
        const hasRealData = currentConnection && predictedConnection && handoverState
        
        if (hasRealData) {
            // 使用真實數據
            const currentSat = currentConnection.satelliteName || `SAT-${currentConnection.satelliteId}`
            const nextSat = predictedConnection.satelliteName || `SAT-${predictedConnection.satelliteId}`
            const signalStrength = currentConnection.signalStrength || -100
            
            let signalQuality: HandoverStatusMetrics['signalQuality']
            if (signalStrength > -60) signalQuality = 'excellent'
            else if (signalStrength > -75) signalQuality = 'good'  
            else if (signalStrength > -90) signalQuality = 'weak'
            else signalQuality = 'lost'
            
            let handoverReason: HandoverStatusMetrics['handoverReason'] = 'none'
            if (predictedConnection && currentConnection) {
                if (signalStrength < -80) handoverReason = 'signal_weak'
                else if (predictedConnection.elevation > currentConnection.elevation + 5) handoverReason = 'better_option'
                else handoverReason = 'coverage_edge'
            }
            
            const handoverTime = handoverState.handoverTime || 0
            const now = Date.now()
            const realCountdown = handoverTime > now ? Math.ceil((handoverTime - now) / 1000) : -1
            
            setMetrics({
                currentSatellite: currentSat,
                nextSatellite: nextSat,
                handoverCountdown: realCountdown,
                signalQuality,
                handoverReason,
                connectionStable: signalQuality === 'excellent' || signalQuality === 'good',
                isHandoverInProgress: isTransitioning,
                handoverProgress: isTransitioning ? transitionProgress * 100 : 0
            })
            
            if (realCountdown > 0) {
                setCountdown(realCountdown)
            }
        } else {
            // 使用模擬數據 - 只在需要重新開始時生成
            if (phaseRef.current === 'need_restart' || !stableDataRef.current) {
                stableDataRef.current = generateStableMockData()
                phaseRef.current = 'preparing'
                setCountdown(stableDataRef.current.initialCountdown)
                console.log('生成新的換手週期:', stableDataRef.current)
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
                    // 穩定期：顯示當前衛星和下一個目標衛星
                    const currentSatelliteName = cycleProgress < 0.5 ? data.currentSat : data.nextSat
                    const nextSatelliteName = cycleProgress < 0.5 ? data.nextSat : data.currentSat
                    setMetrics({
                        currentSatellite: currentSatelliteName,
                        nextSatellite: nextSatelliteName,  // 始終顯示下個目標
                        handoverCountdown: countdown > 5 ? countdown : -1, // 顯示較長的倒數
                        signalQuality: 'good',
                        handoverReason: data.reason, // 顯示預期的換手原因
                        connectionStable: true,
                        isHandoverInProgress: false,
                        handoverProgress: 0
                    })
                } else if (isPreparePhase) {
                    // 準備期：顯示即將換手的倒數計時
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,
                        handoverCountdown: countdown,
                        signalQuality: data.signalQuality,
                        handoverReason: data.reason,
                        connectionStable: false,
                        isHandoverInProgress: false,
                        handoverProgress: 0
                    })
                } else if (isEstablishPhase) {
                    // 建立期：正在建立新連接
                    const establishProgress = ((cycleProgress - 0.78) / 0.06) * 100
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,
                        handoverCountdown: -1,
                        signalQuality: 'weak',
                        handoverReason: data.reason,
                        connectionStable: false,
                        isHandoverInProgress: true,
                        handoverProgress: establishProgress
                    })
                } else if (isSwitchPhase) {
                    // 切換期：雙連接期，正在切換
                    const switchProgress = ((cycleProgress - 0.84) / 0.05) * 100
                    setMetrics({
                        currentSatellite: data.currentSat,
                        nextSatellite: data.nextSat,
                        handoverCountdown: -1,
                        signalQuality: 'weak',
                        handoverReason: data.reason,
                        connectionStable: false,
                        isHandoverInProgress: true,
                        handoverProgress: 50 + switchProgress / 2 // 50-100%
                    })
                } else if (isCompletePhase) {
                    // 完成期：換手完成，穩定在新衛星，準備下次換手
                    setMetrics({
                        currentSatellite: data.nextSat,
                        nextSatellite: data.currentSat, // 為下次換手準備
                        handoverCountdown: countdown > 5 ? countdown : -1,
                        signalQuality: 'good',
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
    
    // 換手原因文字
    const getHandoverReasonText = (reason: string) => {
        switch (reason) {
            case 'signal_weak': return '信號衰減'
            case 'better_option': return '發現更佳衛星'
            case 'coverage_edge': return '接近覆蓋邊緣'
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
                {/* 換手進行中 */}
                {metrics.isHandoverInProgress && (
                    <div className="metric-item critical">
                        <div className="metric-label">🔄 換手中</div>
                        <div className="handover-progress">
                            <div 
                                className="progress-bar"
                                style={{ width: `${metrics.handoverProgress}%` }}
                            ></div>
                            <span className="progress-text">
                                {metrics.handoverProgress.toFixed(0)}%
                            </span>
                        </div>
                    </div>
                )}
                
                {/* 當前衛星信息 - 始終顯示 */}
                <div className="metric-item">
                    <div className="metric-main">
                        <div className="metric-label">📡 當前衛星</div>
                        <div className="metric-value current-sat">
                            {metrics.currentSatellite}
                        </div>
                    </div>
                    <div className="metric-sub-label">
                        信號品質：{getSignalText(metrics.signalQuality)}
                    </div>
                </div>

                {/* 換手倒數計時 - 重新定義語義 */}
                {!metrics.isHandoverInProgress && countdown > 0 && countdown <= 5 && metrics.nextSatellite && (
                    <div className="metric-item countdown-item">
                        <div className="metric-main">
                            <div className="metric-label">⏱️ 開始換手程序</div>
                            <div className="metric-value countdown">
                                {countdown}s
                            </div>
                        </div>
                        <div className="metric-sub-label">準備建立新連接</div>
                    </div>
                )}
                
                {/* 目標衛星和換手原因 - 始終顯示（如果有目標） */}
                {metrics.nextSatellite && (
                    <div className="metric-item reason-item">
                        <div className="metric-main">
                            <div className="metric-label">🎯 下個目標</div>
                            <div className="metric-value reason">
                                {metrics.nextSatellite}
                            </div>
                        </div>
                        {metrics.handoverReason !== 'none' && (
                            <div className="metric-sub-label">
                                預期原因：{getHandoverReasonText(metrics.handoverReason)}
                            </div>
                        )}
                    </div>
                )}
                
                {/* 換手狀態指示 */}
                {!metrics.isHandoverInProgress && countdown <= 0 && (
                    <div className="metric-item">
                        <div className="metric-main">
                            <div className="metric-label">✅ 連接狀態</div>
                            <div className="metric-value stable">
                                {metrics.connectionStable ? '穩定' : '準備中'}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default SatelliteConnectionPanel