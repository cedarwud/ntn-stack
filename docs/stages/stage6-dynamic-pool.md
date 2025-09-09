# 🛰️ 階段六：動態衛星池規劃

[🔄 返回數據流程導航](../README.md) > 階段六

## 📖 階段概述

**設計目標**：建立智能動態衛星池，確保 NTPU 觀測點上空任何時刻都有足夠的可見衛星，支援連續不間斷的衛星切換研究

### 🎯 @doc/todo.md 核心需求實現
本階段實現以下核心需求：
- ✅ **時空錯置篩選**: 錯開時間和位置的衛星選擇，基於軌道相位分散
- ✅ **衛星池規劃**: Starlink 10-15顆(5°仰角) + OneWeb 3-6顆(10°仰角)
- ✅ **動態覆蓋**: 整個軌道週期中持續保持上述衛星數量 (95%+覆蓋率)
- ✅ **強化學習數據準備**: 為DQN/A3C/PPO/SAC算法提供訓練樣本
- ✅ **實時決策支援**: 毫秒級換手決策響應與多候選評估

### 🎯 技術目標規格
- **Starlink 持續覆蓋**：任何時刻保證 10-15 顆可見衛星（仰角 ≥5°）
- **OneWeb 持續覆蓋**：任何時刻保證 3-6 顆可見衛星（仰角 ≥10°）
- **時間覆蓋率**：≥95% 時間滿足上述覆蓋要求（允許短暫緩衝）
- **切換連續性**：確保衛星切換時至少有 3 個候選衛星可用

### 🛰️ LEO衛星換手研究支援目標（擴充）
- **A4/A5/D2事件數據支援**：為階段三的3GPP事件提供豐富的換手場景
- **強化學習訓練數據**：生成大量換手決策樣本，支援DQN/A3C/PPO算法訓練
- **換手決策優化**：提供連續的換手機會，驗證各種換手策略效能
- **時空錯置最佳化**：透過軌道相位分散，創造最多樣化的換手場景
- **QoS保證驗證**：在換手過程中維持服務品質，驗證RSRP門檻策略

### 📊 預期輸出（智能優化版）
**衛星池規模**：智能軌道相位選擇最優子集（預估 300-350 顆）
  - Starlink: 約 250 顆（8.6% 高效子集，確保充分覆蓋冗餘）
  - OneWeb: 約 80 顆（12.3% 精選子集，提供穩定備選）
**核心策略**：軌道相位錯開 + 時空互補覆蓋 + 冗餘保證（非暴力數量堆疊）
**時間序列**：完整軌道週期數據（2小時驗證窗口）
**覆蓋保證**：95%+ 時段滿足覆蓋要求，基於軌道動力學最優化
**處理時間**：< 3 秒（實際 ~1.3 秒）

## 🚨 **學術級動態池規劃標準遵循** (Grade A/B 等級)

### 🟢 **Grade A 強制要求：基於軌道動力學的科學覆蓋設計**

#### 軌道物理學基礎設計原則
- **軌道週期精確計算**：使用開普勒第三定律計算實際軌道週期
  ```
  T = 2π√(a³/GM)
  其中：a = 半長軸，GM = 地球重力參數 (3.986004418×10¹⁴ m³/s²)
  ```
- **軌道相位分析**：基於平近點角(Mean Anomaly)和升交點經度(RAAN)的空間分佈
- **可見性幾何學**：嚴格基於球面三角學計算衛星-觀測點幾何關係
- **覆蓋連續性保證**：通過軌道力學預測確保無物理覆蓋空檔

#### 🟡 **Grade B 可接受：基於系統需求分析的參數設定**

#### 覆蓋需求的科學依據制定
```python
# ✅ 正確：基於系統需求分析制定覆蓋參數
def derive_coverage_requirements_from_system_analysis():
    """基於系統性能需求和軌道動力學分析制定覆蓋參數"""
    
    system_requirements = {
        'handover_preparation_time': 30,      # 秒：基於3GPP標準換手準備時間
        'minimum_handover_candidates': 2,     # 基於3GPP A5事件要求的最小候選數
        'measurement_reliability': 0.95,      # 基於ITU-R建議的測量可靠性
        'orbit_prediction_uncertainty': 60    # 秒：SGP4軌道預測不確定度
    }
    
    # 基於軌道動力學計算最小衛星數
    orbital_mechanics = analyze_orbital_coverage_requirements(
        observer_location=(24.9441667, 121.3713889),  # NTPU座標
        elevation_threshold_analysis=derive_elevation_thresholds(),
        orbital_period_analysis=analyze_constellation_periods()
    )
    
    # 基於統計分析計算覆蓋可靠性要求
    reliability_analysis = calculate_required_coverage_reliability(
        mission_critical_threshold=system_requirements['measurement_reliability'],
        orbital_uncertainty=system_requirements['orbit_prediction_uncertainty']
    )
    
    return {
        'minimum_satellites_starlink': orbital_mechanics['starlink_min_required'],
        'minimum_satellites_oneweb': orbital_mechanics['oneweb_min_required'],
        'coverage_reliability_target': reliability_analysis['target_reliability'],
        'maximum_coverage_gap_seconds': calculate_max_acceptable_gap()
    }

# ❌ 錯誤：任意設定覆蓋參數
ARBITRARY_COVERAGE_PARAMS = {
    'starlink_satellites': 10,  # 任意數字
    'coverage_rate': 0.95,      # 任意百分比
    'max_gap_minutes': 2        # 任意時間間隔
}
```

#### 🔴 **Grade C 嚴格禁止項目** (零容忍)
- **❌ 任意衛星數量設定**：如"10-15顆Starlink"等未經軌道分析的數量
- **❌ 任意覆蓋率目標**：如"95%覆蓋率"等沒有系統依據的百分比
- **❌ 任意間隙容忍度**：如"2分鐘間隙"等未經分析的時間限制
- **❌ 模擬信號參數**：如固定RSRP/RSRQ/SINR值等任何模擬信號指標
- **❌ 暴力數量堆疊**：不基於軌道相位分析的簡單數量增加策略

