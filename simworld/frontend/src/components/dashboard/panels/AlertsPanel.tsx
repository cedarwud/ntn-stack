import React from 'react'
import './PanelCommon.scss'

interface Alert {
    id: string
    level: 'info' | 'warning' | 'error'
    message: string
    timestamp: Date
}

interface AlertsPanelProps {
    alerts: Alert[]
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
    currentScene: string
}

const AlertsPanel: React.FC<AlertsPanelProps> = ({
    alerts,
    style,
    isFullscreen,
    onFullscreen,
    currentScene,
}) => {
    const getAlertIcon = (level: string) => {
        switch (level) {
            case 'error':
                return '🚨'
            case 'warning':
                return '⚠️'
            case 'info':
                return 'ℹ️'
            default:
                return 'ℹ️'
        }
    }

    const getAlertColor = (level: string) => {
        switch (level) {
            case 'error':
                return '#F44336'
            case 'warning':
                return '#FF9800'
            case 'info':
                return '#2196F3'
            default:
                return '#9E9E9E'
        }
    }

    return (
        <div
            className={`panel alerts-panel ${isFullscreen ? 'fullscreen' : ''}`}
            style={style}
        >
            <div className="panel-header">
                <h3>系統告警</h3>
                <div className="panel-controls">
                    <span className="alert-count">{alerts.length} 個告警</span>
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                {alerts.length === 0 ? (
                    <div className="no-alerts">
                        <p>✅ 目前沒有告警</p>
                        <small>系統運行正常</small>
                    </div>
                ) : (
                    <div className="alerts-list">
                        {alerts.map((alert) => (
                            <div
                                key={alert.id}
                                className={`alert-item ${alert.level}`}
                                style={{
                                    borderLeftColor: getAlertColor(alert.level),
                                }}
                            >
                                <div className="alert-icon">
                                    {getAlertIcon(alert.level)}
                                </div>
                                <div className="alert-content">
                                    <div className="alert-message">
                                        {alert.message}
                                    </div>
                                    <div className="alert-timestamp">
                                        {alert.timestamp.toLocaleString()}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}

export default AlertsPanel
