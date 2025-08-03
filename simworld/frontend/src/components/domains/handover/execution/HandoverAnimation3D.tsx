import React from 'react'

interface HandoverStatusInfo {
    // 根據需要定義狀態信息的類型
    isActive?: boolean
    currentSatellite?: string
    targetSatellite?: string
    progress?: number
}

interface HandoverStatusPanelProps {
    enabled: boolean
    statusInfo?: HandoverStatusInfo
}

export const HandoverStatusPanel: React.FC<HandoverStatusPanelProps> = ({
    enabled,
    statusInfo,
}) => {
    if (!enabled) {
        return null
    }

    return (
        <div
            style={{
                position: 'absolute',
                top: '10px',
                right: '10px',
                background: 'rgba(0, 0, 0, 0.8)',
                color: 'white',
                padding: '10px',
                borderRadius: '5px',
                fontSize: '12px',
                fontFamily: 'monospace',
                zIndex: 1000,
            }}
        >
            <div>換手狀態面板</div>
            {statusInfo && (
                <>
                    <div>狀態: {statusInfo.isActive ? '進行中' : '待機'}</div>
                    {statusInfo.currentSatellite && (
                        <div>當前衛星: {statusInfo.currentSatellite}</div>
                    )}
                    {statusInfo.targetSatellite && (
                        <div>目標衛星: {statusInfo.targetSatellite}</div>
                    )}
                    {statusInfo.progress !== undefined && (
                        <div>
                            進度: {Math.round(statusInfo.progress * 100)}%
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default HandoverStatusPanel
