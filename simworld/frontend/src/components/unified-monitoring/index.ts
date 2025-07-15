/**
 * 統一監控系統導出 - Phase 2
 */

export { UnifiedMonitoringCenter } from './UnifiedMonitoringCenter';
export { useCrossSystemMonitoring } from './hooks/useCrossSystemMonitoring';

// 重新導出現有監控組件以便統一使用
export { SystemHealthViewer, AlertsViewer } from '../monitoring';
export { RLMonitoringPanel } from '../rl-monitoring';

// 導入組件類型
import { UnifiedMonitoringCenter } from './UnifiedMonitoringCenter';
import { useCrossSystemMonitoring } from './hooks/useCrossSystemMonitoring';

// 統一監控接口
export interface UnifiedMonitoringInterface {
  // 主組件
  component: typeof UnifiedMonitoringCenter;
  
  // Hook
  hook: typeof useCrossSystemMonitoring;
  
  // 工具函數
  utils: {
    getSystemHealth: () => Promise<any>;
    refreshAllSystems: () => Promise<void>;
    exportMonitoringReport: (format: 'json' | 'csv') => Promise<Blob>;
  };
}

// 為 @todo.md 階段3-4 提供的整合接口
export const UnifiedMonitoringInterface: UnifiedMonitoringInterface = {
  component: UnifiedMonitoringCenter,
  hook: useCrossSystemMonitoring,
  utils: {
    getSystemHealth: async () => {
      // 獲取系統健康狀態的工具函數
      try {
        const [simworldHealth, netstackHealth] = await Promise.all([
          fetch('/system/health').then(r => r.json()),
          fetch('/api/v1/rl/health').then(r => r.json())
        ]);
        
        return {
          simworld: simworldHealth,
          netstack: netstackHealth,
          timestamp: new Date().toISOString()
        };
      } catch (error) {
        console.error('Failed to get system health:', error);
        return null;
      }
    },
    
    refreshAllSystems: async () => {
      // 刷新所有系統的工具函數
      try {
        await Promise.all([
          fetch('/system/health'),
          fetch('/api/v1/rl/health'),
          fetch('/interference/ai-ran/netstack/status')
        ]);
      } catch (error) {
        console.error('Failed to refresh all systems:', error);
        throw error;
      }
    },
    
    exportMonitoringReport: async (format: 'json' | 'csv') => {
      // 導出監控報告的工具函數
      try {
        const health = await UnifiedMonitoringInterface.utils.getSystemHealth();
        
        if (format === 'json') {
          const jsonData = JSON.stringify(health, null, 2);
          return new Blob([jsonData], { type: 'application/json' });
        } else {
          // CSV 格式
          const csvData = `System,Status,Timestamp\n` +
            `SimWorld,${health?.simworld?.status || 'unknown'},${health?.timestamp || ''}\n` +
            `NetStack,${health?.netstack?.status || 'unknown'},${health?.timestamp || ''}`;
          return new Blob([csvData], { type: 'text/csv' });
        }
      } catch (error) {
        console.error('Failed to export monitoring report:', error);
        throw error;
      }
    }
  }
}; 