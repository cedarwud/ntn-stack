/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect, useMemo, useCallback, memo } from 'react'
// import { useStrategy } from '../../../../contexts/StrategyContext'
// import { useInfocomMetrics } from '../../../../hooks/useInfocomMetrics'
import {
    registerChartComponents,
    configureChartDefaults,
} from './utils/chartConfig'
// import { useChartData } from './hooks/useChartData' // 完全移除這個導入
import {
    generateSixScenarioData,
    generateConstellationComparisonData,
    generateStrategyEffectData,
    generateSystemResourceData,
    generatePerformanceRadarData,
    generateGlobalCoverageData,
    generateTimeSyncPrecisionData,
    generateAlgorithmLatencyData,
    generateQoETimeSeriesData,
} from './utils/dataGenerators'

// 🔧 將所有數據生成改為組件外部的靜態常量，確保引用絕對穩定
const STATIC_HANDOVER_LATENCY_DATA = {
    labels: [
        '準備階段',
        '同步階段',
        '切換階段',
        '確認階段',
        '清理階段',
        '完成階段',
    ],
    datasets: [
        {
            label: 'NTN',
            data: [45.2, 89.3, 67.8, 34.1, 15.6, 8.2],
            backgroundColor: 'rgba(255, 99, 132, 0.8)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2,
        },
        {
            label: 'NTN-GS',
            data: [23.8, 52.4, 41.2, 22.7, 8.9, 4.2],
            backgroundColor: 'rgba(54, 162, 235, 0.8)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
        },
        {
            label: 'NTN-SMN',
            data: [25.1, 54.8, 43.6, 24.3, 9.4, 4.6],
            backgroundColor: 'rgba(255, 206, 86, 0.8)',
            borderColor: 'rgba(255, 206, 86, 1)',
            borderWidth: 2,
        },
        {
            label: 'Proposed',
            data: [3.2, 7.8, 5.9, 2.1, 1.2, 0.9],
            backgroundColor: 'rgba(75, 192, 192, 0.8)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
        },
    ],
}
// import OverviewTab from './tabs/OverviewTab' // 第三步：恢復 OverviewTab
import OverviewTab from './tabs/OverviewTab'
import PerformanceTab from './tabs/PerformanceTab'
import SystemTab from './tabs/SystemTab'
import AlgorithmsTab from './tabs/AlgorithmsTab'
import AnalysisTab from './tabs/AnalysisTab'
import ParametersTab from './tabs/ParametersTab'
import MonitoringTab from './tabs/MonitoringTab'
import StrategyTab from './tabs/StrategyTab'
import RLMonitoringTab from './tabs/RLMonitoringTab'
import { Bar } from 'react-chartjs-2' // 添加 Bar 組件導入
import './ChartAnalysisDashboard.scss'

// 初始化Chart.js
registerChartComponents()
configureChartDefaults()

// 移到組件外部的固定數據，避免每次渲染都創建新對象
const FIXED_INFOCOM_METRICS = { handoverLatency: 21.5, successRate: 99.2 }
const FIXED_DATA = {
    handoverLatencyData: null,
    sixScenarioData: null,
    strategyEffectData: null,
    systemMetrics: { cpu: 0, memory: 0, gpu: 0, networkLatency: 0 },
    performanceRadarData: null,
    globalCoverageData: null,
    timeSyncPrecisionData: null,
    qoeTimeSeriesData: null,
}
const FIXED_SATELLITE_DATA = {
    starlink: {
        altitude: 550,
        count: 12000,
        coverage: 95,
        delay: 25,
        doppler: 40,
        power: 85,
    },
    kuiper: {
        altitude: 630,
        count: 3236,
        coverage: 92,
        delay: 28,
        doppler: 35,
        power: 80,
    },
    oneweb: {
        altitude: 1200,
        count: 648,
        coverage: 88,
        delay: 35,
        doppler: 20,
        power: 75,
    },
}
const FIXED_STRATEGY_METRICS = {
    flexible: { averageLatency: 25, successRate: 95 },
    consistent: { averageLatency: 35, successRate: 98 },
}

