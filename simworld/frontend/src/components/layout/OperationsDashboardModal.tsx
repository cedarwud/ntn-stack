import type { FC } from 'react'
import './MeasurementEventsModal.scss' // 復用現有樣式

interface OperationsDashboardModalProps {
    isOpen: boolean
    onClose: () => void
}

const OperationsDashboardModal: FC<OperationsDashboardModalProps> = ({
    isOpen,
    onClose,
}) => {
    if (!isOpen) {
        return null
    }

    const dashboardUrl = 'http://localhost:3000'  // 階段8: Grafana 監控儀表板

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div
                className="constellation-modal operations-dashboard-modal"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div style={{ flex: 1 }}></div>
                    <h3 style={{ margin: 0, color: 'white', textAlign: 'center' }}>
                        ⚙️ 營運儀表板 (Operations Dashboard)
                    </h3>
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
                        <button
                            onClick={onClose}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: 'white',
                                fontSize: '1.5rem',
                                cursor: 'pointer',
                                padding: '0 5px',
                                lineHeight: 1,
                                opacity: 0.7,
                                transition: 'opacity 0.3s',
                            }}
                            onMouseEnter={(e) =>
                                ((e.target as HTMLButtonElement).style.opacity = '1')
                            }
                            onMouseLeave={(e) =>
                                ((e.target as HTMLButtonElement).style.opacity = '0.7')
                            }
                        >
                            ×
                        </button>
                    </div>
                </div>
                <div className="modal-content">
                    <iframe
                        src={dashboardUrl}
                        title="Operations Dashboard"
                        style={{
                            width: '100%',
                            height: '100%',
                            border: 'none',
                        }}
                    />
                </div>
            </div>
        </div>
    )
}

export default OperationsDashboardModal
