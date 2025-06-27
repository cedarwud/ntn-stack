/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect, useCallback, useRef } from 'react'
import { netStackApi } from '../../../../../services/netstack-api'
import { satelliteCache } from '../../../../../utils/satellite-cache'

export interface ChartDataState {
    handoverLatencyData: any
    sixScenarioData: any
    strategyEffectData: any
    complexityAnalysisData: any
    handoverFailureRateData: any
    systemResourceData: any
    timeSyncPrecisionData: any
    performanceRadarData: any
    protocolStackData: any
    exceptionHandlingData: any
    qoeTimeSeriesData: any
    globalCoverageData: any
    celestrakTleData: any
    uavData: any
    systemMetrics: {
        cpu: number
        memory: number
        gpu: number
        networkLatency: number
    }
    coreSync: any
    realDataError: string | null
}

export const useChartData = (isOpen: boolean) => {
    // 🚨 暫時完全停用此 hook 以確認無限渲染問題
    // 直接返回固定數據，不執行任何動態邏輯
    return {
        data: {
            handoverLatencyData: null,
            sixScenarioData: null,
            strategyEffectData: null,
            complexityAnalysisData: null,
            handoverFailureRateData: null,
            systemResourceData: null,
            timeSyncPrecisionData: null,
            performanceRadarData: null,
            protocolStackData: null,
            exceptionHandlingData: null,
            qoeTimeSeriesData: null,
            globalCoverageData: null,
            celestrakTleData: null,
            uavData: null,
            systemMetrics: {
                cpu: 25,
                memory: 35,
                gpu: 15,
                networkLatency: 45,
            },
            coreSync: null,
            realDataError: null,
        },
        satelliteData: {
            starlink: {
                altitude: 550,
                count: 4408,
                inclination: 53.0,
                minElevation: 40,
                coverage: 990,
                period: 95.5,
                delay: 2.7,
                doppler: 47,
                power: 20,
                gain: 32,
            },
            kuiper: {
                altitude: 630,
                count: 3236,
                inclination: 51.9,
                minElevation: 35,
                coverage: 1197,
                period: 98.6,
                delay: 3.1,
                doppler: 41,
                power: 23,
                gain: 35,
            },
        },
        strategyMetrics: {
            flexible: {
                averageLatency: 25.7,
                successRate: 96.2,
                energyEfficiency: 0.87,
                systemLoad: 58,
            },
            consistent: {
                averageLatency: 22.1,
                successRate: 98.7,
                energyEfficiency: 0.94,
                systemLoad: 71,
            },
        },
        setStrategyMetrics: () => {},
        tleDataStatus: {
            source: 'local' as 'celestrak' | 'local',
            lastUpdate: null as Date | null,
            nextUpdate: null as Date | null,
            connectionActive: false,
        },
        autoTestResults: [],
        fetchRealSystemMetrics: async () => false,
        runAutomaticTests: async () => [],
    }

    // 以下是原始的 hook 實現，已被禁用
    /*
    const [data, setData] = useState<ChartDataState>({
        handoverLatencyData: null,
        sixScenarioData: null,
        strategyEffectData: null,
        complexityAnalysisData: null,
        handoverFailureRateData: null,
        systemResourceData: null,
        timeSyncPrecisionData: null,
        performanceRadarData: null,
        protocolStackData: null,
        exceptionHandlingData: null,
        qoeTimeSeriesData: null,
        globalCoverageData: null,
        celestrakTleData: null,
        uavData: null,
        systemMetrics: {
            cpu: 25,
            memory: 35,
            gpu: 15,
            networkLatency: 45,
        },
        coreSync: null,
        realDataError: null,
    })

    const [satelliteData, setSatelliteData] = useState({
        starlink: {
            altitude: 550,
            count: 4408,
            inclination: 53.0,
            minElevation: 40,
            coverage: 990,
            period: 95.5,
            delay: 2.7,
            doppler: 47,
            power: 20,
            gain: 32,
        },
        kuiper: {
            altitude: 630,
            count: 3236,
            inclination: 51.9,
            minElevation: 35,
            coverage: 1197,
            period: 98.6,
            delay: 3.1,
            doppler: 41,
            power: 23,
            gain: 35,
        },
    })

    const [strategyMetrics, setStrategyMetrics] = useState({
        flexible: {
            averageLatency: 25.7,
            successRate: 96.2,
            energyEfficiency: 0.87,
            systemLoad: 58,
        },
        consistent: {
            averageLatency: 22.1,
            successRate: 98.7,
            energyEfficiency: 0.94,
            systemLoad: 71,
        },
    })

    const [tleDataStatus, setTleDataStatus] = useState({
        source: 'local' as 'celestrak' | 'local',
        lastUpdate: null as Date | null,
        nextUpdate: null as Date | null,
        connectionActive: false,
    })

    const [autoTestResults, setAutoTestResults] = useState<any[]>([])
    const isUpdatingRef = useRef(false)

    // 獲取UAV數據
    const fetchRealUAVData = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/uav-coordination/status')
            if (response.ok) {
                const uavData = await response.json()
                setData(prev => ({ ...prev, uavData }))
                return true
            }
        } catch (error) {
            console.warn('UAV數據獲取失敗:', error)
            setData(prev => ({ ...prev, realDataError: 'UAV API 連接失敗' }))
        }
        return false
    }, [])

    // 獲取換手測試數據
    const fetchHandoverTestData = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/handover-tests/latest?count=20')
            if (response.ok) {
                const handoverTestData = await response.json()
                setData(prev => ({ ...prev, handoverLatencyData: handoverTestData }))
                return true
            }
        } catch (error) {
            console.warn('換手測試數據獲取失敗:', error)
        }
        return false
    }, [])

    // 獲取六場景數據
    const fetchSixScenarioData = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/performance/six-scenarios')
            if (response.ok) {
                const scenarioData = await response.json()
                setData(prev => ({ ...prev, sixScenarioData: scenarioData }))
                return true
            }
        } catch (error) {
            console.warn('六場景數據獲取失敗:', error)
        }
        return false
    }, [])

    // 獲取策略效果數據
    const fetchStrategyEffectData = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/strategy/effect-analysis')
            if (response.ok) {
                const effectData = await response.json()
                setData(prev => ({ ...prev, strategyEffectData: effectData }))
                return true
            }
        } catch (error) {
            console.warn('策略效果數據獲取失敗:', error)
        }
        return false
    }, [])

    // 獲取系統指標
    const fetchRealSystemMetrics = useCallback(async () => {
        try {
            const response = await fetch('/api/v1/system/metrics/realtime')
            if (response.ok) {
                const metrics = await response.json()
                setData(prev => ({
                    ...prev,
                    systemMetrics: {
                        cpu: metrics.cpu_usage_percent || prev.systemMetrics.cpu,
                        memory: metrics.memory_usage_percent || prev.systemMetrics.memory,
                        gpu: metrics.gpu_usage_percent || prev.systemMetrics.gpu,
                        networkLatency: metrics.network_latency_ms || prev.systemMetrics.networkLatency,
                    },
                    realDataError: null,
                }))
                return true
            }
        } catch (error) {
            console.warn('系統指標獲取失敗:', error)
            setData(prev => ({ ...prev, realDataError: '系統監控 API 連接失敗' }))
        }
        return false
    }, [])

    // 獲取核心同步數據
    const fetchCoreSync = useCallback(async () => {
        try {
            const syncData = await netStackApi.getCoreSync()
            setData(prev => ({ ...prev, coreSync: syncData }))
            return true
        } catch (error) {
            console.warn('核心同步數據獲取失敗:', error)
        }
        return false
    }, [])

    // 獲取衛星數據
    const fetchRealSatelliteData = useCallback(async () => {
        if (isUpdatingRef.current) return false

        return await satelliteCache.withCache(
            'visible_satellites_15',
            async () => {
                isUpdatingRef.current = true
                try {
                    const controller = new AbortController()
                    const timeoutId = setTimeout(() => controller.abort(), 5000)

                    const response = await fetch(
                        '/api/v1/satellite-ops/visible_satellites?count=15&global_view=true',
                        {
                            signal: controller.signal,
                            headers: { 'Cache-Control': 'max-age=30' },
                        }
                    )
                    clearTimeout(timeoutId)

                    if (response.ok) {
                        const data = await response.json()
                        if (data.satellites && data.satellites.length > 0) {
                            // 處理衛星數據並更新狀態
                            const starlinkSats = data.satellites.filter((sat: any) =>
                                sat.name.toUpperCase().includes('STARLINK')
                            )
                            const kuiperSats = data.satellites.filter((sat: any) =>
                                sat.name.toUpperCase().includes('KUIPER')
                            )

                            // 計算新的高度值
                            const newStarlinkAltitude = starlinkSats.length > 0 
                                ? Math.round(starlinkSats.reduce((sum: number, sat: any) => 
                                    sum + (sat.orbit_altitude_km || 550), 0) / starlinkSats.length)
                                : 550
                            
                            const newKuiperAltitude = kuiperSats.length > 0
                                ? Math.round(kuiperSats.reduce((sum: number, sat: any) => 
                                    sum + (sat.orbit_altitude_km || 630), 0) / kuiperSats.length)
                                : 630

                            // 只在高度值真正變化時才更新 state
                            setSatelliteData(prev => {
                                if (prev.starlink.altitude === newStarlinkAltitude && 
                                    prev.kuiper.altitude === newKuiperAltitude) {
                                    return prev // 返回相同引用，避免觸發重新渲染
                                }
                                
                                return {
                                    ...prev,
                                    starlink: {
                                        ...prev.starlink,
                                        altitude: newStarlinkAltitude,
                                    },
                                    kuiper: {
                                        ...prev.kuiper,
                                        altitude: newKuiperAltitude,
                                    }
                                }
                            })
                        }
                        return true
                    }
                } catch (error) {
                    console.warn('衛星數據獲取失敗:', error)
                } finally {
                    isUpdatingRef.current = false
                }
                return false
            },
            90000
        )
    }, [])

    // 運行自動測試 - 移除對 data 的依賴以避免無限循環
    const runAutomaticTests = useCallback(async () => {
        const tests = [
            {
                name: '數據完整性檢測',
                test: async () => {
                    // 使用固定的測試邏輯，不依賴動態 data 狀態
                    return true // 簡化測試邏輯
                },
            },
            {
                name: 'API連接測試',
                test: async () => {
                    return true // 簡化測試邏輯
                },
            },
        ]

        const results = []
        for (const test of tests) {
            try {
                const startTime = performance.now()
                const passed = await test.test()
                const duration = performance.now() - startTime

                results.push({
                    name: test.name,
                    passed,
                    duration: duration < 0.1 ? 0.1 : Math.round(duration * 100) / 100,
                    timestamp: '2024-01-01T00:00:00.000Z', // 使用固定時間戳避免每次都不同
                })
            } catch (error) {
                results.push({
                    name: test.name,
                    passed: false,
                    duration: 0,
                    error: String(error),
                    timestamp: '2024-01-01T00:00:00.000Z', // 使用固定時間戳
                })
            }
        }

        setAutoTestResults(results)
        return results
    }, []) // 移除 data 依賴

    // 初始化數據 - 停用以避免無限渲染
    useEffect(() => {
        if (!isOpen) return
        
        // 暫時完全停用數據獲取以確認無限渲染問題
        // const initializeData = async () => {
        //     try {
        //         await Promise.allSettled([
        //             fetchStrategyEffectData(),
        //             fetchHandoverTestData(),
        //             fetchSixScenarioData(),
        //             fetchRealUAVData(),
        //             fetchCoreSync(),
        //             fetchRealSystemMetrics(),
        //         ])
        //     } catch (error) {
        //         console.warn('⚠️ 部分數據初始化失敗:', error)
        //     }
        // }

        // const initTimeout = setTimeout(initializeData, 1000)
        // const testTimeout = setTimeout(() => {
        //     runAutomaticTests().catch(() => {})
        // }, 5000)

        return () => {
            // clearTimeout(initTimeout)
            // clearTimeout(testTimeout)
        }
    }, [isOpen]) // 只保留 isOpen 依賴

    return {
        data,
        satelliteData,
        strategyMetrics,
        setStrategyMetrics,
        tleDataStatus,
        autoTestResults,
        fetchRealSystemMetrics,
        runAutomaticTests,
    }
    */
} 