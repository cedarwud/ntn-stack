# 組件清單分析報告

## 📊 分析結果概覽 (⚠️ 重大發現更新)
- **總檔案數**: ~150+ 個組件和服務文件
- **實際顯示組件**: ~15 個檔案 (經驗證真正在UI中可見的)
- **虛假保留組件**: ~40 個檔案 (標記為保留但實際未顯示)
- **建議移除**: ~60 個檔案 (包含過時、未使用、無後端支持的組件)
- **死代碼發現**: 大量組件沒有路由或調用，屬於過度設計
- **需要合併**: ~15 個重複服務

---

## ❌ 建議移除的檔案

### UAV 編隊協調功能 (過度複雜，部分移除)
```
# 注意：根據統一方針，僅移除編隊協調邏輯，保留基本UAV和多UE功能
components/domains/simulation/coordination/UAVSwarmCoordination.tsx  # 部分移除 (編隊邏輯)
# UAVFlight.tsx 和 UAVSelectionPanel.tsx 保留但簡化
```

### 預測性維護組件 (非研究核心)
```
components/domains/analytics/performance/PredictiveMaintenanceViewer.tsx
```

### 監控與分析組件 (暫時用不到)
```
components/domains/monitoring/realtime/CoreNetworkSyncViewer.tsx
services/healthMonitor.ts
services/prometheusApi.ts
```

### 重複的 API 服務 (保留較新版本)
```
services/netstackApi.ts                    # 保留 netstack-api.ts
services/api-client.ts                     # 保留 api.ts
services/precomputedDataService.ts         # 保留 PrecomputedOrbitService.ts
```

---

## ✅ 實際顯示的核心組件 (經驗證)

### 衛星相關組件 (真正在UI中顯示)
```
components/domains/satellite/ConstellationSelectorCompact.tsx  # ✅ 在Sidebar中顯示
components/domains/satellite/visualization/DynamicSatelliteRenderer.tsx  # ✅ 在StereogramView/MainScene中使用
```

### ❌ 虛假保留的衛星組件 (實際未顯示)
```
components/domains/satellite/ConstellationSelector.tsx          # ❌ 未被使用
components/domains/satellite/SatelliteAnalysisPage.tsx         # ❌ 沒有路由，不會顯示
components/domains/satellite/SatelliteAnimationViewer.tsx      # ❌ 未被使用  
components/domains/satellite/TimelineControl.tsx              # ❌ 未被任何組件導入
```

### ❌ 換手決策組件 (完全未使用)
```
components/domains/handover/execution/HandoverStatusPanel.tsx  # ❌ enabled永遠為false，不會顯示
components/domains/handover/visualization/          # ❌ 整個目錄未被使用
```

### ❌ 統一決策中心 (完全虛假)
```
components/unified-decision-center/DecisionControlCenterSimple.tsx  # ❌ API 404錯誤，虛假界面
```

### ❌ 虛假保留的統一決策中心組件
```
components/unified-decision-center/DecisionControlCenter.tsx        # ❌ 沒有路由，不會顯示
components/unified-decision-center/AlgorithmExplainabilityPanel.tsx # ❌ 沒有後端API支持  
components/unified-decision-center/CandidateSelectionPanel.tsx      # ❌ 沒有真實數據
components/unified-decision-center/DecisionFlowTracker.tsx          # ❌ 僅內部使用，無意義
components/unified-decision-center/RealtimeEventStreamer.ts         # ❌ WebSocket後端不存在
components/unified-decision-center/VisualizationCoordinator.ts      # ❌ 僅內部使用，無意義
```

### Sionna 仿真集成 (完全虛假)
```
components/domains/simulation/sionna/index.ts      # ❌ 空文件，沒有實際內容
# 後端API /api/v1/sionna/* 全部返回404錯誤
```

### 場景與視圖組件 (真正顯示的主要UI)
```
components/scenes/StereogramView.tsx              # ✅ 主要UI路由 /:scenes/stereogram
components/scenes/FloorView.tsx                  # ✅ 地面視圖路由 /:scenes/floor-plan  
components/scenes/StaticModel.tsx                # ❓ 需進一步驗證是否被使用
```

### 座標與設備管理 (在Sidebar中顯示)
```
components/domains/coordinates/CoordinateDisplay.tsx     # ✅ 座標顯示
components/domains/device/management/DeviceItem.tsx     # ✅ 設備項目管理  
components/domains/device/management/DevicePopover.tsx  # ✅ 設備彈出設定
components/domains/device/visualization/DeviceOverlaySVG.tsx # ✅ 設備覆蓋層
```

### 核心 API 服務 (保留)
```
services/netstack-api.ts                          # 新版本
services/api.ts                                   # 基礎 API
services/PrecomputedOrbitService.ts               # 軌道預計算
services/realSatelliteService.ts                 # 真實衛星服務
services/HistoricalTrajectoryService.ts          # 軌跡歷史
services/unified-data-service.ts                 # 統一數據服務
services/deviceApi.ts                            # 設備API
services/coordinateApi.ts                        # 座標API
```

