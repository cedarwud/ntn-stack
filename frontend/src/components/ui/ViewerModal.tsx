import React, { useState } from 'react'
import '../../styles/Navbar.scss' // Assuming styles from Navbar.scss can be reused or adapted

export interface ViewerModalProps {
    isOpen: boolean
    onClose: () => void
    modalTitleConfig: {
        base: string
        loading: string
        hoverRefresh: string
    }
    lastUpdateTimestamp: string
    isLoading: boolean
    onRefresh: (() => void) | null
    viewerComponent: React.ReactNode
}

const ViewerModal: React.FC<ViewerModalProps> = ({
    isOpen,
    onClose,
    modalTitleConfig,
    lastUpdateTimestamp,
    isLoading,
    onRefresh,
    viewerComponent,
}) => {
    const [isTitleHovered, setIsTitleHovered] = useState<boolean>(false)

    if (!isOpen) {
        return null
    }

    const handleTitleClick = () => {
        if (!isLoading && onRefresh) {
            onRefresh()
        }
    }

    let titleText = modalTitleConfig.base
    if (isLoading) {
        titleText = modalTitleConfig.loading
    } else if (isTitleHovered) {
        titleText = modalTitleConfig.hoverRefresh
    }

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div
                className="constellation-modal" // Consider making this class name more generic if needed
                onClick={(e) => e.stopPropagation()}
            >
                <div className="modal-header">
                    <div
                        className={`modal-title-refreshable ${
                            isLoading ? 'loading' : ''
                        }`}
                        onClick={handleTitleClick}
                        onMouseEnter={() => setIsTitleHovered(true)}
                        onMouseLeave={() => setIsTitleHovered(false)}
                        title={isLoading ? '正在生成...' : '點擊以重新生成圖表'}
                    >
                        <span>{titleText}</span>
                    </div>
                    {lastUpdateTimestamp && (
                        <span className="last-update-header">
                            最後更新: {lastUpdateTimestamp}
                        </span>
                    )}
                    <button className="close-button" onClick={onClose}>
                        ×
                    </button>
                </div>
                <div className="modal-content">{viewerComponent}</div>
            </div>
        </div>
    )
}

export default ViewerModal
