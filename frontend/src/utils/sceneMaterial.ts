import * as THREE from 'three'
import { TextureLoader, RepeatWrapping, SRGBColorSpace } from 'three'

export function applySatelliteTextureToGroundMesh(root: THREE.Object3D, textureUrl: string) {
    let maxArea = 0
    let groundMesh: THREE.Mesh | null = null
    const loader = new TextureLoader()
    const satelliteTexture = loader.load(textureUrl)
    satelliteTexture.wrapS = RepeatWrapping
    satelliteTexture.wrapT = RepeatWrapping
    satelliteTexture.colorSpace = SRGBColorSpace
    satelliteTexture.repeat.set(1, 1)
    satelliteTexture.anisotropy = 16
    root.traverse((o: THREE.Object3D) => {
        if ((o as THREE.Mesh).isMesh) {
            const m = o as THREE.Mesh
            m.castShadow = true
            m.receiveShadow = true
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
                        groundMesh.material = new THREE.MeshStandardMaterial({
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
} 