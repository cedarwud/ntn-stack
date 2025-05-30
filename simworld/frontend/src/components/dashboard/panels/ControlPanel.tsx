import React, { useState } from 'react'
import './PanelCommon.scss'

interface ControlPanelProps {
    onCommand: (command: string, params: any) => void
    style?: React.CSSProperties
    isFullscreen?: boolean
    onFullscreen?: () => void
    currentScene: string
}

const ControlPanel: React.FC<ControlPanelProps> = ({
    onCommand,
    style,
    isFullscreen,
    onFullscreen,
    currentScene,
}) => {
    const [selectedTab, setSelectedTab] = useState('system')

    const handleCommand = (command: string, params?: any) => {
        onCommand(command, params)
    }

    return (
        <div
            className={`panel control-panel ${
                isFullscreen ? 'fullscreen' : ''
            }`}
            style={style}
        >
            <div className="panel-header">
                <h3>控制面板</h3>
                <div className="panel-controls">
                    <button className="fullscreen-btn" onClick={onFullscreen}>
                        {isFullscreen ? '🗗' : '🗖'}
                    </button>
                </div>
            </div>

            <div className="panel-content">
                <div className="control-tabs">
                    <button
                        className={`tab-btn ${
                            selectedTab === 'system' ? 'active' : ''
                        }`}
                        onClick={() => setSelectedTab('system')}
                    >
                        系統控制
                    </button>
                    <button
                        className={`tab-btn ${
                            selectedTab === 'network' ? 'active' : ''
                        }`}
                        onClick={() => setSelectedTab('network')}
                    >
                        網絡控制
                    </button>
                    <button
                        className={`tab-btn ${
                            selectedTab === 'uav' ? 'active' : ''
                        }`}
                        onClick={() => setSelectedTab('uav')}
                    >
                        UAV 控制
                    </button>
                </div>

                <div className="control-content">
                    {selectedTab === 'system' && (
                        <div className="control-section">
                            <h4>系統操作</h4>
                            <div className="control-buttons">
                                <button
                                    className="control-btn primary"
                                    onClick={() =>
                                        handleCommand('system.restart')
                                    }
                                >
                                    🔄 重啟系統
                                </button>
                                <button
                                    className="control-btn secondary"
                                    onClick={() =>
                                        handleCommand('system.refresh')
                                    }
                                >
                                    🔃 刷新數據
                                </button>
                                <button
                                    className="control-btn secondary"
                                    onClick={() =>
                                        handleCommand('system.backup')
                                    }
                                >
                                    💾 創建備份
                                </button>
                            </div>
                        </div>
                    )}

                    {selectedTab === 'network' && (
                        <div className="control-section">
                            <h4>網絡操作</h4>
                            <div className="control-buttons">
                                <button
                                    className="control-btn primary"
                                    onClick={() =>
                                        handleCommand('network.optimize')
                                    }
                                >
                                    ⚡ 優化網絡
                                </button>
                                <button
                                    className="control-btn secondary"
                                    onClick={() =>
                                        handleCommand('network.reset')
                                    }
                                >
                                    🔄 重置連接
                                </button>
                                <button
                                    className="control-btn secondary"
                                    onClick={() =>
                                        handleCommand('network.diagnose')
                                    }
                                >
                                    🔍 網絡診斷
                                </button>
                            </div>
                        </div>
                    )}

                    {selectedTab === 'uav' && (
                        <div className="control-section">
                            <h4>UAV 操作</h4>
                            <div className="control-buttons">
                                <button
                                    className="control-btn primary"
                                    onClick={() => handleCommand('uav.takeoff')}
                                >
                                    🚁 起飛
                                </button>
                                <button
                                    className="control-btn warning"
                                    onClick={() => handleCommand('uav.land')}
                                >
                                    🛬 降落
                                </button>
                                <button
                                    className="control-btn danger"
                                    onClick={() =>
                                        handleCommand('uav.emergency_stop')
                                    }
                                >
                                    🛑 緊急停止
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default ControlPanel
