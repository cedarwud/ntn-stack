# 🗂️ 舊系統整合追蹤管理

本文檔追蹤所有舊系統檔案的整合狀態，確保重構完成後能完全清理舊代碼。

## 📋 整合追蹤總覽

### 📊 整合進度統計
- **待整合**: 64個檔案 (47個程式檔案 + 17個文檔檔案)
- **整合中**: 0個檔案  
- **已整合**: 0個檔案
- **可刪除**: 0個檔案
- **完成率**: 0.0%

---

## 🎯 核心檔案整合狀態

### TLE_Loader 整合追蹤
| 舊檔案路徑 | 新架構位置 | 狀態 | 整合日期 | 備註 |
|-----------|-----------|------|----------|------|
| `netstack/src/stages/stage1_tle_processor.py` | `tle_loader/tle_data_engine.py` | ⏳ 待整合 | - | 主要邏輯，優先整合 |
| `netstack/src/services/satellite/coordinate_specific_orbit_engine.py` | `tle_loader/orbital_calculator.py` | ⏳ 待整合 | - | SGP4計算引擎 |
| `netstack/src/services/satellite/tle_loader.py` | `tle_loader/tle_data_engine.py` | ⏳ 待整合 | - | 基礎載入邏輯 |
| `netstack/src/services/satellite/local_tle_loader.py` | `tle_loader/fallback_data_provider.py` | ⏳ 待整合 | - | 本地載入功能 |
| `netstack/src/services/satellite/sgp4_engine.py` | `tle_loader/orbital_calculator.py` | ⏳ 待整合 | - | 備用SGP4引擎 |

### Satellite_Filter 整合追蹤  
| 舊檔案路徑 | 新架構位置 | 狀態 | 整合日期 | 備註 |
|-----------|-----------|------|----------|------|
| `netstack/src/stages/stage2_filter_processor.py` | `satellite_filter/intelligent_filter_engine.py` | ⏳ 待整合 | - | 主要處理邏輯 |
| `netstack/src/services/satellite/intelligent_filtering/unified_intelligent_filter.py` | `satellite_filter/intelligent_filter_engine.py` | 🔥 優先整合 | - | **核心**：93.6%篩選率 |
| `netstack/src/services/satellite/preprocessing/satellite_selector.py` | `satellite_filter/candidate_selector.py` | ⏳ 待整合 | - | 候選選擇邏輯 |
| `netstack/src/services/satellite/intelligent_satellite_filtering.py` | `satellite_filter/intelligent_filter_engine.py` | ⏳ 待整合 | - | 智能篩選系統 |
| `netstack/src/services/satellite/intelligent_filtering/geographic_filtering/geographic_filter.py` | `satellite_filter/geographic_optimizer.py` | ⏳ 待整合 | - | 地理篩選邏輯 |
| `netstack/src/services/satellite/intelligent_filtering/constellation_separation/constellation_separator.py` | `satellite_filter/constellation_balancer.py` | ⏳ 待整合 | - | 星座分離邏輯 |

### Signal_Analyzer 整合追蹤
| 舊檔案路徑 | 新架構位置 | 狀態 | 整合日期 | 備註 |
|-----------|-----------|------|----------|------|
| `netstack/src/stages/stage3_signal_processor.py` | `signal_analyzer/signal_quality_engine.py` | ⏳ 待整合 | - | 主要信號處理 |
| `netstack/src/services/satellite/intelligent_filtering/event_analysis/gpp_event_analyzer.py` | `signal_analyzer/threegpp_event_detector.py` | ⏳ 待整合 | - | 3GPP事件分析 |
| `netstack/src/services/satellite/intelligent_filtering/signal_calculation/rsrp_calculator.py` | `signal_analyzer/rsrp_calculation_engine.py` | ⏳ 待整合 | - | RSRP計算引擎 |
| `netstack/src/services/satellite/intelligent_filtering/handover_scoring/handover_scorer.py` | `signal_analyzer/handover_event_processor.py` | ⏳ 待整合 | - | 換手評分邏輯 |
| `netstack/src/services/threegpp_event_generator.py` | `signal_analyzer/threegpp_event_detector.py` | ⏳ 待整合 | - | 3GPP事件生成 |

