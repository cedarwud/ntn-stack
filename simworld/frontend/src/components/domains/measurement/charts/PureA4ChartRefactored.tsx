/**
 * 重構後的 Pure A4 Chart 組件
 * 基於 BaseChart 組件，大幅簡化實現
 */

import React from 'react'
import { BaseChart, createChartConfig } from '../shared'
import type { BaseChartProps, EventA4Params } from '../shared/types'

const PureA4ChartRefactored: React.FC<BaseChartProps<EventA4Params>> = ({
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

export default PureA4ChartRefactored