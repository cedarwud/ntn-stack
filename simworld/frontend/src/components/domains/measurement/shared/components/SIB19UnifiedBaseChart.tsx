/**
 * SIB19 統一基礎圖表組件
 *
 * 實現統一改進主準則 v3.0：
 * - 提供統一的 SIB19 基礎視覺化平台
 * - 支援事件特定的視覺化分化
 * - 消除資訊孤島和重複配置問題
 *
 * 核心功能：
 * 1. 統一 SIB19 狀態控制台
 * 2. 共享衛星星座管理面板
 * 3. 全域時間同步監控器
 * 4. 鄰居細胞統一管理
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
    Tabs,
    TabsContent,
    TabsList,
    TabsTrigger,
    Button,
    Switch,
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui'
import {
    Satellite,
    Clock,
    MapPin,
    Signal,
    AlertTriangle,
    CheckCircle,
    RefreshCw,
    Settings,
    Eye,
    EyeOff,
} from 'lucide-react'
import {
    getSIB19UnifiedDataManager,
    SIB19Data,
    SatellitePosition,
    NeighborCellConfig,
    SMTCWindow,
} from '../services/SIB19UnifiedDataManager'

interface SIB19UnifiedBaseChartProps {
    // 事件特定配置
    eventType?: 'A4' | 'D1' | 'D2' | 'T1'

    // 顯示控制
    showSatelliteConstellation?: boolean
    showNeighborCells?: boolean
    showTimeSync?: boolean
    showSMTCWindows?: boolean

    // 自定義樣式
    className?: string
    height?: number

    // 事件回調
    onSIB19DataUpdate?: (data: SIB19Data) => void
    onSatellitePositionUpdate?: (
        positions: Map<string, SatellitePosition>
    ) => void
    onError?: (error: Error) => void
}

/**
 * SIB19 統一基礎圖表組件
 */
