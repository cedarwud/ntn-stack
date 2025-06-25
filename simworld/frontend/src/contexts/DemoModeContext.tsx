/**
 * 全域演示模式上下文
 * 
 * 提供全域的演示模式開關，控制所有組件在真實數據模式和演示數據模式之間切換
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export interface DemoModeContextType {
    // 模式狀態
    isDemoMode: boolean
    dataSource: 'real' | 'demo' | 'hybrid'
    
    // 控制函數
    setDemoMode: (enabled: boolean) => void
    setDataSource: (source: 'real' | 'demo' | 'hybrid') => void
    
    // 組件特定開關
    componentSettings: {
        satelliteRendering: 'real' | 'demo' | 'hybrid'
        handoverSystem: 'real' | 'demo' | 'hybrid'
        sinrHeatmap: 'real' | 'demo' | 'hybrid'
        performanceMetrics: 'real' | 'demo' | 'hybrid'
        interferenceVisualization: 'real' | 'demo' | 'hybrid'
        aiRanSystem: 'real' | 'demo' | 'hybrid'
    }
    
    // 組件設定更新
    updateComponentSetting: (
        component: keyof DemoModeContextType['componentSettings'], 
        mode: 'real' | 'demo' | 'hybrid'
    ) => void
    
    // 批量切換
    switchAllToDemo: () => void
    switchAllToReal: () => void
    switchAllToHybrid: () => void
    
    // 狀態指示
    getStatusText: () => string
    getStatusColor: () => string
}

const DemoModeContext = createContext<DemoModeContextType | undefined>(undefined)

interface DemoModeProviderProps {
    children: ReactNode
}

export const DemoModeProvider: React.FC<DemoModeProviderProps> = ({ children }) => {
    // 主要狀態
    const [isDemoMode, setIsDemoMode] = useState<boolean>(false) // 預設為真實模式
    const [dataSource, setDataSourceState] = useState<'real' | 'demo' | 'hybrid'>('real')
    
    // 組件特定設定
    const [componentSettings, setComponentSettings] = useState({
        satelliteRendering: 'hybrid' as 'real' | 'demo' | 'hybrid',
        handoverSystem: 'real' as 'real' | 'demo' | 'hybrid',
        sinrHeatmap: 'real' as 'real' | 'demo' | 'hybrid',
        performanceMetrics: 'real' as 'real' | 'demo' | 'hybrid',
        interferenceVisualization: 'real' as 'real' | 'demo' | 'hybrid',
        aiRanSystem: 'real' as 'real' | 'demo' | 'hybrid',
    })
    
    // 從 localStorage 加載設定
    useEffect(() => {
        try {
            const savedDemoMode = localStorage.getItem('simworld-demo-mode')
            const savedDataSource = localStorage.getItem('simworld-data-source')
            const savedComponentSettings = localStorage.getItem('simworld-component-settings')
            
            if (savedDemoMode !== null) {
                setIsDemoMode(JSON.parse(savedDemoMode))
            }
            
            if (savedDataSource) {
                setDataSourceState(savedDataSource as 'real' | 'demo' | 'hybrid')
            }
            
            if (savedComponentSettings) {
                setComponentSettings(JSON.parse(savedComponentSettings))
            }
        } catch (error) {
            console.warn('加載演示模式設定失敗:', error)
        }
    }, [])
    
    // 保存設定到 localStorage
    const saveToLocalStorage = (
        demoMode: boolean,
        source: 'real' | 'demo' | 'hybrid',
        settings: typeof componentSettings
    ) => {
        try {
            localStorage.setItem('simworld-demo-mode', JSON.stringify(demoMode))
            localStorage.setItem('simworld-data-source', source)
            localStorage.setItem('simworld-component-settings', JSON.stringify(settings))
        } catch (error) {
            console.warn('保存演示模式設定失敗:', error)
        }
    }
    
    // 設定演示模式
    const setDemoMode = (enabled: boolean) => {
        setIsDemoMode(enabled)
        const newSource = enabled ? 'demo' : 'real'
        setDataSourceState(newSource)
        saveToLocalStorage(enabled, newSource, componentSettings)
        
        console.log(`🎭 演示模式已${enabled ? '啟用' : '停用'}，數據源切換為: ${newSource}`)
    }
    
    // 設定數據源
    const setDataSource = (source: 'real' | 'demo' | 'hybrid') => {
        setDataSourceState(source)
        setIsDemoMode(source === 'demo')
        saveToLocalStorage(source === 'demo', source, componentSettings)
        
        console.log(`📊 數據源已切換為: ${source}`)
    }
    
    // 更新組件設定
    const updateComponentSetting = (
        component: keyof typeof componentSettings,
        mode: 'real' | 'demo' | 'hybrid'
    ) => {
        const newSettings = {
            ...componentSettings,
            [component]: mode
        }
        setComponentSettings(newSettings)
        saveToLocalStorage(isDemoMode, dataSource, newSettings)
        
        console.log(`🔧 ${component} 數據模式已設為: ${mode}`)
    }
    
    // 批量切換函數
    const switchAllToDemo = () => {
        const demoSettings = Object.keys(componentSettings).reduce((acc, key) => {
            acc[key as keyof typeof componentSettings] = 'demo'
            return acc
        }, {} as typeof componentSettings)
        
        setComponentSettings(demoSettings)
        setDemoMode(true)
        console.log('🎭 所有組件已切換為演示模式')
    }
    
    const switchAllToReal = () => {
        const realSettings = Object.keys(componentSettings).reduce((acc, key) => {
            acc[key as keyof typeof componentSettings] = 'real'
            return acc
        }, {} as typeof componentSettings)
        
        setComponentSettings(realSettings)
        setDemoMode(false)
        console.log('📊 所有組件已切換為真實數據模式')
    }
    
    const switchAllToHybrid = () => {
        const hybridSettings = Object.keys(componentSettings).reduce((acc, key) => {
            acc[key as keyof typeof componentSettings] = 'hybrid'
            return acc
        }, {} as typeof componentSettings)
        
        setComponentSettings(hybridSettings)
        setDataSource('hybrid')
        console.log('🔀 所有組件已切換為混合模式')
    }
    
    // 狀態指示函數
    const getStatusText = (): string => {
        if (dataSource === 'real') return '真實數據模式'
        if (dataSource === 'demo') return '演示數據模式'
        if (dataSource === 'hybrid') return '混合數據模式'
        return '未知模式'
    }
    
    const getStatusColor = (): string => {
        if (dataSource === 'real') return '#00ff00'      // 綠色
        if (dataSource === 'demo') return '#ff6600'      // 橙色
        if (dataSource === 'hybrid') return '#ffff00'    // 黃色
        return '#ff0000'                                 // 紅色（錯誤）
    }
    
    const contextValue: DemoModeContextType = {
        isDemoMode,
        dataSource,
        setDemoMode,
        setDataSource,
        componentSettings,
        updateComponentSetting,
        switchAllToDemo,
        switchAllToReal,
        switchAllToHybrid,
        getStatusText,
        getStatusColor,
    }
    
    return (
        <DemoModeContext.Provider value={contextValue}>
            {children}
        </DemoModeContext.Provider>
    )
}

// 自定義 Hook
export const useDemoMode = (): DemoModeContextType => {
    const context = useContext(DemoModeContext)
    if (context === undefined) {
        throw new Error('useDemoMode must be used within a DemoModeProvider')
    }
    return context
}

// 輔助 Hook：獲取特定組件的數據模式
export const useComponentDataMode = (
    component: keyof DemoModeContextType['componentSettings']
): 'real' | 'demo' | 'hybrid' => {
    const { componentSettings } = useDemoMode()
    return componentSettings[component]
}

// 輔助 Hook：判斷是否應該使用真實數據
export const useShouldUseRealData = (
    component: keyof DemoModeContextType['componentSettings']
): boolean => {
    const mode = useComponentDataMode(component)
    return mode === 'real' || mode === 'hybrid'
}

export default DemoModeContext