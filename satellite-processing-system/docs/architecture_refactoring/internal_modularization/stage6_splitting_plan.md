# 📊 Stage 6 詳細拆分計劃

**檔案**: `temporal_spatial_analysis_engine.py`
**當前狀況**: 5,821行, 145個方法
**嚴重性**: 🚨 極嚴重
**優先級**: 最高 (立即執行)

## 🎯 拆分目標

### 量化目標
- **主處理器行數**: 5,821行 → < 800行
- **違規功能移除**: 87個違規方法 → 0個
- **模組數量**: 1個巨大檔案 → 5個合理模組
- **職責純度**: 60%混雜 → 100%專注Stage 6

### 品質目標
- **單一職責**: 每個模組職責明確
- **低耦合**: 模組間依賴關係清晰
- **高內聚**: 相關功能聚集在同一模組
- **易測試**: 每個模組可獨立測試

## 📊 當前功能分析

### 違規功能分布 (需要移除)
| 功能類型 | 方法數量 | 代表方法 | 目標去向 |
|----------|----------|----------|----------|
| **軌道計算** | 55個 | `_extract_orbital_elements` | shared/orbital_calculations_core.py |
| **可見性分析** | 32個 | `analyze_coverage_windows` | shared/visibility_calculations_core.py |

### 合法功能分布 (需要保留)
| 功能類型 | 方法數量 | 代表方法 | 目標模組 |
|----------|----------|----------|----------|
| **核心處理** | 8個 | 主要的處理流程方法 | stage6_core_processor.py |
| **動態池策略** | 20個 | `_create_*_strategy` | dynamic_pool_strategy_engine.py |
| **覆蓋優化** | 15個 | `optimize_coverage_*` | coverage_optimization_engine.py |
| **備份管理** | 12個 | `*backup*` | backup_satellite_manager.py |
| **工具函數** | 3個 | `get_analysis_statistics` | pool_planning_utilities.py |

## 🗂️ 詳細拆分計劃

### Step 1: 移除違規功能 (預估減少3,500行)

#### 1.1 軌道計算功能移除
**移除方法列表** (55個):
```python
# 軌道元素相關 (18個方法)
_extract_orbital_elements()
_calculate_mean_anomaly_from_position()
_calculate_mean_anomaly_from_real_elements()
_calculate_argument_of_perigee_from_position()
_calculate_raan_from_position()
_perform_orbital_phase_analysis()
_analyze_mean_anomaly_distribution()
_analyze_raan_distribution()
_calculate_constellation_phase_diversity()
_rate_diversity_score()
_rate_diversity_score_adaptive()
_optimize_raan_distribution()
_select_optimal_raan_distributed_satellites()
_select_satellites_by_orbital_phase()
_select_by_mean_anomaly_phases()
_ensure_satellite_count_requirements()
_reduce_to_optimal_subset()
_calculate_subset_phase_diversity()

# 軌道分析相關 (37個方法)
analyze_orbital_phase_distribution()
_analyze_mean_anomaly_orbital_phases()
_extract_precise_mean_anomaly()
_determine_phase_sector()
_assess_orbital_position_quality()
_calculate_mean_anomaly_distribution_metrics()
_analyze_phase_sectors()
... (其餘29個方法)
```

#### 1.2 可見性分析功能移除
**移除方法列表** (32個):
```python
# 覆蓋視窗分析 (12個方法)
analyze_coverage_windows()
generate_staggering_strategies()
optimize_coverage_distribution()
_identify_complementary_coverage_windows()
_verify_coverage_continuity()
_analyze_temporal_coverage_patterns()
_identify_phase_optimization_opportunities()
_analyze_elevation_coverage_distribution()
_analyze_azimuth_distribution()
_calculate_elevation_complementarity_score()
_optimize_elevation_band_allocation()
_optimize_azimuth_distribution()

# 空間分析相關 (20個方法)
_analyze_spatial_coordination()
_analyze_hemisphere_balance()
_calculate_azimuth_distribution_pattern()
_calculate_azimuth_complementarity()
_resolve_spatial_conflicts()
_enhance_spatial_complementarity()
... (其餘14個方法)
```

### Step 2: 保留功能模組化拆分 (預估2,300行 → 5個模組)

#### 2.1 主處理器模組
**檔案**: `stage6_core_processor.py`
**預估行數**: < 800行
**職責**: 協調各子模組，提供統一的Stage 6介面

**保留方法**:
```python
class Stage6CoreProcessor(BaseStageProcessor):
    def __init__(self)                          # 初始化
    def execute(self)                           # 主執行方法
    def _validate_input_data(self)              # 輸入驗證
    def _coordinate_sub_modules(self)           # 協調子模組
    def _aggregate_results(self)                # 結果整合
    def _format_output(self)                    # 輸出格式化
    def _save_results(self)                     # 結果保存
    def get_processing_statistics(self)         # 處理統計
```

#### 2.2 動態池策略引擎
**檔案**: `dynamic_pool_strategy_engine.py`
**預估行數**: < 700行
**職責**: 動態池選擇和策略決策

**包含方法** (20個):
```python
class DynamicPoolStrategyEngine:
    # 策略創建相關 (8個方法)
    def _create_precise_quantity_maintenance_strategy()
    def _create_temporal_spatial_complementary_strategy()
    def _create_proactive_coverage_guarantee_strategy()
    def _select_optimal_staggering_strategy()
    def _evaluate_strategy_performance()
    def _create_dynamic_backup_satellite_strategy()
    def _implement_max_gap_control_mechanism()
    def _verify_95_plus_coverage_guarantee()

    # 策略執行相關 (12個方法)
    def execute_raan_distribution_optimization()
    def execute_temporal_spatial_complementary_strategy()
    def execute_proactive_coverage_guarantee_mechanism()
    def implement_maximum_gap_control()
    def establish_dynamic_backup_satellite_strategy()
    ... (其餘7個方法)
```

