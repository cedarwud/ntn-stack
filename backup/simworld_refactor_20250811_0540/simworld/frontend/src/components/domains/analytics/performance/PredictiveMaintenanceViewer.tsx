import React from 'react'
import { Device } from '../../../../types/device'

interface PredictiveMaintenanceViewerProps {
    devices: Device[]
    enabled: boolean
}

const PredictiveMaintenanceViewer: React.FC<
    PredictiveMaintenanceViewerProps
> = ({ devices, enabled }) => {
    if (!enabled) {
        return null
    }

    return (
        <div className="predictive-maintenance-viewer">
            <div className="maintenance-panel">
                <h3>預測性維護監控</h3>
                <div className="device-health-status">
                    {devices.map((device) => (
                        <div key={device.id} className="device-health-item">
                            <span className="device-name">{device.name}</span>
                            <span className="health-status">
                                {device.active ? '正常' : '需要維護'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default PredictiveMaintenanceViewer
