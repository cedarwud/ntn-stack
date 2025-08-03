/**
 * 統一視圖模式切換組件
 * 實現簡易版/完整版模式的切換界面
 *
 * 功能：
 * - 模式切換按鈕
 * - 模式狀態指示
 * - 模式說明提示
 * - 快捷鍵支援
 */

import React, { useCallback, useEffect } from 'react'
import { ViewModeManager } from '../../types/measurement-view-modes'

interface ViewModeToggleProps {
    viewModeManager: ViewModeManager
    size?: 'small' | 'medium' | 'large'
    showLabel?: boolean
    showDescription?: boolean
    enableKeyboardShortcut?: boolean
    position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
    className?: string
    style?: React.CSSProperties
}

const ViewModeToggle: React.FC<ViewModeToggleProps> = ({
    viewModeManager,
    size = 'medium',
    showLabel = true,
    showDescription = false,
    enableKeyboardShortcut = true,
    position = 'top-right',
    className = '',
    style = {},
}) => {
    const { currentMode, toggleMode, config } = viewModeManager

    // 鍵盤快捷鍵處理
    const handleKeyboardShortcut = useCallback(
        (event: KeyboardEvent) => {
            // Ctrl/Cmd + Shift + M 切換模式
            if (
                enableKeyboardShortcut &&
                (event.ctrlKey || event.metaKey) &&
                event.shiftKey &&
                event.key === 'M'
            ) {
                event.preventDefault()
                toggleMode()
            }
        },
        [enableKeyboardShortcut, toggleMode]
    )

    // 註冊鍵盤監聽
    useEffect(() => {
        if (enableKeyboardShortcut) {
            document.addEventListener('keydown', handleKeyboardShortcut)
            return () => {
                document.removeEventListener('keydown', handleKeyboardShortcut)
            }
        }
    }, [enableKeyboardShortcut, handleKeyboardShortcut])

    // 模式顯示配置
    const modeConfig = {
        simple: {
            icon: '🔰',
            label: '簡易版',
            description: '簡化介面，專注核心功能，適合初學者使用',
            bgColor: 'bg-green-100 hover:bg-green-200',
            textColor: 'text-green-800',
            borderColor: 'border-green-300',
        },
        advanced: {
            icon: '⚡',
            label: '完整版',
            description: '完整功能，詳細參數，適合專業開發和研究使用',
            bgColor: 'bg-blue-100 hover:bg-blue-200',
            textColor: 'text-blue-800',
            borderColor: 'border-blue-300',
        },
    }

    const current = modeConfig[currentMode]
    const next = modeConfig[currentMode === 'simple' ? 'advanced' : 'simple']

    // 尺寸配置
    const sizeConfig = {
        small: {
            button: 'px-2 py-1 text-xs',
            icon: 'text-sm',
            label: 'text-xs',
        },
        medium: {
            button: 'px-3 py-2 text-sm',
            icon: 'text-base',
            label: 'text-sm',
        },
        large: {
            button: 'px-4 py-3 text-base',
            icon: 'text-lg',
            label: 'text-base',
        },
    }

    // 位置配置
    const positionConfig = {
        'top-left': 'top-4 left-4',
        'top-right': 'top-4 right-4',
        'bottom-left': 'bottom-4 left-4',
        'bottom-right': 'bottom-4 right-4',
    }

    const currentSize = sizeConfig[size]

    return (
        <div
            className={`
                fixed ${positionConfig[position]} z-50
                ${className}
            `}
            style={style}
        >
            <div className="flex flex-col items-end space-y-2">
                {/* 模式切換按鈕 */}
                <button
                    onClick={toggleMode}
                    className={`
                        ${currentSize.button}
                        ${current.bgColor}
                        ${current.textColor}
                        ${current.borderColor}
                        border-2 rounded-lg
                        flex items-center space-x-2
                        transition-all duration-200
                        hover:shadow-md
                        focus:outline-none focus:ring-2 focus:ring-offset-2
                        focus:ring-blue-500
                        font-medium
                    `}
                    title={`切換到${next.label} (${
                        enableKeyboardShortcut ? 'Ctrl+Shift+M' : '點擊切換'
                    })`}
                >
                    <span className={`${currentSize.icon}`}>
                        {current.icon}
                    </span>
                    {showLabel && (
                        <span className={currentSize.label}>
                            {current.label}
                        </span>
                    )}
                    <span className={`${currentSize.icon} opacity-50`}>→</span>
                    <span className={`${currentSize.icon} opacity-75`}>
                        {next.icon}
                    </span>
                </button>

                {/* 模式說明 */}
                {showDescription && (
                    <div
                        className={`
                        max-w-xs p-3 rounded-lg shadow-lg
                        bg-white border border-gray-200
                        text-sm text-gray-700
                    `}
                    >
                        <div className="font-semibold mb-1 flex items-center space-x-1">
                            <span>{current.icon}</span>
                            <span>{current.label}</span>
                        </div>
                        <p className="text-xs text-gray-600 mb-2">
                            {current.description}
                        </p>
                        <div className="text-xs text-gray-500">
                            <div>參數級別: {config.parameters.level}</div>
                            <div>
                                更新間隔: {config.performance.updateInterval}ms
                            </div>
                            {enableKeyboardShortcut && (
                                <div className="mt-1 text-blue-600">
                                    快捷鍵: Ctrl+Shift+M
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default ViewModeToggle

// 便利組件：內聯模式切換
export const InlineViewModeToggle: React.FC<{
    viewModeManager: ViewModeManager
    size?: 'small' | 'medium' | 'large'
}> = ({ viewModeManager, size = 'small' }) => {
    const { currentMode, toggleMode } = viewModeManager

    const modeConfig = {
        simple: { icon: '🔰', label: '簡易版', color: 'text-green-600' },
        advanced: { icon: '⚡', label: '完整版', color: 'text-blue-600' },
    }

    const current = modeConfig[currentMode]

    return (
        <button
            onClick={toggleMode}
            className={`
                inline-flex items-center space-x-1 px-2 py-1 rounded
                text-${size === 'small' ? 'xs' : 'sm'}
                ${current.color}
                hover:bg-gray-100 transition-colors duration-200
                focus:outline-none focus:ring-1 focus:ring-gray-300
            `}
            title="切換視圖模式"
        >
            <span>{current.icon}</span>
            <span>{current.label}</span>
        </button>
    )
}

// 便利組件：簡潔切換開關
export const CompactViewModeSwitch: React.FC<{
    viewModeManager: ViewModeManager
}> = ({ viewModeManager }) => {
    const { currentMode, toggleMode } = viewModeManager

    return (
        <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500">簡易</span>
            <button
                onClick={toggleMode}
                className={`
                    relative inline-flex h-6 w-11 items-center rounded-full
                    transition-colors duration-200 ease-in-out
                    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
                    ${currentMode === 'simple' ? 'bg-green-600' : 'bg-blue-600'}
                `}
            >
                <span
                    className={`
                        inline-block h-4 w-4 rounded-full bg-white transition-transform duration-200 ease-in-out
                        ${
                            currentMode === 'simple'
                                ? 'translate-x-1'
                                : 'translate-x-6'
                        }
                    `}
                />
            </button>
            <span className="text-xs text-gray-500">完整</span>
        </div>
    )
}
