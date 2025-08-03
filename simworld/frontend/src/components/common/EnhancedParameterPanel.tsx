/**
 * 增強參數面板組件
 * 支持簡易版/完整版模式的參數顯示和控制
 *
 * 功能：
 * - 根據視圖模式過濾參數
 * - 參數分組和組織
 * - 教育模式支援
 * - 實時驗證和提示
 */

import React, { useState, useMemo, useCallback } from 'react'
import {
    ViewModeManager,
    useVisibleParameters,
    useEducationMode,
} from '../../hooks/useViewModeManager'

// 參數定義介面
export interface ParameterDefinition {
    name: string
    label: string
    type: 'number' | 'string' | 'boolean' | 'select' | 'range'
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    value: any
    min?: number
    max?: number
    step?: number
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    options?: Array<{ value: any; label: string }>
    unit?: string
    description?: string
    physicalMeaning?: string
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    validation?: (value: any) => string | null
    category?: string
    dependency?: string[] // 依賴其他參數
}

// 參數分組定義
export interface ParameterGroup {
    name: string
    label: string
    icon?: string
    description?: string
    parameters: string[]
    collapsible?: boolean
    defaultExpanded?: boolean
}

interface EnhancedParameterPanelProps {
    eventType: string
    parameters: ParameterDefinition[]
    groups?: ParameterGroup[]
    viewModeManager: ViewModeManager
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    onChange: (name: string, value: any) => void
    onValidationError?: (errors: Record<string, string>) => void
    className?: string
    showResetButton?: boolean
    showPresets?: boolean
    presets?: Array<{
        name: string
        label: string
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        values: Record<string, any>
    }>
}

