import React from 'react'

interface HandoverEvent {
    id: string
    timestamp: Date
    sourceNac: string
    targetNac: string
    status: 'pending' | 'in-progress' | 'completed' | 'failed'
}

interface HandoverEventVisualizerProps {
    events?: HandoverEvent[]
    enabled?: boolean
    maxEvents?: number
}

const HandoverEventVisualizer: React.FC<HandoverEventVisualizerProps> = ({
    events = [],
    enabled = true,
    maxEvents = 10,
}) => {
    if (!enabled) {
        return null
    }

    const recentEvents = events.slice(-maxEvents)

    return (
        <div
            style={{
                position: 'absolute',
                bottom: '10px',
                left: '10px',
                background: 'rgba(0, 0, 0, 0.8)',
                color: 'white',
                padding: '10px',
                borderRadius: '5px',
                fontSize: '12px',
                fontFamily: 'monospace',
                zIndex: 1000,
                maxWidth: '300px',
                maxHeight: '200px',
                overflowY: 'auto',
            }}
        >
            <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>
                換手事件 ({recentEvents.length})
            </div>
            {recentEvents.length === 0 ? (
                <div style={{ color: '#888' }}>無換手事件</div>
            ) : (
                recentEvents.map((event, index) => (
                    <div
                        key={event.id || index}
                        style={{
                            marginBottom: '5px',
                            padding: '3px',
                            backgroundColor: getStatusColor(event.status),
                            borderRadius: '3px',
                        }}
                    >
                        <div>
                            {event.sourceNac} → {event.targetNac}
                        </div>
                        <div style={{ fontSize: '10px', opacity: 0.8 }}>
                            {event.timestamp
                                ? event.timestamp.toLocaleTimeString()
                                : '未知時間'}{' '}
                            | {getStatusText(event.status)}
                        </div>
                    </div>
                ))
            )}
        </div>
    )
}

function getStatusColor(status: HandoverEvent['status']): string {
    switch (status) {
        case 'pending':
            return 'rgba(255, 255, 0, 0.2)'
        case 'in-progress':
            return 'rgba(0, 150, 255, 0.2)'
        case 'completed':
            return 'rgba(0, 255, 0, 0.2)'
        case 'failed':
            return 'rgba(255, 0, 0, 0.2)'
        default:
            return 'rgba(128, 128, 128, 0.2)'
    }
}

function getStatusText(status: HandoverEvent['status']): string {
    switch (status) {
        case 'pending':
            return '等待中'
        case 'in-progress':
            return '進行中'
        case 'completed':
            return '已完成'
        case 'failed':
            return '失敗'
        default:
            return '未知'
    }
}

export default HandoverEventVisualizer
