/**
 * 重構後的 Pure T1 Chart 組件
 * 基於 BaseChart 組件，大幅簡化實現
 * Event T1: 時間相關測量事件
 */

import React from 'react'
import { BaseChart, createChartConfig } from '../shared'
import type { BaseChartProps, EventT1Params } from '../shared/types'

const PureT1ChartRefactored: React.FC<BaseChartProps<EventT1Params>> = ({
  eventType,
  params,
  animationState,
  isDarkTheme,
  showThresholdLines,
  className
}) => {
  // 使用工廠函數生成圖表配置
  const chartConfig = createChartConfig(eventType, params, isDarkTheme)

  return (
    <BaseChart
      eventType={eventType}
      params={params}
      animationState={animationState}
      isDarkTheme={isDarkTheme}
      showThresholdLines={showThresholdLines}
      config={chartConfig}
      className={className}
    />
  )
}

export default PureT1ChartRefactored