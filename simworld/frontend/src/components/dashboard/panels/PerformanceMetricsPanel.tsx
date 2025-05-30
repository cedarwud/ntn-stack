import React from 'react'
import './PanelCommon.scss'

interface PerformanceMetricsPanelProps {
    data: any
    loading: boolean
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
    currentScene: string
}

const PerformanceMetricsPanel: React.FC<PerformanceMetricsPanelProps> = ({
    data,
    loading,
    style,
    isFullscreen,
    onFullscreen,
    currentScene,
}) => {
    const metrics = data?.metrics || {}

    return (
        <div
            className={`panel performance-metrics ${
                isFullscreen ? 'fullscreen' : ''
            }`}
            style={style}
        >
            <div className="panel-header">
                <h3>性能指標</h3>
                <div className="panel-controls">
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                {loading && (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>載入性能指標中...</p>
                    </div>
                )}

                {!loading && (
                    <div className="performance-grid">
                        <div className="metric-card">
                            <span className="metric-label">系統吞吐量</span>
                            <span className="metric-value">
                                {metrics.throughput || 'N/A'} req/s
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">平均響應時間</span>
                            <span className="metric-value">
                                {metrics.response_time || 'N/A'} ms
                            </span>
                        </div>
                        <div className="metric-card">
                            <span className="metric-label">成功率</span>
                            <span className="metric-value">
                                {metrics.success_rate || 'N/A'}%
                            </span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default PerformanceMetricsPanel
