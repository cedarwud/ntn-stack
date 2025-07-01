/**
 * 模擬數據生成器
 * 抽取自 FullChartAnalysisDashboard.tsx 的靜態配置
 */

/**
 * 創建模擬圖表數據
 * 用於圖表分析儀表板的備用數據
 */
export const createMockData = () => {
  // Handover 延遲分析數據
  const handoverLatencyData = {
    labels: ['信號檢測', '決策計算', '連接建立', '數據傳輸', '確認完成'],
    datasets: [
      {
        label: 'NTN 標準',
        data: [45, 78, 89, 23, 15],
        backgroundColor: 'rgba(255, 99, 132, 0.7)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-GS',
        data: [32, 54, 45, 15, 7],
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-SMN',
        data: [35, 58, 48, 12, 5],
        backgroundColor: 'rgba(255, 206, 86, 0.7)',
        borderColor: 'rgba(255, 206, 86, 1)',
        borderWidth: 2,
      },
      {
        label: '本論文方案',
        data: [8, 7, 4, 1.5, 0.5],
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
    ],
  }

  // 雙星座對比數據
  const constellationComparisonData = {
    labels: ['延遲', '覆蓋率', '換手頻率', 'QoE', '能耗', '可靠性'],
    datasets: [
      {
        label: 'Starlink',
        data: [85, 92, 75, 88, 82, 90],
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
      {
        label: 'Kuiper',
        data: [78, 85, 88, 86, 85, 87],
        backgroundColor: 'rgba(153, 102, 255, 0.7)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 2,
      },
    ],
  }

  // 六場景數據
  const sixScenarioChartData = {
    labels: [
      'SL-F-同向',
      'SL-F-全向',
      'SL-C-同向',
      'SL-C-全向',
      'KP-F-同向',
      'KP-F-全向',
      'KP-C-同向',
      'KP-C-全向',
    ],
    datasets: [
      {
        label: 'NTN 標準',
        data: [245, 255, 238, 252, 248, 258, 242, 250],
        backgroundColor: 'rgba(255, 99, 132, 0.7)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-GS',
        data: [148, 158, 145, 155, 152, 162, 146, 156],
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 2,
      },
      {
        label: 'NTN-SMN',
        data: [152, 165, 148, 162, 155, 168, 150, 160],
        backgroundColor: 'rgba(255, 206, 86, 0.7)',
        borderColor: 'rgba(255, 206, 86, 1)',
        borderWidth: 2,
      },
      {
        label: '本論文方案',
        data: [18, 24, 16, 22, 20, 26, 17, 23],
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 2,
      },
    ],
  }

  return {
    handoverLatencyData,
    constellationComparisonData,
    sixScenarioChartData,
  }
}

/**
 * RL監控模擬數據初始化
 */
export const createInitialRLData = () => ({
  dqnData: [] as number[],
  ppoData: [] as number[],
  labels: [] as string[],
})

/**
 * RL策略損失數據初始化
 */
export const createInitialPolicyLossData = () => ({
  dqnLoss: [] as number[],
  ppoLoss: [] as number[],
  labels: [] as string[],
})

/**
 * RL訓練指標初始化
 */
export const createInitialTrainingMetrics = () => ({
  dqn: {
    episodes: 0,
    avgReward: 0,
    progress: 0,
    handoverDelay: 0,
    successRate: 0,
    signalDropTime: 0,
    energyEfficiency: 0,
  },
  ppo: {
    episodes: 0,
    avgReward: 0,
    progress: 0,
    handoverDelay: 0,
    successRate: 0,
    signalDropTime: 0,
    energyEfficiency: 0,
  },
})

/**
 * 生成測試用的時間序列數據
 */
export const generateTimeSeriesData = (length: number = 20) => {
  const labels = Array.from({ length }, (_, i) => `T${i + 1}`)
  const data = Array.from({ length }, () => Math.random() * 100)
  
  return { labels, data }
}