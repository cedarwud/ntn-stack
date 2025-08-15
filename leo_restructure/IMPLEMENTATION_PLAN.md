# 🚀 LEO系統重構實施計劃

基於 @leo_restructure/ 新架構整合舊系統的分階段實施計劃。

## 📋 實施策略概覽

### 🎯 核心原則
- ✅ **功能優先**：保留所有驗證過的成功功能 (93.6%篩選率等)
- ✅ **架構升級**：採用新的模組化設計 (tle_loader/satellite_filter/signal_analyzer/pool_planner)
- ✅ **風險控制**：新舊並行，分階段驗證
- ✅ **徹底清理**：完成後完全移除舊代碼

### 📊 5階段實施計劃
```
Stage 1: TLE整合  →  Stage 2: Filter整合  →  Stage 3: Signal整合  →  Stage 4: Pool整合  →  Stage 5: 系統整合
TLE載入引擎        衛星篩選引擎        信號分析引擎        動態池規劃        端到端測試
1-2天             2-3天              1-2天             2-3天            1-2天
```

---

## 🔧 Stage 1: TLE_Loader 整合 (1-2天)

### 🎯 目標
- 整合所有TLE載入相關功能到統一引擎
- 確保8,736顆衛星正確載入
- 建立SGP4軌道計算的標準介面

### 📁 新檔案結構
```
leo_restructure/phase1_core_system/tle_loader/
├── tle_data_engine.py          # ← stage1_tle_processor.py + tle_loader.py
├── orbital_calculator.py       # ← coordinate_specific_orbit_engine.py + sgp4_engine.py  
├── data_validator.py          # ← 新增：TLE數據驗證
└── fallback_data_provider.py  # ← local_tle_loader.py + 備援機制
```

### 🔄 整合動作
1. **保留核心邏輯**: `stage1_tle_processor.py` 的成功載入流程
2. **整合SGP4引擎**: 統一軌道計算介面
3. **加強驗證**: 新增TLE數據完整性檢查
4. **建立備援**: 整合本地載入和網路下載

### ✅ 驗證標準
- [ ] 成功載入8,736顆衛星 (8,085 Starlink + 651 OneWeb)
- [ ] SGP4軌道計算精度 < 1km
- [ ] 處理時間 ≤ 5分鐘
- [ ] 記憶體使用 < 2GB

---

## 🔧 Stage 2: Satellite_Filter 整合 (2-3天) 🚨 關鍵

### 🎯 目標  
- **修復0%可見性合規問題** (最高優先級)
- 整合93.6%篩選率的成功邏輯
- 簡化複雜的多階段篩選系統

### 📁 新檔案結構
```
leo_restructure/phase1_core_system/satellite_filter/
├── intelligent_filter_engine.py    # ← unified_intelligent_filter.py (核心邏輯)
├── geographic_optimizer.py        # ← geographic_filter.py
├── constellation_balancer.py      # ← constellation_separator.py  
└── candidate_selector.py          # ← satellite_selector.py
```

### 🔄 整合動作
1. **保留成功邏輯**: `unified_intelligent_filter.py` 的93.6%篩選演算法
2. **修復可見性問題**: 調整地理篩選參數
3. **簡化架構**: 移除過度複雜的6階段篩選
4. **統一介面**: 建立標準的篩選配置系統

### ✅ 驗證標準
- [ ] 篩選率 ≥ 93.6% (8,736 → ≥563顆)
- [ ] 可見性合規 > 0% (修復當前問題)
- [ ] 星座平衡: Starlink ~450顆, OneWeb ~113顆
- [ ] 處理時間 ≤ 3分鐘

---

## 🔧 Stage 3: Signal_Analyzer 整合 (1-2天)

### 🎯 目標
- 整合3GPP標準的信號分析功能
- 改善A4/A5/D2事件檢測準確性
- 統一RSRP/RSRQ計算引擎

### 📁 新檔案結構  
```
leo_restructure/phase1_core_system/signal_analyzer/
├── signal_quality_engine.py       # ← stage3_signal_processor.py
├── threegpp_event_detector.py     # ← gpp_event_analyzer.py + threegpp_event_generator.py
├── rsrp_calculation_engine.py     # ← rsrp_calculator.py
└── handover_event_processor.py    # ← handover_scorer.py
```

### 🔄 整合動作
1. **保留3GPP標準**: `stage3_signal_processor.py` 的標準實現
2. **整合事件檢測**: 統一A4/A5/D2事件處理
3. **優化RSRP計算**: 統一信號強度計算引擎
4. **改善換手邏輯**: 整合換手評分系統

### ✅ 驗證標準
- [ ] A4/A5/D2事件檢測正常運作
- [ ] RSRP計算精度符合3GPP標準
- [ ] 換手事件數量 > 100個
- [ ] 處理時間 ≤ 5分鐘

---

## 🔧 Stage 4: Pool_Planner 整合 (2-3天)

### 🎯 目標
- 整合動態池規劃與模擬退火演算法
- 達成10-15/3-6顆動態覆蓋目標
- 實現時空分散的衛星選擇

