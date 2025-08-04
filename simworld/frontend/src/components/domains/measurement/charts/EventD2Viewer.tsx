/**
 * Event D2 Viewer Component - 重構版本
 * 提供完整的 Event D2 移動參考位置測量事件查看功能
 * 包含參數控制和 3GPP TS 38.331 規範實現
 * 
 * 重構改進：
 * - 使用 D2DataManager Hook 管理數據
 * - 使用 D2NarrationPanel 組件處理動畫解說
 * - 簡化主組件邏輯，專注於狀態協調和UI控制
 */

import React, { useState, useCallback, useMemo } from 'react'
import PureD2Chart from './PureD2Chart'
import { useD2DataManager, RealD2DataPoint } from './d2-components/D2DataManager'
import D2NarrationPanel from './d2-components/D2NarrationPanel'
import type { EventD2Params } from '../types'
import './EventA4Viewer.scss' // 完全重用 A4 的樣式，確保左側控制面板風格一致

interface EventD2ViewerProps {
    isDarkTheme?: boolean
    onThemeToggle?: () => void
    initialParams?: Partial<EventD2Params>
    // 新增：支援 Modal 模式的屬性
    onReportLastUpdateToNavbar?: (timestamp: number) => void
    reportRefreshHandlerToNavbar?: React.MutableRefObject<(() => void) | null>
    reportIsLoadingToNavbar?: (loading: boolean) => void
    currentScene?: string
    // 新增：支援不同模式的屬性
    mode?: 'processing' | 'real-events' | 'dashboard'
    pageTitle?: string
    showModeSpecificFeatures?: boolean
}

