import React from 'react'
import '../panels/PanelCommon.scss'

interface UAVFlightTrackerProps {
    currentScene: string
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
}

const UAVFlightTracker: React.FC<UAVFlightTrackerProps> = ({
    currentScene,
    style,
    isFullscreen,
    onFullscreen,
}) => {
    return (
        <div
            className={`panel uav-tracker ${isFullscreen ? 'fullscreen' : ''}`}
            style={style}
        >
            <div className="panel-header">
                <h3>UAV 飛行追蹤</h3>
                <div className="panel-controls">
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                <div className="placeholder-content">
                    <div className="placeholder-icon">🚁</div>
                    <p>UAV 飛行軌跡追蹤</p>
                    <small>開發中...</small>
                </div>
            </div>
        </div>
    )
}

export default UAVFlightTracker