### Pool_Planner 整合追蹤
| 舊檔案路徑 | 新架構位置 | 狀態 | 整合日期 | 備註 |
|-----------|-----------|------|----------|------|
| `netstack/src/stages/stage6_dynamic_pool_planner.py` | `pool_planner/pool_optimization_engine.py` | ⏳ 待整合 | - | 動態池規劃主邏輯 |
| `netstack/src/services/satellite/preprocessing/phase_distribution.py` | `pool_planner/temporal_distributor.py` | ⏳ 待整合 | - | 相位分散演算法 |
| `netstack/src/services/satellite/preprocessing/orbital_grouping.py` | `pool_planner/coverage_validator.py` | ⏳ 待整合 | - | 軌道分組邏輯 |

---

## 🗑️ 待清理的Stage檔案

### 主要Stage處理器 (優先清理)
- [ ] `netstack/src/stages/stage1_tle_processor.py` 
- [ ] `netstack/src/stages/stage1_tle_processor_backup.py`
- [ ] `netstack/src/stages/stage2_filter_processor.py`
- [ ] `netstack/src/stages/stage3_signal_processor.py` 
- [ ] `netstack/src/stages/stage4_timeseries_processor.py`
- [ ] `netstack/src/stages/stage5_integration_processor.py`
- [ ] `netstack/src/stages/stage6_dynamic_pool_planner.py`

### 分散的服務檔案 (次要清理)
- [ ] `netstack/src/services/satellite/` 下的40+個檔案
- [ ] `netstack/src/services/satellite/intelligent_filtering/` 整個目錄
- [ ] `netstack/src/services/satellite/preprocessing/` 整個目錄  

### 根目錄的舊Pipeline檔案
- [ ] `run_stage6_independent.py`
- [ ] `verify_complete_pipeline.py`
- [ ] `fix_stage2_filtering.py`
- [ ] `complete_pipeline.py`
- [ ] `test_stage4_pipeline.py`
- [ ] `run_full_6_stage_pipeline.py`
- [ ] `core_fix_stage2.py`
- [ ] `quick_fix_stage2.py` 
- [ ] `full_pipeline_execution.py`

---

## 📄 JSON資料檔案追蹤

### Stage輸出JSON檔案 (需要清理)
- [ ] `/app/data/stage1_tle_sgp4_output.json`
- [ ] `/app/data/stage2_intelligent_filtered_output.json`
- [ ] `/app/data/stage3_signal_analysis_output.json`
- [ ] `/app/data/stage4_timeseries_output.json`
- [ ] `/app/data/stage5_integration_output.json`
- [ ] `/app/data/stage6_dynamic_pools_output.json`

### 臨時輸出JSON檔案 (需要清理)
- [ ] `/tmp/phase1_outputs/stage1_tle_loading_results.json`
- [ ] `/tmp/phase1_outputs/stage2_filtering_results.json`
- [ ] `/tmp/phase1_outputs/stage3_event_analysis_results.json`
- [ ] `/tmp/phase1_outputs/stage4_optimization_results.json`
- [ ] `/tmp/phase1_outputs/phase1_final_report.json`

### 舊版數據檔案 (需要清理)
- [ ] `/app/data/enhanced_timeseries/`
- [ ] `/app/data/layered_phase0_enhanced/`
- [ ] `/app/data/handover_scenarios/`
- [ ] `/app/data/signal_quality_analysis/`
- [ ] `/app/data/processing_cache/`
- [ ] `/app/data/status_files/`

### 前端舊數據檔案 (需要清理)
- [ ] `/simworld/backend/data/starlink_120min_d2_enhanced.json`
- [ ] `/simworld/backend/data/oneweb_120min_d2_enhanced.json`
- [ ] `/simworld/backend/data/starlink_120min_timeseries.json`
- [ ] `/simworld/backend/data/oneweb_120min_timeseries.json`

