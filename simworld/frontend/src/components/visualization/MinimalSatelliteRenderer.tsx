import React from 'react'

interface MinimalSatelliteRendererProps {
    satellites: any[]
    enabled: boolean
}

const MinimalSatelliteRenderer: React.FC<MinimalSatelliteRendererProps> = ({
    satellites,
    enabled
}) => {
    if (!enabled || !satellites || satellites.length === 0) {
        return null
    }

    return (
        <group>
            {satellites.slice(0, 3).map((satellite, index) => (
                <group key={satellite.norad_id || index}>
                    {/* 極簡衛星表示 */}
                    <mesh position={[index * 50, 200, index * 30]}>
                        <sphereGeometry args={[5, 8, 8]} />
                        <meshBasicMaterial color={index === 0 ? '#00ff00' : '#ffffff'} />
                    </mesh>
                </group>
            ))}
        </group>
    )
}

export default MinimalSatelliteRenderer