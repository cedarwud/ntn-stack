/**
 * UAV 指標圖表組件 (Enhanced for Stage 5)
 * 顯示 UAV 的信號質量、位置等實時數據
 * 新增群組性能對比分析功能
 */
import { useState, useEffect, useCallback } from 'react'
import { getUAVList } from '../../../../services/netstackApi'
import { UAVData } from '../../../../types/charts'

interface SwarmGroupMetrics {
    group_id: string
    name: string
    average_signal: number
    average_battery: number
    formation_compliance: number
    coordination_quality: number
    member_count: number
}

interface UAVMetricsChartProps {
    className?: string
    refreshInterval?: number
    viewMode?: 'individual' | 'group_comparison' | 'formation_analysis'
    showGroupMetrics?: boolean
}

const UAVMetricsChart: React.FC<UAVMetricsChartProps> = ({
    className = '',
    refreshInterval = 3000,
    viewMode = 'individual',
    showGroupMetrics = false,
}) => {
    const [uavData, setUavData] = useState<UAVData[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [selectedUAV, setSelectedUAV] = useState<string | null>(null)
    const [groupMetrics, setGroupMetrics] = useState<SwarmGroupMetrics[]>([])
    const [selectedGroup, setSelectedGroup] = useState<string | null>(null)

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

            {/* Stage 5: 群組性能對比視圖 */}
            {viewMode === 'group_comparison' && (
                <div className="group-comparison-view">
                    <h3>群組性能對比分析</h3>

                    {/* 群組選擇器 */}
                    <div className="group-selector">
                        <select
                            value={selectedGroup || ''}
                            onChange={(e) => setSelectedGroup(e.target.value)}
                        >
                            <option value="">選擇群組</option>
                            {groupMetrics.map((group) => (
                                <option
                                    key={group.group_id}
                                    value={group.group_id}
                                >
                                    {group.name} ({group.member_count} UAVs)
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* 群組對比表格 */}
                    <div className="group-comparison-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>群組名稱</th>
                                    <th>成員數量</th>
                                    <th>平均信號</th>
                                    <th>平均電量</th>
                                    <th>編隊符合度</th>
                                    <th>協同質量</th>
                                </tr>
                            </thead>
                            <tbody>
                                {groupMetrics.map((group) => (
                                    <tr
                                        key={group.group_id}
                                        className={
                                            selectedGroup === group.group_id
                                                ? 'selected'
                                                : ''
                                        }
                                        onClick={() =>
                                            setSelectedGroup(group.group_id)
                                        }
                                    >
                                        <td>{group.name}</td>
                                        <td>{group.member_count}</td>
                                        <td>
                                            <span
                                                className={`signal-value ${
                                                    group.average_signal > -70
                                                        ? 'good'
                                                        : group.average_signal >
                                                          -85
                                                        ? 'medium'
                                                        : 'poor'
                                                }`}
                                            >
                                                {group.average_signal.toFixed(
                                                    1
                                                )}{' '}
                                                dBm
                                            </span>
                                        </td>
                                        <td>
                                            <span
                                                className={`battery-value ${
                                                    group.average_battery > 70
                                                        ? 'good'
                                                        : group.average_battery >
                                                          30
                                                        ? 'medium'
                                                        : 'poor'
                                                }`}
                                            >
                                                {group.average_battery.toFixed(
                                                    1
                                                )}
                                                %
                                            </span>
                                        </td>
                                        <td>
                                            <div className="compliance-bar">
                                                <div
                                                    className="compliance-fill"
                                                    style={{
                                                        width: `${
                                                            group.formation_compliance *
                                                            100
                                                        }%`,
                                                    }}
                                                ></div>
                                                <span>
                                                    {(
                                                        group.formation_compliance *
                                                        100
                                                    ).toFixed(1)}
                                                    %
                                                </span>
                                            </div>
                                        </td>
                                        <td>
                                            <div className="quality-indicator">
                                                <div
                                                    className={`quality-dot ${
                                                        group.coordination_quality >
                                                        0.8
                                                            ? 'excellent'
                                                            : group.coordination_quality >
                                                              0.6
                                                            ? 'good'
                                                            : group.coordination_quality >
                                                              0.4
                                                            ? 'fair'
                                                            : 'poor'
                                                    }`}
                                                ></div>
                                                {(
                                                    group.coordination_quality *
                                                    100
                                                ).toFixed(1)}
                                                %
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* 選中群組的詳細信息 */}
                    {selectedGroup && (
                        <div className="selected-group-details">
                            {(() => {
                                const group = groupMetrics.find(
                                    (g) => g.group_id === selectedGroup
                                )
                                return group ? (
                                    <div className="group-detail-card">
                                        <h4>{group.name} 詳細指標</h4>
                                        <div className="detail-grid">
                                            <div className="detail-item">
                                                <span className="label">
                                                    成員數量:
                                                </span>
                                                <span className="value">
                                                    {group.member_count} UAVs
                                                </span>
                                            </div>
                                            <div className="detail-item">
                                                <span className="label">
                                                    平均信號強度:
                                                </span>
                                                <span className="value">
                                                    {group.average_signal.toFixed(
                                                        1
                                                    )}{' '}
                                                    dBm
                                                </span>
                                            </div>
                                            <div className="detail-item">
                                                <span className="label">
                                                    平均電池電量:
                                                </span>
                                                <span className="value">
                                                    {group.average_battery.toFixed(
                                                        1
                                                    )}
                                                    %
                                                </span>
                                            </div>
                                            <div className="detail-item">
                                                <span className="label">
                                                    編隊符合度:
                                                </span>
                                                <span className="value">
                                                    {(
                                                        group.formation_compliance *
                                                        100
                                                    ).toFixed(1)}
                                                    %
                                                </span>
                                            </div>
                                            <div className="detail-item">
                                                <span className="label">
                                                    協同質量:
                                                </span>
                                                <span className="value">
                                                    {(
                                                        group.coordination_quality *
                                                        100
                                                    ).toFixed(1)}
                                                    %
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ) : null
                            })()}
                        </div>
                    )}
                </div>
            )}

            {/* Stage 5: 編隊分析視圖 */}
            {viewMode === 'formation_analysis' && (
                <div className="formation-analysis-view">
                    <h3>編隊性能分析</h3>

                    <div className="formation-metrics-grid">
                        {groupMetrics.map((group) => (
                            <div
                                key={group.group_id}
                                className="formation-card"
                            >
                                <div className="formation-header">
                                    <h4>{group.name}</h4>
                                    <span className="member-count">
                                        {group.member_count} UAVs
                                    </span>
                                </div>

                                <div className="formation-metrics">
                                    {/* 協同質量圓形進度條 */}
                                    <div className="circular-progress">
                                        <svg
                                            viewBox="0 0 36 36"
                                            className="circular-chart"
                                        >
                                            <path
                                                className="circle-bg"
                                                d="M18 2.0845
                                                a 15.9155 15.9155 0 0 1 0 31.831
                                                a 15.9155 15.9155 0 0 1 0 -31.831"
                                            />
                                            <path
                                                className="circle"
                                                strokeDasharray={`${
                                                    group.coordination_quality *
                                                    100
                                                }, 100`}
                                                d="M18 2.0845
                                                a 15.9155 15.9155 0 0 1 0 31.831
                                                a 15.9155 15.9155 0 0 1 0 -31.831"
                                            />
                                            <text
                                                x="18"
                                                y="20.35"
                                                className="percentage"
                                            >
                                                {(
                                                    group.coordination_quality *
                                                    100
                                                ).toFixed(0)}
                                                %
                                            </text>
                                        </svg>
                                        <div className="progress-label">
                                            協同質量
                                        </div>
                                    </div>

                                    {/* 編隊符合度條形圖 */}
                                    <div className="formation-compliance">
                                        <div className="metric-label">
                                            編隊符合度
                                        </div>
                                        <div className="progress-bar">
                                            <div
                                                className="progress-fill"
                                                style={{
                                                    width: `${
                                                        group.formation_compliance *
                                                        100
                                                    }%`,
                                                }}
                                            ></div>
                                        </div>
                                        <div className="metric-value">
                                            {(
                                                group.formation_compliance * 100
                                            ).toFixed(1)}
                                            %
                                        </div>
                                    </div>

                                    {/* 信號與電量指標 */}
                                    <div className="signal-battery-metrics">
                                        <div className="metric-row">
                                            <span className="metric-label">
                                                平均信號:
                                            </span>
                                            <span
                                                className={`metric-value ${
                                                    group.average_signal > -70
                                                        ? 'good'
                                                        : group.average_signal >
                                                          -85
                                                        ? 'medium'
                                                        : 'poor'
                                                }`}
                                            >
                                                {group.average_signal.toFixed(
                                                    1
                                                )}{' '}
                                                dBm
                                            </span>
                                        </div>
                                        <div className="metric-row">
                                            <span className="metric-label">
                                                平均電量:
                                            </span>
                                            <span
                                                className={`metric-value ${
                                                    group.average_battery > 70
                                                        ? 'good'
                                                        : group.average_battery >
                                                          30
                                                        ? 'medium'
                                                        : 'poor'
                                                }`}
                                            >
                                                {group.average_battery.toFixed(
                                                    1
                                                )}
                                                %
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="chart-footer">
                <span className="uav-count">
                    {viewMode === 'individual'
                        ? `共 ${uavData.length} 架 UAV`
                        : viewMode === 'group_comparison'
                        ? `共 ${groupMetrics.length} 個群組`
                        : `編隊分析模式`}
                </span>
                <span className="last-updated">
                    最後更新:{' '}
                    {selectedUAVData
                        ? new Date(selectedUAVData.last_update).toLocaleString()
                        : new Date().toLocaleString()}
                </span>
            </div>
        </div>
    )

    // 加載群組指標數據（模擬）
    useEffect(() => {
        if (showGroupMetrics || viewMode !== 'individual') {
            // 模擬群組數據
            const mockGroupMetrics: SwarmGroupMetrics[] = [
                {
                    group_id: 'group_001',
                    name: 'Alpha Squadron',
                    average_signal: -72.5,
                    average_battery: 85.3,
                    formation_compliance: 0.92,
                    coordination_quality: 0.89,
                    member_count: 3,
                },
                {
                    group_id: 'group_002',
                    name: 'Beta Formation',
                    average_signal: -78.2,
                    average_battery: 67.8,
                    formation_compliance: 0.85,
                    coordination_quality: 0.76,
                    member_count: 4,
                },
                {
                    group_id: 'group_003',
                    name: 'Gamma Wing',
                    average_signal: -69.1,
                    average_battery: 92.4,
                    formation_compliance: 0.96,
                    coordination_quality: 0.94,
                    member_count: 2,
                },
            ]
            setGroupMetrics(mockGroupMetrics)
        }
    }, [showGroupMetrics, viewMode])
}

export default UAVMetricsChart
