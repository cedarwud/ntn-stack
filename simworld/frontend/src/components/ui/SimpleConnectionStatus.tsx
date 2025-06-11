import React, { useState, useEffect } from 'react'
import './SimpleConnectionStatus.scss'

interface ConnectionStatus {
    active: number // 活躍連接數
    preparing: number // 準備換手數
    total: number // 總連接數
}

interface SimpleConnectionStatusProps {
    enabled: boolean
    connections: any[]
}

const SimpleConnectionStatus: React.FC<SimpleConnectionStatusProps> = ({
    enabled,
    connections,
}) => {
    const [status, setStatus] = useState<ConnectionStatus>({
        active: 0,
        preparing: 0,
        total: 0,
    })

    useEffect(() => {
        if (!enabled || connections.length === 0) {
            setStatus({
                active: 0,
                preparing: 0,
                total: 0,
            })
            return
        }

        // 簡化為只計算連接狀態
        const activeConnections = connections.filter(
            (c) => c.status === 'active'
        ).length
        const preparingConnections = connections.filter(
            (c) => c.status === 'handover' || c.status === 'establishing'
        ).length

        setStatus({
            active: activeConnections,
            preparing: preparingConnections,
            total: connections.length,
        })
    }, [enabled, connections])

    if (!enabled) {
        return null
    }

    return (
        <div className="simple-connection-status">
            <div className="status-header">
                <span className="status-icon">🛰️</span>
                <h3>連接狀態</h3>
            </div>

            <div className="status-display">
                <div className="status-item active">
                    <div className="status-indicator">✓</div>
                    <div className="status-info">
                        <div className="status-label">活躍連接</div>
                        <div className="status-value">{status.active}</div>
                    </div>
                </div>

                <div className="status-item preparing">
                    <div className="status-indicator">🔄</div>
                    <div className="status-info">
                        <div className="status-label">準備換手</div>
                        <div className="status-value">{status.preparing}</div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default SimpleConnectionStatus
