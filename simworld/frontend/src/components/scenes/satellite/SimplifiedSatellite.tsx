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

        // 重新設計：真實的衛星軌跡運動
        const satelliteState = useRef({
            // 基於真實衛星參數的軌道配置
            passDuration: 180 + index * 30, // 180-450秒的通過時間（更真實的通過時間）
            startAzimuth: satellite.azimuth_deg - 90, // 從當前方位角-90度開始
            endAzimuth: satellite.azimuth_deg + 90,   // 到當前方位角+90度結束
            maxElevation: satellite.max_elevation_deg || satellite.elevation_deg + 15, // 使用配置的最大仰角
            
            // 運動狀態
            currentTime: Math.random() * 90, // 隨機起始時間，錯開衛星
            currentElevationDeg: 0,
            currentAzimuthDeg: 0,
            currentDistance: 1000,
            
            // 永遠可見（簡化測試）
            visible: true,
            
            // 視覺狀態
            color: getColorFromElevation(45),
            lastUpdateTime: 0,
            lastPosition: new THREE.Vector3(0, 0, 0),
            lastRotation: 0,
            distanceToCamera: 0,
            updateFrequency: UPDATE_INTERVAL_NEAR,
        })

        // 移除重複的 orbitStateRef，整合到 satelliteState 中

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

        // 重新設計：持續軌道運動邏輯，支持換手流程
        useFrame((state, delta) => {
            if (!groupRef.current) return

            // 累積時間 - 持續運動，不重置
            satelliteState.current.currentTime += delta

            // 優化：視距剔除檢查（但衛星仍保持存在）
            const distanceToCamera = groupRef.current.position.distanceTo(camera.position)
            satelliteState.current.distanceToCamera = distanceToCamera

            // 確定適合當前距離的更新頻率
            const updateFrequency = updateFrequencyLookup.getUpdateFrequency(distanceToCamera)
            satelliteState.current.updateFrequency = updateFrequency

            // 根據距離應用不同更新頻率
            if (!shouldUpdate(state, updateFrequency)) {
                return
            }

            // === 真實衛星軌跡計算：從地平線升起，劃過天空，落下 ===
            const { 
                passDuration,
                startAzimuth,
                endAzimuth,
                maxElevation
            } = satelliteState.current
            
            // 通過進度：使用連續的sin波函數，避免重置跳閃
            // 將軌跡設計為連續的8字形或圓形軌道，不重置
            const continuousTime = satelliteState.current.currentTime * 0.5 // 減慢速度
            const progress = (Math.sin(continuousTime * Math.PI / passDuration) + 1) / 2 // 0-1之間的連續值
            
            // 使用連續的有效進度，不再有重置
            const validProgress = progress
            
            // 方位角：均速從起始點移動到結束點
            const currentAzimuthDeg = startAzimuth + (endAzimuth - startAzimuth) * validProgress
            const currentAzimuthRad = currentAzimuthDeg * PI_DIV_180
            
            // 仰角：拋物線軌跡，中間最高
            // 使用 sin(π * progress) 創造平滑的升起-最高-落下軌跡
            const elevationProgress = Math.sin(validProgress * Math.PI)
            const currentElevationDeg = maxElevation * elevationProgress
            const currentElevationRad = currentElevationDeg * PI_DIV_180
            
            // 距離：基於真實的仰角-距離關係
            // 仰角越高距離越近（因為衛星直接在頭頂）
            const baseDistance = 550 // LEO 衛星高度 (km)
            const currentDistance = baseDistance / Math.max(0.1, Math.sin(currentElevationRad))
            
            // 衛星始終可見，不再隱藏（避免跳閃）
            // 允許完整的仰角範圍，不強制最低值
            const adjustedElevationDeg = Math.max(0, currentElevationDeg) // 允許0度以上的所有仰角
            const isVisible = true
            
            // 更新衛星狀態
            satelliteState.current.currentElevationDeg = currentElevationDeg
            satelliteState.current.currentAzimuthDeg = currentAzimuthDeg
            satelliteState.current.currentDistance = currentDistance
            satelliteState.current.visible = isVisible
            
            // === 位置計算：球面到直角坐標系轉換 ===
            // 場景半徑：基於仰角的動態距離
            const sceneRadius = GLB_SCENE_SIZE * 0.4
            const horizontalDistance = sceneRadius * Math.cos(currentElevationRad)
            
            // X, Y 座標：基於方位角
            const x = horizontalDistance * Math.sin(currentAzimuthRad)
            const y = horizontalDistance * Math.cos(currentAzimuthRad)
            
            // Z 座標（高度）：基於真實仰角，允許完整的高度範圍
            const minHeight = MIN_SAT_HEIGHT
            const maxHeight = MAX_SAT_HEIGHT
            // 使用真實仰角計算高度，不限制最低值
            const heightFactor = Math.sin(Math.max(0, currentElevationDeg) * PI_DIV_180)
            const height = minHeight + (maxHeight - minHeight) * heightFactor
            
            // 更新位置 - 統一坐標系：(x, y, z) 對應 (x, z, y)
            groupRef.current.position.set(x, height, y)
            
            // 控制可見性
            groupRef.current.visible = isVisible
            
            // 調試：監控第一顆衛星的仰角變化
            if (index === 0 && Math.floor(satelliteState.current.currentTime) % 5 === 0 && 
                Math.floor(satelliteState.current.currentTime) !== Math.floor(satelliteState.current.currentTime - delta)) {
                console.log(`🛰️ 衛星 ${index} - 仰角: ${currentElevationDeg.toFixed(1)}°, 進度: ${(validProgress * 100).toFixed(1)}%`)
            }
            
            // === 視覺效果更新 ===
            // 顏色更新：基於仰角和信號強度
            const now = state.clock.elapsedTime
            const timeSinceLastUpdate = now - satelliteState.current.lastUpdateTime
            
            if (timeSinceLastUpdate > 0.5 && updateFrequencyLookup.shouldUpdateLight(distanceToCamera)) {
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

            // 朝向計算：衛星面向運動方向（軌跡切線）
            if (distanceToCamera < DISTANCE_LOD_MEDIUM && isVisible) {
                // 計算運動方向：方位角的變化方向
                const motionDirection = (endAzimuth - startAzimuth) > 0 ? 1 : -1
                const rotationAngle = currentAzimuthRad + (motionDirection * Math.PI / 2)
                groupRef.current.rotation.y = rotationAngle
                satelliteState.current.lastRotation = rotationAngle
            } else {
                groupRef.current.rotation.y = satelliteState.current.lastRotation
            }
        })

        // 根據衛星軌跡狀態決定是否渲染
        // 注意：這裡我們始終渲染組件，但在 useFrame 中控制 visible 屬性

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
                userData={{ satelliteId: String(satellite.norad_id) }}
                name={`satellite-${satellite.norad_id}`}
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
    },
    // 優化的比較函數：只有關鍵屬性變化時才重新渲染
    (prevProps, nextProps) => {
        return (
            prevProps.satellite.norad_id === nextProps.satellite.norad_id &&
            prevProps.index === nextProps.index &&
            prevProps.passTemplate === nextProps.passTemplate &&
            // 避免因為小幅度的位置變化導致重新渲染
            Math.abs(prevProps.satellite.elevation_deg - nextProps.satellite.elevation_deg) < 1 &&
            Math.abs(prevProps.satellite.azimuth_deg - nextProps.satellite.azimuth_deg) < 1
        )
    }
)

export default SimplifiedSatellite
