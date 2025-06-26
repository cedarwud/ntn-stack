import React from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import SatelliteRenderer from './components/scenes/visualization/SatelliteRenderer'
import { VisibleSatelliteInfo } from './types/satellite'

// Test satellite data
const testSatellites: VisibleSatelliteInfo[] = [
    {
        norad_id: '44713',
        name: 'OneWeb-0001',
        elevation_deg: 45,
        azimuth_deg: 180,
        distance_km: 1200,
        visibility_duration_s: 600,
    },
]

const TestSatelliteModel: React.FC = () => {
    return (
        <div style={{ width: '100vw', height: '100vh' }}>
            <Canvas camera={{ position: [0, 100, 200], fov: 60 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />

                <SatelliteRenderer
                    satellites={testSatellites}
                    enabled={true}
                    simulationMode="demo"
                    showOrbits={false}
                    showLabels={true}
                />

                <OrbitControls />

                {/* Grid helper for reference */}
                <gridHelper args={[1000, 50]} />
                <axesHelper args={[100]} />
            </Canvas>
        </div>
    )
}

export default TestSatelliteModel
