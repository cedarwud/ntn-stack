/**
 * 主要的 RL 監控面板組件
 * 根據 @tr.md 規劃實現的完整監控系統
 */

import React, { useState, useEffect, useMemo } from 'react'
import { RLMonitoringPanelProps } from './types/rl-monitoring.types'
import { useRLMonitoring } from './hooks/useRLMonitoring'

// 導入重新設計的組件
import TrainingControlCenterSection from './sections/TrainingControlCenterSection'
import PerformanceAnalysisSection from './sections/PerformanceAnalysisSection'
import EnvironmentVisualizationSection from './sections/EnvironmentVisualizationSection'
import ParameterTuningSection from './sections/ParameterTuningSection'
import RealTimeMetricsSection from './sections/RealTimeMetricsSection'
import ResearchDataSection from './sections/ResearchDataSection'

// 樣式
import './RLMonitoringPanel.scss'

const RLMonitoringPanel: React.FC<RLMonitoringPanelProps> = ({
    mode = 'standalone',
    height = '100vh',
    refreshInterval = 2000,
    onDataUpdate,
    onError,
}) => {
    // 使用增強版 RL 監控 Hook
    const { isLoading, error, lastUpdated, data, refresh, events, utils } =
        useRLMonitoring({
            refreshInterval,
            enabled: true,
            autoStart: false,
        })

    // 內部狀態
    const [activeTab, setActiveTab] = useState<string>('control')
    const [isCollapsed, setIsCollapsed] = useState(false)

    // 錯誤處理
    useEffect(() => {
        if (error && onError) {
            onError(error)
        }
    }, [error, onError])

    // 數據更新回調
    useEffect(() => {
        if (data && onDataUpdate) {
            onDataUpdate(data)
        }
    }, [data, onDataUpdate])

    // 錯誤事件監聽
    useEffect(() => {
        const handleError = (errorEvent: { message: string }) => {
            console.error('RL Monitoring Error:', errorEvent)
            if (onError) {
                onError(new Error(errorEvent.message))
            }
        }

        events.onError.on(handleError)
        return () => events.onError.off(handleError)
    }, [events, onError])

    // 重新設計的 6 個分頁配置
    const tabs = useMemo(
        () => [
            {
                id: 'control',
                label: '🎯 訓練控制中心',
                icon: '🎯',
                description: '統一的訓練控制界面和實時進度監控',
            },
            {
                id: 'performance',
                label: '📊 性能分析',
                icon: '📈',
                description: '深度訓練結果分析和算法比較',
            },
            {
                id: 'environment',
                label: '🌐 環境可視化',
                icon: '🌐',
                description: '3D LEO 衛星星座和決策過程動畫',
            },
            {
                id: 'parameters',
                label: '⚙️ 參數調優',
                icon: '⚙️',
                description: '算法超參數和環境參數調整',
            },
            {
                id: 'realtime',
                label: '📈 實時監控',
                icon: '🔴',
                description: 'WebSocket 實時數據流和系統健康監控',
            },
            {
                id: 'research',
                label: '🔬 研究數據',
                icon: '📚',
                description: '實驗數據管理和論文數據匯出',
            },
        ],
        []
    )

    const containerClasses = [
        'rl-monitoring-panel',
        `rl-monitoring-panel--${mode}`,
        isCollapsed ? 'rl-monitoring-panel--collapsed' : '',
        isLoading ? 'rl-monitoring-panel--loading' : '',
    ]
        .filter(Boolean)
        .join(' ')

    return (
        <div className={containerClasses} style={{ height }}>
            {/* 頭部區域 - 只在 standalone 模式下顯示 */}
            {mode === 'standalone' && (
                <div className="rl-monitoring-panel__header">
                    <div className="rl-monitoring-panel__title">
                        <h2>
                            <span className="icon">🤖</span>
                            RL 訓練監控系統
                        </h2>
                        <div className="rl-monitoring-panel__subtitle">
                            基於 {data.training?.algorithms?.length || 0}{' '}
                            個算法的實時監控
                            {lastUpdated && (
                                <span className="last-updated">
                                    最後更新: {lastUpdated.toLocaleTimeString()}
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="rl-monitoring-panel__controls">
                        {/* 全局控制按鈕 */}
                        <button
                            className="control-btn control-btn--refresh"
                            onClick={refresh}
                            disabled={isLoading}
                            title="手動刷新數據"
                        >
                            {isLoading ? '🔄' : '🔄'}
                        </button>

                        <button
                            className="control-btn control-btn--export"
                            onClick={() => utils.exportData('json')}
                            title="導出數據"
                        >
                            📥
                        </button>

                        {mode === 'standalone' && (
                            <button
                                className="control-btn control-btn--collapse"
                                onClick={() => setIsCollapsed(!isCollapsed)}
                                title={isCollapsed ? '展開面板' : '收起面板'}
                            >
                                {isCollapsed ? '📖' : '📕'}
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* 狀態指示器 */}
            {(isLoading || error) && (
                <div className="rl-monitoring-panel__status">
                    {isLoading && (
                        <div className="status-indicator status-indicator--loading">
                            <span className="spinner">⚡</span>
                            正在獲取數據...
                        </div>
                    )}
                    {error && (
                        <div className="status-indicator status-indicator--error">
                            <span className="icon">❌</span>
                            錯誤: {error.message}
                            <button className="retry-btn" onClick={refresh}>
                                重試
                            </button>
                        </div>
                    )}
                </div>
            )}

            {!isCollapsed && (
                <>
                    {/* 標籤頁導航 */}
                    <div className="rl-monitoring-panel__tabs">
                        <div className="tabs-nav">
                            {tabs.map((tab) => (
                                <button
                                    key={tab.id}
                                    className={`tab-btn ${
                                        activeTab === tab.id
                                            ? 'tab-btn--active'
                                            : ''
                                    }`}
                                    onClick={() => setActiveTab(tab.id)}
                                    title={tab.description}
                                >
                                    <span className="tab-icon">{tab.icon}</span>
                                    <span className="tab-label">
                                        {tab.label}
                                    </span>
                                    {/* 狀態指示 */}
                                    {tab.id === 'training' && (
                                        <span className="tab-status">
                                            {(data.realtime?.metrics
                                                ?.active_algorithms?.length ||
                                                0) > 0 && (
                                                <span className="status-dot status-dot--active"></span>
                                            )}
                                        </span>
                                    )}
                                </button>
                            ))}
                        </div>

                        {/* 快速狀態顯示 */}
                        <div className="quick-status">
                            <div className="quick-status__item">
                                <span className="label">活躍算法:</span>
                                <span className="value">
                                    {data.realtime?.metrics?.active_algorithms
                                        ?.length || 0}
                                </span>
                            </div>
                            <div className="quick-status__item">
                                <span className="label">系統狀態:</span>
                                <span
                                    className={`value status-${
                                        data.realtime?.metrics?.system_status ||
                                        'unknown'
                                    }`}
                                >
                                    {data.realtime?.metrics?.system_status ===
                                    'healthy'
                                        ? '🟢'
                                        : '🟡'}
                                    {data.realtime?.metrics?.system_status ||
                                        'unknown'}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 內容區域 */}
                    <div className="rl-monitoring-panel__content">
                        {activeTab === 'control' && (
                            <TrainingControlCenterSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'performance' && (
                            <PerformanceAnalysisSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'environment' && (
                            <EnvironmentVisualizationSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'parameters' && (
                            <ParameterTuningSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'realtime' && (
                            <RealTimeMetricsSection
                                data={data.realtime}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'research' && (
                            <ResearchDataSection
                                data={data.research}
                                onRefresh={refresh}
                            />
                        )}
                    </div>
                </>
            )}

            {/* 底部信息 */}
            <div className="rl-monitoring-panel__footer">
                <div className="footer-info">
                    <span>@tr.md v1.0</span>
                    <span>•</span>
                    <span>
                        API 狀態:{' '}
                        {data.realtime?.status?.overall_health === 'healthy'
                            ? '🟢 正常'
                            : '🔴 異常'}
                    </span>
                    <span>•</span>
                    <span>刷新間隔: {refreshInterval / 1000}秒</span>
                </div>
            </div>
        </div>
    )
}

export default RLMonitoringPanel