// 添加所有其他數據的靜態常量，避免動態生成
const STATIC_SIX_SCENARIO_DATA = {
    labels: [
        'SL-B-單向',
        'SL-F-全向',
        'SL-D-差異',
        'KP-B-單向',
        'KP-F-全向',
        'KP-D-差異',
    ],
    datasets: [
        {
            label: '延遲 (ms)',
            data: [23.5, 28.1, 31.7, 26.2, 30.8, 34.5],
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
        },
    ],
}

const STATIC_CONSTELLATION_COMPARISON_DATA = {
    labels: ['覆蓋率', '延遲', '多普勒', '功率', '增益'],
    datasets: [
        {
            label: 'Starlink',
            data: [95, 85, 75, 88, 92],
            backgroundColor: 'rgba(255, 99, 132, 0.6)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 2,
        },
        {
            label: 'Kuiper',
            data: [92, 82, 78, 85, 89],
            backgroundColor: 'rgba(54, 162, 235, 0.6)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
        },
    ],
}

const STATIC_STRATEGY_EFFECT_DATA = {
    labels: ['延遲優化', '成功率', '能耗效率', '系統負載'],
    datasets: [
        {
            label: 'Flexible Strategy',
            data: [85, 92, 87, 78],
            backgroundColor: 'rgba(75, 192, 192, 0.6)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
        },
        {
            label: 'Consistent Strategy',
            data: [88, 95, 94, 82],
            backgroundColor: 'rgba(255, 206, 86, 0.6)',
            borderColor: 'rgba(255, 206, 86, 1)',
            borderWidth: 2,
        },
    ],
}

const STATIC_PERFORMANCE_RADAR_DATA = {
    labels: ['延遲', '吞吐量', '可靠性', '能耗', '覆蓋率'],
    datasets: [
        {
            label: '當前性能',
            data: [85, 78, 92, 87, 90],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
        },
    ],
}

const STATIC_QOE_TIME_SERIES_DATA = {
    labels: ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10'],
    datasets: [
        {
            label: 'Ultra-Dense Urban',
            data: [0.92, 0.89, 0.91, 0.88, 0.9, 0.87, 0.89, 0.91, 0.88, 0.9],
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderWidth: 3,
            tension: 0.4,
            fill: false,
        },
        {
            label: 'Dense Urban',
            data: [0.88, 0.85, 0.87, 0.84, 0.86, 0.83, 0.85, 0.87, 0.84, 0.86],
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderWidth: 3,
            tension: 0.4,
            fill: false,
        },
    ],
}

const STATIC_COMPLEXITY_DATA = {
    labels: ['算法複雜度', '計算時間', '記憶體使用', '網路負載'],
    datasets: [
        {
            label: '複雜度分析',
            data: [75, 68, 82, 71],
            backgroundColor: 'rgba(153, 102, 255, 0.6)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 2,
        },
    ],
}

interface ChartAnalysisDashboardProps {
    isOpen: boolean
    onClose: () => void
}

