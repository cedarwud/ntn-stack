/* eslint-disable @typescript-eslint/no-explicit-any */
import { COLOR_PALETTE } from './chartConfig'

// 生成QoE時間序列數據
export const generateQoETimeSeriesData = () => {
    const scenarios = [
        'Ultra-Dense Urban',
        'Dense Urban',
        'Urban',
        'Sub-Urban',
        'Rural',
        'Remote',
    ]

    const timePoints = Array.from({ length: 10 }, (_, i) => `T${i + 1}`)

    const datasets = scenarios.map((scenario, index) => ({
        label: scenario,
        data: timePoints.map(() => Math.random() * 0.5 + 0.7 + index * 0.03),
        borderColor: COLOR_PALETTE.extended[index % COLOR_PALETTE.extended.length],
        backgroundColor: COLOR_PALETTE.extended[index % COLOR_PALETTE.extended.length].replace('0.8', '0.2'),
        borderWidth: 3,
        tension: 0.4,
        fill: false,
    }))

    return {
        labels: timePoints,
        datasets,
    }
}

// 生成六場景數據
export const generateSixScenarioData = () => {
    const scenarios = [
        'SL-B-單向',
        'SL-F-全向',
        'SL-D-差異',
        'KP-B-基本',
        'KP-F-全向',
        'KP-D-差異',
        'Mixed-1',
        'Mixed-2',
    ]

    // const methods = ['NTN', 'NTN-GS', 'NTN-SMN', 'Proposed']

    return {
        labels: scenarios,
        datasets: [
            {
                label: 'NTN',
                data: [247.8, 252.1, 249.6, 268.3, 270.2, 265.8, 258.9, 261.3],
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
            },
            {
                label: 'NTN-GS',
                data: [149.2, 152.8, 150.3, 155.7, 158.1, 153.9, 151.2, 154.6],
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
            },
            {
                label: 'NTN-SMN',
                data: [154.3, 157.9, 155.1, 159.8, 162.4, 158.2, 156.7, 160.1],
                backgroundColor: 'rgba(255, 206, 86, 0.8)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 2,
            },
            {
                label: 'Proposed',
                data: [19.7, 21.4, 20.2, 22.1, 22.9, 21.8, 20.8, 22.3],
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
            },
        ],
    }
}

// 生成換手延遲數據
export const generateHandoverLatencyData = () => {
    return {
        labels: [
            '準備階段',
            '同步階段',
            '切換階段',
            '確認階段',
            '清理階段',
            '完成階段',
        ],
        datasets: [
            {
                label: 'NTN',
                data: [45.2, 89.3, 67.8, 34.1, 15.6, 8.2],
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
            },
            {
                label: 'NTN-GS',
                data: [23.8, 52.4, 41.2, 22.7, 8.9, 4.2],
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
            },
            {
                label: 'NTN-SMN',
                data: [25.1, 54.8, 43.6, 24.3, 9.4, 4.6],
                backgroundColor: 'rgba(255, 206, 86, 0.8)',
                borderColor: 'rgba(255, 206, 86, 1)',
                borderWidth: 2,
            },
            {
                label: 'Proposed',
                data: [3.2, 7.8, 5.9, 2.1, 1.2, 0.9],
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
            },
        ],
    }
}

// 生成雙星座對比數據
export const generateConstellationComparisonData = (satelliteData: any) => {
    const metrics = [
        '軌道高度',
        '衛星數量',
        '覆蓋範圍',
        '延遲性能',
        '多普勒',
        '功率',
    ]

    return {
        labels: metrics,
        datasets: [
            {
                label: 'Starlink',
                data: [
                    satelliteData.starlink.altitude / 10,
                    satelliteData.starlink.count / 100,
                    satelliteData.starlink.coverage / 10,
                    100 - satelliteData.starlink.delay * 10,
                    100 - satelliteData.starlink.doppler,
                    satelliteData.starlink.power,
                ],
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
            },
            {
                label: 'Kuiper',
                data: [
                    satelliteData.kuiper.altitude / 10,
                    satelliteData.kuiper.count / 100,
                    satelliteData.kuiper.coverage / 10,
                    100 - satelliteData.kuiper.delay * 10,
                    100 - satelliteData.kuiper.doppler,
                    satelliteData.kuiper.power,
                ],
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
            },
        ],
    }
}

