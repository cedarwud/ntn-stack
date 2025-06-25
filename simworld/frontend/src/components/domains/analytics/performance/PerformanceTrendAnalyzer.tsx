import React, { useState, useEffect } from 'react'
import * as THREE from 'three'
import { Text, Line } from '@react-three/drei'

interface PerformanceTrendAnalyzerProps {
    devices: any[]
    enabled: boolean
}

interface PerformanceDataPoint {
    timestamp: number
    systemLatency: number
    throughput: number
    cpuUsage: number
    memoryUsage: number
    errorRate: number
    responseTime: number
    activeConnections: number
    networkBandwidth: number
}

interface TrendAnalysis {
    metric: string
    trend: 'improving' | 'stable' | 'degrading'
    changePercent: number
    prediction: number
    confidence: number
    recommendation: string
}

interface PerformanceAlert {
    id: string
    metric: string
    severity: 'critical' | 'warning' | 'info'
    threshold: number
    currentValue: number
    timestamp: number
    description: string
}

const PerformanceTrendAnalyzer: React.FC<PerformanceTrendAnalyzerProps> = ({ devices, enabled }) => {
    const [performanceData, setPerformanceData] = useState<PerformanceDataPoint[]>([])
    const [trendAnalysis, setTrendAnalysis] = useState<TrendAnalysis[]>([])
    const [alerts, setAlerts] = useState<PerformanceAlert[]>([])
    const [selectedMetric, setSelectedMetric] = useState<string>('systemLatency')
    const [timeWindow, setTimeWindow] = useState<'1h' | '6h' | '24h' | '7d'>('1h')

    // 模擬性能數據生成
    useEffect(() => {
        if (!enabled) {
            setPerformanceData([])
            setTrendAnalysis([])
            setAlerts([])
            return
        }

        const generatePerformanceData = () => {
            const now = Date.now()
            const dataPoints: PerformanceDataPoint[] = []

            // 生成歷史數據點（最近1小時，每分鐘一個點）
            for (let i = 60; i >= 0; i--) {
                const timestamp = now - (i * 60 * 1000)
                const baseLatency = 25 + Math.sin(i / 10) * 5
                const baseThroughput = 1000 + Math.cos(i / 8) * 200
                
                dataPoints.push({
                    timestamp,
                    systemLatency: Math.max(10, baseLatency + Math.random() * 10 - 5),
                    throughput: Math.max(500, baseThroughput + Math.random() * 100 - 50),
                    cpuUsage: Math.max(20, 45 + Math.sin(i / 15) * 15 + Math.random() * 10 - 5),
                    memoryUsage: Math.max(30, 60 + Math.cos(i / 12) * 10 + Math.random() * 8 - 4),
                    errorRate: Math.max(0, 1 + Math.sin(i / 20) * 0.5 + Math.random() * 0.5 - 0.25),
                    responseTime: Math.max(50, 80 + Math.sin(i / 8) * 20 + Math.random() * 15 - 7.5),
                    activeConnections: Math.max(50, 200 + Math.cos(i / 10) * 50 + Math.random() * 20 - 10),
                    networkBandwidth: Math.max(100, 500 + Math.sin(i / 7) * 100 + Math.random() * 50 - 25)
                })
            }

            setPerformanceData(dataPoints)

            // 生成趨勢分析
            const metrics = ['systemLatency', 'throughput', 'cpuUsage', 'memoryUsage', 'errorRate', 'responseTime']
            const trends: TrendAnalysis[] = metrics.map(metric => {
                const recentValues = dataPoints.slice(-10).map(d => d[metric as keyof PerformanceDataPoint] as number)
                const olderValues = dataPoints.slice(-20, -10).map(d => d[metric as keyof PerformanceDataPoint] as number)
                
                const recentAvg = recentValues.reduce((sum, val) => sum + val, 0) / recentValues.length
                const olderAvg = olderValues.reduce((sum, val) => sum + val, 0) / olderValues.length
                
                const changePercent = ((recentAvg - olderAvg) / olderAvg) * 100
                
                let trend: 'improving' | 'stable' | 'degrading'
                if (Math.abs(changePercent) < 2) {
                    trend = 'stable'
                } else if (metric === 'throughput') {
                    trend = changePercent > 0 ? 'improving' : 'degrading'
                } else {
                    trend = changePercent < 0 ? 'improving' : 'degrading'
                }

                const prediction = recentAvg + (recentAvg - olderAvg) * 2 // 簡單線性預測
                const confidence = Math.max(60, 90 - Math.abs(changePercent) * 2)

                return {
                    metric: getMetricDisplayName(metric),
                    trend,
                    changePercent,
                    prediction,
                    confidence,
                    recommendation: getRecommendation(metric, trend, changePercent)
                }
            })

            setTrendAnalysis(trends)

            // 生成性能告警
            const newAlerts: PerformanceAlert[] = []
            const latestData = dataPoints[dataPoints.length - 1]

            if (latestData.systemLatency > 40) {
                newAlerts.push({
                    id: 'latency_alert',
                    metric: '系統延遲',
                    severity: latestData.systemLatency > 60 ? 'critical' : 'warning',
                    threshold: 40,
                    currentValue: latestData.systemLatency,
                    timestamp: latestData.timestamp,
                    description: '系統延遲超過預期閾值，可能影響用戶體驗'
                })
            }

            if (latestData.cpuUsage > 80) {
                newAlerts.push({
                    id: 'cpu_alert',
                    metric: 'CPU 使用率',
                    severity: latestData.cpuUsage > 90 ? 'critical' : 'warning',
                    threshold: 80,
                    currentValue: latestData.cpuUsage,
                    timestamp: latestData.timestamp,
                    description: 'CPU 使用率過高，建議檢查系統負載'
                })
            }

            if (latestData.errorRate > 2) {
                newAlerts.push({
                    id: 'error_alert',
                    metric: '錯誤率',
                    severity: latestData.errorRate > 5 ? 'critical' : 'warning',
                    threshold: 2,
                    currentValue: latestData.errorRate,
                    timestamp: latestData.timestamp,
                    description: '錯誤率異常升高，需要立即檢查'
                })
            }

            setAlerts(newAlerts)
        }

        const getMetricDisplayName = (metric: string): string => {
            const names: { [key: string]: string } = {
                systemLatency: '系統延遲',
                throughput: '系統吞吐量',
                cpuUsage: 'CPU 使用率',
                memoryUsage: '記憶體使用率',
                errorRate: '錯誤率',
                responseTime: 'API 響應時間'
            }
            return names[metric] || metric
        }

        const getRecommendation = (metric: string, trend: string, changePercent: number): string => {
            const recommendations: { [key: string]: { [key: string]: string } } = {
                systemLatency: {
                    improving: '延遲持續改善，保持當前最佳化策略',
                    stable: '延遲穩定，監控是否有突發狀況',
                    degrading: '延遲惡化，建議檢查網路和資料庫連接'
                },
                throughput: {
                    improving: '吞吐量提升，系統性能表現良好',
                    stable: '吞吐量穩定，維持當前配置',
                    degrading: '吞吐量下降，檢查系統瓶頸和資源分配'
                },
                cpuUsage: {
                    improving: 'CPU 使用率下降，資源利用更有效率',
                    stable: 'CPU 使用率穩定，監控是否有突增',
                    degrading: 'CPU 使用率上升，考慮擴展計算資源'
                }
            }
            return recommendations[metric]?.[trend] || '持續監控該指標變化'
        }

        generatePerformanceData()
        const interval = setInterval(generatePerformanceData, 30000) // 30秒更新

        return () => clearInterval(interval)
    }, [enabled])

    if (!enabled) return null

    const getTrendColor = (trend: string): string => {
        switch (trend) {
            case 'improving': return '#2ed573'
            case 'stable': return '#3742fa'
            case 'degrading': return '#ff4757'
            default: return '#747d8c'
        }
    }

    const getSeverityColor = (severity: string): string => {
        switch (severity) {
            case 'critical': return '#ff4757'
            case 'warning': return '#ffa502'
            case 'info': return '#3742fa'
            default: return '#2ed573'
        }
    }

    const normalizeDataForVisualization = (data: number[], min: number, max: number): number[] => {
        const dataMin = Math.min(...data)
        const dataMax = Math.max(...data)
        const range = dataMax - dataMin || 1
        return data.map(value => min + ((value - dataMin) / range) * (max - min))
    }

    // 準備圖表數據
    const chartData = performanceData.slice(-20) // 最近20個數據點
    const selectedMetricData = chartData.map(d => d[selectedMetric as keyof PerformanceDataPoint] as number)
    const normalizedData = normalizeDataForVisualization(selectedMetricData, -10, 10)

    // 生成趨勢線點
    const trendLinePoints: [number, number, number][] = normalizedData.map((value, index) => [
        index * 4 - 38, // X軸：從-38到38
        value,          // Y軸：正規化後的值
        0               // Z軸：固定為0
    ])

    return (
        <>
            {/* 趨勢分析總覽 */}
            <group position={[-120, 100, 0]}>
                <Text
                    position={[0, 25, 0]}
                    fontSize={8}
                    color="#ffd700"
                    anchorX="center"
                    anchorY="middle"
                >
                    📈 性能趨勢分析
                </Text>

                <Text
                    position={[0, 18, 0]}
                    fontSize={4}
                    color="#ffffff"
                    anchorX="center"
                    anchorY="middle"
                >
                    時間窗口: {timeWindow}
                </Text>

                <Text
                    position={[0, 14, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    數據點: {performanceData.length}
                </Text>

                <Text
                    position={[0, 10, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    告警數: {alerts.length}
                </Text>
            </group>

            {/* 主要趨勢圖表 */}
            <group position={[0, 50, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={6}
                    color="#00d4ff"
                    anchorX="center"
                    anchorY="middle"
                >
                    📊 {selectedMetric === 'systemLatency' ? '系統延遲' : 
                         selectedMetric === 'throughput' ? '系統吞吐量' :
                         selectedMetric === 'cpuUsage' ? 'CPU 使用率' :
                         selectedMetric === 'memoryUsage' ? '記憶體使用率' :
                         selectedMetric === 'errorRate' ? '錯誤率' : 'API 響應時間'} 趨勢
                </Text>

                {/* 趨勢線 */}
                {trendLinePoints.length > 1 && (
                    <Line
                        points={trendLinePoints}
                        color="#00d4ff"
                        lineWidth={3}
                    />
                )}

                {/* 數據點 */}
                {trendLinePoints.map((point, index) => (
                    <mesh key={index} position={point}>
                        <sphereGeometry args={[0.8, 8, 8]} />
                        <meshStandardMaterial
                            color="#00d4ff"
                            emissive="#00d4ff"
                            emissiveIntensity={0.3}
                        />
                    </mesh>
                ))}

                {/* X軸 */}
                <Line
                    points={[[-40, -15, 0], [40, -15, 0]]}
                    color="#666666"
                    lineWidth={1}
                />

                {/* Y軸 */}
                <Line
                    points={[[-40, -15, 0], [-40, 15, 0]]}
                    color="#666666"
                    lineWidth={1}
                />

                {/* 軸標籤 */}
                <Text
                    position={[0, -18, 0]}
                    fontSize={2}
                    color="#999999"
                    anchorX="center"
                    anchorY="middle"
                >
                    時間軸 (最近20個數據點)
                </Text>

                <Text
                    position={[-45, 0, 0]}
                    fontSize={2}
                    color="#999999"
                    anchorX="center"
                    anchorY="middle"
                    rotation={[0, 0, Math.PI / 2]}
                >
                    指標值
                </Text>
            </group>

            {/* 趨勢分析結果 */}
            <group position={[120, 80, 0]}>
                <Text
                    position={[0, 25, 0]}
                    fontSize={6}
                    color="#ff8800"
                    anchorX="center"
                    anchorY="middle"
                >
                    🔍 趨勢分析
                </Text>

                {trendAnalysis.slice(0, 6).map((analysis, index) => (
                    <group key={analysis.metric} position={[0, 18 - index * 6, 0]}>
                        <Text
                            position={[-15, 2, 0]}
                            fontSize={2.5}
                            color="#ffffff"
                            anchorX="left"
                            anchorY="middle"
                        >
                            {analysis.metric}
                        </Text>

                        <mesh position={[0, 0, 0]}>
                            <boxGeometry args={[3, 1.5, 1]} />
                            <meshStandardMaterial
                                color={getTrendColor(analysis.trend)}
                                emissive={getTrendColor(analysis.trend)}
                                emissiveIntensity={0.2}
                            />
                        </mesh>

                        <Text
                            position={[15, 2, 0]}
                            fontSize={2}
                            color={getTrendColor(analysis.trend)}
                            anchorX="right"
                            anchorY="middle"
                        >
                            {analysis.changePercent > 0 ? '+' : ''}{analysis.changePercent.toFixed(1)}%
                        </Text>

                        <Text
                            position={[15, -1, 0]}
                            fontSize={1.5}
                            color="#cccccc"
                            anchorX="right"
                            anchorY="middle"
                        >
                            信心度: {analysis.confidence.toFixed(0)}%
                        </Text>
                    </group>
                ))}
            </group>

            {/* 性能告警 */}
            <group position={[-120, -20, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={6}
                    color="#ff4757"
                    anchorX="center"
                    anchorY="middle"
                >
                    🚨 性能告警
                </Text>

                {alerts.length === 0 ? (
                    <Text
                        position={[0, 10, 0]}
                        fontSize={4}
                        color="#2ed573"
                        anchorX="center"
                        anchorY="middle"
                    >
                        ✅ 目前沒有告警
                    </Text>
                ) : (
                    alerts.map((alert, index) => (
                        <group key={alert.id} position={[0, 12 - index * 8, 0]}>
                            <mesh position={[-20, 0, 0]}>
                                <boxGeometry args={[2, 2, 2]} />
                                <meshStandardMaterial
                                    color={getSeverityColor(alert.severity)}
                                    emissive={getSeverityColor(alert.severity)}
                                    emissiveIntensity={0.5}
                                />
                            </mesh>

                            <Text
                                position={[-15, 2, 0]}
                                fontSize={3}
                                color="#ffffff"
                                anchorX="left"
                                anchorY="middle"
                            >
                                {alert.metric}
                            </Text>

                            <Text
                                position={[-15, -1, 0]}
                                fontSize={2}
                                color={getSeverityColor(alert.severity)}
                                anchorX="left"
                                anchorY="middle"
                            >
                                {alert.severity.toUpperCase()}
                            </Text>

                            <Text
                                position={[20, 2, 0]}
                                fontSize={2.5}
                                color="#ffffff"
                                anchorX="right"
                                anchorY="middle"
                            >
                                {alert.currentValue.toFixed(1)} / {alert.threshold}
                            </Text>

                            <Text
                                position={[20, -1, 0]}
                                fontSize={1.8}
                                color="#cccccc"
                                anchorX="right"
                                anchorY="middle"
                            >
                                {new Date(alert.timestamp).toLocaleTimeString()}
                            </Text>
                        </group>
                    ))
                )}
            </group>

            {/* 性能預測 */}
            <group position={[120, -20, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={6}
                    color="#3742fa"
                    anchorX="center"
                    anchorY="middle"
                >
                    🔮 性能預測
                </Text>

                {trendAnalysis.slice(0, 4).map((analysis, index) => (
                    <group key={`prediction_${analysis.metric}`} position={[0, 12 - index * 6, 0]}>
                        <Text
                            position={[-20, 1, 0]}
                            fontSize={2.5}
                            color="#ffffff"
                            anchorX="left"
                            anchorY="middle"
                        >
                            {analysis.metric}
                        </Text>

                        <Text
                            position={[20, 1, 0]}
                            fontSize={2.5}
                            color={getTrendColor(analysis.trend)}
                            anchorX="right"
                            anchorY="middle"
                        >
                            {analysis.prediction.toFixed(1)}
                        </Text>

                        <Text
                            position={[20, -2, 0]}
                            fontSize={1.5}
                            color="#999999"
                            anchorX="right"
                            anchorY="middle"
                        >
                            未來30分鐘預測
                        </Text>
                    </group>
                ))}
            </group>

            {/* 優化建議 */}
            <group position={[0, -80, 0]}>
                <Text
                    position={[0, 15, 0]}
                    fontSize={6}
                    color="#2ed573"
                    anchorX="center"
                    anchorY="middle"
                >
                    💡 優化建議
                </Text>

                {trendAnalysis
                    .filter(analysis => analysis.trend === 'degrading')
                    .slice(0, 3)
                    .map((analysis, index) => (
                        <Text
                            key={`recommendation_${analysis.metric}`}
                            position={[0, 8 - index * 4, 0]}
                            fontSize={2.5}
                            color="#ffffff"
                            anchorX="center"
                            anchorY="middle"
                            maxWidth={80}
                        >
                            {analysis.metric}: {analysis.recommendation}
                        </Text>
                    ))
                }

                {trendAnalysis.filter(analysis => analysis.trend === 'degrading').length === 0 && (
                    <Text
                        position={[0, 8, 0]}
                        fontSize={3}
                        color="#2ed573"
                        anchorX="center"
                        anchorY="middle"
                    >
                        🎉 系統性能表現良好，無需特別優化
                    </Text>
                )}
            </group>
        </>
    )
}

export default PerformanceTrendAnalyzer