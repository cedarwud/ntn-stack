import React, { useState } from 'react'
import { HandoverState, SatelliteConnection } from '../../types/handover'
import { VisibleSatelliteInfo } from '../../types/satellite'
import './HandoverControlPanel.scss'

interface HandoverControlPanelProps {
    handoverState: HandoverState
    availableSatellites: VisibleSatelliteInfo[]
    currentConnection: SatelliteConnection | null
    onManualHandover: (targetSatelliteId: string) => void
    onCancelHandover: () => void
    isEnabled: boolean
}

const HandoverControlPanel: React.FC<HandoverControlPanelProps> = ({
    handoverState,
    availableSatellites,
    currentConnection,
    onManualHandover,
    onCancelHandover,
    isEnabled,
}) => {
    const [selectedSatelliteId, setSelectedSatelliteId] = useState<string>('')
    const [showConfirmDialog, setShowConfirmDialog] = useState(false)

    // 過濾可用衛星（排除當前連接的衛星）
    const handoverCandidates = availableSatellites.filter(
        (sat) => sat.norad_id !== currentConnection?.satelliteId
    )

    const handleSatelliteSelect = (satelliteId: string) => {
        setSelectedSatelliteId(satelliteId)
    }

    const handleHandoverInitiate = () => {
        if (!selectedSatelliteId || !isEnabled) return
        setShowConfirmDialog(true)
    }

    const handleConfirmHandover = () => {
        onManualHandover(selectedSatelliteId)
        setShowConfirmDialog(false)
        setSelectedSatelliteId('')
    }

    const handleCancelConfirm = () => {
        setShowConfirmDialog(false)
    }

    const getStatusInfo = () => {
        switch (handoverState.status) {
            case 'idle':
                return { text: '待機中', color: '#b0d4e7', icon: '⏸️' }
            case 'predicting':
                return { text: '預測中', color: '#ffa500', icon: '🔮' }
            case 'handover':
                return { text: '換手中', color: '#ff6b35', icon: '🔄' }
            case 'complete':
                return { text: '完成', color: '#44ff44', icon: '✅' }
            case 'failed':
                return { text: '失敗', color: '#ff4444', icon: '❌' }
            default:
                return { text: '未知', color: '#b0d4e7', icon: '❓' }
        }
    }

    const renderSatelliteOption = (satellite: VisibleSatelliteInfo) => {
        const isSelected = selectedSatelliteId === satellite.norad_id
        const signalQuality = Math.max(
            0,
            Math.min(100, satellite.elevation_deg * 2)
        ) // 簡化的信號品質計算

        return (
            <div
                key={satellite.norad_id}
                className={`satellite-option ${isSelected ? 'selected' : ''}`}
                onClick={() => handleSatelliteSelect(satellite.norad_id)}
                title={`選擇 ${satellite.name} 作為換手目標`}
            >
                <div className="option-header">
                    <div className="satellite-icon">🛰️</div>
                    <div className="satellite-name">{satellite.name}</div>
                    {isSelected && <div className="selected-indicator">✓</div>}
                </div>

                <div className="satellite-details">
                    <div className="detail-item">
                        <span className="detail-label">ID:</span>
                        <span className="detail-value">
                            {satellite.norad_id}
                        </span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">仰角:</span>
                        <span className="detail-value">
                            {satellite.elevation_deg.toFixed(1)}°
                        </span>
                    </div>
                    <div className="detail-item">
                        <span className="detail-label">距離:</span>
                        <span className="detail-value">
                            {satellite.distance_km.toFixed(0)} km
                        </span>
                    </div>
                </div>

                <div className="signal-quality">
                    <div className="quality-bar">
                        <div
                            className="quality-fill"
                            style={{ width: `${signalQuality}%` }}
                        ></div>
                    </div>
                    <span className="quality-text">
                        {signalQuality.toFixed(0)}%
                    </span>
                </div>
            </div>
        )
    }

    const statusInfo = getStatusInfo()

    return (
        <div
            className={`handover-control-panel ${!isEnabled ? 'disabled' : ''}`}
        >
            <div className="panel-header">
                <h3>🎛️ 手動換手控制</h3>
                <div className="status-indicator">
                    <span className="status-icon">{statusInfo.icon}</span>
                    <span
                        className="status-text"
                        style={{ color: statusInfo.color }}
                    >
                        {statusInfo.text}
                    </span>
                </div>
            </div>

            {!isEnabled && (
                <div className="disabled-overlay">
                    <div className="disabled-message">
                        <div className="disabled-icon">🚫</div>
                        <div className="disabled-text">
                            換手控制已停用
                            <br />
                            <small>請確認系統狀態和權限</small>
                        </div>
                    </div>
                </div>
            )}

            {/* 當前連接資訊 */}
            {currentConnection && (
                <div className="current-connection">
                    <div className="connection-label">當前連接衛星</div>
                    <div className="connection-info">
                        <div className="connection-name">
                            {currentConnection.satelliteName}
                        </div>
                        <div className="connection-details">
                            ID: {currentConnection.satelliteId} | 仰角:{' '}
                            {currentConnection.elevation.toFixed(1)}° | 信號:{' '}
                            {currentConnection.signalStrength.toFixed(1)} dBm
                        </div>
                    </div>
                </div>
            )}

            {/* 可用衛星選擇 */}
            <div className="satellite-selection">
                <div className="selection-header">
                    <span className="selection-title">選擇目標衛星</span>
                    <span className="selection-count">
                        {handoverCandidates.length} 個可用
                    </span>
                </div>

                {handoverCandidates.length > 0 ? (
                    <div className="satellites-list">
                        {handoverCandidates.map(renderSatelliteOption)}
                    </div>
                ) : (
                    <div className="no-satellites">
                        <div className="no-satellites-icon">🚫</div>
                        <div className="no-satellites-text">
                            暫無可用的換手目標衛星
                        </div>
                    </div>
                )}
            </div>

            {/* 控制按鈕 */}
            <div className="control-buttons">
                <button
                    className="handover-button"
                    onClick={handleHandoverInitiate}
                    disabled={
                        !selectedSatelliteId ||
                        !isEnabled ||
                        handoverState.status === 'handover' ||
                        handoverState.status === 'predicting'
                    }
                >
                    {handoverState.status === 'handover' ? (
                        <>🔄 換手進行中...</>
                    ) : (
                        <>🚀 啟動換手</>
                    )}
                </button>

                {handoverState.status === 'handover' && (
                    <button
                        className="cancel-button"
                        onClick={onCancelHandover}
                    >
                        ❌ 取消換手
                    </button>
                )}
            </div>

            {/* 換手狀態進度 */}
            {handoverState.status !== 'idle' && (
                <div className="handover-progress">
                    <div className="progress-header">
                        <span>換手進度</span>
                        <span className="confidence-score">
                            信心度:{' '}
                            {(handoverState.confidence * 100).toFixed(0)}%
                        </span>
                    </div>
                    <div className="progress-bar">
                        <div
                            className="progress-fill"
                            style={{
                                width:
                                    handoverState.status === 'complete'
                                        ? '100%'
                                        : handoverState.status === 'failed'
                                        ? '100%'
                                        : handoverState.status === 'handover'
                                        ? '60%'
                                        : '30%',
                            }}
                        ></div>
                    </div>
                </div>
            )}

            {/* 確認對話框 */}
            {showConfirmDialog && (
                <div className="confirm-dialog-overlay">
                    <div className="confirm-dialog">
                        <div className="dialog-header">
                            <h4>⚠️ 確認換手操作</h4>
                        </div>
                        <div className="dialog-content">
                            <p>確定要將連接從</p>
                            <div className="dialog-satellite from">
                                {currentConnection?.satelliteName || '未知'}
                            </div>
                            <p>換手到</p>
                            <div className="dialog-satellite to">
                                {availableSatellites.find(
                                    (s) => s.norad_id === selectedSatelliteId
                                )?.name || '未知'}
                            </div>
                            <p>嗎？</p>
                        </div>
                        <div className="dialog-buttons">
                            <button
                                className="confirm-btn"
                                onClick={handleConfirmHandover}
                            >
                                ✅ 確認
                            </button>
                            <button
                                className="cancel-btn"
                                onClick={handleCancelConfirm}
                            >
                                ❌ 取消
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default HandoverControlPanel
