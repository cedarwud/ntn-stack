/**
 * SIB19 統一基礎平台組件
 * 
 * 實現統一改進主準則 v3.0 中的 "資訊統一、應用分化" 理想架構：
 * - 統一的 SIB19 基礎平台為所有測量事件提供共享資訊
 * - 不同事件根據特點選擇性使用 SIB19 相關資訊子集
 * - 提供鄰居細胞統一管理、SMTC 測量窗口、時間同步等核心功能
 */

import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
    Clock, 
    Satellite, 
    RefreshCw, 
    CheckCircle, 
    AlertTriangle, 
    XCircle,
    MapPin,
    Radio
} from 'lucide-react'
import './SIB19UnifiedPlatform.scss'

// 類型定義
interface SIB19Status {
    status: string
    broadcast_id: string
    broadcast_time: string
    validity_hours: number
    time_to_expiry_hours: number
    satellites_count: number
    neighbor_cells_count: number
    time_sync_accuracy_ms: number
    reference_location?: {
        type: string
        latitude: number
        longitude: number
    }
}

interface NeighborCell {
    physical_cell_id: number
    carrier_frequency: number
    satellite_id: string
    use_shared_ephemeris: boolean
    measurement_priority: number
    is_active: boolean
}

interface SMTCWindow {
    start_time: string
    end_time: string
    satellite_id: string
}

interface SIB19UnifiedPlatformProps {
    /** 選擇的事件類型，用於決定顯示哪些 SIB19 資訊子集 */
    selectedEventType?: 'A4' | 'D1' | 'D2' | 'T1'
    /** 是否顯示詳細的技術資訊 */
    showTechnicalDetails?: boolean
    /** 更新間隔（毫秒） */
    updateInterval?: number
    /** 事件處理回調 */
    onSIB19Update?: (status: SIB19Status) => void
    onNeighborCellsUpdate?: (cells: NeighborCell[]) => void
    onSMTCWindowsUpdate?: (windows: SMTCWindow[]) => void
}

