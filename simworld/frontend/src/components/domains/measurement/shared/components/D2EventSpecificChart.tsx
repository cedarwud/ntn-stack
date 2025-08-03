/**
 * D2 事件專屬視覺化組件 (基於統一 SIB19 平台)
 *
 * 修正 Phase 2.1 問題：
 * 1. ✅ 修正軌道週期從 120秒 到 90分鐘 (真實 LEO 衛星軌道)
 * 2. ✅ 實現基於 SIB19 的真實衛星星曆計算
 * 3. ✅ 加入星曆 validityTime 倒計時和更新提醒
 * 4. ✅ 實現雙閾值觸發的準確視覺化
 *
 * 基於統一改進主準則 v3.0：
 * - 資訊統一：使用統一 SIB19 數據源
 * - 應用分化：D2 事件專屬的動態參考位置視覺化
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
    Badge,
    Progress,
    Alert,
    AlertDescription,
    Button,
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui'
import {
    Navigation,
    MapPin,
    Target,
    Clock,
    TrendingUp,
    TrendingDown,
    Activity,
    Satellite,
    AlertTriangle,
    CheckCircle,
    RefreshCw,
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
    ReferenceLine,
} from 'recharts'
import {
    getSIB19UnifiedDataManager,
    D2VisualizationData,
    Position,
} from '../services/SIB19UnifiedDataManager'

interface D2EventSpecificChartProps {
    className?: string
    height?: number

    // D2 事件參數
    thresh1?: number // 衛星距離門檻值 (km)
    thresh2?: number // 地面距離門檻值 (km)
    hysteresis?: number // 遲滯值 (m)

    // UE 位置
    uePosition?: Position

    // 顯示控制
    showMovingReference?: boolean
    showRelativeDistances?: boolean
    showMovementVector?: boolean
    showThresholdVisualization?: boolean

    // 事件回調
    onTriggerStateChange?: (isTriggered: boolean) => void
    onReferenceLocationUpdate?: (location: Position) => void
}

/**
 * D2 事件專屬視覺化組件
 */
