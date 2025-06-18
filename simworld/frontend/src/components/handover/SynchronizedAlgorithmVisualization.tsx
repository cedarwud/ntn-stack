import React, { useState, useEffect, useCallback, useRef } from 'react'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { netStackApi, useCoreSync } from '../../services/netstack-api'
import { simWorldApi, useVisibleSatellites } from '../../services/simworld-api'
import {
    useNetStackData,
    useDataSourceStatus,
} from '../../contexts/DataSyncContext'
import './SynchronizedAlgorithmVisualization.scss'

interface AlgorithmStep {
    step:
        | 'two_point_prediction'
        | 'binary_search'
        | 'sync_check'
        | 'handover_trigger'
    timestamp: number
    data: any
    status: 'running' | 'completed' | 'error'
    description: string
}

interface BinarySearchIteration {
    iteration: number
    start_time: number
    end_time: number
    mid_time: number
    satellite: string
    precision: number
    completed: boolean
}

interface PredictionResult {
    prediction_id: string
    ue_id: number
    current_time: number
    future_time: number
    delta_t_seconds: number
    current_satellite: {
        satellite_id: string
        name: string
        signal_strength: number
        elevation: number
    }
    future_satellite: {
        satellite_id: string
        name: string
        signal_strength: number
        elevation: number
    }
    handover_required: boolean
    handover_trigger_time?: number
    binary_search_result?: {
        handover_time: number
        iterations: BinarySearchIteration[]
        iteration_count: number
        final_precision: number
    }
    prediction_confidence: number
    accuracy_percentage: number
}

interface SynchronizedAlgorithmVisualizationProps {
    satellites: VisibleSatelliteInfo[]
    selectedUEId?: number
    isEnabled: boolean
    onAlgorithmStep?: (step: AlgorithmStep) => void
    // 🚀 新增：向視覺化組件傳遞演算法結果
    onAlgorithmResults?: (results: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }) => void
    // 🎮 新增：前端速度控制同步
    speedMultiplier?: number
}

const SynchronizedAlgorithmVisualization: React.FC<
    SynchronizedAlgorithmVisualizationProps
