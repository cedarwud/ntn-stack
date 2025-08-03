/**
 * A4 事件專屬視覺化組件
 *
 * 基於統一 SIB19 基礎平台，提供 A4 事件特定的視覺化功能：
 * 1. 位置補償 ΔS,T(t) 視覺化
 * 2. 修正觸發條件展示
 * 3. 信號強度熱力圖
 * 4. 服務衛星切換動畫
 *
 * 實現 "應用分化" 理念：選擇性使用 SIB19 資訊子集進行 A4 專屬展示
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Badge,
    Progress,
    // Alert,
    // AlertDescription,
    // Button,
    // Tooltip,
    // TooltipContent,
    // TooltipProvider,
    // TooltipTrigger
} from '@/components/ui'
import {
    // TrendingUp,
    // TrendingDown,
    Target,
    Zap,
    ArrowRight,
    Activity,
    Signal,
    AlertTriangle,
    CheckCircle,
} from 'lucide-react'
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    ResponsiveContainer,
    AreaChart,
    Area,
    ScatterChart,
    Scatter,
    // Cell,
} from 'recharts'
import {
    getSIB19UnifiedDataManager,
    A4VisualizationData,
} from '../services/SIB19UnifiedDataManager'

interface A4EventSpecificChartProps {
    className?: string
    height?: number
    showPositionCompensation?: boolean
    showSignalStrength?: boolean
    showTriggerConditions?: boolean
    showSatelliteHandover?: boolean
    onTriggerStateChange?: (isTriggered: boolean) => void
}

/**
 * A4 事件專屬視覺化組件
 */
