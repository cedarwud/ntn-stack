import React, { useState, useEffect } from 'react'
import { TimePredictionData } from '../../../../types/handover'
import { HANDOVER_CONFIG } from '../config/handoverConfig'
import './TimePredictionTimeline.scss'

interface TimePredictionTimelineProps {
    data: TimePredictionData
    isActive: boolean
    onTimeUpdate?: (currentTime: number) => void
    handoverRequired?: boolean // 新增：是否真的需要換手
}

const TimePredictionTimeline: React.FC<TimePredictionTimelineProps> = ({
    data,
    isActive,
    onTimeUpdate,
    handoverRequired = true, // 預設為 true 保持向後兼容
}) => {
    const [currentTime, setCurrentTime] = useState(Date.now())

    // 移除調試日誌，避免控制台被刷爆
    // const prevIterationsCountRef = useRef(0)
    // useEffect(() => {
    //     const currentCount = data.iterations?.length || 0
    //     if (currentCount !== prevIterationsCountRef.current) {
    //         console.log(`🎯 TimePredictionTimeline Binary Search 更新:`, {
    //             iterationsCount: currentCount,
    //             currentTime: new Date(data.currentTime).toLocaleTimeString(),
    //             futureTime: new Date(data.futureTime).toLocaleTimeString(),
    //         })
    //         prevIterationsCountRef.current = currentCount
    //     }
    // }, [data.iterations?.length, data.currentTime, data.futureTime])

    useEffect(() => {
        if (!isActive) return

        const interval = setInterval(() => {
            const now = Date.now()
            setCurrentTime(now)
            onTimeUpdate?.(now)
        }, HANDOVER_CONFIG.TIMING.UPDATE_INTERVAL_MS)

        return () => clearInterval(interval)
    }, [isActive, onTimeUpdate])

    const formatTime = (timestamp: number) => {
        return new Date(timestamp).toLocaleTimeString('zh-TW', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        })
    }

         
         
    const getTimelineProgress = () => {
        const totalDuration = data.futureTime - data.currentTime
        const elapsed = currentTime - data.currentTime
        return Math.min(Math.max(elapsed / totalDuration, 0), 1) * 100
    }

         
         
    const getHandoverProgress = () => {
        if (!data.handoverTime) return null
        const totalDuration = data.futureTime - data.currentTime
        const handoverOffset = data.handoverTime - data.currentTime
        return Math.min(Math.max(handoverOffset / totalDuration, 0), 1) * 100
    }

    // 根據時間軸進度計算迭代完成狀態
         
         
    const getIterationStatus = (iterationNumber: number) => {
        const progress = getTimelineProgress() / 100 // 0-1
        const totalIterations = data.iterations.length

        // 每個迭代在時間軸的不同階段完成
        const iterationThreshold = iterationNumber / totalIterations

        if (progress >= iterationThreshold) {
            return '✅' // 已完成
        } else {
            return '⏳' // 進行中
        }
    }

    return (
        <div className="time-prediction-timeline">
            <div className="timeline-header">
                <h3>🕐 二點預測時間軸</h3>
                <div className="accuracy-indicator">
                    <span>預測準確率</span>
                    <div className="accuracy-meter">
                        <div
                            className="accuracy-fill"
                            style={{ width: `${data.accuracy * 100}%` }}
                        ></div>
                        <span className="accuracy-text">
                            {(data.accuracy * 100).toFixed(1)}%
                        </span>
                    </div>
                </div>
            </div>

            <div className="timeline-container">
                {/* 時間軸主線 */}
                <div className="timeline-track">
                    <div
                        className="timeline-progress"
                        style={{ width: `${getTimelineProgress()}%` }}
                    ></div>

                    {/* 換手觸發點 - 只有在需要換手時才顯示 */}
                    {data.handoverTime && handoverRequired && (
                        <div
                            className="handover-marker"
                            style={{ left: `${getHandoverProgress()}%` }}
                            title={`預測換手時間: ${formatTime(
                                data.handoverTime
                            )}`}
                        >
                            <div className="marker-icon">⚡</div>
                            <div className="marker-label">Tp</div>
                        </div>
                    )}
                </div>

                {/* 時間點標記 */}
                <div className="time-markers">
                    <div className="time-marker start">
                        <div className="marker-point"></div>
                        <div className="marker-label">
                            <strong>T</strong>
                            <span>{formatTime(data.currentTime)}</span>
                        </div>
                    </div>

                    <div className="time-marker end">
                        <div className="marker-point"></div>
                        <div className="marker-label">
                            <strong>T+Δt</strong>
                            <span>{formatTime(data.futureTime)}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Delta T 顯示 */}
            <div className="delta-info">
                <div className="delta-item">
                    <span className="delta-label">剩餘時間:</span>
                    <span className="delta-value">
                        {Math.max(
                            0,
                            (data.futureTime - currentTime) / 1000
                        ).toFixed(1)}
                        s
                    </span>
                </div>
                {data.handoverTime && handoverRequired && (
                    <div className="delta-item">
                        <span className="delta-label">距離換手:</span>
                        <span className="delta-value">
                            {Math.max(
                                0,
                                (data.handoverTime - currentTime) / 1000
                            ).toFixed(1)}
                            s
                        </span>
                    </div>
                )}
                {!handoverRequired && (
                    <div className="delta-item">
                        <span className="delta-label">換手狀態:</span>
                        <span className="delta-value no-handover">
                            無需換手
                        </span>
                    </div>
                )}
            </div>

            {/* Binary Search 迭代過程 - 總是顯示 */}
            <div className="binary-search-iterations">
                <h4>🔍 Binary Search Refinement</h4>
                <div className="iterations-list">
                    {data.iterations.length > 0 ? (
                        data.iterations.map((iteration) => (
                            <div
                                key={iteration.iteration}
                                className={`iteration-item ${
                                    iteration.completed ? 'completed' : 'active'
                                }`}
                            >
                                <div className="iteration-number">
                                    #{iteration.iteration}
                                </div>
                                <div className="iteration-details">
                                    <div className="iteration-range">
                                        範圍:{' '}
                                        {(
                                            iteration.endTime -
                                            iteration.startTime
                                        ).toFixed(3)}
                                        s
                                    </div>
                                    <div className="iteration-precision">
                                        精度:{' '}
                                        {(iteration.precision * 1000).toFixed(
                                            1
                                        )}
                                        ms
                                    </div>
                                    <div className="iteration-satellite">
                                        衛星: {iteration.satellite}
                                    </div>
                                </div>
                                <div className="iteration-status">
                                    {getIterationStatus(iteration.iteration)}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="empty-iterations">
                            <div className="empty-message">
                                <span className="empty-icon">📊</span>
                                <span>無需複雜搜尋：使用直接預測結果</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default TimePredictionTimeline
