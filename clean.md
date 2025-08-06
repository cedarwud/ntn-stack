# 🛠️ 前端衛星渲染邏輯清理計劃

**版本**: 1.0  
**建立日期**: 2025-08-06  
**目標**: 整合重複的衛星渲染邏輯和API端點，減少代碼複雜度

## 📊 現狀分析

### 🔍 重複邏輯識別結果

經過詳細分析，發現以下重複和冗余：

#### 1. 衛星API服務重複 ⚠️ **嚴重重複**
```
services/simworld-api.ts              - 主要的衛星數據服務 (actively used)
services/satelliteApi.ts              - 標準化API但未被使用 (unused)  
services/netstack-api.ts              - NetStack專用API (specific use)
services/netstack-precomputed-api.ts  - 預計算數據API (specific use)
services/PrecomputedOrbitService.ts   - 軌道預計算服務 (specific use)
services/HistoricalTrajectoryService.ts - 歷史軌跡服務 (specific use)
```

#### 2. 衛星渲染組件重複 ⚠️ **中度重複**
```
components/domains/satellite/visualization/DynamicSatelliteRenderer.tsx
components/domains/satellite/SatelliteAnimationViewer.tsx
components/domains/satellite/animation/HistoricalSatelliteController.tsx  
components/domains/satellite/animation/DEPRECATED_SatelliteAnimationController.tsx.bak (廢棄)
```

#### 3. 衛星數據獲取邏輯重複 ⚠️ **中度重複**
```
- useVisibleSatellites hook 在 simworld-api.ts 中
- Sidebar.tsx 中的獨立衛星數據獲取邏輯
- DataSyncContext.tsx 中的衛星數據同步
- 多個組件各自調用 netstackFetch
```

#### 4. 具體問題定位
**側邊欄"衛星 gNB":**
- 位置: `components/layout/sidebar/DeviceListPanel.tsx:79`
- 問題: 衛星數據獲取邏輯與主渲染器分離，可能造成數據不同步

**立體圖中的衛星渲染:**  
- 路徑: `MainScene.tsx` → `DynamicSatelliteRenderer.tsx`
- 問題: 使用多個服務獲取數據，邏輯複雜且容易出錯

## 🎯 清理計劃

### 📋 執行優先級與風險評估

| Phase | 優先級 | 風險等級 | 預估工時 | 影響範圍 |
|-------|--------|----------|----------|----------|
| Phase 1 | 🔥 高 | 🟢 低風險 | 30min | 廢棄檔案 |
| Phase 2 | 🔶 中 | 🟡 中風險 | 2-3hrs | 數據流 |  
| Phase 3 | 🔶 中 | 🟠 中高風險 | 3-4hrs | API整合 |
| Phase 4 | 🔸 低 | 🟢 低風險 | 1hr | 測試驗證 |

### 🚀 Phase 1: 清理廢棄檔案 (高優先級，低風險)

**目標**: 移除明確廢棄的檔案和未使用的代碼

**行動清單**:
```bash
# 1.1 刪除已廢棄的組件
rm simworld/frontend/src/components/domains/satellite/animation/DEPRECATED_SatelliteAnimationController.tsx.bak

# 1.2 刪除未使用的API服務  
rm simworld/frontend/src/services/satelliteApi.ts

# 1.3 檢查並移除import引用
grep -r "satelliteApi" simworld/frontend/src/
grep -r "DEPRECATED_SatelliteAnimationController" simworld/frontend/src/
```

**預期效果**:
- 減少 ~500行 無用代碼
- 清理 import 依賴關係
- 零功能影響風險

### 🔄 Phase 2: 統一數據流架構 (中優先級，中風險)

**目標**: 統一衛星數據獲取為單一來源，避免多處獲取造成的不同步

**2.1 統一數據源策略**
```typescript
// 目標架構：
DataSyncContext (唯一數據源)
    ↓
useVisibleSatellites (統一數據獲取)
    ↓  
Components (純展示，不直接獲取數據)
```

**2.2 修改範圍**
```typescript
// 修改文件列表：
- simworld/frontend/src/components/layout/Sidebar.tsx
  移除: _fetchVisibleSatellites 函數 (Line 139-239)
  修改: 完全依賴 DataSyncContext 數據

- simworld/frontend/src/components/layout/sidebar/DeviceListPanel.tsx  
  修改: 衛星數據顯示邏輯，移除獨立獲取

- simworld/frontend/src/contexts/DataSyncContext.tsx
  增強: 作為唯一衛星數據管理中心
```

**2.3 實施步驟**
1. 修改 `Sidebar.tsx`，移除獨立衛星數據獲取
2. 修改 `DeviceListPanel.tsx`，從props接收衛星數據
3. 驗證 `DataSyncContext` 的數據流向
4. 測試側邊欄和3D場景的數據同步

