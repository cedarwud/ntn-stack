/**
 * D2NarrationPanel - 動畫解說面板組件
 * 負責處理動畫解說系統、拖拽功能和浮動面板控制
 * 從 EventD2Viewer 中提取的動畫解說邏輯
 */

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import type { EventD2Params } from '../../types'
import '../NarrationPanel.scss' // 動畫解說面板樣式

// 解說內容項目接口
export interface NarrationItem {
    phase: string
    phaseTitle: string
    description: string
    technicalNote: string
    nextAction: string
    scenarioContext: string
    orbitalScenario: string
    constellationStrategy: string
    handoverScenario: string
    satelliteDistance: string
    fixedDistance: string
    timeProgress: string
    satelliteLat: string
    satelliteLon: string
    orbitalVelocity: string
    groundTrack: string
    currentDistance1: number
    currentDistance2: number
    triggerTimeRange: string
    satellitePosition: {
        lat: number
        lon: number
        altitude: number
        velocity: number
        orbitPeriod: number
        currentPhase: number
    }
}

// 面板位置接口
interface PanelPosition {
    x: number
    y: number
}

// 動畫解說面板 Props
interface D2NarrationPanelProps {
    params: EventD2Params
    showNarration: boolean
    showTechnicalDetails: boolean
    isNarrationExpanded: boolean
    onShowNarrationChange: (show: boolean) => void
    onShowTechnicalDetailsChange: (show: boolean) => void
    onIsNarrationExpandedChange: (expanded: boolean) => void
    isDarkTheme?: boolean
}