export const EventD2Viewer: React.FC<EventD2ViewerProps> = React.memo(
    ({ 
        isDarkTheme = true, 
        onThemeToggle, 
        initialParams = {},
        mode = 'dashboard',
        pageTitle,
        showModeSpecificFeatures = true
    }) => {
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

        // UI 控制狀態
        const [showThresholdLines, setShowThresholdLines] = useState(true)
        const [currentMode, setCurrentMode] = useState<'simulation' | 'real-data'>('simulation')
        const [showNarration, setShowNarration] = useState(true)
        const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)
        const [isNarrationExpanded, setIsNarrationExpanded] = useState(false)

        // 使用數據管理 Hook
        const dataManager = useD2DataManager({
            params,
            onDataLoad: (data) => {
                console.log('✅ [EventD2Viewer] 數據載入完成:', data.length)
            },
            onError: (error) => {
                console.error('❌ [EventD2Viewer] 數據載入錯誤:', error)
            },
            onLoadingChange: (loading) => {
                console.log('🔄 [EventD2Viewer] 載入狀態變更:', loading)
            },
        })

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

        // 模式切換處理函數
        const handleModeToggle = useCallback(
            async (mode: 'simulation' | 'real-data') => {
                setCurrentMode(mode)

                if (mode === 'real-data') {
                    console.log('🚀 [EventD2Viewer] 切換到真實數據模式')
                    // 切換到真實模式時載入數據
                    await dataManager.loadRealData()
                } else {
                    console.log('🔄 [EventD2Viewer] 切換到模擬數據模式')
                }
            },
            [dataManager]
        )

        // 根據模式獲取配置
        const getModeConfig = useCallback((mode: string) => {
            switch(mode) {
                case 'processing':
                    return { title: 'D2數據分析', showAdvancedControls: true }
                case 'real-events': 
                    return { title: 'Real D2 Events', showRealDataOnly: true }
                case 'dashboard':
                    return { title: 'D2 移動參考位置事件', showFullFeatures: true }
                default:
                    return { title: 'Event D2 Viewer', showFullFeatures: true }
            }
        }, [])

        const modeConfig = getModeConfig(mode)
        const displayTitle = pageTitle || modeConfig.title

        // 星座信息輔助函數（從 DataManager 取得）
        const getConstellationInfo = dataManager.getConstellationInfo

        // 記錄模式變更
        useMemo(() => {
            console.log(`🎯 [EventD2Viewer] 運行模式: ${mode}, 標題: ${displayTitle}`)
        }, [mode, displayTitle])

        return (
            <div className="event-a4-viewer">
                <div className="event-viewer__content">
                    {/* 控制面板 */}
                    <div className="event-viewer__controls">
                        <div className="control-panel">
                            {/* D2事件控制 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    📊 {displayTitle}
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
                                            <span className="control-label">
                                                衛星星座
                                            </span>
                                            <select
                                                value={dataManager.selectedConstellation}
                                                onChange={(e) =>
                                                    dataManager.handleConstellationChange(
                                                        e.target.value as
                                                            | 'starlink'
                                                            | 'oneweb'
                                                            | 'gps'
                                                    )
                                                }
                                                className="control-select"
                                                disabled={dataManager.isLoadingRealData}
                                            >
                                                <option value="starlink">
                                                    Starlink (7,954 顆)
                                                </option>
                                                <option value="oneweb">
                                                    OneWeb (651 顆)
                                                </option>
                                                <option value="gps">
                                                    GPS (32 顆)
                                                </option>
                                            </select>
                                        </div>
                                        <div className="control-item">
                                            <span className="control-label">
                                                時間段
                                            </span>
                                            <select
                                                value={dataManager.selectedTimeRange.durationMinutes}
                                                onChange={(e) =>
                                                    dataManager.handleTimeRangeChange({
                                                        durationMinutes: Number(e.target.value),
                                                    })
                                                }
                                                className="control-select"
                                                disabled={dataManager.isLoadingRealData}
                                            >
                                                <option value={5}>
                                                    5 分鐘 (短期觀測)
                                                </option>
                                                <option value={15}>
                                                    15 分鐘 (中期觀測)
                                                </option>
                                                <option value={30}>
                                                    30 分鐘 (長期觀測)
                                                </option>
                                                <option value={60}>
                                                    1 小時 (部分軌道)
                                                </option>
                                                <option value={120}>
                                                    2 小時 (LEO完整軌道)
                                                </option>
                                            </select>
                                        </div>
                                    </div>
                                )}

                                {/* 數據模式切換 */}
                                <div className="control-group">
                                    <span className="control-label">數據模式</span>
                                    <div className="mode-toggle-group">
                                        <button
                                            className={`mode-toggle-btn ${
                                                currentMode === 'simulation'
                                                    ? 'active'
                                                    : ''
                                            }`}
                                            onClick={() => handleModeToggle('simulation')}
                                            disabled={dataManager.isLoadingRealData}
                                        >
                                            🎮 模擬數據
                                        </button>
                                        <button
                                            className={`mode-toggle-btn ${
                                                currentMode === 'real-data'
                                                    ? 'active'
                                                    : ''
                                            }`}
                                            onClick={() => handleModeToggle('real-data')}
                                            disabled={dataManager.isLoadingRealData}
                                        >
                                            {dataManager.isLoadingRealData ? (
                                                <>🔄 載入中...</>
                                            ) : (
                                                <>🛰️ NetStack 真實數據</>
                                            )}
                                        </button>
                                    </div>
                                </div>

                                {/* 載入狀態和錯誤顯示 */}
                                {dataManager.realDataError && (
                                    <div className="error-message">
                                        ❌ {dataManager.realDataError}
                                    </div>
                                )}

                                {/* 星座信息顯示 */}
                                {currentMode === 'real-data' && (
                                    <div className="constellation-info">
                                        <h4>📡 {dataManager.selectedConstellation.toUpperCase()} 星座</h4>
                                        <p className="constellation-description">
                                            {getConstellationInfo(dataManager.selectedConstellation).description}
                                        </p>
                                        <p className="constellation-characteristics">
                                            {getConstellationInfo(dataManager.selectedConstellation).characteristics}
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* 參數控制區塊 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    ⚙️ D2 參數控制
                                </h3>
                                
                                {/* Thresh1 控制 */}
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            距離門檻1 (Thresh1) - 衛星距離
                                        </label>
                                        <input
                                            type="number"
                                            min="100000"
                                            max="2000000"
                                            step="1000"
                                            value={params.Thresh1}
                                            onChange={(e) =>
                                                updateParam('Thresh1', Number(e.target.value))
                                            }
                                            className="control-input"
                                        />
                                        <span className="control-unit">
                                            {(params.Thresh1 / 1000).toFixed(1)} km
                                        </span>
                                    </div>
                                </div>

                                {/* Thresh2 控制 */}
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            距離門檻2 (Thresh2) - 固定距離
                                        </label>
                                        <input
                                            type="number"
                                            min="1000"
                                            max="100000"
                                            step="100"
                                            value={params.Thresh2}
                                            onChange={(e) =>
                                                updateParam('Thresh2', Number(e.target.value))
                                            }
                                            className="control-input"
                                        />
                                        <span className="control-unit">
                                            {(params.Thresh2 / 1000).toFixed(1)} km
                                        </span>
                                    </div>
                                </div>

                                {/* Hysteresis 控制 */}
                                <div className="control-group">
                                    <div className="control-item">
                                        <label className="control-label">
                                            磁滯 (Hysteresis)
                                        </label>
                                        <input
                                            type="number"
                                            min="100"
                                            max="5000"
                                            step="50"
                                            value={params.Hys}
                                            onChange={(e) =>
                                                updateParam('Hys', Number(e.target.value))
                                            }
                                            className="control-input"
                                        />
                                        <span className="control-unit">
                                            {(params.Hys / 1000).toFixed(2)} km
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* 動畫解說控制 */}
                            <div className="control-section">
                                <h3 className="control-section__title">
                                    🎬 動畫解說
                                </h3>
                                <div className="control-group control-group--buttons">
                                    <button
                                        className={`control-btn ${
                                            showNarration ? 'control-btn--active' : ''
                                        }`}
                                        onClick={() => setShowNarration(!showNarration)}
                                    >
                                        {showNarration ? '🔊' : '🔇'} 解說面板
                                    </button>
                                    <button
                                        className={`control-btn ${
                                            showTechnicalDetails ? 'control-btn--active' : ''
                                        }`}
                                        onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                                    >
                                        🔧 技術詳情
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 圖表區域 */}
                    <div className="event-viewer__chart">
                        <PureD2Chart
                            params={params}
                            showThresholdLines={showThresholdLines}
                            realD2Data={currentMode === 'real-data' ? dataManager.realD2Data : []}
                            currentMode={currentMode}
                            isDarkTheme={isDarkTheme}
                        />
                    </div>
                </div>

                {/* 動畫解說面板 */}
                <D2NarrationPanel
                    params={params}
                    showNarration={showNarration}
                    showTechnicalDetails={showTechnicalDetails}
                    isNarrationExpanded={isNarrationExpanded}
                    onShowNarrationChange={setShowNarration}
                    onShowTechnicalDetailsChange={setShowTechnicalDetails}
                    onIsNarrationExpandedChange={setIsNarrationExpanded}
                    isDarkTheme={isDarkTheme}
                />
            </div>
        )
    }
)

EventD2Viewer.displayName = 'EventD2Viewer'

export default EventD2Viewer