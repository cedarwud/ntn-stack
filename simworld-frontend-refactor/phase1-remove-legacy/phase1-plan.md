# Phase 1: 組件功能評估與重分類 (已更正)

## 🎯 目標  
重新評估組件與 LEO Satellite Handover 研究的相關性，保留並強化核心研究功能

## 📋 重構方針調整
根據用戶需求：**保留單UE和多UE基本功能，但移除編隊群集協調的複雜功能**

## 📋 組件重分類結果

### ✅ UAV 基本功能組件 (調整後保留)
**🔄 調整：保留核心UE功能，移除複雜編隊協調**
- ✅ `components/domains/device/visualization/UAVFlight.tsx` - **完全保留** (UAV作為UE渲染)
- 🔄 `components/layout/sidebar/UAVSelectionPanel.tsx` - **簡化保留** (多UE選擇，移除編隊控制)
- 🔄 `components/domains/simulation/coordination/UAVSwarmCoordination.tsx` - **部分保留** (多UE管理，移除編隊邏輯)

**調整後的 UAV 功能價值**:
- 🎯 **移動 UE 模擬**: UAV 作為 Sionna RX，模擬真實用戶設備
- 🎯 **多UE場景支援**: 支援建立和控制多個UE
- 🎯 **單/多UE換手**: 靈活的換手場景測試
- ❌ **移除編隊協調**: V字形、圓形、網格等複雜編隊邏輯

### 🔴 確實需要移除的組件 (經驗證)

#### 🔧 虛假保留的衛星組件 (實際未顯示)
- `components/domains/satellite/SatelliteAnalysisPage.tsx` - ❌ 沒有路由，不會顯示
- `components/domains/satellite/TimelineControl.tsx` - ❌ 未被任何組件導入使用
- `components/domains/satellite/SatelliteAnimationViewer.tsx` - ❌ 未被使用

#### 🔧 虛假保留的統一決策中心 (沒有後端支持)
- `components/unified-decision-center/DecisionControlCenter.tsx` - ❌ 沒有路由，不會顯示
- `components/unified-decision-center/AlgorithmExplainabilityPanel.tsx` - ❌ 沒有後端API支持  
- `components/unified-decision-center/VisualizationCoordinator.ts` - ❌ 僅內部使用，無意義
- `components/unified-decision-center/RealtimeEventStreamer.ts` - ❌ WebSocket後端不存在

#### 🔧 空實現的Sionna集成 (完全虛假)
- `components/domains/simulation/sionna/index.ts` - ❌ 空文件
- 相關的Sionna API調用 - ❌ 後端全部404錯誤

#### 🔧 編隊群集協調功能 (過度複雜)
- `UAVSwarmCoordination.tsx` 中的編隊邏輯 (V字形、圓形、網格編隊)

#### 🔧 預測性維護和監控組件 (非核心功能)
- `components/domains/analytics/performance/PredictiveMaintenanceViewer.tsx`
- `components/domains/monitoring/realtime/CoreNetworkSyncViewer.tsx`

## ✅ 經驗證實際使用的組件
- `components/domains/device/management/` - ✅ 在Sidebar中顯示，確定保留
- `components/domains/coordinates/CoordinateDisplay.tsx` - ✅ 在Sidebar中顯示，確定保留

## 🗑️ 文件清理
- 移除廢棄的文檔文件
- 清理不相關的測試文件
- 移除過時的配置文件

## 📝 調整後的執行步驟
1. **簡化 UAV 功能為核心需求**
   - 保留 `UAVFlight.tsx` 的完整渲染功能
   - 簡化 `UAVSelectionPanel.tsx`，保留多選功能，移除編隊控制
   - 修改 `UAVSwarmCoordination.tsx`，保留多UE管理，移除編隊邏輯

2. **移除複雜編隊功能**  
   - 移除V字形、圓形、網格等編隊模式
   - 移除協調任務管理和群集統計
   - 保留基本的多UE建立和位置控制

3. **保持系統集成完整**
   - 確保單UE和多UE都能與衛星可見性計算集成
   - 驗證簡化後的UE移動仍能觸發換手決策
   - 測試 Sionna RX (UE) 與 TX (衛星) 的基本協調功能
