import { useRef, useEffect, useState, useMemo, useCallback } from 'react'
import { useGLTF } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js'
import { ApiRoutes } from '../../../../config/apiRoutes'

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

interface FlightModeParams {
    cruise: FlightParams
    hover: FlightParams
    agile: FlightParams
    explore: FlightParams
}

interface FlightParams {
    pathCurvature: number
    speedFactor: number
    turbulenceEffect: number
    heightVariation: number
    smoothingFactor: number
}

type FlightMode = 'cruise' | 'hover' | 'agile' | 'explore'

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
    const lightRef = useRef<THREE.PointLight>(null)

    // 使用標準加載方式
    const { scene, animations } = useGLTF(UAV_MODEL_URL) as {
        scene: THREE.Group
        animations: THREE.AnimationClip[]
    }

    // 用 useMemo 確保每個 UAV 都有獨立骨架
    const clonedScene = useMemo(() => SkeletonUtils.clone(scene), [scene])

    const [mixer, setMixer] = useState<THREE.AnimationMixer | null>(null)
    const [actions, setActions] = useState<{
        [key: string]: THREE.AnimationAction
    }>({})

    const lastUpdateTimeRef = useRef<number>(0)
    const throttleInterval = 100

    // 🔥 重写的简化自动飞行系统
    const FIXED_BASE_POSITION = useRef<THREE.Vector3>(new THREE.Vector3(...position))
    const [currentPosition, setCurrentPosition] = useState<THREE.Vector3>(
        new THREE.Vector3(...position)
    )
    
    // 简化的飞行状态
    const [flyingTime, setFlyingTime] = useState(0)
    const [flightPhase, setFlightPhase] = useState<'orbit' | 'return'>('orbit')

    // 移除复杂的飞行模式状态，简化为基本飞行控制

    // 移除复杂的飞行参数系统

    // 移除复杂的飞行模式切换逻辑

    // 移除复杂的路径生成函数

    useEffect(() => {
        // 設置警告攔截器以忽略動畫綁定錯誤
        const originalWarning = console.warn
        console.warn = function (...args: unknown[]) {
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

        // 移除复杂路径生成

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
                (material as { color: THREE.Color }).color instanceof
                    THREE.Color
            ) {
                stdMaterial.color.copy(
                    (material as { color: THREE.Color }).color
                )
            }
            if ('map' in material) {
                stdMaterial.map = (material as { map: THREE.Texture }).map
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

    // 🚁 简化的自动飞行逻辑
    useFrame((state, delta) => {
        if (mixer) mixer.update(delta)
        
        if (!group.current || !lightRef.current) return
        
        // 设置光照
        if (lightRef.current) {
            lightRef.current.position.set(0, 5, 0)
            lightRef.current.intensity = 2000
        }
        
        // 如果不是自动模式，直接设置位置并返回
        if (!auto) {
            group.current.position.copy(currentPosition)
            return
        }
        
        // 🔥 简单的圆形飞行模式
        setFlyingTime(prev => prev + delta)
        
        const basePos = FIXED_BASE_POSITION.current
        const radius = 50 // 飞行半径
        const speed = 0.5 // 飞行速度
        const heightVariation = 10 // 高度变化
        
        // 计算圆形轨道位置
        const angle = flyingTime * speed
        const x = basePos.x + Math.cos(angle) * radius
        const z = basePos.z + Math.sin(angle) * radius
        const y = basePos.y + Math.sin(flyingTime * 0.3) * heightVariation
        
        const newPosition = new THREE.Vector3(x, y, z)
        
        // 更新位置
        group.current.position.copy(newPosition)
        setCurrentPosition(newPosition)
        
        // 节流的位置更新回调
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
    }, [manualDirection, auto, onManualMoveDone, onPositionUpdate])
    useEffect(() => {
        // console.log('UAV 模型載入成功')
        // console.log('光源已添加到組件中')
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