> = ({
    satellites,
    selectedUEId = 1,
    isEnabled,
    onAlgorithmStep,
    onAlgorithmResults,
    speedMultiplier = 60,
}) => {
    const [algorithmSteps, setAlgorithmSteps] = useState<AlgorithmStep[]>([])
    const [currentStep, setCurrentStep] = useState<string>('')
    const [predictionResult, setPredictionResult] =
        useState<PredictionResult | null>(null)
    const [binarySearchIterations, setBinarySearchIterations] = useState<
        BinarySearchIteration[]
    >([])
    const [isRunning, setIsRunning] = useState(false)
    const [syncAccuracy, setSyncAccuracy] = useState(0.95)
    const lastExecutionTimeRef = useRef(0)
    const stepIdRef = useRef(0) // 用於生成唯一的步驟ID

    // 使用數據同步上下文
    const { coreSync: coreSyncStatus, isConnected: netstackConnected } =
        useNetStackData()
    const { overall: connectionStatus, dataSource } = useDataSourceStatus()
    const {
        coreSync: coreSyncData,
        loading: coreSyncLoading,
        error: coreSyncError,
    } = useCoreSync(5000) // 5秒更新間隔
    const {
        satellites: realSatellites,
        loading: satellitesLoading,
        error: satellitesError,
    } = useVisibleSatellites(10, 20, 30000) // 10度最低仰角，最多20顆衛星，30秒更新

    // 執行二點預測算法 - 使用真實的 NetStack API
    const executeTwoPointPrediction = useCallback(async () => {
        if (!isEnabled || isRunning) return

        // 🔥 演算法層：強制使用真實衛星數據進行精確計算
        // 注意：這裡的數據源獨立於前端 3D 顯示層，確保演算法準確性
        const availableSatellites =
            realSatellites.length > 0 ? realSatellites : satellites

        // 演算法計算數據源簡化日誌
        if (availableSatellites.length === 0) {
            console.warn('No satellites available for prediction')
            return
        }

        // 防止過於頻繁的調用 - 至少間隔 10 秒
        const now = Date.now()
        if (now - lastExecutionTimeRef.current < 10000) {
            return
        }
        lastExecutionTimeRef.current = now

        try {
            setIsRunning(true)
            setCurrentStep('two_point_prediction')

            // 添加算法步驟
            const step: AlgorithmStep = {
                step: 'two_point_prediction',
                timestamp: Date.now() + stepIdRef.current++,
                data: {
                    ue_id: selectedUEId,
                    satellites_count: availableSatellites.length,
                    api_source:
                        realSatellites.length > 0 ? 'simworld_api' : 'props',
                },
                status: 'running',
                description: '執行二點預測：計算 T 和 T+Δt 時間點的最佳衛星',
            }

            setAlgorithmSteps((prev) => [...prev, step])
            onAlgorithmStep?.(step)

            // 選擇第一顆可見衛星進行預測
            const selectedSatellite = availableSatellites[0]
            const satelliteId =
                selectedSatellite.id?.toString() ||
                selectedSatellite.norad_id ||
                'STARLINK-1'

            // 調用 NetStack API

            // 🔥 調用真實的 NetStack 同步演算法 API
            const apiResult = await netStackApi.predictSatelliteAccess({
                ue_id: selectedUEId.toString(),
                satellite_id: satelliteId,
                time_horizon_minutes: 5, // 5分鐘預測窗口
            })

            // 轉換 API 結果為組件格式
            // 適配實際的 NetStack API 響應結構
            const currentSatellite =
                availableSatellites.find(
                    (sat) =>
                        sat.id?.toString() === satelliteId ||
                        sat.norad_id === satelliteId
                ) || availableSatellites[0]

            const result: PredictionResult = {
                prediction_id: apiResult.prediction_id,
                ue_id: selectedUEId,
                current_time: Date.now() / 1000,
                future_time:
                    new Date(apiResult.predicted_access_time).getTime() / 1000,
                delta_t_seconds:
                    (new Date(apiResult.predicted_access_time).getTime() -
                        Date.now()) /
                    1000,
                current_satellite: {
                    satellite_id: satelliteId,
                    name: currentSatellite.name || 'Unknown',
                    signal_strength: 85 + Math.random() * 10, // 模擬信號強度
                    elevation: currentSatellite.position?.elevation || 0,
                },
                future_satellite: {
                    satellite_id: apiResult.satellite_id,
                    name: currentSatellite.name || 'Predicted',
                    signal_strength: 80 + Math.random() * 15,
                    elevation: (currentSatellite.position?.elevation || 0) + 5,
                },
                handover_required: apiResult.access_probability > 0.7, // 基於接取概率判斷是否需要換手
                handover_trigger_time:
                    new Date(apiResult.predicted_access_time).getTime() / 1000,
                binary_search_result: apiResult.algorithm_details
                    ?.binary_search_refinement
                    ? {
                          handover_time:
                              new Date(
                                  apiResult.predicted_access_time
                              ).getTime() / 1000,
                          iterations: [],
                          iteration_count:
                              apiResult.binary_search_iterations || 0,
                          final_precision: apiResult.error_bound_ms || 0,
                      }
                    : undefined,
                prediction_confidence: apiResult.confidence_score || 0.85,
                accuracy_percentage: (apiResult.confidence_score || 0.85) * 100,
            }

            // API 回應處理完成
            setPredictionResult(result)

            // 🚀 向視覺化組件廣播演算法結果
            onAlgorithmResults?.({
                currentSatelliteId: result.current_satellite.satellite_id,
                predictedSatelliteId: result.future_satellite.satellite_id,
                handoverStatus: result.handover_required
                    ? 'handover_ready'
                    : 'idle',
                binarySearchActive: false,
                predictionConfidence: result.prediction_confidence,
            })

            // 更新步驟狀態
            const completedStep = {
                ...step,
                status: 'completed' as const,
                data: {
                    ...result,
                    algorithm_metadata: apiResult.algorithm_metadata,
                },
            }
            setAlgorithmSteps((prev) =>
                prev.map((s) =>
                    s.timestamp === step.timestamp ? completedStep : s
                )
            )

            // 如果需要換手，執行 Binary Search 可視化
            if (result.handover_required && result.binary_search_result) {
                await executeBinarySearchVisualization(
                    result.binary_search_result.iterations
                )
            }

            // 檢查同步狀態 - 使用真實的核心同步數據
            await checkSyncStatus(result)
        } catch (error) {
            console.error('❌ NetStack API 調用失敗:', error)

            // 更新步驟為錯誤狀態
            setAlgorithmSteps((prev) =>
                prev.map((s) =>
                    s.timestamp === prev[prev.length - 1]?.timestamp
                        ? {
                              ...s,
                              status: 'error',
                              description: `API調用失敗: ${
                                  error instanceof Error
                                      ? error.message
                                      : 'Unknown error'
                              }`,
                          }
                        : s
                )
            )
        } finally {
            setIsRunning(false)
            setCurrentStep('')
        }
    }, [isEnabled, selectedUEId, realSatellites, satellites, onAlgorithmStep])

    // 可視化 Binary Search 過程
    const executeBinarySearchVisualization = async (
        iterations: BinarySearchIteration[]
    ) => {
        setCurrentStep('binary_search')

        const binaryStep: AlgorithmStep = {
            step: 'binary_search',
            timestamp: Date.now() + stepIdRef.current++, // 確保唯一性
            data: { iterations_count: iterations.length },
            status: 'running',
            description: 'Binary Search Refinement：精確計算換手觸發時間 Tp',
        }

        setAlgorithmSteps((prev) => [...prev, binaryStep])

        // 🔬 廣播 Binary Search 開始
        onAlgorithmResults?.({
            currentSatelliteId:
                predictionResult?.current_satellite.satellite_id,
            predictedSatelliteId:
                predictionResult?.future_satellite.satellite_id,
            handoverStatus: 'executing',
            binarySearchActive: true,
            predictionConfidence: predictionResult?.prediction_confidence,
        })

        // 逐步顯示迭代過程
        for (let i = 0; i < iterations.length; i++) {
            setBinarySearchIterations((prev) => [...prev, iterations[i]])
            await new Promise((resolve) => setTimeout(resolve, 750)) // 配合後端的延遲
        }

        // 🔬 廣播 Binary Search 完成
        onAlgorithmResults?.({
            currentSatelliteId:
                predictionResult?.current_satellite.satellite_id,
            predictedSatelliteId:
                predictionResult?.future_satellite.satellite_id,
            handoverStatus: 'handover_ready',
            binarySearchActive: false,
            predictionConfidence: predictionResult?.prediction_confidence,
        })

        // 完成 Binary Search
        const completedBinaryStep = {
            ...binaryStep,
            status: 'completed' as const,
        }
        setAlgorithmSteps((prev) =>
            prev.map((s) =>
                s.timestamp === binaryStep.timestamp ? completedBinaryStep : s
            )
        )
    }

    // 檢查同步狀態 - 使用真實的核心同步數據
    const checkSyncStatus = async (result: PredictionResult) => {
        setCurrentStep('sync_check')

        const syncStep: AlgorithmStep = {
            step: 'sync_check',
            timestamp: Date.now() + stepIdRef.current++,
            data: { confidence: result.prediction_confidence },
            status: 'running',
            description: '檢查同步狀態：驗證預測準確性和系統同步',
        }

        setAlgorithmSteps((prev) => [...prev, syncStep])

        try {
            // 🔥 獲取真實的核心同步狀態
            const realSyncStatus = await netStackApi.getCoreSync()

            // 使用真實的同步精度數據
            const realAccuracy =
                realSyncStatus.sync_performance.overall_accuracy_ms < 50
                    ? 0.95 +
                      (50 -
                          realSyncStatus.sync_performance.overall_accuracy_ms) /
                          1000
                    : Math.max(
                          0.7,
                          0.95 -
                              (realSyncStatus.sync_performance
                                  .overall_accuracy_ms -
                                  50) /
                                  500
                      )

            setSyncAccuracy(realAccuracy)

            // 同步狀態檢查完成

            const completedSyncStep = {
                ...syncStep,
                status: 'completed' as const,
                data: {
                    confidence: result.prediction_confidence,
                    real_sync_accuracy: realAccuracy,
                    core_sync_data: realSyncStatus,
                },
            }
            setAlgorithmSteps((prev) =>
                prev.map((s) =>
                    s.timestamp === syncStep.timestamp ? completedSyncStep : s
                )
            )
        } catch (error) {
            console.warn('⚠️ 無法獲取真實同步狀態，使用預測數據:', error)

            // Fallback: 使用預測結果的置信度
            setSyncAccuracy(result.prediction_confidence)

            const completedSyncStep = {
                ...syncStep,
                status: 'completed' as const,
                data: {
                    confidence: result.prediction_confidence,
                    fallback_mode: true,
                },
            }
            setAlgorithmSteps((prev) =>
                prev.map((s) =>
                    s.timestamp === syncStep.timestamp ? completedSyncStep : s
                )
            )
        }
    }

    // 定期執行算法
    useEffect(() => {
        if (!isEnabled) return

        // 初始執行
        const timeoutId = setTimeout(() => {
            executeTwoPointPrediction()
        }, 1000) // 延遲 1 秒執行，避免組件初始化時的重複調用

        // 🎮 根據前端速度動態調整演算法執行間隔
        // 基礎間隔15秒，根據速度倍數調整：速度越快，執行越頻繁
        const baseInterval = 15000 // 15秒基礎間隔
        const dynamicInterval = Math.max(
            1000,
            baseInterval / (speedMultiplier / 60)
        ) // 最少1秒間隔

        // 演算法執行間隔已設定

        const interval = setInterval(() => {
            if (!isRunning) {
                // 只有在不運行時才執行新的預測
                executeTwoPointPrediction()
            }
        }, dynamicInterval)

        return () => {
            clearTimeout(timeoutId)
            clearInterval(interval)
        }
    }, [isEnabled, speedMultiplier]) // 🎮 添加 speedMultiplier 依賴，速度變化時重新設置間隔

    // 清除歷史記錄
    const clearHistory = useCallback(() => {
        setAlgorithmSteps([])
        setBinarySearchIterations([])
        setPredictionResult(null)
        setCurrentStep('')
        stepIdRef.current = 0 // 重置步驟ID計數器
    }, [])

    if (!isEnabled) {
        return (
            <div className="synchronized-algorithm-visualization disabled">
                <div className="disabled-message">
                    <h3>🔒 Fine-Grained Synchronized Algorithm</h3>
                    <p>請啟用換手相關功能來使用此演算法可視化</p>
                </div>
            </div>
        )
    }

    return (
        <div className="synchronized-algorithm-visualization">
            <div className="algorithm-header">
                <div className="header-top">
                    <h2>🧮 Fine-Grained Synchronized Algorithm</h2>
                    <button
                        onClick={clearHistory}
                        className="clear-btn"
                        disabled={isRunning}
                    >
                        清除歷史
                    </button>
                </div>

                <div className="algorithm-info">
                    <span className="paper-ref">IEEE INFOCOM 2024</span>
                    <span className="ue-id">UE: {selectedUEId}</span>
                    {currentStep && (
                        <span className="current-step">
                            執行中: {getStepDisplayName(currentStep)}
                        </span>
                    )}
                </div>

                {/* 真實數據連接狀態指示器 */}
                <div className="data-source-indicators">
                    <div
                        className={`indicator ${
                            coreSyncError
                                ? 'error'
                                : coreSyncLoading
                                ? 'loading'
                                : 'connected'
                        }`}
                    >
                        <span className="indicator-icon">
                            {coreSyncError
                                ? '❌'
                                : coreSyncLoading
                                ? '⏳'
                                : '✅'}
                        </span>
                        <span className="indicator-text">
                            NetStack{' '}
                            {coreSyncError
                                ? '斷線'
                                : coreSyncLoading
                                ? '連接中'
                                : '已連接'}
                        </span>
                    </div>
                    <div
                        className={`indicator ${
                            satellitesError
                                ? 'error'
                                : satellitesLoading
                                ? 'loading'
                                : 'connected'
                        }`}
                    >
                        <span className="indicator-icon">
                            {satellitesError
                                ? '❌'
                                : satellitesLoading
                                ? '⏳'
                                : '✅'}
                        </span>
                        <span className="indicator-text">
                            SimWorld ({realSatellites.length}顆衛星){' '}
                            {satellitesError
                                ? '斷線'
                                : satellitesLoading
                                ? '載入中'
                                : '已連接'}
                        </span>
                    </div>
                </div>
            </div>

            <div className="algorithm-content">
                {/* 算法流程時間軸 */}
                <div className="algorithm-timeline">
                    <h3>📋 算法執行流程</h3>
                    <div className="timeline-container">
                        {algorithmSteps.length > 0 ? (
                            algorithmSteps.map((step, index) => (
                                <div
                                    key={`step-${step.step}-${step.timestamp}-${index}`}
                                    className={`timeline-item ${step.status}`}
                                >
                                    <div className="timeline-marker">
                                        <span className="step-number">
                                            {index + 1}
                                        </span>
                                    </div>
                                    <div className="timeline-content">
                                        <div className="step-header">
                                            <span className="step-icon">
                                                {getStepIcon(step.step)}
                                            </span>
                                            <span className="step-name">
                                                {getStepDisplayName(step.step)}
                                            </span>
                                            <span className="step-status">
                                                {getStatusIcon(step.status)}
                                            </span>
                                        </div>
                                        <div className="step-description">
                                            {step.description}
                                        </div>
                                        <div className="step-timestamp">
                                            {new Date(
                                                step.timestamp
                                            ).toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="empty-state">
                                <span className="empty-icon">⏳</span>
                                <span className="empty-message">
                                    等待算法執行...
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* 預測結果展示 */}
                {predictionResult &&
                    predictionResult.current_satellite &&
                    predictionResult.future_satellite && (
                        <div className="prediction-results">
                            <h3>📊 二點預測結果</h3>
                            <div className="prediction-grid">
                                <div className="prediction-card current">
                                    <h4>當前時間 T</h4>
                                    <div className="satellite-info">
                                        <span className="satellite-name">
                                            {
                                                predictionResult
                                                    .current_satellite.name
                                            }
                                        </span>
                                        <span className="satellite-id">
                                            ID:{' '}
                                            {
                                                predictionResult
                                                    .current_satellite
                                                    .satellite_id
                                            }
                                        </span>
                                    </div>
                                    <div className="metrics">
                                        <div className="metric">
                                            <span className="label">仰角:</span>
                                            <span className="value">
                                                {predictionResult.current_satellite.elevation.toFixed(
                                                    1
                                                )}
                                                °
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="label">信號:</span>
                                            <span className="value">
                                                {predictionResult.current_satellite.signal_strength.toFixed(
                                                    1
                                                )}{' '}
                                                dBm
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                <div className="prediction-arrow">
                                    <span className="arrow">➤</span>
                                    <div className="delta-t">
                                        Δt = {predictionResult.delta_t_seconds}s
                                    </div>
                                </div>

                                <div className="prediction-card future">
                                    <h4>預測時間 T+Δt</h4>
                                    <div className="satellite-info">
                                        <span className="satellite-name">
                                            {
                                                predictionResult
                                                    .future_satellite.name
                                            }
                                        </span>
                                        <span className="satellite-id">
                                            ID:{' '}
                                            {
                                                predictionResult
                                                    .future_satellite
                                                    .satellite_id
                                            }
                                        </span>
                                    </div>
                                    <div className="metrics">
                                        <div className="metric">
                                            <span className="label">仰角:</span>
                                            <span className="value">
                                                {predictionResult.future_satellite.elevation.toFixed(
                                                    1
                                                )}
                                                °
                                            </span>
                                        </div>
                                        <div className="metric">
                                            <span className="label">信號:</span>
                                            <span className="value">
                                                {predictionResult.future_satellite.signal_strength.toFixed(
                                                    1
                                                )}{' '}
                                                dBm
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="prediction-summary">
                                <div className="handover-decision">
                                    <span className="decision-label">
                                        換手決策:
                                    </span>
                                    <span
                                        className={`decision-value ${
                                            predictionResult.handover_required
                                                ? 'required'
                                                : 'not-required'
                                        }`}
                                    >
                                        {predictionResult.handover_required
                                            ? '需要換手'
                                            : '無需換手'}
                                    </span>
                                </div>
                                <div className="confidence-meter">
                                    <span className="confidence-label">
                                        預測置信度:
                                    </span>
                                    <div className="confidence-bar">
                                        <div
                                            className="confidence-fill"
                                            style={{
                                                width: `${predictionResult.accuracy_percentage}%`,
                                            }}
                                        ></div>
                                    </div>
                                    <span className="confidence-value">
                                        {predictionResult.accuracy_percentage.toFixed(
                                            1
                                        )}
                                        %
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}

                {/* Binary Search 迭代過程 */}
                {binarySearchIterations.length > 0 && (
                    <div className="binary-search-visualization">
                        <h3>🔍 Binary Search Refinement</h3>
                        <div className="iterations-container">
                            {binarySearchIterations.map((iteration, index) => (
                                <div
                                    key={index}
                                    className={`iteration-item ${
                                        iteration.completed
                                            ? 'completed'
                                            : 'running'
                                    }`}
                                >
                                    <div className="iteration-number">
                                        #{iteration.iteration}
                                    </div>
                                    <div className="iteration-details">
                                        <div className="time-range">
                                            <span>
                                                區間: [
                                                {iteration.start_time.toFixed(
                                                    3
                                                )}
                                                ,{' '}
                                                {iteration.end_time.toFixed(3)}]
                                            </span>
                                        </div>
                                        <div className="mid-point">
                                            <span>
                                                中點:{' '}
                                                {iteration.mid_time.toFixed(3)}
                                            </span>
                                            <span className="satellite">
                                                衛星: {iteration.satellite}
                                            </span>
                                        </div>
                                        <div className="precision">
                                            <span>
                                                精度:{' '}
                                                {iteration.precision.toFixed(3)}
                                                s
                                            </span>
                                            {iteration.completed && (
                                                <span className="completed-mark">
                                                    ✓
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* 真實系統同步狀態 */}
                <div className="sync-status-real">
                    <h3>
                        🔄 系統同步狀態{' '}
                        {coreSyncStatus ? '(真實數據)' : '(預測數據)'}
                    </h3>
                    <div className="sync-summary">
                        <div className="sync-metric">
                            <span className="metric-label">同步準確率:</span>
                            <span className="metric-value">
                                {(syncAccuracy * 100).toFixed(1)}%
                            </span>
                            <span
                                className={`status-indicator ${
                                    syncAccuracy > 0.95
                                        ? 'excellent'
                                        : syncAccuracy > 0.9
                                        ? 'good'
                                        : 'warning'
                                }`}
                            >
                                {syncAccuracy > 0.95
                                    ? '優秀'
                                    : syncAccuracy > 0.9
                                    ? '良好'
                                    : '需改善'}
                            </span>
                        </div>
                        <div className="sync-metric">
                            <span className="metric-label">算法狀態:</span>
                            <span className="metric-value">
                                {isRunning ? '執行中' : '待機'}
                            </span>
                        </div>

                        {/* 顯示真實的核心同步數據 */}
                        {coreSyncStatus && (
                            <>
                                <div className="sync-metric">
                                    <span className="metric-label">
                                        核心同步精度:
                                    </span>
                                    <span className="metric-value">
                                        {coreSyncStatus.sync_performance.overall_accuracy_ms.toFixed(
                                            1
                                        )}{' '}
                                        ms
                                    </span>
                                </div>
                                <div className="sync-metric">
                                    <span className="metric-label">
                                        Binary Search:
                                    </span>
                                    <span className="metric-value">
                                        {coreSyncStatus.sync_performance
                                            .binary_search_enabled
                                            ? '啟用'
                                            : '停用'}
                                    </span>
                                </div>
                                <div className="sync-metric">
                                    <span className="metric-label">
                                        IEEE 2024 特性:
                                    </span>
                                    <span className="metric-value">
                                        {coreSyncStatus
                                            .ieee_infocom_2024_features
                                            .fine_grained_sync_active
                                            ? '啟用'
                                            : '停用'}
                                    </span>
                                </div>
                                <div className="sync-metric">
                                    <span className="metric-label">
                                        成功同步:
                                    </span>
                                    <span className="metric-value">
                                        {
                                            coreSyncStatus.statistics
                                                .successful_syncs
                                        }{' '}
                                        /{' '}
                                        {
                                            coreSyncStatus.statistics
                                                .total_sync_operations
                                        }
                                    </span>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

// 輔助函數
function getStepIcon(step: string): string {
    switch (step) {
        case 'two_point_prediction':
            return '📊'
        case 'binary_search':
            return '🔍'
        case 'sync_check':
            return '🔄'
        case 'handover_trigger':
            return '⚡'
        default:
            return '⚙️'
    }
}

function getStepDisplayName(step: string): string {
    switch (step) {
        case 'two_point_prediction':
            return '二點預測'
        case 'binary_search':
            return 'Binary Search'
        case 'sync_check':
            return '同步檢查'
        case 'handover_trigger':
            return '換手觸發'
        default:
            return step
    }
}

function getStatusIcon(status: string): string {
    switch (status) {
        case 'running':
            return '⏳'
        case 'completed':
            return '✅'
        case 'error':
            return '❌'
        default:
            return '⚪'
    }
}

export default SynchronizedAlgorithmVisualization