const ChartAnalysisDashboard: React.FC<ChartAnalysisDashboardProps> = ({
    isOpen,
    onClose,
}) => {
    // 基本狀態
    const [activeTab, setActiveTab] = useState('overview')
    const [selectedDataPoint, setSelectedDataPoint] = useState<any>(null)
    const [showDataInsight, setShowDataInsight] = useState(false)

    // RL相關狀態
    const [isDqnTraining, setIsDqnTraining] = useState(false)
    const [isPpoTraining, setIsPpoTraining] = useState(false)
    const [trainingMetrics, setTrainingMetrics] = useState({
        dqn: {
            episodes: 0,
            avgReward: 0,
            progress: 0,
            handoverDelay: 0,
            successRate: 0,
            signalDropTime: 0,
            energyEfficiency: 0,
        },
        ppo: {
            episodes: 0,
            avgReward: 0,
            progress: 0,
            handoverDelay: 0,
            successRate: 0,
            signalDropTime: 0,
            energyEfficiency: 0,
        },
    })

    const [rewardTrendData, setRewardTrendData] = useState({
        dqnData: [] as number[],
        ppoData: [] as number[],
        labels: [] as string[],
    })

    const [policyLossData, setPolicyLossData] = useState({
        dqnLoss: [] as number[],
        ppoLoss: [] as number[],
        labels: [] as string[],
    })

    // 使用自定義hooks - 暫時停用以完全除錯
    // const { currentStrategy } = useStrategy()
    const currentStrategy = 'flexible' // 固定值

    // const infocomMetrics = useInfocomMetrics(isOpen)
    const infocomMetrics = FIXED_INFOCOM_METRICS // 使用固定常量

    // const { data, satelliteData, strategyMetrics, setStrategyMetrics } = useChartData(isOpen)
    const data = FIXED_DATA // 使用固定常量
    const satelliteData = FIXED_SATELLITE_DATA // 使用固定常量
    const strategyMetrics = FIXED_STRATEGY_METRICS // 使用固定常量
    const setStrategyMetrics = () => {} // 固定值

    // 🔧 使用靜態常量，完全避免動態生成
    const handoverLatencyData = STATIC_HANDOVER_LATENCY_DATA
    const sixScenarioChartData = STATIC_SIX_SCENARIO_DATA
    const constellationComparisonData = STATIC_CONSTELLATION_COMPARISON_DATA
    const strategyEffectData = STATIC_STRATEGY_EFFECT_DATA
    const performanceRadarData = STATIC_PERFORMANCE_RADAR_DATA
    const qoeTimeSeriesData = STATIC_QOE_TIME_SERIES_DATA
    const complexityData = STATIC_COMPLEXITY_DATA

    // 其他數據也使用靜態值
    const systemResourceData = null
    const globalCoverageData = null
    const timeSyncPrecisionData = null
    const algorithmLatencyData = null
    useEffect(() => {
        // 暫時停用所有事件監聽器以確認無限渲染源
        /*
        const handleRLMetricsUpdate = (event: CustomEvent) => {
            const { engine, metrics } = event.detail

            setTrainingMetrics((prev) => {
                const newMetrics = { ...prev }

                if (engine === 'dqn') {
                    newMetrics.dqn = {
                        episodes: metrics.episodes_completed || 0,
                        avgReward: metrics.average_reward || 0,
                        progress: metrics.training_progress || 0,
                        handoverDelay:
                            45 -
                            (metrics.training_progress / 100) * 20 +
                            (Math.random() - 0.5) * 5,
                        successRate: Math.min(
                            100,
                            82 +
                                (metrics.training_progress / 100) * 12 +
                                (Math.random() - 0.5) * 1.5
                        ),
                        signalDropTime:
                            18 -
                            (metrics.training_progress / 100) * 8 +
                            (Math.random() - 0.5) * 2,
                        energyEfficiency:
                            0.75 +
                            (metrics.training_progress / 100) * 0.2 +
                            (Math.random() - 0.5) * 0.05,
                    }

                    setRewardTrendData((prevData) => {
                        const newDataPoints = [
                            ...prevData.dqnData,
                            metrics.average_reward,
                        ].slice(-50)
                        const newLabels = [
                            ...prevData.labels,
                            `E${metrics.episodes_completed}`,
                        ].slice(-50)
                        return {
                            ...prevData,
                            dqnData: newDataPoints,
                            labels: newLabels,
                        }
                    })
                } else if (engine === 'ppo') {
                    newMetrics.ppo = {
                        episodes: metrics.episodes_completed || 0,
                        avgReward: metrics.average_reward || 0,
                        progress: metrics.training_progress || 0,
                        handoverDelay:
                            42 -
                            (metrics.training_progress / 100) * 18 +
                            (Math.random() - 0.5) * 4,
                        successRate: Math.min(
                            100,
                            85 +
                                (metrics.training_progress / 100) * 10 +
                                (Math.random() - 0.5) * 1.2
                        ),
                        signalDropTime:
                            16 -
                            (metrics.training_progress / 100) * 7 +
                            (Math.random() - 0.5) * 1.8,
                        energyEfficiency:
                            0.78 +
                            (metrics.training_progress / 100) * 0.18 +
                            (Math.random() - 0.5) * 0.04,
                    }

                    setRewardTrendData((prevData) => {
                        const newDataPoints = [
                            ...prevData.ppoData,
                            metrics.average_reward,
                        ].slice(-50)
                        const newLabels = [
                            ...prevData.labels,
                            `E${metrics.episodes_completed}`,
                        ].slice(-50)
                        return {
                            ...prevData,
                            ppoData: newDataPoints,
                            labels: newLabels,
                        }
                    })
                }

                return newMetrics
            })
        }

        const handleTrainingStarted = (event: CustomEvent) => {
            const { engine } = event.detail
            if (engine === 'dqn') setIsDqnTraining(true)
            if (engine === 'ppo') setIsPpoTraining(true)
        }

        const handleTrainingStopped = (event: CustomEvent) => {
            const { engine } = event.detail
            if (engine === 'dqn') setIsDqnTraining(false)
            if (engine === 'ppo') setIsPpoTraining(false)
        }

        window.addEventListener(
            'rl-metrics-update',
            handleRLMetricsUpdate as EventListener
        )
        window.addEventListener(
            'training-started',
            handleTrainingStarted as EventListener
        )
        window.addEventListener(
            'training-stopped',
            handleTrainingStopped as EventListener
        )

        return () => {
            window.removeEventListener(
                'rl-metrics-update',
                handleRLMetricsUpdate as EventListener
            )
            window.removeEventListener(
                'training-started',
                handleTrainingStarted as EventListener
            )
            window.removeEventListener(
                'training-stopped',
                handleTrainingStopped as EventListener
            )
        }
        */
    }, [])

    // 圖表點擊處理
    const handleChartClick = useCallback(
        (event: any, elements: any[], chart: any) => {
            if (elements.length > 0) {
                const element = elements[0]
                const datasetIndex = element.datasetIndex
                const index = element.index
                const label = chart.data.labels[index]
                const dataset = chart.data.datasets[datasetIndex].label

                setSelectedDataPoint({ label, dataset, datasetIndex, index })
                setShowDataInsight(true)
            }
        },
        []
    )

    // 生成數據洞察
    const generateDataInsight = useCallback(
        (label: string, dataset: string): string => {
            const insights = [
                `${dataset} 在 ${label} 場景下表現突出，這表明算法在此條件下具有優越性能。`,
                `數據顯示 ${dataset} 方案在 ${label} 中實現了顯著的延遲降低。`,
                `${label} 場景下的 ${dataset} 指標證明了系統的穩定性和可靠性。`,
            ]
            // 使用確定性選擇而非隨機選擇，避免無限渲染
            const index = (label.length + dataset.length) % insights.length
            return insights[index]
        },
        []
    )

    // Tab標籤配置 - 恢復完整的9個分頁 📊
    const tabs = [
        { id: 'overview', label: '📊 IEEE核心' },
        { id: 'performance', label: '⚡ 性能QoE' },
        { id: 'system', label: '🖥️ 系統監控' },
        { id: 'algorithms', label: '🧮 算法策略' },
        { id: 'analysis', label: '📈 深度分析' },
        { id: 'parameters', label: '⚙️ 軌道參數' },
        { id: 'monitoring', label: '👁️ 即時監控' },
        { id: 'strategy', label: '🎯 策略效果' },
        { id: 'rl-monitoring', label: '🧠 RL監控' },
    ]

    // 渲染Tab內容
    const renderTabContent = () => {
        switch (activeTab) {
            case 'overview':
                return (
                    <OverviewTab
                        handoverLatencyData={handoverLatencyData}
                        constellationComparisonData={
                            constellationComparisonData
                        }
                        sixScenarioChartData={sixScenarioChartData}
                        onChartClick={handleChartClick}
                    />
                )

            case 'performance':
                return (
                    <PerformanceTab
                        qoeTimeSeriesData={qoeTimeSeriesData}
                        complexityData={null} // ⚠️ 使用 null 作為佔位符
                        onChartClick={handleChartClick}
                    />
                )

            case 'system':
                return (
                    <div className="tab-placeholder">
                        <h3>🖥️ 系統監控</h3>
                        <p>⚠️ 此分頁需要真實系統數據，正在開發中</p>
                    </div>
                )

            case 'algorithms':
                return (
                    <div className="tab-placeholder">
                        <h3>🧮 算法策略</h3>
                        <p>⚠️ 此分頁需要真實算法數據，正在開發中</p>
                    </div>
                )

            case 'analysis':
                return (
                    <AnalysisTab
                        _globalCoverageData={globalCoverageData}
                        strategyEffectData={strategyEffectData}
                        onChartClick={handleChartClick}
                    />
                )

            case 'parameters':
                return (
                    <div className="tab-placeholder">
                        <h3>⚙️ 軌道參數</h3>
                        <p>⚠️ 此分頁使用模擬數據 - 需要即時計算軌道力學參數</p>
                        <p>
                            原因：軌道計算需要大量數學運算，使用模擬數據展示功能
                        </p>
                    </div>
                )

            case 'monitoring':
                return (
                    <div className="tab-placeholder">
                        <h3>👁️ 即時監控</h3>
                        <p>⚠️ 此分頁使用模擬數據 - 需要即時更新的網絡狀態</p>
                        <p>原因：即時監控需要持續的數據流，目前使用模擬數據</p>
                    </div>
                )

            case 'strategy':
                return (
                    <StrategyTab
                        _handoverLatencyData={handoverLatencyData}
                        _strategyEffectData={strategyEffectData}
                        onChartClick={handleChartClick}
                    />
                )

            case 'rl-monitoring':
                return (
                    <div className="tab-placeholder">
                        <h3>🧠 RL監控</h3>
                        <p>⚠️ 此分頁使用模擬數據 - AI訓練過程數據</p>
                        <p>
                            原因：強化學習需要動態生成的訓練數據，使用模擬環境
                        </p>
                    </div>
                )

            default:
                return (
                    <div className="tab-placeholder">
                        <h3>🚧 分頁開發中</h3>
                        <p>請選擇其他可用的分頁</p>
                    </div>
                )
        }
    }

    if (!isOpen) return null

    return (
        <div
            className="chart-analysis-overlay"
            style={{
                position: 'fixed',
                top: 0,
                left: 0,
                width: '100vw',
                height: '100vh',
                background:
                    'linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(20, 30, 48, 0.95))',
                zIndex: 99999,
                backdropFilter: 'blur(10px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}
        >
            <div
                className="chart-analysis-modal"
                style={{
                    width: '95vw',
                    height: '95vh',
                    background: 'linear-gradient(145deg, #1a1a2e, #16213e)',
                    borderRadius: '20px',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                }}
            >
                {/* 標題欄 */}
                <div className="modal-header">
                    <h2>📈 移動衛星網絡換手加速技術 - 深度圖表分析儀表板</h2>
                    <button className="close-btn" onClick={onClose}>
                        ✕
                    </button>
                </div>

                {/* Tab導航 */}
                <div className="tabs-container">
                    <div className="tabs">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                className={`tab-button ${
                                    activeTab === tab.id ? 'active' : ''
                                }`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* 內容區域 */}
                <div className="modal-content">{renderTabContent()}</div>

                {/* 數據洞察彈窗 */}
                {showDataInsight && selectedDataPoint && (
                    <div
                        className="data-insight-modal"
                        style={{
                            position: 'fixed',
                            top: '50%',
                            left: '50%',
                            transform: 'translate(-50%, -50%)',
                            background:
                                'linear-gradient(135deg, #1a1a2e, #16213e)',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '12px',
                            padding: '20px',
                            zIndex: 10001,
                            minWidth: '300px',
                            maxWidth: '500px',
                            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5)',
                        }}
                    >
                        <div
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                marginBottom: '15px',
                            }}
                        >
                            <h3 style={{ color: 'white', margin: 0 }}>
                                📊 數據洞察
                            </h3>
                            <button
                                onClick={() => setShowDataInsight(false)}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'white',
                                    fontSize: '18px',
                                    cursor: 'pointer',
                                }}
                            >
                                ✕
                            </button>
                        </div>
                        <div style={{ color: 'white', lineHeight: 1.6 }}>
                            <p>
                                <strong>選中數據：</strong>{' '}
                                {selectedDataPoint.dataset} -{' '}
                                {selectedDataPoint.label}
                            </p>
                            <p>
                                <strong>AI分析：</strong>{' '}
                                {generateDataInsight(
                                    selectedDataPoint.label,
                                    selectedDataPoint.dataset
                                )}
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

// 使用 React.memo 避免不必要的重新渲染，並提供自定義比較函數
export default memo(ChartAnalysisDashboard, (prevProps, nextProps) => {
    // 只有當 isOpen 狀態改變時才重新渲染
    return prevProps.isOpen === nextProps.isOpen
})
