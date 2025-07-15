/**
 * RL 監控組件模組導出
 * 提供統一的接口供外部使用
 */

// 主組件
export { default as RLMonitoringPanel } from './RLMonitoringPanel';

// 子組件
export { default as TrainingStatusSection } from './sections/TrainingStatusSection';

// Hooks
export { useRLMonitoring, rlMonitoringEvents } from './hooks/useRLMonitoring';

// 類型定義
export * from './types/rl-monitoring.types';

// 工具函數
export { apiTester } from './utils/apiTester';

// 測試組件
export { default as APITestPanel } from './test/APITestPanel';

// 為 @todo.md 提供的標準接口
import RLMonitoringPanel from './RLMonitoringPanel';
import { useRLMonitoring, rlMonitoringEvents } from './hooks/useRLMonitoring';
import { RLMonitoringInterface, RLMonitoringPanelProps } from './types/rl-monitoring.types';

/**
 * 標準 RL 監控接口實現
 * 供 @todo.md 整合使用
 */
export const RLMonitoringInterface: RLMonitoringInterface = {
  component: RLMonitoringPanel,
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
  events: rlMonitoringEvents,
  utils: {
    exportData: async (_format: 'json' | 'csv' | 'excel') => {
      // 導出當前監控數據
      // Note: This should be called from within a component context
      // For now, return empty data structure
      const dataStr = JSON.stringify({}, null, 2);
      return new Blob([dataStr], { type: 'application/json' });
    },
    resetMonitoring: async () => {
      // 重置監控狀態
      console.log('Resetting RL monitoring...');
    },
    switchAlgorithm: async (algorithm: string) => {
      // 切換算法
      console.log(`Switching to algorithm: ${algorithm}`);
    }
  }
};

// 便捷導出
export const createRLMonitoringPanel = (props: Partial<RLMonitoringPanelProps> = {}) => {
  const defaultProps: RLMonitoringPanelProps = {
    mode: 'standalone',
    height: '100vh',
    refreshInterval: 2000,
    ...props
  };
  
  return RLMonitoringPanel;
};

/**
 * 版本信息
 */
export const VERSION = '1.0.0';
export const BUILD_INFO = {
  version: VERSION,
  name: '@tr.md RL Monitoring System',
  description: '獨立的 RL 訓練監控系統',
  build_date: new Date().toISOString(),
  features: [
    'Real-time training monitoring',
    'Algorithm performance comparison', 
    'Phase 3 visualization integration',
    'WebSocket real-time updates',
    'Research data management'
  ]
};