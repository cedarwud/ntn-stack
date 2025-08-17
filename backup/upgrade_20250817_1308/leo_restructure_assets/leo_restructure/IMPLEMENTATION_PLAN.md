# 🚀 LEO系統重構實施計劃

基於 @leo_restructure/ 新架構整合舊系統的分階段實施計劃。

## 📋 實施策略概覽

### 🎯 核心原則
- ✅ **功能優先**：保留所有驗證過的成功功能 (93.6%篩選率等)
- ✅ **架構升級**：採用新的模組化設計 (tle_loader/satellite_filter/signal_analyzer/pool_planner)
- ✅ **風險控制**：新舊並行，分階段驗證
- ✅ **徹底清理**：完成後完全移除舊代碼

### 📊 6階段實施計劃 (Phase 0 + 5 Stages)
```
Phase 0: 替換整合  →  Stage 1: TLE整合  →  Stage 2: Filter整合  →  Stage 3: Signal整合  →  Stage 4: Pool整合  →  Stage 5: 系統整合
系統切換與清理      TLE載入引擎        衛星篩選引擎        信號分析引擎        動態池規劃        端到端測試
5-7天 🔥最高優先   1-2天             2-3天              1-2天             2-3天            1-2天
```

### 🚀 NEW! 高效開發工作流程 🆕

**基於用戶反饋新增**: 為避免重複建構映像檔，實施4階段漸進式開發策略

#### 🛠️ 開發效率工具 (已實施)
- ✅ **開發別名系統**: `leo-dev`, `leo-test`, `leo-full`, `leo-build`
- ✅ **自動清理管理器**: 智能清理舊數據，跳過 `/netstack/tle_data/` 資料夾
- ✅ **增量更新系統**: 檢測變更，智能選擇更新策略
- ✅ **智能Cron調度**: 維持 TLE 每 6 小時 4 次下載

#### ⚡ 4階段開發流程
```bash
Stage D1: leo-dev   (30秒)   → 超快速開發，日常邏輯驗證
Stage D2: leo-test  (3分鐘)  → 開發驗證，功能完整性測試
Stage D3: leo-full  (10分鐘) → 全量測試，最終確認
Stage D4: leo-build (25分鐘) → 容器建構，生產部署驗證
```

#### 📈 效率提升成果
- **日常開發**: 30分鐘 → 30秒 (**60倍提升**)
- **功能測試**: 30分鐘 → 3分鐘 (**10倍提升**)  
- **完整驗證**: 30分鐘 → 10分鐘 (**3倍提升**)

**實施檔案**:
- `run_phase1.py` (增強版支援D1-D4)
- `shared_core/auto_cleanup_manager.py`
- `shared_core/incremental_update_manager.py`
- `setup_dev_aliases.sh`
- `intelligent_cron_update.sh`

---

## 🔥 Phase 0: 系統替換整合 (5-7天) **最高優先級**

### 🎯 目標
- **完全替代**: 將 leo_restructure 作為唯一的衛星數據處理系統
- **架構保持**: 保持 Pure Cron 驅動架構的核心優勢 (< 30秒啟動)
- **無縫切換**: 前端和API完全兼容，零停機時間切換
- **舊代碼清理**: 按照 `INTEGRATION_TRACKING.md` 清理64個舊文件

### 📋 Phase 0 詳細實施步驟

#### P0.1: Docker建構整合 (1-2天)
```bash
# 目標: 將 leo_restructure 整合到 Docker 建構流程

# 1. 修改建構腳本
netstack/docker/build_with_phase0_data.py:
  - 移除原6階段調用
  - 添加 leo_restructure/run_phase1.py 調用
  - 保持輸出到 /app/data/ 的Volume架構

# 2. 配置Pure Cron驅動
  - 確保建構階段完成數據預計算
  - 容器啟動時純數據載入 (< 30秒)
  - Cron調度增量更新機制對接

# 3. 輸出路徑統一
  - leo_restructure 輸出: /tmp/phase1_outputs/ → /app/data/
  - 格式兼容: JSON 結構與前端期望一致
```

#### P0.2: 配置系統統一 (1天)
```bash
# 目標: 統一配置管理，避免配置衝突

# 1. 配置文件整合
cp leo_restructure/shared_core/config_manager.py netstack/config/leo_config.py

# 2. 仰角門檻統一
  - 使用現有的 satellite_handover_standards.md 標準
  - 分層仰角門檻: 5°/10°/15° 
  - 環境調整係數對接

# 3. 環境變數對接
  - NTPU座標: 24.9441°N, 121.3714°E
  - 星座配置: Starlink 5°, OneWeb 10°
  - 計算參數: 時間範圍200分鐘, 30秒間隔
```

