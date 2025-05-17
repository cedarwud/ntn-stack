import { useState, useEffect, useCallback, useRef } from 'react'
import '../styles/Navbar.css'

interface NavbarProps {
    onMenuClick: (component: string) => void
    activeComponent: string
}

// Props for Viewer components
interface ViewerProps {
    onReportLastUpdateToNavbar?: (time: string) => void // For header last update
    // New props for Navbar to control refresh from header title
    reportRefreshHandlerToNavbar: (handler: () => void) => void
    reportIsLoadingToNavbar: (isLoading: boolean) => void
}

const Navbar: React.FC<NavbarProps> = ({ onMenuClick, activeComponent }) => {
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const [showCFRModal, setShowCFRModal] = useState(false)
    const [showDelayDopplerModal, setShowDelayDopplerModal] = useState(false)
    const [showTimeFrequencyModal, setShowTimeFrequencyModal] = useState(false)
    const [showSINRModal, setShowSINRModal] = useState(false)

    // State for last update times for each modal header
    const [sinrModalLastUpdate, setSinrModalLastUpdate] = useState<string>('')
    const [cfrModalLastUpdate, setCfrModalLastUpdate] = useState<string>('')
    const [delayDopplerModalLastUpdate, setDelayDopplerModalLastUpdate] =
        useState<string>('')
    const [timeFrequencyModalLastUpdate, setTimeFrequencyModalLastUpdate] =
        useState<string>('')

    // Refs for refresh handlers and states for loading status & hover for header titles
    const sinrRefreshHandlerRef = useRef<(() => void) | null>(null)
    const [sinrIsLoadingForHeader, setSinrIsLoadingForHeader] =
        useState<boolean>(true)
    const [isSinrTitleHovered, setIsSinrTitleHovered] = useState<boolean>(false)

    const cfrRefreshHandlerRef = useRef<(() => void) | null>(null)
    const [cfrIsLoadingForHeader, setCfrIsLoadingForHeader] =
        useState<boolean>(true)
    const [isCfrTitleHovered, setIsCfrTitleHovered] = useState<boolean>(false)

    const delayDopplerRefreshHandlerRef = useRef<(() => void) | null>(null)
    const [delayDopplerIsLoadingForHeader, setDelayDopplerIsLoadingForHeader] =
        useState<boolean>(true)
    const [isDelayDopplerTitleHovered, setIsDelayDopplerTitleHovered] =
        useState<boolean>(false)

    const timeFrequencyRefreshHandlerRef = useRef<(() => void) | null>(null)
    const [
        timeFrequencyIsLoadingForHeader,
        setTimeFrequencyIsLoadingForHeader,
    ] = useState<boolean>(true)
    const [isTimeFrequencyTitleHovered, setIsTimeFrequencyTitleHovered] =
        useState<boolean>(false)

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen)
    }

    const handleCFRClick = (e: React.MouseEvent) => {
        e.preventDefault()
        setShowCFRModal(true)
    }

    const closeCFRModal = () => {
        setShowCFRModal(false)
    }

    const handleDelayDopplerClick = (e: React.MouseEvent) => {
        e.preventDefault()
        setShowDelayDopplerModal(true)
    }

    const closeDelayDopplerModal = () => {
        setShowDelayDopplerModal(false)
    }

    const handleTimeFrequencyClick = (e: React.MouseEvent) => {
        e.preventDefault()
        setShowTimeFrequencyModal(true)
    }

    const closeTimeFrequencyModal = () => {
        setShowTimeFrequencyModal(false)
    }

    const handleSINRClick = (e: React.MouseEvent) => {
        e.preventDefault()
        setShowSINRModal(true)
    }

    const closeSINRModal = () => {
        setShowSINRModal(false)
    }

    return (
        <>
            <nav className="navbar">
                <div className="navbar-container">
                    <div className="navbar-logo">Sionna</div>

                    <div className="navbar-menu-toggle" onClick={toggleMenu}>
                        <span
                            className={`menu-icon ${isMenuOpen ? 'open' : ''}`}
                        ></span>
                    </div>

                    <ul className={`navbar-menu ${isMenuOpen ? 'open' : ''}`}>
                        <li
                            className={`navbar-item ${
                                showSINRModal ? 'active' : ''
                            }`}
                            onClick={handleSINRClick}
                        >
                            SINR MAP
                        </li>
                        <li
                            className={`navbar-item ${
                                showCFRModal ? 'active' : ''
                            }`}
                            onClick={handleCFRClick}
                        >
                            Constellation & CFR
                        </li>
                        <li
                            className={`navbar-item ${
                                showDelayDopplerModal ? 'active' : ''
                            }`}
                            onClick={handleDelayDopplerClick}
                        >
                            Delay–Doppler
                        </li>
                        <li
                            className={`navbar-item ${
                                showTimeFrequencyModal ? 'active' : ''
                            }`}
                            onClick={handleTimeFrequencyClick}
                        >
                            Time-Frequency
                        </li>
                        <li
                            className={`navbar-item ${
                                activeComponent === '2DRT' ? 'active' : ''
                            }`}
                            onClick={() => onMenuClick('2DRT')}
                        >
                            Floor Plan
                        </li>
                        <li
                            className={`navbar-item ${
                                activeComponent === '3DRT' ? 'active' : ''
                            }`}
                            onClick={() => onMenuClick('3DRT')}
                        >
                            Stereogram
                        </li>
                    </ul>
                </div>
            </nav>

            {/* SINR Map 彈窗 */}
            {showSINRModal && (
                <div className="modal-backdrop" onClick={closeSINRModal}>
                    <div
                        className="constellation-modal"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <div
                                className={`modal-title-refreshable ${
                                    sinrIsLoadingForHeader ? 'loading' : ''
                                }`}
                                onClick={() => {
                                    if (
                                        !sinrIsLoadingForHeader &&
                                        sinrRefreshHandlerRef.current
                                    ) {
                                        sinrRefreshHandlerRef.current()
                                    }
                                }}
                                onMouseEnter={() => setIsSinrTitleHovered(true)}
                                onMouseLeave={() =>
                                    setIsSinrTitleHovered(false)
                                }
                                title={
                                    sinrIsLoadingForHeader
                                        ? '正在生成...'
                                        : '點擊以重新生成圖表'
                                }
                            >
                                <span>
                                    {sinrIsLoadingForHeader
                                        ? '正在即時運算並生成 SINR Map...'
                                        : isSinrTitleHovered
                                        ? '重新生成圖表'
                                        : 'SINR Map'}
                                </span>
                            </div>
                            {sinrModalLastUpdate && (
                                <span className="last-update-header">
                                    最後更新: {sinrModalLastUpdate}
                                </span>
                            )}
                            <button
                                className="close-button"
                                onClick={closeSINRModal}
                            >
                                ×
                            </button>
                        </div>
                        <div className="modal-content">
                            <SINRViewer
                                onReportLastUpdateToNavbar={
                                    setSinrModalLastUpdate
                                }
                                reportRefreshHandlerToNavbar={(handler) => {
                                    sinrRefreshHandlerRef.current = handler
                                }}
                                reportIsLoadingToNavbar={
                                    setSinrIsLoadingForHeader
                                }
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Constellation & CFR 彈窗 */}
            {showCFRModal && (
                <div className="modal-backdrop" onClick={closeCFRModal}>
                    <div
                        className="constellation-modal"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <div
                                className={`modal-title-refreshable ${
                                    cfrIsLoadingForHeader ? 'loading' : ''
                                }`}
                                onClick={() => {
                                    if (
                                        !cfrIsLoadingForHeader &&
                                        cfrRefreshHandlerRef.current
                                    ) {
                                        cfrRefreshHandlerRef.current()
                                    }
                                }}
                                onMouseEnter={() => setIsCfrTitleHovered(true)}
                                onMouseLeave={() => setIsCfrTitleHovered(false)}
                                title={
                                    cfrIsLoadingForHeader
                                        ? '正在生成...'
                                        : '點擊以重新生成圖表'
                                }
                            >
                                <span>
                                    {cfrIsLoadingForHeader
                                        ? '正在即時運算並生成 Constellation & CFR...'
                                        : isCfrTitleHovered
                                        ? '重新生成圖表'
                                        : 'Constellation & CFR Magnitude'}
                                </span>
                            </div>
                            {cfrModalLastUpdate && (
                                <span className="last-update-header">
                                    最後更新: {cfrModalLastUpdate}
                                </span>
                            )}
                            <button
                                className="close-button"
                                onClick={closeCFRModal}
                            >
                                ×
                            </button>
                        </div>
                        <div className="modal-content">
                            <CFRViewer
                                onReportLastUpdateToNavbar={
                                    setCfrModalLastUpdate
                                }
                                reportRefreshHandlerToNavbar={(handler) => {
                                    cfrRefreshHandlerRef.current = handler
                                }}
                                reportIsLoadingToNavbar={
                                    setCfrIsLoadingForHeader
                                }
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Delay–Doppler 彈窗 */}
            {showDelayDopplerModal && (
                <div
                    className="modal-backdrop"
                    onClick={closeDelayDopplerModal}
                >
                    <div
                        className="constellation-modal"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <div
                                className={`modal-title-refreshable ${
                                    delayDopplerIsLoadingForHeader
                                        ? 'loading'
                                        : ''
                                }`}
                                onClick={() => {
                                    if (
                                        !delayDopplerIsLoadingForHeader &&
                                        delayDopplerRefreshHandlerRef.current
                                    ) {
                                        delayDopplerRefreshHandlerRef.current()
                                    }
                                }}
                                onMouseEnter={() =>
                                    setIsDelayDopplerTitleHovered(true)
                                }
                                onMouseLeave={() =>
                                    setIsDelayDopplerTitleHovered(false)
                                }
                                title={
                                    delayDopplerIsLoadingForHeader
                                        ? '正在生成...'
                                        : '點擊以重新生成圖表'
                                }
                            >
                                <span>
                                    {delayDopplerIsLoadingForHeader
                                        ? '正在即時運算並生成 Delay-Doppler...'
                                        : isDelayDopplerTitleHovered
                                        ? '重新生成圖表'
                                        : 'Delay-Doppler Plots'}
                                </span>
                            </div>
                            {delayDopplerModalLastUpdate && (
                                <span className="last-update-header">
                                    最後更新: {delayDopplerModalLastUpdate}
                                </span>
                            )}
                            <button
                                className="close-button"
                                onClick={closeDelayDopplerModal}
                            >
                                ×
                            </button>
                        </div>
                        <div className="modal-content">
                            <DelayDopplerViewer
                                onReportLastUpdateToNavbar={
                                    setDelayDopplerModalLastUpdate
                                }
                                reportRefreshHandlerToNavbar={(handler) => {
                                    delayDopplerRefreshHandlerRef.current =
                                        handler
                                }}
                                reportIsLoadingToNavbar={
                                    setDelayDopplerIsLoadingForHeader
                                }
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Time-Frequency 彈窗 - 更新為 Time-Frequency */}
            {showTimeFrequencyModal && (
                <div
                    className="modal-backdrop"
                    onClick={closeTimeFrequencyModal}
                >
                    <div
                        className="constellation-modal"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <div
                                className={`modal-title-refreshable ${
                                    timeFrequencyIsLoadingForHeader
                                        ? 'loading'
                                        : ''
                                }`}
                                onClick={() => {
                                    if (
                                        !timeFrequencyIsLoadingForHeader &&
                                        timeFrequencyRefreshHandlerRef.current
                                    ) {
                                        timeFrequencyRefreshHandlerRef.current()
                                    }
                                }}
                                onMouseEnter={() =>
                                    setIsTimeFrequencyTitleHovered(true)
                                }
                                onMouseLeave={() =>
                                    setIsTimeFrequencyTitleHovered(false)
                                }
                                title={
                                    timeFrequencyIsLoadingForHeader
                                        ? '正在生成...'
                                        : '點擊以重新生成圖表'
                                }
                            >
                                <span>
                                    {timeFrequencyIsLoadingForHeader
                                        ? '正在即時運算並生成 Time-Frequency...'
                                        : isTimeFrequencyTitleHovered
                                        ? '重新生成圖表'
                                        : 'Time-Frequency Plots'}
                                </span>
                            </div>
                            {timeFrequencyModalLastUpdate && (
                                <span className="last-update-header">
                                    最後更新: {timeFrequencyModalLastUpdate}
                                </span>
                            )}
                            <button
                                className="close-button"
                                onClick={closeTimeFrequencyModal}
                            >
                                ×
                            </button>
                        </div>
                        <div className="modal-content">
                            <TimeFrequencyViewer
                                onReportLastUpdateToNavbar={
                                    setTimeFrequencyModalLastUpdate
                                }
                                reportRefreshHandlerToNavbar={(handler) => {
                                    timeFrequencyRefreshHandlerRef.current =
                                        handler
                                }}
                                reportIsLoadingToNavbar={
                                    setTimeFrequencyIsLoadingForHeader
                                }
                            />
                        </div>
                    </div>
                </div>
            )}
        </>
    )
}

// SINR Map 顯示組件
const SINRViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)
    const [sinrVmin, setSinrVmin] = useState<number>(-40)
    const [sinrVmax, setSinrVmax] = useState<number>(0)
    const [cellSize, setCellSize] = useState<number>(1.0)
    const [samplesPerTx, setSamplesPerTx] = useState<number>(10 ** 7)

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = '/api/v1/sionna/sinr-map'

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadSINRMapImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        const apiUrl = `${API_PATH}?sinr_vmin=${sinrVmin}&sinr_vmax=${sinrVmax}&cell_size=${cellSize}&samples_per_tx=${samplesPerTx}`
        fetch(apiUrl)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入 SINR Map 失敗:', err)
                setError('無法載入 SINR Map: ' + err.message)
                setIsLoading(false)
            })
    }, [sinrVmin, sinrVmax, cellSize, samplesPerTx, updateTimestamp])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadSINRMapImage)
    }, [loadSINRMapImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadSINRMapImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadSINRMapImage])

    const handleSinrVminChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSinrVmin(Number(e.target.value))
    }
    const handleSinrVmaxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setSinrVmax(Number(e.target.value))
    }
    const handleCellSizeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setCellSize(Number(e.target.value))
    }
    const handleSamplesChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setSamplesPerTx(Number(e.target.value))
    }

    return (
        <div className="image-viewer sinr-image-container">
            {isLoading && (
                <div className="loading">正在即時運算並生成 SINR Map...</div>
            )}
            {error && <div className="error">{error}</div>}
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="SINR Map"
                    className="view-image sinr-view-image"
                />
            )}
        </div>
    )
}