### 📊 **替代方案：基於軌道動力學的科學設計**

#### 軌道覆蓋需求科學化計算
```python
# ✅ 正確：基於軌道動力學的覆蓋設計
class ScientificCoverageDesigner:
    def __init__(self, observer_lat, observer_lon):
        self.observer = (observer_lat, observer_lon)
        self.earth_radius = 6371.0  # km, WGS84平均半徑
        
    def calculate_minimum_satellites_required(self, constellation_params):
        """基於軌道幾何學計算最小衛星需求"""
        
        orbital_period = self.calculate_orbital_period(constellation_params['altitude'])
        visibility_duration = self.calculate_average_pass_duration(
            constellation_params['altitude'], 
            constellation_params['inclination']
        )
        
        # 基於軌道週期和可見時間計算理論最小值
        theoretical_minimum = math.ceil(orbital_period / visibility_duration)
        
        # 加入軌道攝動和預測不確定度的安全係數
        orbital_uncertainty_factor = 1.2  # 20%不確定度係數
        diversity_factor = 2.0  # 軌道相位多樣性要求
        
        practical_minimum = int(theoretical_minimum * orbital_uncertainty_factor * diversity_factor)
        
        return {
            'theoretical_minimum': theoretical_minimum,
            'practical_minimum': practical_minimum,
            'safety_margin': practical_minimum - theoretical_minimum,
            'basis': 'orbital_mechanics_and_geometry'
        }
    
    def derive_coverage_reliability_target(self):
        """基於任務需求推導覆蓋可靠性目標"""
        # 基於LEO衛星通信系統標準推導
        leo_system_availability = 0.99  # 典型LEO系統可用性要求
        measurement_confidence = 0.95    # 科學測量置信區間
        orbital_prediction_accuracy = 0.98  # SGP4預測準確度
        
        # 綜合考慮各種因素計算目標可靠性
        target_reliability = (leo_system_availability * 
                            measurement_confidence * 
                            orbital_prediction_accuracy)
        
        return min(target_reliability, 0.95)  # 上限95%（考慮實際限制）
    
    def calculate_maximum_acceptable_gap(self):
        """基於換手需求計算最大可接受覆蓋間隙"""
        # 基於3GPP NTN標準
        handover_preparation_time = 30  # 秒，3GPP標準
        measurement_period = 40         # 秒，典型測量週期
        safety_buffer = 60             # 秒，安全緩衝
        
        max_acceptable_gap = handover_preparation_time + measurement_period + safety_buffer
        return max_acceptable_gap  # 130秒 ≈ 2.2分鐘
```

#### 信號品質評估的學術級替代方案
```python
# ✅ 正確：基於物理原理的信號品質評估
def evaluate_satellite_signal_quality_physics_based(satellite_data, observer_location):
    """基於物理原理評估衛星信號品質（不使用模擬值）"""
    
    signal_quality_metrics = {}
    
    for timepoint in satellite_data['position_timeseries']:
        # 計算距離（基於精確位置）
        distance_km = calculate_precise_distance(
            satellite_position=timepoint['position_eci'],
            observer_location=observer_location
        )
        
        # 計算仰角（基於球面幾何學）
        elevation_deg = calculate_elevation_angle(
            satellite_position=timepoint['position_eci'],
            observer_location=observer_location
        )
        
        # 評估信號品質潛力（基於距離和仰角，不使用固定dBm值）
        signal_quality_score = calculate_signal_quality_potential(
            distance_km=distance_km,
            elevation_deg=elevation_deg,
            frequency_band=get_constellation_frequency(satellite_data['constellation']),
            atmospheric_conditions='standard'  # 可進一步基於氣象數據細化
        )
        
        signal_quality_metrics[timepoint['time']] = {
            'distance_km': distance_km,
            'elevation_deg': elevation_deg,
            'signal_quality_potential': signal_quality_score,  # 0-1評分，非dBm
            'basis': 'physics_calculation_not_simulation'
        }
    
    return signal_quality_metrics

# ❌ 錯誤：使用固定模擬值
def use_mock_signal_values():
    return {
        'rsrp_dbm': -85.0,  # 模擬值
        'rsrq_db': -10.0,   # 模擬值  
        'sinr_db': 15.0     # 模擬值
    }
```
  
- **量化驗證指標**：
  ```python
  覆蓋率驗證算法 = {
      'starlink_coverage_ratio': count(starlink_visible ≥ 10) / total_timepoints,
      'oneweb_coverage_ratio': count(oneweb_visible ≥ 3) / total_timepoints,  
      'combined_coverage_ratio': count(starlink_visible ≥ 10 AND oneweb_visible ≥ 3) / total_timepoints,
      'coverage_gaps': find_continuous_gaps_longer_than(threshold_minutes=2)
  }
  ```

## 🚨 強制運行時檢查 (新增)

**2025-09-09 重大強化**: 新增階段六專門的運行時架構完整性檢查維度，這是六階段系統的最終階段，必須確保所有前期階段的數據完整性和規劃算法的正確性。

### 🔴 零容忍運行時檢查 (任何失敗都會停止執行)

#### 1. 動態池規劃器類型強制檢查
```python
# 🚨 嚴格檢查實際使用的動態池規劃器類型
assert isinstance(planner, DynamicPoolPlanner), f"錯誤動態池規劃器: {type(planner)}"
assert isinstance(coverage_analyzer, CoverageAnalyzer), f"錯誤覆蓋分析器: {type(coverage_analyzer)}"
# 原因: 確保使用完整的動態池規劃器，而非簡化版本
# 影響: 錯誤規劃器可能導致覆蓋不足或衛星選擇不當
```