**預期效果**:
- 消除數據不同步問題
- 減少約 150-200行 重複邏輯
- 提高數據一致性

### 🔧 Phase 3: API服務整合 (中優先級，中高風險)

**目標**: 整合多個衛星API服務為統一接口

**3.1 創建統一服務**
```typescript
// 新建: services/UnifiedSatelliteService.ts
interface UnifiedSatelliteService {
  // 整合現有功能：
  getVisibleSatellites()        // from simworld-api.ts
  getPrecomputedOrbits()       // from netstack-precomputed-api.ts  
  getHistoricalTrajectories()  // from HistoricalTrajectoryService.ts
  getOrbitData()              // from PrecomputedOrbitService.ts
}
```

**3.2 服務整合映射**
```typescript
// 保留：
✅ simworld-api.ts (作為主要接口，但重構內部實現)
✅ netstack-api.ts (NetStack專用，不整合)

// 整合到 simworld-api.ts：
🔄 netstack-precomputed-api.ts → simworld-api.ts
🔄 PrecomputedOrbitService.ts → simworld-api.ts
🔄 HistoricalTrajectoryService.ts → simworld-api.ts

// 刪除：
❌ satelliteApi.ts (已在Phase 1刪除)
```

**3.3 重構步驟**
1. 分析各服務的核心功能
2. 在 `simworld-api.ts` 中添加整合接口
3. 逐步遷移組件使用新接口
4. 測試所有衛星相關功能
5. 刪除舊服務文件

**預期效果**:
- API調用統一化
- 減少 3-4個 服務文件
- 簡化import依賴

### ✅ Phase 4: 測試驗證 (低優先級，低風險)

**目標**: 確保清理後系統功能完整

**4.1 功能測試清單**
```bash
# 衛星顯示功能
□ 側邊欄"衛星 gNB"正常顯示
□ 3D場景衛星正常渲染  
□ 星座切換功能正常
□ 衛星動畫播放正常

# 數據同步測試
□ 側邊欄與3D場景數據一致
□ 星座切換時數據正確更新
□ 沒有重複的API調用

# 性能測試
□ 頁面載入時間沒有增加
□ 內存使用量沒有明顯增加
□ Console沒有錯誤訊息
```

**4.2 回歸測試**
```bash
# 運行前端測試
npm run test

# 運行linting檢查
npm run lint

# 運行build確認
npm run build
```

## 🎯 預期成果

### 📈 量化指標

**代碼減少**:
- 刪除文件: ~3-4個
- 減少代碼行數: ~800-1000行
- 減少import依賴: ~15-20個

**複雜度降低**:
- API服務數量: 6個 → 3個 (-50%)
- 衛星數據獲取點: 4個 → 1個 (-75%)
- 重複邏輯: 大幅減少

**維護性提升**:
- 單一數據源: 更容易調試
- 統一API接口: 更容易添加新功能
- 清晰職責分離: 更容易理解代碼

### 🚦 風險緩解策略

**備份策略**:
```bash
# 執行清理前創建備份
git checkout -b cleanup/satellite-rendering-consolidation
git add . && git commit -m "Backup before satellite rendering cleanup"
```

**分段測試**:
- 每個Phase完成後立即測試
- 發現問題立即回滾
- 確認無問題再繼續下一Phase

**回滾計劃**:
- Phase 1: 從git restore檔案
- Phase 2: 恢復removed邏輯
- Phase 3: 恢復deleted服務文件

## 📅 執行時間表

**總預估時間**: 6-8小時  
**建議執行時間**: 分2-3次完成，每次2-3小時

**Day 1** (2-3hrs):
- Phase 1: 清理廢棄檔案 (30min)
- Phase 2: 統一數據流架構 (2-2.5hrs)

**Day 2** (3-4hrs):  
- Phase 3: API服務整合 (3-4hrs)

**Day 3** (1hr):
- Phase 4: 測試驗證 (1hr)

## ✋ 注意事項

### ⚠️ 重要提醒

1. **執行前必須**:
   - 創建新的Git分支
   - 確認當前功能正常運作
   - 通知團隊成員避免同時修改相關文件

2. **執行過程中**:
   - 每個Phase完成後立即commit
   - 發現問題立即停止並分析
   - 保持詳細的修改記錄

3. **執行後必須**:
   - 完整測試所有衛星相關功能
   - 更新相關文檔
   - Code Review後再merge

### 🚫 禁止事項

- ❌ 不要同時執行多個Phase  
- ❌ 不要跳過測試步驟
- ❌ 不要在生產環境直接執行
- ❌ 不要忽略Console警告訊息

---

**維護者**: Claude Code  
**最後更新**: 2025-08-06  
**狀態**: 待執行
