/**
 * 新版 RL 監控模態框組件
 * 使用 @tr.md 開發的新 RL 監控系統
 */

import React from 'react'
import RLMonitoringPanel from '../rl-monitoring/RLMonitoringPanel'
import '../rl-monitoring/RLMonitoringPanel.scss'

interface RLMonitoringModalNewProps {
    isOpen: boolean
    onClose: () => void
}

const RLMonitoringModalNew: React.FC<RLMonitoringModalNewProps> = ({
    isOpen,
    onClose,
}) => {
    if (!isOpen) return null

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content rl-monitoring-modal-new"
                onClick={(e) => e.stopPropagation()}
                style={{
                    width: '95vw',
                    height: 'auto',
                    background: 'transparent',
                    border: 'none',
                    borderRadius: '12px',
                    overflow: 'hidden',
                }}
            >
                {/* 模態框頭部 */}
                <div
                    style={{
                        position: 'absolute',
                        top: '10px',
                        right: '15px',
                        zIndex: 10,
                    }}
                >
                    <button
                        className="modal-close-btn"
                        onClick={onClose}
                        style={{
                            background: 'rgba(255, 107, 107, 0.2)',
                            border: '1px solid #ff6b6b',
                            borderRadius: '50%',
                            width: '40px',
                            height: '40px',
                            color: '#ff6b6b',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '20px',
                            transition: 'all 0.2s ease',
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.background =
                                'rgba(255, 107, 107, 0.3)'
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.background =
                                'rgba(255, 107, 107, 0.2)'
                        }}
                        aria-label="關閉 RL 監控"
                    >
                        ✕
                    </button>
                </div>

                {/* 使用新的 RL 監控面板 */}
                <RLMonitoringPanel
                    mode="embedded"
                    height="100%"
                    refreshInterval={5000}
                    onDataUpdate={(data) => {
                        // 只在首次加載時記錄一次，然後只在狀態真正改變時記錄
                        const hasActiveTraining =
                            data.training.status === 'running' ||
                            data.training.algorithms.some(
                                (alg) => alg.training_active === true
                            ) ||
                            data.realtime.metrics.active_algorithms.length > 0

                        // 只在有活動訓練時記錄，而不是每次數據更新
                        if (hasActiveTraining) {
                            console.log(
                                '📊 RL 監控數據更新 (有活動訓練):',
                                data
                            )
                        }
                    }}
                    onError={(error) => {
                        console.error('❌ RL 監控錯誤:', error)
                    }}
                />
            </div>
        </div>
    )
}

export default RLMonitoringModalNew
