# 🎯 功能性命名策略 - 徹底解決 Phase/Stage 混淆問題

## 🚨 問題根源分析

### 當前問題
- `phase0`, `phase1`, `phase2` 等抽象編號造成混淆
- 隨著系統演進，編號意義變化
- 新開發者難以理解各個 "phase" 的實際功能
- 維護時容易搞錯功能對應關係

### 根本解決方案
**完全廢棄 phase/stage 編號，採用功能性命名**

## 🔄 全新功能性命名方案

### 原始 Phase 概念 → 功能性命名映射

| 原始概念 | 實際功能 | **新的功能性命名** |
|----------|----------|-------------------|
| ~~Phase 0~~ | 數據下載與預處理 | `tle_data_preprocessing` |
| ~~Phase 1~~ | TLE載入與SGP4軌道計算 | `orbit_calculation` |
| ~~Phase 2~~ | 智能衛星篩選 | `satellite_selection` |
| ~~Phase 3~~ | 3GPP事件與信號計算 | `signal_analysis` |
| ~~Phase 4~~ | 時間序列生成 | `timeseries_generation` |
| ~~Phase 5~~ | 數據整合與API | `data_integration` |

## 📂 新的文件組織結構

### 核心處理器重命名
```bash
# 舊的混淆命名
build_with_phase0_data_refactored.py  ❌
build_with_phase1_data.py             ❌

# 新的功能性命名  
satellite_orbit_preprocessor.py       ✅
tle_data_processor.py                 ✅
sgp4_orbit_calculator.py              ✅
```

### 服務模組重命名
```bash
# 舊的混淆命名
phase0_integration.py                 ❌
phase1_coordinator.py                 ❌

# 新的功能性命名
starlink_data_downloader.py           ✅
orbit_calculation_service.py          ✅  
satellite_selection_engine.py         ✅
signal_analysis_processor.py          ✅
```

### 數據文件重命名
```bash
# 舊的混淆命名
phase0_precomputed_orbits.json        ❌
phase1_data_summary.json              ❌

# 新的功能性命名
precomputed_satellite_orbits.json     ✅
orbit_calculation_summary.json        ✅
satellite_selection_results.json      ✅
signal_analysis_data.json             ✅
```

## 🏗️ 新的系統架構命名

### 處理流程重新定義
```
🛰️ LEO 衛星數據處理系統
├── TLE Data Preprocessing (TLE數據預處理)
│   ├── tle_data_downloader.py
│   ├── tle_format_validator.py
│   └── satellite_catalog_builder.py
│
├── Orbit Calculation (軌道計算)
│   ├── sgp4_orbit_calculator.py
│   ├── coordinate_transformer.py
│   └── trajectory_generator.py
│
├── Satellite Selection (衛星篩選)
│   ├── geographic_filter.py
│   ├── elevation_threshold_engine.py
│   └── constellation_optimizer.py
│
├── Signal Analysis (信號分析)
│   ├── rsrp_calculator.py
│   ├── handover_event_detector.py
│   └── signal_quality_analyzer.py
│
├── Timeseries Generation (時間序列生成)
│   ├── animation_data_generator.py
│   ├── trajectory_interpolator.py
│   └── temporal_synchronizer.py
│
└── Data Integration (數據整合)
    ├── api_data_provider.py
    ├── frontend_data_formatter.py
    └── research_data_exporter.py
```

### API 端點重命名
```python
# 舊的混淆命名
/api/v1/phase0/satellites          ❌
/api/v1/phase1/orbits              ❌

# 新的功能性命名
/api/v1/satellites/catalog         ✅
/api/v1/orbits/calculated          ✅
/api/v1/satellites/selected        ✅
/api/v1/signals/analysis           ✅
/api/v1/timeseries/animation       ✅
```

## 🔧 配置系統重新設計

