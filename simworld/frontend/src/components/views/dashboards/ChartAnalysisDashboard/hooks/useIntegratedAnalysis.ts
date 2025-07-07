/**
 * 整合分析頁籤的協調者Hook
 * 負責調用多個專門的數據Hook，並組合處理其狀態和數據，為UI層提供統一的接口。
 */
import { useMemo, useEffect } from 'react';

// 導入所有需要的專門化數據Hooks
import { useSignalAnalysisData } from './useSignalAnalysisData';
import { useRealChartData } from './useRealChartData';
import { useTimeSyncData } from './useTimeSyncData';
import { useAlgorithmPerformanceData } from './useAlgorithmPerformanceData';
import { useComplexityComparisonData } from './useComplexityComparisonData';
import { useOptimizationData } from './useOptimizationData';

// 導入策略Hook和數據處理服務
import { useStrategy } from '../../../../../hooks/useStrategy';
import { ChartDataProcessingService } from '../../../../../services/ChartDataProcessingService';

export const useIntegratedAnalysis = (isEnabled: boolean = true) => {
  // 1. 調用所有數據源Hooks
  const signalAnalysis = useSignalAnalysisData();
  const realChart = useRealChartData(isEnabled);
  const timeSync = useTimeSyncData(isEnabled);
  const algoPerf = useAlgorithmPerformanceData(isEnabled);
  const complexity = useComplexityComparisonData(isEnabled);
  const optimization = useOptimizationData(isEnabled);

  const {
    currentStrategy,
    isLoading: strategyLoading,
    switchStrategy,
  } = useStrategy();

  // 2. 數據獲取觸發器 (useEffect)
  useEffect(() => {
    if (isEnabled) {
      signalAnalysis.refreshData();
      timeSync.fetchTimeSyncData();
      algoPerf.fetchAlgorithmPerformance();
      complexity.fetchComplexityComparison();
      optimization.fetchOptimizationData();
    }
  }, [isEnabled, signalAnalysis, timeSync, algoPerf, complexity, optimization]);

  // 3. 衍生數據計算 (useMemo)
  // 將原組件中的所有useMemo數據處理邏輯遷移到這裡

  // 信號分析雷達圖數據
  const signalAnalysisRadarData = useMemo(() => {
    const processed = ChartDataProcessingService.processSignalAnalysis(
      signalAnalysis.signalMetrics,
      signalAnalysis.realTimeSignal
    );
    if (!processed) return null;
    const { radarData } = processed;
    return {
      labels: ['SINR品質', 'CFR響應', '延遲擴散', '多普勒偏移', '通道穩定性', '信號純度'],
      datasets: [{
        label: '當前信號狀態',
        data: [
          radarData.sinrQuality, radarData.cfrResponse, radarData.delaySpread,
          radarData.dopplerShift, radarData.channelStability, radarData.signalPurity
        ],
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        borderColor: 'rgba(34, 197, 94, 1)',
        pointBackgroundColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
      }]
    };
  }, [signalAnalysis.signalMetrics, signalAnalysis.realTimeSignal]);

  // 策略效果對比數據
  const strategyComparisonData = useMemo(() => {
    if (!signalAnalysis.strategyMetrics) return null;
    return {
      labels: ['NTN標準', 'NTN-GS', 'NTN-SMN', '本論文方案'],
      datasets: [
        {
          label: '平均延遲 (ms)',
          data: signalAnalysis.strategyMetrics.handoverLatency,
          backgroundColor: 'rgba(255, 99, 132, 0.8)',
          yAxisID: 'y'
        },
        {
          label: '成功率 (%)',
          data: signalAnalysis.strategyMetrics.successRate,
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          yAxisID: 'y1'
        },
        {
          label: '能效比 (%)',
          data: signalAnalysis.strategyMetrics.energyEfficiency,
          backgroundColor: 'rgba(59, 130, 246, 0.8)',
          yAxisID: 'y1'
        }
      ]
    };
  }, [signalAnalysis.strategyMetrics]);

  // 即時信號監控數據
  const realTimeSignalData = useMemo(() => {
    if (!signalAnalysis.realTimeSignal) return null;
    const { timeLabels, signalStrength, interferenceLevel, channelQuality } = signalAnalysis.realTimeSignal;
    return {
      labels: timeLabels,
      datasets: [
        {
          label: '信號強度 (dBm)',
          data: signalStrength,
          borderColor: 'rgba(34, 197, 94, 1)',
          yAxisID: 'y',
        },
        {
          label: '干擾水平 (dB)',
          data: interferenceLevel,
          borderColor: 'rgba(239, 68, 68, 1)',
          yAxisID: 'y',
        },
        {
          label: '通道品質 (%)',
          data: channelQuality,
          borderColor: 'rgba(59, 130, 246, 1)',
          yAxisID: 'y1',
        }
      ]
    };
  }, [signalAnalysis.realTimeSignal]);

  // 4. 返回統一的接口給UI組件
  return {
    loading: signalAnalysis.loading || realChart.dataStatus.overall === 'loading' || strategyLoading,
    lastUpdate: signalAnalysis.lastUpdate,

    currentStrategy,
    strategyLoading,
    switchStrategy,

    signalAnalysisRadarData,
    strategyComparisonData,
    realTimeSignalData,
    handoverLatencyData: realChart.handoverLatencyData,
    constellationComparisonData: realChart.constellationComparisonData,

    refreshAll: () => {
        signalAnalysis.refreshData();
        timeSync.fetchTimeSyncData();
        algoPerf.fetchAlgorithmPerformance();
        complexity.fetchComplexityComparison();
        optimization.fetchOptimizationData();
    }
  };
}; 