### 舊文檔系統 (全部清理) 🆕
- [ ] `/docs/README.md` - 舊文檔中心
- [ ] `/docs/data-flow-index.md` - 舊數據流程導航
- [ ] `/docs/overviews/data-processing-flow.md` - 舊6階段概述
- [ ] `/docs/stages/README.md` - 舊階段文檔導航
- [ ] `/docs/stages/stage1-tle-loading.md` - 舊階段1文檔
- [ ] `/docs/stages/stage2-filtering.md` - 舊階段2文檔
- [ ] `/docs/stages/stage3-signal.md` - 舊階段3文檔
- [ ] `/docs/stages/stage4-timeseries.md` - 舊階段4文檔
- [ ] `/docs/stages/stage5-integration.md` - 舊階段5文檔
- [ ] `/docs/stages/stage6-dynamic-pool.md` - 舊階段6文檔
- [ ] `/docs/overviews/` - 整個舊概述目錄
- [ ] `/docs/stages/` - 整個舊階段目錄
- [ ] `/docs/algorithms_implementation.md` - 舊演算法文檔
- [ ] `/docs/api_reference.md` - 舊API參考
- [ ] `/docs/satellite_constellation_analysis.md` - 舊衛星分析
- [ ] `/docs/satellite_data_preprocessing.md` - 舊數據預處理
- [ ] `/docs/satellite_handover_standards.md` - 舊換手標準 ⭐ **保留或移植**
- [ ] `/docs/standards_implementation.md` - 舊標準實現
- [ ] `/docs/system_architecture.md` - 舊系統架構
- [ ] `/docs/technical_guide.md` - 舊技術指南

---

## ✅ 清理驗證檢查清單

### Phase 1 整合完成後檢查
- [ ] 所有TLE_Loader檔案功能正常，舊TLE載入檔案可刪除
- [ ] 所有Satellite_Filter檔案功能正常，舊篩選檔案可刪除
- [ ] 所有Signal_Analyzer檔案功能正常，舊信號分析檔案可刪除
- [ ] 所有Pool_Planner檔案功能正常，舊動態池檔案可刪除

### 完整清理前最終檢查
- [ ] 新系統端到端測試通過
- [ ] 性能達到或超越舊系統基準
- [ ] 前端整合測試通過
- [ ] 所有JSON格式兼容性確認
- [ ] 備份重要的舊系統配置檔案

### 清理完成驗證
- [ ] `netstack/src/stages/` 目錄完全清空
- [ ] `netstack/src/services/satellite/` 只保留必要檔案  
- [ ] 根目錄的stage相關檔案全部刪除
- [ ] 所有stage相關JSON檔案清理完成
- [ ] `/docs/` 舊文檔系統完全清理 🆕
- [ ] `/docs/overviews/` 和 `/docs/stages/` 目錄刪除 🆕
- [ ] 系統重啟後功能正常

---

## 📝 整合日誌

### 2025-08-15 
- 📋 建立追蹤文檔
- 🔍 完成舊系統檔案分析
- 📊 統計待整合檔案：47個程式檔案
- 🔄 調整命名策略：F1→tle_loader, F2→satellite_filter, F3→signal_analyzer, A1→pool_planner
- 📚 新增舊文檔系統清理清單：17個文檔檔案
- 📊 更新總計：64個檔案待清理

### [待更新]
- [ ] F1 整合開始
- [ ] F2 整合開始  
- [ ] F3 整合開始
- [ ] A1 整合開始
- [ ] 清理階段開始

---

**📌 重要提醒**：
1. 每完成一個模組整合，立即更新此文檔
2. 刪除任何檔案前，必須先更新狀態為「✅ 已整合」  
3. 保持新舊系統並行運行，直到完全驗證通過
4. 所有JSON檔案清理必須在前端測試通過後進行

*最後更新：2025-08-15*