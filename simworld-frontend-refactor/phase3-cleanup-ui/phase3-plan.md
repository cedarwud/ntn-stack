# Phase 3: UI 組件結構優化 🔄 開始執行

## 🎯 目標
優化 UI 組件結構，保留 LEO Satellite Handover 核心功能

## 📊 當前狀態分析 (2025-08-11)
經檢查發現 Phase 1 和 Phase 2 尚未完全完成：
- **Phase 1**: Sionna 空實現和 UAV 編隊協調仍存在
- **Phase 2**: 發現25個API服務文件，重複服務未整合  
- **決策**: 直接進入 Phase 3，同時處理前期遺留問題

## 🎯 核心保留組件 (LEO Satellite Handover 相關)

### 🛰️ 衛星核心組件 (經驗證後分類)
- **✅ 實際使用的組件**:
  - `ConstellationSelectorCompact.tsx` - ✅ 星座選擇器 (在Sidebar顯示)
  - `visualization/DynamicSatelliteRenderer.tsx` - ✅ 動態衛星渲染器 (在主視圖顯示)
- **❌ 虛假保留組件 (實際未使用)**:
  - `ConstellationSelector.tsx` - ❌ 未被使用
  - `SatelliteAnalysisPage.tsx` - ❌ 沒有路由，不會顯示
  - `SatelliteAnimationViewer.tsx` - ❌ 未被使用
  - `TimelineControl.tsx` - ❌ 未被任何組件導入

### 🔄 換手決策組件 (經驗證後分類)
- **✅ 實際使用的組件**:
  - `execution/HandoverStatusPanel.tsx` - ✅ 在StereogramView中顯示
- **❌ 虛假保留組件 (實際未使用)**:
  - `visualization/` - ❌ 整個目錄未被使用

### 🎮 決策中心組件 (經驗證後分類)
- **✅ 實際使用的組件**:
  - `DecisionControlCenterSimple.tsx` - ✅ 有路由 /decision-center
- **❌ 虛假保留組件 (沒有後端支持)**:
  - `DecisionControlCenter.tsx` - ❌ 沒有路由，不會顯示
  - `AlgorithmExplainabilityPanel.tsx` - ❌ 沒有後端API支持
  - `CandidateSelectionPanel.tsx` - ❌ 沒有真實數據
  - `DecisionFlowTracker.tsx` - ❌ 僅內部使用
  - `VisualizationCoordinator.ts` - ❌ 僅內部使用
  - `RealtimeEventStreamer.ts` - ❌ WebSocket後端不存在

### 📊 Sionna 仿真組件 (❌ 完全虛假實現)
- `domains/simulation/sionna/index.ts` - ❌ **空文件，建議完全移除**
- 相關 Sionna API 調用 - ❌ **後端全部404錯誤**

## ✅ 經驗證的其他組件

### 📍 座標系統組件 (✅ 實際使用)
- `domains/coordinates/CoordinateDisplay.tsx` - ✅ 在Sidebar中顯示

### 📡 設備管理組件 (✅ 實際使用)  
- `domains/device/management/DeviceItem.tsx` - ✅ 在Sidebar中顯示
- `domains/device/management/DevicePopover.tsx` - ✅ 設備彈出設定
- `domains/device/visualization/DeviceOverlaySVG.tsx` - ✅ 設備覆蓋層可視化

### 📊 監控組件 (❌ 暫時用不到)
- `domains/monitoring/realtime/CoreNetworkSyncViewer.tsx` - ❌ 實時監控暫不需要

## 🧹 UI 結構優化

### 第一階段: 組件分類
1. 核心組件 - 直接相關於 LEO Satellite Handover
2. 支援組件 - 可能有用但非核心
3. 過時組件 - 明確與研究無關

### 第二階段: 重構組件層次
1. 重新組織 domains 結構
2. 合併相似功能的組件
3. 簡化組件導入路徑

### 第三階段: 清理樣式文件
1. 移除未使用的 CSS/SCSS 文件
2. 整合重複的樣式定義
3. 優化 CSS 類名命名

## 📂 建議的新目錄結構
```
components/
├── core/                    # 核心 LEO Satellite 組件
│   ├── satellite/          # 衛星相關
│   ├── handover/           # 換手相關
│   └── decision/           # 決策相關
├── scenes/                 # 主要UI場景 (StereogramView, FloorView)
├── visualization/          # 3D 可視化組件
├── ui/                     # 通用 UI 組件
└── legacy/                 # 待移除的過時組件
```

## ✅ 驗證檢查點
- [ ] 核心衛星換手功能完整保留 (僅保留實際使用的組件)
- [ ] 3D 可視化效果正常 (DynamicSatelliteRenderer)
- [ ] 設備管理功能正常 (Sidebar中的設備控制)
- [ ] 用戶介面響應流暢
- [ ] 無斷裂的組件引用
- [ ] 死代碼清理完成 (Sionna、未使用的決策中心等)