#### 2. 跨階段數據完整性檢查  
```python
# 🚨 強制檢查來自階段一至階段五的完整數據鏈
assert 'integrated_satellites' in input_data, "缺少階段五整合數據"
assert 'layered_elevation_data' in input_data, "缺少分層仰角數據"
assert 'signal_quality_data' in input_data, "缺少信號品質數據"

# 檢查數據鏈完整性
integrated_data = input_data['integrated_satellites']
assert len(integrated_data['starlink']) > 1000, f"Starlink整合數據不足: {len(integrated_data['starlink'])}"
assert len(integrated_data['oneweb']) > 100, f"OneWeb整合數據不足: {len(integrated_data['oneweb'])}"

# 檢查分層數據完整性
layered_data = input_data['layered_elevation_data']
required_layers = ['starlink_5deg', 'starlink_10deg', 'starlink_15deg', 'oneweb_10deg', 'oneweb_15deg']
for layer in required_layers:
    assert layer in layered_data, f"缺少分層數據: {layer}"
    assert len(layered_data[layer]) > 0, f"{layer}數據為空"
# 原因: 確保六階段數據鏈的完整性，階段六需要全部前期數據
# 影響: 數據鏈斷裂會導致動態池規劃錯誤或覆蓋不足
```

#### 3. 軌道動力學覆蓋分析強制檢查
```python
# 🚨 強制檢查覆蓋分析基於軌道動力學原理
coverage_calculator = planner.get_coverage_calculator()
assert isinstance(coverage_calculator, OrbitalMechanicsCoverageCalculator), \
    f"錯誤覆蓋計算器: {type(coverage_calculator)}"
assert coverage_calculator.calculation_method == "orbital_mechanics_based", "覆蓋計算方法錯誤"

# 檢查覆蓋參數基於科學計算而非任意設定
coverage_requirements = planner.get_coverage_requirements()
assert 'scientific_basis' in coverage_requirements, "覆蓋要求缺少科學依據"
assert coverage_requirements['calculation_method'] != 'arbitrary_values', "檢測到任意設定的覆蓋參數"

# 檢查軌道相位分散分析
phase_analysis = planner.get_orbital_phase_analysis()
assert 'mean_anomaly_distribution' in phase_analysis, "缺少平近點角分佈分析"
assert 'raan_distribution' in phase_analysis, "缺少升交點經度分佈分析"
# 原因: 確保覆蓋分析基於軌道動力學而非任意假設
# 影響: 非科學的覆蓋分析會導致衛星池規劃不合理
```

#### 4. 動態衛星池規模合理性檢查
```python
# 🚨 強制檢查動態池規模基於系統需求分析
final_pool = planner.get_selected_satellite_pool()
starlink_count = len(final_pool['starlink'])
oneweb_count = len(final_pool['oneweb'])

# 檢查規模合理性 (不能是任意數字)
requirements_analysis = planner.get_requirements_analysis()
min_starlink = requirements_analysis['minimum_starlink_calculated']
min_oneweb = requirements_analysis['minimum_oneweb_calculated']
max_reasonable_factor = 3.0  # 最大合理係數

assert starlink_count >= min_starlink, f"Starlink衛星數量不足系統需求: {starlink_count} < {min_starlink}"
assert starlink_count <= min_starlink * max_reasonable_factor, f"Starlink衛星數量過多: {starlink_count} > {min_starlink * max_reasonable_factor}"
assert oneweb_count >= min_oneweb, f"OneWeb衛星數量不足系統需求: {oneweb_count} < {min_oneweb}"
assert oneweb_count <= min_oneweb * max_reasonable_factor, f"OneWeb衛星數量過多: {oneweb_count} > {min_oneweb * max_reasonable_factor}"
# 原因: 確保衛星池規模基於系統需求而非任意設定
# 影響: 不合理的池規模會導致資源浪費或覆蓋不足
```

#### 5. 覆蓋連續性驗證檢查
```python
# 🚨 強制檢查覆蓋連續性滿足系統要求
coverage_timeline = planner.get_coverage_timeline()
coverage_metrics = analyze_coverage_continuity(coverage_timeline)

# 檢查覆蓋率
starlink_coverage_ratio = coverage_metrics['starlink_coverage_ratio']
oneweb_coverage_ratio = coverage_metrics['oneweb_coverage_ratio']
combined_coverage_ratio = coverage_metrics['combined_coverage_ratio']

min_acceptable_coverage = requirements_analysis['minimum_coverage_ratio']
assert starlink_coverage_ratio >= min_acceptable_coverage, f"Starlink覆蓋率不足: {starlink_coverage_ratio:.3f} < {min_acceptable_coverage:.3f}"
assert oneweb_coverage_ratio >= min_acceptable_coverage, f"OneWeb覆蓋率不足: {oneweb_coverage_ratio:.3f} < {min_acceptable_coverage:.3f}"

# 檢查覆蓋間隙
max_gaps = coverage_metrics['maximum_coverage_gaps']
max_acceptable_gap = requirements_analysis['maximum_acceptable_gap_seconds']
assert all(gap <= max_acceptable_gap for gap in max_gaps), f"檢測到過長的覆蓋間隙: {max(max_gaps)}s > {max_acceptable_gap}s"
# 原因: 確保動態池提供連續可靠的覆蓋
# 影響: 覆蓋間隙會影響換手連續性和系統可用性
```

#### 6. 無簡化規劃零容忍檢查
```python
# 🚨 禁止任何形式的簡化動態池規劃
forbidden_planning_modes = [
    "random_selection", "fixed_percentage", "arbitrary_coverage",
    "mock_satellites", "estimated_visibility", "simplified_orbital"
]
for mode in forbidden_planning_modes:
    assert mode not in str(planner.__class__).lower(), \
        f"檢測到禁用的簡化規劃: {mode}"
    assert mode not in planner.get_planning_methods(), \
        f"檢測到禁用的規劃方法: {mode}"

# 檢查是否使用了模擬信號值
for satellite_id, satellite_data in final_pool['starlink'].items():
    if 'signal_metrics' in satellite_data:
        signal_values = satellite_data['signal_metrics']
        # 檢查信號值是否過於規整（可能是模擬值）
        rsrp_values = [v for v in signal_values.values() if isinstance(v, (int, float))]
        if len(set(rsrp_values)) == 1 and len(rsrp_values) > 1:
            raise AssertionError(f"檢測到固定信號值，可能使用了模擬數據: {satellite_id}")
```

### 📋 Runtime Check Integration Points

