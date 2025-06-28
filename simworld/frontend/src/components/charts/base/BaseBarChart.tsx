/**
 * 基礎長條圖組件
 */
import React from 'react'
import { Bar } from 'react-chartjs-2'
import { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps, ChartWrapper, validateChartData } from './BaseChart'
import { createBarChartOptions } from '../../../utils/chartOptionsFactory'
import { CHART_COLORS } from '../../../constants/chartConstants'

export interface BaseBarChartProps extends BaseChartProps {
    data: ChartData<'bar'>
    horizontal?: boolean
    stacked?: boolean
    showValues?: boolean
}

export const BaseBarChart: React.FC<BaseBarChartProps> = ({
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
    horizontal = false,
    stacked = false,
    showValues = false,
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

    // 建立長條圖專用選項
    const barChartOptions = createBarChartOptions({
        title,
        showLegend: true,
        showGrid: true,
    })

    // 處理水平和堆疊設定
    const finalOptions: ChartOptions<'bar'> = {
        ...barChartOptions,
        ...options,
        indexAxis: horizontal ? 'y' : 'x',
        scales: {
            ...barChartOptions.scales,
            ...(stacked && {
                x: {
                    ...barChartOptions.scales?.x,
                    stacked: true,
                },
                y: {
                    ...barChartOptions.scales?.y,
                    stacked: true,
                },
            }),
            ...options?.scales,
        },
        plugins: {
            ...barChartOptions.plugins,
            ...options?.plugins,
            ...(showValues && {
                datalabels: {
                    display: true,
                    color: 'white',
                    anchor: 'end',
                    align: 'top',
                    formatter: (value: unknown) => {
                        if (typeof value === 'number') {
                            return value.toFixed(1)
                        }
                        return value
                    },
                },
            }),
        },
        onClick: onChartClick,
        onHover: onChartHover,
    }

    // 處理資料集樣式
    const processedData: ChartData<'bar'> = {
        ...data,
        datasets: data.datasets.map((dataset, index) => ({
            ...dataset,
            backgroundColor: dataset.backgroundColor ?? CHART_COLORS.GRADIENT_SET[index % CHART_COLORS.GRADIENT_SET.length],
            borderColor: dataset.borderColor ?? CHART_COLORS.GRADIENT_SET_BORDERS[index % CHART_COLORS.GRADIENT_SET_BORDERS.length],
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
            <Bar data={processedData} options={finalOptions} />
        </ChartWrapper>
    )
}

/**
 * 預設長條圖資料 Hook
 */
// eslint-disable-next-line react-refresh/only-export-components
export const useBarChartData = () => {
    const createEmptyBarData = (): ChartData<'bar'> => ({
        labels: [],
        datasets: []
    })

    const createBarDataset = (
        label: string,
        data: number[],
        options: {
            color?: string
            backgroundColor?: string
            borderColor?: string
            borderWidth?: number
        } = {}
    ) => ({
        label,
        data,
        backgroundColor: options.backgroundColor ?? options.color ?? CHART_COLORS.PRIMARY,
        borderColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
        borderWidth: options.borderWidth ?? 1,
    })

    const createComparisonBarData = (
        labels: string[],
        datasets: Array<{
            label: string
            data: number[]
            color?: string
        }>
    ): ChartData<'bar'> => ({
        labels,
        datasets: datasets.map((dataset, index) => createBarDataset(
            dataset.label,
            dataset.data,
            {
                color: dataset.color ?? CHART_COLORS.GRADIENT_SET[index % CHART_COLORS.GRADIENT_SET.length]
            }
        ))
    })

    return {
        createEmptyBarData,
        createBarDataset,
        createComparisonBarData,
    }
}