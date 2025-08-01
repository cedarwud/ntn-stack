/**
 * 完整的圖表分析儀表板
 * 包含所有 8 個標籤分頁的完整功能
 */

import React, { useState } from 'react'
import { Line } from 'react-chartjs-2'
import OverviewTabContent from '../views/dashboards/ChartAnalysisDashboard/components/OverviewTabContent'
import IntegratedAnalysisTabContent from '../views/dashboards/ChartAnalysisDashboard/components/IntegratedAnalysisTabContent'
import EnhancedAlgorithmTabContent from '../views/dashboards/ChartAnalysisDashboard/components/EnhancedAlgorithmTabContent'
import EnhancedPerformanceTabContent from '../views/dashboards/ChartAnalysisDashboard/components/EnhancedPerformanceTabContent'
import MonitoringTabContent from '../views/dashboards/ChartAnalysisDashboard/components/MonitoringTabContent'
import ParametersTabContent from '../views/dashboards/ChartAnalysisDashboard/components/ParametersTabContent'
import EnhancedSystemTabContent from '../views/dashboards/ChartAnalysisDashboard/components/EnhancedSystemTabContent'
import StrategyTabContent from '../views/dashboards/ChartAnalysisDashboard/components/StrategyTabContent'
import { createInteractiveChartOptions } from '../../config/dashboardChartOptions'
import '../views/dashboards/ChartAnalysisDashboard/ChartAnalysisDashboard.scss'

interface FullChartAnalysisDashboardProps {
    isOpen: boolean
    onClose: () => void
}

type TabName =
    | 'overview'
    | 'performance'
    | 'system'
    | 'algorithms'
    | 'analysis'
    | 'monitoring'
    | 'strategy'
    | 'parameters'

// 模擬數據已移動到 utils/mockDataGenerator.ts

// 圖表選項已移動到 config/dashboardChartOptions.ts

