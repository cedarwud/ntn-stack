/**
 * Enhanced A4 Viewer with View Mode Support
 * 支持簡易版/完整版模式的 A4 事件查看器
 * 
 * 示範如何將視圖模式系統集成到現有組件中
 */

import React, { useState, useCallback, useMemo } from 'react'
import { useViewModeManager } from '../../../../hooks/useViewModeManager'
import { ParameterDefinition, ParameterGroup } from '../../../common/EnhancedParameterPanel'
import ViewModeToggle, { CompactViewModeSwitch } from '../../../common/ViewModeToggle'
import EnhancedParameterPanel from '../../../common/EnhancedParameterPanel'

// A4 事件參數介面
interface A4EventParameters {
    // 基本參數 (簡易版)
    a4Threshold: number
    hysteresis: number
    currentTime: number
    
    // 標準參數
    useRealData: boolean
    uePosition: {
        latitude: number
        longitude: number  
        altitude: number
    }
    neighbour_satellite_id: string
    
    // 專家參數
    time_to_trigger: number
    report_config_id: string
    cell_individual_offset: number
    position_compensation: boolean
    signal_compensation_db: number
    updateInterval: number
    maxDataHistory: number
}

interface EnhancedA4ViewerWithModesProps {
    initialParameters?: Partial<A4EventParameters>
    onParameterChange?: (parameters: A4EventParameters) => void
    onTriggerEvent?: (eventData: any) => void
}