export const A4EventSpecificChart: React.FC<A4EventSpecificChartProps> = ({
    className = '',
    height = 400,
    showPositionCompensation = true,
    showSignalStrength = true,
    showTriggerConditions = true,
    showSatelliteHandover = true,
    onTriggerStateChange,
}) => {
    // 狀態管理
    const [a4Data, setA4Data] = useState<A4VisualizationData | null>(null)
    const [historicalData, setHistoricalData] = useState<
        Array<{
            timestamp: number
            delta_s: number
            rsrp_dbm: number
            is_triggered: boolean
        }>
    >([])
    const [isLoading, setIsLoading] = useState(true)

    // 獲取統一數據管理器
    const dataManager = useMemo(() => getSIB19UnifiedDataManager(), [])

    // A4 數據更新處理
    const handleA4DataUpdate = useCallback(
        (data: A4VisualizationData) => {
            setA4Data(data)
            setIsLoading(false)

            // 更新歷史數據
            const newDataPoint = {
                timestamp: Date.now(),
                delta_s: data.position_compensation.delta_s,
                rsrp_dbm: data.signal_strength.rsrp_dbm,
                is_triggered: data.trigger_conditions.is_triggered,
            }

            setHistoricalData((prev) => {
                const updated = [...prev, newDataPoint]
                // 保持最近 50 個數據點
                return updated.slice(-50)
            })

            // 觸發狀態變化回調
            onTriggerStateChange?.(data.trigger_conditions.is_triggered)
        },
        [onTriggerStateChange]
    )

    // 初始化和事件監聽
    useEffect(() => {
        // 監聽 A4 特定數據更新
        dataManager.on('a4DataUpdated', handleA4DataUpdate)

        // 初始數據加載
        const initializeA4Data = () => {
            const data = dataManager.getA4SpecificData()
            if (data) {
                handleA4DataUpdate(data)
            }
        }

        initializeA4Data()

        // 清理函數
        return () => {
            dataManager.off('a4DataUpdated', handleA4DataUpdate)
        }
    }, [dataManager, handleA4DataUpdate])

    // 渲染位置補償視覺化
    const renderPositionCompensation = () => {
        if (!a4Data || !showPositionCompensation) return null

        const { position_compensation } = a4Data

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        位置補償 ΔS,T(t) 視覺化
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        {/* 原始位置補償 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">
                                {position_compensation.delta_s.toFixed(3)}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                原始 ΔS (km)
                            </div>
                        </div>

                        {/* 有效位置補償 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-green-600">
                                {position_compensation.effective_delta_s.toFixed(
                                    3
                                )}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                有效 ΔS (km)
                            </div>
                        </div>

                        {/* 幾何補償 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-purple-600">
                                {position_compensation.geometric_compensation_km.toFixed(
                                    3
                                )}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                幾何補償 (km)
                            </div>
                        </div>
                    </div>

                    {/* 位置補償向量圖 */}
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    type="number"
                                    dataKey="x"
                                    domain={[-5, 5]}
                                    label={{
                                        value: 'X 軸補償 (km)',
                                        position: 'insideBottom',
                                        offset: -5,
                                    }}
                                />
                                <YAxis
                                    type="number"
                                    dataKey="y"
                                    domain={[-5, 5]}
                                    label={{
                                        value: 'Y 軸補償 (km)',
                                        angle: -90,
                                        position: 'insideLeft',
                                    }}
                                />
                                <RechartsTooltip
                                    formatter={(value, name) => [value, name]}
                                    labelFormatter={() => '位置補償向量'}
                                />
                                <Scatter
                                    data={[
                                        {
                                            x:
                                                position_compensation.delta_s *
                                                Math.cos((45 * Math.PI) / 180),
                                            y:
                                                position_compensation.delta_s *
                                                Math.sin((45 * Math.PI) / 180),
                                            size:
                                                Math.abs(
                                                    position_compensation.effective_delta_s
                                                ) * 100,
                                        },
                                    ]}
                                    fill="#3b82f6"
                                />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        )
    }

    // 渲染信號強度熱力圖
    const renderSignalStrength = () => {
        if (!a4Data || !showSignalStrength) return null

        const { signal_strength } = a4Data
        const signalQuality =
            signal_strength.rsrp_dbm > signal_strength.threshold
                ? 'good'
                : 'poor'

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Signal className="h-4 w-4" />
                        信號強度監控
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        {/* 服務衛星 */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">
                                    服務衛星
                                </span>
                                <Badge variant="outline">
                                    {signal_strength.serving_satellite}
                                </Badge>
                            </div>
                            <div className="text-lg font-bold">
                                {signal_strength.rsrp_dbm.toFixed(1)} dBm
                            </div>
                            <Progress
                                value={Math.max(
                                    0,
                                    ((signal_strength.rsrp_dbm + 120) / 40) *
                                        100
                                )}
                                className="h-2"
                            />
                        </div>

                        {/* 目標衛星 */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">
                                    目標衛星
                                </span>
                                <Badge variant="outline">
                                    {signal_strength.target_satellite}
                                </Badge>
                            </div>
                            <div className="text-lg font-bold">
                                {(signal_strength.rsrp_dbm - 5).toFixed(1)} dBm
                            </div>
                            <Progress
                                value={Math.max(
                                    0,
                                    ((signal_strength.rsrp_dbm - 5 + 120) /
                                        40) *
                                        100
                                )}
                                className="h-2"
                            />
                        </div>
                    </div>

                    {/* 信號品質指示器 */}
                    <div className="flex items-center justify-center gap-2 p-4 rounded-lg bg-muted">
                        {signalQuality === 'good' ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : (
                            <AlertTriangle className="h-5 w-5 text-yellow-500" />
                        )}
                        <span className="font-medium">
                            信號品質:{' '}
                            {signalQuality === 'good' ? '良好' : '較差'}
                        </span>
                        <Badge
                            variant={
                                signalQuality === 'good'
                                    ? 'default'
                                    : 'destructive'
                            }
                        >
                            門檻值: {signal_strength.threshold} dBm
                        </Badge>
                    </div>

                    {/* 歷史信號強度趨勢 */}
                    {historicalData.length > 0 && (
                        <div className="mt-4 h-32">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={historicalData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                        dataKey="timestamp"
                                        type="number"
                                        scale="time"
                                        domain={['dataMin', 'dataMax']}
                                        tickFormatter={(value) =>
                                            new Date(value).toLocaleTimeString()
                                        }
                                    />
                                    <YAxis domain={[-120, -60]} />
                                    <RechartsTooltip
                                        labelFormatter={(value) =>
                                            new Date(value).toLocaleTimeString()
                                        }
                                        formatter={(value) => [
                                            `${value} dBm`,
                                            'RSRP',
                                        ]}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="rsrp_dbm"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </CardContent>
            </Card>
        )
    }

    // 渲染觸發條件監控
    const renderTriggerConditions = () => {
        if (!a4Data || !showTriggerConditions) return null

        const { trigger_conditions } = a4Data

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4" />
                        A4 觸發條件監控
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* 觸發狀態 */}
                        <div className="text-center">
                            <div
                                className={`text-2xl font-bold ${
                                    trigger_conditions.is_triggered
                                        ? 'text-red-600'
                                        : 'text-green-600'
                                }`}
                            >
                                {trigger_conditions.is_triggered
                                    ? '已觸發'
                                    : '未觸發'}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                觸發狀態
                            </div>
                            {trigger_conditions.is_triggered ? (
                                <Zap className="h-6 w-6 text-red-500 mx-auto mt-2" />
                            ) : (
                                <CheckCircle className="h-6 w-6 text-green-500 mx-auto mt-2" />
                            )}
                        </div>

                        {/* 遲滯值 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-600">
                                {trigger_conditions.hysteresis.toFixed(1)} dB
                            </div>
                            <div className="text-xs text-muted-foreground">
                                遲滯值
                            </div>
                        </div>

                        {/* 觸發時間 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-purple-600">
                                {trigger_conditions.time_to_trigger} ms
                            </div>
                            <div className="text-xs text-muted-foreground">
                                觸發時間
                            </div>
                        </div>
                    </div>

                    {/* 觸發條件進度條 */}
                    <div className="mt-4 space-y-2">
                        <div className="flex items-center justify-between text-sm">
                            <span>觸發進度</span>
                            <span>
                                {trigger_conditions.is_triggered
                                    ? '100%'
                                    : '0%'}
                            </span>
                        </div>
                        <Progress
                            value={trigger_conditions.is_triggered ? 100 : 0}
                            className="h-3"
                        />
                    </div>

                    {/* 觸發歷史 */}
                    {historicalData.length > 0 && (
                        <div className="mt-4 h-24">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={historicalData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                        dataKey="timestamp"
                                        type="number"
                                        scale="time"
                                        domain={['dataMin', 'dataMax']}
                                        tickFormatter={(value) =>
                                            new Date(value).toLocaleTimeString()
                                        }
                                    />
                                    <YAxis domain={[0, 1]} />
                                    <RechartsTooltip
                                        labelFormatter={(value) =>
                                            new Date(value).toLocaleTimeString()
                                        }
                                        formatter={(value) => [
                                            value ? '已觸發' : '未觸發',
                                            '狀態',
                                        ]}
                                    />
                                    <Area
                                        type="stepAfter"
                                        dataKey="is_triggered"
                                        stroke="#ef4444"
                                        fill="#ef4444"
                                        fillOpacity={0.3}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </CardContent>
            </Card>
        )
    }

    // 渲染衛星切換動畫
    const renderSatelliteHandover = () => {
        if (!a4Data || !showSatelliteHandover) return null

        const { signal_strength } = a4Data

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <ArrowRight className="h-4 w-4" />
                        服務衛星切換監控
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="flex items-center justify-center gap-4 p-6">
                        {/* 當前服務衛星 */}
                        <div className="text-center">
                            <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center mb-2">
                                <Signal className="h-8 w-8 text-white" />
                            </div>
                            <div className="font-medium">
                                {signal_strength.serving_satellite}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                服務衛星
                            </div>
                        </div>

                        {/* 切換箭頭 */}
                        <div className="flex flex-col items-center">
                            <ArrowRight className="h-8 w-8 text-muted-foreground" />
                            <div className="text-xs text-muted-foreground mt-1">
                                切換中
                            </div>
                        </div>

                        {/* 目標衛星 */}
                        <div className="text-center">
                            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mb-2">
                                <Target className="h-8 w-8 text-white" />
                            </div>
                            <div className="font-medium">
                                {signal_strength.target_satellite}
                            </div>
                            <div className="text-xs text-muted-foreground">
                                目標衛星
                            </div>
                        </div>
                    </div>

                    {/* 切換條件 */}
                    <div className="mt-4 p-3 bg-muted rounded-lg">
                        <div className="text-sm font-medium mb-2">
                            切換條件評估
                        </div>
                        <div className="space-y-1 text-xs">
                            <div className="flex justify-between">
                                <span>信號強度差異:</span>
                                <span>5.0 dB</span>
                            </div>
                            <div className="flex justify-between">
                                <span>遲滯門檻:</span>
                                <span>
                                    {a4Data.trigger_conditions.hysteresis} dB
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>切換建議:</span>
                                <span
                                    className={
                                        a4Data.trigger_conditions.is_triggered
                                            ? 'text-green-600'
                                            : 'text-red-600'
                                    }
                                >
                                    {a4Data.trigger_conditions.is_triggered
                                        ? '建議切換'
                                        : '保持當前'}
                                </span>
                            </div>
                        </div>
                    </div>
                </CardContent>
            </Card>
        )
    }

    if (isLoading) {
        return (
            <div
                className={`a4-event-specific-chart ${className}`}
                style={{ height }}
            >
                <div className="flex items-center justify-center h-full">
                    <div className="text-muted-foreground">
                        載入 A4 事件數據中...
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div
            className={`a4-event-specific-chart ${className}`}
            style={{ height }}
        >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                {renderPositionCompensation()}
                {renderSignalStrength()}
                {renderTriggerConditions()}
                {renderSatelliteHandover()}
            </div>
        </div>
    )
}

export default A4EventSpecificChart
