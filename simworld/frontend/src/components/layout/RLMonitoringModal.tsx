/**
 * 獨立的 RL 監控模態框組件
 * 從 FullChartAnalysisDashboard 中提取出來，作為 navbar 的獨立功能
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Line } from 'react-chartjs-2'
import GymnasiumRLMonitor from '../dashboard/GymnasiumRLMonitor'
import { createRLChartOptions } from '../../config/dashboardChartOptions'
import { useRLMonitoring } from '../views/dashboards/ChartAnalysisDashboard/hooks/useRLMonitoring'
import { apiClient } from '../../services/api-client'
import '../views/dashboards/ChartAnalysisDashboard/ChartAnalysisDashboard.scss'

interface RLMonitoringModalProps {
    isOpen: boolean
    onClose: () => void
}

const RLMonitoringModal: React.FC<RLMonitoringModalProps> = ({
    isOpen,
    onClose,
}) => {
    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div 
                className="modal-content chart-analysis-modal rl-monitoring-standalone"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div className="modal-title-section">
                        <h1 className="modal-title">
                            🧠 強化學習 (RL) 監控中心
                        </h1>
                        <p className="modal-subtitle">
                            實時監控 DQN、PPO、SAC 演算法訓練狀態與性能指標
                        </p>
                    </div>
                    <button 
                        className="modal-close-btn"
                        onClick={onClose}
                        aria-label="關閉 RL 監控"
                    >
                        ✕
                    </button>
                </div>

                <div className="modal-body">
                    <div className="service-unavailable-container" style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        minHeight: '400px',
                        textAlign: 'center',
                        backgroundColor: '#f8f9fa',
                        borderRadius: '8px',
                        border: '2px dashed #dee2e6',
                        margin: '20px',
                        padding: '40px'
                    }}>
                        <div style={{ fontSize: '4rem', marginBottom: '20px' }}>🔧</div>
                        <h2 style={{ color: '#6c757d', marginBottom: '16px', fontSize: '1.5rem' }}>
                            RL 監控功能暫時不可用
                        </h2>
                        <p style={{ color: '#6c757d', marginBottom: '24px', fontSize: '1.1rem', lineHeight: '1.6' }}>
                            強化學習監控系統依賴 PostgreSQL 數據庫，目前系統正在進行數據庫遷移<br />
                            <strong>（PostgreSQL → MongoDB）</strong>
                        </p>
                        <div style={{ 
                            backgroundColor: '#e3f2fd', 
                            padding: '20px', 
                            borderRadius: '8px', 
                            border: '1px solid #90caf9',
                            marginBottom: '20px',
                            maxWidth: '600px'
                        }}>
                            <div style={{ color: '#1976d2', fontWeight: 'bold', marginBottom: '8px' }}>
                                📋 預計恢復時間表：
                            </div>
                            <div style={{ color: '#1976d2', textAlign: 'left' }}>
                                • <strong>Phase 3</strong>：RL 系統 PostgreSQL 遷移 (預計 2-3 週)<br />
                                • <strong>Phase 4</strong>：完整功能測試與驗證 (預計 1 週)<br />
                                • <strong>總計</strong>：約 3-4 週後恢復完整 RL 監控功能
                            </div>
                        </div>
                        <p style={{ color: '#6c757d', fontSize: '0.95rem' }}>
                            感謝您的耐心等待，我們正在努力提供更穩定的 RL 訓練體驗 🚀
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RLMonitoringModal;
