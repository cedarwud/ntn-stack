/**
 * LEO 衛星換手管理系統彈窗
 * 展示 IEEE INFOCOM 2024 論文演算法的完整實現
 */
import React, { useState, useEffect, useCallback } from 'react'
import { netStackApi } from '../../services/netstack-api'
import { simWorldApi } from '../../services/simworld-api'
import { withErrorBoundary } from '../common/ErrorBoundary'
import HandoverManager from './HandoverManager'
import { VisibleSatelliteInfo } from '../../types/satellite'

interface LEOHandoverManagementModalProps {
    isVisible: boolean
    onClose: () => void
    satellites?: VisibleSatelliteInfo[]
    selectedUEId?: number
    handoverMode?: 'demo' | 'real'
    satelliteSpeedMultiplier?: number
    onHandoverStateChange?: (state: any) => void
    onCurrentConnectionChange?: (connection: any) => void
    onPredictedConnectionChange?: (connection: any) => void
    onTransitionChange?: (isTransitioning: boolean, progress: number) => void
    onAlgorithmResults?: (results: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }) => void
}

interface HandoverPrediction {
    prediction_id: string
    ue_id: string
    satellite_id: string
    handover_required: boolean
    handover_trigger_time?: number
    current_satellite: {
        satellite_id: string
        name: string
        signal_strength: number
        elevation: number
        distance_km: number
    }
    future_satellite: {
        satellite_id: string
        name: string
        signal_strength: number
        elevation: number
        distance_km: number
    }
    binary_search_result?: {
        handover_time: number
        iterations: Array<{
            iteration: number
            start_time: number
            end_time: number
            mid_time: number
            satellite: string
            precision: number
            completed: boolean
        }>
    }
}

interface CoreSyncData {
    service_info: {
        is_running: boolean
        uptime_hours: number
        core_sync_state: string
    }
    statistics: {
        total_sync_operations: number
        successful_syncs: number
        average_sync_time_ms: number
        uptime_percentage: number
    }
    ieee_infocom_2024_features: {
        fine_grained_sync_active: boolean
        two_point_prediction: boolean
        signaling_free_coordination: boolean
        binary_search_refinement: number
    }
}

interface SatelliteData {
    satellites: Array<{
        id: number
        name: string
        norad_id: string
        position: {
            latitude: number
            longitude: number
            altitude: number
            elevation: number
            azimuth: number
            range: number
            velocity: number
            doppler_shift: number
        }
        signal_quality: {
            elevation_deg: number
            range_km: number
            estimated_signal_strength: number
            path_loss_db: number
        }
        timestamp: string
    }>
    total_visible: number
}