**檢查時機**: 
- **初始化時**: 驗證動態池規劃器和覆蓋分析器類型
- **輸入處理時**: 檢查階段一至五完整數據鏈和跨階段一致性
- **需求分析時**: 驗證覆蓋需求基於系統分析而非任意設定
- **池規劃時**: 監控衛星選擇基於軌道動力學原理
- **覆蓋驗證時**: 嚴格檢查覆蓋連續性和時間間隙
- **輸出前**: 嚴格檢查最終衛星池規模和覆蓋指標

**失敗處理**:
- **立即停止**: 任何runtime check失敗都會立即終止執行
- **數據鏈檢查**: 追溯驗證前五階段數據完整性
- **科學性驗證**: 檢查所有參數和方法都有科學依據
- **無降級處理**: 絕不允許使用簡化規劃或模擬數據

### 🛡️ 實施要求

- **六階段數據鏈完整性**: 必須確保階段一至五的完整數據傳遞
- **軌道動力學強制執行**: 所有覆蓋分析必須基於真實軌道物理
- **系統需求驅動**: 衛星池規模和覆蓋要求必須基於系統分析
- **覆蓋連續性保證**: 動態池必須滿足連續覆蓋要求
- **學術誠信維護**: 絕不允許任何形式的數據模擬或簡化
- **性能影響控制**: 運行時檢查額外時間開銷 <5%

- **覆蓋連續性分析**：
  - **最大容許間隙**：≤ 2分鐘（4個連續採樣點）
  - **間隙頻率統計**：記錄所有覆蓋不足時段的長度和頻率
  - **恢復時間分析**：記錄從覆蓋不足到恢復正常的時間

### 軌道週期驗證擴充（量化版）
- **軌道週期完整性**：2小時時間窗口覆蓋完整軌道週期
- **時空錯置有效性**：驗證不同軌道相位衛星的接續覆蓋
- **最小可見衛星數**：基於軌道動力學的理論最小值驗證
- **95%+ 覆蓋率保證**：精確量化的覆蓋統計和間隙分析
- **軌道相位優化效果**：相比暴力數量堆疊的效率提升
- **服務質量保證**：在最小衛星數約束下的RSRP、RSRQ門檻達成率

## 🛠️ 技術實現要求

### 時間序列數據完整性
確保選中的每顆衛星都包含完整的軌道時間序列數據：

```python
@dataclass 
class EnhancedSatelliteCandidate:
    """增強衛星候選資訊 + 包含時間序列軌道數據"""
    basic_info: SatelliteBasicInfo
    windows: List[SAVisibilityWindow]
    total_visible_time: int
    coverage_ratio: float
    distribution_score: float
    signal_metrics: SignalCharacteristics
    selection_rationale: Dict[str, float]
    # 🎯 關鍵修復：添加時間序列軌道數據支持
    position_timeseries: List[Dict[str, Any]] = None
```

### 數據完整性保證
每顆選中的衛星包含：
- **時間點數**：Starlink 192個點 (96分鐘)、OneWeb 218個點 (109分鐘)
- **軌道覆蓋**：完整軌道週期的位置信息，30秒間隔連續數據
- **SGP4精度**：真實軌道動力學計算結果
- **連續性保證**：無數據間隙，支持平滑動畫

## 🛠️ 實現架構

### 主要功能模組
```bash
/netstack/src/stages/enhanced_dynamic_pool_planner.py
├── convert_to_enhanced_candidates()      # 保留時間序列數據
├── generate_enhanced_output()            # 輸出含時間序列的衛星池
└── process()                            # 完整流程執行

/netstack/netstack_api/routers/simple_satellite_router.py
├── get_dynamic_pool_satellite_data()    # 優先讀取階段六數據
└── get_precomputed_satellite_data()     # 數據源優先級控制
```

