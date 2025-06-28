import { Suspense, useRef, useCallback, useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import Starfield from '../shared/ui/effects/Starfield'
import MainScene from './MainScene'
import { Device } from '../../types/device'
import { SINRLegend } from '../domains/interference/detection/SINRHeatmap'
import PredictionAccuracyDashboard from '../domains/handover/prediction/PredictionAccuracyDashboard'
import E2EPerformanceMonitoringDashboard from '../dashboard/E2EPerformanceMonitoringDashboard'
import PredictiveMaintenanceViewer from '../domains/analytics/performance/PredictiveMaintenanceViewer'
import IntelligentRecommendationSystem from '../domains/analytics/ai/IntelligentRecommendationSystem'
import CoreNetworkSyncViewer from '../domains/monitoring/realtime/CoreNetworkSyncViewer'
import { HandoverStatusPanel } from '../domains/handover/execution/HandoverAnimation3D'

// 移除衛星圖例，因為已由側邊欄開關控制，不再需要額外說明

interface SceneViewProps {
    devices: Device[]
    auto: boolean
    manualDirection?: unknown
    onManualControl?: (direction: unknown) => void
    onUAVPositionUpdate?: (
        position: [number, number, number],
        deviceId?: number
    ) => void
    uavAnimation: boolean
    selectedReceiverIds?: number[]
    satellites?: Record<string, unknown>[]
    sceneName: string // 新增場景名稱參數
    // 階段四功能狀態
    interferenceVisualizationEnabled?: boolean
    sinrHeatmapEnabled?: boolean
    aiRanVisualizationEnabled?: boolean
    sionna3DVisualizationEnabled?: boolean
    realTimeMetricsEnabled?: boolean
    interferenceAnalyticsEnabled?: boolean
    // 階段五功能狀態
    uavSwarmCoordinationEnabled?: boolean
    meshNetworkTopologyEnabled?: boolean
    satelliteUavConnectionEnabled?: boolean
    failoverMechanismEnabled?: boolean
    // 階段六功能狀態
    predictionPath3DEnabled?: boolean
    predictionAccuracyDashboardEnabled?: boolean
    coreNetworkSyncEnabled?: boolean
    // Stage 3 功能
    realtimePerformanceMonitorEnabled?: boolean
    scenarioTestEnvironmentEnabled?: boolean
    // 3D 換手動畫相關
    handover3DAnimationEnabled?: boolean
    handoverState?: unknown
    currentConnection?: unknown
    predictedConnection?: unknown
    isTransitioning?: boolean
    transitionProgress?: number
    onHandoverEvent?: (event: unknown) => void
    // 階段七功能狀態
    e2ePerformanceMonitoringEnabled?: boolean
    testResultsVisualizationEnabled?: boolean
    performanceTrendAnalysisEnabled?: boolean
    automatedReportGenerationEnabled?: boolean
    // 階段八功能狀態
    predictiveMaintenanceEnabled?: boolean
    intelligentRecommendationEnabled?: boolean
    // 衛星相關 props（動畫永遠開啟）
    satelliteEnabled?: boolean
    satelliteSpeedMultiplier?: number
    handoverStableDuration?: number
    handoverMode?: 'demo' | 'real' // 換手模式控制
    // 🚀 演算法結果對接
    algorithmResults?: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }
}