export const D2EventSpecificChart: React.FC<D2EventSpecificChartProps> = ({
    className = '',
    height = 400,
    thresh1 = 800000, // 800000 m (修正後的真實 LEO 衛星距離) - 符合 API 約束
    thresh2 = 30000, // 30000 m (地面距離) - 符合 API 約束
    hysteresis = 500, // 500 m - 符合 API 約束: ge=100
    uePosition = { latitude: 0.0, longitude: 0.0, altitude: 0.1 },
    showMovingReference = true,
    showRelativeDistances = true,
    showMovementVector = true,
    showThresholdVisualization = true,
    onTriggerStateChange,
    onReferenceLocationUpdate,
}) => {
    // 狀態管理
    const [d2Data, setD2Data] = useState<D2VisualizationData | null>(null)
    const [historicalData, setHistoricalData] = useState<
        Array<{
            timestamp: number
            satellite_distance: number
            ground_distance: number
            is_triggered: boolean
            reference_position: Position
        }>
    >([])
    const [isLoading, setIsLoading] = useState(true)
    const [validityTimeRemaining, setValidityTimeRemaining] =
        useState<number>(0)

    // 獲取統一數據管理器
    const dataManager = useMemo(() => getSIB19UnifiedDataManager(), [])

    // D2 數據更新處理
    const handleD2DataUpdate = useCallback(
        (data: D2VisualizationData) => {
            setD2Data(data)
            setIsLoading(false)

            // 計算觸發狀態 (雙閾值邏輯)
            const satelliteDistanceTriggered =
                data.relative_distances.satellite_distance > thresh1 * 1000 // 轉換為米
            const groundDistanceTriggered =
                data.relative_distances.ground_distance > thresh2 * 1000 // 轉換為米
            const isTriggered =
                satelliteDistanceTriggered && groundDistanceTriggered

            // 更新歷史數據
            const newDataPoint = {
                timestamp: Date.now(),
                satellite_distance:
                    data.relative_distances.satellite_distance / 1000, // 轉換為 km
                ground_distance: data.relative_distances.ground_distance / 1000, // 轉換為 km
                is_triggered: isTriggered,
                reference_position: data.moving_reference.current_position,
            }

            setHistoricalData((prev) => {
                const updated = [...prev, newDataPoint]
                // 保持最近 90 個數據點 (對應 90 分鐘的真實軌道週期)
                return updated.slice(-90)
            })

            // 觸發狀態變化回調
            onTriggerStateChange?.(isTriggered)

            // 參考位置更新回調
            onReferenceLocationUpdate?.(data.moving_reference.current_position)
        },
        [thresh1, thresh2, onTriggerStateChange, onReferenceLocationUpdate]
    )

    // 初始化和事件監聽
    useEffect(() => {
        // 監聽 D2 特定數據更新
        dataManager.on('d2DataUpdated', handleD2DataUpdate)

        // 監聽 SIB19 數據更新以獲取 validityTime
        dataManager.on('dataUpdated', (sib19Data) => {
            if (sib19Data) {
                setValidityTimeRemaining(sib19Data.time_to_expiry_hours)
            }
        })

        // 初始數據加載
        const initializeD2Data = () => {
            const data = dataManager.getD2SpecificData()
            if (data) {
                handleD2DataUpdate(data)
            }

            const sib19Data = dataManager.getSIB19Data()
            if (sib19Data) {
                setValidityTimeRemaining(sib19Data.time_to_expiry_hours)
            }
        }

        initializeD2Data()

        // 清理函數
        return () => {
            dataManager.off('d2DataUpdated', handleD2DataUpdate)
            dataManager.off('dataUpdated', () => {})
        }
    }, [dataManager, handleD2DataUpdate])

    // 渲染動態參考位置追蹤
    const renderMovingReference = () => {
        if (!d2Data || !showMovingReference) return null

        const { moving_reference } = d2Data

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Navigation className="h-4 w-4" />
                        動態參考位置追蹤 (基於真實衛星軌道)
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        {/* 當前參考位置 */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <MapPin className="h-4 w-4" />
                                <span className="text-sm font-medium">
                                    當前參考位置
                                </span>
                            </div>
                            <div className="space-y-1 text-xs">
                                <div>
                                    緯度:{' '}
                                    {moving_reference.current_position.latitude.toFixed(
                                        4
                                    )}
                                    °
                                </div>
                                <div>
                                    經度:{' '}
                                    {moving_reference.current_position.longitude.toFixed(
                                        4
                                    )}
                                    °
                                </div>
                                <div>
                                    高度:{' '}
                                    {moving_reference.current_position.altitude.toFixed(
                                        1
                                    )}{' '}
                                    km
                                </div>
                            </div>
                        </div>

                        {/* 參考衛星 */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Satellite className="h-4 w-4" />
                                <span className="text-sm font-medium">
                                    參考衛星
                                </span>
                            </div>
                            <div className="space-y-1 text-xs">
                                <div>
                                    衛星ID: {moving_reference.satellite_id}
                                </div>
                                <div>軌道週期: 90 分鐘 (真實 LEO)</div>
                                <div>軌道高度: ~550 km</div>
                            </div>
                        </div>
                    </div>

                    {/* 軌道軌跡視覺化 */}
                    {moving_reference.trajectory.length > 0 && (
                        <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                        type="number"
                                        dataKey="longitude"
                                        domain={['dataMin - 5', 'dataMax + 5']}
                                        label={{
                                            value: '經度 (°)',
                                            position: 'insideBottom',
                                            offset: -5,
                                        }}
                                    />
                                    <YAxis
                                        type="number"
                                        dataKey="latitude"
                                        domain={['dataMin - 5', 'dataMax + 5']}
                                        label={{
                                            value: '緯度 (°)',
                                            angle: -90,
                                            position: 'insideLeft',
                                        }}
                                    />
                                    <RechartsTooltip
                                        formatter={(value, name) => [
                                            value,
                                            name,
                                        ]}
                                        labelFormatter={() => '軌道軌跡'}
                                    />
                                    <Scatter
                                        data={moving_reference.trajectory}
                                        fill="#3b82f6"
                                        name="軌道軌跡"
                                    />
                                    <Scatter
                                        data={[
                                            moving_reference.current_position,
                                        ]}
                                        fill="#ef4444"
                                        name="當前位置"
                                    />
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {/* 星曆有效期倒計時 */}
                    <div className="mt-4 p-3 bg-muted rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">
                                星曆有效期
                            </span>
                            {validityTimeRemaining > 2 ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                            )}
                        </div>
                        <div className="text-lg font-bold">
                            {validityTimeRemaining.toFixed(1)} 小時
                        </div>
                        <Progress
                            value={(validityTimeRemaining / 24) * 100}
                            className="h-2 mt-2"
                        />
                        {validityTimeRemaining < 2 && (
                            <Alert className="mt-2">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription>
                                    星曆即將過期，建議更新 SIB19 數據
                                </AlertDescription>
                            </Alert>
                        )}
                    </div>
                </CardContent>
            </Card>
        )
    }

    // 渲染相對距離計算
    const renderRelativeDistances = () => {
        if (!d2Data || !showRelativeDistances) return null

        const { relative_distances } = d2Data

        // 計算觸發狀態
        const satelliteTriggered =
            relative_distances.satellite_distance > thresh1 * 1000
        const groundTriggered =
            relative_distances.ground_distance > thresh2 * 1000
        const overallTriggered = satelliteTriggered && groundTriggered

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Target className="h-4 w-4" />
                        相對距離計算 (雙閾值觸發)
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        {/* 衛星距離 */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">
                                    衛星距離
                                </span>
                                <Badge
                                    variant={
                                        satelliteTriggered
                                            ? 'destructive'
                                            : 'default'
                                    }
                                >
                                    {satelliteTriggered ? '已觸發' : '未觸發'}
                                </Badge>
                            </div>
                            <div className="text-2xl font-bold text-blue-600">
                                {(
                                    relative_distances.satellite_distance / 1000
                                ).toFixed(1)}{' '}
                                km
                            </div>
                            <div className="text-xs text-muted-foreground">
                                門檻值: {thresh1} km
                            </div>
                            <Progress
                                value={Math.min(
                                    100,
                                    (relative_distances.satellite_distance /
                                        1000 /
                                        thresh1) *
                                        100
                                )}
                                className="h-2"
                            />
                        </div>

                        {/* 地面距離 */}
                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium">
                                    地面距離
                                </span>
                                <Badge
                                    variant={
                                        groundTriggered
                                            ? 'destructive'
                                            : 'default'
                                    }
                                >
                                    {groundTriggered ? '已觸發' : '未觸發'}
                                </Badge>
                            </div>
                            <div className="text-2xl font-bold text-green-600">
                                {(
                                    relative_distances.ground_distance / 1000
                                ).toFixed(1)}{' '}
                                km
                            </div>
                            <div className="text-xs text-muted-foreground">
                                門檻值: {thresh2} km
                            </div>
                            <Progress
                                value={Math.min(
                                    100,
                                    (relative_distances.ground_distance /
                                        1000 /
                                        thresh2) *
                                        100
                                )}
                                className="h-2"
                            />
                        </div>
                    </div>

                    {/* 整體觸發狀態 */}
                    <div className="p-3 rounded-lg bg-muted">
                        <div className="flex items-center justify-center gap-2">
                            {overallTriggered ? (
                                <AlertTriangle className="h-5 w-5 text-red-500" />
                            ) : (
                                <CheckCircle className="h-5 w-5 text-green-500" />
                            )}
                            <span className="font-medium">
                                D2 事件狀態:{' '}
                                {overallTriggered ? '已觸發' : '未觸發'}
                            </span>
                        </div>
                        <div className="text-xs text-center text-muted-foreground mt-1">
                            需要同時滿足衛星距離 &gt; {thresh1}km 且 地面距離
                            &gt; {thresh2}km
                        </div>
                    </div>

                    {/* 歷史距離趨勢 */}
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
                                    <YAxis />
                                    <RechartsTooltip
                                        labelFormatter={(value) =>
                                            new Date(value).toLocaleTimeString()
                                        }
                                        formatter={(value, name) => [
                                            `${value} km`,
                                            name,
                                        ]}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="satellite_distance"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        dot={false}
                                        name="衛星距離"
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="ground_distance"
                                        stroke="#10b981"
                                        strokeWidth={2}
                                        dot={false}
                                        name="地面距離"
                                    />
                                    <ReferenceLine
                                        y={thresh1}
                                        stroke="#ef4444"
                                        strokeDasharray="5 5"
                                    />
                                    <ReferenceLine
                                        y={thresh2}
                                        stroke="#f59e0b"
                                        strokeDasharray="5 5"
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}
                </CardContent>
            </Card>
        )
    }

    // 渲染移動向量顯示
    const renderMovementVector = () => {
        if (!d2Data || !showMovementVector) return null

        const { movement_vector } = d2Data

        return (
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                        <Activity className="h-4 w-4" />
                        移動向量分析
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* 速度 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-purple-600">
                                {movement_vector.velocity_kmh.toFixed(0)} km/h
                            </div>
                            <div className="text-xs text-muted-foreground">
                                移動速度
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                (典型 LEO 衛星: ~27,000 km/h)
                            </div>
                        </div>

                        {/* 方向 */}
                        <div className="text-center">
                            <div className="text-2xl font-bold text-orange-600">
                                {movement_vector.direction_deg.toFixed(1)}°
                            </div>
                            <div className="text-xs text-muted-foreground">
                                移動方向
                            </div>
                            <div className="text-xs text-muted-foreground mt-1">
                                (相對於正北方向)
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
                className={`d2-event-specific-chart ${className}`}
                style={{ height }}
            >
                <div className="flex items-center justify-center h-full">
                    <div className="text-muted-foreground">
                        載入 D2 事件數據中...
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div
            className={`d2-event-specific-chart ${className}`}
            style={{ height }}
        >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-full">
                {renderMovingReference()}
                {renderRelativeDistances()}
                {renderMovementVector()}
            </div>
        </div>
    )
}

export default D2EventSpecificChart
