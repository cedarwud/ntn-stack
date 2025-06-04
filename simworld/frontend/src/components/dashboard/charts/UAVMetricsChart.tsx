/**
 * UAV 指標圖表組件
 * 顯示 UAV 的信號質量、位置等實時數據
 */
import { useState, useEffect, useCallback } from 'react'
import { getUAVList } from '../../../services/netstackApi'
import { UAVData } from '../../../types/charts'

interface UAVMetricsChartProps {
    className?: string
    refreshInterval?: number
}

const UAVMetricsChart: React.FC<UAVMetricsChartProps> = ({
    className = '',
    refreshInterval = 3000,
}) => {
    const [uavData, setUavData] = useState<UAVData[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedUAV, setSelectedUAV] = useState<string | null>(null)

    // 使用 useCallback 避免函數重新創建
    const loadUAVData = useCallback(async () => {
        try {
            setLoading(true)
            const data = await getUAVList()
            setUavData(data.uavs)
            setError(null)

            // 如果沒有選中的 UAV，自動選擇第一個
            if (!selectedUAV && data.uavs.length > 0) {
                setSelectedUAV(data.uavs[0].uav_id)
            }
        } catch (err) {
            console.error('載入 UAV 數據失敗:', err)
            setError('無法載入 UAV 數據')
        } finally {
            setLoading(false)
        }
    }, [selectedUAV])

    // 組件掛載時載入數據
    useEffect(() => {
        loadUAVData()
    }, [loadUAVData])

    // 設置定時刷新
    useEffect(() => {
        if (refreshInterval > 0) {
            const interval = setInterval(loadUAVData, refreshInterval)
            return () => clearInterval(interval)
        }
    }, [refreshInterval, loadUAVData])

    // 獲取連接狀態顏色
    const getConnectionStatusColor = (status: string): string => {
        switch (status) {
            case 'connected':
                return '#10b981'
            case 'connecting':
                return '#f59e0b'
            case 'disconnected':
                return '#ef4444'
            default:
                return '#6b7280'
        }
    }

    // 獲取飛行狀態顏色
    const getFlightStatusColor = (status: string): string => {
        switch (status) {
            case 'flying':
                return '#10b981'
            case 'takeoff':
            case 'landing':
                return '#f59e0b'
            case 'idle':
                return '#6b7280'
            case 'error':
                return '#ef4444'
            default:
                return '#6b7280'
        }
    }

    // 獲取信號強度描述
    const getSignalStrengthLabel = (rsrp: number): string => {
        if (rsrp >= -80) return '優秀'
        if (rsrp >= -90) return '良好'
        if (rsrp >= -100) return '一般'
        if (rsrp >= -110) return '差'
        return '很差'
    }

    // 獲取信號強度顏色
    const getSignalStrengthColor = (rsrp: number): string => {
        if (rsrp >= -80) return '#10b981'
        if (rsrp >= -90) return '#84cc16'
        if (rsrp >= -100) return '#f59e0b'
        if (rsrp >= -110) return '#f97316'
        return '#ef4444'
    }

    const selectedUAVData = uavData.find((uav) => uav.uav_id === selectedUAV)

    if (loading) {
        return (
            <div className={`uav-metrics-chart ${className}`}>
                <div className="loading">
                    <div className="loading-spinner"></div>
                    <span>載入 UAV 數據中...</span>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={`uav-metrics-chart ${className}`}>
                <div className="error">
                    <span className="error-icon">⚠️</span>
                    <span>{error}</span>
                    <button onClick={loadUAVData} className="retry-button">
                        重試
                    </button>
                </div>
            </div>
        )
    }

    if (uavData.length === 0) {
        return (
            <div className={`uav-metrics-chart ${className}`}>
                <div className="no-data">無 UAV 數據</div>
            </div>
        )
    }

    return (
        <div className={`uav-metrics-chart ${className}`}>
            <div className="chart-header">
                <h3>UAV 監控面板</h3>
                <div className="uav-selector">
                    <select
                        value={selectedUAV || ''}
                        onChange={(e) => setSelectedUAV(e.target.value)}
                    >
                        {uavData.map((uav) => (
                            <option key={uav.uav_id} value={uav.uav_id}>
                                {uav.name} ({uav.uav_id.slice(0, 8)}...)
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {selectedUAVData && (
                <div className="uav-details">
                    {/* UAV 基本狀態 */}
                    <div className="status-section">
                        <h4>基本狀態</h4>
                        <div className="status-grid">
                            <div className="status-item">
                                <span className="label">飛行狀態:</span>
                                <span
                                    className="value"
                                    style={{
                                        color: getFlightStatusColor(
                                            selectedUAVData.flight_status
                                        ),
                                    }}
                                >
                                    {selectedUAVData.flight_status}
                                </span>
                            </div>
                            <div className="status-item">
                                <span className="label">連接狀態:</span>
                                <span
                                    className="value"
                                    style={{
                                        color: getConnectionStatusColor(
                                            selectedUAVData.ue_connection_status
                                        ),
                                    }}
                                >
                                    {selectedUAVData.ue_connection_status}
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 位置信息 */}
                    <div className="position-section">
                        <h4>位置信息</h4>
                        <div className="position-grid">
                            <div className="position-item">
                                <span className="label">緯度:</span>
                                <span className="value">
                                    {selectedUAVData.current_position.latitude.toFixed(
                                        6
                                    )}
                                    °
                                </span>
                            </div>
                            <div className="position-item">
                                <span className="label">經度:</span>
                                <span className="value">
                                    {selectedUAVData.current_position.longitude.toFixed(
                                        6
                                    )}
                                    °
                                </span>
                            </div>
                            <div className="position-item">
                                <span className="label">高度:</span>
                                <span className="value">
                                    {selectedUAVData.current_position.altitude.toFixed(
                                        1
                                    )}
                                    m
                                </span>
                            </div>
                            <div className="position-item">
                                <span className="label">速度:</span>
                                <span className="value">
                                    {selectedUAVData.current_position.speed.toFixed(
                                        1
                                    )}{' '}
                                    m/s
                                </span>
                            </div>
                            <div className="position-item">
                                <span className="label">航向:</span>
                                <span className="value">
                                    {selectedUAVData.current_position.heading.toFixed(
                                        1
                                    )}
                                    °
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 信號質量 */}
                    <div className="signal-section">
                        <h4>信號質量</h4>
                        <div className="signal-summary">
                            <div className="signal-strength">
                                <span className="label">信號強度:</span>
                                <span
                                    className="value"
                                    style={{
                                        color: getSignalStrengthColor(
                                            selectedUAVData.signal_quality
                                                .rsrp_dbm
                                        ),
                                    }}
                                >
                                    {getSignalStrengthLabel(
                                        selectedUAVData.signal_quality.rsrp_dbm
                                    )}
                                </span>
                            </div>
                        </div>
                        <div className="signal-metrics">
                            <div className="metric-item">
                                <span className="label">RSRP:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.rsrp_dbm.toFixed(
                                        1
                                    )}{' '}
                                    dBm
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">RSRQ:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.rsrq_db.toFixed(
                                        1
                                    )}{' '}
                                    dB
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">SINR:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.sinr_db.toFixed(
                                        1
                                    )}{' '}
                                    dB
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">CQI:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.cqi}
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">吞吐量:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.throughput_mbps.toFixed(
                                        2
                                    )}{' '}
                                    Mbps
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">延遲:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.latency_ms.toFixed(
                                        1
                                    )}{' '}
                                    ms
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">丟包率:</span>
                                <span className="value">
                                    {(
                                        selectedUAVData.signal_quality
                                            .packet_loss_rate * 100
                                    ).toFixed(2)}
                                    %
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">抖動:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.jitter_ms.toFixed(
                                        1
                                    )}{' '}
                                    ms
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 高級指標 */}
                    <div className="advanced-section">
                        <h4>高級指標</h4>
                        <div className="advanced-metrics">
                            <div className="metric-item">
                                <span className="label">鏈路預算餘量:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.link_budget_margin_db.toFixed(
                                        1
                                    )}{' '}
                                    dB
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">多普勒頻移:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.doppler_shift_hz.toFixed(
                                        0
                                    )}{' '}
                                    Hz
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">波束對準分數:</span>
                                <span className="value">
                                    {(
                                        selectedUAVData.signal_quality
                                            .beam_alignment_score * 100
                                    ).toFixed(1)}
                                    %
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">干擾水平:</span>
                                <span className="value">
                                    {selectedUAVData.signal_quality.interference_level_db.toFixed(
                                        1
                                    )}{' '}
                                    dB
                                </span>
                            </div>
                            <div className="metric-item">
                                <span className="label">測量可信度:</span>
                                <span className="value">
                                    {(
                                        selectedUAVData.signal_quality
                                            .measurement_confidence * 100
                                    ).toFixed(1)}
                                    %
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="chart-footer">
                <span className="uav-count">共 {uavData.length} 架 UAV</span>
                <span className="last-updated">
                    最後更新:{' '}
                    {selectedUAVData
                        ? new Date(selectedUAVData.last_update).toLocaleString()
                        : ''}
                </span>
            </div>
        </div>
    )
}

export default UAVMetricsChart