export default function SceneView({
    devices = [],
    auto,
    manualDirection,
    onManualControl,
    onUAVPositionUpdate,
    uavAnimation,
    selectedReceiverIds = [],
    sceneName,
    interferenceVisualizationEnabled = false,
    sinrHeatmapEnabled = false,
    aiRanVisualizationEnabled = false,
    sionna3DVisualizationEnabled = false,
    realTimeMetricsEnabled = false,
    interferenceAnalyticsEnabled = false,
    uavSwarmCoordinationEnabled = false,
    meshNetworkTopologyEnabled = false,
    satelliteUavConnectionEnabled = false,
    failoverMechanismEnabled = false,
    predictionPath3DEnabled = false,
    predictionAccuracyDashboardEnabled = false,
    coreNetworkSyncEnabled = false,
    // Stage 3 功能  
    realtimePerformanceMonitorEnabled = false,
    scenarioTestEnvironmentEnabled = false,
    handover3DAnimationEnabled = false,
    handoverState,
    currentConnection,
    predictedConnection,
    isTransitioning = false,
    transitionProgress = 0,
    onHandoverEvent,
    e2ePerformanceMonitoringEnabled = false,
    testResultsVisualizationEnabled = false,
    performanceTrendAnalysisEnabled = false,
    automatedReportGenerationEnabled = false,
    predictiveMaintenanceEnabled = false,
    intelligentRecommendationEnabled = false,
    satelliteEnabled = false,
    satelliteSpeedMultiplier = 60,
    handoverStableDuration = 5,
    handoverMode = 'demo',
    algorithmResults,
}: SceneViewProps) {
    // Suppress unused variable warnings
    void realtimePerformanceMonitorEnabled
    void scenarioTestEnvironmentEnabled
    
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [satellites, setSatellites] = useState<Record<string, unknown>[]>([])
    const [handoverStatusInfo, setHandoverStatusInfo] = useState<unknown>(null)
    
    // 換手狀態更新回調
    const handleHandoverStatusUpdate = useCallback((statusInfo: unknown) => {
        setHandoverStatusInfo(statusInfo)
    }, [])
    
    // 測試用：載入衛星數據
    useEffect(() => {
        if (satelliteEnabled) {
            fetch('/api/v1/satellite-ops/visible_satellites?count=24&min_elevation_deg=5')
                .then(res => res.json())
                .then(data => {
                    // StereogramView: 載入衛星數據
                    setSatellites(data.satellites || [])
                })
                .catch(err => console.error('StereogramView: 衛星數據載入失敗:', err))
        } else {
            setSatellites([])
        }
    }, [satelliteEnabled])

    // WebGL 上下文恢復處理
    const handleWebGLContextLost = useCallback((event: Event) => {
        console.warn('WebGL 上下文丟失，嘗試恢復...')
        event.preventDefault()
    }, [])

    const handleWebGLContextRestored = useCallback(() => {
        console.log('WebGL 上下文已恢復')
    }, [])

    // 添加 WebGL 上下文事件監聽器
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
            {/* 星空星點層（在最底層，不影響互動） */}
            <Starfield starCount={180} />

            {/* 衛星圖例已移除，由側邊欄開關控制 */}
            
            {/* 添加 SINR 圖例 - 只有在啟用時才顯示 */}
            {sinrHeatmapEnabled && <SINRLegend />}
            
            
            {/* 添加預測精度儀表板 - 作為HTML覆蓋層 */}
            {predictionAccuracyDashboardEnabled && (
                <PredictionAccuracyDashboard isEnabled={predictionAccuracyDashboardEnabled} />
            )}
            
            {/* 添加核心網路同步監控 - 作為HTML覆蓋層 */}
            {coreNetworkSyncEnabled && (
                <CoreNetworkSyncViewer enabled={coreNetworkSyncEnabled} devices={devices} />
            )}
            
            
            {/* 添加階段七HTML覆蓋層組件 */}
            {e2ePerformanceMonitoringEnabled && (
                <E2EPerformanceMonitoringDashboard enabled={e2ePerformanceMonitoringEnabled} />
            )}
            
            {/* 添加階段八HTML覆蓋層組件 */}
            
            {predictiveMaintenanceEnabled && (
                <PredictiveMaintenanceViewer devices={devices} enabled={predictiveMaintenanceEnabled} />
            )}
            
            
            {intelligentRecommendationEnabled && (
                <IntelligentRecommendationSystem />
            )}
            
            {/* 🎯 換手狀態面板 */}
            <HandoverStatusPanel 
                enabled={satelliteUavConnectionEnabled && handover3DAnimationEnabled}
                statusInfo={handoverStatusInfo}
            />
            
            {/* 3D Canvas內容照舊，會蓋在星空上 */}
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
                    // 配置渲染器的上下文恢復選項
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
                        auto={auto}
                        manualDirection={manualDirection}
                        manualControl={onManualControl}
                        onUAVPositionUpdate={onUAVPositionUpdate}
                        uavAnimation={uavAnimation}
                        selectedReceiverIds={selectedReceiverIds}
                        sceneName={sceneName}
                        interferenceVisualizationEnabled={interferenceVisualizationEnabled}
                        sinrHeatmapEnabled={sinrHeatmapEnabled}
                        aiRanVisualizationEnabled={aiRanVisualizationEnabled}
                        sionna3DVisualizationEnabled={sionna3DVisualizationEnabled}
                        realTimeMetricsEnabled={realTimeMetricsEnabled}
                        interferenceAnalyticsEnabled={interferenceAnalyticsEnabled}
                        uavSwarmCoordinationEnabled={uavSwarmCoordinationEnabled}
                        meshNetworkTopologyEnabled={meshNetworkTopologyEnabled}
                        satelliteUavConnectionEnabled={satelliteUavConnectionEnabled}
                        failoverMechanismEnabled={failoverMechanismEnabled}
                        predictionPath3DEnabled={predictionPath3DEnabled}
                        handover3DAnimationEnabled={handover3DAnimationEnabled}
                        handoverState={handoverState}
                        currentConnection={currentConnection}
                        predictedConnection={predictedConnection}
                        isTransitioning={isTransitioning}
                        transitionProgress={transitionProgress}
                        onHandoverEvent={onHandoverEvent}
                        testResultsVisualizationEnabled={testResultsVisualizationEnabled}
                        performanceTrendAnalysisEnabled={performanceTrendAnalysisEnabled}
                        automatedReportGenerationEnabled={automatedReportGenerationEnabled}
                        satellites={satellites}
                        satelliteEnabled={satelliteEnabled}
                        satelliteSpeedMultiplier={satelliteSpeedMultiplier}
                        handoverStableDuration={handoverStableDuration}
                        handoverMode={handoverMode}
                        algorithmResults={algorithmResults}
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

// 添加CSS樣式
const styleSheet = document.createElement('style')
styleSheet.type = 'text/css'
styleSheet.innerHTML = `
/* 衛星圖例 CSS 已移除，不再需要 */
`
document.head.appendChild(styleSheet)
