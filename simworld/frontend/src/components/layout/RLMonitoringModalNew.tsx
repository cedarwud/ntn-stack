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
        <div className="modal-backdrop" onClick={onClose}>
            <div
                className="constellation-modal rl-monitoring-modal-new"
                onClick={(e) => e.stopPropagation()}
            >
                {/* 模態框頭部 */}
                <div className="modal-header">
                    <div style={{ flex: 1 }}></div>
                    <h3 style={{ margin: 0, color: 'white', textAlign: 'center' }}>
                        🤖 RL 訓練監控系統
                    </h3>
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                            onClick={onClose}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'white',
                                fontSize: '1.5rem',
                                cursor: 'pointer',
                                padding: '0 5px',
                                lineHeight: 1,
                                opacity: 0.7,
                                transition: 'opacity 0.3s',
                            }}
                            onMouseEnter={(e) =>
                                ((e.target as HTMLButtonElement).style.opacity = '1')
                            }
                            onMouseLeave={(e) =>
                                ((e.target as HTMLButtonElement).style.opacity = '0.7')
                            }
                        >
                            ×
                        </button>
                    </div>
                </div>

                {/* 模態框內容 */}
                <div className="modal-content">
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
        </div>
    )
}

export default RLMonitoringModalNew