#### 2.3 覆蓋優化引擎
**檔案**: `coverage_optimization_engine.py`
**預估行數**: < 700行
**職責**: 衛星覆蓋範圍優化計算

**包含方法** (15個):
```python
class CoverageOptimizationEngine:
    # 覆蓋分析相關 (8個方法)
    def _finalize_coverage_distribution_optimization()
    def _calculate_phase_diversity_score()
    def _analyze_constellation_specific_patterns()
    def _analyze_selected_phase_distribution()
    def _generate_complementarity_optimization()
    def _execute_precise_satellite_selection_algorithm()
    def _apply_multi_criteria_selection()
    def _calculate_satellite_selection_score_advanced()

    # 優化算法相關 (7個方法)
    def _assess_phase_distribution_contribution()
    def _assess_raan_distribution_contribution()
    def _assess_complementarity_contribution()
    def _select_with_phase_diversity_constraint()
    def _validate_satellite_selections()
    def _assess_orbital_diversity()
    def _generate_orbital_phase_selection_recommendations()
```

#### 2.4 備份衛星管理器
**檔案**: `backup_satellite_manager.py`
**預估行數**: < 600行
**職責**: 備份衛星池管理和切換邏輯

**包含方法** (12個):
```python
class BackupSatelliteManager:
    # 備份池管理 (6個方法)
    def _establish_backup_satellite_pool()
    def _implement_intelligent_backup_evaluation()
    def _establish_rapid_switching_mechanism()
    def _calculate_expected_coverage_at_time()
    def _implement_predictive_coverage_analysis()
    def _analyze_coverage_trends()

    # 監控和調整 (6個方法)
    def _establish_real_time_coverage_monitoring()
    def _calculate_variance()
    def _generate_predictive_alerts()
    def _establish_automatic_adjustment_mechanism()
    def _configure_real_time_coverage_monitoring()
    def _implement_coverage_guarantee_algorithm()
```

#### 2.5 規劃工具模組
**檔案**: `pool_planning_utilities.py`
**預估行數**: < 400行
**職責**: 通用工具函數和輔助計算

**包含方法** (3個):
```python
class PoolPlanningUtilities:
    def get_analysis_statistics()               # 統計分析
    def _extract_satellite_number()             # 衛星編號提取
    def _get_satellite_orbital_data()           # 軌道數據獲取

    # 新增工具方法
    def validate_pool_configuration()           # 池配置驗證
    def format_planning_results()               # 結果格式化
    def calculate_pool_metrics()                # 池指標計算
```

## 🔧 技術實施細節

### 模組間介面設計
```python
# 主處理器介面
class Stage6CoreProcessor:
    def __init__(self):
        self.strategy_engine = DynamicPoolStrategyEngine()
        self.coverage_optimizer = CoverageOptimizationEngine()
        self.backup_manager = BackupSatelliteManager()
        self.utilities = PoolPlanningUtilities()

    def execute(self):
        # 協調各子模組執行
        strategies = self.strategy_engine.create_strategies()
        optimized_coverage = self.coverage_optimizer.optimize(strategies)
        backup_plan = self.backup_manager.create_backup_plan(optimized_coverage)
        return self.utilities.format_planning_results(backup_plan)
```

### 共享模組使用
```python
# 替代移除的軌道計算功能
from shared.core_modules.orbital_calculations_core import OrbitalCalculationsCore
from shared.core_modules.visibility_calculations_core import VisibilityCalculationsCore

class DynamicPoolStrategyEngine:
    def __init__(self):
        self.orbital_calc = OrbitalCalculationsCore()
        self.visibility_calc = VisibilityCalculationsCore()

    def create_strategies(self):
        # 使用共享模組而非重複實現
        orbital_data = self.orbital_calc.calculate_orbital_elements()
        coverage_data = self.visibility_calc.analyze_coverage_windows()
        return self._create_strategies_from_data(orbital_data, coverage_data)
```

## 📋 實施檢查清單

### Phase 1: 違規功能移除
- [ ] 備份原始檔案 `temporal_spatial_analysis_engine.py.backup`
- [ ] 確認55個軌道計算方法列表
- [ ] 確認32個可見性分析方法列表
- [ ] 逐一移除違規方法 (保留呼叫介面)
- [ ] 測試移除後主要功能不受影響
- [ ] 驗證行數減少約3,500行

### Phase 2: 模組拆分
- [ ] 創建5個新模組檔案
- [ ] 設計模組間介面
- [ ] 移植20個動態池策略方法
- [ ] 移植15個覆蓋優化方法
- [ ] 移植12個備份管理方法
- [ ] 移植3個工具方法並擴充
- [ ] 實現主處理器協調邏輯

### Phase 3: 整合測試
- [ ] 單元測試每個新模組
- [ ] 整合測試Stage 6完整流程
- [ ] 性能測試確認無回歸
- [ ] 介面相容性測試
- [ ] 文檔更新和同步

## 🎯 預期成果

### 量化改善
- **檔案大小**: 5,821行 → 5個檔案各<800行
- **職責純度**: 60%混雜 → 100%專注
- **維護效率**: 預估提升70%
- **測試覆蓋**: 從困難 → 每模組獨立測試

### 質量提升
- **可讀性**: 大幅改善
- **可維護性**: 模組化設計
- **可擴展性**: 為RL和GLB準備
- **學術合規**: 使用共享標準模組

---

**執行時間**: 預估2天
**風險等級**: 高 (檔案極大，功能複雜)
**成功標準**: 所有原有功能正常，檔案拆分達標
**下一步**: 等待批准後立即開始執行