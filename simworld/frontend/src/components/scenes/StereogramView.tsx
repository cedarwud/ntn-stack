import { Suspense, useRef, useCallback, useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import Starfield from '../ui/Starfield'
import MainScene from './MainScene'
import { Device } from '../../types/device'
import { VisibleSatelliteInfo } from '../../types/satellite'
import { SINRLegend } from './visualization/SINRHeatmap'
import HandoverPerformanceDashboard from '../dashboard/HandoverPerformanceDashboard'
import PredictionAccuracyDashboard from '../dashboard/PredictionAccuracyDashboard'
import E2EPerformanceMonitoringDashboard from '../dashboard/E2EPerformanceMonitoringDashboard'
import MLModelMonitoringDashboard from '../dashboard/MLModelMonitoringDashboard'
import PredictiveMaintenanceViewer from '../viewers/PredictiveMaintenanceViewer'
import AdaptiveLearningSystemViewer from '../viewers/AdaptiveLearningSystemViewer'
import IntelligentRecommendationSystem from '../viewers/IntelligentRecommendationSystem'
import CoreNetworkSyncViewer from '../viewers/CoreNetworkSyncViewer'
import AnomalyAlertSystem from '../viewers/AnomalyAlertSystem'
import SatelliteConnectionPanel from '../ui/SatelliteConnectionPanel'

// 移除衛星圖例，因為已由側邊欄開關控制，不再需要額外說明

interface SceneViewProps {
    devices: Device[]
    auto: boolean
    manualDirection?: any
    onManualControl?: (direction: any) => void
    onUAVPositionUpdate?: (
        position: [number, number, number],
        deviceId?: number
    ) => void
    uavAnimation: boolean
    selectedReceiverIds?: number[]
    satellites?: VisibleSatelliteInfo[]
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
    handoverPredictionEnabled?: boolean
    handoverDecisionVisualizationEnabled?: boolean
    predictionPath3DEnabled?: boolean
    handoverPerformanceDashboardEnabled?: boolean
    predictionAccuracyDashboardEnabled?: boolean
    coreNetworkSyncEnabled?: boolean
    // Stage 3 異常處理功能
    anomalyAlertSystemEnabled?: boolean
    // 3D 換手動畫相關
    handover3DAnimationEnabled?: boolean
    handoverState?: any
    currentConnection?: any
    predictedConnection?: any
    isTransitioning?: boolean
    transitionProgress?: number
    onHandoverEvent?: (event: any) => void
    // 階段七功能狀態
    e2ePerformanceMonitoringEnabled?: boolean
    testResultsVisualizationEnabled?: boolean
    performanceTrendAnalysisEnabled?: boolean
    automatedReportGenerationEnabled?: boolean
    // 階段八功能狀態
    mlModelMonitoringEnabled?: boolean
    predictiveMaintenanceEnabled?: boolean
    adaptiveLearningEnabled?: boolean
    intelligentRecommendationEnabled?: boolean
}

export default function SceneView({
    devices = [],
    auto,
    manualDirection,
    onManualControl,
    onUAVPositionUpdate,
    uavAnimation,
    selectedReceiverIds = [],
    satellites = [],
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
    handoverPredictionEnabled = false,
    handoverDecisionVisualizationEnabled = false,
    predictionPath3DEnabled = false,
    handoverPerformanceDashboardEnabled = false,
    predictionAccuracyDashboardEnabled = false,
    coreNetworkSyncEnabled = false,
    // Stage 3 異常處理功能
    anomalyAlertSystemEnabled = false,
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
    mlModelMonitoringEnabled = false,
    predictiveMaintenanceEnabled = false,
    adaptiveLearningEnabled = false,
    intelligentRecommendationEnabled = false,
}: SceneViewProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [satelliteConnections, setSatelliteConnections] = useState<any[]>([])
    
    // 處理衛星連線數據更新
    const handleConnectionsUpdate = useCallback((connections: any[]) => {
        setSatelliteConnections(connections)
    }, [])

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
            
            {/* 添加換手性能儀表板 - 作為HTML覆蓋層 */}
            {handoverPerformanceDashboardEnabled && (
                <HandoverPerformanceDashboard enabled={handoverPerformanceDashboardEnabled} />
            )}
            
            {/* 添加預測精度儀表板 - 作為HTML覆蓋層 */}
            {predictionAccuracyDashboardEnabled && (
                <PredictionAccuracyDashboard isEnabled={predictionAccuracyDashboardEnabled} />
            )}
            
            {/* 添加核心網路同步監控 - 作為HTML覆蓋層 */}
            {coreNetworkSyncEnabled && (
                <CoreNetworkSyncViewer enabled={coreNetworkSyncEnabled} devices={devices} />
            )}
            
            {/* Stage 3 異常監控系統 - 作為HTML覆蓋層 */}
            {anomalyAlertSystemEnabled && (
                <AnomalyAlertSystem enabled={anomalyAlertSystemEnabled} devices={devices} />
            )}
            
            {/* 添加階段七HTML覆蓋層組件 */}
            {e2ePerformanceMonitoringEnabled && (
                <E2EPerformanceMonitoringDashboard enabled={e2ePerformanceMonitoringEnabled} />
            )}
            
            {/* 添加階段八HTML覆蓋層組件 */}
            {mlModelMonitoringEnabled && (
                <MLModelMonitoringDashboard enabled={mlModelMonitoringEnabled} />
            )}
            
            {predictiveMaintenanceEnabled && (
                <PredictiveMaintenanceViewer devices={devices} enabled={predictiveMaintenanceEnabled} />
            )}
            
            {adaptiveLearningEnabled && (
                <AdaptiveLearningSystemViewer devices={devices} enabled={adaptiveLearningEnabled} />
            )}
            
            {intelligentRecommendationEnabled && (
                <IntelligentRecommendationSystem devices={devices} enabled={intelligentRecommendationEnabled} />
            )}
            
            {/* 衛星連線狀態面板 - 顯示在右上角 */}
            <SatelliteConnectionPanel 
                enabled={satelliteUavConnectionEnabled} 
                connections={satelliteConnections}
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
                        satellites={satellites}
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
                        handoverPredictionEnabled={handoverPredictionEnabled}
                        handoverDecisionVisualizationEnabled={handoverDecisionVisualizationEnabled}
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
                        onSatelliteConnectionsUpdate={handleConnectionsUpdate}
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
