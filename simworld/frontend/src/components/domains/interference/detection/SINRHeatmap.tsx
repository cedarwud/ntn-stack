import React, { useMemo, useEffect, useState, useCallback, useRef } from 'react'
import * as THREE from 'three'
import { ApiRoutes } from '../../../../config/apiRoutes'
import { Device } from '../../../../types/device'

interface SINRHeatmapProps {
    devices: Device[]
    enabled: boolean
    useRealData?: boolean // 新增：使用真實數據模式開關
    onLegendData?: (data: {
        realMetrics: InterferenceMetrics | null
        dataMode: 'simulation' | 'real' | 'hybrid'
    }) => void
}

interface InterferenceMetrics {
    total_detections: number
    detection_accuracy: number
    average_response_time_ms: number
    throughput_improvement_percent: number
    latency_reduction_ms: number
    reliability_improvement_percent: number
}

const SINRHeatmap: React.FC<SINRHeatmapProps> = React.memo(
    ({ devices, enabled, useRealData = true, onLegendData }) => {
        const [_heatmapData, _setHeatmapData] = useState<number[][]>([])
        const [realInterferenceMetrics, setRealInterferenceMetrics] =
            useState<InterferenceMetrics | null>(null)
        const [realSINRTexture, setRealSINRTexture] =
            useState<THREE.Texture | null>(null)
        const [dataMode, setDataMode] = useState<
            'simulation' | 'real' | 'hybrid'
        >(
            'simulation' // 預設為模擬模式，API 連接成功後切換
        )
        const [_apiConnectionStatus, setApiConnectionStatus] = useState<
            'connecting' | 'connected' | 'failed'
        >('connecting')

        // 🔄 使用 useRef 保存回調函數，避免依賴變化
        const onLegendDataRef = useRef(onLegendData)
        onLegendDataRef.current = onLegendData

        // 添加 log 狀態控制，只在開啟時列印一次
        const hasLoggedMetricsRef = useRef(false)
        const hasFetchedSINRMapRef = useRef(false)
        const prevEnabledRef = useRef(enabled)
        const prevUseRealDataRef = useRef(useRealData)

        // 獲取真實干擾指標
        useEffect(() => {
            if (!enabled || !useRealData) {
                // 重置 log 狀態，以便下次開啟時可以再次列印
                hasLoggedMetricsRef.current = false
                // 清空圖例數據
                onLegendDataRef.current?.({
                    realMetrics: null,
                    dataMode: 'simulation',
                })
                return
            }

            // 檢查是否剛剛開啟（enabled 或 useRealData 從 false 變為 true）
            const isJustEnabled =
                (!prevEnabledRef.current && enabled) ||
                (!prevUseRealDataRef.current && useRealData)

            const fetchInterferenceMetrics = async () => {
                try {
                    // 暫時禁用真實指標獲取，因為後端尚未實現 /metrics 端點
                    // 直接使用模擬數據避免 404 錯誤

                    // 只在剛開啟時列印一次 log
                    if (isJustEnabled && !hasLoggedMetricsRef.current) {
                        console.log(
                            '🎯 SINR 指標：使用模擬數據模式 (API 端點尚未實現)'
                        )
                        hasLoggedMetricsRef.current = true
                    }

                    setDataMode('simulation')
                    setRealInterferenceMetrics(null)
                    setApiConnectionStatus('failed')

                    // 通知父組件使用模擬數據
                    onLegendDataRef.current?.({
                        realMetrics: null,
                        dataMode: 'simulation',
                    })
                    return
                } catch (error) {
                    console.warn('獲取真實干擾指標失敗，使用模擬數據:', error)
                    setDataMode('simulation')
                    setRealInterferenceMetrics(null)
                    setApiConnectionStatus('failed')

                    // 更新圖例數據
                    onLegendDataRef.current?.({
                        realMetrics: null,
                        dataMode: 'simulation',
                    })
                }
            }

            // 更新前一次的狀態
            prevEnabledRef.current = enabled
            prevUseRealDataRef.current = useRealData

            fetchInterferenceMetrics()
            const interval = setInterval(fetchInterferenceMetrics, 60000) // 改為每60秒更新，減少頻率

            return () => clearInterval(interval)
        }, [enabled, useRealData])

        // 獲取真實 SINR 地圖
        useEffect(() => {
            if (!enabled || !useRealData) {
                // 重置 SINR 地圖獲取狀態
                hasFetchedSINRMapRef.current = false
                return
            }

            // 檢查是否剛剛開啟（enabled 或 useRealData 從 false 變為 true）
            const isJustEnabled =
                (!prevEnabledRef.current && enabled) ||
                (!prevUseRealDataRef.current && useRealData)

            const fetchRealSINRMap = async () => {
                try {
                    const response = await fetch(
                        ApiRoutes.simulations.getSINRMap
                    )
                    if (response.ok) {
                        const blob = await response.blob()
                        const imageUrl = URL.createObjectURL(blob)

                        const image = new Image()
                        image.onload = () => {
                            const texture = new THREE.Texture(image)
                            texture.needsUpdate = true
                            texture.flipY = false
                            setRealSINRTexture(texture)

                            // 只在剛開啟時列印一次 log
                            if (
                                isJustEnabled &&
                                !hasFetchedSINRMapRef.current
                            ) {
                                console.log('🗺️ 已獲取真實 SINR 熱力圖')
                                hasFetchedSINRMapRef.current = true
                            }

                            setDataMode('real')

                            // 更新圖例數據
                            onLegendDataRef.current?.({
                                realMetrics: realInterferenceMetrics,
                                dataMode: 'real',
                            })

                            // 清理 blob URL
                            URL.revokeObjectURL(imageUrl)
                        }
                        image.src = imageUrl
                    }
                } catch (error) {
                    console.warn('獲取真實 SINR 地圖失敗，使用模擬計算:', error)
                    setDataMode('simulation')
                    setRealSINRTexture(null)

                    // 更新圖例數據
                    onLegendDataRef.current?.({
                        realMetrics: realInterferenceMetrics,
                        dataMode: 'simulation',
                    })
                }
            }

            fetchRealSINRMap()
            const interval = setInterval(fetchRealSINRMap, 120000) // 改為每120秒更新，減少頻率

            return () => clearInterval(interval)
        }, [enabled, useRealData, realInterferenceMetrics])

        // 計算 SINR 熱力圖數據（模擬模式或混合模式備用）
        const { texture, geometry } = useMemo(() => {
            if (!enabled) return { texture: null, geometry: null }

            // 如果有真實 SINR 貼圖且處於真實數據模式，直接使用
            if (
                realSINRTexture &&
                (dataMode === 'real' || dataMode === 'hybrid')
            ) {
                const geometry = new THREE.PlaneGeometry(200, 200, 1, 1)
                return { texture: realSINRTexture, geometry }
            }

            const width = 100
            const height = 100
            const data = new Uint8Array(width * height * 4)

            // 獲取發射器(Tx)和干擾源(Jammer)位置

            const transmitters = devices.filter((d) => d.role === 'desired')

            const jammers = devices.filter((d) => d.role === 'jammer')

            for (let i = 0; i < height; i++) {
                for (let j = 0; j < width; j++) {
                    const x = (j / width) * 200 - 100 // -100 到 +100 的範圍
                    const y = (i / height) * 200 - 100

                    let signalStrength = 0
                    let interferenceLevel = 0

                    // 計算信號強度（來自 Tx 發射器）
                    transmitters.forEach((tx) => {
                        const distance = Math.sqrt(
                            Math.pow(x - (tx.position_x || 0), 2) +
                                Math.pow(y - (tx.position_y || 0), 2)
                        )
                        // 簡化的路徑損耗模型 (Free Space Path Loss)
                        const pathLoss =
                            20 * Math.log10(Math.max(distance, 1)) + 32.45
                        signalStrength += Math.pow(10, (30 - pathLoss) / 10) // 轉換為線性功率
                    })

                    // 計算干擾強度（來自 Jammer 干擾源）
                    jammers.forEach((jammer) => {
                        const distance = Math.sqrt(
                            Math.pow(x - (jammer.position_x || 0), 2) +
                                Math.pow(y - (jammer.position_y || 0), 2)
                        )
                        const pathLoss =
                            20 * Math.log10(Math.max(distance, 1)) + 32.45
                        interferenceLevel += Math.pow(10, (25 - pathLoss) / 10) // 干擾功率
                    })

                    // 計算 SINR (Signal to Interference + Noise Ratio)
                    const noise = 1e-12 // 熱雜訊功率
                    const sinr = signalStrength / (interferenceLevel + noise)
                    const sinrDb = 10 * Math.log10(sinr)

                    // 將 SINR 映射到顏色 (-20dB 到 +20dB)
                    const normalizedSinr = Math.max(
                        0,
                        Math.min(1, (sinrDb + 20) / 40)
                    )

                    const index = (i * width + j) * 4

                    // 彩色映射：藍色(低) -> 綠色(中) -> 紅色(高)
                    if (normalizedSinr < 0.5) {
                        // 藍色到綠色
                        const t = normalizedSinr * 2
                        data[index] = Math.floor(255 * (1 - t)) // R
                        data[index + 1] = Math.floor(255 * t) // G
                        data[index + 2] = 255 // B
                    } else {
                        // 綠色到紅色
                        const t = (normalizedSinr - 0.5) * 2
                        data[index] = Math.floor(255 * t) // R
                        data[index + 1] = Math.floor(255 * (1 - t)) // G
                        data[index + 2] = 0 // B
                    }
                    data[index + 3] = 180 // Alpha (透明度)
                }
            }

            const texture = new THREE.DataTexture(
                data,
                width,
                height,
                THREE.RGBAFormat
            )
            texture.needsUpdate = true
            texture.minFilter = THREE.LinearFilter
            texture.magFilter = THREE.LinearFilter

            const geometry = new THREE.PlaneGeometry(200, 200)

            return { texture, geometry }
        }, [devices, enabled, realSINRTexture, dataMode])

        if (!enabled || !texture || !geometry) return null

        return (
            <group>
                <mesh position={[0, 0.5, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                    <primitive object={geometry} />
                    <meshBasicMaterial
                        map={texture}
                        transparent
                        opacity={dataMode === 'real' ? 0.8 : 0.6}
                        side={THREE.DoubleSide}
                    />
                </mesh>

                {/* 數據模式指示器 */}
                {useRealData && (
                    <group position={[80, 20, 80]}>
                        <mesh>
                            <sphereGeometry args={[2, 8, 8]} />
                            <meshBasicMaterial
                                color={
                                    dataMode === 'real'
                                        ? 0x00ff00
                                        : dataMode === 'hybrid'
                                        ? 0xffff00
                                        : 0xff0000
                                }
                                transparent
                                opacity={0.8}
                            />
                        </mesh>
                    </group>
                )}

                {/* 真實指標顯示 */}
                {realInterferenceMetrics && dataMode !== 'simulation' && (
                    <group position={[70, 15, 70]}>
                        <mesh>
                            <boxGeometry args={[8, 4, 0.5]} />
                            <meshBasicMaterial
                                color={0x333333}
                                transparent
                                opacity={0.7}
                            />
                        </mesh>
                    </group>
                )}

                {/* SINR 圖例移到 Canvas 外部 - React Three Fiber 無法渲染 HTML 元素 */}
            </group>
        )
    }
)

// SINR 圖例組件（增強版，支援真實指標顯示）
export const SINRLegend: React.FC<{
    realMetrics?: InterferenceMetrics | null
    dataMode?: 'simulation' | 'real' | 'hybrid'
}> = ({ realMetrics, dataMode = 'simulation' }) => {
    return (
        <div
            className="sinr-legend"
            style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'rgba(0, 0, 0, 0.8)',
                color: 'white',
                padding: '10px',
                borderRadius: '5px',
                fontSize: '12px',
                zIndex: 1000,
                minWidth: '200px',
            }}
        >
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '8px',
                }}
            >
                <h4 style={{ margin: '0', marginRight: '8px' }}>SINR 熱力圖</h4>
                <div
                    style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        backgroundColor:
                            dataMode === 'real'
                                ? '#00ff00'
                                : dataMode === 'hybrid'
                                ? '#ffff00'
                                : '#ff0000',
                        marginLeft: 'auto',
                    }}
                />
                <span style={{ fontSize: '10px', marginLeft: '4px' }}>
                    {dataMode === 'real'
                        ? '真實'
                        : dataMode === 'hybrid'
                        ? '混合'
                        : '模擬'}
                </span>
            </div>

            {/* 基本 SINR 圖例 */}
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                }}
            >
                <div
                    style={{
                        width: '20px',
                        height: '10px',
                        background: 'red',
                        marginRight: '8px',
                    }}
                ></div>
                <span>高 SINR (&gt; 10dB)</span>
            </div>
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '4px',
                }}
            >
                <div
                    style={{
                        width: '20px',
                        height: '10px',
                        background: 'green',
                        marginRight: '8px',
                    }}
                ></div>
                <span>中 SINR (0dB)</span>
            </div>
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    marginBottom: '8px',
                }}
            >
                <div
                    style={{
                        width: '20px',
                        height: '10px',
                        background: 'blue',
                        marginRight: '8px',
                    }}
                ></div>
                <span>低 SINR (&lt; -10dB)</span>
            </div>

            {/* 真實干擾指標顯示 */}
            {realMetrics && dataMode !== 'simulation' && (
                <div style={{ borderTop: '1px solid #555', paddingTop: '8px' }}>
                    <h5 style={{ margin: '0 0 6px 0', fontSize: '11px' }}>
                        📊 真實干擾指標
                    </h5>
                    <div style={{ fontSize: '10px' }}>
                        <div>檢測數量: {realMetrics.total_detections}</div>
                        <div>
                            準確率: {realMetrics.detection_accuracy.toFixed(1)}%
                        </div>
                        <div>
                            回應時間:{' '}
                            {realMetrics.average_response_time_ms.toFixed(1)}ms
                        </div>
                        <div>
                            吞吐量改善:{' '}
                            {realMetrics.throughput_improvement_percent.toFixed(
                                1
                            )}
                            %
                        </div>
                        <div>
                            延遲降低:{' '}
                            {realMetrics.latency_reduction_ms.toFixed(1)}ms
                        </div>
                        <div>
                            可靠性改善:{' '}
                            {realMetrics.reliability_improvement_percent.toFixed(
                                1
                            )}
                            %
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

// Wrapper component that handles both 3D heatmap and HTML legend
export const SINRHeatmapWithLegend: React.FC<SINRHeatmapProps> = React.memo(
    ({ devices, enabled, useRealData = true }) => {
        const [legendData, setLegendData] = useState<{
            realMetrics: InterferenceMetrics | null
            dataMode: 'simulation' | 'real' | 'hybrid'
        }>({
            realMetrics: null,
            dataMode: 'simulation',
        })

        const handleLegendData = useCallback(
            (data: {
                realMetrics: InterferenceMetrics | null
                dataMode: 'simulation' | 'real' | 'hybrid'
            }) => {
                setLegendData(data)
            },
            []
        )

        if (!enabled) return null

        return (
            <>
                <SINRHeatmap
                    devices={devices}
                    enabled={enabled}
                    useRealData={useRealData}
                    onLegendData={handleLegendData}
                />
                <SINRLegend
                    realMetrics={legendData.realMetrics}
                    dataMode={legendData.dataMode}
                />
            </>
        )
    }
)

export default SINRHeatmap
