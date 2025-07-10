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
        <div className="modal-overlay" onClick={onClose}>
            <div
                className="modal-content full-screen-modal"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    <h2>⚙️ 營運儀表板 (Operations Dashboard)</h2>
                    <button onClick={onClose} className="close-button">
                        &times;
                    </button>
                </div>
                <div className="modal-body">
                    <iframe
                        src={dashboardUrl}
                        title="Operations Dashboard"
                        style={{
                            width: '100%',
                            height: 'calc(100vh - 120px)', // 調整高度以適應模態框
                            border: 'none',
                        }}
                    />
                </div>
            </div>
        </div>
    )
}

export default OperationsDashboardModal
