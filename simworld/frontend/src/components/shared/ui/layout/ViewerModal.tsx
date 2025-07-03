import { useState } from 'react'
import '../../../../styles/Navbar.scss' // Assuming styles from Navbar.scss can be reused or adapted

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
    className?: string
    isDarkTheme?: boolean
    onThemeToggle?: () => void
}

const ViewerModal: React.FC<ViewerModalProps> = ({
    isOpen,
    onClose,
    modalTitleConfig,
    lastUpdateTimestamp,
    isLoading,
    onRefresh,
    viewerComponent,
    className = '',
    isDarkTheme = true,
    onThemeToggle,
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
                className={`constellation-modal ${className}`}
                onClick={(e) => e.stopPropagation()}
            >
                <div
                    className="modal-header"
                    style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '15px 20px',
                    }}
                >
                    <div style={{ flex: 1 }}></div>
                    <div
                        className={`modal-title-refreshable ${
                            isLoading ? 'loading' : ''
                        }`}
                        onClick={handleTitleClick}
                        onMouseEnter={() => setIsTitleHovered(true)}
                        onMouseLeave={() => setIsTitleHovered(false)}
                        title={isLoading ? '正在生成...' : '點擊以重新生成圖表'}
                        style={{
                            flex: 1,
                            textAlign: 'center',
                        }}
                    >
                        <span>{titleText}</span>
                    </div>
                    <div
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '5px',
                            flex: 1,
                            justifyContent: 'flex-end',
                        }}
                    >
                        {lastUpdateTimestamp && (
                            <span
                                style={{
                                    fontSize: '0.8rem',
                                    color: '#cccccc',
                                    whiteSpace: 'nowrap',
                                    opacity: 0.7,
                                }}
                            >
                                最後更新: {lastUpdateTimestamp}
                            </span>
                        )}
                        {onThemeToggle && (
                            <div
                                onClick={onThemeToggle}
                                style={{
                                    width: '40px',
                                    height: '20px',
                                    backgroundColor: '#444',
                                    borderRadius: '10px',
                                    position: 'relative',
                                    cursor: 'pointer',
                                    display: 'flex',
                                    alignItems: 'center',
                                    padding: '2px',
                                    transition: 'background-color 0.3s ease',
                                }}
                            >
                                <div
                                    style={{
                                        width: '16px',
                                        height: '16px',
                                        backgroundColor: '#666',
                                        borderRadius: '50%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '10px',
                                        transition: 'transform 0.3s ease',
                                        transform: isDarkTheme
                                            ? 'translateX(0)'
                                            : 'translateX(18px)',
                                    }}
                                >
                                    {isDarkTheme ? '🌙' : '☀️'}
                                </div>
                            </div>
                        )}
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
                                marginLeft: '15px',
                            }}
                            onMouseEnter={(e) =>
                                ((e.target as HTMLButtonElement).style.opacity =
                                    '1')
                            }
                            onMouseLeave={(e) =>
                                ((e.target as HTMLButtonElement).style.opacity =
                                    '0.7')
                            }
                        >
                            ×
                        </button>
                    </div>
                </div>
                <div className="modal-content">{viewerComponent}</div>
            </div>
        </div>
    )
}

export default ViewerModal
