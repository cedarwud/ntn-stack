import React, { useState, useEffect, useCallback, useRef } from 'react'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { netStackApi, useCoreSync } from '../../services/netstack-api'
import { useVisibleSatellites } from '../../services/simworld-api'
import { useNetStackData } from '../../contexts/DataSyncContext'
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
    const { coreSync: coreSyncStatus } = useNetStackData()
    // const { overall: connectionStatus, dataSource } = useDataSourceStatus()
    const {
        status: _coreSyncData,
        loading: coreSyncLoading,
        error: coreSyncError,
    } = useCoreSync() // 5秒更新間隔
    const {
        satellites: realSatellites,
        loading: satellitesLoading,
        error: satellitesError,
    } = useVisibleSatellites(-10, 50, 120000) // -10度最低仰角，最多50顆衛星，120秒更新

    // 執行二點預測算法 - 使用真實的 NetStack API
    const executeTwoPointPrediction = useCallback(
        async (forceExecute = false) => {
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

            // 防止過於頻繁的調用 - 但允許手動強制執行
            const now = Date.now()
            if (!forceExecute && now - lastExecutionTimeRef.current < 10000) {
                // 只在手動執行時顯示頻率限制訊息
                if (forceExecute) {
                    console.log(
                        '⏱️ 執行頻率限制，跳過自動執行 (距離上次執行:',
                        Math.round((now - lastExecutionTimeRef.current) / 1000),
                        '秒)'
                    )
                }
                return
            }
            lastExecutionTimeRef.current = now

            // 只在手動執行時記錄詳細日誌
            if (forceExecute) {
                console.log('🚀 開始執行演算法: 手動觸發')
            }

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
                            realSatellites.length > 0
                                ? 'simworld_api'
                                : 'props',
                        execution_type: forceExecute ? 'manual' : 'automatic',
                    },
                    status: 'running',
                    description: `執行二點預測：計算 T 和 T+Δt 時間點的最佳衛星 (${
                        forceExecute ? '手動' : '自動'
                    }執行)`,
                }

                setAlgorithmSteps((prev) => [...prev, step])
                onAlgorithmStep?.(step)

                // 選擇第一顆可見衛星進行預測
                const selectedSatellite = availableSatellites[0]
                const satelliteId =
                    selectedSatellite.norad_id?.toString() || 'STARLINK-1'

                // 只在手動執行時記錄衛星選擇詳情
                if (forceExecute) {
                    console.log('🛰️ 選定衛星:', {
                        name: selectedSatellite.name,
                        norad_id: satelliteId,
                        total_satellites: availableSatellites.length,
                    })
                }

                // 🎯 動態時間間隔計算 - 基於speedMultiplier調整預測時間範圍
                const baseDeltaT = 15 * 60 // 基礎15分鐘
                const satelliteVariation = (parseInt(satelliteId) % 7) * 60 // 基於衛星ID的變化
                const timeVariation = Math.floor((Date.now() / 30000) % 10) * 30 // 每30秒變化
                const orbitVariation = Math.sin(Date.now() / 60000) * 120 // 軌道週期變化

                // 🎮 根據speedMultiplier調整預測時間範圍
                // speedMultiplier越大，預測時間間隔越短（更頻繁的換手）
                const speedFactor = Math.max(0.1, Math.min(10, speedMultiplier / 60)) // 0.1-10倍調整
                
                // 生成多個時間預測選項 (短期、中期、長期) - 根據速度調整
                const shortTermDelta = Math.max(60, (baseDeltaT * 0.3 + satelliteVariation * 0.2) / speedFactor) // 1-5分鐘
                const mediumTermDelta = Math.max(180, (baseDeltaT * 0.7 + satelliteVariation + timeVariation) / speedFactor) // 3-15分鐘  
                const longTermDelta = Math.max(300, (baseDeltaT * 1.2 + orbitVariation) / speedFactor) // 5-25分鐘

                // 隨機選擇一個預測時間 (模擬多種情況)
                const predictionOptions = [shortTermDelta, mediumTermDelta, longTermDelta]
                const selectedIndex = Math.floor((Date.now() / 10000) % predictionOptions.length)
                const dynamicDeltaT = Math.min(1800, predictionOptions[selectedIndex]) // 最大30分鐘

                const currentTimeStamp = Date.now()
                const futureTimeStamp = currentTimeStamp + dynamicDeltaT * 1000
                const deltaSeconds = dynamicDeltaT

                // 只在手動執行時記錄時間計算詳情
                if (forceExecute) {
                    console.log(
                        `🕐 多重時間預測: 短期=${Math.round(shortTermDelta)}s, 中期=${Math.round(mediumTermDelta)}s, 長期=${Math.round(longTermDelta)}s, 選中=${deltaSeconds}s (索引:${selectedIndex}, 速度因子:${speedFactor.toFixed(2)})`
                    )
                }

                // 🔥 調用真實的 NetStack 同步演算法 API
                let apiResult
                let usingFallback = false
                try {
                    // 只在手動執行時記錄API調用
                    if (forceExecute) {
                        console.log('📡 調用 NetStack API...')
                    }
                    const netStackResponse = await fetch(
                        `http://localhost:8080/api/v1/core-sync/prediction/satellite-access`,
                        {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                ue_id: `ue_${satelliteId}`,
                                satellite_id: satelliteId,
                                time_horizon_minutes: dynamicDeltaT / 60, // 使用動態計算的時間間隔
                            }),
                        }
                    )

                    if (netStackResponse.ok) {
                        apiResult = await netStackResponse.json()
                        // 只在手動執行時記錄API成功詳情
                        if (forceExecute) {
                            console.log('✅ NetStack API 調用成功:', apiResult)
                        }
                    } else {
                        throw new Error(
                            `NetStack API返回錯誤: ${netStackResponse.status}`
                        )
                    }
                } catch (apiError) {
                    console.warn(
                        '❌ NetStack API 調用失敗，使用本地預測:',
                        apiError
                    )
                    usingFallback = true
                    // Fallback: 使用本地預測邏輯
                    apiResult = {
                        prediction_id: `local_${currentTimeStamp}`,
                        predicted_access_time: new Date(
                            futureTimeStamp
                        ).toISOString(),
                        satellite_id: satelliteId,
                        confidence_score: 0.8,
                        access_probability: 0.85,
                        error_bound_ms: 1000,
                        binary_search_iterations: 3,
                        algorithm_details: {
                            two_point_prediction: {
                                time_t: new Date(
                                    currentTimeStamp
                                ).toISOString(),
                                time_t_delta: new Date(
                                    futureTimeStamp
                                ).toISOString(),
                            },
                            binary_search_refinement: {
                                iterations: 3,
                                converged: true,
                            },
                        },
                        algorithm_metadata: {
                            execution_time_ms: 50,
                            algorithm_version: 'local_fallback_v1.0',
                            ieee_infocom_2024_compliance: false,
                        },
                    }
                }

                // 轉換 API 結果為組件格式
                // 適配實際的 NetStack API 響應結構
                const currentSatellite =
                    availableSatellites.find(
                        (sat) => sat.norad_id?.toString() === satelliteId
                    ) || availableSatellites[0]

                // 🔧 選擇未來衛星 - 確保與當前衛星不同
                const futureSatellite = (() => {
                    // 首先嘗試根據API返回的satellite_id找到對應衛星
                    if (
                        apiResult.satellite_id &&
                        apiResult.satellite_id !== satelliteId
                    ) {
                        const foundSat = availableSatellites.find(
                            (sat) =>
                                sat.norad_id?.toString() ===
                                apiResult.satellite_id
                        )
                        if (foundSat) return foundSat
                    }

                    // 如果API沒有返回不同的衛星ID，選擇列表中的下一個衛星
                    const currentIndex = availableSatellites.findIndex(
                        (sat) => sat.norad_id?.toString() === satelliteId
                    )

                    if (currentIndex >= 0 && availableSatellites.length > 1) {
                        // 選擇下一個衛星，如果是最後一個則選第一個
                        const nextIndex =
                            (currentIndex + 1) % availableSatellites.length
                        return availableSatellites[nextIndex]
                    }

                    // 最後備用：選擇信號強度最高的不同衛星
                    const differentSatellites = availableSatellites.filter(
                        (sat) => sat.norad_id?.toString() !== satelliteId
                    )

                    if (differentSatellites.length > 0) {
                        // 按仰角排序，選擇仰角最高的
                        return differentSatellites.sort((a, b) => {
                            const elevationA =
                                'elevation_deg' in a
                                    ? a.elevation_deg
                                    : 'position' in a
                                    ? a.position?.elevation || 0
                                    : 0
                            const elevationB =
                                'elevation_deg' in b
                                    ? b.elevation_deg
                                    : 'position' in b
                                    ? b.position?.elevation || 0
                                    : 0
                            return elevationB - elevationA
                        })[0]
                    }

                    // 如果只有一顆衛星，返回當前衛星（但會在名稱上標示為預測）
                    return currentSatellite
                })()

                // 🔧 修復時間計算邏輯 - 統一使用UTC時間
                const currentTime = currentTimeStamp / 1000 // 使用之前定義的時間戳，轉換為UTC時間戳
                let futureTime: number
                let deltaT: number

                try {
                    // 嘗試解析API返回的時間 - API返回的是UTC時間
                    const apiTimeString = apiResult.predicted_access_time

                    // 🔧 修復瀏覽器時區問題：確保時間字符串被解析為UTC
                    // 如果時間字符串沒有時區標識，添加'Z'後綴表示UTC
                    const utcTimeString = apiTimeString.endsWith('Z')
                        ? apiTimeString
                        : apiTimeString + 'Z'
                    const apiTime = new Date(utcTimeString).getTime() / 1000 // 轉換為UTC時間戳

                    deltaT = apiTime - currentTime
                    futureTime = apiTime

                    // 詳細的調試信息
                    console.log('🕐 時間計算詳情 (修復時區):', {
                        using_fallback: usingFallback,
                        api_time_string_original: apiTimeString,
                        api_time_string_utc: utcTimeString,
                        current_time_utc: currentTime,
                        api_time_utc: apiTime,
                        delta_t: deltaT,
                        delta_t_minutes: Math.round((deltaT / 60) * 100) / 100,
                        is_valid_time:
                            !isNaN(apiTime) && isFinite(apiTime) && apiTime > 0,
                        current_date_utc: new Date(
                            currentTime * 1000
                        ).toISOString(),
                        api_date_utc: new Date(apiTime * 1000).toISOString(),
                        timezone_fix: 'Added Z suffix to ensure UTC parsing',
                        dynamic_delta_seconds: deltaSeconds,
                        source: usingFallback ? 'fallback' : 'netstack_api',
                    })

                    // 改善時間驗證：只有明顯錯誤的時間才被拒絕
                    const isValidTime =
                        !isNaN(apiTime) && isFinite(apiTime) && apiTime > 0
                    const isReasonableRange = deltaT > -300 && deltaT < 86400 // 過去5分鐘到未來24小時

                    if (!isValidTime || !isReasonableRange) {
                        console.warn('⚠️ 時間驗證失敗，使用動態計算值:', {
                            deltaT,
                            deltaT_minutes: deltaT / 60,
                            isValidTime,
                            isReasonableRange,
                            reason: !isValidTime
                                ? '無效時間'
                                : '時間範圍不合理',
                            fallback_seconds: deltaSeconds,
                            note: '使用動態計算的時間間隔',
                        })
                        deltaT = deltaSeconds // 使用動態計算的時間間隔
                        futureTime = currentTime + deltaT
                    } else {
                        console.log('✅ 使用API返回的真實時間差 (修復時區):', {
                            deltaT_seconds: deltaT,
                            deltaT_minutes:
                                Math.round((deltaT / 60) * 100) / 100,
                            source: usingFallback ? 'fallback' : 'netstack_api',
                            note: '時區修復成功，時間計算正常',
                        })
                    }
                } catch (timeError) {
                    console.warn('❌ 時間解析異常，使用動態計算值:', timeError)
                    deltaT = deltaSeconds // 使用動態計算的時間間隔
                    futureTime = currentTime + deltaT
                }

                const result: PredictionResult = {
                    prediction_id: apiResult.prediction_id,
                    ue_id: selectedUEId,
                    current_time: currentTime,
                    future_time: futureTime,
                    delta_t_seconds: deltaT,
                    current_satellite: {
                        satellite_id: satelliteId,
                        name: (currentSatellite.name || 'Unknown')
                            .replace(' [DTC]', '')
                            .replace('[DTC]', ''),
                        signal_strength: 85 + Math.random() * 10, // 模擬信號強度
                        elevation:
                            'position' in currentSatellite
                                ? currentSatellite.position?.elevation || 0
                                : currentSatellite.elevation_deg || 0,
                    },
                    future_satellite: {
                        satellite_id:
                            futureSatellite.norad_id?.toString() ||
                            apiResult.satellite_id,
                        name:
                            (futureSatellite.name || 'Predicted')
                                .replace(' [DTC]', '')
                                .replace('[DTC]', '') +
                            (futureSatellite === currentSatellite
                                ? ' (預測)'
                                : ''),
                        signal_strength: 80 + Math.random() * 15,
                        elevation:
                            'position' in futureSatellite
                                ? futureSatellite.position?.elevation || 0
                                : futureSatellite.elevation_deg || 0,
                    },
                    handover_required: futureSatellite !== currentSatellite, // 只有當衛星不同時才需要換手
                    handover_trigger_time: futureTime,
                    binary_search_result: apiResult.algorithm_details
                        ?.binary_search_refinement
                        ? {
                              handover_time: futureTime,
                              iterations: [],
                              iteration_count:
                                  apiResult.binary_search_iterations || 0,
                              final_precision: apiResult.error_bound_ms || 0,
                          }
                        : undefined,
                    prediction_confidence: apiResult.confidence_score || 0.85,
                    accuracy_percentage:
                        (apiResult.confidence_score || 0.85) * 100,
                }

                // 只在手動執行或結果發生重大變化時記錄結果
                if (forceExecute || result.handover_required) {
                    console.log('🛰️ 二點預測結果:', {
                        current: result.current_satellite.name,
                        future: result.future_satellite.name,
                        handover_required: result.handover_required,
                        delta_t_minutes: Math.round(deltaT / 60),
                        different_satellites:
                            futureSatellite !== currentSatellite,
                        available_satellites: availableSatellites.length,
                    })
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
        },
        [
            isEnabled,
            selectedUEId,
            realSatellites,
            satellites,
            onAlgorithmStep,
            onAlgorithmResults,
            speedMultiplier,
        ]
    )

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

            // Fallback: 使用預測結果的信賴水準
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

    // 當speedMultiplier改變時，清除緩存的預測結果並立即重新執行
    useEffect(() => {
        if (!isEnabled) return
        
        // 清除緩存的結果
        setPredictionResult(null)
        setBinarySearchIterations([])
        lastExecutionTimeRef.current = 0 // 重置頻率限制
        
        // 立即執行新的預測
        const timeoutId = setTimeout(() => {
            executeTwoPointPrediction(true) // 強制執行
        }, 100)
        
        return () => clearTimeout(timeoutId)
    }, [speedMultiplier, executeTwoPointPrediction])

    // 定期執行算法 - 修復依賴問題
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
    }, [isEnabled, speedMultiplier, isRunning]) // 移除 executeTwoPointPrediction 依賴，避免無限循環

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
                    <h2>🧮 演算法監控</h2>
                    <div className="header-actions">
                        <button
                            onClick={() => executeTwoPointPrediction(true)}
                            className="execute-btn"
                            disabled={isRunning}
                        >
                            {isRunning ? '執行中...' : '立即執行'}
                        </button>
                        <button
                            onClick={clearHistory}
                            className="clear-btn"
                            disabled={isRunning}
                        >
                            清除歷史
                        </button>
                    </div>
                </div>

                <div className="algorithm-info">
                    <span className="ue-id">UE: {selectedUEId}</span>
                    {currentStep && (
                        <span className="current-step">
                            執行中: {getStepDisplayName(currentStep)}
                        </span>
                    )}
                </div>

                {/* 數據來源狀態指示器 */}
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
                                ? '連線失敗'
                                : coreSyncLoading
                                ? '連接中'
                                : '已連線'}
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
                                ? '連線失敗'
                                : satellitesLoading
                                ? '載入中'
                                : '已連線'}
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
                                        <div className="delta-t-value">
                                            Δt ={' '}
                                            {Math.round(
                                                predictionResult.delta_t_seconds
                                            )}
                                            s
                                        </div>
                                        <div className="delta-t-minutes">
                                            ({(predictionResult.delta_t_seconds / 60).toFixed(1)}分鐘)
                                        </div>
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
                                        預測信賴水準:
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

                {/* 系統同步狀態 */}
                <div className="sync-status-real">
                    <h3>🔄 系統同步狀態</h3>
                    <div className="algorithm-status-explanation">
                        <div className="status-item">
                            <span className="status-label">當前算法狀態:</span>
                            <span
                                className={`status-value ${
                                    isRunning
                                        ? 'running'
                                        : currentStep
                                        ? 'processing'
                                        : 'idle'
                                }`}
                            >
                                {isRunning
                                    ? '執行中'
                                    : currentStep
                                    ? '處理中'
                                    : '待機'}
                            </span>
                        </div>
                    </div>
                    <div className="sync-summary">
                        <div className="sync-metric">
                            <span className="metric-label">同步準確率:</span>
                            <span className="metric-value">
                                {(syncAccuracy * 100).toFixed(1)}%
                            </span>
                        </div>
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
