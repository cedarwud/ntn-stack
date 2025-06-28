/**
 * 基礎雷達圖組件
 */
import React from 'react'
import { Radar } from 'react-chartjs-2'
import { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps, ChartWrapper, validateChartData } from './BaseChart'
import { createRadarChartOptions } from '../../../utils/chartOptionsFactory'
import { CHART_COLORS } from '../../../constants/chartConstants'

export interface BaseRadarChartProps extends BaseChartProps {
    data: ChartData<'radar'>
    fill?: boolean
    showGrid?: boolean
    maxValue?: number
}

export const BaseRadarChart: React.FC<BaseRadarChartProps> = ({
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
    fill = true,
    showGrid = true,
    maxValue,
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

    // 建立雷達圖專用選項
    const radarChartOptions = createRadarChartOptions({
        title,
        showLegend: true,
        showGrid,
    })

    // 處理最大值設定
    const finalOptions: ChartOptions<'radar'> = {
        ...radarChartOptions,
        ...options,
        scales: {
            r: {
                ...radarChartOptions.scales?.r,
                beginAtZero: true,
                ...(maxValue && { max: maxValue }),
                grid: {
                    display: showGrid,
                },
                pointLabels: {
                    color: 'white',
                    font: {
                        size: 12,
                    },
                },
                ticks: {
                    color: 'white',
                    font: {
                        size: 10,
                    },
                    stepSize: maxValue ? maxValue / 5 : undefined,
                },
                ...options?.scales?.r,
            },
        },
        onClick: onChartClick,
        onHover: onChartHover,
    }

    // 處理資料集樣式
    const processedData: ChartData<'radar'> = {
        ...data,
        datasets: data.datasets.map((dataset, index) => ({
            ...dataset,
            fill: dataset.fill ?? fill,
            borderColor: dataset.borderColor ?? CHART_COLORS.GRADIENT_SET_BORDERS[index % CHART_COLORS.GRADIENT_SET_BORDERS.length],
            backgroundColor: dataset.backgroundColor ?? CHART_COLORS.GRADIENT_SET[index % CHART_COLORS.GRADIENT_SET.length],
            pointBackgroundColor: dataset.pointBackgroundColor ?? CHART_COLORS.GRADIENT_SET_BORDERS[index % CHART_COLORS.GRADIENT_SET_BORDERS.length],
            pointBorderColor: dataset.pointBorderColor ?? CHART_COLORS.GRADIENT_SET_BORDERS[index % CHART_COLORS.GRADIENT_SET_BORDERS.length],
            pointRadius: dataset.pointRadius ?? 4,
            pointHoverRadius: dataset.pointHoverRadius ?? 6,
            borderWidth: dataset.borderWidth ?? 2,
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
            <Radar data={processedData} options={finalOptions} />
        </ChartWrapper>
    )
}

/**
 * 預設雷達圖資料 Hook
 */
// eslint-disable-next-line react-refresh/only-export-components
export const useRadarChartData = () => {
    const createEmptyRadarData = (): ChartData<'radar'> => ({
        labels: [],
        datasets: []
    })

    const createRadarDataset = (
        label: string,
        data: number[],
        options: {
            color?: string
            borderColor?: string
            backgroundColor?: string
            fill?: boolean
        } = {}
    ) => ({
        label,
        data,
        fill: options.fill ?? true,
        borderColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
        backgroundColor: options.backgroundColor ?? options.color ?? CHART_COLORS.PRIMARY,
        pointBackgroundColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
        pointBorderColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
    })

    const createPerformanceRadarData = (
        metrics: {
            [key: string]: number
        },
        maxValues?: {
            [key: string]: number
        }
    ): ChartData<'radar'> => {
        const labels = Object.keys(metrics)
        const data = Object.values(metrics)
        
        // 正規化數據（如果提供了最大值）
        const normalizedData = maxValues 
            ? data.map((value, index) => {
                const maxVal = maxValues[labels[index]]
                return maxVal ? (value / maxVal) * 100 : value
            })
            : data

        return {
            labels,
            datasets: [createRadarDataset('性能指標', normalizedData)]
        }
    }

    return {
        createEmptyRadarData,
        createRadarDataset,
        createPerformanceRadarData,
    }
}