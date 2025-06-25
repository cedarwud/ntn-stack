import { useState, useRef, useEffect } from 'react'
import type { FC, RefObject } from 'react'
import { useNavigate } from 'react-router-dom'
import '../../styles/Navbar.scss'
import SINRViewer from '../viewers/SINRViewer'
import CFRViewer from '../viewers/CFRViewer'
import DelayDopplerViewer from '../viewers/DelayDopplerViewer'
import TimeFrequencyViewer from '../viewers/TimeFrequencyViewer'
import FourWayHandoverComparisonViewer from '../viewers/FourWayHandoverComparisonViewer'
import ViewerModal from '../ui/ViewerModal'
import ChartAnalysisDashboard from '../charts/ChartAnalysisDashboard'
import { ViewerProps } from '../../types/viewer'
import {
    SCENE_DISPLAY_NAMES,
    getSceneDisplayName,
} from '../../utils/sceneUtils'

interface NavbarProps {
    onMenuClick: (component: string) => void
    activeComponent: string
    currentScene: string
}

// Define a type for the individual modal configuration
interface ModalConfig {
    id: string
    menuText: string
    titleConfig: {
        base: string
        loading: string
        hoverRefresh: string
    }
    isOpen: boolean
    openModal: () => void
    closeModal: () => void
    lastUpdate: string
    setLastUpdate: (time: string) => void
    isLoading: boolean
    setIsLoading: (loading: boolean) => void
    refreshHandlerRef: RefObject<(() => void) | null>
    ViewerComponent: FC<ViewerProps>
}

