// components/viewers/SceneViewer.tsx
import React from 'react'
import { Device } from '../../types/device'

interface SceneViewerProps {
    scene?: string
    devices?: Device[]
    refreshDeviceData?: () => Promise<void>
    sceneName?: string
    onSceneChange?: (scene: string) => void
    children?: React.ReactNode
}

const SceneViewer: React.FC<SceneViewerProps> = ({
    scene = 'default',
    devices = [],
    refreshDeviceData: _refreshDeviceData,
    sceneName,
    onSceneChange,
    children,
}) => {
    return (
        <div className="scene-viewer">
            <div className="scene-content">{children}</div>
            {onSceneChange && (
                <div className="scene-controls">
                    <select
                        value={scene}
                        onChange={(e) => onSceneChange(e.target.value)}
                    >
                        <option value="default">Default Scene</option>
                        <option value="nycu">NYCU Scene</option>
                        <option value="demo">Demo Scene</option>
                    </select>
                </div>
            )}
            {sceneName && (
                <div className="scene-name">Current Scene: {sceneName}</div>
            )}
            <div className="device-count">Devices: {devices.length}</div>
        </div>
    )
}

export default SceneViewer