// Constellation & CFR 顯示組件
const CFRViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = '/api/v1/sionna/cfr-plot'

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadCFRImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        fetch(API_PATH)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入 Constellation & CFR 失敗:', err)
                setError('無法載入 Constellation & CFR: ' + err.message)
                setIsLoading(false)
            })
    }, [updateTimestamp])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadCFRImage)
    }, [loadCFRImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadCFRImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadCFRImage])

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Constellation & CFR...
                </div>
            )}
            {error && <div className="error">{error}</div>}
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="Constellation & CFR Magnitude"
                    className="view-image"
                />
            )}
        </div>
    )
}

// Delay-Doppler 顯示組件
const DelayDopplerViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const imageUrlRef = useRef<string | null>(null)

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadDopplerImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        fetch('/api/v1/sionna/doppler-plots')
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入延遲多普勒圖失敗:', err)
                setError('無法載入延遲多普勒圖: ' + err.message)
                setIsLoading(false)
            })
    }, [updateTimestamp])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadDopplerImage)
    }, [loadDopplerImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadDopplerImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadDopplerImage])

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Delay-Doppler...
                </div>
            )}
            {error && <div className="error">{error}</div>}
            <div className="delay-doppler-container">
                {imageUrl && (
                    <div className="image-item doppler-image-v2">
                        <img
                            src={imageUrl}
                            alt="Delay-Doppler Plot"
                            className="view-image doppler-image-v2"
                        />
                    </div>
                )}
            </div>
        </div>
    )
}

