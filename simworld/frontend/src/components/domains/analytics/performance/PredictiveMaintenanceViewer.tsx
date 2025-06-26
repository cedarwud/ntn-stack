/**
 * 預測性維護可視化組件
 *
 * 階段八：進階 AI 智慧決策與自動化調優
 * 提供設備故障預測、維護排程和系統健康度監控功能
 */

import React, { useState, useEffect, useCallback } from 'react'

interface Device {
    id: string
    name: string
    type: string
    status: string
}

import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import './PredictiveMaintenanceViewer.scss'

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
)

interface DeviceHealth {
    device_id: string
    device_name: string
    device_type: 'satellite' | 'gnb' | 'uav' | 'core_network' | 'database'
    current_health_score: number
    predicted_failure_probability: number
    next_maintenance_date: string
    remaining_useful_life: number // days
    critical_parameters: {
        parameter_name: string
        current_value: number
        threshold_value: number
        trend: 'improving' | 'stable' | 'degrading'
        severity: 'normal' | 'warning' | 'critical'
    }[]
    maintenance_history: {
        date: string
        type: 'preventive' | 'corrective' | 'emergency'
        duration: number
        cost: number
    }[]
}

interface PredictionModel {
    model_id: string
    model_name: string
    device_type: string
    accuracy: number
    precision: number
    recall: number
    last_training_date: string
    training_data_count: number
    feature_importance: {
        feature_name: string
        importance_score: number
    }[]
}

interface MaintenanceSchedule {
    schedule_id: string
    device_id: string
    device_name: string
    maintenance_type: 'preventive' | 'predictive' | 'corrective'
    scheduled_date: string
    estimated_duration: number
    priority: 'critical' | 'high' | 'medium' | 'low'
    assigned_team: string
    cost_estimate: number
    prerequisite_checks: string[]
    replacement_parts: {
        part_name: string
        quantity: number
        cost: number
        availability: 'in_stock' | 'order_required' | 'unavailable'
    }[]
}

interface PredictiveMaintenanceViewerProps {
    devices: Device[]
    enabled: boolean
}

const PredictiveMaintenanceViewer: React.FC<
    PredictiveMaintenanceViewerProps
