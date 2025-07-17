/**
 * 主要的 RL 監控面板組件
 * 根據 @tr.md 重新設計：從6分頁整合為4分頁，專注LEO衛星切換研究
 * 新架構：實驗控制台 → 實時監控 → 實驗結果 → 算法對比
 */

import React, { useState, useEffect, useMemo } from 'react'
import { RLMonitoringPanelProps } from './types/rl-monitoring.types'
import { useRLMonitoring } from './hooks/useRLMonitoring'

// 導入重新設計的組件 (根據 @tr.md 新架構)
import ExperimentControlSection from './sections/ExperimentControlSection'
import RealtimeMonitoringSection from './sections/RealtimeMonitoringSection'
import ExperimentResultsSection from './sections/ExperimentResultsSection'
import AlgorithmComparisonSection from './sections/AlgorithmComparisonSection'

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
    const [activeTab, setActiveTab] = useState<string>('experiment')
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

    // 重新設計的 4 個分頁配置 (根據 @tr.md 新架構)
    const tabs = useMemo(
        () => [
            {
                id: 'experiment',
                label: '🚀 實驗控制台',
                icon: '🚀',
                description: '統一參數管理和實驗執行 (整合原訓練控制中心+參數調優)',
            },
            {
                id: 'monitoring',
                label: '📊 實時監控',
                icon: '📊',
                description: 'LEO衛星切換性能實時追蹤和決策過程可視化',
            },
            {
                id: 'results',
                label: '📈 實驗結果',
                icon: '📈',
                description: '深度分析和論文圖表生成 (整合原訓練分析+收斂分析)',
            },
            {
                id: 'comparison',
                label: '⚖️ 算法對比',
                icon: '⚖️',
                description: '傳統算法vs RL算法基準測試和統計顯著性分析',
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
                                    {tab.id === 'experiment' && (
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

                    {/* 內容區域 - 重新設計的4個分頁 */}
                    <div className="rl-monitoring-panel__content">
                        {activeTab === 'experiment' && (
                            <ExperimentControlSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'monitoring' && (
                            <RealtimeMonitoringSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'results' && (
                            <ExperimentResultsSection
                                data={data}
                                onRefresh={refresh}
                            />
                        )}

                        {activeTab === 'comparison' && (
                            <AlgorithmComparisonSection
                                data={data}
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
