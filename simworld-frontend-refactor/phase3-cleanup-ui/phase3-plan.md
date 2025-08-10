# Phase 3: UI 組件結構優化

## 🎯 目標
優化 UI 組件結構，保留 LEO Satellite Handover 核心功能

## 🎯 核心保留組件 (LEO Satellite Handover 相關)

### 🛰️ 衛星核心組件 (絕對保留)
- `domains/satellite/` - 所有衛星相關組件
  - `ConstellationSelector.tsx` - 星座選擇器
  - `SatelliteAnalysisPage.tsx` - 衛星分析頁面
  - `SatelliteAnimationViewer.tsx` - 衛星動畫查看器
  - `TimelineControl.tsx` - 時間軸控制
  - `visualization/DynamicSatelliteRenderer.tsx` - 動態衛星渲染器

### 🔄 換手決策組件 (核心功能)
- `domains/handover/` - 換手相關組件
  - `execution/HandoverStatusPanel.tsx` - 換手狀態面板
  - `visualization/` - 換手可視化組件

### 🎮 決策中心組件 (重要功能)
- `unified-decision-center/` - 統一決策中心
  - `DecisionControlCenter.tsx` - 決策控制中心
  - `AlgorithmExplainabilityPanel.tsx` - 算法解釋面板
  - `CandidateSelectionPanel.tsx` - 候選選擇面板

### 📊 Sionna 仿真組件 (研究相關)
- `domains/simulation/sionna/` - Sionna 仿真庫集成

## 🤔 需要評估的組件

### 📍 座標系統組件
- `domains/coordinates/CoordinateDisplay.tsx` - 可能對衛星位置顯示有用

### 📡 設備管理組件
- `domains/device/management/` - 可能對地面站管理有用
- `domains/device/visualization/DeviceOverlaySVG.tsx` - 設備覆蓋層可視化

### 📊 監控組件
- `domains/monitoring/realtime/CoreNetworkSyncViewer.tsx` - 實時網路同步監控

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
├── simulation/             # 仿真相關 (Sionna, etc.)
├── visualization/          # 3D 可視化組件
├── ui/                     # 通用 UI 組件
└── legacy/                 # 待移除的過時組件
```

## ✅ 驗證檢查點
- [ ] 核心衛星換手功能完整保留
- [ ] 3D 可視化效果正常
- [ ] Sionna 仿真集成工作正常
- [ ] 用戶介面響應流暢
- [ ] 無斷裂的組件引用
