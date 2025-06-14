import React from 'react'
import { SATELLITE_CONFIG } from '../../config/satellite.config'

interface SatelliteControlPanelProps {
    satelliteEnabled: boolean
    satelliteAnimationEnabled: boolean
    satelliteSpeedMultiplier: number
    showOrbitTracks: boolean
    onSatelliteEnabledChange: (enabled: boolean) => void
    onSatelliteAnimationEnabledChange: (enabled: boolean) => void
    onSatelliteSpeedChange: (speed: number) => void
    onShowOrbitTracksChange: (show: boolean) => void
}

const SatelliteControlPanel: React.FC<SatelliteControlPanelProps> = ({
    satelliteEnabled,
    satelliteAnimationEnabled,
    satelliteSpeedMultiplier,
    showOrbitTracks,
    onSatelliteEnabledChange,
    onSatelliteAnimationEnabledChange,
    onSatelliteSpeedChange,
    onShowOrbitTracksChange,
}) => {
    // 預設速度選項
    const speedOptions = [
        { value: 1, label: '1x (真實速度)' },
        { value: 10, label: '10x' },
        { value: 30, label: '30x' },
        { value: 60, label: '60x (推薦)' },
        { value: 120, label: '120x' },
        { value: 300, label: '300x (快速)' },
        { value: 600, label: '600x (極快)' }
    ]

    return (
        <div className="satellite-control-panel">
            <div className="control-section">
                <h3 className="section-title">
                    <span className="section-icon">🛰️</span>
                    衛星控制面板
                </h3>
                
                {/* 基本開關 */}
                <div className="control-group">
                    <div className="control-item">
                        <label className="control-label">
                            <input
                                type="checkbox"
                                checked={satelliteEnabled}
                                onChange={(e) => onSatelliteEnabledChange(e.target.checked)}
                                className="control-checkbox"
                            />
                            <span className="control-text">顯示衛星星座</span>
                        </label>
                    </div>
                    
                    <div className="control-item">
                        <label className="control-label">
                            <input
                                type="checkbox"
                                checked={satelliteAnimationEnabled}
                                onChange={(e) => onSatelliteAnimationEnabledChange(e.target.checked)}
                                disabled={!satelliteEnabled}
                                className="control-checkbox"
                            />
                            <span className="control-text">啟用軌跡動畫</span>
                        </label>
                    </div>
                    
                    <div className="control-item">
                        <label className="control-label">
                            <input
                                type="checkbox"
                                checked={showOrbitTracks}
                                onChange={(e) => onShowOrbitTracksChange(e.target.checked)}
                                disabled={!satelliteEnabled || !satelliteAnimationEnabled}
                                className="control-checkbox"
                            />
                            <span className="control-text">顯示軌跡線</span>
                        </label>
                    </div>
                </div>

                {/* 速度控制 */}
                {satelliteAnimationEnabled && (
                    <div className="control-group">
                        <div className="control-item">
                            <label className="control-label-full">
                                <span className="control-text">動畫速度倍數</span>
                                <select
                                    value={satelliteSpeedMultiplier}
                                    onChange={(e) => onSatelliteSpeedChange(Number(e.target.value))}
                                    className="control-select"
                                    disabled={!satelliteAnimationEnabled}
                                >
                                    {speedOptions.map(option => (
                                        <option key={option.value} value={option.value}>
                                            {option.label}
                                        </option>
                                    ))}
                                </select>
                            </label>
                        </div>

                        {/* 自訂速度滑塊 */}
                        <div className="control-item">
                            <label className="control-label-full">
                                <span className="control-text">
                                    自訂速度: {satelliteSpeedMultiplier}x
                                </span>
                                <input
                                    type="range"
                                    min="1"
                                    max="600"
                                    step="1"
                                    value={satelliteSpeedMultiplier}
                                    onChange={(e) => onSatelliteSpeedChange(Number(e.target.value))}
                                    className="control-slider"
                                    disabled={!satelliteAnimationEnabled}
                                />
                            </label>
                        </div>
                    </div>
                )}

                {/* 資訊顯示 */}
                <div className="control-group info-group">
                    <div className="info-item">
                        <span className="info-label">軌道參數:</span>
                        <span className="info-value">OneWeb LEO (1200km)</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">軌道週期:</span>
                        <span className="info-value">{SATELLITE_CONFIG.ORBITAL_PERIOD_MIN}分鐘</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">可見數量:</span>
                        <span className="info-value">{SATELLITE_CONFIG.VISIBLE_COUNT}顆</span>
                    </div>
                    {satelliteAnimationEnabled && (
                        <div className="info-item">
                            <span className="info-label">實際時間比:</span>
                            <span className="info-value">
                                1分鐘 = {(60 / satelliteSpeedMultiplier).toFixed(1)}秒
                            </span>
                        </div>
                    )}
                </div>

                {/* 狀態提示 */}
                <div className="status-group">
                    <div className={`status-indicator ${satelliteEnabled ? 'active' : 'inactive'}`}>
                        <span className="status-dot"></span>
                        <span className="status-text">
                            {satelliteEnabled ? '衛星已啟用' : '衛星已停用'}
                        </span>
                    </div>
                    {satelliteEnabled && (
                        <div className={`status-indicator ${satelliteAnimationEnabled ? 'active' : 'inactive'}`}>
                            <span className="status-dot"></span>
                            <span className="status-text">
                                {satelliteAnimationEnabled ? '動畫模式' : '靜態模式'}
                            </span>
                        </div>
                    )}
                </div>
            </div>

            <style jsx>{`
                .satellite-control-panel {
                    background: rgba(20, 25, 30, 0.95);
                    border: 1px solid rgba(64, 128, 255, 0.3);
                    border-radius: 8px;
                    padding: 16px;
                    margin: 8px 0;
                    backdrop-filter: blur(10px);
                }

                .section-title {
                    color: #4080ff;
                    font-size: 14px;
                    font-weight: 600;
                    margin: 0 0 12px 0;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }

                .section-icon {
                    font-size: 16px;
                }

                .control-group {
                    margin-bottom: 16px;
                }

                .control-group:last-child {
                    margin-bottom: 0;
                }

                .control-item {
                    margin-bottom: 8px;
                }

                .control-label {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    color: #e1e8ed;
                    font-size: 12px;
                    cursor: pointer;
                }

                .control-label-full {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                    color: #e1e8ed;
                    font-size: 12px;
                }

                .control-checkbox {
                    accent-color: #4080ff;
                }

                .control-select {
                    width: 100%;
                    padding: 4px 8px;
                    background: rgba(40, 50, 60, 0.8);
                    color: #e1e8ed;
                    border: 1px solid rgba(64, 128, 255, 0.3);
                    border-radius: 4px;
                    font-size: 11px;
                }

                .control-select:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .control-slider {
                    width: 100%;
                    height: 4px;
                    background: rgba(64, 128, 255, 0.2);
                    border-radius: 2px;
                    outline: none;
                    accent-color: #4080ff;
                }

                .control-slider:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .info-group {
                    background: rgba(30, 35, 40, 0.6);
                    padding: 8px;
                    border-radius: 4px;
                    border: 1px solid rgba(64, 128, 255, 0.2);
                }

                .info-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 4px;
                    font-size: 11px;
                }

                .info-item:last-child {
                    margin-bottom: 0;
                }

                .info-label {
                    color: #8899aa;
                }

                .info-value {
                    color: #4080ff;
                    font-weight: 500;
                }

                .status-group {
                    margin-top: 12px;
                }

                .status-indicator {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    margin-bottom: 4px;
                    font-size: 11px;
                }

                .status-indicator:last-child {
                    margin-bottom: 0;
                }

                .status-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 50%;
                    background: #666;
                }

                .status-indicator.active .status-dot {
                    background: #00ff88;
                    box-shadow: 0 0 4px #00ff88;
                }

                .status-indicator.inactive .status-dot {
                    background: #ff6666;
                }

                .status-text {
                    color: #e1e8ed;
                }

                .control-checkbox:disabled,
                .control-text:has(+ .control-checkbox:disabled) {
                    opacity: 0.5;
                }
            `}</style>
        </div>
    )
}

export default SatelliteControlPanel