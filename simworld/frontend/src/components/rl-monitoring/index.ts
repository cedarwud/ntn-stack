/**
 * RL 監控系統導出
 * @tr.md 項目的核心組件
 */

// 主組件
export { default as RLMonitoringPanel } from './RLMonitoringPanel';

// 子組件
export { default as TrainingStatusSection } from './sections/TrainingStatusSection';
export { default as AlgorithmComparisonSection } from './sections/AlgorithmComparisonSection';
export { default as VisualizationSection } from './sections/VisualizationSection';
export { default as RealTimeMetricsSection } from './sections/RealTimeMetricsSection';
export { default as ResearchDataSection } from './sections/ResearchDataSection';

// Hooks
export { useRLMonitoring, rlMonitoringEvents } from './hooks/useRLMonitoring';

// 類型定義
export * from './types/rl-monitoring.types';

// 標準整合接口 (為 @todo.md 使用)
export const RLMonitoringInterface = {
  // 主組件
  component: RLMonitoringPanel,
  
  // 獨立 hooks
  hooks: {
    useRLStatus: () => {
      const { training } = useRLMonitoring({ refreshInterval: 2000 });
      return training;
    },
    useAlgorithmMetrics: () => {
      const { algorithms } = useRLMonitoring({ refreshInterval: 2000 });
      return algorithms;
    },
    useVisualization: () => {
      const { visualization } = useRLMonitoring({ refreshInterval: 2000 });
      return visualization;
    },
    useRealTimeData: () => {
      const { realtime } = useRLMonitoring({ refreshInterval: 2000 });
      return realtime;
    }
  },
  
  // 事件系統
  events: rlMonitoringEvents,
  
  // 工具函數
  utils: {
    exportData: async (format: 'json' | 'csv' | 'excel') => {
      const { utils } = useRLMonitoring({ refreshInterval: 2000 });
      return utils.exportData(format);
    },
    resetMonitoring: async () => {
      const { utils } = useRLMonitoring({ refreshInterval: 2000 });
      return utils.resetMonitoring();
    },
    switchAlgorithm: async (algorithm: string) => {
      const { utils } = useRLMonitoring({ refreshInterval: 2000 });
      return utils.switchAlgorithm(algorithm);
    }
  }
};

// 預設導出
export default RLMonitoringPanel;/**
 * RL 監控系統導出
 * @tr.md 項目的核心組件
 */

// 主組件
export { default as RLMonitoringPanel } from './RLMonitoringPanel';

// 子組件
export { default as TrainingStatusSection } from './sections/TrainingStatusSection';
export { default as AlgorithmComparisonSection } from './sections/AlgorithmComparisonSection';
export { default as VisualizationSection } from './sections/VisualizationSection';
export { default as RealTimeMetricsSection } from './sections/RealTimeMetricsSection';
export { default as ResearchDataSection } from './sections/ResearchDataSection';

// Hooks
export { useRLMonitoring, rlMonitoringEvents } from './hooks/useRLMonitoring';

// 類型定義
export * from './types/rl-monitoring.types';

// 標準整合接口 (為 @todo.md 使用)
export const RLMonitoringInterface = {
  // 主組件
  component: RLMonitoringPanel,
  
  // 獨立 hooks
  hooks: {
    useRLStatus: () => {
      const { training } = useRLMonitoring({ refreshInterval: 2000 });
      return training;
    },
    useAlgorithmMetrics: () => {
      const { algorithms } = useRLMonitoring({ refreshInterval: 2000 });
      return algorithms;
    },
    useVisualization: () => {
      const { visualization } = useRLMonitoring({ refreshInterval: 2000 });
      return visualization;
    },
    useRealTimeData: () => {
      const { realtime } = useRLMonitoring({ refreshInterval: 2000 });
      return realtime;
    }
  },
  
  // 事件系統
  events: rlMonitoringEvents,
  
  // 工具函數
  utils: {
    exportData: async (format: 'json' | 'csv' | 'excel') => {
      const { utils } = useRLMonitoring({ refreshInterval: 2000 });
      return utils.exportData(format);
    },
    resetMonitoring: async () => {
      const { utils } = useRLMonitoring({ refreshInterval: 2000 });
      return utils.resetMonitoring();
    },
    switchAlgorithm: async (algorithm: string) => {
      const { utils } = useRLMonitoring({ refreshInterval: 2000 });
      return utils.switchAlgorithm(algorithm);
    }
  }
};

// 預設導出
export default RLMonitoringPanel;