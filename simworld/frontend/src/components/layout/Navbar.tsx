import { useState, useRef, useEffect } from 'react'
import type { FC, RefObject } from 'react'
import { useNavigate } from 'react-router-dom'
import '../../styles/Navbar.scss'
import SINRViewer from '../viewers/SINRViewer'
import CFRViewer from '../viewers/CFRViewer'
import DelayDopplerViewer from '../viewers/DelayDopplerViewer'
import TimeFrequencyViewer from '../viewers/TimeFrequencyViewer'
import TestViewer from '../viewers/TestViewer'
import InterferenceVisualization from '../viewers/InterferenceVisualization'
import AIDecisionVisualization from '../viewers/AIDecisionVisualization'
import UAVSwarmCoordinationViewer from '../viewers/UAVSwarmCoordinationViewer'
import MeshNetworkTopologyViewer from '../viewers/MeshNetworkTopologyViewer'
import FrequencySpectrumVisualization from '../viewers/FrequencySpectrumVisualization'
import AIRANDecisionVisualization from '../viewers/AIRANDecisionVisualization'
import ViewerModal from '../ui/ViewerModal'
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

    // States for modal visibility
    const [showSINRModal, setShowSINRModal] = useState(false)
    const [showCFRModal, setShowCFRModal] = useState(false)
    const [showDelayDopplerModal, setShowDelayDopplerModal] = useState(false)
    const [showTimeFrequencyModal, setShowTimeFrequencyModal] = useState(false)
    const [showTestModal, setShowTestModal] = useState(false)
    const [showInterferenceModal, setShowInterferenceModal] = useState(false)
    const [showAIDecisionModal, setShowAIDecisionModal] = useState(false)
    const [showUAVSwarmModal, setShowUAVSwarmModal] = useState(false)
    const [showMeshNetworkModal, setShowMeshNetworkModal] = useState(false)
    const [showFrequencySpectrumModal, setShowFrequencySpectrumModal] = useState(false)
    const [showAIRANDecisionModal, setShowAIRANDecisionModal] = useState(false)

    // States for last update times
    const [sinrModalLastUpdate, setSinrModalLastUpdate] = useState<string>('')
    const [cfrModalLastUpdate, setCfrModalLastUpdate] = useState<string>('')
    const [delayDopplerModalLastUpdate, setDelayDopplerModalLastUpdate] =
        useState<string>('')
    const [timeFrequencyModalLastUpdate, setTimeFrequencyModalLastUpdate] =
        useState<string>('')
    const [interferenceModalLastUpdate, setInterferenceModalLastUpdate] =
        useState<string>('')
    const [aiDecisionModalLastUpdate, setAIDecisionModalLastUpdate] =
        useState<string>('')
    const [uavSwarmModalLastUpdate, setUAVSwarmModalLastUpdate] =
        useState<string>('')
    const [meshNetworkModalLastUpdate, setMeshNetworkModalLastUpdate] =
        useState<string>('')
    const [frequencySpectrumModalLastUpdate, setFrequencySpectrumModalLastUpdate] =
        useState<string>('')
    const [airanDecisionModalLastUpdate, setAIRANDecisionModalLastUpdate] =
        useState<string>('')

    // Refs for refresh handlers
    const sinrRefreshHandlerRef = useRef<(() => void) | null>(null)
    const cfrRefreshHandlerRef = useRef<(() => void) | null>(null)
    const delayDopplerRefreshHandlerRef = useRef<(() => void) | null>(null)
    const timeFrequencyRefreshHandlerRef = useRef<(() => void) | null>(null)
    const interferenceRefreshHandlerRef = useRef<(() => void) | null>(null)
    const aiDecisionRefreshHandlerRef = useRef<(() => void) | null>(null)
    const uavSwarmRefreshHandlerRef = useRef<(() => void) | null>(null)
    const meshNetworkRefreshHandlerRef = useRef<(() => void) | null>(null)
    const frequencySpectrumRefreshHandlerRef = useRef<(() => void) | null>(null)
    const airanDecisionRefreshHandlerRef = useRef<(() => void) | null>(null)

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
    const [interferenceIsLoadingForHeader, setInterferenceIsLoadingForHeader] =
        useState<boolean>(true)
    const [aiDecisionIsLoadingForHeader, setAIDecisionIsLoadingForHeader] =
        useState<boolean>(true)
    const [uavSwarmIsLoadingForHeader, setUAVSwarmIsLoadingForHeader] =
        useState<boolean>(true)
    const [meshNetworkIsLoadingForHeader, setMeshNetworkIsLoadingForHeader] =
        useState<boolean>(true)
    const [frequencySpectrumIsLoadingForHeader, setFrequencySpectrumIsLoadingForHeader] =
        useState<boolean>(true)
    const [airanDecisionIsLoadingForHeader, setAIRANDecisionIsLoadingForHeader] =
        useState<boolean>(true)

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
            id: 'interference',
            menuText: '3D 干擾可視化',
            titleConfig: {
                base: '3D 干擾源和影響展示',
                loading: '正在計算干擾模式...',
                hoverRefresh: '重新計算干擾',
            },
            isOpen: showInterferenceModal,
            openModal: () => setShowInterferenceModal(true),
            closeModal: () => setShowInterferenceModal(false),
            lastUpdate: interferenceModalLastUpdate,
            setLastUpdate: setInterferenceModalLastUpdate,
            isLoading: interferenceIsLoadingForHeader,
            setIsLoading: setInterferenceIsLoadingForHeader,
            refreshHandlerRef: interferenceRefreshHandlerRef,
            ViewerComponent: InterferenceVisualization,
        },
        {
            id: 'aiDecision',
            menuText: 'AI 決策透明化',
            titleConfig: {
                base: 'AI-RAN 決策過程可視化',
                loading: '正在分析 AI 決策過程...',
                hoverRefresh: '重新分析決策',
            },
            isOpen: showAIDecisionModal,
            openModal: () => setShowAIDecisionModal(true),
            closeModal: () => setShowAIDecisionModal(false),
            lastUpdate: aiDecisionModalLastUpdate,
            setLastUpdate: setAIDecisionModalLastUpdate,
            isLoading: aiDecisionIsLoadingForHeader,
            setIsLoading: setAIDecisionIsLoadingForHeader,
            refreshHandlerRef: aiDecisionRefreshHandlerRef,
            ViewerComponent: AIDecisionVisualization,
        },
        {
            id: 'uavSwarm',
            menuText: 'UAV 群組協同',
            titleConfig: {
                base: 'UAV 群組 3D 軌跡和編隊顯示',
                loading: '正在計算 UAV 群組協同...',
                hoverRefresh: '重新載入 UAV 群組',
            },
            isOpen: showUAVSwarmModal,
            openModal: () => setShowUAVSwarmModal(true),
            closeModal: () => setShowUAVSwarmModal(false),
            lastUpdate: uavSwarmModalLastUpdate,
            setLastUpdate: setUAVSwarmModalLastUpdate,
            isLoading: uavSwarmIsLoadingForHeader,
            setIsLoading: setUAVSwarmIsLoadingForHeader,
            refreshHandlerRef: uavSwarmRefreshHandlerRef,
            ViewerComponent: UAVSwarmCoordinationViewer,
        },
        {
            id: 'meshNetwork',
            menuText: 'Mesh 網路拓撲',
            titleConfig: {
                base: 'Mesh 網路動態拓撲可視化',
                loading: '正在分析網路拓撲...',
                hoverRefresh: '重新分析拓撲',
            },
            isOpen: showMeshNetworkModal,
            openModal: () => setShowMeshNetworkModal(true),
            closeModal: () => setShowMeshNetworkModal(false),
            lastUpdate: meshNetworkModalLastUpdate,
            setLastUpdate: setMeshNetworkModalLastUpdate,
            isLoading: meshNetworkIsLoadingForHeader,
            setIsLoading: setMeshNetworkIsLoadingForHeader,
            refreshHandlerRef: meshNetworkRefreshHandlerRef,
            ViewerComponent: MeshNetworkTopologyViewer,
        },
        {
            id: 'frequencySpectrum',
            menuText: '頻譜分析',
            titleConfig: {
                base: '頻譜使用狀況和抗干擾效果',
                loading: '正在掃描頻譜...',
                hoverRefresh: '重新掃描頻譜',
            },
            isOpen: showFrequencySpectrumModal,
            openModal: () => setShowFrequencySpectrumModal(true),
            closeModal: () => setShowFrequencySpectrumModal(false),
            lastUpdate: frequencySpectrumModalLastUpdate,
            setLastUpdate: setFrequencySpectrumModalLastUpdate,
            isLoading: frequencySpectrumIsLoadingForHeader,
            setIsLoading: setFrequencySpectrumIsLoadingForHeader,
            refreshHandlerRef: frequencySpectrumRefreshHandlerRef,
            ViewerComponent: FrequencySpectrumVisualization,
        },
        {
            id: 'airanDecision',
            menuText: 'AI-RAN 進階決策',
            titleConfig: {
                base: 'AI-RAN 進階智能決策分析',
                loading: '正在分析 AI-RAN 決策...',
                hoverRefresh: '重新分析 AI-RAN',
            },
            isOpen: showAIRANDecisionModal,
            openModal: () => setShowAIRANDecisionModal(true),
            closeModal: () => setShowAIRANDecisionModal(false),
            lastUpdate: airanDecisionModalLastUpdate,
            setLastUpdate: setAIRANDecisionModalLastUpdate,
            isLoading: airanDecisionIsLoadingForHeader,
            setIsLoading: setAIRANDecisionIsLoadingForHeader,
            refreshHandlerRef: airanDecisionRefreshHandlerRef,
            ViewerComponent: AIRANDecisionVisualization,
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
    const hasActiveChart = modalConfigs.some((config) => config.isOpen)

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
                        {/* 圖表 Dropdown */}
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
                                圖表
                                <span className="dropdown-arrow-small">▼</span>
                            </span>
                            <div
                                className={`charts-dropdown ${
                                    isChartsDropdownOpen ? 'show' : ''
                                }`}
                            >
                                {modalConfigs.map((config) => (
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
                                onReportLastUpdateToNavbar={config.setLastUpdate}
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
        </>
    )
}

export default Navbar