const LEOHandoverManagementModal: React.FC<LEOHandoverManagementModalProps> = ({
    isVisible,
    onClose,
    satellites,
    selectedUEId,
    handoverMode,
    satelliteSpeedMultiplier,
    onHandoverStateChange,
    onCurrentConnectionChange,
    onPredictedConnectionChange,
    onTransitionChange,
    onAlgorithmResults,
}) => {
    const [activeTab, setActiveTab] = useState<
        'management' | 'algorithm' | 'prediction' | 'sync' | 'satellites'
    >('management')
    const [loading, setLoading] = useState(false)
    const [handoverPrediction, setHandoverPrediction] =
        useState<HandoverPrediction | null>(null)
    const [coreSyncData, setCoreSyncData] = useState<CoreSyncData | null>(null)
    const [satelliteData, setSatelliteData] = useState<SatelliteData | null>(
        null
    )
    const [error, setError] = useState<string | null>(null)

    // 載入數據
    const loadData = useCallback(async () => {
        if (!isVisible) return

        setLoading(true)
        setError(null)

        try {
            // 並行載入所有數據
            const [predictionResult, coreSyncResult, satelliteResult] =
                await Promise.allSettled([
                    netStackApi.predictSatelliteAccess({
                        ue_id: 'UE_DEMO_001',
                        satellite_id: 'STARLINK-1600',
                    }),
                    netStackApi.getCoreSync(),
                    simWorldApi.getVisibleSatellites(5, 10), // 最小仰角5度，最多10個衛星
                ])

            if (predictionResult.status === 'fulfilled') {
                setHandoverPrediction(predictionResult.value)
            } else {
                console.debug('Prediction API unavailable, using fallback data')
            }

            if (coreSyncResult.status === 'fulfilled') {
                setCoreSyncData(coreSyncResult.value)
            } else {
                console.debug('CoreSync API unavailable, using fallback data')
            }

            if (
                satelliteResult.status === 'fulfilled' &&
                satelliteResult.value.success
            ) {
                setSatelliteData(satelliteResult.value.results)
            } else {
                console.debug('Satellite API unavailable, using fallback data')
            }
        } catch (err) {
            setError(
                err instanceof Error ? err.message : 'Unknown error occurred'
            )
        } finally {
            setLoading(false)
        }
    }, [isVisible])

    useEffect(() => {
        loadData()
    }, [loadData])

    // 鍵盤快捷鍵
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose()
            }
        }

        if (isVisible) {
            document.addEventListener('keydown', handleKeyDown)
        }

        return () => {
            document.removeEventListener('keydown', handleKeyDown)
        }
    }, [isVisible, onClose])

    if (!isVisible) return null

    return (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-[1000]">
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 text-white rounded-lg shadow-2xl w-[95vw] h-[90vh] max-w-7xl border border-gray-700">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                    <div>
                        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                            🛰️ LEO 衛星換手管理系統
                        </h2>
                        <p className="text-gray-400 text-sm mt-1">
                            IEEE INFOCOM 2024 - Advanced Handover Prediction
                            Algorithm
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button
                            onClick={loadData}
                            disabled={loading}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded-lg text-sm font-medium transition-colors"
                        >
                            {loading ? '🔄 更新中...' : '🔄 刷新數據'}
                        </button>
                        <button
                            onClick={onClose}
                            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-sm font-medium transition-colors"
                        >
                            ✕ 關閉
                        </button>
                    </div>
                </div>

                {/* Tab Navigation */}
                <div className="flex border-b border-gray-700">
                    {[
                        {
                            key: 'management',
                            label: '🎮 換手管理',
                            desc: 'Real-time Handover Management',
                        },
                        {
                            key: 'algorithm',
                            label: '🧮 核心演算法',
                            desc: 'Binary Search + Two-Point Prediction',
                        },
                        {
                            key: 'prediction',
                            label: '🎯 換手預測',
                            desc: 'Real-time Handover Prediction',
                        },
                        {
                            key: 'sync',
                            label: '⚡ 同步狀態',
                            desc: 'Core Synchronization Status',
                        },
                        {
                            key: 'satellites',
                            label: '🛰️ 衛星狀態',
                            desc: 'Visible Satellites',
                        },
                    ].map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key as any)}
                            className={`flex-1 px-6 py-4 text-left transition-colors ${
                                activeTab === tab.key
                                    ? 'bg-blue-600 text-white border-b-2 border-blue-400'
                                    : 'hover:bg-gray-800 text-gray-300'
                            }`}
                        >
                            <div className="font-medium">{tab.label}</div>
                            <div className="text-xs text-gray-400">
                                {tab.desc}
                            </div>
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-auto p-6">
                    {error && (
                        <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-6">
                            <p className="text-red-200">❌ 錯誤: {error}</p>
                        </div>
                    )}

                    {/* Management Tab */}
                    {activeTab === 'management' && (
                        <div
                            className="h-full"
                            style={{
                                backgroundColor: 'transparent',
                                padding: '0',
                                minHeight: '500px',
                                overflow: 'auto',
                            }}
                        >
                            <HandoverManager
                                satellites={satellites || []}
                                selectedUEId={selectedUEId}
                                isEnabled={true}
                                handoverMode={handoverMode}
                                speedMultiplier={satelliteSpeedMultiplier}
                                onHandoverStateChange={onHandoverStateChange}
                                onCurrentConnectionChange={
                                    onCurrentConnectionChange
                                }
                                onPredictedConnectionChange={
                                    onPredictedConnectionChange
                                }
                                onTransitionChange={onTransitionChange}
                                onAlgorithmResults={onAlgorithmResults}
                                hideUI={false}
                            />
                        </div>
                    )}

                    {/* Algorithm Tab */}
                    {activeTab === 'algorithm' && (
                        <AlgorithmView
                            coreSyncData={coreSyncData}
                            handoverPrediction={handoverPrediction}
                            loading={loading}
                        />
                    )}

                    {/* Prediction Tab */}
                    {activeTab === 'prediction' && (
                        <PredictionView
                            prediction={handoverPrediction}
                            loading={loading}
                        />
                    )}

                    {/* Sync Tab */}
                    {activeTab === 'sync' && (
                        <SyncView
                            coreSyncData={coreSyncData}
                            loading={loading}
                        />
                    )}

                    {/* Satellites Tab */}
                    {activeTab === 'satellites' && (
                        <SatellitesView
                            satelliteData={satelliteData}
                            loading={loading}
                        />
                    )}
                </div>
            </div>
        </div>
    )
}

