import React, { useRef, useMemo } from 'react'
import * as THREE from 'three'
import { useFrame, useThree } from '@react-three/fiber'
import StaticModel from '../StaticModel'
import { VisibleSatelliteInfo } from '../../../types/satellite'
import { SatellitePassTemplate } from '../../../utils/satellite/satellitePassTemplates'
import {
    getColorFromElevation,
    calculateSpeedFactor,
} from '../../../utils/satellite/satelliteHelpers'
import {
    GLB_SCENE_SIZE,
    MIN_SAT_HEIGHT,
    MAX_SAT_HEIGHT,
    PASS_DURATION_MIN,
    PASS_DURATION_MAX,
    SAT_SCALE,
    SAT_MODEL_URL,
} from '../../../utils/satellite/satelliteConstants'

// 效能相關常數
const PI_DIV_180 = Math.PI / 180 // 預計算常用值
const MAX_VISIBLE_DISTANCE = GLB_SCENE_SIZE * 1.2 // 最大可見距離
const VISIBILITY_ELEVATION_THRESHOLD = 0.5 // 可見性仰角閾值 (度)
const COLOR_UPDATE_THRESHOLD = 5 // 顏色更新閾值 (度)
const MODEL_DETAIL_HIGH = 12 // 高精度模型
const MODEL_DETAIL_MEDIUM = 8 // 中精度模型
const MODEL_DETAIL_LOW = 6 // 低精度模型
const DISTANCE_LOD_NEAR = 1000 // 近距離臨界點
const DISTANCE_LOD_MEDIUM = 1500 // 中距離臨界點
const UPDATE_INTERVAL_NEAR = 1 // 近處更新頻率 (每幀)
const UPDATE_INTERVAL_MEDIUM = 2 // 中距更新頻率 (每2幀)
const UPDATE_INTERVAL_FAR = 4 // 遠處更新頻率 (每4幀)

interface SimplifiedSatelliteProps {
    satellite: VisibleSatelliteInfo
    index: number
    passTemplate: SatellitePassTemplate
}

