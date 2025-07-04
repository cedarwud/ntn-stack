/**
 * 重構後的 Pure D2 Chart 組件
 * 基於 BaseChart 組件，大幅簡化實現
 * Event D2: 服務基站距離變化事件
 */

import React from 'react'
import { BaseChart, createChartConfig } from '../shared'
import type { BaseChartProps, EventD2Params } from '../shared/types'

const PureD2ChartRefactored: React.FC<BaseChartProps<EventD2Params>> = ({
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

export default PureD2ChartRefactored