// Algorithm View Component
const AlgorithmView: React.FC<{
    coreSyncData: CoreSyncData | null
    handoverPrediction: HandoverPrediction | null
    loading: boolean
}> = ({ coreSyncData, handoverPrediction, loading }) => {
    if (loading) {
        return (
            <div className="text-center py-12 text-gray-400">
                🔄 載入演算法數據中...
            </div>
        )
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* IEEE INFOCOM 2024 Features */}
            <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-6 border border-blue-700">
                <h3 className="text-xl font-bold mb-4 flex items-center">
                    🏆 IEEE INFOCOM 2024 演算法特性
                </h3>

                {coreSyncData?.ieee_infocom_2024_features ? (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span>細粒度同步 (Fine-grained Sync)</span>
                            <span
                                className={`px-3 py-1 rounded-full text-xs ${
                                    coreSyncData.ieee_infocom_2024_features
                                        .fine_grained_sync_active
                                        ? 'bg-green-600 text-green-100'
                                        : 'bg-red-600 text-red-100'
                                }`}
                            >
                                {coreSyncData.ieee_infocom_2024_features
                                    .fine_grained_sync_active
                                    ? '✅ 啟用'
                                    : '❌ 停用'}
                            </span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span>二點預測 (Two-Point Prediction)</span>
                            <span
                                className={`px-3 py-1 rounded-full text-xs ${
                                    coreSyncData.ieee_infocom_2024_features
                                        .two_point_prediction
                                        ? 'bg-green-600 text-green-100'
                                        : 'bg-red-600 text-red-100'
                                }`}
                            >
                                {coreSyncData.ieee_infocom_2024_features
                                    .two_point_prediction
                                    ? '✅ 啟用'
                                    : '❌ 停用'}
                            </span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span>無信令協調 (Signaling-free)</span>
                            <span
                                className={`px-3 py-1 rounded-full text-xs ${
                                    coreSyncData.ieee_infocom_2024_features
                                        .signaling_free_coordination
                                        ? 'bg-green-600 text-green-100'
                                        : 'bg-red-600 text-red-100'
                                }`}
                            >
                                {coreSyncData.ieee_infocom_2024_features
                                    .signaling_free_coordination
                                    ? '✅ 啟用'
                                    : '❌ 停用'}
                            </span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span>二分搜尋精度 (Binary Search)</span>
                            <span className="px-3 py-1 bg-purple-600 text-purple-100 rounded-full text-xs">
                                {
                                    coreSyncData.ieee_infocom_2024_features
                                        .binary_search_refinement
                                }{' '}
                                次迭代
                            </span>
                        </div>
                    </div>
                ) : (
                    <div className="text-gray-400">無演算法特性數據</div>
                )}
            </div>

            {/* Binary Search Iterations */}
            <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-6 border border-purple-700">
                <h3 className="text-xl font-bold mb-4 flex items-center">
                    🔍 二分搜尋迭代過程
                </h3>

                {handoverPrediction?.binary_search_result?.iterations ? (
                    <div className="space-y-3 max-h-80 overflow-y-auto">
                        {handoverPrediction.binary_search_result.iterations.map(
                            (iteration, index) => (
                                <div
                                    key={index}
                                    className="bg-purple-800 bg-opacity-50 rounded-lg p-3 border border-purple-600"
                                >
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="font-medium">
                                            迭代 #{iteration.iteration}
                                        </span>
                                        <span
                                            className={`px-2 py-1 rounded text-xs ${
                                                iteration.completed
                                                    ? 'bg-green-600 text-green-100'
                                                    : 'bg-yellow-600 text-yellow-100'
                                            }`}
                                        >
                                            {iteration.completed
                                                ? '✅ 完成'
                                                : '⏳ 進行中'}
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-sm">
                                        <div>
                                            開始時間:{' '}
                                            {iteration.start_time.toFixed(2)}s
                                        </div>
                                        <div>
                                            結束時間:{' '}
                                            {iteration.end_time.toFixed(2)}s
                                        </div>
                                        <div>
                                            中點時間:{' '}
                                            {iteration.mid_time.toFixed(2)}s
                                        </div>
                                        <div>
                                            精度:{' '}
                                            {iteration.precision.toFixed(4)}
                                        </div>
                                    </div>
                                    <div className="mt-2 text-sm text-purple-200">
                                        目標衛星: {iteration.satellite}
                                    </div>
                                </div>
                            )
                        )}
                    </div>
                ) : (
                    <div className="text-gray-400">無二分搜尋數據</div>
                )}
            </div>

            {/* Algorithm Performance */}
            <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-6 border border-green-700">
                <h3 className="text-xl font-bold mb-4 flex items-center">
                    📊 演算法性能指標
                </h3>

                {coreSyncData?.statistics ? (
                    <div className="grid grid-cols-2 gap-4">
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-300">
                                {coreSyncData.statistics.total_sync_operations}
                            </div>
                            <div className="text-sm text-gray-300">
                                總同步操作
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-300">
                                {coreSyncData.statistics.successful_syncs}
                            </div>
                            <div className="text-sm text-gray-300">
                                成功同步
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-300">
                                {coreSyncData.statistics.average_sync_time_ms.toFixed(
                                    1
                                )}
                                ms
                            </div>
                            <div className="text-sm text-gray-300">
                                平均同步時間
                            </div>
                        </div>
                        <div className="text-center">
                            <div className="text-3xl font-bold text-green-300">
                                {coreSyncData.statistics.uptime_percentage.toFixed(
                                    1
                                )}
                                %
                            </div>
                            <div className="text-sm text-gray-300">
                                系統正常運行率
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-gray-400">無性能指標數據</div>
                )}
            </div>

            {/* Two-Point Prediction Visualization */}
            <div className="bg-gradient-to-br from-orange-900 to-orange-800 rounded-lg p-6 border border-orange-700">
                <h3 className="text-xl font-bold mb-4 flex items-center">
                    📈 二點預測可視化
                </h3>

                {handoverPrediction ? (
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span>預測ID</span>
                            <span className="font-mono text-orange-200">
                                {handoverPrediction.prediction_id}
                            </span>
                        </div>

                        <div className="flex items-center justify-between">
                            <span>換手需求</span>
                            <span
                                className={`px-3 py-1 rounded-full text-xs ${
                                    handoverPrediction.handover_required
                                        ? 'bg-red-600 text-red-100'
                                        : 'bg-green-600 text-green-100'
                                }`}
                            >
                                {handoverPrediction.handover_required
                                    ? '🔄 需要換手'
                                    : '✅ 保持連接'}
                            </span>
                        </div>

                        {handoverPrediction.handover_trigger_time && (
                            <div className="flex items-center justify-between">
                                <span>預測換手時間</span>
                                <span className="font-mono text-orange-200">
                                    {handoverPrediction.handover_trigger_time.toFixed(
                                        2
                                    )}
                                    s
                                </span>
                            </div>
                        )}

                        <div className="mt-4 space-y-2">
                            <div className="text-sm font-medium">
                                當前衛星 → 目標衛星
                            </div>
                            <div className="flex items-center justify-between bg-orange-800 bg-opacity-50 rounded p-2">
                                <div className="text-sm">
                                    <div className="font-medium">
                                        {
                                            handoverPrediction.current_satellite
                                                .name
                                        }
                                    </div>
                                    <div className="text-orange-200">
                                        信號:{' '}
                                        {handoverPrediction.current_satellite.signal_strength.toFixed(
                                            1
                                        )}{' '}
                                        dBm
                                    </div>
                                </div>
                                <div className="text-2xl">→</div>
                                <div className="text-sm text-right">
                                    <div className="font-medium">
                                        {
                                            handoverPrediction.future_satellite
                                                .name
                                        }
                                    </div>
                                    <div className="text-orange-200">
                                        信號:{' '}
                                        {handoverPrediction.future_satellite.signal_strength.toFixed(
                                            1
                                        )}{' '}
                                        dBm
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="text-gray-400">無預測數據</div>
                )}
            </div>
        </div>
    )
}

