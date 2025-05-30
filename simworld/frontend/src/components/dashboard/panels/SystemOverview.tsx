import React from 'react'
import './PanelCommon.scss'

interface SystemOverviewProps {
    data: any
    loading: boolean
    error: string | null
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
    currentScene: string
}

const SystemOverview: React.FC<SystemOverviewProps> = ({
    data,
    loading,
    error,
    style,
    isFullscreen,
    onFullscreen,
    currentScene,
}) => {
    const systemStats = data?.system_stats || {}
    const services = data?.services || {}

    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'healthy':
            case 'running':
            case 'active':
                return '#4CAF50'
            case 'warning':
            case 'degraded':
                return '#FF9800'
            case 'error':
            case 'down':
            case 'inactive':
                return '#F44336'
            default:
                return '#9E9E9E'
        }
    }

    return (
        <div
            className={`panel system-overview ${
                isFullscreen ? 'fullscreen' : ''
            }`}
            style={style}
        >
            <div className="panel-header">
                <h3>系統總覽</h3>
                <div className="panel-controls">
                    <span className="scene-indicator">
                        場景: {currentScene}
                    </span>
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                {loading && (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>載入系統狀態中...</p>
                    </div>
                )}

                {error && (
                    <div className="error-state">
                        <p>❌ 系統狀態載入失敗</p>
                        <small>{error}</small>
                    </div>
                )}

                {!loading && !error && (
                    <div className="overview-grid">
                        {/* 系統指標 */}
                        <div className="metrics-section">
                            <h4>系統指標</h4>
                            <div className="metrics-grid">
                                <div className="metric-card">
                                    <span className="metric-label">
                                        CPU 使用率
                                    </span>
                                    <span className="metric-value">
                                        {systemStats.cpu_usage_percent || 0}%
                                    </span>
                                </div>
                                <div className="metric-card">
                                    <span className="metric-label">
                                        記憶體使用
                                    </span>
                                    <span className="metric-value">
                                        {systemStats.memory_usage_mb || 0} MB
                                    </span>
                                </div>
                                <div className="metric-card">
                                    <span className="metric-label">
                                        網路連接
                                    </span>
                                    <span className="metric-value">
                                        {systemStats.active_connections || 0}
                                    </span>
                                </div>
                                <div className="metric-card">
                                    <span className="metric-label">
                                        請求速率
                                    </span>
                                    <span className="metric-value">
                                        {systemStats.request_rate_per_second ||
                                            0}
                                        /s
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* 服務狀態 */}
                        <div className="services-section">
                            <h4>服務狀態</h4>
                            <div className="services-list">
                                {Object.entries(services).length > 0 ? (
                                    Object.entries(services).map(
                                        ([serviceName, serviceData]: [
                                            string,
                                            any
                                        ]) => (
                                            <div
                                                key={serviceName}
                                                className="service-item"
                                            >
                                                <div
                                                    className="service-status"
                                                    style={{
                                                        backgroundColor:
                                                            getStatusColor(
                                                                serviceData.status
                                                            ),
                                                    }}
                                                ></div>
                                                <span className="service-name">
                                                    {serviceName}
                                                </span>
                                                <span className="service-info">
                                                    {serviceData.status ||
                                                        'Unknown'}
                                                </span>
                                            </div>
                                        )
                                    )
                                ) : (
                                    <div className="no-services">
                                        <p>沒有可用的服務狀態</p>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* 快速狀態 */}
                        <div className="quick-status">
                            <div className="status-indicator">
                                <div className="status-light healthy"></div>
                                <span>系統正常運行</span>
                            </div>
                            <div className="uptime">
                                <span>
                                    運行時間: {systemStats.uptime || 'N/A'}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default SystemOverview
