/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import React, {
    useState,
    useEffect,
    useMemo,
    useCallback,
    useRef,
    memo,
} from 'react'
import { useStrategy } from '../../../../contexts/StrategyContext'
import { useInfocomMetrics } from '../../../../hooks/useInfocomMetrics'
import {
    registerChartComponents,
    configureChartDefaults,
} from './utils/chartConfig'
import { useChartData } from './hooks/useChartData'
import {
    generateHandoverLatencyData,
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
import OverviewTab from './tabs/OverviewTab'
import PerformanceTab from './tabs/PerformanceTab'
import SystemTab from './tabs/SystemTab'
import AlgorithmsTab from './tabs/AlgorithmsTab'
import AnalysisTab from './tabs/AnalysisTab'
import ParametersTab from './tabs/ParametersTab'
import MonitoringTab from './tabs/MonitoringTab'
import StrategyTab from './tabs/StrategyTab'
import RLMonitoringTab from './tabs/RLMonitoringTab'
import './ChartAnalysisDashboard.scss'

// 初始化Chart.js
registerChartComponents()
configureChartDefaults()

interface ChartAnalysisDashboardProps {
    isOpen: boolean
    onClose: () => void
}

const ChartAnalysisDashboard: React.FC<ChartAnalysisDashboardProps> = ({
    isOpen,
    onClose,
}) => {
    // 使用 useRef 緩存生成的數據，避免無限渲染
    const cachedData = useRef<{
        handoverLatencyData?: any
        sixScenarioData?: any
        performanceRadarData?: any
        globalCoverageData?: any
        timeSyncPrecisionData?: any
        algorithmLatencyData?: any
        qoeTimeSeriesData?: any
        lastSatelliteData?: any
        lastCurrentStrategy?: any
        lastInfocomMetrics?: any
        lastData?: any
        lastOnClose?: any
    }>({})

    // 渲染計數器
    const renderCount = useRef(0)
    renderCount.current += 1
    console.log(
        '🔵 ChartAnalysisDashboard render #',
        renderCount.current,
        'isOpen:',
        isOpen,
        'onClose changed:',
        onClose === cachedData.current.lastOnClose ? 'same' : 'different'
    )

    cachedData.current.lastOnClose = onClose

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
    console.log(
        '🔧 currentStrategy changed:',
        currentStrategy,
        'reference:',
        currentStrategy === cachedData.current.lastCurrentStrategy
            ? 'same'
            : 'different'
    )
    cachedData.current.lastCurrentStrategy = currentStrategy

    // const infocomMetrics = useInfocomMetrics(isOpen)
    const infocomMetrics = { handoverLatency: 21.5, successRate: 99.2 } // 固定值
    console.log(
        '🔧 infocomMetrics changed:',
        infocomMetrics ? 'exists' : 'null',
        'reference:',
        infocomMetrics === cachedData.current.lastInfocomMetrics
            ? 'same'
            : 'different'
    )
    cachedData.current.lastInfocomMetrics = infocomMetrics

    // const { data, satelliteData, strategyMetrics, setStrategyMetrics } = useChartData(isOpen)
    const data = {
        handoverLatencyData: null,
        sixScenarioData: null,
        strategyEffectData: null,
        systemMetrics: { cpu: 0, memory: 0, gpu: 0, networkLatency: 0 },
        performanceRadarData: null,
        globalCoverageData: null,
        timeSyncPrecisionData: null,
        qoeTimeSeriesData: null,
    } // 固定值
    const satelliteData = {
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
    } // 固定模擬數據
    const strategyMetrics = {
        flexible: { averageLatency: 25, successRate: 95 },
        consistent: { averageLatency: 35, successRate: 98 },
    } // 固定模擬數據
    const setStrategyMetrics = () => {} // 固定值
    console.log(
        '🔧 useChartData returned - data exists:',
        data ? true : false,
        'reference:',
        data === cachedData.current.lastData ? 'same' : 'different'
    )
    console.log(
        '🔧 useChartData returned - satelliteData exists:',
        satelliteData ? true : false,
        'reference:',
        satelliteData === cachedData.current.lastSatelliteData
            ? 'same'
            : 'different'
    )
    cachedData.current.lastData = data
    cachedData.current.lastSatelliteData = satelliteData

    // 生成圖表數據 - 使用緩存避免重復生成
    const handoverLatencyData = useMemo(() => {
        console.log('🟦 handoverLatencyData useMemo triggered')
        if (data.handoverLatencyData) return data.handoverLatencyData
        if (!cachedData.current.handoverLatencyData) {
            cachedData.current.handoverLatencyData =
                generateHandoverLatencyData()
        }
        return cachedData.current.handoverLatencyData
    }, [data.handoverLatencyData])

    const sixScenarioChartData = useMemo(() => {
        if (data.sixScenarioData) return data.sixScenarioData
        if (!cachedData.current.sixScenarioData) {
            cachedData.current.sixScenarioData = generateSixScenarioData()
        }
        return cachedData.current.sixScenarioData
    }, [data.sixScenarioData])

    const constellationComparisonData = useMemo(() => {
        const result = generateConstellationComparisonData(satelliteData)
        cachedData.current.lastSatelliteData = satelliteData
        return result
    }, [satelliteData])

    const strategyEffectData = useMemo(() => {
        return (
            data.strategyEffectData ||
            generateStrategyEffectData(strategyMetrics)
        )
    }, [data.strategyEffectData, strategyMetrics])

    const systemResourceData = useMemo(() => {
        return generateSystemResourceData(data.systemMetrics)
    }, [data.systemMetrics])

    const performanceRadarData = useMemo(() => {
        if (data.performanceRadarData) return data.performanceRadarData
        if (!cachedData.current.performanceRadarData) {
            cachedData.current.performanceRadarData =
                generatePerformanceRadarData()
        }
        return cachedData.current.performanceRadarData
    }, [data.performanceRadarData])

    const globalCoverageData = useMemo(() => {
        if (data.globalCoverageData) return data.globalCoverageData
        if (!cachedData.current.globalCoverageData) {
            cachedData.current.globalCoverageData = generateGlobalCoverageData()
        }
        return cachedData.current.globalCoverageData
    }, [data.globalCoverageData])

    const timeSyncPrecisionData = useMemo(() => {
        if (data.timeSyncPrecisionData) return data.timeSyncPrecisionData
        if (!cachedData.current.timeSyncPrecisionData) {
            cachedData.current.timeSyncPrecisionData =
                generateTimeSyncPrecisionData()
        }
        return cachedData.current.timeSyncPrecisionData
    }, [data.timeSyncPrecisionData])

    const algorithmLatencyData = useMemo(() => {
        if (!cachedData.current.algorithmLatencyData) {
            cachedData.current.algorithmLatencyData =
                generateAlgorithmLatencyData()
        }
        return cachedData.current.algorithmLatencyData
    }, [])

    const qoeTimeSeriesData = useMemo(() => {
        if (data.qoeTimeSeriesData) return data.qoeTimeSeriesData
        if (!cachedData.current.qoeTimeSeriesData) {
            cachedData.current.qoeTimeSeriesData = generateQoETimeSeriesData()
        }
        return cachedData.current.qoeTimeSeriesData
    }, [data.qoeTimeSeriesData])

    // 監聽RL訓練數據更新
    useEffect(() => {
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
            return insights[Math.floor(Math.random() * insights.length)]
        },
        []
    )

    // Tab標籤配置 - 暫時只顯示第一個分頁進行測試
    const tabs = [
        { id: 'overview', label: '📊 IEEE核心', icon: '📊' },
        // { id: 'performance', label: '⚡ 性能QoE', icon: '⚡' },
        // { id: 'system', label: '🖥️ 系統監控', icon: '🖥️' },
        // { id: 'algorithms', label: '🧮 算法策略', icon: '🧮' },
        // { id: 'analysis', label: '📈 深度分析', icon: '📈' },
        // { id: 'parameters', label: '⚙️ 軌道參數', icon: '⚙️' },
        // { id: 'monitoring', label: '👁️ 即時監控', icon: '👁️' },
        // { id: 'strategy', label: '🎯 策略效果', icon: '🎯' },
        // { id: 'rl-monitoring', label: '🧠 RL監控', icon: '🧠' },
        // { id: 'rl-monitoring', label: '🧠 RL監控', icon: '🧠' },
    ]

    // 渲染Tab內容 - 暫時只處理第一個分頁進行測試
    const renderTabContent = () => {
        console.log('🔄 renderTabContent called, activeTab:', activeTab)

        switch (activeTab) {
            case 'overview':
                console.log(
                    '📊 Rendering Overview Tab with handoverLatencyData:',
                    handoverLatencyData ? 'exists' : 'null'
                )
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

            default:
                return (
                    <div className="tab-placeholder">
                        <h3>🚧 分頁測試中</h3>
                        <p>目前只測試第一個分頁</p>
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
                                <span className="tab-icon">{tab.icon}</span>
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

// 使用 React.memo 避免不必要的重新渲染
export default memo(ChartAnalysisDashboard)
