# Stage 4 模組化拆分計劃

## 原始檔案
- `timeseries_preprocessing_processor.py` (2,503行, 51個方法)

## 拆分策略 (5個專業化模組)

### 1. RL預處理引擎 (rl_preprocessing_engine.py)
**職責**: 強化學習數據準備和訓練序列生成
**方法** (12個):
- `_prepare_rl_training_sequences`
- `_build_rl_state_vectors` 
- `_construct_20d_state_vector`
- `_define_rl_action_space`
- `_calculate_rl_reward_functions`
- `_create_rl_experience_buffer`
- `_determine_optimal_handover_action`
- `_calculate_real_qos_reward`
- `_calculate_cqi_from_rsrp`
- `generate_rl_training_data`
- `_create_training_episodes`
- `_get_emergency_rsrp_threshold`

### 2. 時序轉換引擎 (timeseries_conversion_engine.py) 
**職責**: 時序數據轉換、格式化和預處理
**方法** (10個):
- `convert_to_enhanced_timeseries`
- `_generate_full_orbital_timeseries`
- `_wgs84_eci_to_geographic_conversion`
- `_process_constellation_timeseries`
- `_process_satellite_timeseries`
- `_extract_original_signal_data`
- `_calculate_max_elevation`
- `_calculate_visible_time`
- `_calculate_avg_signal_quality`
- `_preserve_academic_data_integrity`

### 3. 覆蓋分析引擎 (coverage_analysis_engine.py)
**職責**: 覆蓋窗口分析、間隙檢測和空間分析
**方法** (8個):
- `_analyze_orbital_cycle_coverage`
- `_analyze_constellation_coverage`
- `_extract_visibility_windows`
- `_analyze_coverage_gaps`
- `_calculate_combined_coverage_metrics`
- `_identify_spatial_temporal_windows`
- `_identify_staggered_coverage_windows`
- `_calculate_window_geographic_center`

### 4. 時序數據驗證器 (timeseries_validator.py)
**職責**: 學術標準驗證和數據完整性檢查
**方法** (8個):
- `validate_input`
- `validate_output` 
- `_validate_stage3_input`
- `_validate_timeseries_integrity`
- `_validate_academic_compliance`
- `_perform_zero_tolerance_runtime_checks`
- `run_validation_checks`
- `_calculate_optimal_batch_size`

### 5. 時序輸出管理器 (timeseries_output_manager.py)
**職責**: 結果保存、格式化和輸出管理
**方法** (8個):
- `save_enhanced_timeseries`
- `save_results`
- `extract_key_metrics`
- `get_default_output_filename`
- `_load_stage3_output`
- `_extract_satellites_data`
- `_calculate_processing_summary`
- `_perform_real_time_monitoring`

### 6. 主協調器 (timeseries_preprocessing_processor.py)
**職責**: 協調各專業化模組，保持原有API
**方法** (5個):
- `__init__`
- `_initialize_core_components`
- `load_signal_analysis_output`
- `process_timeseries_preprocessing`
- `process`
- `execute`

## 整合設計
- 所有模組使用共享核心模組
- 維持Grade A學術標準
- 保持向後兼容API
- 消除跨階段功能違規