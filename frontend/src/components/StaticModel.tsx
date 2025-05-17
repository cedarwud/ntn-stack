import React, { useMemo } from 'react'
import { useGLTF } from '@react-three/drei'
import * as THREE from 'three'

export interface StaticModelProps {
    url: string
    position: [number, number, number]
    scale: [number, number, number]
    pivotOffset?: [number, number, number]
}

const StaticModel: React.FC<StaticModelProps> = ({
    url,
    position,
    scale,
    pivotOffset = [0, 0, 0],
}) => {
    const { scene } = useGLTF(url) as any
    const clonedScene = useMemo(() => {
        const clone = scene.clone(true)
        clone.traverse((node: THREE.Object3D) => {
            if ((node as THREE.Mesh).isMesh) {
                const mesh = node as THREE.Mesh
                if (mesh.material) {
                    if (Array.isArray(mesh.material)) {
                        mesh.material = mesh.material.map((mat) => mat.clone())
                    } else {
                        mesh.material = mesh.material.clone()
                    }
                }
            }
        })
        return clone
    }, [scene])
    return (
        <group position={position} scale={scale}>
            <primitive
                object={clonedScene}
                position={pivotOffset}
                onUpdate={(self: THREE.Object3D) =>
                    self.traverse((child: THREE.Object3D) => {
                        if ((child as THREE.Mesh).isMesh) {
                            child.castShadow = true
                            child.receiveShadow = true
                        }
                    })
                }
            />
        </group>
    )
}

export default StaticModel