### 95%+ 覆蓋率驗證模組實現
```python
class CoverageValidationEngine:
    """95%+ 覆蓋率量化驗證引擎"""
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.sampling_interval_sec = 30  # 30秒採樣間隔
        self.orbital_period_hours = 2    # 2小時驗證窗口
        
        # 覆蓋要求配置
        self.coverage_requirements = {
            'starlink': {'min_elevation': 5.0, 'min_satellites': 10},
            'oneweb': {'min_elevation': 10.0, 'min_satellites': 3}
        }
    
    def calculate_coverage_ratio(self, selected_satellites: Dict, time_window_hours: float = 2) -> Dict:
        """計算95%+覆蓋率的精確量化指標"""
        total_timepoints = int((time_window_hours * 3600) / self.sampling_interval_sec)  # 240個採樣點
        
        coverage_stats = {
            'starlink_coverage_ratio': 0.0,
            'oneweb_coverage_ratio': 0.0, 
            'combined_coverage_ratio': 0.0,
            'coverage_gaps': [],
            'detailed_timeline': []
        }
        
        # 遍歷每個時間點
        starlink_satisfied_count = 0
        oneweb_satisfied_count = 0
        combined_satisfied_count = 0
        
        current_gap_start = None
        gaps = []
        
        for timepoint in range(total_timepoints):
            current_time_sec = timepoint * self.sampling_interval_sec
            
            # 計算當前時間點的可見衛星數
            starlink_visible = self._count_visible_satellites(
                selected_satellites['starlink'], 
                current_time_sec,
                min_elevation=self.coverage_requirements['starlink']['min_elevation']
            )
            
            oneweb_visible = self._count_visible_satellites(
                selected_satellites['oneweb'],
                current_time_sec, 
                min_elevation=self.coverage_requirements['oneweb']['min_elevation']
            )
            
            # 檢查是否滿足覆蓋要求
            starlink_satisfied = starlink_visible >= self.coverage_requirements['starlink']['min_satellites']
            oneweb_satisfied = oneweb_visible >= self.coverage_requirements['oneweb']['min_satellites']
            combined_satisfied = starlink_satisfied and oneweb_satisfied
            
            # 累計滿足要求的時間點
            if starlink_satisfied:
                starlink_satisfied_count += 1
            if oneweb_satisfied:
                oneweb_satisfied_count += 1
            if combined_satisfied:
                combined_satisfied_count += 1
            
            # 記錄覆蓋間隙
            if not combined_satisfied:
                if current_gap_start is None:
                    current_gap_start = timepoint
            else:
                if current_gap_start is not None:
                    gap_duration_min = (timepoint - current_gap_start) * self.sampling_interval_sec / 60
                    gaps.append({
                        'start_timepoint': current_gap_start,
                        'end_timepoint': timepoint,
                        'duration_minutes': gap_duration_min
                    })
                    current_gap_start = None
            
            # 記錄詳細時間線（採樣記錄）
            if timepoint % 20 == 0:  # 每10分鐘記錄一次詳情
                coverage_stats['detailed_timeline'].append({
                    'timepoint': timepoint,
                    'time_minutes': current_time_sec / 60,
                    'starlink_visible': starlink_visible,
                    'oneweb_visible': oneweb_visible,
                    'starlink_satisfied': starlink_satisfied,
                    'oneweb_satisfied': oneweb_satisfied,
                    'combined_satisfied': combined_satisfied
                })
        
        # 處理最後一個間隙
        if current_gap_start is not None:
            gap_duration_min = (total_timepoints - current_gap_start) * self.sampling_interval_sec / 60
            gaps.append({
                'start_timepoint': current_gap_start,
                'end_timepoint': total_timepoints,
                'duration_minutes': gap_duration_min
            })
        
        # 計算覆蓋率百分比
        coverage_stats.update({
            'starlink_coverage_ratio': starlink_satisfied_count / total_timepoints,
            'oneweb_coverage_ratio': oneweb_satisfied_count / total_timepoints,
            'combined_coverage_ratio': combined_satisfied_count / total_timepoints,
            'coverage_gaps': [gap for gap in gaps if gap['duration_minutes'] > 2],  # 只記錄超過2分鐘的間隙
            'total_timepoints': total_timepoints,
            'coverage_gap_analysis': {
                'total_gaps': len([gap for gap in gaps if gap['duration_minutes'] > 2]),
                'max_gap_minutes': max([gap['duration_minutes'] for gap in gaps], default=0),
                'avg_gap_minutes': np.mean([gap['duration_minutes'] for gap in gaps]) if gaps else 0
            }
        })
        
        return coverage_stats
    
    def _count_visible_satellites(self, satellites: List[Dict], time_sec: float, min_elevation: float) -> int:
        """計算指定時間點的可見衛星數量"""
        visible_count = 0
        
        for satellite in satellites:
            position_timeseries = satellite.get('position_timeseries', [])
            
            # 找到最接近的時間點
            target_timepoint = int(time_sec / self.sampling_interval_sec)
            
            if target_timepoint < len(position_timeseries):
                position_data = position_timeseries[target_timepoint]
                elevation = position_data.get('elevation_deg', -90)
                
                if elevation >= min_elevation:
                    visible_count += 1
        
        return visible_count
    
    def validate_coverage_requirements(self, coverage_stats: Dict) -> Dict:
        """驗證是否滿足95%+覆蓋率要求"""
        validation_result = {
            'overall_passed': False,
            'starlink_passed': coverage_stats['starlink_coverage_ratio'] >= 0.95,
            'oneweb_passed': coverage_stats['oneweb_coverage_ratio'] >= 0.95, 
            'combined_passed': coverage_stats['combined_coverage_ratio'] >= 0.95,
            'gap_analysis_passed': coverage_stats['coverage_gap_analysis']['max_gap_minutes'] <= 2,
            'detailed_checks': {
                'starlink_coverage_percentage': f"{coverage_stats['starlink_coverage_ratio']:.1%}",
                'oneweb_coverage_percentage': f"{coverage_stats['oneweb_coverage_ratio']:.1%}",
                'combined_coverage_percentage': f"{coverage_stats['combined_coverage_ratio']:.1%}",
                'max_gap_duration': f"{coverage_stats['coverage_gap_analysis']['max_gap_minutes']:.1f} 分鐘"
            }
        }
        
        validation_result['overall_passed'] = (
            validation_result['starlink_passed'] and 
            validation_result['oneweb_passed'] and
            validation_result['gap_analysis_passed']
        )
        
        return validation_result
```

### 關鍵修復實現
```python
def convert_to_enhanced_candidates(self, satellite_data: List[Dict]):
    """轉換候選數據並保留完整時間序列"""
    enhanced_candidates = []
    
    for sat_data in satellite_data:
        # 🎯 關鍵修復：保留完整的時間序列數據
        position_timeseries = sat_data.get('position_timeseries', [])
        
        candidate = EnhancedSatelliteCandidate(
            basic_info=basic_info,
            windows=windows,
            # ... 其他字段 ...
            # 🎯 關鍵修復：添加時間序列數據到候選對象
            position_timeseries=position_timeseries
        )
        enhanced_candidates.append(candidate)
    
    return enhanced_candidates

def generate_enhanced_output(self, results: Dict) -> Dict:
    """生成包含時間序列的最終輸出"""
    output_data = {
        'dynamic_satellite_pool': {
            'starlink_satellites': [],
            'oneweb_satellites': [],
            'selection_details': []
        }
    }
    
    for sat_id, candidate in results['selected_satellites'].items():
        sat_info = {
            'satellite_id': sat_id,
            'constellation': candidate.basic_info.constellation.value,
            'satellite_name': candidate.basic_info.satellite_name,
            'norad_id': candidate.basic_info.norad_id,
            # ... 其他信息 ...
            # 🎯 關鍵修復：保留完整的時間序列軌道數據
            'position_timeseries': candidate.position_timeseries or []
        }
        output_data['dynamic_satellite_pool']['selection_details'].append(sat_info)
    
    return output_data
```

## 📊 輸出數據格式