> = ({ enabled }) => {
    const [deviceHealthData, setDeviceHealthData] = useState<DeviceHealth[]>([])
    const [predictionModels, setPredictionModels] = useState<PredictionModel[]>(
        []
    )
    const [maintenanceSchedule, setMaintenanceSchedule] = useState<
        MaintenanceSchedule[]
    >([])
    const [selectedDevice, setSelectedDevice] = useState<string | null>(null)
    const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>(
        '30d'
    )
    const [loading, setLoading] = useState(false)
    const [lastUpdate, setLastUpdate] = useState<string>('')

    // 模擬生成設備健康數據
    const generateDeviceHealthData = useCallback((): DeviceHealth[] => {
        const deviceTypes: DeviceHealth['device_type'][] = [
            'satellite',
            'gnb',
            'uav',
            'core_network',
            'database',
        ]

        return Array.from({ length: 12 }, (_, index) => ({
            device_id: `device_${index + 1}`,
            device_name: `${deviceTypes[
                index % deviceTypes.length
            ].toUpperCase()}-${String(index + 1).padStart(3, '0')}`,
            device_type: deviceTypes[index % deviceTypes.length],
            current_health_score: Math.random() * 40 + 60, // 60-100
            predicted_failure_probability: Math.random() * 0.3, // 0-30%
            next_maintenance_date: new Date(
                Date.now() + Math.random() * 90 * 24 * 60 * 60 * 1000
            )
                .toISOString()
                .split('T')[0],
            remaining_useful_life: Math.floor(Math.random() * 180 + 30), // 30-210 days
            critical_parameters: [
                {
                    parameter_name: 'CPU 使用率',
                    current_value: Math.random() * 30 + 50, // 50-80%
                    threshold_value: 85,
                    trend: (['improving', 'stable', 'degrading'] as const)[
                        Math.floor(Math.random() * 3)
                    ],
                    severity: (['normal', 'warning', 'critical'] as const)[
                        Math.floor(Math.random() * 3)
                    ],
                },
                {
                    parameter_name: '記憶體使用率',
                    current_value: Math.random() * 25 + 45, // 45-70%
                    threshold_value: 80,
                    trend: ['improving', 'stable', 'degrading'][
                        Math.floor(Math.random() * 3)
                    ] as 'improving' | 'stable' | 'degrading',
                    severity: ['normal', 'warning'][
                        Math.floor(Math.random() * 2)
                    ] as 'normal' | 'warning',
                },
                {
                    parameter_name: '溫度',
                    current_value: Math.random() * 20 + 45, // 45-65°C
                    threshold_value: 70,
                    trend: ['improving', 'stable', 'degrading'][
                        Math.floor(Math.random() * 3)
                    ] as 'improving' | 'stable' | 'degrading',
                    severity: ['normal', 'warning'][
                        Math.floor(Math.random() * 2)
                    ] as 'normal' | 'warning',
                },
            ],
            maintenance_history: Array.from({ length: 3 }, () => ({
                date: new Date(
                    Date.now() - Math.random() * 180 * 24 * 60 * 60 * 1000
                )
                    .toISOString()
                    .split('T')[0],
                type: ['preventive', 'corrective', 'emergency'][
                    Math.floor(Math.random() * 3)
                ] as 'preventive' | 'corrective' | 'emergency',
                duration: Math.floor(Math.random() * 8 + 2), // 2-10 hours
                cost: Math.floor(Math.random() * 5000 + 1000), // $1000-6000
            })),
        }))
    }, [])

    // 模擬生成預測模型數據
    const generatePredictionModels = useCallback((): PredictionModel[] => {
        const deviceTypes = [
            'satellite',
            'gnb',
            'uav',
            'core_network',
            'database',
        ]

        return deviceTypes.map((type, index) => ({
            model_id: `model_${type}_${index + 1}`,
            model_name: `${type.toUpperCase()} 故障預測模型`,
            device_type: type,
            accuracy: Math.random() * 0.1 + 0.85, // 85-95%
            precision: Math.random() * 0.1 + 0.8, // 80-90%
            recall: Math.random() * 0.15 + 0.75, // 75-90%
            last_training_date: new Date(
                Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000
            )
                .toISOString()
                .split('T')[0],
            training_data_count: Math.floor(Math.random() * 5000 + 10000), // 10k-15k
            feature_importance: [
                {
                    feature_name: 'CPU 使用率歷史',
                    importance_score: Math.random() * 0.3 + 0.2,
                },
                {
                    feature_name: '記憶體使用模式',
                    importance_score: Math.random() * 0.25 + 0.15,
                },
                {
                    feature_name: '網路延遲變化',
                    importance_score: Math.random() * 0.2 + 0.1,
                },
                {
                    feature_name: '錯誤日誌頻率',
                    importance_score: Math.random() * 0.15 + 0.1,
                },
                {
                    feature_name: '溫度趨勢',
                    importance_score: Math.random() * 0.1 + 0.05,
                },
            ].sort((a, b) => b.importance_score - a.importance_score),
        }))
    }, [])

    // 模擬生成維護排程數據
    const generateMaintenanceSchedule =
        useCallback((): MaintenanceSchedule[] => {
            const maintenanceTypes: MaintenanceSchedule['maintenance_type'][] =
                ['preventive', 'predictive', 'corrective']
            const priorities: MaintenanceSchedule['priority'][] = [
                'critical',
                'high',
                'medium',
                'low',
            ]
            const teams = ['Team A', 'Team B', 'Team C', 'Team D']

            return Array.from({ length: 8 }, (_, index) => ({
                schedule_id: `schedule_${index + 1}`,
                device_id: `device_${index + 1}`,
                device_name: `設備-${String(index + 1).padStart(3, '0')}`,
                maintenance_type:
                    maintenanceTypes[index % maintenanceTypes.length],
                scheduled_date: new Date(
                    Date.now() + Math.random() * 60 * 24 * 60 * 60 * 1000
                )
                    .toISOString()
                    .split('T')[0],
                estimated_duration: Math.floor(Math.random() * 6 + 2), // 2-8 hours
                priority: priorities[index % priorities.length],
                assigned_team: teams[index % teams.length],
                cost_estimate: Math.floor(Math.random() * 8000 + 2000), // $2000-10000
                prerequisite_checks: [
                    '檢查備用電源',
                    '確認備份系統',
                    '通知相關團隊',
                    '準備替換零件',
                ].slice(0, Math.floor(Math.random() * 3 + 2)),
                replacement_parts: [
                    {
                        part_name: '記憶體模組',
                        quantity: Math.floor(Math.random() * 3 + 1),
                        cost: Math.floor(Math.random() * 500 + 200),
                        availability: [
                            'in_stock',
                            'order_required',
                            'unavailable',
                        ][Math.floor(Math.random() * 3)] as
                            | 'in_stock'
                            | 'order_required'
                            | 'unavailable',
                    },
                    {
                        part_name: '網路卡',
                        quantity: 1,
                        cost: Math.floor(Math.random() * 300 + 100),
                        availability: ['in_stock', 'order_required'][
                            Math.floor(Math.random() * 2)
                        ] as 'in_stock' | 'order_required',
                    },
                ],
            }))
        }, [])

    // 初始化數據
    useEffect(() => {
        if (enabled) {
            setLoading(true)
            setTimeout(() => {
                setDeviceHealthData(generateDeviceHealthData())
                setPredictionModels(generatePredictionModels())
                setMaintenanceSchedule(generateMaintenanceSchedule())
                setLastUpdate(new Date().toLocaleTimeString())
                setLoading(false)
            }, 1000)
        }
    }, [
        enabled,
        generateDeviceHealthData,
        generatePredictionModels,
        generateMaintenanceSchedule,
    ])

    // 自動更新數據
    useEffect(() => {
        if (!enabled) return

        const interval = setInterval(() => {
            setDeviceHealthData(generateDeviceHealthData())
            setLastUpdate(new Date().toLocaleTimeString())
        }, 30000) // 30秒更新

        return () => clearInterval(interval)
    }, [enabled, generateDeviceHealthData])

    // 準備圖表數據
    const healthScoreChartData = {
        labels: deviceHealthData.map((d) => d.device_name),
        datasets: [
            {
                label: '當前健康分數',
                data: deviceHealthData.map((d) => d.current_health_score),
                backgroundColor: deviceHealthData.map((d) =>
                    d.current_health_score >= 80
                        ? '#4CAF50'
                        : d.current_health_score >= 60
                        ? '#FF9800'
                        : '#F44336'
                ),
                borderColor: deviceHealthData.map((d) =>
                    d.current_health_score >= 80
                        ? '#388E3C'
                        : d.current_health_score >= 60
                        ? '#F57C00'
                        : '#D32F2F'
                ),
                borderWidth: 1,
            },
        ],
    }

    const failureProbabilityChartData = {
        labels: deviceHealthData.map((d) => d.device_name),
        datasets: [
            {
                label: '故障概率 (%)',
                data: deviceHealthData.map(
                    (d) => d.predicted_failure_probability * 100
                ),
                backgroundColor: 'rgba(255, 99, 132, 0.6)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1,
                tension: 0.4,
            },
        ],
    }

    const modelAccuracyChartData = {
        labels: predictionModels.map((m) => m.model_name),
        datasets: [
            {
                label: '準確率',
                data: predictionModels.map((m) => m.accuracy * 100),
                backgroundColor: '#2196F3',
                borderColor: '#1976D2',
                borderWidth: 1,
            },
            {
                label: '精確度',
                data: predictionModels.map((m) => m.precision * 100),
                backgroundColor: '#4CAF50',
                borderColor: '#388E3C',
                borderWidth: 1,
            },
            {
                label: '召回率',
                data: predictionModels.map((m) => m.recall * 100),
                backgroundColor: '#FF9800',
                borderColor: '#F57C00',
                borderWidth: 1,
            },
        ],
    }

    const getHealthStatus = (
        score: number
    ): { text: string; color: string } => {
        if (score >= 80) return { text: '健康', color: '#4CAF50' }
        if (score >= 60) return { text: '注意', color: '#FF9800' }
        return { text: '警告', color: '#F44336' }
    }

    const getPriorityColor = (priority: string): string => {
        switch (priority) {
            case 'critical':
                return '#F44336'
            case 'high':
                return '#FF9800'
            case 'medium':
                return '#2196F3'
            case 'low':
                return '#4CAF50'
            default:
                return '#9E9E9E'
        }
    }

    if (!enabled) return null

    return (
        <div className="predictive-maintenance-viewer">
            <div className="viewer-header">
                <h2>🔧 預測性維護監控</h2>
                <div className="header-controls">
                    <select
                        value={timeRange}
                        onChange={(e) =>
                            setTimeRange(
                                e.target.value as '7d' | '30d' | '90d' | '1y'
                            )
                        }
                        className="time-range-select"
                    >
                        <option value="7d">過去 7 天</option>
                        <option value="30d">過去 30 天</option>
                        <option value="90d">過去 90 天</option>
                        <option value="1y">過去 1 年</option>
                    </select>
                    <span className="last-update">最後更新: {lastUpdate}</span>
                </div>
            </div>

            {loading ? (
                <div className="loading-indicator">
                    <div className="spinner"></div>
                    <p>正在加載預測性維護數據...</p>
                </div>
            ) : (
                <div className="viewer-content">
                    {/* 設備健康概覽 */}
                    <div className="section device-health-overview">
                        <h3>📊 設備健康概覽</h3>
                        <div className="charts-container">
                            <div className="chart-card">
                                <h4>設備健康分數</h4>
                                <Bar
                                    data={healthScoreChartData}
                                    options={{
                                        responsive: true,
                                        scales: {
                                            y: {
                                                beginAtZero: true,
                                                max: 100,
                                                title: {
                                                    display: true,
                                                    text: '健康分數',
                                                },
                                            },
                                        },
                                    }}
                                />
                            </div>
                            <div className="chart-card">
                                <h4>故障預測概率</h4>
                                <Line
                                    data={failureProbabilityChartData}
                                    options={{
                                        responsive: true,
                                        scales: {
                                            y: {
                                                beginAtZero: true,
                                                max: 100,
                                                title: {
                                                    display: true,
                                                    text: '故障概率 (%)',
                                                },
                                            },
                                        },
                                    }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* 設備詳細列表 */}
                    <div className="section device-list">
                        <h3>🖥️ 設備狀態詳情</h3>
                        <div className="device-cards">
                            {deviceHealthData.map((device) => {
                                const healthStatus = getHealthStatus(
                                    device.current_health_score
                                )
                                return (
                                    <div
                                        key={device.device_id}
                                        className={`device-card ${
                                            selectedDevice === device.device_id
                                                ? 'selected'
                                                : ''
                                        }`}
                                        onClick={() =>
                                            setSelectedDevice(device.device_id)
                                        }
                                    >
                                        <div className="device-header">
                                            <h4>{device.device_name}</h4>
                                            <span
                                                className="health-status"
                                                style={{
                                                    color: healthStatus.color,
                                                }}
                                            >
                                                {healthStatus.text}
                                            </span>
                                        </div>
                                        <div className="device-metrics">
                                            <div className="metric">
                                                <span className="label">
                                                    健康分數:
                                                </span>
                                                <span className="value">
                                                    {device.current_health_score.toFixed(
                                                        1
                                                    )}
                                                </span>
                                            </div>
                                            <div className="metric">
                                                <span className="label">
                                                    故障概率:
                                                </span>
                                                <span className="value">
                                                    {(
                                                        device.predicted_failure_probability *
                                                        100
                                                    ).toFixed(1)}
                                                    %
                                                </span>
                                            </div>
                                            <div className="metric">
                                                <span className="label">
                                                    剩餘壽命:
                                                </span>
                                                <span className="value">
                                                    {
                                                        device.remaining_useful_life
                                                    }{' '}
                                                    天
                                                </span>
                                            </div>
                                            <div className="metric">
                                                <span className="label">
                                                    下次維護:
                                                </span>
                                                <span className="value">
                                                    {
                                                        device.next_maintenance_date
                                                    }
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    {/* 預測模型性能 */}
                    <div className="section model-performance">
                        <h3>🤖 預測模型性能</h3>
                        <div className="chart-card">
                            <Bar
                                data={modelAccuracyChartData}
                                options={{
                                    responsive: true,
                                    scales: {
                                        y: {
                                            beginAtZero: true,
                                            max: 100,
                                            title: {
                                                display: true,
                                                text: '性能指標 (%)',
                                            },
                                        },
                                    },
                                }}
                            />
                        </div>
                    </div>

                    {/* 維護排程 */}
                    <div className="section maintenance-schedule">
                        <h3>📅 維護排程</h3>
                        <div className="schedule-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>設備</th>
                                        <th>維護類型</th>
                                        <th>排程日期</th>
                                        <th>預估時間</th>
                                        <th>優先級</th>
                                        <th>負責團隊</th>
                                        <th>預估成本</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {maintenanceSchedule.map((schedule) => (
                                        <tr key={schedule.schedule_id}>
                                            <td>{schedule.device_name}</td>
                                            <td>
                                                <span
                                                    className={`maintenance-type ${schedule.maintenance_type}`}
                                                >
                                                    {schedule.maintenance_type ===
                                                    'preventive'
                                                        ? '預防性'
                                                        : schedule.maintenance_type ===
                                                          'predictive'
                                                        ? '預測性'
                                                        : '矯正性'}
                                                </span>
                                            </td>
                                            <td>{schedule.scheduled_date}</td>
                                            <td>
                                                {schedule.estimated_duration}{' '}
                                                小時
                                            </td>
                                            <td>
                                                <span
                                                    className="priority-badge"
                                                    style={{
                                                        backgroundColor:
                                                            getPriorityColor(
                                                                schedule.priority
                                                            ),
                                                    }}
                                                >
                                                    {schedule.priority ===
                                                    'critical'
                                                        ? '緊急'
                                                        : schedule.priority ===
                                                          'high'
                                                        ? '高'
                                                        : schedule.priority ===
                                                          'medium'
                                                        ? '中'
                                                        : '低'}
                                                </span>
                                            </td>
                                            <td>{schedule.assigned_team}</td>
                                            <td>
                                                $
                                                {schedule.cost_estimate.toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default PredictiveMaintenanceViewer
