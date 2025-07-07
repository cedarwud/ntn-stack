/**
 * 整合分析標籤頁內容組件 - 階段六重構版本
 * 關注點分離：UI渲染與業務邏輯完全分離
 * UI組件只負責渲染，所有邏輯由 useIntegratedAnalysis Hook 提供
 */
import React from 'react'
import { Bar, Line, Radar } from 'react-chartjs-2'
import { useIntegratedAnalysis } from '../hooks/useIntegratedAnalysis'
import { ChartPlaceholder } from './ChartPlaceholder' // 假設有一個佔位符組件

// ==================== 圖表選項 (可考慮也移入Hook或專用配置檔案) ====================
const commonChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { position: 'top' as const, labels: { color: 'white' } },
        title: { display: true, color: 'white', font: { size: 16 } },
    },
    scales: {
        x: {
            ticks: { color: 'white' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' },
        },
    },
}

const dualYAxisOptions = {
    ...commonChartOptions,
    scales: {
        ...commonChartOptions.scales,
        y: {
            type: 'linear' as const,
            position: 'left' as const,
            ticks: { color: 'white' },
            grid: { color: 'rgba(255, 255, 255, 0.2)' },
        },
        y1: {
            type: 'linear' as const,
            position: 'right' as const,
            ticks: { color: 'white' },
            grid: { drawOnChartArea: false },
        },
    },
}

const radarOptions = {
    ...commonChartOptions,
    scales: {
        r: {
            angleLines: { color: 'rgba(255, 255, 255, 0.2)' },
            grid: { color: 'rgba(255, 255, 255, 0.2)' },
            pointLabels: { color: 'white', font: { size: 14 } },
            ticks: { backdropColor: 'transparent', color: 'white' },
        },
    },
}

// ==================== 主組件實現 ====================
export const IntegratedAnalysisTabContent: React.FC = () => {
    const {
        loading,
        lastUpdate,
        currentStrategy,
        strategyLoading,
        switchStrategy,
        signalAnalysisRadarData,
        strategyComparisonData,
        realTimeSignalData,
        handoverLatencyData,
        constellationComparisonData,
        refreshAll,
    } = useIntegratedAnalysis(true)

    if (loading && !lastUpdate) {
        return <div className="p-4 text-center">正在加載首次數據...</div>
    }

    return (
        <div className="p-4 bg-gray-900 text-white min-h-screen">
            {/* ==================== 頁首控制項 ==================== */}
            <div className="flex justify-between items-center mb-4 p-4 bg-gray-800 rounded-lg shadow-lg">
                <div>
                    <h1 className="text-2xl font-bold text-green-400">
                        整合即時分析儀表板
                    </h1>
                    <p className="text-sm text-gray-400">
                        上次更新: {lastUpdate || 'N/A'}
                    </p>
                </div>
                <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                        <button
                            onClick={() => switchStrategy('flexible')}
                            disabled={
                                strategyLoading ||
                                currentStrategy === 'flexible'
                            }
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                                currentStrategy === 'flexible'
                                    ? 'bg-green-500 text-white'
                                    : 'bg-gray-700 hover:bg-gray-600'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            靈活換手
                        </button>
                        <button
                            onClick={() => switchStrategy('consistent')}
                            disabled={
                                strategyLoading ||
                                currentStrategy === 'consistent'
                            }
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                                currentStrategy === 'consistent'
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-700 hover:bg-gray-600'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            一致換手
                        </button>
                    </div>
                    <button
                        onClick={refreshAll}
                        disabled={loading}
                        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-md flex items-center space-x-2 transition-transform transform hover:scale-105 disabled:opacity-50"
                    >
                        {loading ? (
                            <svg
                                className="animate-spin h-5 w-5 text-white"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                ></circle>
                                <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8v8H4z"
                                ></path>
                            </svg>
                        ) : (
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="h-5 w-5"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                            >
                                <path
                                    fillRule="evenodd"
                                    d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.899 2.166l-1.581.892A5.002 5.002 0 005.56 6.303l-1.06.602v1.596a1 1 0 11-2 0V3a1 1 0 011-1zm12 1a1 1 0 011 1v6.398l-1.06.603a5.002 5.002 0 00-7.839-3.266l-1.581-.892A7.002 7.002 0 0115 5.101V3a1 1 0 011-1z"
                                    clipRule="evenodd"
                                />
                            </svg>
                        )}
                        <span>{loading ? '刷新中...' : '全部刷新'}</span>
                    </button>
                </div>
            </div>

            {/* ==================== 圖表網格 ==================== */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* 圖表1: 信號分析雷達圖 */}
                <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
                    <h2 className="text-lg font-semibold mb-2">
                        核心信號質量分析
                    </h2>
                    {signalAnalysisRadarData ? (
                        <Radar
                            data={signalAnalysisRadarData}
                            options={radarOptions}
                        />
                    ) : (
                        <ChartPlaceholder message="正在等待信號分析數據..." />
                    )}
                </div>

                {/* 圖表2: 策略效果對比 */}
                <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
                    <h2 className="text-lg font-semibold mb-2">
                        多方案策略效果對比
                    </h2>
                    {strategyComparisonData ? (
                        <Bar
                            data={strategyComparisonData}
                            options={dualYAxisOptions}
                        />
                    ) : (
                        <ChartPlaceholder message="正在等待策略效果數據..." />
                    )}
                </div>

                {/* 圖表3: 即時信號監控 */}
                <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
                    <h2 className="text-lg font-semibold mb-2">
                        即時信號強度與質量 (24H)
                    </h2>
                    {realTimeSignalData ? (
                        <Line
                            data={realTimeSignalData}
                            options={dualYAxisOptions}
                        />
                    ) : (
                        <ChartPlaceholder message="正在等待即時信號數據..." />
                    )}
                </div>

                {/* 圖表4: 換手延遲分析 */}
                <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
                    <h2 className="text-lg font-semibold mb-2">
                        換手延遲階段分析
                    </h2>
                    {handoverLatencyData ? (
                        <Bar
                            data={handoverLatencyData.data}
                            options={commonChartOptions}
                        />
                    ) : (
                        <ChartPlaceholder message="正在等待換手數據..." />
                    )}
                </div>

                {/* 圖表5: 星座性能對比 */}
                <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96">
                    <h2 className="text-lg font-semibold mb-2">
                        不同衛星星座性能對比
                    </h2>
                    {constellationComparisonData ? (
                        <Bar
                            data={constellationComparisonData.data}
                            options={commonChartOptions}
                        />
                    ) : (
                        <ChartPlaceholder message="正在等待星座數據..." />
                    )}
                </div>

                {/* 更多圖表可以按此模式添加 */}
                <div className="bg-gray-800 p-4 rounded-lg shadow-lg h-96 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                        <h2 className="text-lg font-semibold mb-2">
                            歷史策略性能軌跡
                        </h2>
                        <p>
                            (此圖表已在重構中移除，因其依賴不可靠的模擬數據。)
                        </p>
                        <p className="text-sm mt-2">可基於真實數據重新實現。</p>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default IntegratedAnalysisTabContent