export const SIB19UnifiedPlatform: React.FC<SIB19UnifiedPlatformProps> = ({
    selectedEventType,
    showTechnicalDetails = false,
    updateInterval = 5000,
    onSIB19Update,
    onNeighborCellsUpdate,
    onSMTCWindowsUpdate
}) => {
    // 狀態管理
    const [sib19Status, setSIB19Status] = useState<SIB19Status | null>(null)
    const [neighborCells, setNeighborCells] = useState<NeighborCell[]>([])
    const [smtcWindows, setSMTCWindows] = useState<SMTCWindow[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
    const [autoUpdate, setAutoUpdate] = useState(true)

    // API 調用函數
    const fetchSIB19Status = useCallback(async () => {
        try {
            const response = await fetch('/api/measurement-events/sib19-status')
            const data = await response.json()
            setSIB19Status(data)
            onSIB19Update?.(data)
            return data
        } catch (error) {
            console.error('SIB19 狀態獲取失敗:', error)
            return null
        }
    }, [onSIB19Update])

    const fetchNeighborCells = useCallback(async () => {
        try {
            // 模擬鄰居細胞數據 - 實際應從 API 獲取
            const mockCells: NeighborCell[] = [
                {
                    physical_cell_id: 1,
                    carrier_frequency: 12000.0,
                    satellite_id: 'sl_44713',
                    use_shared_ephemeris: true,
                    measurement_priority: 1,
                    is_active: true
                },
                {
                    physical_cell_id: 2,
                    carrier_frequency: 12100.0,
                    satellite_id: 'sl_44714',
                    use_shared_ephemeris: true,
                    measurement_priority: 2,
                    is_active: true
                },
                {
                    physical_cell_id: 3,
                    carrier_frequency: 12200.0,
                    satellite_id: 'sl_44715',
                    use_shared_ephemeris: true,
                    measurement_priority: 3,
                    is_active: true
                },
                {
                    physical_cell_id: 4,
                    carrier_frequency: 12300.0,
                    satellite_id: 'sl_44716',
                    use_shared_ephemeris: true,
                    measurement_priority: 4,
                    is_active: false
                }
            ]
            setNeighborCells(mockCells)
            onNeighborCellsUpdate?.(mockCells)
            return mockCells
        } catch (error) {
            console.error('鄰居細胞數據獲取失敗:', error)
            return []
        }
    }, [onNeighborCellsUpdate])

    const fetchSMTCWindows = useCallback(async () => {
        try {
            // 模擬 SMTC 測量窗口數據
            const now = new Date()
            const mockWindows: SMTCWindow[] = [
                {
                    start_time: new Date(now.getTime() + 1000).toISOString(),
                    end_time: new Date(now.getTime() + 11000).toISOString(),
                    satellite_id: 'sl_44713'
                },
                {
                    start_time: new Date(now.getTime() + 15000).toISOString(),
                    end_time: new Date(now.getTime() + 25000).toISOString(),
                    satellite_id: 'sl_44714'
                }
            ]
            setSMTCWindows(mockWindows)
            onSMTCWindowsUpdate?.(mockWindows)
            return mockWindows
        } catch (error) {
            console.error('SMTC 測量窗口獲取失敗:', error)
            return []
        }
    }, [onSMTCWindowsUpdate])

    // 統一更新函數
    const updateAllData = useCallback(async () => {
        if (isLoading) return

        setIsLoading(true)
        try {
            await Promise.all([
                fetchSIB19Status(),
                fetchNeighborCells(),
                fetchSMTCWindows()
            ])
            setLastUpdated(new Date())
        } catch (error) {
            console.error('數據更新失敗:', error)
        } finally {
            setIsLoading(false)
        }
    }, [isLoading, fetchSIB19Status, fetchNeighborCells, fetchSMTCWindows])

    // 自動更新機制
    useEffect(() => {
        if (!autoUpdate) return

        updateAllData() // 立即更新一次

        const interval = setInterval(updateAllData, updateInterval)
        return () => clearInterval(interval)
    }, [autoUpdate, updateInterval, updateAllData])

    // 獲取狀態指示器
    const getStatusIndicator = (status: string) => {
        switch (status) {
            case 'valid':
                return <CheckCircle className="h-4 w-4 text-green-500" />
            case 'expiring':
                return <AlertTriangle className="h-4 w-4 text-yellow-500" />
            case 'expired':
            case 'error':
                return <XCircle className="h-4 w-4 text-red-500" />
            default:
                return <RefreshCw className="h-4 w-4 text-gray-500" />
        }
    }

    // 獲取狀態顏色
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'valid':
                return 'bg-green-100 text-green-800'
            case 'expiring':
                return 'bg-yellow-100 text-yellow-800'
            case 'expired':
            case 'error':
                return 'bg-red-100 text-red-800'
            default:
                return 'bg-gray-100 text-gray-800'
        }
    }

    // 根據事件類型過濾顯示內容
    const shouldShowComponent = (component: string) => {
        if (!selectedEventType) return true // 沒有選擇事件類型時顯示所有
        
        const eventComponentMap = {
            'A4': ['status', 'neighbor_cells', 'smtc', 'time_sync', 'position_compensation'],
            'D1': ['status', 'neighbor_cells', 'reference_location', 'time_sync'],
            'D2': ['status', 'neighbor_cells', 'moving_reference', 'time_sync', 'smtc'],
            'T1': ['status', 'time_frame', 'time_sync']
        }
        
        return eventComponentMap[selectedEventType]?.includes(component) ?? true
    }

    return (
        <div className="sib19-unified-platform">
            {/* 主控制面板 */}
            <Card className="sib19-control-panel">
                <CardHeader className="pb-2">
                    <div className="flex items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <Satellite className="h-5 w-5" />
                            SIB19 統一基礎平台
                            {selectedEventType && (
                                <Badge variant="outline" className="ml-2">
                                    {selectedEventType} 事件專用
                                </Badge>
                            )}
                        </CardTitle>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={updateAllData}
                                disabled={isLoading}
                            >
                                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                                更新
                            </Button>
                            <Button
                                variant={autoUpdate ? "default" : "outline"}
                                size="sm"
                                onClick={() => setAutoUpdate(!autoUpdate)}
                            >
                                <Clock className="h-4 w-4" />
                                {autoUpdate ? '自動' : '手動'}
                            </Button>
                        </div>
                    </div>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {/* SIB19 狀態 */}
                        {shouldShowComponent('status') && sib19Status && (
                            <div className="sib19-status-card">
                                <div className="flex items-center gap-2 mb-2">
                                    {getStatusIndicator(sib19Status.status)}
                                    <Badge className={getStatusColor(sib19Status.status)}>
                                        {sib19Status.status.toUpperCase()}
                                    </Badge>
                                </div>
                                <div className="text-sm space-y-1">
                                    <div>ID: {sib19Status.broadcast_id}</div>
                                    <div>有效期: {sib19Status.validity_hours}h</div>
                                    <div>剩餘: {sib19Status.time_to_expiry_hours.toFixed(1)}h</div>
                                    <div>衛星數: {sib19Status.satellites_count}</div>
                                </div>
                            </div>
                        )}

                        {/* 時間同步狀態 */}
                        {shouldShowComponent('time_sync') && sib19Status && (
                            <div className="time-sync-card">
                                <div className="flex items-center gap-2 mb-2">
                                    <Clock className="h-4 w-4" />
                                    <span className="font-medium">時間同步</span>
                                </div>
                                <div className="text-sm space-y-1">
                                    <div>精度: {sib19Status.time_sync_accuracy_ms.toFixed(1)}ms</div>
                                    <div className="flex items-center gap-1">
                                        {sib19Status.time_sync_accuracy_ms < 50 ? (
                                            <CheckCircle className="h-3 w-3 text-green-500" />
                                        ) : (
                                            <AlertTriangle className="h-3 w-3 text-yellow-500" />
                                        )}
                                        <span>
                                            {sib19Status.time_sync_accuracy_ms < 50 ? '符合要求' : '需要改善'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 鄰居細胞管理 */}
                        {shouldShowComponent('neighbor_cells') && (
                            <div className="neighbor-cells-card">
                                <div className="flex items-center gap-2 mb-2">
                                    <Radio className="h-4 w-4" />
                                    <span className="font-medium">鄰居細胞</span>
                                </div>
                                <div className="text-sm space-y-1">
                                    <div>總數: {neighborCells.length}/8</div>
                                    <div>激活: {neighborCells.filter(c => c.is_active).length}</div>
                                    <div className="flex flex-wrap gap-1">
                                        {neighborCells.slice(0, 4).map((cell) => (
                                            <Badge
                                                key={cell.physical_cell_id}
                                                variant={cell.is_active ? "default" : "secondary"}
                                                className="text-xs"
                                            >
                                                {cell.physical_cell_id}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* 參考位置 */}
                        {shouldShowComponent('reference_location') && sib19Status?.reference_location && (
                            <div className="reference-location-card">
                                <div className="flex items-center gap-2 mb-2">
                                    <MapPin className="h-4 w-4" />
                                    <span className="font-medium">參考位置</span>
                                </div>
                                <div className="text-sm space-y-1">
                                    <div>類型: {sib19Status.reference_location.type}</div>
                                    <div>緯度: {sib19Status.reference_location.latitude.toFixed(4)}°</div>
                                    <div>經度: {sib19Status.reference_location.longitude.toFixed(4)}°</div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* 技術詳細資訊 */}
                    {showTechnicalDetails && (
                        <div className="mt-4 space-y-4">
                            {/* 鄰居細胞詳細列表 */}
                            {shouldShowComponent('neighbor_cells') && neighborCells.length > 0 && (
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-sm">鄰居細胞詳細配置</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2 text-sm">
                                            {neighborCells.map((cell) => (
                                                <div
                                                    key={cell.physical_cell_id}
                                                    className={`p-2 rounded border ${
                                                        cell.is_active ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
                                                    }`}
                                                >
                                                    <div className="flex items-center justify-between mb-1">
                                                        <span className="font-medium">Cell {cell.physical_cell_id}</span>
                                                        <Badge
                                                            variant={cell.is_active ? "default" : "secondary"}
                                                            className="text-xs"
                                                        >
                                                            P{cell.measurement_priority}
                                                        </Badge>
                                                    </div>
                                                    <div className="space-y-1 text-xs text-gray-600">
                                                        <div>衛星: {cell.satellite_id}</div>
                                                        <div>頻率: {cell.carrier_frequency} MHz</div>
                                                        <div>共享星曆: {cell.use_shared_ephemeris ? '是' : '否'}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}

                            {/* SMTC 測量窗口 */}
                            {shouldShowComponent('smtc') && smtcWindows.length > 0 && (
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-sm">SMTC 測量窗口</CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-2 text-sm">
                                            {smtcWindows.map((window, index) => (
                                                <div key={index} className="p-2 bg-blue-50 rounded border border-blue-200">
                                                    <div className="flex items-center justify-between">
                                                        <span className="font-medium">{window.satellite_id}</span>
                                                        <Badge variant="outline" className="text-xs">
                                                            {Math.floor((new Date(window.end_time).getTime() - new Date(window.start_time).getTime()) / 1000)}s
                                                        </Badge>
                                                    </div>
                                                    <div className="text-xs text-gray-600 mt-1">
                                                        <div>開始: {new Date(window.start_time).toLocaleTimeString()}</div>
                                                        <div>結束: {new Date(window.end_time).toLocaleTimeString()}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </CardContent>
                                </Card>
                            )}
                        </div>
                    )}

                    {/* 狀態提示 */}
                    {sib19Status?.status === 'expiring' && (
                        <Alert className="mt-4">
                            <AlertTriangle className="h-4 w-4" />
                            <AlertDescription>
                                SIB19 廣播即將過期，系統將在 {sib19Status.time_to_expiry_hours.toFixed(1)} 小時內自動更新
                            </AlertDescription>
                        </Alert>
                    )}

                    {sib19Status?.status === 'expired' && (
                        <Alert className="mt-4" variant="destructive">
                            <XCircle className="h-4 w-4" />
                            <AlertDescription>
                                SIB19 廣播已過期，請聯繫系統管理員或等待自動更新
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* 最後更新時間 */}
                    {lastUpdated && (
                        <div className="mt-4 text-xs text-gray-500 text-center">
                            最後更新: {lastUpdated.toLocaleString()}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}

export default SIB19UnifiedPlatform