### 📁 新檔案結構
```  
leo_restructure/phase1_core_system/pool_planner/
├── pool_optimization_engine.py    # ← stage6_dynamic_pool_planner.py + 新SA演算法
├── simulated_annealing_core.py    # ← 新的SA演算法實現
├── temporal_distributor.py        # ← phase_distribution.py
└── coverage_validator.py          # ← orbital_grouping.py + 覆蓋驗證
```

### 🔄 整合動作
1. **保留動態池邏輯**: `stage6_dynamic_pool_planner.py` 的規劃演算法
2. **加入模擬退火**: 實現新的SA優化演算法
3. **整合時空分散**: `phase_distribution.py` 的相位分散
4. **強化覆蓋驗證**: 確保動態覆蓋需求達成

### ✅ 驗證標準
- [ ] Starlink: 10-15顆同時可見 (5°仰角)
- [ ] OneWeb: 3-6顆同時可見 (10°仰角)
- [ ] 時空分散: 相位差 > 15°
- [ ] 覆蓋率 > 95%

---

## 🔧 Stage 5: 系統整合測試 (1-2天)

### 🎯 目標
- 端到端功能驗證
- 性能基準達成
- 前端兼容性確認

### 🧪 測試項目
```
leo_restructure/tests_integration/
├── phase1_complete_test.py         # 完整流程測試
├── performance_benchmark_test.py   # 性能對比測試
├── frontend_compatibility_test.py  # 前端格式測試
└── legacy_cleanup_verification.py # 舊系統清理驗證
```

### ✅ 最終驗證標準
- [ ] **功能驗證**: 所有模組獨立測試通過
- [ ] **性能驗證**: 總處理時間 ≤ 20分鐘  
- [ ] **品質驗證**: 篩選率 ≥ 93.6%，可見性合規 > 50%
- [ ] **覆蓋驗證**: 10-15/3-6顆動態覆蓋達成
- [ ] **兼容驗證**: JSON格式前端兼容

---

## 🗑️ 舊系統清理階段

### 📋 清理順序
1. **階段性清理**: 每完成一個模組，清理對應舊檔案
2. **JSON檔案清理**: 前端測試通過後清理數據檔案
3. **目錄清理**: 最後清理空目錄和配置檔案
4. **最終驗證**: 系統重啟測試

### 🛡️ 安全措施
- 清理前建立完整備份
- 保留重要配置檔案
- 分批清理，逐步驗證
- 建立回退機制

---

## 📊 實施時程表

| 階段 | 工作內容 | 預估時間 | 關鍵里程碑 |
|-----|---------|---------|-----------|
| **Stage 1** | TLE_Loader 整合 | 1-2天 | 8,736顆衛星載入成功 |
| **Stage 2** | Satellite_Filter 整合 | 2-3天 | 可見性合規>0%，篩選率≥93.6% |  
| **Stage 3** | Signal_Analyzer 整合 | 1-2天 | A4/A5/D2事件檢測正常 |
| **Stage 4** | Pool_Planner 整合 | 2-3天 | 10-15/3-6顆動態覆蓋達成 |
| **Stage 5** | 系統整合測試 | 1-2天 | 端到端測試通過 |
| **清理** | 舊系統清理 | 1天 | 47個檔案完全清理 |

### 🎯 總計：8-12天完成

---

## 🚨 風險控制機制

### ⚠️ 主要風險點
1. **Satellite_Filter風險**: 可見性合規0%問題復發
2. **性能風險**: 新系統性能低於舊系統  
3. **兼容性風險**: 前端JSON格式不兼容
4. **清理風險**: 誤刪重要檔案

### 🛡️ 風險緩解措施
- **並行開發**: 新舊系統同時運行
- **分階段驗證**: 每階段完成立即測試
- **性能基準**: 建立量化的成功標準
- **備份機制**: 重要檔案保留備份
- **回退計劃**: 每階段都有回退方案

---

## 🏁 成功標準總覽

### ✅ 功能成功標準
- TLE_Loader: 8,736顆衛星載入 ✅
- Satellite_Filter: 篩選率≥93.6%，可見性合規>0% ✅
- Signal_Analyzer: A4/A5/D2事件檢測正常 ✅  
- Pool_Planner: 10-15/3-6顆動態覆蓋 ✅

### ⚡ 性能成功標準
- 總處理時間 ≤ 20分鐘 ✅
- 記憶體使用 < 4GB ✅
- 篩選準確率 ≥ 93.6% ✅
- 系統響應時間 < 100ms ✅

### 🧹 清理成功標準
- 47個舊檔案完全移除 ✅
- 所有stage相關JSON清理 ✅
- 系統重啟功能正常 ✅
- 新架構完全運行 ✅

---

**📋 實施建議**：建議從TLE_Loader開始，因為它是整個系統的數據基礎，風險最低且最容易驗證成功。每完成一個Stage立即更新 `INTEGRATION_TRACKING.md` 追蹤狀態。

*計劃制定日期：2025-08-15*