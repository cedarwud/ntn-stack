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
    
    // 使用統一的數據同步上下文獲取衛星數據
    const { state } = useDataSync()
    const satellites = satelliteState.satelliteEnabled ? (state.simworld.satellites || []) : []

    const handleHandoverStatusUpdate = useCallback((statusInfo: unknown) => {
        setHandoverStatusInfo(statusInfo)
    }, [])

    // 衛星數據現在通過 DataSyncContext 統一管理，不需要額外的 API 調用
    useEffect(() => {
        if (satelliteState.satelliteEnabled) {
            console.log('🚀 StereogramView: 使用 DataSyncContext 統一的衛星數據，數量:', satellites.length)
        } else {
            console.log('📡 StereogramView: 衛星顯示已禁用')
        }
    }, [satelliteState.satelliteEnabled, satellites.length])

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
                    console.log('WebGL 渲染器已創建')
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
                        handoverTimingSpeed={
                            handoverState.handoverTimingSpeed
                        }
                        algorithmResults={handoverState.algorithmResults}
                        onHandoverStatusUpdate={handleHandoverStatusUpdate}
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
        </div>
    )
}
