# 🤖 RL 監控系統使用指南

## 📋 概述

RL 監控系統 (@tr.md) 是一個獨立的強化學習訓練監控平台，提供實時的 DQN、PPO、SAC 算法監控功能。

## 🚀 快速開始

### 基本使用

```tsx
import { RLMonitoringPanel } from '@/components/rl-monitoring';

function App() {
  return (
    <RLMonitoringPanel
      mode="standalone"
      height="100vh"
      refreshInterval={2000}
      onDataUpdate={(data) => console.log('RL Data:', data)}
      onError={(error) => console.error('RL Error:', error)}
    />
  );
}
```

### 嵌入模式（為 @todo.md 使用）

```tsx
import { RLMonitoringPanel } from '@/components/rl-monitoring';

function DecisionControlCenter() {
  return (
    <div className="unified-dashboard">
      {/* 其他 3D 視覺化組件 */}
      <HandoverAnimation3D />
      
      {/* 嵌入 RL 監控 */}
      <RLMonitoringPanel
        mode="embedded"
        height="400px"
        refreshInterval={2000}
      />
      
      {/* 更多組件... */}
    </div>
  );
}
```

## 🧩 組件結構

### 主組件

- **RLMonitoringPanel**: 主要監控面板
  - 支援獨立和嵌入兩種模式
  - 內建 5 個功能區塊
  - 完整的錯誤處理機制

### 子組件

1. **TrainingStatusSection**: 訓練狀態監控
   - 實時顯示 DQN/PPO/SAC 訓練進度
   - 算法切換控制
   - 健康狀態檢查

2. **AlgorithmComparisonSection**: 算法性能對比
   - 多維度性能比較
   - 排名和推薦系統
   - 統計顯著性測試

3. **VisualizationSection**: 決策透明化
   - Phase 3 視覺化引擎整合
   - 特徵重要性分析
   - 決策過程解釋

4. **RealTimeMetricsSection**: 實時監控
   - WebSocket 實時數據流
   - 系統資源監控
   - 事件流追蹤

5. **ResearchDataSection**: 研究數據管理
   - 實驗歷史記錄
   - 數據導出功能
   - 統計分析報告

## 🔧 API 接口

### useRLMonitoring Hook

```tsx
import { useRLMonitoring } from '@/components/rl-monitoring';

function MyComponent() {
  const {
    isLoading,
    error,
    data,
    refresh,
    toggleDqnTraining,
    togglePpoTraining,
    toggleSacTraining,
    utils
  } = useRLMonitoring({
    refreshInterval: 2000,
    enabled: true,
    autoStart: false
  });

  return (
    <div>
      {/* 使用數據... */}
      <button onClick={toggleDqnTraining}>
        {data.training.algorithms[0]?.training_active ? '停止' : '開始'} DQN 訓練
      </button>
    </div>
  );
}
```

### 事件系統

```tsx
import { rlMonitoringEvents } from '@/components/rl-monitoring';

// 監聽訓練開始事件
rlMonitoringEvents.onTrainingStart.on((event) => {
  console.log(`${event.algorithm} 開始訓練`);
});

// 監聽算法切換事件
rlMonitoringEvents.onAlgorithmSwitch.on((event) => {
  console.log(`算法從 ${event.from_algorithm} 切換到 ${event.to_algorithm}`);
});

// 監聽數據更新事件
rlMonitoringEvents.onDataUpdate.on((event) => {
  console.log('監控數據更新:', event.data);
});
```

## 📊 數據格式

### 訓練數據結構

```typescript
interface TrainingData {
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number; // 0-1
  currentEpisode: number;
  totalEpisodes: number;
  algorithms: AlgorithmStatus[];
}

interface AlgorithmStatus {
  algorithm: 'dqn' | 'ppo' | 'sac';
  status: string;
  progress: number;
  training_active: boolean;
  metrics: {
    episodes_completed: number;
    average_reward: number;
    success_rate: number;
    // ... 其他指標
  };
}
```

### 性能數據結構

```typescript
interface PerformanceMetrics {
  latency: number;
  success_rate: number;
  throughput: number;
  error_rate: number;
  response_time: number;
  resource_utilization: {
    cpu: number;
    memory: number;
    gpu?: number;
  };
}
```

## 🎨 樣式自定義

### CSS 變數

```scss
.rl-monitoring-panel {
  --primary-color: #667eea;
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --background-color: #ffffff;
  --text-color: #1f2937;
}
```

### 主題覆蓋

```scss
// 自定義主色調
.rl-monitoring-panel--custom-theme {
  --primary-color: #your-color;
  
  .section-title {
    color: var(--primary-color);
  }
}
```

## 🔌 API 端點整合

### 後端 API 配置

```typescript
// 在 useRLMonitoring 中配置的 API 端點
const API_ENDPOINTS = {
  health: '/api/v1/rl/health',
  status: '/api/v1/rl/status',
  training: '/api/v1/rl/training/status-summary',
  performance: '/api/v1/rl/performance/report',
  visualization: '/api/v1/rl/phase-3/visualizations/generate',
  websocket: '/ws/rl-monitor'
};
```

### 自定義 API 端點

```tsx
// 如需自定義 API 端點，可以修改 useRLMonitoring hook
const customRLMonitoring = useRLMonitoring({
  refreshInterval: 2000,
  apiBaseUrl: 'http://your-api-server:8080',
  endpoints: {
    // 自定義端點...
  }
});
```

## 🧪 測試

### 組件測試

```tsx
import { render, screen } from '@testing-library/react';
import { RLMonitoringPanel } from '@/components/rl-monitoring';

test('RL monitoring panel renders correctly', () => {
  render(<RLMonitoringPanel mode="standalone" />);
  
  expect(screen.getByText('RL 訓練監控系統')).toBeInTheDocument();
  expect(screen.getByText('🚀 訓練狀態')).toBeInTheDocument();
});
```

### API 測試

```tsx
import { apiTester } from '@/components/rl-monitoring';

// 測試 API 連通性
const testResults = await apiTester.testAllEndpoints();
console.log('API 測試結果:', testResults);
```

## 📱 響應式設計

組件支援桌面和移動端，會自動適配不同螢幕尺寸：

- **桌面端**: 完整功能展示
- **平板端**: 優化布局
- **手機端**: 簡化界面

## 🔒 錯誤處理

### 內建錯誤恢復

- 自動重試機制
- 降級顯示
- 錯誤邊界保護
- 用戶友好的錯誤信息

### 自定義錯誤處理

```tsx
<RLMonitoringPanel
  onError={(error) => {
    // 自定義錯誤處理邏輯
    sendErrorToLoggingService(error);
    showUserNotification('監控系統暫時不可用');
  }}
/>
```

## 📚 更多資源

- [TR.md 項目文檔](../../tr.md)
- [API 文檔](../../../netstack/docs/api.md)
- [開發指南](./DEVELOPMENT.md)
- [測試報告](./test/README.md)

---

**版本**: 1.0.0  
**最後更新**: 2025-01-25  
**開發團隊**: NTN Stack Team