export const D2NarrationPanel: React.FC<D2NarrationPanelProps> = ({
    params,
    showNarration,
    showTechnicalDetails,
    isNarrationExpanded,
    onShowNarrationChange,
    onShowTechnicalDetailsChange,
    onIsNarrationExpandedChange,
    isDarkTheme = true,
}) => {
    // 動畫解說面板的位置和透明度狀態
    const [narrationPosition, setNarrationPosition] = useState<PanelPosition>(() => {
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

    // 使用 ref 直接操作 DOM
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

    // 初始化拖拽狀態的位置
    useEffect(() => {
        dragState.current.currentX = narrationPosition.x
        dragState.current.currentY = narrationPosition.y
    }, [narrationPosition.x, narrationPosition.y])

    // 核心拖拽更新函數
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
                animationFrameId.current = requestAnimationFrame(updatePosition)
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

    // 拖拽處理函數
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
            dragState.current.offsetX = e.clientX - dragState.current.currentX
            dragState.current.offsetY = e.clientY - dragState.current.currentY
            setIsDragging(true)

            document.addEventListener('mousemove', handleMouseMove)
            document.addEventListener('mouseup', handleMouseUp)
        },
        [handleMouseMove, handleMouseUp]
    )

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
            const earthRotationOffset = (timeSeconds * earthRotationRate) / 3600 // 小時轉換

            return {
                lat: centerLat + orbitRadius * Math.cos(angle),
                lon: centerLon + orbitRadius * Math.sin(angle) - earthRotationOffset * 0.1, // 地球自轉修正
                altitude: altitude,
                velocity: orbitalVelocity,
                orbitPeriod: orbitPeriod,
                currentPhase: (timeSeconds % orbitPeriod) / orbitPeriod, // 軌道相位 (0-1)
            }
        },
        [params.movingReferenceLocation]
    )

    // 動畫解說內容生成 - 基於衛星軌道和 LEO 星座切換策略
    const narrationContent = useMemo((): NarrationItem => {
        const currentTime = 45 // 固定時間點用於演示
        const satellitePosition = calculateSatellitePosition(currentTime)

        // 模擬 UE 位置
        const _uePosition = { lat: 0.048, lon: 0.528 }

        // 計算軌道參數
        const orbitalVelocity = 7.5 // km/s for LEO at 550km
        const _orbitalPeriod = 5570 // seconds for real LEO orbit
        const groundTrackSpeed = orbitalVelocity * Math.cos((Math.PI / 180) * 53) // 軌道傾角53度

        // 模擬距離值（實際應用中會基於真實地理計算）
        let simulatedDistance1: number, simulatedDistance2: number

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
                (simulatedDistance1 - params.Hys) / 1000
            ).toFixed(1)} > ${(params.Thresh1 / 1000).toFixed(
                1
            )} km\\n固定距離: ${(simulatedDistance2 / 1000).toFixed(1)} + ${
                params.Hys / 1000
            } = ${((simulatedDistance2 + params.Hys) / 1000).toFixed(1)} < ${(
                params.Thresh2 / 1000
            ).toFixed(
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
            description = `衛星距離條件已滿足 (${(simulatedDistance1 / 1000).toFixed(
                1
            )} km > ${(params.Thresh1 / 1000).toFixed(
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
                (simulatedDistance1 - params.Hys) / 1000
            ).toFixed(1)} > ${(params.Thresh1 / 1000).toFixed(
                1
            )}\\n條件2: ❌ Ml2 + Hys = ${(
                (simulatedDistance2 + params.Hys) / 1000
            ).toFixed(1)} ≮ ${(params.Thresh2 / 1000).toFixed(
                1
            )}\\n\\n候選衛星評估：\\n• 仰角門檻：> 15度\\n• 預期服務時間：> 8分鐘\\n• 負載容量：< 80%\\n• 切換延遲：< 50ms`
            nextAction = '繼續監控並準備候選衛星資源，等待最佳切換時機'
        } else if (!condition1 && condition2) {
            phase = 'partial'
            phaseTitle = '⚠️ 星座監控中 - 當前衛星服務中'
            description = `固定參考點距離條件已滿足 (${(simulatedDistance2 / 1000).toFixed(
                1
            )} km < ${(params.Thresh2 / 1000).toFixed(
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
                (simulatedDistance1 - params.Hys) / 1000
            ).toFixed(1)} ≯ ${(params.Thresh1 / 1000).toFixed(
                1
            )}\\n條件2: ✅ Ml2 + Hys = ${(
                (simulatedDistance2 + params.Hys) / 1000
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
            technicalNote = `衛星距離: ${(simulatedDistance1 / 1000).toFixed(
                1
            )} km, 固定距離: ${(simulatedDistance2 / 1000).toFixed(
                1
            )} km\\n\\nLEO 星座監控重點：\\n• 多衛星可見性分析\\n• 信號品質趨勢預測\\n• 軌道機動影響評估\\n• 星座完整性驗證\\n• 切換演算法性能優化\\n• 用戶移動性適應`
            nextAction = '持續星座監控，優化切換演算法和服務品質'
        }

        // 根據時間添加詳細的 LEO 軌道情境解說
        let scenarioContext = ''
        let orbitalScenario = ''
        if (currentTime < 30) {
            scenarioContext = '🚀 場景：LEO衛星從地平線升起，開始進入服務範圍'
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
            currentDistance1: simulatedDistance1, // UE 到移動參考位置
            currentDistance2: simulatedDistance2, // UE 到固定參考位置
            triggerTimeRange: '20-80秒',
            satellitePosition, // 當前衛星位置
        }
    }, [params, calculateSatellitePosition])

    // 如果不顯示解說面板，返回 null
    if (!showNarration) {
        return null
    }

    return (
        <div
            ref={narrationPanelRef}
            className={`narration-panel ${isDragging ? 'dragging' : ''} ${
                isDarkTheme ? 'dark-theme' : 'light-theme'
            }`}
            style={{
                position: 'fixed',
                left: 0,
                top: 0,
                transform: `translate(${narrationPosition.x}px, ${narrationPosition.y}px)`,
                opacity: narrationOpacity,
                zIndex: 1000,
                width: isNarrationMinimized ? '280px' : '420px',
                maxHeight: isNarrationMinimized ? '60px' : '80vh',
                overflow: isNarrationMinimized ? 'hidden' : 'auto',
                transition: isDragging ? 'none' : 'all 0.3s ease',
            }}
            onMouseDown={handleMouseDown}
        >
            {/* 面板標題欄 */}
            <div className="narration-header">
                <h4 className="narration-title">
                    🛰️ LEO 星座 D2 事件動畫解說
                </h4>
                <div className="narration-controls">
                    <button
                        className="narration-btn"
                        onClick={() => setIsNarrationMinimized(!isNarrationMinimized)}
                        title={isNarrationMinimized ? '展開' : '最小化'}
                    >
                        {isNarrationMinimized ? '📖' : '📕'}
                    </button>
                    <button
                        className="narration-btn"
                        onClick={() => onShowTechnicalDetailsChange(!showTechnicalDetails)}
                        title="切換技術詳情"
                    >
                        🔧
                    </button>
                    <button
                        className="narration-btn"
                        onClick={() => onIsNarrationExpandedChange(!isNarrationExpanded)}
                        title={isNarrationExpanded ? '收縮' : '展開'}
                    >
                        {isNarrationExpanded ? '🔽' : '🔼'}
                    </button>
                    <button
                        className="narration-btn close-btn"
                        onClick={() => onShowNarrationChange(false)}
                        title="關閉解說"
                    >
                        ✕
                    </button>
                </div>
            </div>

            {/* 透明度控制 */}
            {!isNarrationMinimized && (
                <div className="opacity-control">
                    <label>透明度: {Math.round(narrationOpacity * 100)}%</label>
                    <input
                        type="range"
                        min="0.3"
                        max="1"
                        step="0.05"
                        value={narrationOpacity}
                        onChange={(e) => setNarrationOpacity(parseFloat(e.target.value))}
                        className="opacity-slider"
                    />
                </div>
            )}

            {/* 主要內容 */}
            {!isNarrationMinimized && (
                <div className="narration-content">
                    {/* 當前階段狀態 */}
                    <div className={`phase-indicator phase-${narrationContent.phase}`}>
                        <h5>{narrationContent.phaseTitle}</h5>
                        <p>{narrationContent.description}</p>
                    </div>

                    {/* 星座切換策略 */}
                    <div className="constellation-strategy">
                        <h6>{narrationContent.constellationStrategy}</h6>
                        <div className="handover-scenario">
                            {narrationContent.handoverScenario.split('\\n').map((line, i) => (
                                <p key={i}>{line}</p>
                            ))}
                        </div>
                    </div>

                    {/* 軌道情境解說 */}
                    <div className="scenario-context">
                        <h6>{narrationContent.scenarioContext}</h6>
                        <p>{narrationContent.orbitalScenario}</p>
                    </div>

                    {/* 技術詳情 */}
                    {showTechnicalDetails && (
                        <div className="technical-details">
                            <h6>📊 技術參數詳情</h6>
                            <pre className="technical-note">
                                {narrationContent.technicalNote.split('\\n').join('\n')}
                            </pre>
                        </div>
                    )}

                    {/* 下一步動作 */}
                    <div className="next-action">
                        <h6>🎯 下一步動作</h6>
                        <p>{narrationContent.nextAction}</p>
                    </div>

                    {/* 擴展詳情 */}
                    {isNarrationExpanded && (
                        <div className="expanded-details">
                            <div className="orbital-data">
                                <h6>🛰️ 軌道數據</h6>
                                <div className="data-grid">
                                    <div>衛星距離: {narrationContent.satelliteDistance} km</div>
                                    <div>固定距離: {narrationContent.fixedDistance} km</div>
                                    <div>時間進度: {narrationContent.timeProgress}</div>
                                    <div>衛星位置: {narrationContent.satelliteLat}°, {narrationContent.satelliteLon}°</div>
                                    <div>軌道速度: {narrationContent.orbitalVelocity}</div>
                                    <div>地面軌跡: {narrationContent.groundTrack}</div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default D2NarrationPanel