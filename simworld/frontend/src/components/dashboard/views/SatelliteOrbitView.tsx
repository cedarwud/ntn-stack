import React from 'react'
import '../panels/PanelCommon.scss'

interface SatelliteOrbitViewProps {
    currentScene: string
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
}

const SatelliteOrbitView: React.FC<SatelliteOrbitViewProps> = ({
    currentScene,
    style,
    isFullscreen,
    onFullscreen,
}) => {
    return (
        <div
            className={`panel satellite-orbit ${
                isFullscreen ? 'fullscreen' : ''
            }`}
            style={style}
        >
            <div className="panel-header">
                <h3>衛星軌道</h3>
                <div className="panel-controls">
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                <div className="placeholder-content">
                    <div className="placeholder-icon">🛰️</div>
                    <p>衛星軌道可視化</p>
                    <small>開發中...</small>
                </div>
            </div>
        </div>
    )
}

export default SatelliteOrbitView
