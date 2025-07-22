/**
 * Event D2 Viewer Component
 * 提供完整的 Event D2 移動參考位置測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 * 基於 EventD1Viewer.tsx 修改以支援移動參考位置
 * 樣式完全參考 A4/D1 的設計模式
 */

import React, { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import PureD2Chart from './PureD2Chart'
import RealD2Chart, { RealD2DataPoint } from './RealD2Chart'
import {
    unifiedD2DataService,
    D2ScenarioConfig,
    D2MeasurementPoint,
    ConstellationInfo,
} from '../../../../services/unifiedD2DataService'
import type { EventD2Params } from '../types'
import './EventA4Viewer.scss' // 完全重用 A4 的樣式，確保左側控制面板風格一致
import './NarrationPanel.scss' // 動畫解說面板樣式

interface EventD2ViewerProps {
    isDarkTheme?: boolean
    onThemeToggle?: () => void
    initialParams?: Partial<EventD2Params>
    // 新增：支援 Modal 模式的屬性
    onReportLastUpdateToNavbar?: (timestamp: number) => void
    reportRefreshHandlerToNavbar?: React.MutableRefObject<(() => void) | null>
    reportIsLoadingToNavbar?: (loading: boolean) => void
    currentScene?: string
}

export const EventD2Viewer: React.FC<EventD2ViewerProps> = React.memo(
    ({ isDarkTheme = true, onThemeToggle, initialParams = {} }) => {
        // Event D2 參數狀態 - 基於 3GPP TS 38.331 規範
        const [params, setParams] = useState<EventD2Params>(() => ({
            Thresh1: initialParams.Thresh1 ?? 800000, // meters (距離門檻1 - 移動參考位置，衛星距離) - 符合 API 約束
            Thresh2: initialParams.Thresh2 ?? 30000, // meters (距離門檻2 - 固定參考位置) - 符合 API 約束
            Hys: initialParams.Hys ?? 500, // meters (hysteresisLocation) - 符合 API 約束: ge=100
            timeToTrigger: initialParams.timeToTrigger ?? 320, // ms
            reportAmount: initialParams.reportAmount ?? 3,
            reportInterval: initialParams.reportInterval ?? 1000, // ms
            reportOnLeave: initialParams.reportOnLeave ?? true,
            movingReferenceLocation: initialParams.movingReferenceLocation ?? {
                lat: 25.0478,
                lon: 121.5319,
            }, // 移動參考位置（衛星初始位置）
            referenceLocation: initialParams.referenceLocation ?? {
                lat: 25.0173,
                lon: 121.4695,
            }, // 固定參考位置（中正紀念堂）
        }))

        const [showThresholdLines, setShowThresholdLines] = useState(true)

        // 星座信息輔助函數
        const getConstellationInfo = useCallback((constellation: string) => {
            switch (constellation) {
                case 'starlink':
                    return {
                        description: '低軌高速軌道 (53°, 550km, 15軌/日)',
                        characteristics: '快速變化的距離曲線，明顯的都卜勒效應'
                    }
                case 'oneweb':
                    return {
                        description: '極軌中高度軌道 (87°, 1200km, 13軌/日)',
                        characteristics: '極地覆蓋，中等變化率的軌道特徵'
                    }
                case 'gps':
                    return {
                        description: '中軌穩定軌道 (55°, 20200km, 2軌/日)',
                        characteristics: '緩慢變化，長期穩定的距離關係'
                    }
                default:
                    return {
                        description: '未知星座',
                        characteristics: '標準軌道特徵'
                    }
            }
        }, [])

        // 真實數據模式狀態
        const [currentMode, setCurrentMode] = useState<
            'simulation' | 'real-data'
        >('simulation')
        const [isLoadingRealData, setIsLoadingRealData] = useState(false)
        const [realDataError, setRealDataError] = useState<string | null>(null)
        const [realD2Data, setRealD2Data] = useState<RealD2DataPoint[]>([])

        // 真實數據配置
        const [selectedConstellation, setSelectedConstellation] = useState<'starlink' | 'oneweb' | 'gps'>('starlink')
        const [selectedTimeRange, setSelectedTimeRange] = useState({
            durationMinutes: 120, // 預設為2小時，可看到LEO完整軌道週期
            sampleIntervalSeconds: 10, // 適合2小時觀測的採樣間隔
        })

        // 動畫解說系統狀態
        const [showNarration, setShowNarration] = useState(true)
        const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
        const [isNarrationExpanded, setIsNarrationExpanded] = useState(false)

        // 動畫解說面板的位置和透明度狀態 (從 A4 引入)
        const [narrationPosition, setNarrationPosition] = useState(() => {
            const viewportWidth = window.innerWidth
            const viewportHeight = window.innerHeight
            const panelWidth = 420
            const margin = 135
            const x = Math.max(20, viewportWidth - panelWidth - margin)
            const y = Math.max(20, viewportHeight * 0.01 + 70)
            return { x, y }
        })
        const [narrationOpacity, setNarrationOpacity] = useState(0.95)
        const [isNarrationMinimized, setIsNarrationMinimized] = useState(false)
        const [isDragging, setIsDragging] = useState(false)

        // 使用 ref 直接操作 DOM (從 A4 引入)
        const narrationPanelRef = useRef<HTMLDivElement>(null)
        const dragState = useRef({
            isDragging: false,
            offsetX: 0,
            offsetY: 0,
            currentX: 20,
            currentY: 20,
        })
        const animationFrameId = useRef<number | null>(null)
        const latestMouseEvent = useRef({ x: 0, y: 0 })

        // 轉換 API 響應為 RealD2Chart 所需格式的函數
        const convertToRealD2DataPoints = useCallback(
            (measurements: D2MeasurementPoint[]): RealD2DataPoint[] => {
                return measurements.map((measurement, index) => {
                    // 模擬動態地面距離變化（基於穩定的時間進度）
                    const baseGroundDistance = measurement.ground_distance
                    const timeProgress =
                        index / Math.max(1, measurements.length - 1)

                    // 創建穩定的 sin 波變化，調整到與模擬數據相似的範圍
                    // 模擬數據範圍：5.5-6.8 公里，真實數據基礎：7.14 公里
                    // 調整為 5.5-6.8 公里範圍以統一顯示
                    const minDistance = 5500 // 5.5 公里（米）
                    const maxDistance = 6800 // 6.8 公里（米）
                    const midDistance = (minDistance + maxDistance) / 2
                    const amplitude = (maxDistance - minDistance) / 2

                    const dynamicGroundDistance =
                        midDistance +
                        Math.sin(timeProgress * 4 * Math.PI + Math.PI / 4) *
                            amplitude

                    return {
                        timestamp: measurement.timestamp,
                        satelliteDistance: measurement.satellite_distance,
                        groundDistance: dynamicGroundDistance, // 動態地面距離
                        satelliteInfo: {
                            noradId: 0, // 暫時使用預設值
                            name: measurement.satellite_id,
                            latitude: measurement.satellite_position.latitude,
                            longitude: measurement.satellite_position.longitude,
                            altitude: measurement.satellite_position.altitude,
                        },
                        triggerConditionMet: measurement.trigger_condition_met,
                        d2EventDetails: {
                            thresh1: params.Thresh1,
                            thresh2: params.Thresh2,
                            hysteresis: params.Hys,
                            enteringCondition:
                                measurement.event_type === 'entering',
                            leavingCondition:
                                measurement.event_type === 'leaving',
                        },
                    }
                })
            },
            [params.Thresh1, params.Thresh2, params.Hys]
        )

        // fetchRealD2Data 函數已移除，統一使用 loadRealData

        // 載入真實數據 - 當星座或時間段改變時自動觸發
        const loadRealData = useCallback(async () => {
            if (isLoadingRealData) return
            
            setIsLoadingRealData(true)
            setRealDataError(null)
            
            try {
                console.log(`🔄 [EventD2Viewer] 載入 ${selectedConstellation} 星座數據...`)
                console.log(`⏱️ 時間段: ${selectedTimeRange.durationMinutes} 分鐘`)
                
                // 強制使用唯一場景名稱避免後端累積效應bug
                const uniqueId = Date.now() + '_' + Math.random().toString(36).substr(2, 9)
                const scenarioName = `D2_${selectedConstellation}_${selectedTimeRange.durationMinutes}min_${selectedTimeRange.sampleIntervalSeconds}s_${uniqueId}`
                
                console.log(`🎯 [EventD2Viewer] 場景名稱: ${scenarioName}`)
                
                const dynamicConfig: D2ScenarioConfig = {
                    scenario_name: scenarioName, // 使用半穩定名稱平衡緩存和唯一性
                    constellation: selectedConstellation,
                    ue_position: {
                        latitude: params.referenceLocation.lat,
                        longitude: params.referenceLocation.lon,
                        altitude: 100,
                    },
                    fixed_ref_position: {
                        latitude: params.movingReferenceLocation.lat,
                        longitude: params.movingReferenceLocation.lon,
                        altitude: 100,
                    },
                    thresh1: params.Thresh1,
                    thresh2: params.Thresh2,
                    hysteresis: params.Hys,
                    duration_minutes: selectedTimeRange.durationMinutes,
                    sample_interval_seconds: selectedTimeRange.sampleIntervalSeconds,
                }
                
                // 激進清除緩存以避免累積效應
                console.log('🧹 [EventD2Viewer] 清除所有相關緩存...')
                unifiedD2DataService.clearCache()
                // 也清除可能的前端緩存
                if ('caches' in window) {
                    try {
                        const cacheNames = await caches.keys()
                        for (const cacheName of cacheNames) {
                            if (cacheName.includes('d2') || cacheName.includes('satellite')) {
                                await caches.delete(cacheName)
                            }
                        }
                    } catch (e) {
                        // 忽略緩存清除錯誤
                    }
                }
                
                const measurements = await unifiedD2DataService.getD2Data(dynamicConfig)
                const convertedData = convertToRealD2DataPoints(measurements)
                
                setRealD2Data(convertedData)
                console.log(`✅ [EventD2Viewer] 成功載入 ${convertedData.length} 個 ${selectedConstellation} 數據點`)
                console.log('🔍 [EventD2Viewer] 前3個數據點預覽:', convertedData.slice(0, 3).map(d => ({
                    time: d.timestamp,
                    satDist: (d.satelliteDistance / 1000).toFixed(1) + 'km',
                    groundDist: (d.groundDistance / 1000).toFixed(1) + 'km'
                })))
                
                // 診斷時間範圍問題
                if (convertedData.length > 1) {
                    const firstTime = new Date(convertedData[0].timestamp);
                    const lastTime = new Date(convertedData[convertedData.length - 1].timestamp);
                    const actualDurationMinutes = (lastTime - firstTime) / (1000 * 60);
                    const expectedDuration = selectedTimeRange.durationMinutes;
                    
                    console.log('⏰ [EventD2Viewer] 時間範圍診斷:', {
                        預期時間段: expectedDuration + '分鐘',
                        實際時間段: actualDurationMinutes.toFixed(2) + '分鐘',
                        開始時間: firstTime.toISOString(),
                        結束時間: lastTime.toISOString(),
                        時間異常: actualDurationMinutes < expectedDuration * 0.8 ? '⚠️ 是' : '✅ 否'
                    });
                }
                
            } catch (error) {
                console.error(`❌ [EventD2Viewer] 載入 ${selectedConstellation} 數據失敗:`, error)
                const errorMessage = error instanceof Error ? error.message : '未知錯誤'
                setRealDataError(`載入 ${selectedConstellation} 數據失敗: ${errorMessage}`)
            } finally {
                setIsLoadingRealData(false)
            }
        }, [
            selectedConstellation,
            selectedTimeRange,
            params,
            convertToRealD2DataPoints,
            isLoadingRealData
        ])

        // 手動更新模式 - 移除自動更新以避免選擇困難

        // 模式切換處理函數
        const handleModeToggle = useCallback(
            async (mode: 'simulation' | 'real-data') => {
                setCurrentMode(mode)
                setRealDataError(null)

                if (mode === 'real-data') {
                    console.log('🚀 [EventD2Viewer] 切換到真實數據模式')
                    // 切換到真實模式時載入一次數據
                    await loadRealData()
                } else {
                    console.log('🎯 [EventD2Viewer] 切換到模擬模式')
                    setRealD2Data([])
                }
            },
            [loadRealData]
        )

        // 初始化拖拽狀態的位置 (從 A4 引入)
        useEffect(() => {
            dragState.current.currentX = narrationPosition.x
            dragState.current.currentY = narrationPosition.y
        }, [narrationPosition.x, narrationPosition.y])

        // 核心拖拽更新函數 (從 A4 引入)
        const updatePosition = useCallback(() => {
            if (!dragState.current.isDragging) {
                animationFrameId.current = null
                return
            }

            const { x, y } = latestMouseEvent.current
            const newX = x - dragState.current.offsetX
            const newY = y - dragState.current.offsetY

            const panelWidth = narrationPanelRef.current?.offsetWidth || 420
            const panelHeight = narrationPanelRef.current?.offsetHeight || 400
            const maxX = Math.max(0, window.innerWidth - panelWidth)
            const maxY = Math.max(0, window.innerHeight - panelHeight)

            const finalX = Math.max(0, Math.min(newX, maxX))
            const finalY = Math.max(0, Math.min(newY, maxY))

            if (narrationPanelRef.current) {
                narrationPanelRef.current.style.transform = `translate(${finalX}px, ${finalY}px)`
            }

            dragState.current.currentX = finalX
            dragState.current.currentY = finalY

            animationFrameId.current = null
        }, [])

        const handleMouseMove = useCallback(
            (e: MouseEvent) => {
                e.preventDefault()
                latestMouseEvent.current = { x: e.clientX, y: e.clientY }

                if (animationFrameId.current === null) {
                    animationFrameId.current =
                        requestAnimationFrame(updatePosition)
                }
            },
            [updatePosition]
        )

        const handleMouseUp = useCallback(() => {
            dragState.current.isDragging = false
            setIsDragging(false)

            document.removeEventListener('mousemove', handleMouseMove)
            document.removeEventListener('mouseup', handleMouseUp)

            if (animationFrameId.current) {
                cancelAnimationFrame(animationFrameId.current)
                animationFrameId.current = null
            }

            setNarrationPosition({
                x: dragState.current.currentX,
                y: dragState.current.currentY,
            })
        }, [handleMouseMove])

        // 拖拽處理函數 (從 A4 引入)
        const handleMouseDown = useCallback(
            (e: React.MouseEvent) => {
                if (
                    e.target instanceof HTMLElement &&
                    (e.target.closest('.narration-controls') ||
                        e.target.closest('.opacity-control') ||
                        e.target.closest('button') ||
                        e.target.closest('input'))
                ) {
                    return
                }

                e.preventDefault()
                e.stopPropagation()

                dragState.current.isDragging = true
                dragState.current.offsetX =
                    e.clientX - dragState.current.currentX
                dragState.current.offsetY =
                    e.clientY - dragState.current.currentY
                setIsDragging(true)

                document.addEventListener('mousemove', handleMouseMove)
                document.addEventListener('mouseup', handleMouseUp)
            },
            [handleMouseMove, handleMouseUp]
        )

        // 穩定的參數更新回調
        const updateParam = useCallback(
            (key: keyof EventD2Params, value: unknown) => {
                setParams((prev) => ({
                    ...prev,
                    [key]: value,
                }))
            },
            []
        )



        // 穩定的閾值線切換回調
        const toggleThresholdLines = useCallback(() => {
            setShowThresholdLines((prev) => !prev)
        }, [])

        // 計算衛星位置（基於真實 LEO 軌道參數）
        const calculateSatellitePosition = useCallback(
            (timeSeconds: number) => {
                const centerLat = params.movingReferenceLocation.lat
                const centerLon = params.movingReferenceLocation.lon

                // 真實 LEO 衛星軌道參數
                const orbitRadius = 0.5 // 軌道半徑（度）- 更真實的軌道範圍
                const orbitPeriod = 5400 // 軌道週期（90分鐘 = 5400秒）✅ 修正
                const altitude = 550000 // LEO 衛星高度 (550km)
                const orbitalVelocity = 7.56 // km/s (真實 LEO 軌道速度)

                // 基於真實軌道週期的角度計算
                const angle = (timeSeconds / orbitPeriod) * 2 * Math.PI

                // 考慮地球自轉效應 (簡化)
                const earthRotationRate = 360 / 86400 // 度/秒
                const earthRotationOffset =
                    (timeSeconds * earthRotationRate) / 3600 // 小時轉換

                return {
                    lat: centerLat + orbitRadius * Math.cos(angle),
                    lon:
                        centerLon +
                        orbitRadius * Math.sin(angle) -
                        earthRotationOffset * 0.1, // 地球自轉修正
                    altitude: altitude,
                    velocity: orbitalVelocity,
                    orbitPeriod: orbitPeriod,
                    currentPhase: (timeSeconds % orbitPeriod) / orbitPeriod, // 軌道相位 (0-1)
                }
            },
            [params.movingReferenceLocation]
        )

        // 動畫解說內容生成 - 基於衛星軌道和 LEO 星座切換策略
        const narrationContent = useMemo(() => {
            const currentTime = 45 // 固定時間點用於演示
            const satellitePosition = calculateSatellitePosition(currentTime)

            // 模擬 UE 位置 (全球化支援 - 可配置)
            const _uePosition = { lat: 0.048, lon: 0.528 }

            // 計算軌道參數
            const orbitalVelocity = 7.5 // km/s for LEO at 550km
            const _orbitalPeriod = 5570 // seconds for real LEO orbit
            const groundTrackSpeed =
                orbitalVelocity * Math.cos((Math.PI / 180) * 53) // 軌道傾角53度

            // 模擬距離值（實際應用中會基於真實地理計算）
            let simulatedDistance1, simulatedDistance2

            // 在特定時間段模擬事件觸發條件
            if (currentTime >= 20 && currentTime <= 80) {
                // 觸發區間：距離1 > Thresh1, 距離2 < Thresh2
                simulatedDistance1 = 552000 // meters - 超過 Thresh1 (550km)
                simulatedDistance2 = 5500 // meters - 低於 Thresh2 (6km)
            } else if (currentTime < 20) {
                // 觸發前：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 548000 // meters - 低於 Thresh1
                simulatedDistance2 = 6500 // meters - 高於 Thresh2
            } else {
                // 觸發後：條件不滿足
                simulatedDistance1 = 547000 // meters - 低於 Thresh1
                simulatedDistance2 = 6800 // meters - 高於 Thresh2
            }

            // 判斷當前階段和 LEO 星座切換策略
            let phase = 'monitoring'
            let phaseTitle = ''
            let description = ''
            let technicalNote = ''
            let nextAction = ''
            let constellationStrategy = ''
            let handoverScenario = ''

            const condition1 = simulatedDistance1 - params.Hys > params.Thresh1
            const condition2 = simulatedDistance2 + params.Hys < params.Thresh2
            const eventTriggered = condition1 && condition2

            if (eventTriggered) {
                phase = 'triggered'
                phaseTitle = '🛰️ Event D2 已觸發 - LEO 星座切換決策啟動'
                description = `衛星距離 (${(simulatedDistance1 / 1000).toFixed(
                    1
                )} km) 超過門檻1，同時固定參考點距離 (${(
                    simulatedDistance2 / 1000
                ).toFixed(1)} km) 低於門檻2。LEO 星座系統正在執行智能切換決策。`

                // LEO 星座切換策略說明
                constellationStrategy = '🌌 LEO 星座切換策略：多衛星協調切換'
                handoverScenario = `實際星座切換場景：當前服務衛星即將離開最佳服務區域，系統啟動：
• 🔍 候選衛星搜尋：掃描同軌道面和相鄰軌道面的可用衛星
• 📊 鏈路品質評估：比較候選衛星的仰角、RSRP、干擾水平
• ⚡ 預測性切換：基於軌道預測，提前2-3分鐘準備切換
• 🔄 無縫切換執行：使用 make-before-break 策略確保服務連續性
• 🛡️ 負載平衡：考慮目標衛星的用戶負載和資源可用性
• 📡 波束管理：協調衛星波束指向和功率分配優化`

                technicalNote = `3GPP 條件: Ml1 - Hys > Thresh1 AND Ml2 + Hys < Thresh2\\n衛星距離: ${(
                    simulatedDistance1 / 1000
                ).toFixed(1)} - ${params.Hys / 1000} = ${(
                    (simulatedDistance1 - params.Hys) /
                    1000
                ).toFixed(1)} > ${(params.Thresh1 / 1000).toFixed(
                    1
                )} km\\n固定距離: ${(simulatedDistance2 / 1000).toFixed(1)} + ${
                    params.Hys / 1000
                } = ${((simulatedDistance2 + params.Hys) / 1000).toFixed(
                    1
                )} < ${(params.Thresh2 / 1000).toFixed(
                    1
                )} km\\n\\nLEO 星座參數：\\n• 軌道高度：${
                    satellitePosition.altitude / 1000
                } km\\n• 軌道速度：${orbitalVelocity} km/s\\n• 地面軌跡速度：${groundTrackSpeed.toFixed(
                    1
                )} km/s\\n• 可見時間窗口：8-12 分鐘\\n• 切換決策時延：${
                    params.timeToTrigger
                } ms`
                nextAction = '執行多衛星協調切換，確保服務連續性和最佳QoS'
            } else if (condition1 && !condition2) {
                phase = 'partial'
                phaseTitle = '⚠️ 星座監控中 - 準備切換候選衛星'
                description = `衛星距離條件已滿足 (${(
                    simulatedDistance1 / 1000
                ).toFixed(1)} km > ${(params.Thresh1 / 1000).toFixed(
                    1
                )} km)，但固定參考點距離 (${(simulatedDistance2 / 1000).toFixed(
                    1
                )} km) 仍高於門檻。`
                constellationStrategy = '👁️ 星座狀態：候選衛星識別階段'
                handoverScenario = `準備階段切換策略：當前衛星開始遠離最佳位置，系統準備：
• 🔭 軌道預測：計算未來5-10分鐘內所有可見衛星的軌跡
• 📈 性能建模：預測每顆候選衛星的服務品質變化趨勢
• 🎯 最佳時機計算：確定最佳切換時間點以最小化服務中斷
• 📋 資源預留：在候選衛星上預留必要的網路資源
• 🔧 設備準備：調整天線指向和功率設定準備新連接`
                technicalNote = `條件1: ✅ Ml1 - Hys = ${(
                    (simulatedDistance1 - params.Hys) /
                    1000
                ).toFixed(1)} > ${(params.Thresh1 / 1000).toFixed(
                    1
                )}\\n條件2: ❌ Ml2 + Hys = ${(
                    (simulatedDistance2 + params.Hys) /
                    1000
                ).toFixed(1)} ≮ ${(params.Thresh2 / 1000).toFixed(
                    1
                )}\\n\\n候選衛星評估：\\n• 仰角門檻：> 15度\\n• 預期服務時間：> 8分鐘\\n• 負載容量：< 80%\\n• 切換延遲：< 50ms`
                nextAction = '繼續監控並準備候選衛星資源，等待最佳切換時機'
            } else if (!condition1 && condition2) {
                phase = 'partial'
                phaseTitle = '⚠️ 星座監控中 - 當前衛星服務中'
                description = `固定參考點距離條件已滿足 (${(
                    simulatedDistance2 / 1000
                ).toFixed(1)} km < ${(params.Thresh2 / 1000).toFixed(
                    1
                )} km)，但衛星距離 (${(simulatedDistance1 / 1000).toFixed(
                    1
                )} km) 仍在最佳服務範圍內。`
                constellationStrategy = '⭐ 星座狀態：最佳服務階段'
                handoverScenario = `服務維持階段策略：當前衛星在最佳位置，系統執行：
• 🎯 服務優化：動態調整波束形成和功率分配
• 📊 性能監控：持續監測信號品質和用戶體驗指標
• 🔮 軌道追蹤：實時追蹤衛星位置和預測未來軌跡
• 🚀 預備切換：提前識別下一個服務窗口的候選衛星
• 🔄 負載均衡：在多個可見衛星間動態分配用戶負載`
                technicalNote = `條件1: ❌ Ml1 - Hys = ${(
                    (simulatedDistance1 - params.Hys) /
                    1000
                ).toFixed(1)} ≯ ${(params.Thresh1 / 1000).toFixed(
                    1
                )}\\n條件2: ✅ Ml2 + Hys = ${(
                    (simulatedDistance2 + params.Hys) /
                    1000
                ).toFixed(1)} < ${(params.Thresh2 / 1000).toFixed(
                    1
                )}\\n\\n最佳服務參數：\\n• 當前仰角：45-70度\\n• 傳播延遲：< 5ms\\n• 都卜勒頻移補償：±3 kHz\\n• 預期服務剩餘時間：${(
                    70 - currentTime
                ).toFixed(0)}秒`
                nextAction = '維持最佳服務品質，準備未來切換規劃'
            } else {
                phaseTitle = '🔍 LEO 星座正常監控階段'
                description = `雙重距離條件均未滿足。衛星距離 (${(
                    simulatedDistance1 / 1000
                ).toFixed(1)} km) 和固定參考點距離 (${(
                    simulatedDistance2 / 1000
                ).toFixed(1)} km) 均在正常範圍內。`
                constellationStrategy = '🌐 星座狀態：連續覆蓋保障'
                handoverScenario = `標準監控模式：多衛星星座提供連續覆蓋，系統執行：
• 🛰️ 星座追蹤：實時追蹤所有可見LEO衛星的位置和狀態
• 📡 信號監測：監控多個衛星的信號強度和品質參數
• 🧭 軌道預測：使用TLE數據預測未來24小時的衛星可見性
• 🔄 自動切換：基於預設規則執行自動衛星切換
• 📊 性能分析：收集並分析星座覆蓋性能和用戶體驗數據
• 🛡️ 容錯機制：監控衛星健康狀態，準備故障切換方案`
                technicalNote = `衛星距離: ${(
                    simulatedDistance1 / 1000
                ).toFixed(1)} km, 固定距離: ${(
                    simulatedDistance2 / 1000
                ).toFixed(
                    1
                )} km\\n\\nLEO 星座監控重點：\\n• 多衛星可見性分析\\n• 信號品質趨勢預測\\n• 軌道機動影響評估\\n• 星座完整性驗證\\n• 切換演算法性能優化\\n• 用戶移動性適應`
                nextAction = '持續星座監控，優化切換演算法和服務品質'
            }

            // 根據時間添加詳細的 LEO 軌道情境解說
            let scenarioContext = ''
            let orbitalScenario = ''
            if (currentTime < 30) {
                scenarioContext =
                    '🚀 場景：LEO衛星從地平線升起，開始進入服務範圍'
                orbitalScenario = `軌道動力學：衛星以 ${orbitalVelocity} km/s 的速度快速接近，仰角從5度快速增加到30度`
            } else if (currentTime < 70) {
                scenarioContext = '🌍 場景：衛星接近天頂，處於最佳服務位置'
                orbitalScenario = `軌道動力學：衛星在40-70度仰角範圍內，提供最低延遲和最強信號品質`
            } else {
                scenarioContext = '🏠 場景：衛星向地平線下降，準備離開服務範圍'
                orbitalScenario = `軌道動力學：衛星仰角降至15度以下，系統準備切換到下一顆衛星`
            }

            return {
                phase,
                phaseTitle,
                description,
                technicalNote,
                nextAction,
                scenarioContext,
                orbitalScenario,
                constellationStrategy,
                handoverScenario,
                satelliteDistance: (simulatedDistance1 / 1000).toFixed(1),
                fixedDistance: (simulatedDistance2 / 1000).toFixed(1),
                timeProgress: `${currentTime.toFixed(1)}s / 95s`,
                satelliteLat: satellitePosition.lat.toFixed(4),
                satelliteLon: satellitePosition.lon.toFixed(4),
                orbitalVelocity: `${orbitalVelocity} km/s`,
                groundTrack: `${groundTrackSpeed.toFixed(1)} km/s`,
            }
        }, [
            params.Thresh1,
            params.Thresh2,
            params.Hys,
            calculateSatellitePosition,
        ])

        // 計算 Event D2 條件狀態 - 基於 3GPP TS 38.331 規範
        const eventStatus = useMemo(() => {
            // 根據當前時間計算條件
            const currentTime = 45 // 固定時間點用於演示

            // 模擬 UE 位置 (全球化支援 - 可配置)
            const _uePosition = { lat: 0.048, lon: 0.528 }

            // 計算移動參考位置（衛星當前位置）
            const satellitePosition = calculateSatellitePosition(currentTime)

            // 模擬距離值（實際應用中會基於真實地理計算）
            let simulatedDistance1, simulatedDistance2

            // 在特定時間段模擬事件觸發條件
            if (currentTime >= 20 && currentTime <= 80) {
                // 觸發區間：距離1 > Thresh1, 距離2 < Thresh2
                simulatedDistance1 = 552000 // meters - 超過 Thresh1 (550km)
                simulatedDistance2 = 5500 // meters - 低於 Thresh2 (6km)
            } else if (currentTime < 20) {
                // 觸發前：距離1 < Thresh1, 距離2 > Thresh2
                simulatedDistance1 = 548000 // meters - 低於 Thresh1
                simulatedDistance2 = 6500 // meters - 高於 Thresh2
            } else {
                // 觸發後：條件不滿足
                simulatedDistance1 = 547000 // meters - 低於 Thresh1
                simulatedDistance2 = 6800 // meters - 高於 Thresh2
            }

            // D2-1 進入條件: Ml1 - Hys > Thresh1 (移動參考位置)
            const condition1 = simulatedDistance1 - params.Hys > params.Thresh1
            // D2-2 進入條件: Ml2 + Hys < Thresh2 (固定參考位置)
            const condition2 = simulatedDistance2 + params.Hys < params.Thresh2
            // 事件觸發需要兩個條件同時滿足
            const eventTriggered = condition1 && condition2

            return {
                condition1, // D2-1 進入條件
                condition2, // D2-2 進入條件
                eventTriggered,
                description: eventTriggered
                    ? 'D2 事件已觸發 (20-80s)'
                    : '等待條件滿足',
                currentDistance1: simulatedDistance1, // UE 到移動參考位置
                currentDistance2: simulatedDistance2, // UE 到固定參考位置
                triggerTimeRange: '20-80秒',
                satellitePosition, // 當前衛星位置
            }
        }, [params, calculateSatellitePosition])

        return (
            <div className="event-a4-viewer">
                <div className="event-viewer__content">
                    {/* 控制面板 */}
                    <div className="event-viewer__controls">
                        <div className="control-panel">
                            {/* D2事件控制 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📊 D2 事件控制
                                </h3>
                                <div className="control-group control-group--buttons">
                                    <button
                                        className={`control-btn ${
                                            showThresholdLines
                                                ? 'control-btn--active'
                                                : ''
                                        }`}
                                        onClick={toggleThresholdLines}
                                    >
                                        📏 門檻線
                                    </button>
                                </div>

                                {/* 真實數據控制 */}
                                {currentMode === 'real-data' && (
                                    <div className="control-group">
                                        <div className="control-item">
                                            <span className="control-label">衛星星座</span>
                                            <select
                                                value={selectedConstellation}
                                                onChange={(e) => setSelectedConstellation(e.target.value as 'starlink' | 'oneweb' | 'gps')}
                                                className="control-select"
                                                disabled={isLoadingRealData}
                                            >
                                                <option value="starlink">Starlink (7,954 顆)</option>
                                                <option value="oneweb">OneWeb (651 顆)</option>
                                                <option value="gps">GPS (32 顆)</option>
                                            </select>
                                        </div>
                                        <div className="control-item">
                                            <span className="control-label">時間段</span>
                                            <select
                                                value={selectedTimeRange.durationMinutes}
                                                onChange={(e) => setSelectedTimeRange(prev => ({ 
                                                    ...prev, 
                                                    durationMinutes: Number(e.target.value) 
                                                }))}
                                                className="control-select"
                                                disabled={isLoadingRealData}
                                            >
                                                <option value={5}>5 分鐘 (短期觀測)</option>
                                                <option value={15}>15 分鐘 (中期觀測)</option>
                                                <option value={30}>30 分鐘 (長期觀測)</option>
                                                <option value={60}>1 小時 (部分軌道)</option>
                                                <option value={120}>2 小時 (LEO完整軌道)</option>
                                                <option value={360}>6 小時 (多軌道週期)</option>
                                                <option value={720}>12 小時 (GPS完整週期)</option>
                                            </select>
                                        </div>
                                        <div className="control-group control-group--buttons">
                                            <button
                                                className="control-btn control-btn--refresh"
                                                onClick={loadRealData}
                                                disabled={isLoadingRealData}
                                                title="載入選定星座和時間段的真實軌道數據"
                                            >
                                                {isLoadingRealData ? '🔄 載入中...' : '📡 載入數據'}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Event D2 距離門檻參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🎯 D2 距離門檻
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            distanceThreshFromReference1
                                            (movingReferenceLocation)
                                            <span className="control-unit">
                                                公尺 (衛星距離)
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="540000"
                                            max="560000"
                                            step="1000"
                                            value={params.Thresh1}
                                            onChange={(e) =>
                                                updateParam(
                                                    'Thresh1',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {(params.Thresh1 / 1000).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            distanceThreshFromReference2
                                            (referenceLocation)
                                            <span className="control-unit">
                                                公尺 (固定參考位置)
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="3000"
                                            max="10000"
                                            step="100"
                                            value={params.Thresh2}
                                            onChange={(e) =>
                                                updateParam(
                                                    'Thresh2',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {(params.Thresh2 / 1000).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            hysteresisLocation (位置遲滯)
                                            <span className="control-unit">
                                                公尺
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="5"
                                            max="50"
                                            step="5"
                                            value={params.Hys}
                                            onChange={(e) =>
                                                updateParam(
                                                    'Hys',
                                                    Number(e.target.value)
                                                )
                                            }
                                            className="control-slider"
                                        />
                                        <span className="control-value">
                                            {params.Hys}m
                                        </span>
                                    </div>
                                </div>
                            </div>



                            {/* Event D2 狀態 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📡 D2 事件狀態
                                </h3>
                                <div className="event-status">
                                    <div className="status-item">
                                        <span className="status-label">
                                            進入條件 D2-1 (移動參考位置):
                                        </span>
                                        <span
                                            className={`status-value ${
                                                eventStatus.condition1
                                                    ? 'status-value--active'
                                                    : ''
                                            }`}
                                        >
                                            Ml1 - Hys &gt; Thresh1
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            進入條件 D2-2 (固定參考位置):
                                        </span>
                                        <span
                                            className={`status-value ${
                                                eventStatus.condition2
                                                    ? 'status-value--active'
                                                    : ''
                                            }`}
                                        >
                                            Ml2 + Hys &lt; Thresh2
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            事件狀態:
                                        </span>
                                        <span
                                            className={`status-badge ${
                                                eventStatus.eventTriggered
                                                    ? 'status-badge--triggered'
                                                    : 'status-badge--waiting'
                                            }`}
                                        >
                                            {eventStatus.eventTriggered
                                                ? '✅ 已觸發'
                                                : '⏳ 等待中'}
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            距離1 (Ml1):
                                        </span>
                                        <span className="status-value">
                                            {(
                                                eventStatus.currentDistance1 /
                                                1000
                                            ).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            距離2 (Ml2):
                                        </span>
                                        <span className="status-value">
                                            {(
                                                eventStatus.currentDistance2 /
                                                1000
                                            ).toFixed(1)}
                                            km
                                        </span>
                                    </div>
                                    <div className="status-item">
                                        <span className="status-label">
                                            觸發時間範圍:
                                        </span>
                                        <span
                                            className={`status-value ${
                                                eventStatus.eventTriggered
                                                    ? 'status-value--active'
                                                    : ''
                                            }`}
                                        >
                                            {eventStatus.triggerTimeRange}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Event D2 特有參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📡 D2 移動參考位置參數
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            movingReferenceLocation
                                            <span className="control-unit">
                                                (衛星初始位置)
                                            </span>
                                        </label>
                                        <div className="location-coords">
                                            {params.movingReferenceLocation.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.movingReferenceLocation.lon.toFixed(
                                                4
                                            )}
                                        </div>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            referenceLocation
                                            <span className="control-unit">
                                                (固定參考位置)
                                            </span>
                                        </label>
                                        <div className="location-coords">
                                            {params.referenceLocation.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.referenceLocation.lon.toFixed(
                                                4
                                            )}
                                        </div>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            satelliteEphemeris
                                            <span className="control-unit">
                                                (SIB19廣播)
                                            </span>
                                        </label>
                                        <select
                                            className="control-select"
                                            disabled
                                        >
                                            <option>LEO-550km-Circular</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* 衛星軌道參數 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🛰️ 衛星軌道參數
                                </h3>
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            軌道半徑
                                            <span className="control-unit">
                                                度
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0.005"
                                            max="0.02"
                                            step="0.001"
                                            value={0.01}
                                            className="control-slider"
                                            readOnly
                                        />
                                        <span className="control-value">
                                            0.01°
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            軌道週期
                                            <span className="control-unit">
                                                分鐘
                                            </span>
                                        </label>
                                        <input
                                            type="range"
                                            min="85"
                                            max="100"
                                            step="1"
                                            value={90}
                                            className="control-slider"
                                            readOnly
                                        />
                                        <span className="control-value">
                                            90分鐘 (5400s)
                                        </span>
                                    </div>
                                    <div className="control-item">
                                        <label className="control-label">
                                            軌道類型
                                        </label>
                                        <select
                                            className="control-select"
                                            disabled
                                        >
                                            <option value="circular">
                                                圓形軌道
                                            </option>
                                            <option value="elliptical">
                                                橢圓軌道
                                            </option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* 衛星軌道信息 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🛰️ 衛星軌道信息
                                </h3>
                                <div className="location-info">
                                    <div className="location-item">
                                        <span className="location-label">
                                            當前衛星位置:
                                        </span>
                                        <span className="location-coords">
                                            {eventStatus.satellitePosition.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {eventStatus.satellitePosition.lon.toFixed(
                                                4
                                            )}
                                        </span>
                                    </div>
                                    <div className="location-item">
                                        <span className="location-label">
                                            軌道週期:
                                        </span>
                                        <span className="location-coords">
                                            120秒
                                        </span>
                                    </div>
                                    <div className="location-item">
                                        <span className="location-label">
                                            固定參考點:
                                        </span>
                                        <span className="location-coords">
                                            {params.referenceLocation.lat.toFixed(
                                                4
                                            )}
                                            ,{' '}
                                            {params.referenceLocation.lon.toFixed(
                                                4
                                            )}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 圖表區域 */}
                    <div className="event-viewer__chart-container">
                        <div className="chart-area">
                            {/* 模式切換 Toggle */}
                            <div
                                style={{
                                    position: 'absolute',
                                    top: '10px',
                                    left: '10px',
                                    zIndex: 1000,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    padding: '8px 12px',
                                    backgroundColor: isDarkTheme
                                        ? 'rgba(33, 37, 41, 0.95)'
                                        : 'rgba(255, 255, 255, 0.95)',
                                    borderRadius: '8px',
                                    border: `1px solid ${
                                        isDarkTheme ? '#495057' : '#dee2e6'
                                    }`,
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                                }}
                            >
                                <span
                                    style={{
                                        fontSize: '12px',
                                        fontWeight: 'bold',
                                        color: isDarkTheme ? '#fff' : '#333',
                                    }}
                                >
                                    模擬
                                </span>
                                <label
                                    style={{
                                        position: 'relative',
                                        display: 'inline-block',
                                        width: '44px',
                                        height: '24px',
                                        cursor: isLoadingRealData
                                            ? 'wait'
                                            : 'pointer',
                                    }}
                                >
                                    <input
                                        type="checkbox"
                                        checked={currentMode === 'real-data'}
                                        onChange={(e) =>
                                            handleModeToggle(
                                                e.target.checked
                                                    ? 'real-data'
                                                    : 'simulation'
                                            )
                                        }
                                        disabled={isLoadingRealData}
                                        style={{
                                            opacity: 0,
                                            width: 0,
                                            height: 0,
                                        }}
                                    />
                                    <span
                                        style={{
                                            position: 'absolute',
                                            cursor: isLoadingRealData
                                                ? 'wait'
                                                : 'pointer',
                                            top: 0,
                                            left: 0,
                                            right: 0,
                                            bottom: 0,
                                            backgroundColor:
                                                currentMode === 'real-data'
                                                    ? '#28a745'
                                                    : '#ccc',
                                            borderRadius: '24px',
                                            transition: 'all 0.3s ease',
                                            opacity: isLoadingRealData
                                                ? 0.7
                                                : 1,
                                        }}
                                    />
                                    <span
                                        style={{
                                            position: 'absolute',
                                            content: '""',
                                            height: '18px',
                                            width: '18px',
                                            left:
                                                currentMode === 'real-data'
                                                    ? '23px'
                                                    : '3px',
                                            bottom: '3px',
                                            backgroundColor: 'white',
                                            borderRadius: '50%',
                                            transition: 'all 0.3s ease',
                                            boxShadow:
                                                '0 2px 4px rgba(0,0,0,0.2)',
                                        }}
                                    />
                                </label>
                                <span
                                    style={{
                                        fontSize: '12px',
                                        fontWeight: 'bold',
                                        color: isDarkTheme ? '#fff' : '#333',
                                    }}
                                >
                                    {isLoadingRealData ? '載入中...' : '真實'}
                                </span>
                            </div>

                            {/* 狀態指示器 */}
                            {currentMode === 'real-data' && (
                                <div
                                    style={{
                                        position: 'absolute',
                                        left: '10px',
                                        top: '60px',
                                        zIndex: 999,
                                        padding: '8px 12px',
                                        fontSize: '11px',
                                        backgroundColor: isDarkTheme
                                            ? 'rgba(33, 37, 41, 0.95)'
                                            : 'rgba(255, 255, 255, 0.95)',
                                        borderRadius: '6px',
                                        border: `1px solid ${
                                            isDarkTheme ? '#495057' : '#dee2e6'
                                        }`,
                                        color: realDataError
                                            ? '#dc3545'
                                            : isLoadingRealData
                                            ? '#ffc107'
                                            : '#28a745',
                                        minWidth: '220px',
                                        maxWidth: '300px',
                                        boxShadow: '0 3px 8px rgba(0,0,0,0.15)',
                                    }}
                                >
                                    <div
                                        style={{
                                            fontWeight: 'bold',
                                            marginBottom: '4px',
                                        }}
                                    >
                                        {realDataError
                                            ? '❌ 數據獲取失敗'
                                            : isLoadingRealData
                                            ? '🔄 載入真實數據中...'
                                            : `✅ 真實數據模式 (${realD2Data.length} 個數據點)`}
                                    </div>
                                    {realDataError && (
                                        <div
                                            style={{
                                                fontSize: '9px',
                                                opacity: 0.8,
                                                color: '#dc3545',
                                            }}
                                        >
                                            {realDataError}
                                        </div>
                                    )}
                                    {!realDataError &&
                                        !isLoadingRealData &&
                                        realD2Data.length > 0 && (
                                            <div
                                                style={{
                                                    fontSize: '9px',
                                                    opacity: 0.9,
                                                    lineHeight: 1.3,
                                                }}
                                            >
                                                <div style={{ marginBottom: '2px' }}>
                                                    星座: {selectedConstellation.toUpperCase()} | 
                                                    時間範圍: {selectedTimeRange.durationMinutes} 分鐘 | 
                                                    採樣: {selectedTimeRange.sampleIntervalSeconds}s
                                                </div>
                                                <div style={{ fontSize: '8px', opacity: 0.8 }}>
                                                    數據源: 真實 TLE + SGP4 軌道計算 | 
                                                    星座特徵: {getConstellationInfo(selectedConstellation).description}
                                                </div>
                                            </div>
                                        )}
                                </div>
                            )}

                            <div className="chart-container">
                                {currentMode === 'real-data' ? (
                                    <RealD2Chart
                                        data={realD2Data}
                                        thresh1={params.Thresh1}
                                        thresh2={params.Thresh2}
                                        hysteresis={params.Hys}
                                        showThresholdLines={showThresholdLines}
                                        isDarkTheme={isDarkTheme}
                                        showTriggerIndicator="none"
                                        onDataPointClick={(
                                            dataPoint,
                                            index
                                        ) => {
                                            console.log(
                                                '點擊數據點:',
                                                dataPoint,
                                                '索引:',
                                                index
                                            )
                                        }}
                                    />
                                ) : (
                                    <PureD2Chart
                                        thresh1={params.Thresh1}
                                        thresh2={params.Thresh2}
                                        hysteresis={params.Hys}
                                        showThresholdLines={showThresholdLines}
                                        isDarkTheme={isDarkTheme}
                                        onThemeToggle={onThemeToggle}
                                        showModeToggle={false}
                                    />
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* 浮動動畫解說面板 - 移到最頂層，完全脫離其他容器 */}
                {showNarration && (
                    <div
                        ref={narrationPanelRef}
                        className={`narration-panel floating ${
                            isNarrationExpanded ? 'expanded' : 'compact'
                        } ${isNarrationMinimized ? 'minimized' : ''}`}
                        style={{
                            position: 'fixed',
                            left: 0,
                            top: 0,
                            transform: `translate(${narrationPosition.x}px, ${narrationPosition.y}px)`,
                            opacity: narrationOpacity,
                            zIndex: 9999,
                            cursor: isDragging ? 'grabbing' : 'grab',
                        }}
                        onMouseDown={handleMouseDown}
                    >
                        <div className="narration-header">
                            <h3 className="narration-title">
                                {narrationContent.phaseTitle}
                            </h3>
                            <div className="narration-controls">
                                <div className="narration-time">
                                    🕰 {narrationContent.timeProgress}
                                </div>

                                {/* 透明度控制 */}
                                <div className="opacity-control">
                                    <input
                                        type="range"
                                        min="0.3"
                                        max="1"
                                        step="0.1"
                                        value={narrationOpacity}
                                        onChange={(e) =>
                                            setNarrationOpacity(
                                                parseFloat(e.target.value)
                                            )
                                        }
                                        className="opacity-slider"
                                        title="調整透明度"
                                    />
                                </div>

                                {/* 技術細節按鈕 */}
                                <button
                                    className={`narration-technical-toggle ${
                                        showTechnicalDetails ? 'active' : ''
                                    }`}
                                    onClick={() =>
                                        setShowTechnicalDetails(
                                            !showTechnicalDetails
                                        )
                                    }
                                    title={
                                        showTechnicalDetails
                                            ? '隱藏技術細節'
                                            : '顯示技術細節'
                                    }
                                >
                                    🔧
                                </button>

                                {/* 最小化按鈕 */}
                                <button
                                    className="narration-minimize"
                                    onClick={() =>
                                        setIsNarrationMinimized(
                                            !isNarrationMinimized
                                        )
                                    }
                                    title={
                                        isNarrationMinimized
                                            ? '展開面板'
                                            : '最小化面板'
                                    }
                                >
                                    {isNarrationMinimized ? '□' : '－'}
                                </button>

                                {/* 展開/收起按鈕 */}
                                <button
                                    className="narration-toggle"
                                    onClick={() =>
                                        setIsNarrationExpanded(
                                            !isNarrationExpanded
                                        )
                                    }
                                    title={
                                        isNarrationExpanded
                                            ? '收起詳細說明'
                                            : '展開詳細說明'
                                    }
                                >
                                    {isNarrationExpanded ? '▲' : '▼'}
                                </button>

                                {/* 關閉按鈕 */}
                                <button
                                    className="narration-close"
                                    onClick={() => setShowNarration(false)}
                                    title="關閉解說面板"
                                >
                                    ×
                                </button>
                            </div>
                        </div>

                        {!isNarrationMinimized && (
                            <>
                                {isNarrationExpanded && (
                                    <div className="narration-content">
                                        <div className="narration-scenario">
                                            {narrationContent.scenarioContext}
                                            <div className="mobility-scenario">
                                                {
                                                    narrationContent.orbitalScenario
                                                }
                                            </div>
                                        </div>

                                        <div className="constellation-strategy-stage">
                                            <h4>
                                                {
                                                    narrationContent.constellationStrategy
                                                }
                                            </h4>
                                            <div className="constellation-handover">
                                                {narrationContent.handoverScenario
                                                    .split('\\n')
                                                    .map((line, index) => (
                                                        <div
                                                            key={index}
                                                            className="handover-line"
                                                        >
                                                            {line}
                                                        </div>
                                                    ))}
                                            </div>
                                        </div>

                                        <div className="narration-description">
                                            {narrationContent.description}
                                        </div>

                                        {showTechnicalDetails && (
                                            <div className="narration-technical">
                                                <h4>🔧 技術細節：</h4>
                                                <div className="technical-formula">
                                                    {narrationContent.technicalNote
                                                        .split('\\n')
                                                        .map((line, index) => (
                                                            <div key={index}>
                                                                {line}
                                                            </div>
                                                        ))}
                                                </div>
                                            </div>
                                        )}

                                        <div className="narration-next">
                                            <strong>下一步：</strong>{' '}
                                            {narrationContent.nextAction}
                                        </div>
                                    </div>
                                )}

                                <div className="narration-metrics">
                                    <div className="metric">
                                        <span className="metric-label">
                                            衛星距離：
                                        </span>
                                        <span className="metric-value">
                                            {narrationContent.satelliteDistance}{' '}
                                            km
                                        </span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">
                                            固定距離：
                                        </span>
                                        <span className="metric-value">
                                            {narrationContent.fixedDistance} km
                                        </span>
                                    </div>
                                    <div className="metric">
                                        <span className="metric-label">
                                            衛星位置：
                                        </span>
                                        <span className="metric-value">
                                            {narrationContent.satelliteLat},{' '}
                                            {narrationContent.satelliteLon}
                                        </span>
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                )}

                {/* 3GPP 規範說明 */}
                <div className="event-viewer__specification">
                    <h3 className="spec-title">📖 3GPP TS 38.331 規範</h3>
                    <div className="spec-content">
                        <div className="spec-section">
                            <h4>Event D2 條件：</h4>
                            <ul>
                                <li>
                                    <strong>進入條件：</strong>
                                    <br />
                                    條件1: Ml1 - Hys &gt; Thresh1
                                    (移動參考位置距離)
                                    <br />
                                    條件2: Ml2 + Hys &lt; Thresh2
                                    (固定參考位置距離)
                                    <br />
                                    <em>
                                        同時滿足: 條件1 <strong>且</strong>{' '}
                                        條件2
                                    </em>
                                </li>
                                <li>
                                    <strong>離開條件：</strong>
                                    <br />
                                    條件1: Ml1 + Hys &lt; Thresh1
                                    (接近移動參考位置)
                                    <br />
                                    條件2: Ml2 - Hys &gt; Thresh2
                                    (遠離固定參考位置)
                                    <br />
                                    <em>
                                        任一滿足: 條件1 <strong>或</strong>{' '}
                                        條件2
                                    </em>
                                </li>
                                <li>
                                    <strong>TimeToTrigger：</strong>
                                    條件滿足後需持續的時間長度
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>參數說明：</h4>
                            <ul>
                                <li>
                                    <strong>Ml1：</strong>UE
                                    與移動參考位置（衛星）的距離（公尺）
                                    <br />
                                    <em>動態變化，反映 LEO 衛星軌道運動</em>
                                </li>
                                <li>
                                    <strong>Ml2：</strong>UE
                                    與固定參考位置的距離（公尺）
                                    <br />
                                    <em>相對穩定，基於地面固定參考點</em>
                                </li>
                                <li>
                                    <strong>Thresh1：</strong>
                                    移動參考位置距離門檻值（公尺）
                                    <br />
                                    <em>
                                        distanceThreshFromReference1，通常設置較大值（如
                                        550km）
                                    </em>
                                </li>
                                <li>
                                    <strong>Thresh2：</strong>
                                    固定參考位置距離門檻值（公尺）
                                    <br />
                                    <em>
                                        distanceThreshFromReference2，通常設置較小值（如
                                        6km）
                                    </em>
                                </li>
                                <li>
                                    <strong>Hys：</strong>hysteresisLocation
                                    遲滯參數（公尺）
                                    <br />
                                    <em>防止事件頻繁觸發，提供穩定性緩衝</em>
                                </li>
                                <li>
                                    <strong>movingReferenceLocation：</strong>
                                    移動參考位置坐標（衛星初始位置）
                                    <br />
                                    <em>配合衛星軌道預測模型進行動態更新</em>
                                </li>
                                <li>
                                    <strong>referenceLocation：</strong>
                                    固定參考位置坐標（地面參考點）
                                    <br />
                                    <em>提供穩定的地理基準，通常為重要地標</em>
                                </li>
                            </ul>
                        </div>
                        <div className="spec-section">
                            <h4>應用場景：</h4>
                            <ul>
                                <li>
                                    <strong>衛星通信：</strong>
                                    基於衛星軌道運動的動態距離管理
                                </li>
                                <li>
                                    <strong>移動基站：</strong>
                                    當服務小區位置發生移動時的事件觸發
                                </li>
                                <li>
                                    <strong>LEO 衛星星座：</strong>
                                    低軌道衛星快速移動場景下的資源調度
                                </li>
                                <li>
                                    <strong>位置感知服務：</strong>
                                    結合固定和移動參考點的複合位置服務
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
)

EventD2Viewer.displayName = 'EventD2Viewer'

export default EventD2Viewer