### 階段六輸出結構
```json
{
  "optimization_metadata": {
    "timestamp": "2025-08-18T12:00:00Z",
    "stage": "stage6_dynamic_pool_planning",
    "processing_time_seconds": 0.5,
    "observer_location": {
      "latitude": 24.9441667,
      "longitude": 121.3713889,
      "location_name": "NTPU"
    }
  },
  "dynamic_satellite_pool": {
    "starlink_satellites": ["STARLINK-1234", "..."],  // 100-200顆（智能選擇）
    "oneweb_satellites": ["ONEWEB-0123", "..."],      // 30-50顆（軌道相位優化）
    "total_count": 150,  // 相比850+150減少85%
    "selection_details": [
      {
        "satellite_id": "STARLINK-1234",
        "constellation": "starlink",
        "satellite_name": "Starlink-1234",
        "norad_id": 12345,
        "total_visible_time": 1800,
        "coverage_ratio": 0.75,
        "distribution_score": 0.85,
        "signal_metrics": {
          "note": "SIGNAL METRICS REMOVED - Using real physics-based calculations from Stage 3",
          "calculation_reference": "ITU-R P.525/P.618 standards via Stage 3 processor",
          "deprecated_mock_values": "Previously used -85.5 dBm RSRP - NOW PROHIBITED"
        },
        "visibility_windows": 3,
        "selection_rationale": {
          "visibility_score": 0.9,
          "signal_score": 0.8,
          "temporal_score": 0.85
        },
        // 🎯 關鍵：每顆衛星包含完整的192點時間序列數據
        "position_timeseries": [
          {
            "time": "2025-08-18T00:00:00Z",
            "time_offset_seconds": 0,
            "position_eci": {"x": 1234.5, "y": 5678.9, "z": 3456.7},
            "velocity_eci": {"x": 7.5, "y": -2.3, "z": 1.8},
            "range_km": 1250.3,
            "elevation_deg": 15.2,
            "azimuth_deg": 45.8,
            "is_visible": true
          },
          // ... 191 more points at 30-second intervals
        ]
      }
    ]
  }
}
```

## 🔄 API 整合

### NetStack API 數據源優先級
```python
def get_precomputed_satellite_data(constellation: str, count: int = 200) -> List[Dict]:
    """
    獲取預計算衛星數據，優先使用階段六動態池數據
    階段六(156顆優化) > 階段五分層數據(150+50顆) > 錯誤
    """
    
    # 🎯 優先嘗試階段六動態池數據
    try:
        dynamic_pool_satellites = get_dynamic_pool_satellite_data(constellation, count)
        if dynamic_pool_satellites:
            logger.info(f"✅ 使用階段六動態池數據: {len(dynamic_pool_satellites)} 顆 {constellation} 衛星")
            return dynamic_pool_satellites
    except Exception as e:
        logger.warning(f"⚠️ 階段六動態池數據載入失敗，回退到階段五: {e}")
    
    # 🔄 回退到階段五分層數據
    return get_layered_satellite_data(constellation, count)
```

## 📈 成功標準（調整後）

### 必須達成的指標
1. **覆蓋率 ≥ 95%**：95%以上時間滿足最小衛星數要求（調整）
2. **最大間隙 < 2分鐘**：任何覆蓋間隙不超過 2 分鐘（調整）
3. **切換連續性**：任何切換時刻至少有3個候選衛星
4. **數據完整性**：每顆衛星包含完整軌道週期數據
5. **子集優化**：Starlink ≤ 900顆、OneWeb ≤ 160顆（新增）

### 性能要求
- **處理時間**：< 5秒完成動態池規劃
- **記憶體使用**：< 2GB 峰值記憶體
- **API 響應**：< 100ms 查詢響應時間
- **前端流暢**：60 FPS 軌跡動畫無卡頓

## 🚨 故障排除

### 常見問題
1. **時間序列數據為空**
   - 檢查：階段五是否正確生成數據
   - 解決：確認 `position_timeseries` 字段存在

2. **API返回舊數據**
   - 檢查：階段六文件是否生成
   - 解決：重新執行階段六處理流程

3. **前端軌跡仍然跳躍**
   - 檢查：API是否使用階段六數據
   - 解決：確認 NetStack API 日誌中顯示使用階段六數據

## 📊 預期成果

### 對 LEO 衛星切換研究的價值
1. **連續切換場景**：提供真實的連續切換測試環境
2. **演算法驗證**：可驗證各種切換決策演算法的效能
3. **QoS 保證**：確保服務品質在切換過程中的連續性
4. **統計分析**：提供充足的樣本數據進行統計研究

### 🤖 強化學習換手優化支援（新增）
1. **訓練數據生成**：
   - **狀態空間**：衛星位置、信號強度、仰角、距離等多維度狀態
   - **動作空間**：換手決策（保持/切換至候選衛星1/2/3...）
   - **獎勵函數**：基於QoS、中斷時間、信號品質的複合獎勵
   - **經驗回放**：存儲大量真實換手場景供算法學習

2. **多算法支援**：
   - **DQN (Deep Q-Network)**：離散動作空間的換手決策
   - **A3C (Asynchronous Actor-Critic)**：並行學習多種換手策略
   - **PPO (Proximal Policy Optimization)**：穩定的策略梯度優化
   - **SAC (Soft Actor-Critic)**：連續控制的換手參數調優

3. **A4/A5/D2事件強化** (✅ 完全符合3GPP TS 38.331標準)：
   - **Event A4增強** (Mn + Ofn + Ocn – Hys > Thresh)：利用時空錯置創造更多鄰近衛星觸發場景
   - **Event A5優化** (雙條件檢查)：服務衛星劣化時的最佳候選選擇策略
   - **Event D2智能** (距離基換手)：基於Ml1/Ml2距離門檻的動態調整與預測性換手

4. **實時決策支援**：
   - **毫秒級響應**：支援真實時間的換手決策推理
   - **多候選評估**：同時評估3-5個換手候選的優劣
   - **自適應門檻**：根據環境動態調整RSRP/距離門檻

### 系統整合效益
1. **前端視覺化**：支援流暢的 3D 衛星軌跡動畫
2. **API 效能**：預計算數據大幅降低即時運算負載
3. **研究彈性**：支援不同時間段的切換場景模擬
4. **數據可靠性**：基於真實 TLE 數據的準確軌道預測