// 生成策略效果數據
export const generateStrategyEffectData = (strategyMetrics: any) => {
    const timeLabels = Array.from({ length: 30 }, (_, i) => `${i + 1}分鐘前`)

    return {
        labels: timeLabels,
        datasets: [
            {
                label: 'Flexible Strategy',
                data: timeLabels.map((_, i) => 
                    strategyMetrics.flexible.averageLatency + 
                    Math.sin(i * 0.2) * 3 + 
                    (Math.random() - 0.5) * 2
                ),
                borderColor: 'rgba(255, 206, 86, 1)',
                backgroundColor: 'rgba(255, 206, 86, 0.2)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
            },
            {
                label: 'Consistent Strategy',
                data: timeLabels.map((_, i) => 
                    strategyMetrics.consistent.averageLatency + 
                    Math.sin(i * 0.15) * 2 + 
                    (Math.random() - 0.5) * 1.5
                ),
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderWidth: 3,
                tension: 0.4,
                fill: true,
            },
        ],
    }
}

// 生成系統資源數據
export const generateSystemResourceData = (systemMetrics: any) => {
    return {
        labels: ['CPU 使用率', 'RAM 使用率', 'GPU 使用率', '網路延遲'],
        datasets: [
            {
                label: '系統資源使用率',
                data: [
                    systemMetrics.cpu,
                    systemMetrics.memory,
                    systemMetrics.gpu,
                    systemMetrics.networkLatency,
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                ],
                borderWidth: 2,
            },
        ],
    }
}

// 生成性能雷達圖數據
export const generatePerformanceRadarData = () => {
    return {
        labels: [
            '延遲性能',
            '可靠性',
            '能耗效率',
            '覆蓋範圍',
            '切換速度',
            '訊號品質',
        ],
        datasets: [
            {
                label: 'Proposed方案',
                data: [95, 88, 92, 85, 96, 89],
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 3,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)',
                pointBorderColor: 'white',
                pointHoverBackgroundColor: 'white',
                pointHoverBorderColor: 'rgba(75, 192, 192, 1)',
                pointRadius: 6,
                pointHoverRadius: 8,
            },
            {
                label: 'NTN方案',
                data: [45, 52, 48, 55, 42, 49],
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 3,
                pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                pointBorderColor: 'white',
                pointHoverBackgroundColor: 'white',
                pointHoverBorderColor: 'rgba(255, 99, 132, 1)',
                pointRadius: 6,
                pointHoverRadius: 8,
            },
        ],
    }
}

// 生成全球覆蓋數據
export const generateGlobalCoverageData = () => {
    const continents = ['北美洲', '南美洲', '歐洲', '亞洲', '非洲', '大洋洲']
    
    return {
        labels: continents,
        datasets: [
            {
                label: 'Starlink 覆蓋率 (%)',
                data: [98.5, 92.3, 97.8, 94.2, 89.7, 96.1],
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
            },
            {
                label: 'Kuiper 覆蓋率 (%)',
                data: [96.2, 91.8, 95.4, 93.7, 88.9, 94.5],
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 2,
            },
        ],
    }
}

// 生成時間同步精度數據
export const generateTimeSyncPrecisionData = () => {
    return {
        labels: ['GPS同步', 'NTP同步', 'PTP同步', 'Proposed同步'],
        datasets: [
            {
                label: '同步精度 (μs)',
                data: [1000, 100, 10, 1],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                ],
                borderWidth: 2,
            },
        ],
    }
}

// 生成算法延遲數據
export const generateAlgorithmLatencyData = () => {
    return {
        labels: ['RACH', 'SYNC', 'HANDOVER', 'RELEASE'],
        datasets: [
            {
                label: '傳統算法 (ms)',
                data: [45.2, 89.3, 67.8, 34.1],
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 2,
            },
            {
                label: '優化算法 (ms)',
                data: [12.3, 18.7, 15.2, 8.9],
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
            },
        ],
    }
} 