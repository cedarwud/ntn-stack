import { useState, useRef, useEffect } from 'react'
import type { FC, RefObject } from 'react'
import { useNavigate } from 'react-router-dom'
import '../../styles/Navbar.scss'

import MeasurementEventsModal from './MeasurementEventsModal'

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

    const [_isMobile, setIsMobile] = useState(false)

    // 新增 Measurement Events Modal 狀態
    const [showMeasurementEventsModal, setShowMeasurementEventsModal] =
        useState(false)

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

    const _modalConfigs: ModalConfig[] = []

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

                        {/* 3GPP A4 測量事件按鈕 - 專注於信號切換事件 */}
                        <li
                            className={`navbar-item ${
                                showMeasurementEventsModal ? 'active' : ''
                            }`}
                            onClick={() => setShowMeasurementEventsModal(true)}
                        >
                            📡 A4 信號切換
                        </li>

                        {/* D2 移動參考位置事件統一入口 */}
                        <li
                            className="navbar-item"
                            onClick={() => navigate('/d2-dashboard')}
                        >
                            📊 D2 事件監控
                        </li>
                    </ul>
                </div>
            </nav>

            {/* 測量事件模態框 */}
            <MeasurementEventsModal
                isOpen={showMeasurementEventsModal}
                onClose={() => setShowMeasurementEventsModal(false)}
            />
        </>
    )
}

export default Navbar
