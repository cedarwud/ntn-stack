// components/views/SceneView.tsx
import React from 'react'
import { Device } from '../../types/device'

interface SceneViewProps {
    title?: string
    devices?: Device[]
    auto?: boolean
    manualDirection?: string | null
    children?: React.ReactNode
    className?: string
    [key: string]: any // 允許其他任意 props
}

const SceneView: React.FC<SceneViewProps> = ({
    title,
    devices = [],
    auto,
    manualDirection,
    children,
    className = '',
    ...otherProps
}) => {
    return (
        <div className={`scene-view ${className}`}>
            {title && (
                <div className="scene-view-header">
                    <h2>{title}</h2>
                </div>
            )}
            <div className="scene-view-content">{children}</div>
            <div className="scene-view-status">
                <div>Devices: {devices.length}</div>
                {auto !== undefined && (
                    <div>Auto Mode: {auto ? 'On' : 'Off'}</div>
                )}
                {manualDirection && <div>Direction: {manualDirection}</div>}
            </div>
        </div>
    )
}

export default SceneView
