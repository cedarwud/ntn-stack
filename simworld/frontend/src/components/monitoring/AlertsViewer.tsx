/**
 * 系統告警查看器組件
 * 階段8：整合 AlertManager 告警顯示
 */

import React, { useState, useEffect, useCallback } from 'react'
import prometheusApiService, { AlertManagerAlert } from '../../services/prometheusApi'
import './AlertsViewer.scss'

interface AlertsViewerProps {
    className?: string
    autoRefresh?: boolean
    refreshInterval?: number
}

const AlertsViewer: React.FC<AlertsViewerProps> = ({
    className = '',
    autoRefresh = true,
    refreshInterval = 5000
}) => {
    const [alerts, setAlerts] = useState<AlertManagerAlert[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
    const [isAlertManagerAvailable, setIsAlertManagerAvailable] = useState(false)

    // 獲取告警數據
    const fetchAlerts = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            // 檢查 AlertManager 健康狀態
            const isHealthy = await prometheusApiService.checkAlertManagerHealth()
            setIsAlertManagerAvailable(isHealthy)

            if (!isHealthy) {
                setAlerts([])
                setError('AlertManager 服務不可用')
                return
            }

            // 獲取告警列表
            const alertsResult = await prometheusApiService.getAlerts()
            
            if (alertsResult.status === 'success') {
                setAlerts(alertsResult.data)
                setLastUpdate(new Date())
            } else {
                setError('獲取告警數據失敗')
            }
        } catch (err) {
            console.error('獲取告警失敗:', err)
            setError(err instanceof Error ? err.message : '未知錯誤')
            setIsAlertManagerAvailable(false)
        } finally {
            setLoading(false)
        }
    }, [])

    // 自動刷新邏輯
    useEffect(() => {
        fetchAlerts()

        if (autoRefresh && refreshInterval > 0) {
            const interval = setInterval(fetchAlerts, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [fetchAlerts, autoRefresh, refreshInterval])

    // 告警狀態統計
    const alertStats = {
        total: alerts.length,
        active: alerts.filter(alert => alert.status.state === 'active').length,
        suppressed: alerts.filter(alert => alert.status.state === 'suppressed').length,
        critical: alerts.filter(alert => alert.labels.severity === 'critical').length,
        warning: alerts.filter(alert => alert.labels.severity === 'warning').length
    }

    // 獲取告警狀態樣式
    const getAlertStatusClass = (alert: AlertManagerAlert): string => {
        if (alert.status.state === 'suppressed') return 'suppressed'
        if (alert.labels.severity === 'critical') return 'critical'
        if (alert.labels.severity === 'warning') return 'warning'
        return 'info'
    }

    // 格式化時間
    const formatTime = (timeStr: string): string => {
        return new Date(timeStr).toLocaleString('zh-TW', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        })
    }

    // 獲取告警圖標
    const getAlertIcon = (alert: AlertManagerAlert): string => {
        if (alert.status.state === 'suppressed') return '🔇'
        if (alert.labels.severity === 'critical') return '🚨'
        if (alert.labels.severity === 'warning') return '⚠️'
        return 'ℹ️'
    }

    return (
        <div className={`alerts-viewer ${className}`}>
            {/* 告警狀態標頭 */}
            <div className="alerts-header">
                <div className="alerts-title">
                    <h3>🚨 系統告警 (階段8)</h3>
                    <div className="status-indicator">
                        <span className={`connection-status ${isAlertManagerAvailable ? 'online' : 'offline'}`}>
                            {isAlertManagerAvailable ? '🟢 AlertManager 在線' : '🔴 AlertManager 離線'}
                        </span>
                        {lastUpdate && (
                            <span className="last-update">
                                最後更新: {lastUpdate.toLocaleTimeString('zh-TW')}
                            </span>
                        )}
                    </div>
                </div>

                {/* 告警統計 */}
                <div className="alerts-stats">
                    <div className="stat-item total">
                        <span className="stat-value">{alertStats.total}</span>
                        <span className="stat-label">總計</span>
                    </div>
                    <div className="stat-item active">
                        <span className="stat-value">{alertStats.active}</span>
                        <span className="stat-label">活躍</span>
                    </div>
                    <div className="stat-item critical">
                        <span className="stat-value">{alertStats.critical}</span>
                        <span className="stat-label">緊急</span>
                    </div>
                    <div className="stat-item warning">
                        <span className="stat-value">{alertStats.warning}</span>
                        <span className="stat-label">警告</span>
                    </div>
                </div>

                {/* 刷新按鈕 */}
                <button 
                    className="refresh-btn"
                    onClick={fetchAlerts}
                    disabled={loading}
                >
                    {loading ? '⏳' : '🔄'} 刷新
                </button>
            </div>

            {/* 告警內容 */}
            <div className="alerts-content">
                {loading && alerts.length === 0 && (
                    <div className="loading-state">
                        <div className="loading-spinner">⏳</div>
                        <span>載入告警數據中...</span>
                    </div>
                )}

                {error && (
                    <div className="error-state">
                        <div className="error-icon">❌</div>
                        <div className="error-message">
                            <strong>告警載入失敗</strong>
                            <p>{error}</p>
                        </div>
                    </div>
                )}

                {!loading && !error && alerts.length === 0 && (
                    <div className="empty-state">
                        <div className="empty-icon">✅</div>
                        <div className="empty-message">
                            <strong>沒有活躍告警</strong>
                            <p>系統運行正常，無告警訊息</p>
                        </div>
                    </div>
                )}

                {alerts.length > 0 && (
                    <div className="alerts-list">
                        {alerts.map((alert, index) => (
                            <div 
                                key={`${alert.fingerprint}-${index}`}
                                className={`alert-item ${getAlertStatusClass(alert)}`}
                            >
                                <div className="alert-header">
                                    <div className="alert-title">
                                        <span className="alert-icon">{getAlertIcon(alert)}</span>
                                        <span className="alert-name">{alert.labels.alertname || '未知告警'}</span>
                                        <span className="alert-severity">{alert.labels.severity || 'info'}</span>
                                    </div>
                                    <div className="alert-status">
                                        <span className={`status-badge ${alert.status.state}`}>
                                            {alert.status.state}
                                        </span>
                                    </div>
                                </div>

                                <div className="alert-details">
                                    {alert.annotations.summary && (
                                        <div className="alert-summary">
                                            <strong>摘要:</strong> {alert.annotations.summary}
                                        </div>
                                    )}
                                    
                                    {alert.annotations.description && (
                                        <div className="alert-description">
                                            <strong>描述:</strong> {alert.annotations.description}
                                        </div>
                                    )}

                                    {alert.annotations.action_required && (
                                        <div className="alert-action">
                                            <strong>建議行動:</strong> {alert.annotations.action_required}
                                        </div>
                                    )}
                                </div>

                                <div className="alert-metadata">
                                    <div className="alert-labels">
                                        {Object.entries(alert.labels)
                                            .filter(([key]) => !['alertname', 'severity'].includes(key))
                                            .slice(0, 3) // 只顯示前3個標籤，避免過於雜亂
                                            .map(([key, value]) => (
                                                <span key={key} className="label-tag">
                                                    {key}: {value}
                                                </span>
                                            ))
                                        }
                                    </div>
                                    
                                    <div className="alert-timing">
                                        <span className="start-time">
                                            開始: {formatTime(alert.startsAt)}
                                        </span>
                                        {alert.endsAt !== '0001-01-01T00:00:00Z' && (
                                            <span className="end-time">
                                                結束: {formatTime(alert.endsAt)}
                                            </span>
                                        )}
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

export default AlertsViewer