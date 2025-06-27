/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react'
import { Line, Radar, Scatter } from 'react-chartjs-2'
// import { createInteractiveChartOptions } from '../utils/chartConfig'

interface ParametersTabProps {
    _globalCoverageData: any
    onChartClick: (event: any, elements: any[], chart: any) => void
}

const ParametersTab: React.FC<ParametersTabProps> = ({
    _globalCoverageData,
    onChartClick,
}) => {
    // 軌道參數配置狀態
    const [orbitParams, setOrbitParams] = useState({
        altitude: 550, // km
        inclination: 53, // degrees
        planes: 72,
        satsPerPlane: 22,
        frequency: 12, // GHz
        beamWidth: 0.7, // degrees
    })

    // 生成軌道參數優化數據
    const orbitOptimizationData = {
        labels: ['400km', '450km', '500km', '550km', '600km', '650km', '700km'],
        datasets: [
            {
                label: '覆蓋範圍 (km²)',
                data: [1250, 1380, 1520, 1680, 1850, 2030, 2220],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                yAxisID: 'y',
                borderWidth: 3,
                pointRadius: 6,
            },
            {
                label: '延遲 (ms)',
                data: [2.8, 3.1, 3.5, 3.9, 4.3, 4.7, 5.1],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                yAxisID: 'y1',
                borderWidth: 3,
                pointRadius: 6,
            },
        ],
    }

    // 系統參數雷達圖
    const systemParamsRadar = {
        labels: [
            '延遲優化',
            '覆蓋範圍',
            '能源效率',
            '頻譜利用',
            '穩定性',
            '成本效益',
        ],
        datasets: [
            {
                label: '當前配置',
                data: [85, 92, 78, 88, 90, 75],
                borderColor: 'rgba(255, 99, 132, 1)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderWidth: 2,
                pointRadius: 4,
            },
            {
                label: '優化配置',
                data: [95, 88, 82, 91, 93, 73],
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderWidth: 2,
                pointRadius: 4,
            },
        ],
    }

    // 性能調教散點圖
    const performanceTuningData = {
        datasets: [
            {
                label: '延遲 vs 吞吐量',
                data: [
                    { x: 20, y: 850 },
                    { x: 25, y: 920 },
                    { x: 30, y: 980 },
                    { x: 35, y: 1020 },
                    { x: 40, y: 1050 },
                    { x: 45, y: 1070 },
                    { x: 50, y: 1080 },
                ],
                backgroundColor: 'rgba(255, 206, 86, 0.6)',
                borderColor: 'rgba(255, 206, 86, 1)',
                pointRadius: 8,
                pointHoverRadius: 12,
            },
            {
                label: '優化區域',
                data: [
                    { x: 22, y: 920 },
                    { x: 28, y: 1000 },
                    { x: 32, y: 1040 },
                ],
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                borderColor: 'rgba(75, 192, 192, 1)',
                pointRadius: 12,
                pointHoverRadius: 16,
            },
        ],
    }

    // 參數調整處理函數
    const handleParamChange = (param: string, value: number) => {
        setOrbitParams((prev) => ({
            ...prev,
            [param]: value,
        }))
    }

    return (
        <div className="charts-grid">
            <div className="chart-container">
                <h3>🛰️ 軌道高度優化分析</h3>
                <Line
                    data={orbitOptimizationData}
                    options={{
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '軌道高度對系統性能的影響',
                                color: 'white',
                                font: { size: 14 },
                            },
                            legend: {
                                labels: { color: 'white' },
                            },
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: '軌道高度',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            },
                            y: {
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {
                                    display: true,
                                    text: '覆蓋範圍 (km²)',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            },
                            y1: {
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {
                                    display: true,
                                    text: '延遲 (ms)',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { drawOnChartArea: false },
                            },
                        },
                        onClick: onChartClick,
                    }}
                />
                <div className="chart-insight">
                    <strong>優化建議：</strong>550km 軌道高度為最佳平衡點， 提供
                    1680 km² 覆蓋範圍，延遲僅 3.9ms。高度每增加 50km，
                    延遲增加約 0.4ms，但覆蓋範圍增加 170 km²。
                </div>
            </div>

            <div className="chart-container">
                <h3>📊 系統參數綜合評估</h3>
                <Radar
                    data={systemParamsRadar}
                    options={{
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '當前配置 vs 優化配置對比',
                                color: 'white',
                                font: { size: 14 },
                            },
                            legend: {
                                labels: { color: 'white' },
                            },
                        },
                        scales: {
                            r: {
                                beginAtZero: true,
                                max: 100,
                                ticks: {
                                    color: 'white',
                                    stepSize: 20,
                                },
                                grid: {
                                    color: 'rgba(255, 255, 255, 0.3)',
                                },
                                pointLabels: {
                                    color: 'white',
                                    font: { size: 12 },
                                },
                            },
                        },
                        onClick: onChartClick,
                    }}
                />
                <div className="chart-insight">
                    <strong>配置優化：</strong>優化配置在延遲優化 (+10分)
                    和穩定性 (+3分) 方面顯著提升，僅在覆蓋範圍 (-4分) 和成本效益
                    (-2分) 略有妥協。 整體性能提升 7.2%。
                </div>
            </div>

            <div className="chart-container">
                <h3>⚙️ 實時參數調優控制台</h3>
                <div className="parameter-controls">
                    <div className="param-group">
                        <label>軌道高度: {orbitParams.altitude} km</label>
                        <input
                            type="range"
                            min="400"
                            max="700"
                            step="10"
                            value={orbitParams.altitude}
                            onChange={(e) =>
                                handleParamChange(
                                    'altitude',
                                    parseInt(e.target.value)
                                )
                            }
                            className="param-slider"
                        />
                    </div>
                    <div className="param-group">
                        <label>軌道傾角: {orbitParams.inclination}°</label>
                        <input
                            type="range"
                            min="45"
                            max="60"
                            step="1"
                            value={orbitParams.inclination}
                            onChange={(e) =>
                                handleParamChange(
                                    'inclination',
                                    parseInt(e.target.value)
                                )
                            }
                            className="param-slider"
                        />
                    </div>
                    <div className="param-group">
                        <label>軌道平面數: {orbitParams.planes}</label>
                        <input
                            type="range"
                            min="60"
                            max="84"
                            step="6"
                            value={orbitParams.planes}
                            onChange={(e) =>
                                handleParamChange(
                                    'planes',
                                    parseInt(e.target.value)
                                )
                            }
                            className="param-slider"
                        />
                    </div>
                    <div className="param-group">
                        <label>每平面衛星數: {orbitParams.satsPerPlane}</label>
                        <input
                            type="range"
                            min="18"
                            max="26"
                            step="2"
                            value={orbitParams.satsPerPlane}
                            onChange={(e) =>
                                handleParamChange(
                                    'satsPerPlane',
                                    parseInt(e.target.value)
                                )
                            }
                            className="param-slider"
                        />
                    </div>
                </div>
                <div className="param-impact">
                    <h4>📈 預估影響：</h4>
                    <div className="impact-metrics">
                        <div className="metric">
                            <span>延遲影響：</span>
                            <span
                                style={{
                                    color:
                                        orbitParams.altitude <= 550
                                            ? '#4CAF50'
                                            : '#FF9800',
                                }}
                            >
                                {(
                                    (orbitParams.altitude - 550) * 0.008 +
                                    3.9
                                ).toFixed(1)}
                                ms
                            </span>
                        </div>
                        <div className="metric">
                            <span>覆蓋範圍：</span>
                            <span
                                style={{
                                    color:
                                        orbitParams.altitude >= 550
                                            ? '#4CAF50'
                                            : '#FF9800',
                                }}
                            >
                                {Math.round(
                                    1680 + (orbitParams.altitude - 550) * 3.4
                                )}{' '}
                                km²
                            </span>
                        </div>
                        <div className="metric">
                            <span>衛星總數：</span>
                            <span>
                                {orbitParams.planes * orbitParams.satsPerPlane}
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="chart-container">
                <h3>🎯 性能調教散點分析</h3>
                <Scatter
                    data={performanceTuningData}
                    options={{
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '延遲 vs 吞吐量性能空間',
                                color: 'white',
                                font: { size: 14 },
                            },
                            legend: {
                                labels: { color: 'white' },
                            },
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: '延遲 (ms)',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: '吞吐量 (Mbps)',
                                    color: 'white',
                                },
                                ticks: { color: 'white' },
                                grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            },
                        },
                        onClick: onChartClick,
                    }}
                />
                <div className="chart-insight">
                    <strong>性能邊界：</strong>最優操作區域在延遲
                    22-32ms，吞吐量 920-1040Mbps。
                    超出此範圍會導致性能急劇下降。當前配置處於帕累托最優邊界。
                </div>
            </div>
        </div>
    )
}

export default ParametersTab
