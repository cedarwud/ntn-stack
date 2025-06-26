import React from 'react'
import { SatelliteConnection, HandoverState } from '../../../../types/handover'
import {
    getSignalQualityLevel,
    getSignalQualityPercentage,
} from '../config/handoverConfig'
import './UnifiedHandoverStatus.scss'

interface UnifiedHandoverStatusProps {
    currentConnection: SatelliteConnection | null
    predictedConnection: SatelliteConnection | null
    handoverState: HandoverState
    isTransitioning: boolean
    transitionProgress: number
    predictionResult?: unknown
    algorithmRunning?: boolean
    deltaT?: number
}

const UnifiedHandoverStatus: React.FC<UnifiedHandoverStatusProps> = ({
    currentConnection,
    predictedConnection,
    handoverState,
    isTransitioning,
    transitionProgress,
    predictionResult,
    algorithmRunning = false,
    deltaT,
}) => {
    // 統一的衛星資訊顯示格式
    const formatSatelliteInfo = (
        connection: SatelliteConnection | null,
        type: 'current' | 'predicted'
    ) => {
        if (!connection) {
            return (
                <div className="satellite-card no-connection">
                    <div className="satellite-header">
                        <span className="satellite-icon">🛰️</span>
                        <span className="satellite-name">無連接</span>
                    </div>
                    <div className="satellite-status">等待連接...</div>
                </div>
            )
        }

        return (
            <div className={`satellite-card ${type}`}>
                <div className="satellite-header">
                    <span className="satellite-icon">🛰️</span>
                    <div className="satellite-identity">
                        <span className="satellite-name">
                            {connection.satelliteName}
                        </span>
                        <span className="satellite-id">
                            ID: {connection.satelliteId}
                        </span>
                    </div>
                </div>
                <div className="satellite-metrics">
                    <div className="metric">
                        <span className="label">仰角</span>
                        <span className="value">
                            {connection.elevation?.toFixed(1) || 'N/A'}°
                        </span>
                    </div>
                    <div className="metric">
                        <span className="label">信號強度</span>
                        <span className="value">
                            {connection.signalStrength?.toFixed(1) || 'N/A'} dBm
                        </span>
                    </div>
                    <div className="metric">
                        <span className="label">距離</span>
                        <span className="value">
                            {connection.distance?.toFixed(0) || 'N/A'} km
                        </span>
                    </div>
                </div>
                <div className="connection-quality">
                    <div className="quality-bar">
                        <div
                            className={`quality-fill ${getQualityClass(
                                connection.signalStrength || 0
                            )}`}
                            style={{
                                width: `${getQualityPercentage(
                                    connection.signalStrength || 0
                                )}%`,
                            }}
                        ></div>
                    </div>
                    <span className="quality-text">
                        {getQualityText(connection.signalStrength || 0)}
                    </span>
                </div>
            </div>
        )
    }

    // 信號品質計算
         
         
    const getQualityPercentage = getSignalQualityPercentage

         
         
    const getQualityClass = getSignalQualityLevel

         
         
    const getQualityText = (signalStrength: number) => {
        const level = getSignalQualityLevel(signalStrength)
        const textMap = {
            excellent: '優秀',
            good: '良好',
            fair: '一般',
            poor: '較弱',
        }
        return textMap[level]
    }

    // 換手狀態指示器
         
         
    const getHandoverStatusDisplay = () => {
        const statusConfig = {
            idle: { icon: '⏸️', text: '待機中', class: 'idle' },
            calculating: { icon: '🧮', text: '計算中', class: 'calculating' },
            handover_ready: { icon: '⚡', text: '準備換手', class: 'ready' },
            executing: { icon: '🔄', text: '執行中', class: 'executing' },
            predicting: { icon: '🔮', text: '預測中', class: 'predicting' },
            handover: { icon: '🔄', text: '換手中', class: 'handover' },
            failed: { icon: '❌', text: '失敗', class: 'failed' },
            complete: { icon: '✅', text: '完成', class: 'complete' },
        }

        const config =
            statusConfig[handoverState.status as keyof typeof statusConfig] ||
            statusConfig.idle

        return (
            <div className={`handover-status ${config.class}`}>
                <span className="status-icon">{config.icon}</span>
                <span className="status-text">{config.text}</span>
                {algorithmRunning && (
                    <span className="algorithm-indicator">🤖</span>
                )}
            </div>
        )
    }

    return (
        <div className="unified-handover-status">
            {/* 標題區域 */}
            <div className="status-header">
                <h3>🔄 換手狀態監控</h3>
                {getHandoverStatusDisplay()}
            </div>

            {/* 主要狀態區域 */}
            <div className="status-main">
                {/* 當前連接 */}
                <div className="connection-section current">
                    <div className="section-header">
                        <span className="section-title">當前時間 T</span>
                        <span className="section-subtitle">
                            {new Date().toLocaleTimeString()}
                        </span>
                    </div>
                    {formatSatelliteInfo(currentConnection, 'current')}
                </div>

                {/* 時間間隔顯示 */}
                <div className="time-transition">
                    <div className="transition-arrow">
                        <span className="arrow">➤</span>
                        {deltaT && (
                            <div className="delta-time">
                                <div className="delta-value">
                                    Δt = {Math.round(deltaT)}s
                                </div>
                                <div className="delta-minutes">
                                    ({(deltaT / 60).toFixed(1)}分鐘)
                                </div>
                            </div>
                        )}
                    </div>

                    {/* 進度條 */}
                    {isTransitioning && (
                        <div className="transition-progress">
                            <div className="progress-bar">
                                <div
                                    className="progress-fill"
                                    style={{ width: `${transitionProgress}%` }}
                                ></div>
                            </div>
                            <span className="progress-text">
                                {transitionProgress.toFixed(1)}%
                            </span>
                        </div>
                    )}
                </div>

                {/* 預測連接 */}
                <div className="connection-section predicted">
                    <div className="section-header">
                        <span className="section-title">預測時間 T+Δt</span>
                        <span className="section-subtitle">
                            {deltaT
                                ? new Date(
                                      Date.now() + deltaT * 1000
                                  ).toLocaleTimeString()
                                : 'N/A'}
                        </span>
                    </div>
                    {formatSatelliteInfo(predictedConnection, 'predicted')}
                </div>
            </div>

            {/* 預測置信度 */}
            {predictionResult && (
                <div className="prediction-confidence">
                    <div className="confidence-header">
                        <span>預測準確度</span>
                    </div>
                    <div className="confidence-meter">
                        <div
                            className="confidence-fill"
                            style={{
                                width: `${
                                    ((
                                        predictionResult as {
                                            prediction_confidence?: number
                                        }
                                    )?.prediction_confidence || 0.95) * 100
                                }%`,
                            }}
                        ></div>
                        <span className="confidence-text">
                            {(
                                ((
                                    predictionResult as {
                                        prediction_confidence?: number
                                    }
                                )?.prediction_confidence || 0.95) * 100
                            ).toFixed(1)}
                            %
                        </span>
                    </div>
                </div>
            )}

            {/* 換手決策 */}
            {predictionResult && (
                <div className="handover-decision">
                    <span className="decision-label">換手決策:</span>
                    <span
                        className={`decision-value ${
                            (
                                predictionResult as {
                                    handover_required?: boolean
                                }
                            )?.handover_required
                                ? 'required'
                                : 'not-required'
                        }`}
                    >
                        {(predictionResult as { handover_required?: boolean })
                            ?.handover_required
                            ? '需要換手'
                            : '無需換手'}
                    </span>
                </div>
            )}
        </div>
    )
}

export default UnifiedHandoverStatus
