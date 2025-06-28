/**
 * 基礎圓餅圖和甜甜圈圖組件
 */
import React from 'react'
import { Pie, Doughnut } from 'react-chartjs-2'
import { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps, ChartWrapper, validateChartData } from './BaseChart'
import { createPieChartOptions, createDoughnutChartOptions } from '../../../utils/chartOptionsFactory'
import { CHART_COLORS } from '../../../constants/chartConstants'

export interface BasePieChartProps extends BaseChartProps {
    data: ChartData<'pie' | 'doughnut'>
    showPercentages?: boolean
    showValues?: boolean
    legendPosition?: 'top' | 'bottom' | 'left' | 'right'
}

export interface BaseDoughnutChartProps extends BasePieChartProps {
    data: ChartData<'doughnut'>
    cutout?: string | number
    centerText?: string
}

export const BasePieChart: React.FC<BasePieChartProps> = ({
    title,
    data,
    options,
    width,
    height,
    className,
    isLoading = false,
    error = null,
    onChartClick,
    onChartHover,
    showPercentages = true,
    showValues = false,
    legendPosition = 'bottom',
}) => {
    // 驗證資料
    if (!isLoading && !error && !validateChartData(data)) {
        return (
            <ChartWrapper
                title={title}
                className={className}
                width={width}
                height={height}
                isLoading={false}
                error="圖表資料無效"
                data={data}
            >
                <div />
            </ChartWrapper>
        )
    }

    // 建立圓餅圖專用選項
    const pieChartOptions = createPieChartOptions({
        title,
        showLegend: true,
        plugins: {
            legend: {
                position: legendPosition,
            },
            tooltip: {
                enabled: true,
                callbacks: {
                    label: function(context: { label?: string; parsed?: number; dataset: { data: number[] } }) {
                        const label = context.label || ''
                        const value = context.parsed || 0
                        const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
                        const percentage = ((value / total) * 100).toFixed(1)
                        
                        if (showPercentages && showValues) {
                            return `${label}: ${value} (${percentage}%)`
                        } else if (showPercentages) {
                            return `${label}: ${percentage}%`
                        } else {
                            return `${label}: ${value}`
                        }
                    },
                },
            },
        },
    })

    // 合併使用者提供的選項
    const finalOptions: ChartOptions<'pie'> = {
        ...pieChartOptions,
        ...options,
        onClick: onChartClick,
        onHover: onChartHover,
    }

    // 處理資料集樣式
    const processedData: ChartData<'pie'> = {
        ...data,
        datasets: data.datasets.map((dataset) => ({
            ...dataset,
            backgroundColor: dataset.backgroundColor ?? CHART_COLORS.GRADIENT_SET,
            borderColor: dataset.borderColor ?? CHART_COLORS.GRADIENT_SET_BORDERS,
            borderWidth: dataset.borderWidth ?? 1,
        }))
    }

    return (
        <ChartWrapper
            title={title}
            className={className}
            width={width}
            height={height}
            isLoading={isLoading}
            error={error}
            data={data}
        >
            <Pie data={processedData} options={finalOptions} />
        </ChartWrapper>
    )
}

export const BaseDoughnutChart: React.FC<BaseDoughnutChartProps> = ({
    title,
    data,
    options,
    width,
    height,
    className,
    isLoading = false,
    error = null,
    onChartClick,
    onChartHover,
    showPercentages = true,
    showValues = false,
    legendPosition = 'bottom',
    cutout = '50%',
    centerText,
}) => {
    // 驗證資料
    if (!isLoading && !error && !validateChartData(data)) {
        return (
            <ChartWrapper
                title={title}
                className={className}
                width={width}
                height={height}
                isLoading={false}
                error="圖表資料無效"
                data={data}
            >
                <div />
            </ChartWrapper>
        )
    }

    // 建立甜甜圈圖專用選項
    const doughnutChartOptions = createDoughnutChartOptions({
        title,
        showLegend: true,
        plugins: {
            legend: {
                position: legendPosition,
            },
            tooltip: {
                enabled: true,
                callbacks: {
                    label: function(context: { label?: string; parsed?: number; dataset: { data: number[] } }) {
                        const label = context.label || ''
                        const value = context.parsed || 0
                        const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0)
                        const percentage = ((value / total) * 100).toFixed(1)
                        
                        if (showPercentages && showValues) {
                            return `${label}: ${value} (${percentage}%)`
                        } else if (showPercentages) {
                            return `${label}: ${percentage}%`
                        } else {
                            return `${label}: ${value}`
                        }
                    },
                },
            },
        },
    })

    // 合併使用者提供的選項
    const finalOptions: ChartOptions<'doughnut'> = {
        ...doughnutChartOptions,
        ...options,
        cutout,
        onClick: onChartClick,
        onHover: onChartHover,
    }

    // 處理資料集樣式
    const processedData: ChartData<'doughnut'> = {
        ...data,
        datasets: data.datasets.map((dataset) => ({
            ...dataset,
            backgroundColor: dataset.backgroundColor ?? CHART_COLORS.GRADIENT_SET,
            borderColor: dataset.borderColor ?? CHART_COLORS.GRADIENT_SET_BORDERS,
            borderWidth: dataset.borderWidth ?? 1,
        }))
    }

    return (
        <ChartWrapper
            title={title}
            className={className}
            width={width}
            height={height}
            isLoading={isLoading}
            error={error}
            data={data}
        >
            <div style={{ position: 'relative' }}>
                <Doughnut data={processedData} options={finalOptions} />
                {centerText && (
                    <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        color: 'white',
                        fontSize: '16px',
                        fontWeight: 'bold',
                        pointerEvents: 'none',
                    }}>
                        {centerText}
                    </div>
                )}
            </div>
        </ChartWrapper>
    )
}

/**
 * 預設圓餅圖資料 Hook
 */
// eslint-disable-next-line react-refresh/only-export-components
export const usePieChartData = () => {
    const createEmptyPieData = (): ChartData<'pie'> => ({
        labels: [],
        datasets: []
    })

    const createPieDataset = (
        data: number[],
        options: {
            colors?: string[]
            borderColors?: string[]
            borderWidth?: number
        } = {}
    ) => ({
        data,
        backgroundColor: options.colors ?? CHART_COLORS.GRADIENT_SET,
        borderColor: options.borderColors ?? CHART_COLORS.GRADIENT_SET_BORDERS,
        borderWidth: options.borderWidth ?? 1,
    })

    const createDistributionPieData = (
        distribution: {
            [key: string]: number
        }
    ): ChartData<'pie'> => ({
        labels: Object.keys(distribution),
        datasets: [createPieDataset(Object.values(distribution))]
    })

    return {
        createEmptyPieData,
        createPieDataset,
        createDistributionPieData,
    }
}