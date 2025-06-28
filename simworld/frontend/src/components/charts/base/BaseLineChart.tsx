/**
 * 基礎線性圖表組件
 */
import React from 'react'
import { Line } from 'react-chartjs-2'
import { ChartData, ChartOptions } from 'chart.js'
import { BaseChartProps, ChartWrapper, validateChartData } from './BaseChart'
import { createLineChartOptions } from '../../../utils/chartOptionsFactory'
import { CHART_COLORS } from '../../../constants/chartConstants'

export interface BaseLineChartProps extends BaseChartProps {
    data: ChartData<'line'>
    showPoints?: boolean
    smooth?: boolean
    fill?: boolean
    tension?: number
}

export const BaseLineChart: React.FC<BaseLineChartProps> = ({
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
    showPoints = true,
    fill = false,
    tension = 0.3,
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

    // 建立線性圖專用選項
    const lineChartOptions = createLineChartOptions({
        title,
        tension,
        fill,
        showLegend: true,
        showGrid: true,
    })

    // 合併使用者提供的選項
    const finalOptions: ChartOptions<'line'> = {
        ...lineChartOptions,
        ...options,
        onClick: onChartClick,
        onHover: onChartHover,
    }

    // 處理資料集樣式
    const processedData: ChartData<'line'> = {
        ...data,
        datasets: data.datasets.map((dataset, index) => ({
            ...dataset,
            tension: dataset.tension ?? tension,
            fill: dataset.fill ?? fill,
            pointRadius: showPoints ? (dataset.pointRadius ?? 4) : 0,
            pointHoverRadius: showPoints ? (dataset.pointHoverRadius ?? 6) : 0,
            borderColor: dataset.borderColor ?? CHART_COLORS.GRADIENT_SET_BORDERS[index % CHART_COLORS.GRADIENT_SET_BORDERS.length],
            backgroundColor: dataset.backgroundColor ?? CHART_COLORS.GRADIENT_SET[index % CHART_COLORS.GRADIENT_SET.length],
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
            <Line data={processedData} options={finalOptions} />
        </ChartWrapper>
    )
}

/**
 * 預設線性圖表 Hook
 */
// eslint-disable-next-line react-refresh/only-export-components
export const useLineChartData = () => {
    const createEmptyLineData = (): ChartData<'line'> => ({
        labels: [],
        datasets: []
    })

    const createLineDataset = (
        label: string,
        data: number[],
        options: {
            color?: string
            borderColor?: string
            backgroundColor?: string
            fill?: boolean
            tension?: number
        } = {}
    ) => ({
        label,
        data,
        fill: options.fill ?? false,
        tension: options.tension ?? 0.3,
        borderColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
        backgroundColor: options.backgroundColor ?? options.color ?? CHART_COLORS.PRIMARY,
        pointBackgroundColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
        pointBorderColor: options.borderColor ?? options.color ?? CHART_COLORS.PRIMARY_BORDER,
    })

    return {
        createEmptyLineData,
        createLineDataset,
    }
}