#### P0.3: 輸出格式對接 (1天)
```bash
# 目標: 確保前端立體圖和API完全兼容

# 1. JSON格式統一
leo_restructure/phase1_core_system/a1_dynamic_pool_planner/output_formatter.py:
  - 生成前端需要的動畫數據格式
  - 時間序列: 200個時間點, 30秒間隔
  - 衛星位置: elevation, azimuth, distance

# 2. API接口兼容
  - /api/v1/satellites/positions 數據源切換
  - /api/v1/satellites/constellations/info 更新
  - 響應時間保持 < 100ms

# 3. 立體圖數據格式
  - 3D座標轉換
  - 動畫時間軸數據
  - 換手事件標記
```

#### P0.4: 系統替換與驗證 (2-3天) 🔥 **關鍵階段**
```bash
# 目標: 完全切換到新系統，全面驗證功能

# Day 1: 系統切換
# 1. 備份舊系統
mkdir -p netstack/src/stages_backup/
mv netstack/src/stages/ netstack/src/stages_backup/

# 2. 部署新系統
cp -r leo_restructure/ netstack/src/leo_core/

# 3. 更新Makefile
# 修改 netstack-build 調用新系統

# Day 2-3: 全面驗證
# 1. 建構測試
make down-v && make build-n && make up

# 2. API測試
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/satellites/positions

# 3. 前端測試
# 檢查立體圖動畫正常運行

# 4. 性能驗證
# 啟動時間 < 30秒
# API響應 < 100ms
# 記憶體使用 < 2GB
```

### ✅ Phase 0 驗證標準

#### 🎯 系統替換驗證
- [ ] **完全切換**: 0% 使用舊6階段系統，100% 使用 leo_restructure
- [ ] **建構成功**: `make build-n` 使用新系統成功完成
- [ ] **啟動成功**: `make up` 後所有服務健康 (< 30秒)
- [ ] **API兼容**: 所有現有API端點正常響應

#### ⚡ 性能基準驗證
- [ ] **啟動時間**: < 30秒 (Pure Cron 驅動核心要求)
- [ ] **API響應**: < 100ms (衛星位置查詢)
- [ ] **記憶體使用**: < 2GB (建構階段)
- [ ] **存儲需求**: ~450-500MB (Volume + PostgreSQL)

#### 🎮 前端兼容驗證
- [ ] **立體圖渲染**: 衛星動畫正常顯示
- [ ] **時間軸控制**: 播放/暫停/倍速功能正常
- [ ] **換手事件**: A4/A5/D2事件正確標記
- [ ] **數據更新**: Cron自動更新機制正常

#### 🧹 舊代碼清理驗證
- [ ] **Stage檔案**: 7個主要stage處理器已備份/清理
- [ ] **服務檔案**: 40+個分散服務檔案已清理
- [ ] **JSON檔案**: 舊的階段輸出JSON已清理
- [ ] **系統測試**: 清理後系統重啟功能正常

### 🚨 Phase 0 風險控制

#### ⚠️ 主要風險
1. **建構失敗**: leo_restructure 與 Docker 建構不兼容
2. **性能倒退**: 新系統啟動時間 > 30秒
3. **前端破壞**: 立體圖數據格式不兼容
4. **API破壞**: 現有API端點響應異常

#### 🛡️ 風險緩解
- **完整備份**: 所有舊代碼備份到 `stages_backup/`
- **分步驗證**: 每個子階段獨立測試
- **快速回退**: 15分鐘內可回退到舊系統
- **並行測試**: 新舊系統並行運行驗證

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
| **🔥 Phase 0** | **系統替換整合** | **5-7天** | **完全替代6階段系統** ⭐ |
| **Stage 1** | TLE_Loader 整合 | 1-2天 | 8,736顆衛星載入成功 |
| **Stage 2** | Satellite_Filter 整合 | 2-3天 | 可見性合規>0%，篩選率≥93.6% |  
| **Stage 3** | Signal_Analyzer 整合 | 1-2天 | A4/A5/D2事件檢測正常 |
| **Stage 4** | Pool_Planner 整合 | 2-3天 | 10-15/3-6顆動態覆蓋達成 |
| **Stage 5** | 系統整合測試 | 1-2天 | 端到端測試通過 |
| **清理** | 舊系統清理 | 1天 | 64個檔案完全清理 |

### 🎯 總計：13-19天完成 (Phase 0: 5-7天 + Stages 1-5: 8-12天)

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