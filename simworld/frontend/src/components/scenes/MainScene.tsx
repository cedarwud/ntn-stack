import { useLayoutEffect, useMemo, useState, useCallback } from 'react'
import { useGLTF } from '@react-three/drei'
import { useThree } from '@react-three/fiber'
import type { OrbitControls as OrbitControlsImpl } from 'three-stdlib'
import * as THREE from 'three'
import { TextureLoader, RepeatWrapping, SRGBColorSpace } from 'three'
import UAVFlight, {
    UAVManualDirection,
} from '../domains/device/visualization/UAVFlight'
import StaticModel from './StaticModel'
import { ApiRoutes } from '../../config/apiRoutes'
import {
    getBackendSceneName,
    getSceneTextureName,
} from '../../utils/sceneUtils'
import InterferenceOverlay from '../domains/interference/detection/InterferenceOverlay'
import SINRHeatmap from '../domains/interference/detection/SINRHeatmap'
import AIRANVisualization from '../domains/interference/mitigation/AIRANVisualization'
import Sionna3DVisualization from '../domains/simulation/sionna/Sionna3DVisualization'
import RealTimeMetrics from './visualization/RealTimeMetrics'
import InterferenceAnalytics from '../domains/interference/analysis/InterferenceAnalytics'
import UAVSwarmCoordination from '../domains/simulation/coordination/UAVSwarmCoordination'
import MeshNetworkTopology from './visualization/MeshNetworkTopology'
import FailoverMechanism from '../domains/interference/mitigation/FailoverMechanism'
import TestResultsVisualization from '../domains/analytics/testing/TestResultsVisualization'
import PerformanceTrendAnalyzer from '../domains/analytics/performance/PerformanceTrendAnalyzer'
import AutomatedReportGenerator from '../domains/analytics/ai/AutomatedReportGenerator'
// import HandoverAnomalyVisualization from './visualization/HandoverAnomalyVisualization' // 未使用，已註釋
import HandoverAnimation3D from '../domains/handover/execution/HandoverAnimation3D'
import PredictionPath3D from '../shared/visualization/PredictionPath3D'
import DynamicSatelliteRenderer from '../domains/satellite/visualization/DynamicSatelliteRenderer'

export interface MainSceneProps {
    devices: unknown[]
    auto: boolean
    manualControl?: (direction: UAVManualDirection) => void
    manualDirection?: UAVManualDirection
    onUAVPositionUpdate?: (
        position: [number, number, number],
        deviceId?: number
    ) => void
    uavAnimation: boolean
    selectedReceiverIds?: number[]
    sceneName: string
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
    // 新增 3D 換手動畫相關 props
    handover3DAnimationEnabled?: boolean
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    handoverState?: any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    currentConnection?: any
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    predictedConnection?: any
    isTransitioning?: boolean
    transitionProgress?: number
    onHandoverEvent?: (event: Event) => void
    // 階段七功能狀態
    testResultsVisualizationEnabled?: boolean
    performanceTrendAnalysisEnabled?: boolean
    automatedReportGenerationEnabled?: boolean
    // 衛星相關 props（動畫永遠開啟）
    satellites?: unknown[]
    satelliteEnabled?: boolean
    satelliteSpeedMultiplier?: number
    handoverStableDuration?: number
    handoverMode?: 'demo' | 'real' // 換手模式控制
    // 🚀 演算法結果 - 用於對接視覺化
    algorithmResults?: {
        currentSatelliteId?: string
        predictedSatelliteId?: string
        handoverStatus?: 'idle' | 'calculating' | 'handover_ready' | 'executing'
        binarySearchActive?: boolean
        predictionConfidence?: number
    }
    // 🎯 換手狀態回調
    onHandoverStatusUpdate?: (statusInfo: unknown) => void
    // 🎯 SINR 圖例數據回調
    onSinrLegendData?: (data: {
        realMetrics: unknown | null
        dataMode: 'simulation' | 'real' | 'hybrid'
    }) => void
}

const UAV_SCALE = 10

