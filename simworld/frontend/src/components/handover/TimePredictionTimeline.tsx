import React, { useState, useEffect } from 'react'
import { TimePredictionData } from '../../types/handover'
import './TimePredictionTimeline.scss'

interface TimePredictionTimelineProps {
    data: TimePredictionData
    isActive: boolean
    onTimeUpdate?: (currentTime: number) => void
}

const TimePredictionTimeline: React.FC<TimePredictionTimelineProps> = ({
    data,
    isActive,
    onTimeUpdate,
}) => {
    const [currentTime, setCurrentTime] = useState(Date.now())

    useEffect(() => {
        if (!isActive) return

        const interval = setInterval(() => {
            const now = Date.now()
            setCurrentTime(now)
            onTimeUpdate?.(now)
        }, 100) // 100ms 更新間隔

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

                    {/* 換手觸發點 */}
                    {data.handoverTime && (
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
                    <span className="delta-label">Δt 間隔:</span>
                    <span className="delta-value">
                        {((data.futureTime - data.currentTime) / 1000).toFixed(
                            1
                        )}
                        s
                    </span>
                </div>
                {data.handoverTime && (
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
            </div>

            {/* Binary Search 迭代過程 */}
            {data.iterations.length > 0 && (
                <div className="binary-search-iterations">
                    <h4>🔍 Binary Search Refinement</h4>
                    <div className="iterations-list">
                        {data.iterations.map((iteration) => (
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
                                    {iteration.completed ? '✅' : '⏳'}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}

export default TimePredictionTimeline