const EnhancedA4ViewerWithModes: React.FC<EnhancedA4ViewerWithModesProps> = ({
    initialParameters = {},
    onParameterChange,
    onTriggerEvent
}) => {
    // 初始化視圖模式管理器
    const viewModeManager = useViewModeManager({
        eventType: 'A4',
        defaultMode: 'simple',
        enableLocalStorage: true,
        onModeChange: (mode) => {
            console.log(`A4 Viewer 切換到 ${mode} 模式`)
        }
    })

    // 參數狀態
    const [parameters, setParameters] = useState<A4EventParameters>({
        // 預設值
        a4Threshold: 3.0,
        hysteresis: 1.0,
        currentTime: 0,
        useRealData: true,
        uePosition: {
            latitude: 25.0478,
            longitude: 121.5319,
            altitude: 100
        },
        neighbour_satellite_id: 'auto',
        time_to_trigger: 128,
        report_config_id: 'default',
        cell_individual_offset: 0,
        position_compensation: true,
        signal_compensation_db: 0,
        updateInterval: 2000,
        maxDataHistory: 100,
        ...initialParameters
    })

    // 參數定義配置
    const parameterDefinitions: ParameterDefinition[] = useMemo(() => [
        // 基本參數
        {
            name: 'a4Threshold',
            label: 'A4 門檻值',
            type: 'range',
            value: parameters.a4Threshold,
            min: 0.5,
            max: 10.0,
            step: 0.5,
            unit: 'dB',
            description: '鄰居細胞信號強度相對於服務細胞的門檻值',
            physicalMeaning: '值越小越容易觸發切換，影響網路切換的敏感度',
            category: 'basic',
            validation: (value: number) => {
                if (value < 0.5) return '門檻值不能小於 0.5dB'
                if (value > 10.0) return '門檻值不能大於 10.0dB'
                return null
            }
        },
        {
            name: 'hysteresis',
            label: '遲滯值',
            type: 'range',
            value: parameters.hysteresis,
            min: 0.0,
            max: 5.0,
            step: 0.1,
            unit: 'dB',
            description: '防止頻繁切換的遲滯邊界',
            physicalMeaning: '提供切換穩定性，避免在信號邊界附近反復切換',
            category: 'basic'
        },
        {
            name: 'currentTime',
            label: '當前時間',
            type: 'range',
            value: parameters.currentTime,
            min: 0,
            max: 300,
            step: 1,
            unit: 's',
            description: '仿真的當前時間點',
            category: 'basic'
        },
        
        // 標準參數
        {
            name: 'useRealData',
            label: '使用真實數據',
            type: 'boolean',
            value: parameters.useRealData,
            description: '使用真實軌道數據還是模擬數據',
            category: 'standard'
        },
        {
            name: 'uePosition.latitude',
            label: 'UE 緯度',
            type: 'number',
            value: parameters.uePosition.latitude,
            min: -90,
            max: 90,
            step: 0.0001,
            unit: '°',
            description: '用戶設備的地理緯度',
            category: 'standard'
        },
        {
            name: 'uePosition.longitude',
            label: 'UE 經度',
            type: 'number',
            value: parameters.uePosition.longitude,
            min: -180,
            max: 180,
            step: 0.0001,
            unit: '°',
            description: '用戶設備的地理經度',
            category: 'standard'
        },
        {
            name: 'neighbour_satellite_id',
            label: '鄰居衛星',
            type: 'select',
            value: parameters.neighbour_satellite_id,
            options: [
                { value: 'auto', label: '自動選擇' },
                { value: 'starlink_1234', label: 'Starlink-1234' },
                { value: 'starlink_1235', label: 'Starlink-1235' },
                { value: 'starlink_1236', label: 'Starlink-1236' }
            ],
            description: '指定的鄰居衛星 ID',
            category: 'standard'
        },
        
        // 專家參數
        {
            name: 'time_to_trigger',
            label: '觸發時間',
            type: 'select',
            value: parameters.time_to_trigger,
            options: [
                { value: 0, label: '0ms' },
                { value: 40, label: '40ms' },
                { value: 64, label: '64ms' },
                { value: 80, label: '80ms' },
                { value: 100, label: '100ms' },
                { value: 128, label: '128ms' },
                { value: 160, label: '160ms' },
                { value: 256, label: '256ms' },
                { value: 320, label: '320ms' },
                { value: 480, label: '480ms' },
                { value: 512, label: '512ms' },
                { value: 640, label: '640ms' }
            ],
            unit: 'ms',
            description: '事件觸發的時間延遲',
            category: 'expert'
        },
        {
            name: 'position_compensation',
            label: '位置補償',
            type: 'boolean',
            value: parameters.position_compensation,
            description: '啟用基於位置的信號強度補償',
            physicalMeaning: '補償衛星移動和用戶位置變化對信號測量的影響',
            category: 'expert'
        },
        {
            name: 'updateInterval',
            label: '更新間隔',
            type: 'range',
            value: parameters.updateInterval,
            min: 500,
            max: 5000,
            step: 100,
            unit: 'ms',
            description: '數據更新的時間間隔',
            category: 'expert'
        },
        {
            name: 'maxDataHistory',
            label: '最大數據點',
            type: 'range',
            value: parameters.maxDataHistory,
            min: 20,
            max: 500,
            step: 10,
            description: '圖表顯示的最大歷史數據點數量',
            category: 'expert'
        }
    ], [parameters])

    // 參數分組定義
    const parameterGroups: ParameterGroup[] = useMemo(() => [
        {
            name: 'basic',
            label: '基本參數',
            icon: '🎯',
            description: '核心的 A4 事件觸發參數',
            parameters: ['a4Threshold', 'hysteresis', 'currentTime'],
            defaultExpanded: true
        },
        {
            name: 'position',
            label: '位置配置',
            icon: '📍',
            description: 'UE 位置和鄰居衛星設定',
            parameters: ['uePosition.latitude', 'uePosition.longitude', 'neighbour_satellite_id'],
            defaultExpanded: viewModeManager.currentMode === 'advanced'
        },
        {
            name: 'advanced',
            label: '進階設定',
            icon: '⚙️',
            description: '專業用途的詳細參數配置',
            parameters: ['time_to_trigger', 'position_compensation', 'updateInterval', 'maxDataHistory'],
            defaultExpanded: false
        }
    ], [viewModeManager.currentMode])

    // 預設配置
    const presets = useMemo(() => [
        {
            name: 'urban',
            label: '城市環境',
            values: {
                a4Threshold: 2.0,
                hysteresis: 0.5,
                time_to_trigger: 128,
                position_compensation: true
            }
        },
        {
            name: 'rural',
            label: '郊區環境',
            values: {
                a4Threshold: 4.0,
                hysteresis: 1.5,
                time_to_trigger: 256,
                position_compensation: false
            }
        },
        {
            name: 'mobile',
            label: '高速移動',
            values: {
                a4Threshold: 3.0,
                hysteresis: 1.0,
                time_to_trigger: 64,
                position_compensation: true
            }
        }
    ], [])

    // 處理參數變更
    const handleParameterChange = useCallback((name: string, value: any) => {
        setParameters(prev => {
            let newParams = { ...prev }
            
            // 處理嵌套屬性 (如 uePosition.latitude)
            if (name.includes('.')) {
                const [parent, child] = name.split('.')
                newParams = {
                    ...newParams,
                    [parent]: {
                        ...newParams[parent as keyof A4EventParameters],
                        [child]: value
                    }
                }
            } else {
                newParams = {
                    ...newParams,
                    [name]: value
                }
            }
            
            // 通知父組件
            if (onParameterChange) {
                onParameterChange(newParams)
            }
            
            return newParams
        })
    }, [onParameterChange])

    // 處理驗證錯誤
    const handleValidationError = useCallback((errors: Record<string, string>) => {
        console.warn('A4 參數驗證錯誤:', errors)
    }, [])

    return (
        <div className="h-full flex flex-col bg-white">
            {/* 標題列 */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <div className="flex items-center space-x-3">
                    <h1 className="text-xl font-semibold text-gray-900">
                        A4 事件測量
                    </h1>
                    <CompactViewModeSwitch viewModeManager={viewModeManager} />
                </div>
                
                <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                        當前模式: {viewModeManager.currentMode === 'simple' ? '簡易版' : '完整版'}
                    </span>
                </div>
            </div>

            {/* 主要內容區 */}
            <div className="flex-1 flex overflow-hidden">
                {/* 參數面板 */}
                <div className="w-80 bg-gray-50 border-r border-gray-200 overflow-y-auto">
                    <EnhancedParameterPanel
                        eventType="A4"
                        parameters={parameterDefinitions}
                        groups={parameterGroups}
                        viewModeManager={viewModeManager}
                        onChange={handleParameterChange}
                        onValidationError={handleValidationError}
                        className="p-4"
                        showResetButton={true}
                        showPresets={viewModeManager.currentMode === 'advanced'}
                        presets={presets}
                    />
                </div>

                {/* 圖表區域 */}
                <div className="flex-1 relative">
                    {/* 模式切換浮動按鈕 */}
                    <ViewModeToggle
                        viewModeManager={viewModeManager}
                        size="medium"
                        showLabel={true}
                        showDescription={viewModeManager.currentMode === 'simple'}
                        enableKeyboardShortcut={true}
                        position="top-right"
                    />

                    {/* 圖表內容 */}
                    <div className="h-full p-6">
                        <div className="h-full bg-gray-100 rounded-lg flex items-center justify-center">
                            <div className="text-center">
                                <h3 className="text-lg font-medium text-gray-700 mb-2">
                                    A4 事件圖表區域
                                </h3>
                                <p className="text-sm text-gray-500">
                                    當前參數: 門檻值 {parameters.a4Threshold}dB, 
                                    遲滯值 {parameters.hysteresis}dB
                                </p>
                                <p className="text-xs text-gray-400 mt-2">
                                    模式: {viewModeManager.currentMode === 'simple' ? '簡易版' : '完整版'} |
                                    參數級別: {viewModeManager.config.parameters.level} |
                                    更新間隔: {viewModeManager.config.performance.updateInterval}ms
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 狀態欄 */}
            <div className="px-4 py-2 bg-gray-100 border-t border-gray-200 text-xs text-gray-600">
                <div className="flex items-center justify-between">
                    <span>
                        UE 位置: {parameters.uePosition.latitude.toFixed(4)}°, {parameters.uePosition.longitude.toFixed(4)}°
                    </span>
                    <span>
                        鄰居衛星: {parameters.neighbour_satellite_id}
                    </span>
                    <span>
                        觸發時間: {parameters.time_to_trigger}ms
                    </span>
                </div>
            </div>
        </div>
    )
}

export default EnhancedA4ViewerWithModes