const MainScene: React.FC<MainSceneProps> = ({
    devices = [],
    auto,
    manualDirection,
    manualControl,
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
    handover3DAnimationEnabled = false,
    handoverState,
    currentConnection,
    predictedConnection,
    isTransitioning = false,
    transitionProgress = 0,
    onHandoverEvent,
    testResultsVisualizationEnabled = false,
    performanceTrendAnalysisEnabled = false,
    automatedReportGenerationEnabled = false,
    satellites = [],
    satelliteEnabled = false,
    satelliteSpeedMultiplier = 60,
    handoverStableDuration = 5,
    handoverMode = 'demo',
    algorithmResults,
    onHandoverStatusUpdate,
    onSinrLegendData,
}) => {
    // 標記未使用但保留的props為已消費（避免TypeScript警告）
    void handoverState
    void isTransitioning
    void transitionProgress
    void onHandoverEvent

    // 根據場景名稱動態生成 URL
    const backendSceneName = getBackendSceneName(sceneName)
    const SCENE_URL = ApiRoutes.scenes.getSceneModel(backendSceneName)
    const BS_MODEL_URL = ApiRoutes.simulations.getModel('tower')
    const JAMMER_MODEL_URL = ApiRoutes.simulations.getModel('jam')
    const SATELLITE_TEXTURE_URL = ApiRoutes.scenes.getSceneTexture(
        backendSceneName,
        getSceneTextureName(sceneName)
    )

    // 🔗 衛星位置狀態管理 - 用於 HandoverAnimation3D
    const [satellitePositions, setSatellitePositions] = useState<
        Map<string, [number, number, number]>
    >(new Map())

    // 🔗 換手狀態管理 - 用於同步給 DynamicSatelliteRenderer
    const [internalHandoverState, setInternalHandoverState] =
        useState<unknown>(null)

    // 衛星位置更新回調
    const handleSatellitePositions = useCallback(
        (positions: Map<string, [number, number, number]>) => {
            setSatellitePositions(positions)
        },
        []
    )

    // 換手狀態更新回調
    const handleHandoverStateUpdate = useCallback((state: Event) => {
        setInternalHandoverState(state)
    }, [])

    // 動態預加載模型以提高性能
    useMemo(() => {
        useGLTF.preload(SCENE_URL)
        useGLTF.preload(BS_MODEL_URL)
        useGLTF.preload(JAMMER_MODEL_URL)
    }, [SCENE_URL, BS_MODEL_URL, JAMMER_MODEL_URL])

    // 加載主場景模型，使用 useMemo 避免重複加載
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { scene: mainScene } = useGLTF(SCENE_URL) as any
    const { controls } = useThree()

    useLayoutEffect(() => {
        ;(controls as OrbitControlsImpl)?.target?.set(0, 0, 0)
    }, [controls])

    const prepared = useMemo(() => {
        const root = mainScene.clone(true)
        let maxArea = 0
        let groundMesh: THREE.Mesh | null = null
        const loader = new TextureLoader()
        const satelliteTexture = loader.load(SATELLITE_TEXTURE_URL)
        satelliteTexture.wrapS = RepeatWrapping
        satelliteTexture.wrapT = RepeatWrapping
        satelliteTexture.colorSpace = SRGBColorSpace
        satelliteTexture.repeat.set(1, 1)
        satelliteTexture.anisotropy = 16
        satelliteTexture.flipY = false

        // 處理場景中的所有網格
        root.traverse((o: THREE.Object3D) => {
            if ((o as THREE.Mesh).isMesh) {
                const m = o as THREE.Mesh
                m.castShadow = true
                m.receiveShadow = true

                // 處理可能的材質問題
                if (m.material) {
                    // 確保材質能正確接收光照
                    if (Array.isArray(m.material)) {
                        m.material.forEach((mat) => {
                            if (mat instanceof THREE.MeshBasicMaterial) {
                                const newMat = new THREE.MeshStandardMaterial({
                                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                    color: (mat as any).color,
                                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                    map: (mat as any).map,
                                })
                                mat = newMat
                            }
                        })
                    } else if (m.material instanceof THREE.MeshBasicMaterial) {
                        const basicMat = m.material
                        const newMat = new THREE.MeshStandardMaterial({
                            color: basicMat.color,
                            map: basicMat.map,
                        })
                        m.material = newMat
                    }
                }

                if (m.geometry) {
                    m.geometry.computeBoundingBox()
                    const bb = m.geometry.boundingBox
                    if (bb) {
                        const size = new THREE.Vector3()
                        bb.getSize(size)
                        const area = size.x * size.z
                        if (area > maxArea) {
                            if (groundMesh) groundMesh.castShadow = true
                            maxArea = area
                            groundMesh = m
                            groundMesh.material =
                                new THREE.MeshStandardMaterial({
                                    map: satelliteTexture,
                                    color: 0xffffff,
                                    roughness: 0.8,
                                    metalness: 0.1,
                                    emissive: 0x555555,
                                    emissiveIntensity: 0.4,
                                    vertexColors: false,
                                    normalScale: new THREE.Vector2(0.5, 0.5),
                                })
                            groundMesh.receiveShadow = true
                            groundMesh.castShadow = false
                        }
                    }
                }
            }
        })
        return root
    }, [mainScene, SATELLITE_TEXTURE_URL])

    const deviceMeshes = useMemo(() => {
        return devices.map((device: Event) => {
            const isSelected =
                device.role === 'receiver' &&
                device.id !== null &&
                selectedReceiverIds.includes(device.id)

            if (device.role === 'receiver') {
                const position: [number, number, number] = [
                    device.position_x,
                    device.position_z,
                    device.position_y,
                ]

                const shouldControl = isSelected

                return (
                    <UAVFlight
                        key={
                            device.id ||
                            `temp-${device.position_x}-${device.position_y}-${device.position_z}`
                        }
                        position={position}
                        scale={[UAV_SCALE, UAV_SCALE, UAV_SCALE]}
                        auto={shouldControl ? auto : false}
                        manualDirection={shouldControl ? manualDirection : null}
                        onManualMoveDone={() => {
                            if (manualControl) {
                                manualControl(null)
                            }
                        }}
                        onPositionUpdate={(pos) => {
                            if (onUAVPositionUpdate && shouldControl) {
                                onUAVPositionUpdate(
                                    pos,
                                    device.id !== null ? device.id : undefined
                                )
                            }
                        }}
                        uavAnimation={shouldControl ? uavAnimation : false}
                    />
                )
            } else if (device.role === 'desired') {
                return (
                    <StaticModel
                        key={device.id}
                        url={BS_MODEL_URL}
                        position={[
                            device.position_x,
                            device.position_z + 5,
                            device.position_y,
                        ]}
                        scale={[0.05, 0.05, 0.05]}
                        pivotOffset={[0, -900, 0]}
                    />
                )
            } else if (device.role === 'jammer') {
                return (
                    <StaticModel
                        key={device.id}
                        url={JAMMER_MODEL_URL}
                        position={[
                            device.position_x,
                            device.position_z + 5,
                            device.position_y,
                        ]}
                        scale={[0.005, 0.005, 0.005]}
                        pivotOffset={[0, -8970, 0]}
                    />
                )
            } else {
                return null
            }
        })
    }, [
        devices,
        auto,
        manualDirection,
        onUAVPositionUpdate,
        manualControl,
        uavAnimation,
        selectedReceiverIds,
        BS_MODEL_URL,
        JAMMER_MODEL_URL,
    ])

    return (
        <>
            <primitive object={prepared} castShadow receiveShadow />
            {deviceMeshes}

            {/* 階段四可視化覆蓋層 */}
            <InterferenceOverlay
                devices={devices}
                enabled={interferenceVisualizationEnabled}
            />
            <SINRHeatmap
                devices={devices}
                enabled={sinrHeatmapEnabled}
                onLegendData={onSinrLegendData}
            />
            <AIRANVisualization
                devices={devices}
                enabled={aiRanVisualizationEnabled}
            />
            <Sionna3DVisualization
                devices={devices}
                enabled={sionna3DVisualizationEnabled}
            />
            <RealTimeMetrics
                devices={devices}
                enabled={realTimeMetricsEnabled}
            />
            <InterferenceAnalytics
                devices={devices}
                enabled={interferenceAnalyticsEnabled}
            />

            {/* 階段五可視化覆蓋層 */}
            <UAVSwarmCoordination
                devices={devices}
                enabled={uavSwarmCoordinationEnabled}
            />
            <MeshNetworkTopology
                devices={devices}
                enabled={meshNetworkTopologyEnabled}
            />
            <FailoverMechanism
                devices={devices}
                enabled={failoverMechanismEnabled}
            />

            {/* 🚀 新的換手連接線動畫系統 - 根據 handover.md 設計 */}
            <HandoverAnimation3D
                devices={devices}
                enabled={
                    satelliteUavConnectionEnabled && handover3DAnimationEnabled
                }
                satellitePositions={satellitePositions}
                stableDuration={handoverStableDuration}
                handoverMode={handoverMode}
                onStatusUpdate={onHandoverStatusUpdate}
                onHandoverStateUpdate={handleHandoverStateUpdate}
            />

            {/* 階段七可視化覆蓋層 */}
            <TestResultsVisualization
                devices={devices}
                enabled={testResultsVisualizationEnabled}
            />
            <PerformanceTrendAnalyzer
                devices={devices}
                enabled={performanceTrendAnalysisEnabled}
            />
            <AutomatedReportGenerator
                devices={devices}
                enabled={automatedReportGenerationEnabled}
            />

            {/* 衛星渲染器 - 動態軌跡模擬 */}
            <DynamicSatelliteRenderer
                satellites={satellites}
                enabled={satelliteEnabled}
                currentConnection={currentConnection}
                predictedConnection={predictedConnection}
                showLabels={true}
                speedMultiplier={satelliteSpeedMultiplier}
                algorithmResults={algorithmResults}
                handoverState={internalHandoverState}
                onSatelliteClick={(satelliteId) => {
                    console.log('🛰️ 點擊衛星:', satelliteId)
                    // 可以在這裡處理衛星點擊事件
                }}
                onSatellitePositions={handleSatellitePositions}
            />

            {/* 階段六換手視覺化 */}
            <PredictionPath3D
                satellites={satellites}
                enabled={predictionPath3DEnabled}
            />
        </>
    )
}

export default MainScene
