import { useRef, useEffect, useState, useMemo } from 'react'
import { useGLTF } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
// @ts-ignore
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js'
import { ApiRoutes } from '../../config/apiRoutes'

const UAV_MODEL_URL = ApiRoutes.simulations.getModel('uav')

// 請調整此值以補償懸停動畫的 Y 軸位移
const HOVER_ANIMATION_Y_OFFSET = -1.28 // 範例值，如果向上跳了 5 個單位，則設為 -5

export type UAVManualDirection =
    | 'up'
    | 'down'
    | 'left'
    | 'right'
    | 'ascend'
    | 'descend'
    | 'left-up'
    | 'right-up'
    | 'left-down'
    | 'right-down'
    | 'rotate-left'
    | 'rotate-right'
    | null

export interface UAVFlightProps {
    position: [number, number, number]
    scale: [number, number, number]
    auto: boolean
    manualDirection?: UAVManualDirection
    onManualMoveDone?: () => void
    onPositionUpdate?: (position: [number, number, number]) => void
    uavAnimation: boolean
}

export default function UAVFlight({
    position,
    scale,
    auto,
    manualDirection,
    onManualMoveDone,
    onPositionUpdate,
    uavAnimation,
}: UAVFlightProps) {
    const group = useRef<THREE.Group>(null)
    const cloneRef = useRef<THREE.Object3D>(null)
    const lightRef = useRef<THREE.PointLight>(null)

    // 使用標準加載方式
    const { scene, animations } = useGLTF(UAV_MODEL_URL) as any

    // 用 useMemo 確保每個 UAV 都有獨立骨架
    const clonedScene = useMemo(() => SkeletonUtils.clone(scene), [scene])

    const [mixer, setMixer] = useState<THREE.AnimationMixer | null>(null)
    const [actions, setActions] = useState<{
        [key: string]: THREE.AnimationAction
    }>({})

    const lastUpdateTimeRef = useRef<number>(0)
    const throttleInterval = 100

    const [currentPosition, setCurrentPosition] = useState<THREE.Vector3>(
        new THREE.Vector3(...position)
    )
    const initialPosition = useRef<THREE.Vector3>(
        new THREE.Vector3(...position)
    )
    useEffect(() => {
        initialPosition.current.set(...position)
    }, [position])

    const [targetPosition, setTargetPosition] = useState<THREE.Vector3>(
        new THREE.Vector3(...position)
    )
    const moveSpeed = useRef(0.5)
    const lastDirection = useRef(new THREE.Vector3(0, 0, 0))
    const turbulence = useRef({ x: 0, y: 0, z: 0 })
    const velocity = useRef(new THREE.Vector3(0, 0, 0))
    const acceleration = useRef(0.5)
    const deceleration = useRef(0.3)
    const maxSpeed = useRef(1.5)

    const flightModes = ['cruise', 'hover', 'agile', 'explore'] as const
    type FlightMode = (typeof flightModes)[number]
    const [flightMode, setFlightMode] = useState<FlightMode>('cruise')
    const flightModeTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
    const flightModeParams = useRef({
        cruise: {
            pathCurvature: 0.2,
            speedFactor: 1.0,
            turbulenceEffect: 0.2,
            heightVariation: 5,
            smoothingFactor: 0.85,
        },
        hover: {
            pathCurvature: 0.4,
            speedFactor: 0.6,
            turbulenceEffect: 0.4,
            heightVariation: 2,
            smoothingFactor: 0.7,
        },
        agile: {
            pathCurvature: 0.5,
            speedFactor: 1.5,
            turbulenceEffect: 0.1,
            heightVariation: 15,
            smoothingFactor: 0.6,
        },
        explore: {
            pathCurvature: 0.3,
            speedFactor: 0.8,
            turbulenceEffect: 0.3,
            heightVariation: 10,
            smoothingFactor: 0.8,
        },
    })
    const [waypoints, setWaypoints] = useState<THREE.Vector3[]>([])
    const currentWaypoint = useRef(0)
    const pathCurvature = useRef(0.3 + Math.random() * 0.4)

    useEffect(() => {
        const updateTurbulence = () => {
            const strength =
                flightModeParams.current[flightMode].turbulenceEffect
            turbulence.current = {
                x: (Math.random() - 0.5) * 0.4 * strength,
                y: (Math.random() - 0.5) * 0.2 * strength,
                z: (Math.random() - 0.5) * 0.4 * strength,
            }
        }
        updateTurbulence()
        const interval = setInterval(updateTurbulence, 2000)
        const switchFlightMode = () => {
            const nextMode =
                flightModes[Math.floor(Math.random() * flightModes.length)]
            setFlightMode(nextMode)
            const modeParams = flightModeParams.current[nextMode]
            pathCurvature.current = modeParams.pathCurvature
            maxSpeed.current = 1.0 * modeParams.speedFactor
            acceleration.current = 0.5 * modeParams.speedFactor
            const duration = 10000 + Math.random() * 15000
            if (flightModeTimer.current) clearTimeout(flightModeTimer.current)
            flightModeTimer.current = setTimeout(switchFlightMode, duration)
        }
        flightModeTimer.current = setTimeout(switchFlightMode, 10000)
        return () => {
            clearInterval(interval)
            if (flightModeTimer.current) clearTimeout(flightModeTimer.current)
        }
    }, [flightMode])

    const generateBezierPath = (
        start: THREE.Vector3,
        end: THREE.Vector3,
        points: number = 10
    ) => {
        const path: THREE.Vector3[] = []
        const direction = new THREE.Vector3().subVectors(end, start).normalize()
        const up = new THREE.Vector3(0, 1, 0)
        const perpendicular = new THREE.Vector3()
            .crossVectors(direction, up)
            .normalize()
        if (perpendicular.lengthSq() < 0.001) {
            perpendicular
                .crossVectors(direction, new THREE.Vector3(1, 0, 0))
                .normalize()
        }
        const distance = start.distanceTo(end)
        const curveOffset = distance * pathCurvature.current
        const offset1 = perpendicular
            .clone()
            .multiplyScalar(curveOffset * (Math.random() > 0.5 ? 1 : -1))
        const offset2 = perpendicular
            .clone()
            .multiplyScalar(curveOffset * (Math.random() > 0.5 ? 1 : -1))
        const heightVariation =
            flightModeParams.current[flightMode].heightVariation
        const control1 = start
            .clone()
            .add(direction.clone().multiplyScalar(distance / 3))
            .add(offset1)
            .add(
                new THREE.Vector3(0, (Math.random() - 0.3) * heightVariation, 0)
            )
        const control2 = start
            .clone()
            .add(direction.clone().multiplyScalar((distance * 2) / 3))
            .add(offset2)
            .add(
                new THREE.Vector3(0, (Math.random() - 0.3) * heightVariation, 0)
            )
        for (let i = 0; i < points; i++) {
            const t = i / (points - 1)
            const b0 = Math.pow(1 - t, 3)
            const b1 = 3 * Math.pow(1 - t, 2) * t
            const b2 = 3 * (1 - t) * Math.pow(t, 2)
            const b3 = Math.pow(t, 3)
            const point = new THREE.Vector3(
                b0 * start.x + b1 * control1.x + b2 * control2.x + b3 * end.x,
                b0 * start.y + b1 * control1.y + b2 * control2.y + b3 * end.y,
                b0 * start.z + b1 * control1.z + b2 * control2.z + b3 * end.z
            )
            if (i > 0 && i < points - 1) {
                const smallNoise = new THREE.Vector3(
                    (Math.random() - 0.5) * 2,
                    (Math.random() - 0.5) * 1,
                    (Math.random() - 0.5) * 2
                )
                point.add(smallNoise)
            }
            path.push(point)
        }
        return path
    }
    const generateNewTarget = () => {
        const modeParams = flightModeParams.current[flightMode]
        let distance
        let heightRange
        switch (flightMode) {
            case 'hover':
                distance = 80 + Math.random() * 120
                heightRange = [40, 80]
                break
            case 'agile':
                distance = 100 + Math.random() * 150
                heightRange = [30, 120]
                break
            case 'explore':
                distance = 150 + Math.random() * 200
                heightRange = [60, 150]
                break
            case 'cruise':
            default:
                distance = 120 + Math.random() * 150
                heightRange = [50, 100]
        }
        const randomDirection = new THREE.Vector3(
            Math.random() * 2 - 1,
            0,
            Math.random() * 2 - 1
        ).normalize()
        const newX = initialPosition.current.x + randomDirection.x * distance
        const newZ = initialPosition.current.z + randomDirection.z * distance
        const newY =
            heightRange[0] + Math.random() * (heightRange[1] - heightRange[0])
        return new THREE.Vector3(newX, newY, newZ)
    }
    const hasReachedTarget = (
        current: THREE.Vector3,
        target: THREE.Vector3,
        threshold: number = 5
    ) => {
        return current.distanceTo(target) < threshold
    }
    const generatePath = () => {
        const start = currentPosition
        const end = generateNewTarget()
        const distance = start.distanceTo(end)
        const points = Math.max(8, Math.min(20, Math.floor(distance / 15)))
        const newWaypoints = generateBezierPath(start, end, points)
        setWaypoints(newWaypoints)
        currentWaypoint.current = 0
        setTargetPosition(end)
        return newWaypoints
    }
    useEffect(() => {
        // 設置警告攔截器以忽略動畫綁定錯誤
        const originalWarning = console.warn
        console.warn = function (...args: any[]) {
            const message = args[0]
            if (
                message &&
                typeof message === 'string' &&
                message.includes(
                    'THREE.PropertyBinding: No target node found for track:'
                )
            ) {
                // 忽略找不到節點的警告
                return
            }
            if (
                message &&
                typeof message === 'string' &&
                message.includes(
                    'Unknown extension "KHR_materials_pbrSpecularGlossiness"'
                )
            ) {
                // 忽略未知擴展警告
                return
            }
            originalWarning.apply(console, args)
        }

        // 安全地播放動畫，忽略錯誤
        // try {
        //     // 檢查是否有可用的動畫
        //     if (actions && Object.keys(actions).length > 0) {
        //         const action = actions[Object.keys(actions)[0]]
        //         if (action) {
        //             action.setLoop(THREE.LoopRepeat, Infinity)
        //             action.play()
        //             action.paused = !uavAnimation
        //         }
        //     } else {
        //         console.log('沒有可用的動畫')
        //     }
        // } catch (error) {
        //     console.error('動畫播放錯誤:', error)
        // }

        generatePath()

        if (clonedScene) {
            clonedScene.traverse((child: THREE.Object3D) => {
                if ((child as THREE.Mesh).isMesh) {
                    child.castShadow = true
                    child.receiveShadow = true

                    // 檢查材質，如果必要，替換為標準材質
                    const mesh = child as THREE.Mesh
                    if (Array.isArray(mesh.material)) {
                        mesh.material = mesh.material.map((mat) =>
                            ensureStandardMaterial(mat)
                        )
                    } else {
                        mesh.material = ensureStandardMaterial(mesh.material)
                    }
                }
            })
        }

        // 清理函數：恢復原始警告功能
        return () => {
            console.warn = originalWarning
        }
    }, [actions, clonedScene, uavAnimation])

    // 確保使用標準材質
    const ensureStandardMaterial = (material: THREE.Material) => {
        if (
            !(material instanceof THREE.MeshStandardMaterial) &&
            !(material instanceof THREE.MeshPhysicalMaterial)
        ) {
            const stdMaterial = new THREE.MeshStandardMaterial()

            // 複製基本屬性
            if (
                'color' in material &&
                (material as any).color instanceof THREE.Color
            ) {
                stdMaterial.color.copy((material as any).color)
            }
            if ('map' in material) {
                stdMaterial.map = (material as any).map
            }

            return stdMaterial
        }
        return material
    }

    // 尋找動畫 root（骨架/SkinnedMesh/Armature）
    function findAnimationRoot(obj: THREE.Object3D): THREE.Object3D {
        let found: THREE.Object3D | null = null
        obj.traverse((child) => {
            if (
                child.type === 'Bone' ||
                child.type === 'SkinnedMesh' ||
                child.name.toLowerCase().includes('armature')
            ) {
                if (!found) found = child
            }
        })
        return found || obj
    }

    useEffect(() => {
        if (clonedScene && animations && animations.length > 0) {
            // // 診斷 log (暫時註解掉以減少控制台輸出)
            // console.log('=== AnimationClip tracks ===')
            // animations.forEach((clip: THREE.AnimationClip) => {
            //     console.log(
            //         'clip:',
            //         clip.name,
            //         clip.tracks.map((t) => t.name)
            //     )
            // })
            // console.log('=== clonedScene children ===')
            // clonedScene.traverse((obj: THREE.Object3D) => {
            //     console.log('obj:', obj.name, obj.type)
            // })

            // 自動尋找動畫 root
            const animationRoot = findAnimationRoot(clonedScene)
            // console.log(
            //     'AnimationMixer root:',
            //     animationRoot.name,
            //     animationRoot.type
            // )
            const newMixer = new THREE.AnimationMixer(animationRoot)
            const newActions: { [key: string]: THREE.AnimationAction } = {}
            animations.forEach((clip: THREE.AnimationClip) => {
                newActions[clip.name] = newMixer.clipAction(clip)
            })
            setMixer(newMixer)
            setActions(newActions)
        }
    }, [clonedScene, animations])

    // 控制動畫播放/暫停
    useEffect(() => {
        if (mixer && animations && animations.length > 0 && clonedScene) {
            // 只建立 hover 動畫
            const hoverClip = animations.find(
                (clip: THREE.AnimationClip) => clip.name === 'hover'
            )
            let hoverAction: THREE.AnimationAction | null = null
            if (hoverClip) {
                hoverAction = mixer.clipAction(hoverClip)
                hoverAction.reset()
                hoverAction.setLoop(THREE.LoopRepeat, Infinity)

                if (uavAnimation) {
                    hoverAction.enabled = true
                    hoverAction.play()
                    hoverAction.paused = false
                    hoverAction.setEffectiveWeight(1)
                    clonedScene.position.y = HOVER_ANIMATION_Y_OFFSET
                } else {
                    hoverAction.stop()
                    hoverAction.paused = true
                    hoverAction.enabled = false
                    hoverAction.reset()
                    clonedScene.position.y = 0 // 恢復原始相對 Y 位置
                }
            }
            // 停用所有非 hover 動畫
            animations.forEach((clip: THREE.AnimationClip) => {
                if (clip.name !== 'hover') {
                    const action = mixer.existingAction(clip)
                    if (action) {
                        action.stop()
                        action.enabled = false
                        action.setEffectiveWeight(0)
                        action.reset()
                    }
                }
            })
        }
    }, [mixer, animations, uavAnimation, clonedScene])

    // 驅動 mixer
    useFrame((state, delta) => {
        if (mixer) mixer.update(delta)
        if (group.current) {
            // 不要在這裡直接修改 group.current.position，currentPosition 已經包含了Z軸位移
            // group.current.position.copy(currentPosition)
            // 如果 currentPosition 已經包含了動畫的Z軸位移，那麼上面的 HOVER_ANIMATION_Z_OFFSET 應該加到 currentPosition
            // 但目前假設動畫位移是 clonsedScene 內部的，由 HOVER_ANIMATION_Z_OFFSET 補償
            group.current.position.set(
                currentPosition.x,
                currentPosition.y,
                currentPosition.z
            )
        }
        if (lightRef.current) {
            lightRef.current.position.set(0, 5, 0)
            lightRef.current.intensity = 2000
        }
        if (!auto) return
        if (!group.current || !lightRef.current || waypoints.length === 0)
            return
        const current = currentPosition.clone()
        const modeParams = flightModeParams.current[flightMode]
        const currentTargetIndex = currentWaypoint.current
        if (currentTargetIndex >= waypoints.length - 1) {
            const newPath = generatePath()
            if (newPath.length > 0) {
                velocity.current.set(0, 0, 0)
                return
            }
        }
        const currentTarget = waypoints[currentTargetIndex]
        if (hasReachedTarget(current, currentTarget, 10)) {
            currentWaypoint.current = Math.min(
                currentWaypoint.current + 1,
                waypoints.length - 1
            )
            return
        }
        const rawDirection = new THREE.Vector3()
            .subVectors(currentTarget, current)
            .normalize()
        const smoothingFactor = modeParams.smoothingFactor
        const smoothDirection = new THREE.Vector3(
            smoothingFactor * rawDirection.x +
                (1 - smoothingFactor) * lastDirection.current.x,
            smoothingFactor * rawDirection.y +
                (1 - smoothingFactor) * lastDirection.current.y,
            smoothingFactor * rawDirection.z +
                (1 - smoothingFactor) * lastDirection.current.z
        ).normalize()
        lastDirection.current = smoothDirection.clone()
        const turbulenceEffect = modeParams.turbulenceEffect
        const movementWithTurbulence = new THREE.Vector3(
            smoothDirection.x + turbulence.current.x * turbulenceEffect,
            smoothDirection.y + turbulence.current.y * turbulenceEffect,
            smoothDirection.z + turbulence.current.z * turbulenceEffect
        ).normalize()
        const distanceToTarget = current.distanceTo(currentTarget)
        const targetSpeed =
            Math.min(maxSpeed.current, distanceToTarget / 10) *
            modeParams.speedFactor
        const currentSpeed = velocity.current.length()
        let accelerationFactor =
            Math.min(1, distanceToTarget / 50) *
            (currentSpeed < targetSpeed
                ? acceleration.current
                : -deceleration.current)
        const speedChange = accelerationFactor * delta * 10
        velocity.current.lerp(
            movementWithTurbulence.clone().multiplyScalar(targetSpeed),
            delta * 2
        )
        if (velocity.current.length() > 0) {
            if (currentSpeed + speedChange > 0) {
                velocity.current
                    .normalize()
                    .multiplyScalar(currentSpeed + speedChange)
            } else {
                velocity.current.set(0, 0, 0)
            }
        }
        if (
            velocity.current.length() >
            maxSpeed.current * modeParams.speedFactor
        ) {
            velocity.current
                .normalize()
                .multiplyScalar(maxSpeed.current * modeParams.speedFactor)
        }
        const newPosition = current
            .clone()
            .add(velocity.current.clone().multiplyScalar(delta * 30))
        group.current.position.set(newPosition.x, newPosition.y, newPosition.z)
        setCurrentPosition(newPosition)
        const now = performance.now()
        if (now - lastUpdateTimeRef.current > throttleInterval) {
            onPositionUpdate?.([newPosition.x, newPosition.y, newPosition.z])
            lastUpdateTimeRef.current = now
        }
    })
    useEffect(() => {
        if (!auto && manualDirection) {
            let finalPosition: [number, number, number] | null = null
            setCurrentPosition((prev) => {
                const next = prev.clone()
                switch (manualDirection) {
                    case 'up':
                        next.y += 1
                        break
                    case 'down':
                        next.y -= 1
                        break
                    case 'left':
                        next.x -= 1
                        break
                    case 'right':
                        next.x += 1
                        break
                    case 'ascend':
                        next.z += 1
                        break
                    case 'descend':
                        next.z -= 1
                        break
                    case 'left-up':
                        next.x -= 1
                        next.z -= 1
                        break
                    case 'right-up':
                        next.x += 1
                        next.z -= 1
                        break
                    case 'left-down':
                        next.x -= 1
                        next.z += 1
                        break
                    case 'right-down':
                        next.x += 1
                        next.z += 1
                        break
                    case 'rotate-left':
                        if (group.current) {
                            group.current.rotation.y += 0.087
                        }
                        break
                    case 'rotate-right':
                        if (group.current) {
                            group.current.rotation.y -= 0.087
                        }
                        break
                }
                finalPosition = [next.x, next.y, next.z]
                return next
            })
            if (onManualMoveDone) onManualMoveDone()
            if (finalPosition) {
                const now = performance.now()
                if (now - lastUpdateTimeRef.current > throttleInterval) {
                    onPositionUpdate?.(finalPosition)
                    lastUpdateTimeRef.current = now
                }
            }
        }
    }, [
        manualDirection,
        auto,
        onManualMoveDone,
        onPositionUpdate,
        throttleInterval,
    ])
    useEffect(() => {
        console.log('UAV 模型載入成功:', clonedScene)
        console.log('光源已添加到組件中')
    }, [clonedScene])
    return (
        <group ref={group} position={position} scale={scale}>
            <primitive
                object={clonedScene}
                onUpdate={(self: THREE.Object3D) => {
                    // 只做材質處理，不要 setState
                    self.traverse((child: THREE.Object3D) => {
                        if ((child as THREE.Mesh).isMesh) {
                            const mesh = child as THREE.Mesh
                            if (Array.isArray(mesh.material)) {
                                mesh.material = mesh.material.map((mat) =>
                                    ensureStandardMaterial(mat)
                                )
                            } else {
                                mesh.material = ensureStandardMaterial(
                                    mesh.material
                                )
                            }
                            mesh.castShadow = true
                            mesh.receiveShadow = true
                        }
                    })
                }}
            />
            <pointLight
                ref={lightRef}
                position={[0, 5, 0]}
                intensity={2000}
                distance={100}
                decay={2}
                color={0xffffff}
                castShadow
                shadow-mapSize-width={512}
                shadow-mapSize-height={512}
                shadow-bias={-0.001}
            />
        </group>
    )
}