const SimplifiedSatellite = React.memo(
    ({ satellite, index, passTemplate }: SimplifiedSatelliteProps) => {
        const groupRef = useRef<THREE.Group>(null)
        const { camera } = useThree()

        // 使用 useRef 而非 useState 避免不必要的重渲染
        const materialRef = useRef<THREE.MeshBasicMaterial>(null)
        const pointLightRef = useRef<THREE.PointLight>(null)
        const frameCountRef = useRef(0) // 用於追蹤幀數

        // 優化：使用 useMemo 為效能相關計算建立查表內容
        const updateFrequencyLookup = useMemo(() => {
            // 根據距離決定更新頻率
            return {
                getUpdateFrequency: (distance: number) => {
                    if (distance < DISTANCE_LOD_NEAR)
                        return UPDATE_INTERVAL_NEAR
                    if (distance < DISTANCE_LOD_MEDIUM)
                        return UPDATE_INTERVAL_MEDIUM
                    return UPDATE_INTERVAL_FAR
                },
                getGeometryDetail: (distance: number) => {
                    if (distance < DISTANCE_LOD_NEAR) return MODEL_DETAIL_HIGH
                    if (distance < DISTANCE_LOD_MEDIUM)
                        return MODEL_DETAIL_MEDIUM
                    return MODEL_DETAIL_LOW
                },
                shouldUpdateLight: (distance: number) => {
                    // 遠距離時不更新燈光
                    return distance < DISTANCE_LOD_MEDIUM
                },
            }
        }, [])

        // 使用 useRef 管理衛星數據
        const satelliteState = useRef({
            // 通過時間 (秒)
            passDuration:
                PASS_DURATION_MIN +
                Math.random() * (PASS_DURATION_MAX - PASS_DURATION_MIN),
            // 通過進度 (0-1)
            progress: Math.random(), // 隨機初始進度以錯開不同衛星
            // 可見性狀態
            visible: true,
            // 仰角相關
            currentElevationDeg: satellite.elevation_deg,
            // 當前距離
            currentDistance: satellite.distance_km || 1000,
            // 色彩
            color: getColorFromElevation(satellite.elevation_deg),
            // 上次更新時間 - 用於節流
            lastUpdateTime: 0,
            // 記錄位置和旋轉用於平滑過渡
            lastPosition: new THREE.Vector3(0, 0, 0),
            lastRotation: 0,
            // 距離攝影機的距離
            distanceToCamera: 0,
            // 更新頻率
            updateFrequency: UPDATE_INTERVAL_NEAR,
        })

        // 初始隨機位置 - 只計算一次以提高性能
        const initialPosition = useMemo(() => {
            const elevation = satellite.elevation_deg * PI_DIV_180
            const azimuth = satellite.azimuth_deg * PI_DIV_180

            // 基於場景大小計算位置
            const distance = GLB_SCENE_SIZE * 0.4
            const x = distance * Math.sin(azimuth)
            const y = distance * Math.cos(azimuth)
            const z =
                MIN_SAT_HEIGHT +
                (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) * Math.sin(elevation)

            return { x, y, z }
        }, [satellite.elevation_deg, satellite.azimuth_deg])

        // 優化：計算是否需要在此幀執行更新
        const shouldUpdate = (state: any, frequency: number) => {
            frameCountRef.current = (frameCountRef.current + 1) % 1000 // 防止溢出
            return frameCountRef.current % frequency === 0
        }

        // 動畫邏輯
        useFrame((state, delta) => {
            if (!groupRef.current) return

            // 優化：視距剔除檢查
            const distanceToCamera = groupRef.current.position.distanceTo(
                camera.position
            )
            satelliteState.current.distanceToCamera = distanceToCamera

            // 如果超出最大可見距離，隱藏並跳過其餘計算
            if (distanceToCamera > MAX_VISIBLE_DISTANCE) {
                if (groupRef.current.visible) {
                    groupRef.current.visible = false
                }
                return
            }

            // 確定適合當前距離的更新頻率
            const updateFrequency =
                updateFrequencyLookup.getUpdateFrequency(distanceToCamera)
            satelliteState.current.updateFrequency = updateFrequency

            // 優化：根據距離應用不同更新頻率
            if (!shouldUpdate(state, updateFrequency)) {
                return
            }

            // 獲取通過數據
            const {
                passDuration,
                progress: currentProgress,
                currentDistance,
            } = satelliteState.current

            // 計算速度因子 - 距離越近，視角移動越快
            const distanceFactor = calculateSpeedFactor(
                groupRef.current.position.y,
                currentDistance
            )

            // 更新進度，考慮距離因子和更新頻率
            // 距離越近，視角運動越快
            // 更新頻率越低，每次更新需要更大的步進
            const progressDelta =
                (delta * distanceFactor * updateFrequency) / passDuration
            satelliteState.current.progress += progressDelta

            // 進度循環
            if (satelliteState.current.progress > 1) {
                satelliteState.current.progress = 0

                // 生成新的通過時間
                satelliteState.current.passDuration =
                    PASS_DURATION_MIN +
                    Math.random() * (PASS_DURATION_MAX - PASS_DURATION_MIN)
            }

            // 計算當前通過位置
            const progress = satelliteState.current.progress
            const { startAzimuth, endAzimuth, maxElevation } = passTemplate

            // 根據進度計算當前方位角 (線性)
            const currentAzimuthDeg =
                startAzimuth + (endAzimuth - startAzimuth) * progress
            const currentAzimuthRad = currentAzimuthDeg * PI_DIV_180

            // 根據進度計算當前仰角 (拋物線形狀)
            // 使用sin函數創建平滑的仰角變化
            const elevationProgress = Math.sin(progress * Math.PI) // 0->1->0
            const currentElevationDeg = maxElevation * elevationProgress
            const currentElevationRad = currentElevationDeg * PI_DIV_180

            // 更新距離
            const baseDistance = 1000 // 基準距離 (km)
            const variationRange = 400 // 變化範圍 (km)
            const normalizedDistance =
                baseDistance - variationRange * Math.sin(progress * Math.PI)
            satelliteState.current.currentDistance = normalizedDistance

            // 保存當前仰角，用於顏色計算
            satelliteState.current.currentElevationDeg = currentElevationDeg

            // 決定可見性 - 僅當仰角大於閾值時可見
            const newVisible =
                currentElevationDeg > VISIBILITY_ELEVATION_THRESHOLD

            // 只有當可見性需要變更時才更新
            if (newVisible !== satelliteState.current.visible) {
                satelliteState.current.visible = newVisible

                // 如果不可見且元素存在，就隱藏它
                if (!newVisible && groupRef.current) {
                    groupRef.current.visible = false
                } else if (newVisible && groupRef.current) {
                    groupRef.current.visible = true

                    // 更新顏色
                    const newColor = getColorFromElevation(currentElevationDeg)
                    satelliteState.current.color = newColor
                    if (materialRef.current) {
                        materialRef.current.color = newColor
                    }
                    if (
                        pointLightRef.current &&
                        updateFrequencyLookup.shouldUpdateLight(
                            distanceToCamera
                        )
                    ) {
                        pointLightRef.current.color = newColor
                    }
                }
            }

            // 如果不可見則跳過其他計算
            if (!satelliteState.current.visible) return

            // 計算3D空間中的位置
            // 使用球面坐標到笛卡爾坐標的轉換
            const range = GLB_SCENE_SIZE * 0.45 // 場景半徑
            const horizontalDist = range * Math.cos(currentElevationRad)

            const x = horizontalDist * Math.sin(currentAzimuthRad)
            const y = horizontalDist * Math.cos(currentAzimuthRad)

            // 高度基於仰角 - 使用非線性映射讓變化更明顯
            const height =
                MIN_SAT_HEIGHT +
                (MAX_SAT_HEIGHT - MIN_SAT_HEIGHT) *
                    Math.pow(Math.sin(currentElevationRad), 0.8)

            // 優化：只有在需要時才更新顏色 (遠處衛星減少顏色更新)
            const now = state.clock.elapsedTime
            const timeSinceLastUpdate =
                now - satelliteState.current.lastUpdateTime
            const shouldUpdateColors =
                timeSinceLastUpdate > 0.5 && // 節流
                updateFrequencyLookup.shouldUpdateLight(distanceToCamera) && // 根據距離決定
                Math.abs(
                    currentElevationDeg -
                        satelliteState.current.currentElevationDeg
                ) > COLOR_UPDATE_THRESHOLD // 仰角變化顯著

            if (shouldUpdateColors) {
                satelliteState.current.lastUpdateTime = now
                const newColor = getColorFromElevation(currentElevationDeg)
                satelliteState.current.color = newColor

                if (materialRef.current) {
                    materialRef.current.color = newColor
                }
                if (pointLightRef.current) {
                    pointLightRef.current.color = newColor
                }
            }

            // 更新位置
            groupRef.current.position.set(x, height, y)

            // 優化：僅在較近距離計算朝向
            if (distanceToCamera < DISTANCE_LOD_MEDIUM) {
                // 計算朝向 - 始終朝向軌道方向
                const nextProgress = Math.min(progress + 0.01, 1)
                const nextAzimuthDeg =
                    startAzimuth + (endAzimuth - startAzimuth) * nextProgress
                const nextAzimuthRad = nextAzimuthDeg * PI_DIV_180

                const facingDir = new THREE.Vector2(
                    Math.sin(nextAzimuthRad) - Math.sin(currentAzimuthRad),
                    Math.cos(nextAzimuthRad) - Math.cos(currentAzimuthRad)
                )

                // 只有當向量長度不為零時才更新旋轉
                if (facingDir.length() > 0.001) {
                    // 計算朝向方向
                    const newRotation = Math.atan2(facingDir.x, facingDir.y)
                    groupRef.current.rotation.y = newRotation
                    satelliteState.current.lastRotation = newRotation
                }
            } else {
                // 遠處衛星使用上次計算的旋轉角度
                groupRef.current.rotation.y =
                    satelliteState.current.lastRotation
            }
        })

        // 如果不可見就不渲染
        if (!satelliteState.current.visible) return null

        // 根據距離調整衛星幾何體詳細度 - 性能優化
        // 在渲染時根據初始距離設定基本細節級別
        const initialDistance = satellite.distance_km || 1000
        const geometryDetail =
            updateFrequencyLookup.getGeometryDetail(initialDistance)

        // 光照強度也根據距離調整
        const lightIntensity = initialDistance < DISTANCE_LOD_NEAR ? 120 : 80
        const lightDistance = initialDistance < DISTANCE_LOD_NEAR ? 25 : 15

        return (
            <group
                ref={groupRef}
                position={[
                    initialPosition.x,
                    initialPosition.z,
                    initialPosition.y,
                ]}
            >
                {/* 始終渲染完整模型，不做距離簡化 */}
                <StaticModel
                    url={SAT_MODEL_URL}
                    scale={[SAT_SCALE, SAT_SCALE, SAT_SCALE]}
                    pivotOffset={[0, 0, 0]}
                    position={[0, 0, 0]}
                />

                {/* 近距離才渲染點光源 */}
                {initialDistance < DISTANCE_LOD_MEDIUM ? (
                    <pointLight
                        ref={pointLightRef}
                        color={satelliteState.current.color}
                        intensity={lightIntensity}
                        distance={lightDistance}
                        decay={2}
                    />
                ) : null}

                <mesh>
                    <sphereGeometry
                        args={[1.5, geometryDetail, geometryDetail]}
                    />
                    <meshBasicMaterial
                        ref={materialRef}
                        color={satelliteState.current.color}
                        transparent={true}
                        opacity={
                            initialDistance < DISTANCE_LOD_MEDIUM ? 0.6 : 0.4
                        }
                    />
                </mesh>
            </group>
        )
    }
)

export default SimplifiedSatellite