### 配置文件重命名
```yaml
# 舊的混淆命名
phase0_config.yaml                 ❌
phase1_settings.json               ❌

# 新的功能性命名
orbit_calculation_config.yaml      ✅
satellite_selection_config.yaml    ✅
signal_analysis_config.yaml        ✅
```

### 環境變數重命名
```bash
# 舊的混淆命名
PHASE0_DATA_DIR                    ❌
PHASE1_OUTPUT_PATH                 ❌

# 新的功能性命名
TLE_DATA_DIRECTORY                 ✅
ORBIT_CALCULATION_OUTPUT           ✅
SATELLITE_SELECTION_CACHE          ✅
SIGNAL_ANALYSIS_RESULTS            ✅
```

## 📊 類和函數重命名

### Python 類重命名
```python
# 舊的混淆命名
class Phase0Integration            ❌
class Phase1Coordinator            ❌
class Phase25DataPreprocessor      ❌

# 新的功能性命名
class StarlinkDataDownloader       ✅
class OrbitCalculationEngine       ✅
class SatelliteSelectionOptimizer  ✅
class SignalAnalysisProcessor      ✅
```

### 函數重命名
```python
# 舊的混淆命名
get_phase0_satellite_data()        ❌
execute_phase1_orbit_calculation() ❌

# 新的功能性命名
get_satellite_catalog()            ✅
calculate_satellite_orbits()       ✅
select_optimal_satellites()        ✅
analyze_signal_quality()           ✅
```

## 🗂️ 新的資料夾結構

### 專案根目錄重組
```
ntn-stack/
├── tle_data_preprocessing/         # 取代 phase0 相關
│   ├── downloader/
│   ├── validator/
│   └── catalog/
│
├── orbit_calculation/              # 取代 phase1 相關
│   ├── sgp4_engine/
│   ├── coordinate_system/
│   └── trajectory/
│
├── satellite_selection/            # 取代 phase2 相關
│   ├── geographic_filter/
│   ├── elevation_engine/
│   └── optimization/
│
├── signal_analysis/                # 取代 phase3 相關
│   ├── rsrp_calculation/
│   ├── handover_detection/
│   └── quality_metrics/
│
└── system_integration/             # 取代 phase4-5 相關
    ├── api_services/
    ├── data_export/
    └── frontend_interface/
```

## 🎯 實施策略

### 階段性重構計劃

#### 階段 1: 核心文件重命名
```bash
# 主要處理器
mv build_with_phase0_data_refactored.py → satellite_orbit_preprocessor.py
mv phase0_integration.py → starlink_data_downloader.py
```

#### 階段 2: API 和服務重構
- 更新所有 API 端點使用功能性路徑
- 重命名服務類和方法
- 更新配置系統

#### 階段 3: 文檔和註釋更新
- 更新所有技術文檔
- 重寫註釋使用功能性描述
- 更新 README 和說明文件

## ✅ 長期效益

### 1. **語意清晰**
- 文件名直接反映功能，無需解釋
- 新開發者快速理解系統結構
- 維護時不會搞錯功能對應關係

### 2. **擴展友善**
- 新增功能時按功能分類，不用編號
- 系統架構演進不會影響現有命名
- 模組化設計便於獨立開發

### 3. **維護便利**
- 問題定位更快速精確
- 代碼審查更直觀
- 重構風險降低

## 🚨 重要原則

### 命名原則
1. **功能優先**: 名稱必須直接反映實際功能
2. **避免編號**: 不使用 phase/stage/step 等序號
3. **領域專用**: 使用衛星通訊領域的專業術語
4. **一致性**: 整個系統使用統一的命名風格

### 禁用詞彙
- ❌ phase*, stage*, step*
- ❌ 數字編號 (除非有明確意義，如頻率、版本)
- ❌ 抽象概念 (processor, handler 等過於通用)

---

**這個功能性命名策略將徹底解決 phase/stage 混淆問題，建立清晰可維護的系統架構。**