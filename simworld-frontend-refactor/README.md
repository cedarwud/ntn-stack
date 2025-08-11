# SimWorld Frontend 重構計劃

## 🎯 重構目標
針對 **LEO Satellite Handover 研究** 的專項重構，優化核心研究工具，強化 UAV-衛星交互架構

## 🚨 重大發現與修正方針
**經深入驗證發現：大量標記為"保留"的組件實際上沒有在UI中顯示，屬於死代碼**
- 📊 **實際使用組件**: 僅~15個真正在UI中可見
- ❌ **虛假保留組件**: ~40個標記保留但不顯示  
- 🔍 **死代碼嚴重**: 過度設計導致維護負擔沉重

**重要文檔**:
- 📊 [`component-analysis.md`](./component-analysis.md) - 組件詳細分析  
- 🚨 [`dead-code-analysis-report.md`](./dead-code-analysis-report.md) - 死代碼分析報告
- 📋 [`unified-single-ue-plan.md`](./unified-single-ue-plan.md) - 單UE重構方針

## 🌟 專案核心技術焦點 (修正版)
- **LEO 衛星換手算法研究** ✅ (實際可用)
- **3D 衛星軌道可視化動畫** ✅ (DynamicSatelliteRenderer + Three.js實現)
- ~~**Sionna 無線通信仿真**~~ ❌ (空實現，後端404)
- ~~**高級時間軸控制**~~ ❌ (TimelineControl組件未被使用)

---

## 📋 重構階段總覽

### 📌 [Phase 1: 組件功能重評估](./phase1-remove-legacy/phase1-plan.md) 🔶 部分完成
**預計時間**: 1-2 天  
**優先級**: 🔴 高
- ✅ **保留單UE和多UE基本功能** (核心研究場景)
- ⚠️ **編隊群集協調邏輯** (UAVSwarmCoordination.tsx 仍存在)
- ⚠️ **Sionna空實現** (index.ts空文件仍存在，需清理)
- 🔄 需完成剩餘清理工作

### 📌 [Phase 2: 整合重複 API](./phase2-consolidate-apis/phase2-plan.md) ✅ 已完成  
**預計時間**: 2-3 天  
**優先級**: 🟡 中高
- ✅ **API 服務大幅減少** (25個→14個服務文件)
- ✅ **移除重複的NetStack服務** (保留 netstack-api.ts，移除其他重複)
- ✅ **移除重複的預計算服務** (移除3個重複版本)
- ✅ **提升代碼維護性** (消除重複代碼，無破壞性變更)

### 📌 [Phase 3: UI 組件優化](./phase3-cleanup-ui/phase3-plan.md) ✅ 已完成
**預計時間**: 3-4 天  
**優先級**: 🟡 中
- ✅ **保留核心衛星組件** (DynamicSatelliteRenderer, ConstellationSelectorCompact)
- ✅ **保留實際使用的換手組件** (HandoverStatusPanel)
- ✅ **移除 Sionna 空實現目錄** (已清理)
- ✅ **移除 UAV 編隊協調組件** (已清理)
- ✅ **API 服務大幅整合** (25個→14個，移除11個重複服務)
- ✅ **移除未使用組件** (ConstellationSelector等)

### 📌 [Phase 4: 性能與結構優化](./phase4-optimize-structure/phase4-plan.md)
**預計時間**: 2-3 天  
**優先級**: 🟢 中低
- ⚡ 3D 渲染性能優化
- 📦 代碼分割和懶載入
- 🧪 測試框架增強
- 📚 文檔結構化

---

## 🛰️ 實際可用功能清單 (經驗證)

### ✅ 真正顯示的核心組件 (15個)
- **主要UI場景** (`components/scenes/`)
  - StereogramView ✅ (主要界面路由)
  - FloorView ✅ (地面視圖路由)
- **衛星可視化** (`domains/satellite/`)
  - ConstellationSelectorCompact ✅ (在Sidebar顯示)  
  - DynamicSatelliteRenderer ✅ (3D衛星渲染)
- **設備管理** (`domains/device/`, `domains/coordinates/`)
  - 設備管理組件 ✅ (在Sidebar顯示)
  - 座標顯示組件 ✅

### ❌ 虛假保留組件 (更正：42個)
- **未使用的衛星組件**: SatelliteAnalysisPage, TimelineControl, SatelliteAnimationViewer
- **虛假的決策中心**: DecisionControlCenter, DecisionControlCenterSimple (API 404錯誤)
- **虛假的換手組件**: HandoverStatusPanel (enabled永遠為false), handover/visualization整個目錄
- **空實現的Sionna**: 整個sionna目錄只有空的index.ts
- **沒有後端支持**: AlgorithmExplainabilityPanel, WebSocket功能

### 🗑️ 大量移除建議 (65個組件)
- **完整的統一決策中心**: DecisionControlCenter, DecisionControlCenterSimple及相關子組件  
- **完整的換手功能**: HandoverStatusPanel, handover/visualization整個目錄
- **Sionna仿真目錄**: 空實現，無實際內容
- **時間軸和動畫控制**: TimelineControl, SatelliteAnimationViewer
- **預測性維護組件**: 設備維護分析
- **監控分析組件**: 實時監控相關
- **編隊群集協調**: UAV複雜編隊功能
- **WebSocket相關**: 沒有後端支持的實時功能
- **API虛假調用**: 調用404端點的服務

---

## 🚀 執行順序建議

### 🔥 立即執行 (風險低，收益高)
1. **Phase 1** - 移除明確無關的組件
2. **Phase 2** - 整合重複 API，提升維護性

### 📅 後續執行 (需要仔細測試)  
3. **Phase 3** - UI 組件重構 (影響用戶界面)
4. **Phase 4** - 性能優化 (需要基準測試)

---

## ⚠️ 重構風險與緩解

### 🛡️ 風險控制措施
- **完整備份** - 重構前創建完整項目備份
- **分支管理** - 每個 Phase 使用獨立分支
- **功能測試** - 每階段完成後進行完整功能測試
- **回退計劃** - 準備快速回退到穩定版本

### 🧪 測試檢查點
- [ ] 衛星軌道可視化正常
- [ ] 換手決策流程完整
- [ ] 3D 渲染性能穩定
- [ ] API 響應正常
- [ ] 設備管理功能正常

---

## 📈 預期收益

### 🎯 研究效率提升
- **代碼結構清晰** - 專注於 LEO Satellite Handover
- **維護成本降低** - 移除無關功能和重複代碼
- **性能改善** - 優化 3D 渲染和軌道計算

### 🔬 研究價值增強
- **核心功能專注** - 專注於實際可用的衛星換手研究工具
- **可視化效果提升** - 更直觀的衛星換手動畫
- **數據分析優化** - 專註於換手相關指標
- **代碼可維護性** - 移除死代碼後更容易維護和擴展

---

## 📞 重構支持

如有疑問或需要協助，請參考各階段詳細計劃文檔或聯繫開發團隊。

**⚡ 重構原則**: 功能完整性 > 代碼清潔度 > 性能優化
