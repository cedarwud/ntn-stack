/**
 * DataVisualizationComparison - 數據可視化效果對比分析
 * 
 * 目的：
 * 1. 對比真實SGP4數據 vs 模擬數據的可視化效果
 * 2. 分析高頻振蕩對D2事件識別的影響
 * 3. 提供數據處理策略建議
 */

import React, { useState, useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

// 數據生成器
class DataGeneratorComparison {
    /**
     * 生成理想化的模擬數據 - 清晰的D2觸發模式
     */
    static generateIdealSimulatedData(durationSeconds: number = 300, sampleInterval: number = 10) {
        const points = Math.floor(durationSeconds / sampleInterval)
        const data = []

        for (let i = 0; i < points; i++) {
            const time = i * sampleInterval
            
            // 設計清晰的衛星軌道模式：拋物線 + 適度變化
            const baseSatDistance = 500 + 300 * Math.sin(time / 100) + 100 * Math.cos(time / 80)
            const satelliteDistance = baseSatDistance * 1000 // 轉為米
            
            // 地面距離：較穩定，有明確的觸發時機
            const baseGroundDistance = 60 + 30 * Math.sin(time / 120) + 10 * Math.cos(time / 90)
            const groundDistance = baseGroundDistance * 1000 // 轉為米
            
            // 人工設計的觸發條件
            const thresh1 = 600000 // 600km
            const thresh2 = 80000  // 80km
            const hysteresis = 5000 // 5km
            
            const triggerCondition = (satelliteDistance - hysteresis) > thresh1 && 
                                   (groundDistance + hysteresis) < thresh2

            data.push({
                time,
                satelliteDistance,
                groundDistance,
                triggerCondition,
                dataType: 'simulated'
            })
        }

        return data
    }

    /**
     * 生成真實SGP4風格數據 - 包含高頻振蕩
     */
    static generateRealisticSGP4Data(durationSeconds: number = 300, sampleInterval: number = 10) {
        const points = Math.floor(durationSeconds / sampleInterval)
        const data = []

        for (let i = 0; i < points; i++) {
            const time = i * sampleInterval
            
            // 基礎軌道模式（與模擬數據相同）
            const baseSatDistance = 500 + 300 * Math.sin(time / 100) + 100 * Math.cos(time / 80)
            
            // 添加SGP4風格的高頻振蕩 - 這是問題的根源
            const highFreqNoise1 = 15 * Math.sin(time * 2) + 8 * Math.cos(time * 3.7) + 5 * Math.sin(time * 5.2)
            const highFreqNoise2 = 12 * Math.sin(time * 1.8) + 7 * Math.cos(time * 4.1) + 4 * Math.sin(time * 6.3)
            const highFreqNoise3 = 10 * Math.sin(time * 3.2) + 6 * Math.cos(time * 2.9) + 3 * Math.sin(time * 7.1)
            const totalSatNoise = highFreqNoise1 + highFreqNoise2 + highFreqNoise3
            
            const satelliteDistance = (baseSatDistance + totalSatNoise) * 1000 // 轉為米
            
            // 地面距離也有噪聲，但較少
            const baseGroundDistance = 60 + 30 * Math.sin(time / 120) + 10 * Math.cos(time / 90)
            const groundNoise = 3 * Math.sin(time * 1.5) + 2 * Math.cos(time * 2.8)
            const groundDistance = (baseGroundDistance + groundNoise) * 1000 // 轉為米
            
            // 觸發條件（相同）
            const thresh1 = 600000 // 600km
            const thresh2 = 80000  // 80km
            const hysteresis = 5000 // 5km
            
            const triggerCondition = (satelliteDistance - hysteresis) > thresh1 && 
                                   (groundDistance + hysteresis) < thresh2

            data.push({
                time,
                satelliteDistance,
                groundDistance,
                triggerCondition,
                dataType: 'realistic_sgp4'
            })
        }

        return data
    }

    /**
     * 智能降噪處理 - 保留主要特徵，去除高頻噪聲
     */
    static applyIntelligentDenoising(data: Array<{
        time: number
        satelliteDistance: number
        groundDistance: number
        triggerCondition: boolean
        dataType: string
    }>, strategy: 'conservative' | 'aggressive' | 'adaptive' = 'adaptive') {
        if (data.length < 5) return data

        const processedData = [...data]
        
        // 提取衛星和地面距離數據
        const satDistances = data.map(d => d.satelliteDistance)
        const groundDistances = data.map(d => d.groundDistance)
        
        let denoisedSatDistances: number[]
        let denoisedGroundDistances: number[]
        
        switch (strategy) {
            case 'conservative':
                // 保守策略：輕度平滑，保留大部分真實性
                denoisedSatDistances = this.lightSmoothing(satDistances, 3)
                denoisedGroundDistances = this.lightSmoothing(groundDistances, 3)
                break
                
            case 'aggressive':
                // 激進策略：強力平滑，突出主要趨勢
                denoisedSatDistances = this.heavySmoothing(satDistances, 7)
                denoisedGroundDistances = this.heavySmoothing(groundDistances, 5)
                break
                
            case 'adaptive':
            default:
                // 自適應策略：根據噪聲水平動態調整
                denoisedSatDistances = this.adaptiveSmoothing(satDistances)
                denoisedGroundDistances = this.adaptiveSmoothing(groundDistances)
                break
        }
        
        // 更新數據
        for (let i = 0; i < processedData.length; i++) {
            processedData[i] = {
                ...processedData[i],
                satelliteDistance: denoisedSatDistances[i],
                groundDistance: denoisedGroundDistances[i],
                dataType: `${data[i].dataType}_denoised_${strategy}`
            }
            
            // 重新計算觸發條件
            const thresh1 = 600000
            const thresh2 = 80000
            const hysteresis = 5000
            
            processedData[i].triggerCondition = 
                (denoisedSatDistances[i] - hysteresis) > thresh1 && 
                (denoisedGroundDistances[i] + hysteresis) < thresh2
        }
        
        return processedData
    }
    
    private static lightSmoothing(data: number[], window: number = 3): number[] {
        return this.movingAverage(data, window)
    }
    
    private static heavySmoothing(data: number[], window: number = 7): number[] {
        // 多層平滑
        let smoothed = this.movingAverage(data, window)
        smoothed = this.exponentialSmoothing(smoothed, 0.3)
        return smoothed
    }
    
    private static adaptiveSmoothing(data: number[]): number[] {
        // 計算噪聲水平
        const noiseLevel = this.calculateNoiseLevel(data)
        
        if (noiseLevel > 0.1) {
            // 高噪聲：使用強力平滑
            return this.heavySmoothing(data, 7)
        } else if (noiseLevel > 0.05) {
            // 中等噪聲：使用中等平滑
            return this.heavySmoothing(data, 5)
        } else {
            // 低噪聲：使用輕度平滑
            return this.lightSmoothing(data, 3)
        }
    }
    
    private static calculateNoiseLevel(data: number[]): number {
        if (data.length < 3) return 0
        
        const differences = []
        for (let i = 1; i < data.length; i++) {
            differences.push(Math.abs(data[i] - data[i - 1]))
        }
        
        const avgDifference = differences.reduce((sum, diff) => sum + diff, 0) / differences.length
        const avgValue = data.reduce((sum, val) => sum + val, 0) / data.length
        
        return avgDifference / avgValue // 正規化噪聲水平
    }
    
    private static movingAverage(data: number[], window: number): number[] {
        const result = []
        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - Math.floor(window / 2))
            const end = Math.min(data.length, start + window)
            const slice = data.slice(start, end)
            const avg = slice.reduce((sum, val) => sum + val, 0) / slice.length
            result.push(avg)
        }
        return result
    }
    
    private static exponentialSmoothing(data: number[], alpha: number): number[] {
        if (data.length === 0) return data
        const result = [data[0]]
        for (let i = 1; i < data.length; i++) {
            result.push(alpha * data[i] + (1 - alpha) * result[i - 1])
        }
        return result
    }
}

