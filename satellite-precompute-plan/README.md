# 真實衛星歷史數據預計算方案

## 🔄 **計劃狀態更新** 

**✅ 主要功能已整合至 sky.md Phase 0**  
本計劃中的核心座標特定軌道預計算功能已整合到主開發流程 `sky.md` 的 Phase 0 階段。

**📋 整合內容**：
- **CoordinateSpecificOrbitEngine** - 座標特定軌道預計算引擎
- **96分鐘軌道週期計算** - 完整軌道週期可見性分析  
- **衛星可見性篩選** - 5度仰角閾值過濾機制
- **Docker 建置時預計算** - 避免運行時計算延遲
- **前端展示優化** - 60倍加速、距離縮放的動畫數據

**🎯 當前狀態**：
- **Phase 0 重構**: 已將預計算引擎整合為主要開發目標
- **功能統合**: 避免重複開發，統一在 sky.md 管理
- **實施優先級**: 立即開始 Phase 0 座標軌道預計算引擎開發

## 📋 調整後的開發重點

**主要開發流程** → 請參考 `sky.md` Phase 0-4  
**輔助支援文檔** → 本目錄保留技術參數和架構參考

## 📚 檔案結構與開發順序

### 📚 支援文檔狀態 (已整合至 sky.md)

| 原階段 | 整合狀態 | 原檔案名稱 | 新整合位置 | 說明 |
|--------|----------|------------|-----------|------|
| **方案總覽** | ✅ 整合完成 | [`01-project-overview.md`](./01-project-overview.md) | `sky.md` Phase 0.4 | 技術參數已整合至座標軌道引擎設計 |
| **Phase 1** | ✅ 重新設計 | [`02-phase1-database-setup.md`](./02-phase1-database-setup.md) | `sky.md` Phase 0 → Phase 1 | 資料庫機制改為檔案預計算 + API 整合 |
| **Phase 2** | ✅ 核心整合 | [`03-phase2-precompute-engine.md`](./03-phase2-precompute-engine.md) | `sky.md` Phase 0.4 | CoordinateSpecificOrbitEngine 整合 |  
| **Phase 3** | ✅ API 重設計 | [`04-phase3-api-endpoints.md`](./04-phase3-api-endpoints.md) | `sky.md` Phase 1.1 | NetStack API 增強，支援預計算數據 |
| **Phase 4** | ✅ 前端整合 | [`05-phase4-frontend-timeline.md`](./05-phase4-frontend-timeline.md) | `sky.md` Phase 2 | 前端視覺化與展示增強 |
| **Phase 5** | ✅ 部署整合 | [`06-phase5-container-startup.md`](./06-phase5-container-startup.md) | `sky.md` Phase 4 | 部署優化與生產準備 |

### 📊 保留的技術參考文檔

| 分類 | 檔案名稱 | 狀態 | 說明 |
|------|----------|------|------|
| **技術參數** | [`01-project-overview.md`](./01-project-overview.md) | 📋 保留參考 | 衛星數量、時間參數、座標範圍等技術規格 |
| **驗收標準** | [`00-verification-standards.md`](./00-verification-standards.md) | 📋 保留參考 | 各階段驗證機制與完成確認標準 |
| **性能指標** | [`00-performance-metrics.md`](./00-performance-metrics.md) | 📋 保留參考 | 效能指標、資源使用預估、未來擴展規劃 |

---

## 🔄 **整合後的開發路徑**

### ✅ **已移轉至 sky.md 的功能**

1. **座標特定軌道預計算引擎** → `sky.md` Phase 0.4
   - CoordinateSpecificOrbitEngine 類別設計
   - 96分鐘軌道週期計算
   - 5度仰角閾值篩選
   - NTPU 座標優化

2. **Docker 建置整合** → `sky.md` Phase 0 驗收標準
   - precompute_coordinate_orbits.py 腳本
   - 建置時預計算流程
   - JSON 格式數據輸出

3. **API 端點設計** → `sky.md` Phase 1.1
   - /satellites/precomputed/{location}
   - /satellites/optimal-window/{location}  
   - /satellites/display-data/{location}

4. **前端整合** → `sky.md` Phase 2
   - PrecomputedOrbitService
   - SatelliteAnimationController
   - 60倍加速動畫優化

### 🎯 **立即執行項目**

**優先級 1**: 開始 `sky.md` Phase 0.4 開發
- 實現 CoordinateSpecificOrbitEngine
- 基於現有1天數據 (20250727) 驗證概念
- 完成 NTPU 座標的軌道預計算

**優先級 2**: 完善 Phase 0 其他功能
- Docker 建置時預計算整合
- 預計算數據檔案輸出格式
- 容器啟動性能優化

---

## 📋 **總結**

**✅ 成功整合**: 核心預計算功能已統一整合至 `sky.md` 主流程  
**🎯 發展方向**: 專注於 Phase 0 座標軌道預計算引擎的實現  
**📚 文檔角色**: 本目錄轉為技術參考和規格支援

**下一步**: 立即開始 `sky.md` Phase 0.4 的 CoordinateSpecificOrbitEngine 開發  
