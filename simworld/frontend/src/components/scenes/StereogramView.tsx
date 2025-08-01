import { Suspense, useRef, useCallback, useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import Starfield from '../shared/ui/effects/Starfield'
import MainScene from './MainScene'
import { Device } from '../../types/device'
import { SINRLegend } from '../domains/interference/detection/SINRHeatmap'
import FullChartAnalysisDashboard from '../layout/FullChartAnalysisDashboard'
import PredictiveMaintenanceViewer from '../domains/analytics/performance/PredictiveMaintenanceViewer'
import IntelligentRecommendationSystem from '../domains/analytics/ai/IntelligentRecommendationSystem'
import CoreNetworkSyncViewer from '../domains/monitoring/realtime/CoreNetworkSyncViewer'
import { HandoverStatusPanel } from '../domains/handover/execution/HandoverAnimation3D'
import {
    FeatureState,
    HandoverState,
    SatelliteState,
    UIState,
} from '../../contexts/appStateHooks'
import { useDataSync } from '../../contexts/DataSyncContext'

// Phase 2: 新增組件導入
import SatelliteAnimationController from '../domains/satellite/animation/SatelliteAnimationController'
import HandoverEventVisualizer from '../domains/handover/visualization/HandoverEventVisualizer'
import type { HandoverEvent } from '../../types/satellite'

interface SceneViewProps {
    devices: Device[]
    uiState: UIState
    featureState: FeatureState
    handoverState: HandoverState
    satelliteState: SatelliteState
    sceneName: string
    onUAVPositionUpdate?: (
        position: [number, number, number],
        deviceId?: number
    ) => void
    onManualControl?: (direction: unknown) => void
    onHandoverEvent?: (event: unknown) => void
}

export default function SceneView({
    devices = [],
    uiState,
    featureState,
    handoverState,
    satelliteState,
    sceneName,
    onUAVPositionUpdate,
    onManualControl,
    onHandoverEvent,
}: SceneViewProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [handoverStatusInfo, setHandoverStatusInfo] = useState<unknown>(null)

    // Phase 2: 新增狀態管理
    const [currentLocation, setCurrentLocation] = useState('ntpu')
    // 修復：使用 AppStateContext 中的星座選擇，確保與側邊欄同步
    const currentConstellation = satelliteState.selectedConstellation
    const [satellitePositions, setSatellitePositions] = useState<
        Map<string, [number, number, number]>
    >(new Map())
    const [handoverEvents, setHandoverEvents] = useState<HandoverEvent[]>([])
    const [animationConfig] = useState({
        acceleration: 1, // 修正：改為 1 倍速度
        distanceScale: 0.1,
        fps: 30,
        smoothing: true,
    })

    // 使用統一的數據同步上下文獲取衛星數據
    const { state } = useDataSync()
    // 修復：使用 AppStateContext 中的統一衛星數據，確保與側邊欄同步
    const satellites = satelliteState.satelliteEnabled
        ? satelliteState.skyfieldSatellites || []
        : []

    const handleHandoverStatusUpdate = useCallback((statusInfo: unknown) => {
        setHandoverStatusInfo(statusInfo)
    }, [])

    // Phase 2: 事件處理函數
    const handleLocationChange = useCallback(
        (locationId: string) => {
            console.log(`🌍 切換觀測點: ${currentLocation} -> ${locationId}`)
            setCurrentLocation(locationId)
            // 清除當前衛星位置，等待新數據載入
            setSatellitePositions(new Map())
        },
        [currentLocation]
    )

    const handleSatellitePositions = useCallback(
        (positions: Map<string, [number, number, number]>) => {
            setSatellitePositions(positions)
        },
        []
    )

    const handleHandoverEvent = useCallback(
        (event: HandoverEvent) => {
            console.log(
                `🔄 換手事件: ${event.fromSatelliteId} -> ${event.toSatelliteId}`
            )
            setHandoverEvents((prev) => [...prev, event])

            // 通知父組件
            if (onHandoverEvent) {
                onHandoverEvent(event)
            }
        },
        [onHandoverEvent]
    )

    const handleHandoverComplete = useCallback((event: HandoverEvent) => {
        console.log(
            `✅ 換手完成: ${event.fromSatelliteId} -> ${event.toSatelliteId}`
        )
    }, [])

    // 衛星數據現在通過 DataSyncContext 統一管理，不需要額外的 API 調用
    useEffect(() => {
        if (satelliteState.satelliteEnabled) {
            // 只在有錯誤或首次載入時記錄日誌
            if (satellites.length === 0) {
                console.log(`⚠️ StereogramView: [${currentConstellation.toUpperCase()}] 無衛星數據`)
            }
        }
    }, [
        satelliteState.satelliteEnabled,
        satellites.length,
        currentConstellation,
    ])

    const handleWebGLContextLost = useCallback((event: Event) => {
        console.warn('WebGL 上下文丟失，嘗試恢復...')
        event.preventDefault()
    }, [])

    const handleWebGLContextRestored = useCallback(() => {
        console.log('WebGL 上下文已恢復')
    }, [])

    useEffect(() => {
        const canvas = canvasRef.current
        if (canvas) {
            canvas.addEventListener('webglcontextlost', handleWebGLContextLost)
            canvas.addEventListener(
                'webglcontextrestored',
                handleWebGLContextRestored
            )

            return () => {
                canvas.removeEventListener(
                    'webglcontextlost',
                    handleWebGLContextLost
                )
                canvas.removeEventListener(
                    'webglcontextrestored',
                    handleWebGLContextRestored
                )
            }
        }
    }, [handleWebGLContextLost, handleWebGLContextRestored])

    return (
        <div
            className="scene-container"
            style={{
                width: '100%',
                height: '100%',
                position: 'relative',
                background:
                    'radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%)',
                overflow: 'hidden',
            }}
        >
            <Starfield starCount={180} />

            {featureState.sinrHeatmapEnabled && <SINRLegend />}

            {featureState.predictionAccuracyDashboardEnabled && (
                <FullChartAnalysisDashboard
                    isOpen={featureState.predictionAccuracyDashboardEnabled}
                    onClose={() => {}}
                />
            )}

            {featureState.coreNetworkSyncEnabled && (
                <CoreNetworkSyncViewer
                    enabled={featureState.coreNetworkSyncEnabled}
                    devices={devices}
                />
            )}

            {featureState.predictiveMaintenanceEnabled && (
                <PredictiveMaintenanceViewer
                    devices={devices}
                    enabled={featureState.predictiveMaintenanceEnabled}
                />
            )}

            {featureState.intelligentRecommendationEnabled && (
                <IntelligentRecommendationSystem />
            )}

            <HandoverStatusPanel
                enabled={
                    featureState.satelliteUavConnectionEnabled &&
                    handoverState.handover3DAnimationEnabled
                }
                statusInfo={handoverStatusInfo}
            />

            <Canvas
                ref={canvasRef}
                shadows
                camera={{ position: [0, 400, 500], near: 0.1, far: 1e4 }}
                gl={{
                    toneMapping: THREE.ACESFilmicToneMapping,
                    toneMappingExposure: 1.2,
                    alpha: true,
                    preserveDrawingBuffer: false,
                    powerPreference: 'high-performance',
                    antialias: true,
                    failIfMajorPerformanceCaveat: false,
                }}
                onCreated={({ gl }) => {
                    gl.debug.checkShaderErrors = true
                    // console.log('WebGL 渲染器已創建')
                }}
            >
                <hemisphereLight args={[0xffffff, 0x444444, 1.0]} />
                <ambientLight intensity={0.2} />
                <directionalLight
                    castShadow
                    position={[15, 30, 10]}
                    intensity={1.5}
                    shadow-mapSize-width={4096}
                    shadow-mapSize-height={4096}
                    shadow-camera-near={1}
                    shadow-camera-far={1000}
                    shadow-camera-top={500}
                    shadow-camera-bottom={-500}
                    shadow-camera-left={500}
                    shadow-camera-right={-500}
                    shadow-bias={-0.0004}
                    shadow-radius={8}
                />
                <Suspense fallback={null}>
                    <MainScene
                        devices={devices}
                        auto={uiState.auto}
                        manualDirection={uiState.manualDirection}
                        manualControl={onManualControl}
                        onUAVPositionUpdate={onUAVPositionUpdate}
                        uavAnimation={uiState.uavAnimation}
                        selectedReceiverIds={uiState.selectedReceiverIds}
                        sceneName={sceneName}
                        interferenceVisualizationEnabled={
                            featureState.interferenceVisualizationEnabled
                        }
                        sinrHeatmapEnabled={featureState.sinrHeatmapEnabled}
                        aiRanVisualizationEnabled={
                            featureState.aiRanVisualizationEnabled
                        }
                        sionna3DVisualizationEnabled={
                            featureState.sionna3DVisualizationEnabled
                        }
                        realTimeMetricsEnabled={
                            featureState.realTimeMetricsEnabled
                        }
                        interferenceAnalyticsEnabled={
                            featureState.interferenceAnalyticsEnabled
                        }
                        uavSwarmCoordinationEnabled={
                            featureState.uavSwarmCoordinationEnabled
                        }
                        meshNetworkTopologyEnabled={
                            featureState.meshNetworkTopologyEnabled
                        }
                        satelliteUavConnectionEnabled={
                            featureState.satelliteUavConnectionEnabled
                        }
                        failoverMechanismEnabled={
                            featureState.failoverMechanismEnabled
                        }
                        predictionPath3DEnabled={
                            featureState.predictionPath3DEnabled
                        }
                        handover3DAnimationEnabled={
                            handoverState.handover3DAnimationEnabled
                        }
                        handoverState={handoverState.handoverState}
                        currentConnection={handoverState.currentConnection}
                        predictedConnection={handoverState.predictedConnection}
                        isTransitioning={handoverState.isTransitioning}
                        transitionProgress={handoverState.transitionProgress}
                        onHandoverEvent={onHandoverEvent}
                        testResultsVisualizationEnabled={
                            featureState.testResultsVisualizationEnabled
                        }
                        performanceTrendAnalysisEnabled={
                            featureState.performanceTrendAnalysisEnabled
                        }
                        automatedReportGenerationEnabled={
                            featureState.automatedReportGenerationEnabled
                        }
                        satellites={satellites}
                        satelliteEnabled={satelliteState.satelliteEnabled}
                        satelliteSpeedMultiplier={
                            handoverState.handoverStableDuration
                        }
                        handoverStableDuration={
                            handoverState.handoverStableDuration
                        }
                        handoverMode={handoverState.handoverMode}
                        satelliteMovementSpeed={
                            handoverState.satelliteMovementSpeed
                        }
                        handoverTimingSpeed={handoverState.handoverTimingSpeed}
                        algorithmResults={handoverState.algorithmResults}
                        onHandoverStatusUpdate={handleHandoverStatusUpdate}
                    />

                    {/* Phase 2: 衛星動畫控制器 - 修復：使用統一衛星數據 */}
                    <SatelliteAnimationController
                        enabled={satelliteState.satelliteEnabled}
                        location={currentLocation}
                        constellation={currentConstellation}
                        animationConfig={animationConfig}
                        onHandoverEvent={handleHandoverEvent}
                        onSatellitePositions={handleSatellitePositions}
                        unifiedSatellites={satellites}
                    />

                    {/* Phase 2: 換手事件視覺化 */}
                    <HandoverEventVisualizer
                        enabled={satelliteState.satelliteEnabled}
                        handoverEvents={handoverEvents}
                        currentTime={0} // 這裡需要從 TimelineController 獲取
                        satellitePositions={satellitePositions}
                        onHandoverComplete={handleHandoverComplete}
                        showTrails={true}
                        animationDuration={3.0}
                    />

                    <ContactShadows
                        position={[0, 0.1, 0]}
                        opacity={0.4}
                        scale={400}
                        blur={1.5}
                        far={50}
                    />
                </Suspense>
                <OrbitControls makeDefault />
            </Canvas>

            {/* Phase 2 UI 控制組件已移至側邊欄 */}
        </div>
    )
}