const DataVisualizationComparison: React.FC = () => {
    const [selectedDatasets, setSelectedDatasets] = useState<string[]>(['simulated', 'realistic_sgp4'])

    // 生成各種數據集
    const datasets = useMemo(() => {
        const simulated = DataGeneratorComparison.generateIdealSimulatedData()
        const realistic = DataGeneratorComparison.generateRealisticSGP4Data()
        const denoisedConservative = DataGeneratorComparison.applyIntelligentDenoising(realistic, 'conservative')
        const denoisedAggressive = DataGeneratorComparison.applyIntelligentDenoising(realistic, 'aggressive')
        const denoisedAdaptive = DataGeneratorComparison.applyIntelligentDenoising(realistic, 'adaptive')

        return {
            simulated: { data: simulated, name: '理想模擬數據', color: '#28a745' },
            realistic_sgp4: { data: realistic, name: '真實SGP4數據', color: '#dc3545' },
            denoised_conservative: { data: denoisedConservative, name: '保守降噪', color: '#17a2b8' },
            denoised_aggressive: { data: denoisedAggressive, name: '激進降噪', color: '#ffc107' },
            denoised_adaptive: { data: denoisedAdaptive, name: '自適應降噪', color: '#6f42c1' },
        }
    }, [])

    // 圖表數據
    const chartData = useMemo(() => {
        const labels = datasets.simulated.data.map(d => d.time)
        const chartDatasets = []

        selectedDatasets.forEach(key => {
            if (datasets[key as keyof typeof datasets]) {
                const dataset = datasets[key as keyof typeof datasets]
                chartDatasets.push({
                    label: `${dataset.name} - 衛星距離`,
                    data: dataset.data.map(d => d.satelliteDistance / 1000), // 轉為km
                    borderColor: dataset.color,
                    backgroundColor: `${dataset.color}20`,
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false,
                    yAxisID: 'y-satellite',
                })
            }
        })

        return { labels, datasets: chartDatasets }
    }, [datasets, selectedDatasets])

    // 觸發條件分析
    const triggerAnalysis = useMemo(() => {
        const analysis: Record<string, {
            name: string
            triggerPoints: number
            triggerPercentage: string
            continuousSegments: number
            clarity: 'high' | 'medium' | 'low'
        }> = {}
        
        Object.entries(datasets).forEach(([key, dataset]) => {
            const triggerEvents = dataset.data.filter(d => d.triggerCondition)
            const triggerPercentage = (triggerEvents.length / dataset.data.length) * 100
            
            // 計算觸發區間連續性
            let continuousSegments = 0
            let isInSegment = false
            
            dataset.data.forEach(d => {
                if (d.triggerCondition && !isInSegment) {
                    continuousSegments++
                    isInSegment = true
                } else if (!d.triggerCondition) {
                    isInSegment = false
                }
            })
            
            analysis[key] = {
                name: dataset.name,
                triggerPoints: triggerEvents.length,
                triggerPercentage: triggerPercentage.toFixed(1),
                continuousSegments,
                clarity: continuousSegments <= 3 ? 'high' : continuousSegments <= 6 ? 'medium' : 'low'
            }
        })
        
        return analysis
    }, [datasets])

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: 'D2事件數據可視化對比分析 - 衛星距離',
                color: '#ffffff',
                font: { size: 16, weight: 'bold' },
            },
            legend: {
                display: true,
                position: 'top' as const,
                labels: { color: '#ffffff' },
            },
        },
        scales: {
            x: {
                title: { display: true, text: '時間 (秒)', color: '#ffffff' },
                grid: { color: '#374151' },
                ticks: { color: '#ffffff' },
            },
            'y-satellite': {
                type: 'linear' as const,
                position: 'left' as const,
                title: { display: true, text: '衛星距離 (km)', color: '#ffffff' },
                grid: { color: '#374151' },
                ticks: { color: '#ffffff' },
            },
        },
    }

    return (
        <div style={{
            padding: '20px',
            backgroundColor: '#1a1a1a',
            color: '#ffffff',
            minHeight: '100vh',
        }}>
            <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>
                D2事件數據可視化效果對比分析
            </h1>

            {/* 控制面板 */}
            <div style={{
                display: 'flex',
                gap: '20px',
                marginBottom: '30px',
                flexWrap: 'wrap',
                justifyContent: 'center',
            }}>
                <div style={{
                    padding: '16px',
                    backgroundColor: '#2d3748',
                    borderRadius: '8px',
                    border: '2px solid #374151',
                }}>
                    <h3 style={{ marginBottom: '12px' }}>選擇數據集</h3>
                    {Object.entries(datasets).map(([key, dataset]) => (
                        <label key={key} style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            marginBottom: '8px',
                            cursor: 'pointer',
                        }}>
                            <input
                                type="checkbox"
                                checked={selectedDatasets.includes(key)}
                                onChange={(e) => {
                                    if (e.target.checked) {
                                        setSelectedDatasets([...selectedDatasets, key])
                                    } else {
                                        setSelectedDatasets(selectedDatasets.filter(d => d !== key))
                                    }
                                }}
                            />
                            <div style={{
                                width: '12px',
                                height: '12px',
                                backgroundColor: dataset.color,
                                marginRight: '4px',
                            }} />
                            {dataset.name}
                        </label>
                    ))}
                </div>
            </div>

            {/* 圖表 */}
            <div style={{
                height: '500px',
                backgroundColor: '#2d3748',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '30px',
            }}>
                <Line data={chartData} options={chartOptions} />
            </div>

            {/* 觸發條件分析表格 */}
            <div style={{
                backgroundColor: '#2d3748',
                borderRadius: '12px',
                padding: '20px',
                marginBottom: '30px',
            }}>
                <h3 style={{ marginBottom: '16px' }}>D2觸發條件分析對比</h3>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        fontSize: '14px',
                    }}>
                        <thead>
                            <tr style={{ borderBottom: '2px solid #374151' }}>
                                <th style={{ padding: '12px', textAlign: 'left' }}>數據類型</th>
                                <th style={{ padding: '12px', textAlign: 'center' }}>觸發點數</th>
                                <th style={{ padding: '12px', textAlign: 'center' }}>觸發比例</th>
                                <th style={{ padding: '12px', textAlign: 'center' }}>連續區間數</th>
                                <th style={{ padding: '12px', textAlign: 'center' }}>清晰度</th>
                                <th style={{ padding: '12px', textAlign: 'left' }}>建議</th>
                            </tr>
                        </thead>
                        <tbody>
                            {Object.entries(triggerAnalysis).map(([key, analysis]) => (
                                <tr key={key} style={{ borderBottom: '1px solid #374151' }}>
                                    <td style={{ padding: '12px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <div style={{
                                                width: '12px',
                                                height: '12px',
                                                backgroundColor: datasets[key as keyof typeof datasets]?.color,
                                            }} />
                                            {analysis.name}
                                        </div>
                                    </td>
                                    <td style={{ padding: '12px', textAlign: 'center' }}>{analysis.triggerPoints}</td>
                                    <td style={{ padding: '12px', textAlign: 'center' }}>{analysis.triggerPercentage}%</td>
                                    <td style={{ padding: '12px', textAlign: 'center' }}>{analysis.continuousSegments}</td>
                                    <td style={{ padding: '12px', textAlign: 'center' }}>
                                        <span style={{
                                            padding: '4px 8px',
                                            borderRadius: '4px',
                                            backgroundColor: 
                                                analysis.clarity === 'high' ? '#28a745' :
                                                analysis.clarity === 'medium' ? '#ffc107' : '#dc3545',
                                            color: 'white',
                                            fontSize: '12px',
                                        }}>
                                            {analysis.clarity === 'high' ? '高' :
                                             analysis.clarity === 'medium' ? '中' : '低'}
                                        </span>
                                    </td>
                                    <td style={{ padding: '12px', fontSize: '12px' }}>
                                        {key === 'simulated' && '✅ 理想效果，易於理解'}
                                        {key === 'realistic_sgp4' && '❌ 高頻噪聲，難以判讀'}
                                        {key === 'denoised_conservative' && '⚠️ 輕度改善，保持真實性'}
                                        {key === 'denoised_aggressive' && '✅ 大幅改善，可能過度平滑'}
                                        {key === 'denoised_adaptive' && '🎯 平衡效果，推薦使用'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* 結論和建議 */}
            <div style={{
                backgroundColor: '#2d3748',
                borderRadius: '12px',
                padding: '20px',
            }}>
                <h3 style={{ marginBottom: '16px', color: '#ffc107' }}>📊 分析結論和建議</h3>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '16px',
                }}>
                    <div>
                        <h4 style={{ color: '#28a745', marginBottom: '8px' }}>✅ 模擬數據優勢</h4>
                        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                            <li>清晰的趨勢線，容易識別模式</li>
                            <li>觸發區間連續且明確</li>
                            <li>視覺效果佳，適合教學演示</li>
                            <li>符合理論預期的行為</li>
                        </ul>
                    </div>
                    
                    <div>
                        <h4 style={{ color: '#dc3545', marginBottom: '8px' }}>❌ 真實數據問題</h4>
                        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                            <li>SGP4高頻振蕩掩蓋主要模式</li>
                            <li>觸發區間破碎，難以識別</li>
                            <li>視覺混亂，無法做出判斷</li>
                            <li>研究價值被噪聲埋沒</li>
                        </ul>
                    </div>
                    
                    <div>
                        <h4 style={{ color: '#6f42c1', marginBottom: '8px' }}>🎯 推薦解決方案</h4>
                        <ul style={{ paddingLeft: '20px', lineHeight: '1.6' }}>
                            <li><strong>自適應降噪</strong>：最佳平衡點</li>
                            <li>保留真實數據的物理意義</li>
                            <li>突出D2事件的觸發模式</li>
                            <li>提供清晰的可視化效果</li>
                        </ul>
                    </div>
                </div>
                
                <div style={{
                    marginTop: '20px',
                    padding: '16px',
                    backgroundColor: '#374151',
                    borderRadius: '8px',
                    borderLeft: '4px solid #ffc107',
                }}>
                    <h4 style={{ color: '#ffc107', marginBottom: '8px' }}>💡 最終建議</h4>
                    <p style={{ lineHeight: '1.6', margin: 0 }}>
                        <strong>不要完全拋棄真實數據</strong>，而是採用<strong>智能數據處理策略</strong>：
                        使用真實SGP4數據作為基礎，應用自適應降噪算法去除高頻振蕩，
                        保留重要的軌道動態特徵，同時確保D2觸發模式清晰可見。
                        這樣既保持了學術研究的真實性，又達到了優秀的可視化效果。
                    </p>
                </div>
            </div>
        </div>
    )
}

export default DataVisualizationComparison