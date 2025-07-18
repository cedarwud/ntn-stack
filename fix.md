# Fetch 調用修復計劃

## 問題描述
前端有多個文件使用直接 `fetch('/api/...')` 調用，這些調用會繞過 Vite 開發代理系統，導致 404 錯誤。

## 為什麼需要修復
- 直接 fetch 調用路徑如 `/api/v1/rl/health` 會向 `http://localhost:5173/api/v1/rl/health` 發送請求
- 但實際的 API 服務運行在 `http://localhost:8080`  
- Vite 代理配置將 `/netstack/*` 代理到 `http://localhost:8080/*`
- 所以應該使用 `netstackFetch('/api/v1/rl/health')` 來正確路由到後端

## 修復方法
1. 導入 `netstackFetch` from `../../../config/api-config` (路徑根據文件位置調整)
2. 將 `fetch('/api/...', options)` 替換為 `netstackFetch('/api/...', options)`

## 需要修復的文件清單

### 高優先級 (RL 監控相關)

#### 1. `/components/unified-decision-center/DecisionControlCenterSimple.tsx`
**問題**: Line 40 - `fetch('/api/v1/rl/health')`
**影響**: 系統健康檢查失敗
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../../config/api-config'

// 修改調用
const response = await netstackFetch('/api/v1/rl/health')
```

#### 2. `/services/enhanced-rl-monitoring.ts`
**問題**: 多個 fetch 調用 (Lines 286, 341, 355, 381, 394, 408, 428)
**影響**: RL 監控數據無法獲取
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../config/api-config'

// 修改所有 fetch 調用
- fetch('/api/v1/rl/status')
+ netstackFetch('/api/v1/rl/status')

- fetch('/api/v1/rl/training/sessions')
+ netstackFetch('/api/v1/rl/training/sessions')

- fetch('/api/v1/rl/performance/metrics')  
+ netstackFetch('/api/v1/rl/performance/metrics')

- fetch('/api/v1/rl/decisions/recent?limit=10')
+ netstackFetch('/api/v1/rl/decisions/recent?limit=10')

- fetch('/api/v1/rl/events/recent?limit=20')
+ netstackFetch('/api/v1/rl/events/recent?limit=20')

- fetch('/api/v1/rl/algorithms/control', { method: 'POST', ... })
+ netstackFetch('/api/v1/rl/algorithms/control', { method: 'POST', ... })

- fetch('/api/v1/rl/algorithms/switch', { method: 'POST', ... })
+ netstackFetch('/api/v1/rl/algorithms/switch', { method: 'POST', ... })
```

#### 3. `/components/unified-monitoring/hooks/useCrossSystemMonitoring.ts`
**問題**: Lines 224, 252, 274 - RL 相關 fetch 調用
**影響**: 跨系統監控失效
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../../../config/api-config'

// 修改調用
- fetch('/api/v1/rl/training/sessions', { signal: controller.signal })
+ netstackFetch('/api/v1/rl/training/sessions', { signal: controller.signal })

- fetch('/api/v1/rl/algorithms', { signal: controller.signal })
+ netstackFetch('/api/v1/rl/algorithms', { signal: controller.signal })

- fetch('/api/v1/rl/status', { signal: controller.signal })
+ netstackFetch('/api/v1/rl/status', { signal: controller.signal })
```

#### 4. `/components/unified-monitoring/index.ts`
**問題**: Lines 42, 61 - RL 健康檢查
**影響**: 統一監控面板數據錯誤
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../../config/api-config'

// 修改調用
- fetch('/api/v1/rl/health').then(r => r.json())
+ netstackFetch('/api/v1/rl/health').then(r => r.json())

- fetch('/api/v1/rl/health')
+ netstackFetch('/api/v1/rl/health')
```

#### 5. `/components/rl-monitoring/utils/apiTester.ts`
**問題**: Lines 170, 185 - Phase 3 端點測試
**影響**: API 測試功能失效
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../../../config/api-config'

// 修改調用
- fetch('/api/v1/rl/phase-3/visualizations/generate', { method: 'POST', ... })
+ netstackFetch('/api/v1/rl/phase-3/visualizations/generate', { method: 'POST', ... })

- fetch('/api/v1/rl/phase-3/explain/decision', { method: 'POST', ... })
+ netstackFetch('/api/v1/rl/phase-3/explain/decision', { method: 'POST', ... })
```

### 中優先級 (衛星操作相關)

#### 6. `/utils/satellite-cache.ts`
**問題**: Lines 154, 160 - 衛星數據獲取
**影響**: 衛星可視化數據無法獲取
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../config/api-config'

// 修改調用
- fetch('/api/v1/satellite-ops/visible_satellites?constellation=starlink&count=10&global_view=true')
+ netstackFetch('/api/v1/satellite-ops/visible_satellites?constellation=starlink&count=10&global_view=true')

- fetch('/api/v1/satellite-ops/visible_satellites?constellation=kuiper&count=10&global_view=true')  
+ netstackFetch('/api/v1/satellite-ops/visible_satellites?constellation=kuiper&count=10&global_view=true')
```

#### 7. `/utils/satelliteDebugger.ts`
**問題**: Line 272 - 衛星調試數據
**影響**: 衛星調試功能失效
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../config/api-config'

// 修改調用
- fetch('/api/v1/satellite-ops/visible_satellites?count=1&global_view=true', { method: 'GET' })
+ netstackFetch('/api/v1/satellite-ops/visible_satellites?count=1&global_view=true', { method: 'GET' })
```

### 低優先級 (特殊用途)

#### 8. `/hooks/useInfocomMetrics.ts`
**問題**: Line 52 - 算法性能數據
**影響**: InfoCom 論文數據顯示
**修復**:
```typescript
// 添加導入
import { netstackFetch } from '../config/api-config'

// 修改調用
- fetch('/api/algorithm-performance/infocom-2024-detailed')
+ netstackFetch('/api/algorithm-performance/infocom-2024-detailed')
```

#### 9. `/test/console-errors.test.tsx`
**問題**: Line 157 - 測試用 404 調用
**影響**: 這是故意的測試，可能不需要修復
**修復**: 保持原樣或添加註釋說明這是故意的測試

## 修復執行順序
1. 先修復高優先級的 RL 監控相關文件 (1-5)
2. 再修復中優先級的衛星操作文件 (6-7) 
3. 最後考慮低優先級文件 (8-9)

## 驗證方法
修復完成後：
1. 重啟容器：`make simworld-restart`
2. 檢查日誌：`docker logs simworld_frontend 2>&1 | grep -E "404|Error"`
3. 測試關鍵端點：
   - `curl http://localhost:5173/netstack/api/v1/rl/health`
   - `curl http://localhost:5173/netstack/api/v1/rl/training/sessions`
4. 確認前端功能正常工作

## 預期結果
- 無 404 錯誤日誌
- RL 監控功能正常
- 衛星數據正常顯示
- 系統健康檢查通過