import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { ContactShadows, OrbitControls } from '@react-three/drei'
import * as THREE from 'three'
import { Device } from '../App'
import Starfield from './Starfield'
import MainScene from './MainScene'

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
}

export default function SceneView({
    devices = [],
    auto,
    manualDirection,
    onManualControl,
    onUAVPositionUpdate,
    uavAnimation,
    selectedReceiverIds = [],
}: SceneViewProps) {
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
            {/* 3D Canvas內容照舊，會蓋在星空上 */}
            <Canvas
                shadows
                camera={{ position: [40, 80, 120], near: 0.1, far: 1e4 }}
                gl={{
                    toneMapping: THREE.ACESFilmicToneMapping,
                    toneMappingExposure: 1.2,
                    alpha: true,
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
