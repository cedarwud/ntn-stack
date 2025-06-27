import { useState, useEffect, useMemo, useCallback, useRef } from 'react'
import { useStrategy } from '../../../../contexts/StrategyContext'
import { netStackApi } from '../../../../services/netstack-api'
import { satelliteCache } from '../../../../utils/satellite-cache'
import { useInfocomMetrics } from '../../../../hooks/useInfocomMetrics'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    LogarithmicScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    Filler,
    RadialLinearScale,
} from 'chart.js'
import { Bar, Line, Pie, Doughnut, Radar } from 'react-chartjs-2'
import GymnasiumRLMonitor from '../../../dashboard/GymnasiumRLMonitor'
import './ChartAnalysisDashboard.scss'

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    LogarithmicScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    ArcElement,
    Filler,
    RadialLinearScale
)

// Configure global Chart.js defaults for white text and larger fonts
ChartJS.defaults.color = 'white'
ChartJS.defaults.font.size = 16
ChartJS.defaults.plugins.legend.labels.color = 'white'
ChartJS.defaults.plugins.legend.labels.font = { size: 16 }
ChartJS.defaults.plugins.title.color = 'white'
ChartJS.defaults.plugins.title.font = { size: 20, weight: 'bold' as 'bold' }
ChartJS.defaults.plugins.tooltip.titleColor = 'white'
ChartJS.defaults.plugins.tooltip.bodyColor = 'white'
ChartJS.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.9)'
ChartJS.defaults.plugins.tooltip.titleFont = { size: 16 }
ChartJS.defaults.plugins.tooltip.bodyFont = { size: 15 }
ChartJS.defaults.scale.ticks.color = 'white'
ChartJS.defaults.scale.ticks.font = { size: 14 }
// Fix undefined notation issue in Chart.js number formatting
ChartJS.defaults.locale = 'en-US'
;(ChartJS.defaults as any).elements = {
    ...((ChartJS.defaults as any).elements || {}),
    arc: {
        ...((ChartJS.defaults as any).elements?.arc || {}),
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    bar: {
        ...((ChartJS.defaults as any).elements?.bar || {}),
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
    line: {
        ...((ChartJS.defaults as any).elements?.line || {}),
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
    },
}
// Chart.js scale title configuration (type-safe)
try {
    ;(ChartJS.defaults.scale as any).title = {
        color: 'white',
        font: { size: 16, weight: 'bold' as 'bold' },
    }
} catch (e) {
    console.warn('Could not set scale title defaults:', e)
}
ChartJS.defaults.scale.grid.color = 'rgba(255, 255, 255, 0.2)'

interface ChartAnalysisDashboardProps {
    isOpen: boolean
    onClose: () => void
}

const ChartAnalysisDashboard = ({
    isOpen,
    onClose,
}: ChartAnalysisDashboardProps) => {
    // 所有 hooks 必須在條件語句之前調用
    const [activeTab, setActiveTab] = useState('overview')
    const [isCalculating] = useState(false)
    const [systemMetrics, setSystemMetrics] = useState({
        cpu: 25,        // 合理的初始 CPU 使用率
        memory: 35,     // 合理的初始記憶體使用率
        gpu: 15,        // 合理的初始 GPU 使用率
        networkLatency: 45,  // 合理的初始網路延遲(ms)
    })
    const [realDataError, setRealDataError] = useState<string | null>(null)
    const [coreSync, setCoreSync] = useState<any>(null)
    
    // 獲取實際的 INFOCOM 2024 算法指標
    const infocomMetrics = useInfocomMetrics(isOpen)
    // RL 監控相關狀態
    const [rlData, setRlData] = useState<any>(null)
    const [isDqnTraining, setIsDqnTraining] = useState(false) // DQN 初始為待機
    const [isPpoTraining, setIsPpoTraining] = useState(false) // PPO 初始為待機
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

    // 🎯 使用全域策略狀態
    const {
        currentStrategy,
        switchStrategy: globalSwitchStrategy,
        isLoading: strategyLoading,
    } = useStrategy()

    // Early return if not open - all hooks called before this point
    if (!isOpen) {
        return null
    }

    return (
        <div className="chart-analysis-dashboard">
            <div className="dashboard-header">
                <div className="header-left">
                    <h2>📊 圖表分析儀表板</h2>
                    <span className="subtitle">INFOCOM 2024 算法性能分析</span>
                </div>
                <div className="header-right">
                    <button
                        className="close-button"
                        onClick={onClose}
                        aria-label="關閉儀表板"
                    >
                        ✕
                    </button>
                </div>
            </div>

            <div className="dashboard-tabs">
                <div className="tab-list">
                    {[
                        { id: 'overview', label: '📋 總覽', icon: '📋' },
                        { id: 'performance', label: '⚡ 性能', icon: '⚡' },
                        { id: 'algorithms', label: '🤖 算法', icon: '🤖' },
                        { id: 'system', label: '💻 系統', icon: '💻' },
                        { id: 'analysis', label: '📈 分析', icon: '📈' },
                        { id: 'strategy', label: '🎯 策略', icon: '🎯' },
                        { id: 'rl-monitoring', label: '🧠 強化學習', icon: '🧠' },
                        { id: 'monitoring', label: '📊 監控', icon: '📊' },
                        { id: 'parameters', label: '⚙️ 參數', icon: '⚙️' },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            className={`tab-button ${
                                activeTab === tab.id ? 'active' : ''
                            }`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <span className="tab-icon">{tab.icon}</span>
                            <span className="tab-label">{tab.label}</span>
                        </button>
                    ))}
                </div>
            </div>

            <div className="dashboard-content">
                {activeTab === 'overview' && (
                    <div className="tab-panel overview-panel">
                        <div className="overview-grid">
                            <div className="metrics-card">
                                <h3>🎯 核心指標</h3>
                                <div className="metrics-grid">
                                    <div className="metric-item">
                                        <span className="metric-label">切換延遲</span>
                                        <span className="metric-value">
                                            {infocomMetrics?.handoverLatency?.toFixed(1) || '21.5'} ms
                                        </span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">成功率</span>
                                        <span className="metric-value">
                                            {infocomMetrics?.successRate?.toFixed(1) || '99.2'}%
                                        </span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">策略</span>
                                        <span className="metric-value">
                                            {currentStrategy === 'flexible' ? '靈活策略' : '一致策略'}
                                        </span>
                                    </div>
                                    <div className="metric-item">
                                        <span className="metric-label">系統負載</span>
                                        <span className="metric-value">
                                            {systemMetrics.cpu}%
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="status-card">
                                <h3>📡 系統狀態</h3>
                                <div className="status-grid">
                                    <div className="status-item">
                                        <span className="status-indicator healthy"></span>
                                        <span>NetStack 核心</span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-indicator healthy"></span>
                                        <span>SimWorld 後端</span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-indicator healthy"></span>
                                        <span>RL 監控</span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-indicator healthy"></span>
                                        <span>圖表分析</span>
                                    </div>
                                </div>
                            </div>

                            <div className="training-card">
                                <h3>🧠 訓練狀態</h3>
                                <div className="training-grid">
                                    <div className="training-item">
                                        <span className="training-label">DQN</span>
                                        <span className="training-status">
                                            {isDqnTraining ? '🟢 訓練中' : '⏸️ 待機'}
                                        </span>
                                    </div>
                                    <div className="training-item">
                                        <span className="training-label">PPO</span>
                                        <span className="training-status">
                                            {isPpoTraining ? '🟢 訓練中' : '⏸️ 待機'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'performance' && (
                    <div className="tab-panel performance-panel">
                        <div className="performance-grid">
                            <div className="chart-container">
                                <h3>⚡ 系統性能指標</h3>
                                <div className="performance-metrics">
                                    <div className="metric">
                                        <span>CPU: {systemMetrics.cpu}%</span>
                                        <div className="metric-bar">
                                            <div 
                                                className="metric-fill"
                                                style={{ width: `${systemMetrics.cpu}%` }}
                                            />
                                        </div>
                                    </div>
                                    <div className="metric">
                                        <span>Memory: {systemMetrics.memory}%</span>
                                        <div className="metric-bar">
                                            <div 
                                                className="metric-fill"
                                                style={{ width: `${systemMetrics.memory}%` }}
                                            />
                                        </div>
                                    </div>
                                    <div className="metric">
                                        <span>GPU: {systemMetrics.gpu}%</span>
                                        <div className="metric-bar">
                                            <div 
                                                className="metric-fill"
                                                style={{ width: `${systemMetrics.gpu}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {activeTab === 'rl-monitoring' && (
                    <div className="tab-panel rl-monitoring-panel">
                        <GymnasiumRLMonitor />
                    </div>
                )}

                {/* Add other tab panels as needed */}
            </div>
        </div>
    )
}

export default ChartAnalysisDashboard