const Navbar: FC<NavbarProps> = ({
    onMenuClick,
    activeComponent,
    currentScene,
}) => {
    const navigate = useNavigate()
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const [isDropdownOpen, setIsDropdownOpen] = useState(false)
    const [isChartsDropdownOpen, setIsChartsDropdownOpen] = useState(false)
    const [isMobile, setIsMobile] = useState(false)

    // 新增 Chart Analysis Modal 狀態
    const [showChartAnalysisModal, setShowChartAnalysisModal] = useState(false)

    // States for modal visibility
    const [showSINRModal, setShowSINRModal] = useState(false)
    const [showCFRModal, setShowCFRModal] = useState(false)
    const [showDelayDopplerModal, setShowDelayDopplerModal] = useState(false)
    const [showTimeFrequencyModal, setShowTimeFrequencyModal] = useState(false)
    const [showFourWayComparisonModal, setShowFourWayComparisonModal] =
        useState(false)
    // States for last update times
    const [sinrModalLastUpdate, setSinrModalLastUpdate] = useState<string>('')
    const [cfrModalLastUpdate, setCfrModalLastUpdate] = useState<string>('')
    const [delayDopplerModalLastUpdate, setDelayDopplerModalLastUpdate] =
        useState<string>('')
    const [timeFrequencyModalLastUpdate, setTimeFrequencyModalLastUpdate] =
        useState<string>('')
    const [
        fourWayComparisonModalLastUpdate,
        setFourWayComparisonModalLastUpdate,
    ] = useState<string>('')
    // Refs for refresh handlers
    const sinrRefreshHandlerRef = useRef<(() => void) | null>(null)
    const cfrRefreshHandlerRef = useRef<(() => void) | null>(null)
    const delayDopplerRefreshHandlerRef = useRef<(() => void) | null>(null)
    const timeFrequencyRefreshHandlerRef = useRef<(() => void) | null>(null)
    const fourWayComparisonRefreshHandlerRef = useRef<(() => void) | null>(null)
    // States for loading status for header titles
    const [sinrIsLoadingForHeader, setSinrIsLoadingForHeader] =
        useState<boolean>(true)
    const [cfrIsLoadingForHeader, setCfrIsLoadingForHeader] =
        useState<boolean>(true)
    const [delayDopplerIsLoadingForHeader, setDelayDopplerIsLoadingForHeader] =
        useState<boolean>(true)
    const [
        timeFrequencyIsLoadingForHeader,
        setTimeFrequencyIsLoadingForHeader,
    ] = useState<boolean>(true)
    const [
        fourWayComparisonIsLoadingForHeader,
        setFourWayComparisonIsLoadingForHeader,
    ] = useState<boolean>(true)
    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen)
    }

    const handleSceneChange = (sceneKey: string) => {
        console.log('Scene change clicked:', sceneKey)
        console.log('Current activeComponent:', activeComponent)
        // 根據當前的視圖導航到新場景
        const currentView =
            activeComponent === '3DRT' ? 'stereogram' : 'floor-plan'
        console.log('Navigating to:', `/${sceneKey}/${currentView}`)
        navigate(`/${sceneKey}/${currentView}`)
    }

    const handleFloorPlanClick = () => {
        navigate(`/${currentScene}/floor-plan`)
        onMenuClick('2DRT')
    }

    const handleStereogramClick = () => {
        navigate(`/${currentScene}/stereogram`)
        onMenuClick('3DRT')
    }

    const modalConfigs: ModalConfig[] = [
        {
            id: 'sinr',
            menuText: 'SINR MAP',
            titleConfig: {
                base: 'SINR Map',
                loading: '正在即時運算並生成 SINR Map...',
                hoverRefresh: '重新生成圖表',
            },
            isOpen: showSINRModal,
            openModal: () => setShowSINRModal(true),
            closeModal: () => setShowSINRModal(false),
            lastUpdate: sinrModalLastUpdate,
            setLastUpdate: setSinrModalLastUpdate,
            isLoading: sinrIsLoadingForHeader,
            setIsLoading: setSinrIsLoadingForHeader,
            refreshHandlerRef: sinrRefreshHandlerRef,
            ViewerComponent: SINRViewer,
        },
        {
            id: 'cfr',
            menuText: 'Constellation & CFR',
            titleConfig: {
                base: 'Constellation & CFR Magnitude',
                loading: '正在即時運算並生成 Constellation & CFR...',
                hoverRefresh: '重新生成圖表',
            },
            isOpen: showCFRModal,
            openModal: () => setShowCFRModal(true),
            closeModal: () => setShowCFRModal(false),
            lastUpdate: cfrModalLastUpdate,
            setLastUpdate: setCfrModalLastUpdate,
            isLoading: cfrIsLoadingForHeader,
            setIsLoading: setCfrIsLoadingForHeader,
            refreshHandlerRef: cfrRefreshHandlerRef,
            ViewerComponent: CFRViewer,
        },
        {
            id: 'delayDoppler',
            menuText: 'Delay–Doppler',
            titleConfig: {
                base: 'Delay-Doppler Plots',
                loading: '正在即時運算並生成 Delay-Doppler...',
                hoverRefresh: '重新生成圖表',
            },
            isOpen: showDelayDopplerModal,
            openModal: () => setShowDelayDopplerModal(true),
            closeModal: () => setShowDelayDopplerModal(false),
            lastUpdate: delayDopplerModalLastUpdate,
            setLastUpdate: setDelayDopplerModalLastUpdate,
            isLoading: delayDopplerIsLoadingForHeader,
            setIsLoading: setDelayDopplerIsLoadingForHeader,
            refreshHandlerRef: delayDopplerRefreshHandlerRef,
            ViewerComponent: DelayDopplerViewer,
        },
        {
            id: 'timeFrequency',
            menuText: 'Time-Frequency',
            titleConfig: {
                base: 'Time-Frequency Plots',
                loading: '正在即時運算並生成 Time-Frequency...',
                hoverRefresh: '重新生成圖表',
            },
            isOpen: showTimeFrequencyModal,
            openModal: () => setShowTimeFrequencyModal(true),
            closeModal: () => setShowTimeFrequencyModal(false),
            lastUpdate: timeFrequencyModalLastUpdate,
            setLastUpdate: setTimeFrequencyModalLastUpdate,
            isLoading: timeFrequencyIsLoadingForHeader,
            setIsLoading: setTimeFrequencyIsLoadingForHeader,
            refreshHandlerRef: timeFrequencyRefreshHandlerRef,
            ViewerComponent: TimeFrequencyViewer,
        },
        {
            id: 'fourWayComparison',
            menuText: '四種方案詳細對比',
            titleConfig: {
                base: '四種換手方案詳細性能對比',
                loading: '正在獲取真實NetStack數據並生成詳細對比結果...',
                hoverRefresh: '重新獲取詳細對比數據',
            },
            isOpen: showFourWayComparisonModal,
            openModal: () => setShowFourWayComparisonModal(true),
            closeModal: () => setShowFourWayComparisonModal(false),
            lastUpdate: fourWayComparisonModalLastUpdate,
            setLastUpdate: setFourWayComparisonModalLastUpdate,
            isLoading: fourWayComparisonIsLoadingForHeader,
            setIsLoading: setFourWayComparisonIsLoadingForHeader,
            refreshHandlerRef: fourWayComparisonRefreshHandlerRef,
            ViewerComponent: FourWayHandoverComparisonViewer,
        },
    ]

    const [dropdownPosition, setDropdownPosition] = useState<{ left: number }>({
        left: 0,
    })
    const logoRef = useRef<HTMLDivElement>(null)

    // 計算下拉選單位置
    useEffect(() => {
        const updatePosition = () => {
            if (logoRef.current) {
                const rect = logoRef.current.getBoundingClientRect()
                setDropdownPosition({
                    left: rect.left + rect.width / 2,
                })
            }
        }

        // 初始計算
        updatePosition()

        // 監聽視窗調整事件
        window.addEventListener('resize', updatePosition)
        return () => {
            window.removeEventListener('resize', updatePosition)
        }
    }, [])

    // 檢查是否為移動端
    useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth <= 768)
        }

        checkMobile()
        window.addEventListener('resize', checkMobile)

        return () => {
            window.removeEventListener('resize', checkMobile)
        }
    }, [])

    // 處理圖表 dropdown 的點擊/hover 事件
    const handleChartsDropdownToggle = () => {
        if (isMobile) {
            setIsChartsDropdownOpen(!isChartsDropdownOpen)
        }
    }

    const handleChartsMouseEnter = () => {
        if (!isMobile) {
            setIsChartsDropdownOpen(true)
        }
    }

    const handleChartsMouseLeave = () => {
        if (!isMobile) {
            setIsChartsDropdownOpen(false)
        }
    }

    // 檢查是否有任何圖表模態框打開
    const hasActiveChart = modalConfigs.some(
        (config) =>
            ['sinr', 'cfr', 'delayDoppler', 'timeFrequency'].includes(
                config.id
            ) && config.isOpen
    )

    return (
        <>
            <nav className="navbar">
                <div className="navbar-container">
                    <div
                        className="navbar-dropdown-wrapper"
                        onMouseEnter={() => setIsDropdownOpen(true)}
                        onMouseLeave={() => setIsDropdownOpen(false)}
                    >
                        <div
                            className="navbar-logo"
                            ref={logoRef}
                            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                        >
                            {getSceneDisplayName(currentScene)}
                            <span className="dropdown-arrow">▼</span>
                        </div>
                        <div
                            className={`scene-dropdown ${
                                isDropdownOpen ? 'show' : ''
                            }`}
                            style={{ left: `${dropdownPosition.left}px` }}
                        >
                            {Object.entries(SCENE_DISPLAY_NAMES).map(
                                ([key, value]) => (
                                    <div
                                        key={key}
                                        className={`scene-option ${
                                            key === currentScene ? 'active' : ''
                                        }`}
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            handleSceneChange(key)
                                            setIsDropdownOpen(false)
                                        }}
                                    >
                                        {value}
                                    </div>
                                )
                            )}
                        </div>
                    </div>

                    <div className="navbar-menu-toggle" onClick={toggleMenu}>
                        <span
                            className={`menu-icon ${isMenuOpen ? 'open' : ''}`}
                        ></span>
                    </div>

                    <ul className={`navbar-menu ${isMenuOpen ? 'open' : ''}`}>
                        {/* 信號分析 Dropdown */}
                        <li
                            className={`navbar-item navbar-dropdown-item ${
                                hasActiveChart ? 'active' : ''
                            } ${
                                isMobile && isChartsDropdownOpen
                                    ? 'mobile-expanded'
                                    : ''
                            }`}
                            onMouseEnter={handleChartsMouseEnter}
                            onMouseLeave={handleChartsMouseLeave}
                        >
                            <span
                                className="dropdown-trigger"
                                onClick={handleChartsDropdownToggle}
                            >
                                信號分析
                                <span className="dropdown-arrow-small">▼</span>
                            </span>
                            <div
                                className={`charts-dropdown ${
                                    isChartsDropdownOpen ? 'show' : ''
                                }`}
                            >
                                {modalConfigs
                                    .filter((config) =>
                                        [
                                            'sinr',
                                            'cfr',
                                            'delayDoppler',
                                            'timeFrequency',
                                            'fourWayComparison',
                                        ].includes(config.id)
                                    )
                                    .map((config) => (
                                        <div
                                            key={config.id}
                                            className={`charts-dropdown-item ${
                                                config.isOpen ? 'active' : ''
                                            }`}
                                            onClick={(e) => {
                                                e.preventDefault()
                                                e.stopPropagation()
                                                config.openModal()
                                                setIsChartsDropdownOpen(false)
                                                if (isMobile) {
                                                    setIsMenuOpen(false)
                                                }
                                            }}
                                        >
                                            {config.menuText}
                                        </div>
                                    ))}
                            </div>
                        </li>

                        <li
                            className={`navbar-item ${
                                activeComponent === '2DRT' ? 'active' : ''
                            }`}
                            onClick={handleFloorPlanClick}
                        >
                            平面圖
                        </li>
                        <li
                            className={`navbar-item ${
                                activeComponent === '3DRT' ? 'active' : ''
                            }`}
                            onClick={handleStereogramClick}
                        >
                            立體圖
                        </li>

                        {/* 新增圖表分析按鈕 */}
                        <li
                            className={`navbar-item ${
                                showChartAnalysisModal ? 'active' : ''
                            }`}
                            onClick={() => setShowChartAnalysisModal(true)}
                        >
                            📈 圖表分析
                        </li>
                    </ul>
                </div>
            </nav>

            {/* Render modals using ViewerModal component */}
            {modalConfigs.map((config) =>
                config.isOpen ? (
                    <ViewerModal
                        key={config.id}
                        isOpen={config.isOpen}
                        onClose={config.closeModal}
                        modalTitleConfig={config.titleConfig}
                        lastUpdateTimestamp={config.lastUpdate}
                        isLoading={config.isLoading}
                        onRefresh={config.refreshHandlerRef.current}
                        viewerComponent={
                            <config.ViewerComponent
                                onReportLastUpdateToNavbar={
                                    config.setLastUpdate
                                }
                                reportRefreshHandlerToNavbar={(
                                    handler: () => void
                                ) => {
                                    config.refreshHandlerRef.current = handler
                                }}
                                reportIsLoadingToNavbar={config.setIsLoading}
                                currentScene={currentScene}
                            />
                        }
                    />
                ) : null
            )}

            {/* 新增 Chart Analysis Dashboard - 100% 全屏彈窗 */}
            <ChartAnalysisDashboard
                isOpen={showChartAnalysisModal}
                onClose={() => setShowChartAnalysisModal(false)}
            />
        </>
    )
}

export default Navbar
