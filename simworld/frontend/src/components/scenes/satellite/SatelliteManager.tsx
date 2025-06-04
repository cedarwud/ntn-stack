import { useMemo } from 'react'
import { useGLTF } from '@react-three/drei'
import { useThree } from '@react-three/fiber'
import * as THREE from 'three'
import { VisibleSatelliteInfo } from '../../../types/satellite'
import SimplifiedSatellite from './SimplifiedSatellite'
import { satellitePassTemplates } from '../../../utils/satellite/satellitePassTemplates'
import {
    MAX_VISIBLE_SATELLITES,
    SAT_MODEL_URL,
} from '../../../utils/satellite/satelliteConstants'

// 效能優化常數
const DISTANCE_THRESHOLD_NEAR = 1200 // 近距離閾值
const DISTANCE_THRESHOLD_FAR = 2000 // 遠距離閾值

interface SatelliteManagerProps {
    satellites: VisibleSatelliteInfo[]
}

// 預加載衛星模型
useGLTF.preload(SAT_MODEL_URL)

const SatelliteManager: React.FC<SatelliteManagerProps> = ({
    satellites = [],
}) => {
    const { camera } = useThree()

    // 根據距離將衛星分組，仍保留更新頻率優化
    const satelliteGroups = useMemo(() => {
        // 限制衛星數量以減輕渲染負擔
        const visibleSatellites = satellites.slice(0, MAX_VISIBLE_SATELLITES)

        // 根據距離分組
        const near: VisibleSatelliteInfo[] = []
        const medium: VisibleSatelliteInfo[] = []
        const far: VisibleSatelliteInfo[] = []

        // 計算攝影機位置（場景中心為原點）
        const cameraPosition = new THREE.Vector3()
        camera.getWorldPosition(cameraPosition)

        // 分組策略
        visibleSatellites.forEach((satellite) => {
            // 簡單估算距離（實際使用中可能需要更複雜的計算）
            const distance = satellite.distance_km || 1000

            if (distance < DISTANCE_THRESHOLD_NEAR) {
                near.push(satellite)
            } else if (distance < DISTANCE_THRESHOLD_FAR) {
                medium.push(satellite)
            } else {
                far.push(satellite)
            }
        })

        return {
            near,
            medium,
            far,
        }
    }, [satellites, camera])

    // 渲染衛星 - 保留分組但所有衛星都使用完整模型渲染
    return (
        <>
            {/* 近距離衛星 - 完整詳細渲染 */}
            {satelliteGroups.near.map((satellite, index) => {
                const passTemplate =
                    satellitePassTemplates[
                        index % satellitePassTemplates.length
                    ]
                return (
                    <SimplifiedSatellite
                        key={`satellite-near-${satellite.norad_id}`}
                        satellite={satellite}
                        index={index}
                        passTemplate={passTemplate}
                    />
                )
            })}

            {/* 中距離衛星 - 標準渲染 */}
            {satelliteGroups.medium.map((satellite, index) => {
                const passTemplateIndex =
                    (index + satelliteGroups.near.length) %
                    satellitePassTemplates.length
                const passTemplate = satellitePassTemplates[passTemplateIndex]
                return (
                    <SimplifiedSatellite
                        key={`satellite-medium-${satellite.norad_id}`}
                        satellite={satellite}
                        index={index + satelliteGroups.near.length}
                        passTemplate={passTemplate}
                    />
                )
            })}

            {/* 遠距離衛星 - 標準渲染（不使用實例化） */}
            {satelliteGroups.far.map((satellite, index) => {
                const passTemplateIndex =
                    (index +
                        satelliteGroups.near.length +
                        satelliteGroups.medium.length) %
                    satellitePassTemplates.length
                const passTemplate = satellitePassTemplates[passTemplateIndex]
                return (
                    <SimplifiedSatellite
                        key={`satellite-far-${satellite.norad_id}`}
                        satellite={satellite}
                        index={
                            index +
                            satelliteGroups.near.length +
                            satelliteGroups.medium.length
                        }
                        passTemplate={passTemplate}
                    />
                )
            })}
        </>
    )
}

export default SatelliteManager