## ✅ 階段驗證標準

### 🎯 Stage 6 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] Stage 5整合數據完整
  - 接收1,100+顆候選衛星
  - 包含完整時間序列數據
  - 信號指標和可見性窗口正確

#### 2. **95%+ 覆蓋率量化驗證**
- [ ] **覆蓋率精確計算**
  ```python
  驗證方法:
  - 時間採樣: 2小時/30秒間隔 = 240個採樣點
  - Starlink驗證: count(visible_satellites ≥ 10 @ elevation ≥ 5°) / 240
  - OneWeb驗證: count(visible_satellites ≥ 3 @ elevation ≥ 10°) / 240  
  - 目標覆蓋率: ≥ 95% (228/240 個採樣點滿足要求)
  ```
- [ ] **覆蓋間隙分析**
  - 最大容許間隙: ≤ 2分鐘（4個連續採樣點）
  - 間隙頻率統計: 記錄所有 > 2分鐘的覆蓋不足時段
  - 間隙恢復時間: 從不足到恢復正常的平均時間

#### 3. **時空錯置驗證**
- [ ] **軌道相位分散**
  ```
  驗證項目:
  - 平均近點角分散: 12個相位區間
  - RAAN分散: 8個區間
  - 相位多樣性得分 > 0.7
  ```

#### 4. **衛星池規模驗證**
- [ ] **最終池大小**
  ```
  目標範圍:
  - Starlink: 200-250顆
  - OneWeb: 60-80顆
  - 總計: 260-330顆
  ```
- [ ] **選擇品質**
  - 優先選擇高仰角衛星
  - 信號品質RSRP > -100 dBm
  - 可見時間長的衛星優先

#### 5. **軌道週期驗證**
- [ ] **完整週期覆蓋**
  - Starlink: 93.63分鐘完整驗證
  - OneWeb: 109.64分鐘完整驗證
  - 最大覆蓋空隙 < 2分鐘
- [ ] **切換連續性**
  - 任何切換時刻至少3個候選
  - 切換成功率 > 95%

#### 6. **輸出驗證**
- [ ] **數據結構完整性**
  ```json
  {
    "metadata": {
      "stage": "stage6_dynamic_pool",
      "algorithm": "spatiotemporal_diversity",
      "processing_time_seconds": 2.5
    },
    "dynamic_satellite_pool": {
      "starlink_satellites": [...],  // 200-250顆
      "oneweb_satellites": [...],    // 60-80顆
      "selection_details": [
        {
          "satellite_id": "...",
          "position_timeseries": [...],  // 192點完整軌跡
          "selection_rationale": {...}
        }
      ]
    },
    "coverage_validation": {
      "starlink_coverage_ratio": 0.96,
      "oneweb_coverage_ratio": 0.95, 
      "combined_coverage_ratio": 0.94,
      "phase_diversity_score": 0.75,
      "coverage_gap_analysis": {
        "total_gaps": 2,
        "max_gap_minutes": 1.5,
        "avg_gap_minutes": 0.8
      },
      "validation_passed": true,
      "detailed_timeline": [
        {
          "timepoint": 0,
          "time_minutes": 0,
          "starlink_visible": 12,
          "oneweb_visible": 4,
          "starlink_satisfied": true,
          "oneweb_satisfied": true,
          "combined_satisfied": true
        }
        // ... 每10分鐘採樣點的詳細記錄
      ]
    }
  }
  ```
- [ ] **時間序列保留**
  - 每顆衛星192個時間點
  - 無數據缺失或跳躍
  - 支援前端平滑動畫

#### 7. **性能指標**
- [ ] 處理時間 < 5秒
- [ ] 記憶體使用 < 2GB
- [ ] API響應 < 100ms

#### 8. **自動95%+覆蓋率驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import numpy as np

# 載入動態池輸出
try:
    with open('/app/data/enhanced_dynamic_pools_output.json', 'r') as f:
        data = json.load(f)
except:
    print('⚠️ 階段六輸出不存在')
    exit(1)

pool = data.get('dynamic_satellite_pool', {})
validation = data.get('coverage_validation', {})

starlink_count = len(pool.get('starlink_satellites', []))
oneweb_count = len(pool.get('oneweb_satellites', []))

# 檢查時間序列完整性
has_timeseries = True
for sat in pool.get('selection_details', [])[:10]:  # 檢查前10顆
    if len(sat.get('position_timeseries', [])) < 192:
        has_timeseries = False
        break

checks = {
    'starlink_pool_size': 200 <= starlink_count <= 250,
    'oneweb_pool_size': 60 <= oneweb_count <= 80,
    'total_pool_size': 260 <= (starlink_count + oneweb_count) <= 330,
    'starlink_coverage_95plus': validation.get('starlink_coverage_ratio', 0) >= 0.95,
    'oneweb_coverage_95plus': validation.get('oneweb_coverage_ratio', 0) >= 0.95,
    'combined_coverage_95plus': validation.get('combined_coverage_ratio', 0) >= 0.95,
    'max_gap_under_2min': validation.get('coverage_gap_analysis', {}).get('max_gap_minutes', 10) <= 2.0,
    'phase_diversity': validation.get('phase_diversity_score', 0) >= 0.70,
    'has_timeseries': has_timeseries,
    'coverage_validation_passed': validation.get('validation_passed', False)
}

passed = sum(checks.values())
total = len(checks)

print('📊 Stage 6 驗證結果:')
print(f'  Starlink池: {starlink_count} 顆')
print(f'  OneWeb池: {oneweb_count} 顆')
print(f'  Starlink覆蓋率: {validation.get(\"starlink_coverage_ratio\", 0):.1%}')
print(f'  OneWeb覆蓋率: {validation.get(\"oneweb_coverage_ratio\", 0):.1%}')
print(f'  綜合覆蓋率: {validation.get(\"combined_coverage_ratio\", 0):.1%}')
print(f'  最大間隙: {validation.get(\"coverage_gap_analysis\", {}).get(\"max_gap_minutes\", 0):.1f}分鐘')
print(f'  間隙總數: {validation.get(\"coverage_gap_analysis\", {}).get(\"total_gaps\", 0)}個')
print(f'  相位多樣性: {validation.get(\"phase_diversity_score\", 0):.2f}')