export const SIB19UnifiedBaseChart: React.FC<SIB19UnifiedBaseChartProps> = ({
    eventType,
    showSatelliteConstellation = true,
    showNeighborCells = true,
    showTimeSync = true,
    showSMTCWindows = true,
    className = '',
    height = 600,
    onSIB19DataUpdate,
    onSatellitePositionUpdate,
    onError,
}) => {
    // 狀態管理
    const [sib19Data, setSIB19Data] = useState<SIB19Data | null>(null)
    const [satellitePositions, setSatellitePositions] = useState<
        Map<string, SatellitePosition>
    >(new Map())
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [autoUpdate, setAutoUpdate] = useState(true)
    const [selectedTab, setSelectedTab] = useState('status')

    // 獲取統一數據管理器
    const dataManager = useMemo(() => getSIB19UnifiedDataManager(), [])

    // 數據更新處理
    const handleDataUpdate = useCallback(
        (data: SIB19Data) => {
            setSIB19Data(data)
            setIsLoading(false)
            setError(null)
            onSIB19DataUpdate?.(data)
        },
        [onSIB19DataUpdate]
    )

    const handleSatellitePositionUpdate = useCallback(
        (positions: Map<string, SatellitePosition>) => {
            setSatellitePositions(positions)
            onSatellitePositionUpdate?.(positions)
        },
        [onSatellitePositionUpdate]
    )

    const handleError = useCallback(
        (err: Error) => {
            setError(err.message)
            setIsLoading(false)
            onError?.(err)
        },
        [onError]
    )

    // 初始化和事件監聽
    useEffect(() => {
        // 監聽數據更新事件
        dataManager.on('dataUpdated', handleDataUpdate)
        dataManager.on('updateError', handleError)

        // 初始數據加載
        const initializeData = async () => {
            setIsLoading(true)
            const success = await dataManager.forceUpdate()
            if (success) {
                const data = dataManager.getSIB19Data()
                const positions = dataManager.getSatellitePositions()

                if (data) {
                    handleDataUpdate(data)
                }
                handleSatellitePositionUpdate(positions)
            }
        }

        initializeData()

        // 清理函數
        return () => {
            dataManager.off('dataUpdated', handleDataUpdate)
            dataManager.off('updateError', handleError)
        }
    }, [
        dataManager,
        handleDataUpdate,
        handleError,
        handleSatellitePositionUpdate,
    ])

    // 自動更新控制
    useEffect(() => {
        // 注意：startAutoUpdate 和 stopAutoUpdate 在構造函數中已經處理
        // 這裡只需要控制自動更新的開關
        if (!autoUpdate) {
            dataManager.stopAutoUpdate()
        }
    }, [autoUpdate, dataManager])

    // 手動刷新
    const handleRefresh = useCallback(async () => {
        setIsLoading(true)
        await dataManager.forceUpdate()
    }, [dataManager])

    // 狀態指示器顏色
    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'valid':
                return 'bg-green-500'
            case 'expiring':
                return 'bg-yellow-500'
            case 'expired':
                return 'bg-red-500'
            default:
                return 'bg-gray-500'
        }
    }

    // 狀態指示器文本
    const getStatusText = (status: string): string => {
        switch (status) {
            case 'valid':
                return '有效'
            case 'expiring':
                return '即將過期'
            case 'expired':
                return '已過期'
            case 'not_initialized':
                return '未初始化'
            default:
                return '未知'
        }
    }

    // 渲染 SIB19 狀態控制台
    const renderStatusConsole = () => (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Satellite className="h-4 w-4" />
                    SIB19 統一狀態控制台
                </CardTitle>
                <div className="flex items-center gap-2">
                    <TooltipProvider>
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleRefresh}
                                    disabled={isLoading}
                                >
                                    <RefreshCw
                                        className={`h-4 w-4 ${
                                            isLoading ? 'animate-spin' : ''
                                        }`}
                                    />
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>手動刷新</TooltipContent>
                        </Tooltip>
                    </TooltipProvider>

                    <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                            自動更新
                        </span>
                        <Switch
                            checked={autoUpdate}
                            onCheckedChange={setAutoUpdate}
                            size="sm"
                        />
                    </div>
                </div>
            </CardHeader>

            <CardContent>
                {error && (
                    <Alert className="mb-4">
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>{error}</AlertDescription>
                    </Alert>
                )}

                {sib19Data && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {/* 廣播狀態 */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <div
                                    className={`w-2 h-2 rounded-full ${getStatusColor(
                                        sib19Data.status
                                    )}`}
                                />
                                <span className="text-sm font-medium">
                                    廣播狀態
                                </span>
                            </div>
                            <Badge
                                variant={
                                    sib19Data.status === 'valid'
                                        ? 'default'
                                        : 'destructive'
                                }
                            >
                                {getStatusText(sib19Data.status)}
                            </Badge>
                        </div>

                        {/* 有效期倒計時 */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4" />
                                <span className="text-sm font-medium">
                                    剩餘時間
                                </span>
                            </div>
                            <div className="text-lg font-bold">
                                {sib19Data.time_to_expiry_hours.toFixed(1)}h
                            </div>
                            <Progress
                                value={
                                    (sib19Data.time_to_expiry_hours /
                                        sib19Data.validity_time) *
                                    100
                                }
                                className="h-2"
                            />
                        </div>

                        {/* 衛星數量 */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Satellite className="h-4 w-4" />
                                <span className="text-sm font-medium">
                                    追蹤衛星
                                </span>
                            </div>
                            <div className="text-lg font-bold">
                                {sib19Data.satellites_count}
                            </div>
                        </div>

                        {/* 時間同步精度 */}
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Clock className="h-4 w-4" />
                                <span className="text-sm font-medium">
                                    同步精度
                                </span>
                            </div>
                            <div className="text-lg font-bold">
                                {sib19Data.time_correction.current_accuracy_ms.toFixed(
                                    1
                                )}
                                ms
                            </div>
                            {sib19Data.time_correction.current_accuracy_ms <
                            50 ? (
                                <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : (
                                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                            )}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    )

    // 渲染衛星星座管理面板
    const renderSatelliteConstellation = () => (
        <Card>
            <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Satellite className="h-4 w-4" />
                    共享衛星星座管理面板
                </CardTitle>
            </CardHeader>

            <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Array.from(satellitePositions.entries()).map(
                        ([satelliteId, position]) => (
                            <Card key={satelliteId} className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-medium text-sm">
                                        {satelliteId}
                                    </span>
                                    <Badge variant="outline">
                                        {position.elevation > 10
                                            ? '可見'
                                            : '不可見'}
                                    </Badge>
                                </div>

                                <div className="space-y-1 text-xs text-muted-foreground">
                                    <div>
                                        仰角: {position.elevation.toFixed(1)}°
                                    </div>
                                    <div>
                                        方位角: {position.azimuth.toFixed(1)}°
                                    </div>
                                    <div>
                                        距離:{' '}
                                        {(position.distance / 1000).toFixed(0)}
                                        km
                                    </div>
                                </div>

                                <div className="mt-2">
                                    <Progress
                                        value={Math.max(0, position.elevation)}
                                        max={90}
                                        className="h-1"
                                    />
                                </div>
                            </Card>
                        )
                    )}
                </div>
            </CardContent>
        </Card>
    )

    // 渲染鄰居細胞管理
    const renderNeighborCells = () => (
        <Card>
            <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Signal className="h-4 w-4" />
                    鄰居細胞統一管理 (最多 8 個)
                </CardTitle>
            </CardHeader>

            <CardContent>
                {sib19Data?.neighbor_cells &&
                sib19Data.neighbor_cells.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {sib19Data.neighbor_cells.slice(0, 8).map((cell) => (
                            <Card key={cell.cell_id} className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-medium text-sm">
                                        {cell.cell_id}
                                    </span>
                                    <Badge
                                        variant={
                                            cell.is_active
                                                ? 'default'
                                                : 'secondary'
                                        }
                                    >
                                        {cell.is_active ? '活躍' : '非活躍'}
                                    </Badge>
                                </div>

                                <div className="space-y-1 text-xs text-muted-foreground">
                                    <div>衛星: {cell.satellite_id}</div>
                                    <div>載波頻率: {cell.carrier_freq} MHz</div>
                                    <div>物理細胞ID: {cell.phys_cell_id}</div>
                                    <div>
                                        信號強度: {cell.signal_strength} dBm
                                    </div>
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="text-center text-muted-foreground py-8">
                        暫無鄰居細胞配置
                    </div>
                )}
            </CardContent>
        </Card>
    )

    // 渲染 SMTC 測量窗口
    const renderSMTCWindows = () => (
        <Card>
            <CardHeader>
                <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    SMTC 測量窗口管理
                </CardTitle>
            </CardHeader>

            <CardContent>
                {sib19Data?.smtc_windows &&
                sib19Data.smtc_windows.length > 0 ? (
                    <div className="space-y-3">
                        {sib19Data.smtc_windows.map((window, index) => (
                            <Card key={index} className="p-3">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="font-medium text-sm">
                                        {window.satellite_id}
                                    </span>
                                    <Badge variant="outline">
                                        {window.measurement_type}
                                    </Badge>
                                </div>

                                <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                                    <div>
                                        <div>開始時間</div>
                                        <div className="font-medium">
                                            {new Date(
                                                window.start_time
                                            ).toLocaleTimeString()}
                                        </div>
                                    </div>
                                    <div>
                                        <div>結束時間</div>
                                        <div className="font-medium">
                                            {new Date(
                                                window.end_time
                                            ).toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-2">
                                    <div className="flex items-center justify-between text-xs">
                                        <span>優先級</span>
                                        <span>{window.priority}</span>
                                    </div>
                                    <Progress
                                        value={window.priority * 20}
                                        className="h-1 mt-1"
                                    />
                                </div>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="text-center text-muted-foreground py-8">
                        暫無 SMTC 測量窗口
                    </div>
                )}
            </CardContent>
        </Card>
    )

    return (
        <div
            className={`sib19-unified-base-chart ${className}`}
            style={{ height }}
        >
            <Tabs
                value={selectedTab}
                onValueChange={setSelectedTab}
                className="w-full"
            >
                <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="status">狀態控制台</TabsTrigger>
                    <TabsTrigger value="satellites">衛星星座</TabsTrigger>
                    <TabsTrigger value="cells">鄰居細胞</TabsTrigger>
                    <TabsTrigger value="smtc">SMTC 窗口</TabsTrigger>
                </TabsList>

                <TabsContent value="status" className="mt-4">
                    {renderStatusConsole()}
                </TabsContent>

                <TabsContent value="satellites" className="mt-4">
                    {showSatelliteConstellation &&
                        renderSatelliteConstellation()}
                </TabsContent>

                <TabsContent value="cells" className="mt-4">
                    {showNeighborCells && renderNeighborCells()}
                </TabsContent>

                <TabsContent value="smtc" className="mt-4">
                    {showSMTCWindows && renderSMTCWindows()}
                </TabsContent>
            </Tabs>

            {/* 事件特定標識 */}
            {eventType && (
                <div className="absolute top-2 right-2">
                    <Badge variant="secondary" className="text-xs">
                        {eventType} 事件專用
                    </Badge>
                </div>
            )}
        </div>
    )
}

export default SIB19UnifiedBaseChart