---

## ✅ 組件評估結果 (已澄清用途)

### 座標與設備管理 ✅ (側邊欄與平面圖設定管理)
**用途說明**: 用於側邊欄設備控制和平面圖的設定管理顯示
```
components/domains/coordinates/CoordinateDisplay.tsx     # 保留 - 座標顯示
components/domains/device/management/DeviceItem.tsx     # 保留 - 設備項目管理
components/domains/device/management/DevicePopover.tsx  # 保留 - 設備彈出設定
components/domains/device/visualization/DeviceOverlaySVG.tsx # 保留 - 設備覆蓋層
services/deviceApi.ts                                   # 保留 - 設備API
services/coordinateApi.ts                              # 保留 - 座標API
```

### 監控與分析 ❌ (暫時用不到)
**用途說明**: 監控分析功能現在暫時用不到
```
components/domains/monitoring/realtime/CoreNetworkSyncViewer.tsx  # 移除 - 實時監控
services/healthMonitor.ts                                        # 移除 - 健康監控  
services/prometheusApi.ts                                        # 移除 - 指標監控
```

### 場景與視圖組件 ✅ (衛星移動與換手動畫場景渲染)
**用途說明**: 用來渲染衛星移動跟換手動畫的場景組件
```
components/scenes/StereogramView.tsx              # 保留 - 立體圖視圖場景
components/scenes/FloorView.tsx                  # 保留 - 地面視圖場景  
components/scenes/StaticModel.tsx                # 保留 - 靜態模型場景
```

---

## 🔄 需要合併的重複服務

### API 服務合併計劃
1. **NetStack API**: `netstack-api.ts` ← `netstackApi.ts` ← `netstack-precomputed-api.ts`
2. **基礎 API**: `api.ts` ← `api-client.ts` ← `base-api.ts`  
3. **預計算服務**: `PrecomputedOrbitService.ts` ← `precomputedDataService.ts`

---

## 📦 Package.json 依賴檢查結果

### ✅ 必要依賴 (全部保留)
- `@react-three/drei, @react-three/fiber` - 3D 可視化核心
- `three` - 3D 渲染引擎  
- `axios` - HTTP 客戶端
- `socket.io-client` - 實時通信
- `date-fns` - 時間處理 (軌道計算需要)
- `lodash` - 工具函數
- `react, react-dom` - 核心框架

### 📋 開發依賴 (全部合理)
- TypeScript 相關工具鏈
- 測試框架 (Vitest, Testing Library)
- 構建工具 (Vite)
- 代碼品質工具 (ESLint)

**結論**: Package.json 依賴項目前都是必要的，沒有明顯需要移除的套件。

---

## 🎯 重構優先級建議

### 🔴 高優先級 (立即執行)
1. **簡化 UAV 組件** - 移除編隊協調邏輯，保留基本多UE功能
2. **移除監控分析組件** - 暫時用不到實時監控功能
3. **移除預測性維護組件** - 非研究核心功能
4. **合併重複 API 服務** - 提升維護性

### 🟡 中優先級 (已澄清，按計劃執行)  
1. ✅ **保留設備管理組件** - 用於側邊欄與平面圖設定管理
2. ❌ **移除監控組件** - 暫時用不到實時監控功能  
3. ✅ **保留場景視圖組件** - 用於衛星移動與換手動畫場景渲染
4. 重新組織 UI 組件結構

### 🟢 低優先級 (後期優化)
1. 性能優化
2. 測試覆蓋率提升
3. 文檔完善

---

## 🚨 重大發現總結

### 📊 實際可見組件統計 (修正後)
- **主要UI**: StereogramView, FloorView (2個)
- **側邊欄功能**: ConstellationSelectorCompact, 設備管理組件 (5個)  
- **3D渲染**: DynamicSatelliteRenderer (1個)
- **基礎服務**: 核心API服務和配置 (6個)
- **總計實際使用**: ~14個真正有用的組件 (更正：HandoverStatusPanel不會顯示)

### ❌ 死代碼問題嚴重
- **虛假保留組件**: ~40個標記保留但實際不顯示
- **過度設計**: 統一決策中心、Sionna集成、時間軸控制等
- **沒有後端支持**: WebSocket、強化學習API、Sionna API全部404
- **沒有路由**: 大量組件沒有對應的路由配置

### 🎯 修正後的重構策略  
- **核心保留**: 僅保留真正在UI中顯示的15個組件
- **大量移除**: 移除~60個過時、未使用、虛假保留的組件
- **簡化架構**: 專注於實際可用的衛星渲染和設備管理功能
- **提升效率**: 移除死代碼可大幅減少維護負擔和bundle大小

**結論**: 項目存在嚴重的過度設計和死代碼問題，需要大幅度簡化。