// Time-Frequency 顯示組件
const TimeFrequencyViewer: React.FC<ViewerProps> = ({
    onReportLastUpdateToNavbar,
    reportRefreshHandlerToNavbar,
    reportIsLoadingToNavbar,
}) => {
    const [isLoading, setIsLoading] = useState(true)
    const [imageUrl, setImageUrl] = useState<string | null>(null)
    const [error, setError] = useState<string | null>(null)

    const imageUrlRef = useRef<string | null>(null)
    const API_PATH = '/api/v1/sionna/channel-response-plots'

    const updateTimestamp = useCallback(() => {
        const now = new Date()
        const timeString = now.toLocaleTimeString()
        onReportLastUpdateToNavbar?.(timeString)
    }, [onReportLastUpdateToNavbar])

    useEffect(() => {
        imageUrlRef.current = imageUrl
    }, [imageUrl])

    const loadChannelResponseImage = useCallback(() => {
        setIsLoading(true)
        setError(null)
        fetch(API_PATH)
            .then((response) => {
                if (!response.ok) {
                    if (response.status === 400) {
                        return response.json().then((data) => {
                            throw new Error(
                                data.detail ||
                                    '需要至少一個活動的發射器和接收器'
                            )
                        })
                    }
                    throw new Error(
                        `API 請求失敗: ${response.status} ${response.statusText}`
                    )
                }
                return response.blob()
            })
            .then((blob) => {
                if (imageUrlRef.current) {
                    URL.revokeObjectURL(imageUrlRef.current)
                }
                const url = URL.createObjectURL(blob)
                setImageUrl(url)
                setIsLoading(false)
                updateTimestamp()
            })
            .catch((err) => {
                console.error('載入通道響應圖失敗:', err)
                setError('無法載入通道響應圖: ' + err.message)
                setIsLoading(false)
            })
    }, [updateTimestamp])

    useEffect(() => {
        reportRefreshHandlerToNavbar(loadChannelResponseImage)
    }, [loadChannelResponseImage, reportRefreshHandlerToNavbar])

    useEffect(() => {
        reportIsLoadingToNavbar(isLoading)
    }, [isLoading, reportIsLoadingToNavbar])

    useEffect(() => {
        loadChannelResponseImage()
        return () => {
            if (imageUrlRef.current) {
                URL.revokeObjectURL(imageUrlRef.current)
            }
        }
    }, [loadChannelResponseImage])

    return (
        <div className="image-viewer">
            {isLoading && (
                <div className="loading">
                    正在即時運算並生成 Time-Frequency...
                </div>
            )}
            {error && <div className="error">{error}</div>}
            {imageUrl && (
                <img
                    src={imageUrl}
                    alt="Time-Frequency"
                    className="view-image"
                />
            )}
        </div>
    )
}

export default Navbar
