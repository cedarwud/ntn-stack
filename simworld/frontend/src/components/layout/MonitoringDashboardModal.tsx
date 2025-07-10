/**
 * 綜合監控儀表板模態框
 * 階段8：整合所有監控組件的統一界面
 */

import React, { useState } from 'react'
import { AlertsViewer, SystemHealthViewer } from '../monitoring'
import './MonitoringDashboardModal.scss'

interface MonitoringDashboardModalProps {
    isOpen: boolean
    onClose: () => void
}

type TabType = 'overview' | 'system' | 'alerts' | 'grafana'

const MonitoringDashboardModal: React.FC<MonitoringDashboardModalProps> = ({
    isOpen,
    onClose,
}) => {
    const [activeTab, setActiveTab] = useState<TabType>('overview')

    if (!isOpen) return null

    const tabs = [
        { id: 'overview' as TabType, label: '📊 總覽', icon: '📊' },
        { id: 'system' as TabType, label: '💻 系統健康', icon: '💻' },
        { id: 'alerts' as TabType, label: '🚨 告警', icon: '🚨' },
        { id: 'grafana' as TabType, label: '📈 Grafana', icon: '📈' }
    ]

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div 
                className="modal-content monitoring-dashboard-modal"
                onClick={(e) => e.stopPropagation()}
            >
                {/* 模態框標題 */}
                <div className="modal-header">
                    <div className="modal-title-section">
                        <h1 className="modal-title">
                            📊 NTN Stack 監控儀表板
                        </h1>
                        <p className="modal-subtitle">
                            階段8：全系統監控與告警管理中心
                        </p>
                    </div>
                    <button 
                        className="modal-close-btn"
                        onClick={onClose}
                        aria-label="關閉監控儀表板"
                    >
                        ✕
                    </button>
                </div>

                {/* 標籤導航 */}
                <div className="monitoring-tabs">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <span className="tab-icon">{tab.icon}</span>
                            <span className="tab-label">{tab.label}</span>
                        </button>
                    ))}
                </div>

                {/* 內容區域 */}
                <div className="modal-body">
                    <div className="monitoring-content">
                        {/* 總覽頁面 */}
                        {activeTab === 'overview' && (
                            <div className="overview-tab">
                                <div className="overview-grid">
                                    {/* 快速狀態卡片 */}
                                    <div className="quick-status-section">
                                        <h3>🚀 快速狀態</h3>
                                        <div className="status-cards">
                                            <div className="status-card services">
                                                <div className="card-header">
                                                    <span className="card-icon">🔧</span>
                                                    <span className="card-title">核心服務</span>
                                                </div>
                                                <div className="card-content">
                                                    <div className="metric-large">5/5</div>
                                                    <div className="metric-label">服務在線</div>
                                                </div>
                                            </div>

                                            <div className="status-card alerts">
                                                <div className="card-header">
                                                    <span className="card-icon">🚨</span>
                                                    <span className="card-title">活躍告警</span>
                                                </div>
                                                <div className="card-content">
                                                    <div className="metric-large">0</div>
                                                    <div className="metric-label">緊急告警</div>
                                                </div>
                                            </div>

                                            <div className="status-card performance">
                                                <div className="card-header">
                                                    <span className="card-icon">⚡</span>
                                                    <span className="card-title">系統性能</span>
                                                </div>
                                                <div className="card-content">
                                                    <div className="metric-large">良好</div>
                                                    <div className="metric-label">總體狀態</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* 嵌入式系統健康 */}
                                    <div className="embedded-health">
                                        <SystemHealthViewer 
                                            className="embedded"
                                            showCharts={false}
                                            autoRefresh={true}
                                        />
                                    </div>

                                    {/* 嵌入式告警預覽 */}
                                    <div className="embedded-alerts">
                                        <AlertsViewer 
                                            className="embedded preview"
                                            autoRefresh={true}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 系統健康頁面 */}
                        {activeTab === 'system' && (
                            <div className="system-tab">
                                <SystemHealthViewer 
                                    className="full-view"
                                    showCharts={true}
                                    autoRefresh={true}
                                    refreshInterval={2000}
                                />
                            </div>
                        )}

                        {/* 告警頁面 */}
                        {activeTab === 'alerts' && (
                            <div className="alerts-tab">
                                <AlertsViewer 
                                    className="full-view"
                                    autoRefresh={true}
                                    refreshInterval={3000}
                                />
                            </div>
                        )}

                        {/* Grafana 頁面 */}
                        {activeTab === 'grafana' && (
                            <div className="grafana-tab">
                                <div className="grafana-container">
                                    <div className="grafana-header">
                                        <h3>📈 Grafana 儀表板</h3>
                                        <p>專業監控可視化界面</p>
                                    </div>
                                    <div className="grafana-iframe-container">
                                        <iframe
                                            src="http://localhost:3000/d/ntn-overview/ntn-stack-overview?orgId=1&refresh=5s&theme=dark"
                                            title="Grafana 監控儀表板"
                                            className="grafana-iframe"
                                            frameBorder="0"
                                            allowFullScreen
                                        />
                                    </div>
                                    <div className="grafana-links">
                                        <a 
                                            href="http://localhost:3000" 
                                            target="_blank" 
                                            rel="noopener noreferrer"
                                            className="external-link"
                                        >
                                            🔗 在新視窗開啟 Grafana
                                        </a>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default MonitoringDashboardModal