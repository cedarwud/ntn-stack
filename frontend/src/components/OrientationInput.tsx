import React from 'react'

export interface OrientationInputProps {
    value: { x: string; y: string; z: string }
    onChange: (axis: 'x' | 'y' | 'z', value: string) => void
}

const OrientationInput: React.FC<OrientationInputProps> = ({
    value,
    onChange,
}) => {
    return (
        <>
            <input
                type="text"
                value={value.x}
                onChange={(e) => onChange('x', e.target.value)}
                placeholder="X"
            />
            <input
                type="text"
                value={value.y}
                onChange={(e) => onChange('y', e.target.value)}
                placeholder="Y"
            />
            <input
                type="text"
                value={value.z}
                onChange={(e) => onChange('z', e.target.value)}
                placeholder="Z"
            />
        </>
    )
}

export function parseOrientationInput(value: string): number {
    if (value.includes('/')) {
        const parts = value.split('/')
        if (parts.length === 2) {
            const numerator = parseFloat(parts[0])
            const denominator = parseFloat(parts[1])
            if (!isNaN(numerator) && !isNaN(denominator) && denominator !== 0) {
                return (numerator / denominator) * Math.PI
            }
        }
    }
    const numValue = parseFloat(value)
    if (!isNaN(numValue)) {
        return numValue
    }
    return 0
}

export default OrientationInput
