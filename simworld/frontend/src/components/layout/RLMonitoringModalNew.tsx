/**
 * 新版 RL 監控模態框組件
 * 使用 @tr.md 開發的新 RL 監控系統
 */

import React, { useRef } from 'react'
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
    const panelRef = useRef<any>(null)

    if (!isOpen) return null

    const handleRefresh = () => {
        // TODO: 實現刷新功能，需要從 RLMonitoringPanel 暴露 refresh 方法
        console.log('Refresh data')
    }

    const handleExport = () => {
        // TODO: 實現導出功能，需要從 RLMonitoringPanel 暴露 export 方法
        console.log('Export data')
    }

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
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '10px' }}>
                        {/* 導出按鈕 */}
                        <button
                            className="control-btn control-btn--export"
                            onClick={handleExport}
                            title="導出數據"
                            style={{
                                background: 'rgba(255, 255, 255, 0.1)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: '6px',
                                color: 'white',
                                padding: '8px 12px',
                                cursor: 'pointer',
                                fontSize: '14px',
                                transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                                (e.target as HTMLButtonElement).style.background = 'rgba(255, 255, 255, 0.2)';
                                (e.target as HTMLButtonElement).style.borderColor = 'rgba(255, 255, 255, 0.4)';
                            }}
                            onMouseLeave={(e) => {
                                (e.target as HTMLButtonElement).style.background = 'rgba(255, 255, 255, 0.1)';
                                (e.target as HTMLButtonElement).style.borderColor = 'rgba(255, 255, 255, 0.2)';
                            }}
                        >
                            📥
                        </button>
                        
                        {/* 刷新按鈕 */}
                        <button
                            className="control-btn control-btn--refresh"
                            onClick={handleRefresh}
                            title="手動刷新數據"
                            style={{
                                background: 'rgba(255, 255, 255, 0.1)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: '6px',
                                color: 'white',
                                padding: '8px 12px',
                                cursor: 'pointer',
                                fontSize: '14px',
                                transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                                (e.target as HTMLButtonElement).style.background = 'rgba(255, 255, 255, 0.2)';
                                (e.target as HTMLButtonElement).style.borderColor = 'rgba(255, 255, 255, 0.4)';
                            }}
                            onMouseLeave={(e) => {
                                (e.target as HTMLButtonElement).style.background = 'rgba(255, 255, 255, 0.1)';
                                (e.target as HTMLButtonElement).style.borderColor = 'rgba(255, 255, 255, 0.2)';
                            }}
                        >
                            🔄
                        </button>
                        
                        {/* 關閉按鈕 */}
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