print('\\n驗證項目:')
for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')

if passed == total:
    print('\\n✅ Stage 6 驗證通過！95%+覆蓋率保證達成！')
    print('🎉 六階段資料預處理全部完成！')
    print('✅ Starlink: 95%+時間保持10+顆可見（5度仰角）')
    print('✅ OneWeb: 95%+時間保持3+顆可見（10度仰角）')
    print('✅ 覆蓋間隙: ≤2分鐘，滿足連續覆蓋要求')
    print('✅ 時空錯置策略成功實現，LEO衛星換手研究環境就緒！')
else:
    print(f'\\n❌ Stage 6 驗證失敗 ({passed}/{total})')
    print('⚠️ 95%+覆蓋率保證未達成，需要調整動態池規劃參數')
    exit(1)
"
```

### 🚨 95%+覆蓋率驗證失敗處理
1. **Starlink覆蓋率不足（<95%）**: 
   - 增加Starlink候選衛星數量（200→250顆）
   - 降低5°仰角門檻至4°（緊急情況）
   - 調整軌道相位分散參數，增加時空互補性
   
2. **OneWeb覆蓋率不足（<95%）**: 
   - 增加OneWeb候選衛星數量（60→80顆）
   - 檢查10°仰角門檻是否過於嚴格
   - 優化OneWeb軌道平面選擇策略
   
3. **覆蓋間隙過長（>2分鐘）**: 
   - 強化軌道相位錯開算法
   - 增加覆蓋緩衝衛星（每個星座+20%）  
   - 實施動態候補衛星策略
   
4. **綜合覆蓋率不達標**: 
   - 同時增加兩個星座的衛星數量
   - 重新計算最佳軌道週期時間窗口
   - 檢查TLE數據的時效性和準確性
   
5. **時間序列數據缺失**: 確認Stage 5數據完整性
6. **相位多樣性不足**: 優化選擇算法、增加RAAN分散

### 📊 95%+覆蓋率關鍵指標總覽
- **Starlink覆蓋率**: ≥95% 時間保持10+顆可見（5°仰角）  
- **OneWeb覆蓋率**: ≥95% 時間保持3+顆可見（10°仰角）
- **綜合覆蓋率**: ≥95% 時間同時滿足兩個星座要求
- **最大間隙**: ≤2分鐘連續覆蓋不足時段
- **時空錯置**: 軌道相位均勻分散，相位多樣性≥0.7
- **切換保證**: 任何時刻有充足候選衛星

## 📖 **學術標準參考文獻**

### 軌道動力學理論基礎
- **Kepler's Laws**: 開普勒三定律 - 軌道週期和半長軸關係
- **Vallado, D.A.**: "Fundamentals of Astrodynamics and Applications" - SGP4/SDP4軌道模型
- **NASA/TP-2010-216239**: "SGP4 Orbit Determination" - 軌道計算精度標準
- **Curtis, H.D.**: "Orbital Mechanics for Engineering Students" - 軌道力學工程應用

### 衛星覆蓋分析理論
- **Satellite Coverage Analysis**: Walker星座和軌道相位分佈理論
- **Spherical Trigonometry**: 球面三角學在衛星可見性計算中的應用
- **Orbital Geometry**: 軌道幾何學和地面軌跡分析
- **ITU-R S.1257**: 衛星系統覆蓋分析標準

### 3GPP換手標準
- **3GPP TS 38.331**: "RRC Protocol specification" - A4/A5/D2事件標準
- **3GPP TS 38.821**: "NTN Solutions" - 非地面網路換手需求
- **3GPP TR 38.811**: "NTN Study" - LEO衛星換手研究報告

### 系統可靠性理論
- **Reliability Engineering**: 系統可靠性分析方法
- **Fault Tolerant Systems**: 容錯系統設計原理
- **Mission Critical Systems**: 關鍵任務系統可用性要求
- **Statistical Analysis**: 覆蓋統計分析和置信區間計算

### 軌道預測精度標準
- **USSTRATCOM**: 軌道預測精度標準和不確定度分析
- **SGP4 Accuracy Analysis**: SGP4模型精度評估研究
- **Orbital Perturbations**: 軌道攝動對預測精度的影響
- **Monte Carlo Methods**: 軌道不確定度統計分析方法

### 🎯 **基於學術標準的最終驗證要求**

執行完Stage 6驗證後，系統應達到以下**基於科學分析**的標準：
- ✅ **軌道動力學覆蓋保證**: 基於開普勒定律和軌道週期分析的連續覆蓋
- ✅ **幾何可見性驗證**: 基於球面三角學的精確可見性計算  
- ✅ **統計可靠性達標**: 基於系統可靠性理論的覆蓋統計分析
- ✅ **軌道相位優化**: 基於Walker星座理論的相位分佈優化
- ✅ **物理間隙控制**: 基於3GPP換手時間要求的最大間隙限制
- ✅ **預測精度保證**: 考慮SGP4精度限制的時間窗口設計

---

**上一階段**: [階段五：數據整合](./stage5-integration.md)  
**目標狀態**: 建立可保證完整軌道週期覆蓋的時空錯置動態衛星池

---

🎯 **階段六終極目標**：實現「95%以上時間 NTPU 上空都有 10+ 顆 Starlink（5°仰角）+ 3+ 顆 OneWeb（10°仰角）可見衛星」的95%+覆蓋率保證，最大間隙≤2分鐘，為 LEO 衛星換手研究提供連續穩定的實驗環境。

**📊 量化成功標準**：
- Starlink覆蓋率 ≥ 95%（228/240個時間點滿足≥10顆可見）
- OneWeb覆蓋率 ≥ 95%（228/240個時間點滿足≥3顆可見）
- 綜合覆蓋率 ≥ 95%（兩個星座同時滿足要求）
- 最大覆蓋間隙 ≤ 2分鐘（4個連續採樣點）