const EnhancedParameterPanel: React.FC<EnhancedParameterPanelProps> = ({
    eventType,
    parameters,
    groups = [],
    viewModeManager,
    onChange,
    onValidationError,
    className = '',
    showResetButton = true,
    showPresets = false,
    presets = [],
}) => {
    const educationMode = useEducationMode(viewModeManager)
    const { config } = viewModeManager

    // 獲取可見參數
    const visibleParameters = useVisibleParameters(
        eventType,
        parameters.map((p) => p.name),
        viewModeManager
    )

    // 過濾可見的參數定義
    const visibleParameterDefs = useMemo(() => {
        return parameters.filter((param) =>
            visibleParameters.includes(param.name)
        )
    }, [parameters, visibleParameters])

    // 驗證狀態
    const [validationErrors, setValidationErrors] = useState<
        Record<string, string>
    >({})
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
        new Set(
            groups.filter((g) => g.defaultExpanded !== false).map((g) => g.name)
        )
    )

    // 參數分組
    const parametersByGroup = useMemo(() => {
        const grouped: Record<string, ParameterDefinition[]> = {}
        const ungrouped: ParameterDefinition[] = []

        // 初始化分組
        groups.forEach((group) => {
            grouped[group.name] = []
        })

        // 分配參數到分組
        visibleParameterDefs.forEach((param) => {
            const group = groups.find((g) => g.parameters.includes(param.name))
            if (group) {
                grouped[group.name].push(param)
            } else {
                ungrouped.push(param)
            }
        })

        // 如果有未分組的參數，創建預設分組
        if (ungrouped.length > 0) {
            grouped['_default'] = ungrouped
        }

        return grouped
    }, [visibleParameterDefs, groups])

    // 處理參數變更
    const handleParameterChange = useCallback(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (name: string, value: any) => {
            const param = parameters.find((p) => p.name === name)
            if (!param) return

            // 驗證
            let error: string | null = null
            if (param.validation) {
                error = param.validation(value)
            }

            // 基本範圍驗證
            if (!error && param.type === 'number') {
                if (param.min !== undefined && value < param.min) {
                    error = `值不能小於 ${param.min}`
                }
                if (param.max !== undefined && value > param.max) {
                    error = `值不能大於 ${param.max}`
                }
            }

            // 更新驗證狀態
            setValidationErrors((prev) => {
                const newErrors = { ...prev }
                if (error) {
                    newErrors[name] = error
                } else {
                    delete newErrors[name]
                }

                // 通知父組件
                if (onValidationError) {
                    onValidationError(newErrors)
                }

                return newErrors
            })

            // 如果沒有錯誤，更新值
            if (!error) {
                onChange(name, value)
            }
        },
        [parameters, onChange, onValidationError]
    )

    // 切換分組展開狀態
    const toggleGroup = useCallback((groupName: string) => {
        setExpandedGroups((prev) => {
            const newSet = new Set(prev)
            if (newSet.has(groupName)) {
                newSet.delete(groupName)
            } else {
                newSet.add(groupName)
            }
            return newSet
        })
    }, [])

    // 應用預設值
    const applyPreset = useCallback(
        (preset: (typeof presets)[0]) => {
            Object.entries(preset.values).forEach(([name, value]) => {
                if (visibleParameters.includes(name)) {
                    handleParameterChange(name, value)
                }
            })
        },
        [visibleParameters, handleParameterChange]
    )

    // 重置所有參數
    const resetParameters = useCallback(() => {
        // 這裡需要父組件提供初始值
        setValidationErrors({})
        // 父組件應該處理實際的重置邏輯
    }, [])

    // 渲染單個參數控制
    const renderParameter = useCallback(
        (param: ParameterDefinition) => {
            const hasError = validationErrors[param.name]
            const showEducation =
                educationMode.enabled &&
                (educationMode.showDescriptions ||
                    educationMode.showPhysicalMeaning)

            return (
                <div key={param.name} className="space-y-2">
                    {/* 參數標籤和說明 */}
                    <div className="flex items-center justify-between">
                        <label className="text-sm font-medium text-gray-700 flex items-center space-x-1">
                            <span>{param.label}</span>
                            {param.unit && (
                                <span className="text-xs text-gray-500">
                                    ({param.unit})
                                </span>
                            )}
                            {hasError && (
                                <span className="text-red-500 text-xs">⚠️</span>
                            )}
                        </label>

                        {showEducation && param.description && (
                            <button
                                className="text-blue-500 hover:text-blue-700 text-xs"
                                title={param.description}
                            >
                                ℹ️
                            </button>
                        )}
                    </div>

                    {/* 參數控制 */}
                    <div className="space-y-1">
                        {param.type === 'number' && (
                            <input
                                type="number"
                                value={param.value}
                                min={param.min}
                                max={param.max}
                                step={param.step}
                                onChange={(e) =>
                                    handleParameterChange(
                                        param.name,
                                        Number(e.target.value)
                                    )
                                }
                                className={`
                                w-full px-3 py-2 border rounded-md text-sm
                                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                                ${
                                    hasError
                                        ? 'border-red-300 bg-red-50'
                                        : 'border-gray-300'
                                }
                            `}
                            />
                        )}

                        {param.type === 'range' && (
                            <div className="space-y-1">
                                <input
                                    type="range"
                                    value={param.value}
                                    min={param.min}
                                    max={param.max}
                                    step={param.step}
                                    onChange={(e) =>
                                        handleParameterChange(
                                            param.name,
                                            Number(e.target.value)
                                        )
                                    }
                                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                                />
                                <div className="flex justify-between text-xs text-gray-500">
                                    <span>{param.min}</span>
                                    <span className="font-medium">
                                        {param.value}
                                    </span>
                                    <span>{param.max}</span>
                                </div>
                            </div>
                        )}

                        {param.type === 'boolean' && (
                            <div className="flex items-center space-x-2">
                                <input
                                    type="checkbox"
                                    checked={param.value}
                                    onChange={(e) =>
                                        handleParameterChange(
                                            param.name,
                                            e.target.checked
                                        )
                                    }
                                    className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                                />
                                <span className="text-sm text-gray-600">
                                    啟用
                                </span>
                            </div>
                        )}

                        {param.type === 'select' && param.options && (
                            <select
                                value={param.value}
                                onChange={(e) =>
                                    handleParameterChange(
                                        param.name,
                                        e.target.value
                                    )
                                }
                                className={`
                                w-full px-3 py-2 border rounded-md text-sm
                                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                                ${
                                    hasError
                                        ? 'border-red-300 bg-red-50'
                                        : 'border-gray-300'
                                }
                            `}
                            >
                                {param.options.map((option) => (
                                    <option
                                        key={option.value}
                                        value={option.value}
                                    >
                                        {option.label}
                                    </option>
                                ))}
                            </select>
                        )}

                        {param.type === 'string' && (
                            <input
                                type="text"
                                value={param.value}
                                onChange={(e) =>
                                    handleParameterChange(
                                        param.name,
                                        e.target.value
                                    )
                                }
                                className={`
                                w-full px-3 py-2 border rounded-md text-sm
                                focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                                ${
                                    hasError
                                        ? 'border-red-300 bg-red-50'
                                        : 'border-gray-300'
                                }
                            `}
                            />
                        )}
                    </div>

                    {/* 錯誤訊息 */}
                    {hasError && (
                        <p className="text-red-600 text-xs">{hasError}</p>
                    )}

                    {/* 教育模式說明 */}
                    {showEducation && (
                        <div className="text-xs text-gray-600 space-y-1">
                            {educationMode.showDescriptions &&
                                param.description && <p>{param.description}</p>}
                            {educationMode.showPhysicalMeaning &&
                                param.physicalMeaning && (
                                    <p className="italic">
                                        💡 {param.physicalMeaning}
                                    </p>
                                )}
                        </div>
                    )}
                </div>
            )
        },
        [validationErrors, educationMode, handleParameterChange]
    )

    // 渲染參數分組
    const renderGroup = useCallback(
        (groupName: string, groupDef?: ParameterGroup) => {
            const groupParams = parametersByGroup[groupName] || []
            if (groupParams.length === 0) return null

            const isExpanded = expandedGroups.has(groupName)
            const isCollapsible = groupDef?.collapsible !== false

            return (
                <div
                    key={groupName}
                    className="border border-gray-200 rounded-lg"
                >
                    {/* 分組標題 */}
                    {groupName !== '_default' && (
                        <div
                            className={`
                            px-4 py-3 bg-gray-50 border-b border-gray-200
                            ${
                                isCollapsible
                                    ? 'cursor-pointer hover:bg-gray-100'
                                    : ''
                            }
                            flex items-center justify-between
                        `}
                            onClick={
                                isCollapsible
                                    ? () => toggleGroup(groupName)
                                    : undefined
                            }
                        >
                            <div className="flex items-center space-x-2">
                                {groupDef?.icon && <span>{groupDef.icon}</span>}
                                <h3 className="text-sm font-medium text-gray-900">
                                    {groupDef?.label || groupName}
                                </h3>
                                {groupDef?.description &&
                                    educationMode.showDescriptions && (
                                        <span className="text-xs text-gray-500">
                                            - {groupDef.description}
                                        </span>
                                    )}
                            </div>
                            {isCollapsible && (
                                <span
                                    className={`transform transition-transform ${
                                        isExpanded ? 'rotate-180' : ''
                                    }`}
                                >
                                    ▼
                                </span>
                            )}
                        </div>
                    )}

                    {/* 分組內容 */}
                    {(!isCollapsible || isExpanded) && (
                        <div className="p-4 space-y-4">
                            {groupParams.map(renderParameter)}
                        </div>
                    )}
                </div>
            )
        },
        [
            parametersByGroup,
            expandedGroups,
            educationMode.showDescriptions,
            toggleGroup,
            renderParameter,
        ]
    )

    return (
        <div className={`space-y-4 ${className}`}>
            {/* 工具列 */}
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                    參數配置
                    <span className="ml-2 text-sm text-gray-500">
                        ({config.parameters.level} 模式)
                    </span>
                </h2>

                <div className="flex items-center space-x-2">
                    {/* 預設值選擇 */}
                    {showPresets && presets.length > 0 && (
                        <select
                            onChange={(e) => {
                                const preset = presets.find(
                                    (p) => p.name === e.target.value
                                )
                                if (preset) applyPreset(preset)
                            }}
                            defaultValue=""
                            className="text-xs px-2 py-1 border border-gray-300 rounded"
                        >
                            <option value="">選擇預設...</option>
                            {presets.map((preset) => (
                                <option key={preset.name} value={preset.name}>
                                    {preset.label}
                                </option>
                            ))}
                        </select>
                    )}

                    {/* 重置按鈕 */}
                    {showResetButton && (
                        <button
                            onClick={resetParameters}
                            className="text-xs px-3 py-1 text-gray-600 hover:text-gray-800 border border-gray-300 rounded hover:bg-gray-50"
                        >
                            重置
                        </button>
                    )}
                </div>
            </div>

            {/* 參數面板 */}
            <div className="space-y-3">
                {/* 渲染已定義的分組 */}
                {groups.map((group) => renderGroup(group.name, group))}

                {/* 渲染未分組的參數 */}
                {renderGroup('_default')}
            </div>

            {/* 驗證摘要 */}
            {Object.keys(validationErrors).length > 0 && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="text-sm font-medium text-red-800 mb-2">
                        參數驗證錯誤：
                    </h4>
                    <ul className="text-xs text-red-700 space-y-1">
                        {Object.entries(validationErrors).map(
                            ([name, error]) => (
                                <li key={name}>
                                    • {name}: {error}
                                </li>
                            )
                        )}
                    </ul>
                </div>
            )}
        </div>
    )
}

export default EnhancedParameterPanel