// Prediction View Component
const PredictionView: React.FC<{
    prediction: HandoverPrediction | null
    loading: boolean
}> = ({ prediction, loading }) => {
    if (loading) {
        return (
            <div className="text-center py-12 text-gray-400">
                🔄 載入預測數據中...
            </div>
        )
    }

    if (!prediction) {
        return (
            <div className="text-center py-12 text-gray-400">
                無預測數據可用
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Prediction Overview */}
            <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-6 border border-blue-700">
                <h3 className="text-2xl font-bold mb-4">🎯 換手預測總覽</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                        <div className="text-4xl mb-2">🆔</div>
                        <div className="font-mono text-sm text-blue-200">
                            {prediction.prediction_id}
                        </div>
                        <div className="text-gray-400">預測ID</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl mb-2">📱</div>
                        <div className="font-mono text-sm text-blue-200">
                            {prediction.ue_id}
                        </div>
                        <div className="text-gray-400">用戶設備ID</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl mb-2">🛰️</div>
                        <div className="font-mono text-sm text-blue-200">
                            {prediction.satellite_id}
                        </div>
                        <div className="text-gray-400">目標衛星ID</div>
                    </div>
                </div>
            </div>

            {/* Satellite Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gradient-to-br from-green-900 to-green-800 rounded-lg p-6 border border-green-700">
                    <h4 className="text-xl font-bold mb-4 text-green-300">
                        📡 當前衛星
                    </h4>
                    <div className="space-y-3">
                        <div className="flex justify-between">
                            <span>名稱:</span>
                            <span className="font-medium">
                                {prediction.current_satellite.name}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>ID:</span>
                            <span className="font-mono text-sm">
                                {prediction.current_satellite.satellite_id}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>信號強度:</span>
                            <span className="font-medium">
                                {prediction.current_satellite.signal_strength.toFixed(
                                    1
                                )}{' '}
                                dBm
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>仰角:</span>
                            <span className="font-medium">
                                {prediction.current_satellite.elevation.toFixed(
                                    1
                                )}
                                °
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>距離:</span>
                            <span className="font-medium">
                                {prediction.current_satellite.distance_km.toFixed(
                                    1
                                )}{' '}
                                km
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-gradient-to-br from-orange-900 to-orange-800 rounded-lg p-6 border border-orange-700">
                    <h4 className="text-xl font-bold mb-4 text-orange-300">
                        🎯 目標衛星
                    </h4>
                    <div className="space-y-3">
                        <div className="flex justify-between">
                            <span>名稱:</span>
                            <span className="font-medium">
                                {prediction.future_satellite.name}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>ID:</span>
                            <span className="font-mono text-sm">
                                {prediction.future_satellite.satellite_id}
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>信號強度:</span>
                            <span className="font-medium">
                                {prediction.future_satellite.signal_strength.toFixed(
                                    1
                                )}{' '}
                                dBm
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>仰角:</span>
                            <span className="font-medium">
                                {prediction.future_satellite.elevation.toFixed(
                                    1
                                )}
                                °
                            </span>
                        </div>
                        <div className="flex justify-between">
                            <span>距離:</span>
                            <span className="font-medium">
                                {prediction.future_satellite.distance_km.toFixed(
                                    1
                                )}{' '}
                                km
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Handover Decision */}
            <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-6 border border-purple-700">
                <h4 className="text-xl font-bold mb-4">🔄 換手決策</h4>
                <div className="flex items-center justify-center">
                    <div
                        className={`text-6xl p-8 rounded-full ${
                            prediction.handover_required
                                ? 'bg-red-800 text-red-300'
                                : 'bg-green-800 text-green-300'
                        }`}
                    >
                        {prediction.handover_required ? '🔄' : '✅'}
                    </div>
                </div>
                <div className="text-center mt-4">
                    <div className="text-2xl font-bold">
                        {prediction.handover_required
                            ? '需要執行換手'
                            : '維持當前連接'}
                    </div>
                    {prediction.handover_trigger_time && (
                        <div className="text-lg text-purple-300 mt-2">
                            預計換手時間:{' '}
                            {prediction.handover_trigger_time.toFixed(2)} 秒
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

// Sync View Component
const SyncView: React.FC<{
    coreSyncData: CoreSyncData | null
    loading: boolean
}> = ({ coreSyncData, loading }) => {
    if (loading) {
        return (
            <div className="text-center py-12 text-gray-400">
                🔄 載入同步數據中...
            </div>
        )
    }

    if (!coreSyncData) {
        return (
            <div className="text-center py-12 text-gray-400">
                無同步數據可用
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Service Status */}
            <div className="bg-gradient-to-r from-green-900 to-blue-900 rounded-lg p-6 border border-green-700">
                <h3 className="text-2xl font-bold mb-4">⚡ 服務狀態</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                        <div
                            className={`text-6xl mb-2 ${
                                coreSyncData.service_info.is_running
                                    ? 'text-green-400'
                                    : 'text-red-400'
                            }`}
                        >
                            {coreSyncData.service_info.is_running ? '✅' : '❌'}
                        </div>
                        <div className="font-bold">
                            {coreSyncData.service_info.is_running
                                ? '運行中'
                                : '已停止'}
                        </div>
                        <div className="text-gray-400">服務狀態</div>
                    </div>
                    <div className="text-center">
                        <div className="text-4xl font-bold text-blue-300 mb-2">
                            {coreSyncData.service_info.uptime_hours.toFixed(1)}
                        </div>
                        <div className="font-bold">小時</div>
                        <div className="text-gray-400">運行時間</div>
                    </div>
                    <div className="text-center">
                        <div className="text-lg font-mono text-green-300 mb-2">
                            {coreSyncData.service_info.core_sync_state}
                        </div>
                        <div className="font-bold">同步狀態</div>
                        <div className="text-gray-400">核心狀態</div>
                    </div>
                </div>
            </div>

            {/* Statistics */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-lg p-6 border border-blue-700">
                    <h4 className="text-xl font-bold mb-4">📊 統計數據</h4>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span>總同步操作:</span>
                            <span className="text-2xl font-bold text-blue-300">
                                {coreSyncData.statistics.total_sync_operations.toLocaleString()}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span>成功同步:</span>
                            <span className="text-2xl font-bold text-green-300">
                                {coreSyncData.statistics.successful_syncs.toLocaleString()}
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span>成功率:</span>
                            <span className="text-2xl font-bold text-green-300">
                                {(
                                    (coreSyncData.statistics.successful_syncs /
                                        coreSyncData.statistics
                                            .total_sync_operations) *
                                    100
                                ).toFixed(1)}
                                %
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-lg p-6 border border-purple-700">
                    <h4 className="text-xl font-bold mb-4">⏱️ 性能指標</h4>
                    <div className="space-y-4">
                        <div className="text-center">
                            <div className="text-4xl font-bold text-purple-300 mb-2">
                                {coreSyncData.statistics.average_sync_time_ms.toFixed(
                                    1
                                )}
                            </div>
                            <div className="font-bold">毫秒</div>
                            <div className="text-gray-400">平均同步時間</div>
                        </div>
                        <div className="text-center">
                            <div className="text-4xl font-bold text-green-300 mb-2">
                                {coreSyncData.statistics.uptime_percentage.toFixed(
                                    1
                                )}
                            </div>
                            <div className="font-bold">%</div>
                            <div className="text-gray-400">正常運行率</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

// Satellites View Component
const SatellitesView: React.FC<{
    satelliteData: SatelliteData | null
    loading: boolean
}> = ({ satelliteData, loading }) => {
    if (loading) {
        return (
            <div className="text-center py-12 text-gray-400">
                🔄 載入衛星數據中...
            </div>
        )
    }

    if (!satelliteData || !satelliteData.satellites.length) {
        return (
            <div className="text-center py-12 text-gray-400">
                無可見衛星數據
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Overview */}
            <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-lg p-6 border border-blue-700">
                <h3 className="text-2xl font-bold mb-4">🛰️ 可見衛星總覽</h3>
                <div className="text-center">
                    <div className="text-6xl font-bold text-blue-300 mb-2">
                        {satelliteData.total_visible}
                    </div>
                    <div className="text-xl">顆可見衛星</div>
                </div>
            </div>

            {/* Satellites Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {satelliteData.satellites.map((satellite, index) => (
                    <div
                        key={satellite.norad_id}
                        className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-lg p-4 border border-gray-600 hover:border-blue-500 transition-colors"
                    >
                        <div className="flex items-center justify-between mb-3">
                            <h4 className="font-bold text-lg truncate">
                                {satellite.name}
                            </h4>
                            <span className="text-xs bg-blue-600 text-blue-100 px-2 py-1 rounded">
                                #{index + 1}
                            </span>
                        </div>

                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span>NORAD ID:</span>
                                <span className="font-mono">
                                    {satellite.norad_id}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>仰角:</span>
                                <span
                                    className={`font-bold ${
                                        satellite.signal_quality.elevation_deg >
                                        45
                                            ? 'text-green-300'
                                            : satellite.signal_quality
                                                  .elevation_deg > 20
                                            ? 'text-yellow-300'
                                            : 'text-red-300'
                                    }`}
                                >
                                    {satellite.signal_quality.elevation_deg.toFixed(
                                        1
                                    )}
                                    °
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>方位角:</span>
                                <span className="font-bold">
                                    {satellite.position.azimuth.toFixed(1)}°
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span>距離:</span>
                                <span className="font-bold">
                                    {satellite.signal_quality.range_km.toFixed(
                                        0
                                    )}{' '}
                                    km
                                </span>
                            </div>
                        </div>

                        {/* Signal Quality Indicator */}
                        <div className="mt-3 w-full bg-gray-600 rounded-full h-2">
                            <div
                                className={`h-2 rounded-full ${
                                    satellite.signal_quality.elevation_deg > 45
                                        ? 'bg-green-500'
                                        : satellite.signal_quality
                                              .elevation_deg > 20
                                        ? 'bg-yellow-500'
                                        : 'bg-red-500'
                                }`}
                                style={{
                                    width: `${Math.min(
                                        satellite.signal_quality.elevation_deg,
                                        90
                                    )}%`,
                                }}
                            />
                        </div>
                        <div className="text-xs text-gray-400 mt-1 text-center">
                            信號品質:{' '}
                            {satellite.signal_quality.elevation_deg > 45
                                ? '優良'
                                : satellite.signal_quality.elevation_deg > 20
                                ? '良好'
                                : '一般'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

export default withErrorBoundary(LEOHandoverManagementModal, {
    level: 'component',
    fallback: <div className="text-red-500 p-4">LEO 換手管理系統載入失敗</div>,
})