const FullChartAnalysisDashboard: React.FC<FullChartAnalysisDashboardProps> = ({
    isOpen,
    onClose,
}) => {
    const [activeTab, setActiveTab] = useState<TabName>('overview')

    if (!isOpen) return null

    // 模擬數據已移動到 utils/mockDataGenerator.ts
    // 如需使用請: import { createMockData } from '../../utils/mockDataGenerator'
    // 然後: const mockData = createMockData()

    const tabs = [
        { key: 'overview', label: '核心圖表', icon: '📊' },
        { key: 'performance', label: '性能監控', icon: '⚡' },
        { key: 'system', label: '系統架構', icon: '🖥️' },
        { key: 'algorithms', label: '算法分析', icon: '🔬' },
        { key: 'analysis', label: '深度分析', icon: '📈' },
        { key: 'monitoring', label: '衛星監控', icon: '🔍' },
        { key: 'strategy', label: '即時策略效果', icon: '🎯' },
        { key: 'parameters', label: '軌道參數', icon: '📋' },
    ]

    // 渲染標籤頁內容
    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return (
                    <OverviewTabContent
                        createInteractiveChartOptions={
                            createInteractiveChartOptions
                        }
                    />
                )
            case 'performance':
                return <EnhancedPerformanceTabContent />
            case 'system':
                return <EnhancedSystemTabContent />
            case 'algorithms':
                return <EnhancedAlgorithmTabContent />
            case 'analysis':
                return <IntegratedAnalysisTabContent />
            case 'monitoring':
                return <MonitoringTabContent />
            case 'strategy':
                return <StrategyTabContent />
            case 'parameters':
                return <ParametersTabContent />
            default:
                return (
                    <OverviewTabContent
                        createInteractiveChartOptions={
                            createInteractiveChartOptions
                        }
                    />
                )
        }
    }

    return (
        <div className="chart-analysis-overlay">
            <div className="chart-analysis-modal">
                <div className="modal-header">
                    <h2>🚀 NTN 衛星網路換手分析儀表板</h2>
                    <button className="close-btn" onClick={onClose}>
                        ✕
                    </button>
                </div>

                {/* 標籤頁導航 */}
                <div className="tabs-container">
                    <div className="tabs">
                        {tabs.map((tab) => (
                            <button
                                key={tab.key}
                                className={`tab-button ${
                                    activeTab === tab.key ? 'active' : ''
                                }`}
                                onClick={() => setActiveTab(tab.key as TabName)}
                            >
                                <span className="tab-icon">{tab.icon}</span>
                                <span className="tab-label">{tab.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="modal-content">
                    <style>{`
            /* 弹窗样式 - 参考完整图表弹窗 */
            .chart-analysis-overlay {
              position: fixed;
              top: 0;
              left: 0;
              width: 100vw;
              height: 100vh;
              background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(20, 30, 48, 0.95));
              z-index: 10000;
              display: flex;
              align-items: center;
              justify-content: center;
              backdrop-filter: blur(10px);
            }
            
            .chart-analysis-modal {
              width: 95vw;
              height: 95vh;
              background: linear-gradient(145deg, #1a1a2e, #16213e);
              border-radius: 20px;
              box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
              display: flex;
              flex-direction: column;
              overflow: hidden;
              border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .modal-content {
              flex: 1;
              padding: 20px;
              overflow-y: auto;
              background: linear-gradient(180deg, #1a1a2e, #16213e);
            }
            
            .modal-content::-webkit-scrollbar {
              width: 8px;
            }
            
            .modal-content::-webkit-scrollbar-track {
              background: rgba(255, 255, 255, 0.1);
              border-radius: 4px;
            }
            
            .modal-content::-webkit-scrollbar-thumb {
              background: linear-gradient(180deg, #667eea, #764ba2);
              border-radius: 4px;
            }
            
            .full-chart-analysis-dashboard .charts-grid {
              display: grid !important;
              gap: 20px !important;
              width: 100% !important;
              grid-template-columns: 1fr 1fr !important;
              grid-template-rows: auto auto !important;
              margin: 0 !important;
              padding: 0 !important;
            }
            
            /* 前两个图表填满宽度 */
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(1) {
              grid-column: 1 !important;
              grid-row: 1 !important;
              width: 100% !important;
              max-width: none !important;
              min-width: 0 !important;
            }
            
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(2) {
              grid-column: 2 !important;
              grid-row: 1 !important;
              width: 100% !important;
              max-width: none !important;
              min-width: 0 !important;
            }
            
            /* 第三个图表占第1列第2行 */
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(3) {
              grid-column: 1 !important;
              grid-row: 2 !important;
              width: 100% !important;
              max-width: none !important;
              min-width: 0 !important;
            }
            
            /* 第四个图表占第2列第2行 */
            .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(4) {
              grid-column: 2 !important;
              grid-row: 2 !important;
              width: 100% !important;
              max-width: none !important;
              min-width: 0 !important;
            }
            
            /* 响应式：小屏幕时改为单列布局 */
            @media (max-width: 1200px) {
              .full-chart-analysis-dashboard .charts-grid {
                grid-template-columns: 1fr !important;
                grid-template-rows: auto auto auto !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(1) {
                grid-column: 1 !important;
                grid-row: 1 !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(2) {
                grid-column: 1 !important;
                grid-row: 2 !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(3) {
                grid-column: 1 !important;
                grid-row: 3 !important;
              }
            }
            
            .full-chart-analysis-dashboard .chart-container {
              background: rgba(255, 255, 255, 0.05);
              border-radius: 15px;
              padding: 25px;
              border: 1px solid rgba(255, 255, 255, 0.1);
              backdrop-filter: blur(5px);
              height: auto;
              min-height: 500px;
              display: flex;
              flex-direction: column;
              width: 100% !important;
              box-sizing: border-box !important;
              margin: 0 !important;
            }
            
            .full-chart-analysis-dashboard .chart-container.extra-large {
              min-height: 600px;
            }
            
            .full-chart-analysis-dashboard .chart-container canvas {
              height: 350px !important;
              max-height: 350px !important;
              width: 100% !important;
              max-width: 100% !important;
              flex-shrink: 0;
            }
            
            .full-chart-analysis-dashboard .chart-container.extra-large canvas {
              height: 450px !important;
              max-height: 450px !important;
              width: 100% !important;
              max-width: 100% !important;
            }
            
            /* 确保Chart.js容器也能自适应 */
            .full-chart-analysis-dashboard .chart-container > div {
              width: 100% !important;
              height: auto !important;
            }
            
            .full-chart-analysis-dashboard .chart-container h3 {
              color: white;
              margin-bottom: 20px;
              font-size: 1.4rem;
              text-align: center;
              font-weight: bold;
            }
            
            .full-chart-analysis-dashboard .chart-insight {
              margin-top: 15px;
              padding: 15px;
              background: rgba(102, 126, 234, 0.1);
              border-radius: 10px;
              color: white;
              border-left: 4px solid #667eea;
              font-size: 1.1rem;
              line-height: 1.6;
              flex-shrink: 0;
            }
            
            .full-chart-analysis-dashboard .chart-insight strong {
              color: white;
            }
            
            .full-chart-analysis-dashboard .algorithm-comparison-table,
            .full-chart-analysis-dashboard .algorithm-features {
              margin-top: 16px;
              flex-shrink: 0;
            }
            
            /* 移动端适配 */
            @media (max-width: 768px) {
              .chart-analysis-modal {
                width: 100vw !important;
                height: 100vh !important;
                border-radius: 0 !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid {
                grid-template-columns: 1fr !important;
                grid-template-rows: auto auto auto !important;
                gap: 15px !important;
                padding: 10px !important;
                width: 100% !important;
              }
              
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(1),
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(2),
              .full-chart-analysis-dashboard .charts-grid .chart-container:nth-child(3) {
                grid-column: 1 !important;
                width: 100% !important;
              }
              
              .full-chart-analysis-dashboard .chart-container {
                padding: 15px !important;
                min-height: 400px !important;
                width: 100% !important;
                margin: 0 !important;
              }
              
              .full-chart-analysis-dashboard .chart-container canvas {
                height: 250px !important;
                max-height: 250px !important;
                width: 100% !important;
                max-width: 100% !important;
              }
            }
          `}</style>
                    <div className="full-chart-analysis-dashboard">
                        {renderTabContent()}
                    </div>
                </div>

                {/* 數據來源說明頁腳 */}
                <div
                    className="modal-footer"
                    style={{
                        padding: '20px 24px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                        backgroundColor: 'rgba(0, 0, 0, 0.3)',
                        fontSize: '0.9rem',
                        color: 'rgba(255, 255, 255, 0.9)',
                        lineHeight: '1.6',
                        minHeight: '100px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '12px',
                    }}
                >
                    <div
                        style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: '16px',
                            alignItems: 'flex-start',
                        }}
                    >
                        <div style={{ flex: '1', minWidth: '300px' }}>
                            <strong
                                style={{
                                    color: 'white',
                                    display: 'block',
                                    marginBottom: '8px',
                                }}
                            >
                                🔄 重構版數據來源：
                            </strong>
                            <div
                                style={{
                                    paddingLeft: '16px',
                                    color: 'rgba(255, 255, 255, 0.85)',
                                }}
                            >
                                《Accelerating Handover in Mobile Satellite
                                Network》IEEE INFOCOM 2024 | UERANSIM + Open5GS
                                原型系統 | NetStack Core Sync API | Celestrak
                                TLE 即時軌道數據 | 真實 Starlink & Kuiper
                                衛星參數
                            </div>
                        </div>
                    </div>
                    <div
                        style={{
                            fontSize: '0.85rem',
                            color: 'rgba(255, 255, 255, 0.7)',
                            fontStyle: 'italic',
                            padding: '12px 16px',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderLeft: '3px solid rgba(59, 130, 246, 0.5)',
                            borderRadius: '4px',
                        }}
                    >
                        💡
                        此版本採用智能數據回退機制：優先使用真實API數據，API失敗時自動切換到模擬數據。
                        所有圖表容器已優化為更大尺寸，提供完整的內容顯示空間。
                    </div>
                </div>
            </div>
        </div>
    )
}

export default FullChartAnalysisDashboard
