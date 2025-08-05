import React from 'react'
import { Device } from '../../../../types/device'

interface CoreNetworkSyncViewerProps {
    devices: Device[]
    enabled: boolean
}

const CoreNetworkSyncViewer: React.FC<CoreNetworkSyncViewerProps> = ({
    devices,
    enabled,
}) => {
    if (!enabled) {
        return null
    }

    return (
        <div className="core-network-sync-viewer">
            <div className="sync-panel">
                <h3>核心網路同步監控</h3>
                <div className="sync-status">
                    {devices.map((device) => (
                        <div key={device.id} className="sync-item">
                            <span className="device-name">{device.name}</span>
                            <span className="sync-status">
                                {device.active ? '已同步' : '未同步'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default CoreNetworkSyncViewer
