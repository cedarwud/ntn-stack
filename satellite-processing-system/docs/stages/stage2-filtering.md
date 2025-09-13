# 🎯 階段二：地理可見性篩選

[🔄 返回數據流程導航](../README.md) > 階段二

## 📖 階段概述

**目標**：從 8,791 顆衛星中篩選出對NTPU觀測點地理可見的候選衛星  
**輸入**：階段一純ECI軌道數據（記憶體傳遞 + `/app/data/tle_orbital_calculation_output.json`）  
**輸出**：篩選結果保存至 `/app/data/satellite_visibility_filtered_output.json` + 記憶體傳遞  
**核心工作**：
1. 從ECI座標計算相對NTPU觀測點的仰角、方位角、距離
2. 判斷衛星可見性（`is_visible`）並應用ITU-R標準篩選
3. 篩選掉地理不可見或不符合標準的衛星
**實際結果**：約500-1000顆符合可見性標準的候選衛星  
**篩選邏輯**：嚴格地理可見性篩選 + ITU-R標準檢查  
**處理時間**：約 20-25 秒

### 🗂️ 統一輸出目錄結構

六階段處理系統採用統一的輸出目錄結構：

```bash
/app/data/                                    # 統一數據目錄
├── stage1_orbital_calculation_output.json   # 階段一：軌道計算
├── satellite_visibility_filtered_output.json # 階段二：地理可見性篩選 ⭐  
├── stage3_signal_analysis_output.json       # 階段三：信號分析
├── stage4_timeseries_preprocessing_output.json  # 階段四：時間序列
├── stage5_data_integration_output.json      # 階段五：數據整合
├── stage6_dynamic_pool_output.json          # 階段六：動態池規劃
└── validation_snapshots/                    # 驗證快照目錄
    ├── stage1_validation.json
    ├── stage2_validation.json               # 階段二驗證快照
    └── ...
```

**命名規則**：
- 所有階段輸出使用 `stage{N}_` 前綴
- 統一保存至 `/app/data/` 目錄（容器內）
- 驗證快照保存至 `validation_snapshots/` 子目錄
- 無額外子目錄，保持扁平結構

### 🎯 @doc/todo.md 對應實現
本階段實現以下核心需求：
- ✅ **觀測點設定**: 設定 NTPU 觀測點座標 (24°56'39"N 121°22'17"E)
- ✅ **ECI轉換**: 將階段一的ECI座標轉換為觀測點相對座標（仰角、方位角）
- ✅ **可見性判斷**: 計算每個時間點的衛星可見性（`is_visible`）
- ✅ **ITU-R標準篩選**: 應用Starlink 5°/OneWeb 10°仰角標準
- 🔧 **地理篩選**: 篩選掉對NTPU觀測點不可見或不符合標準的衛星
- 🎯 **候選準備**: 為後續階段提供真正可見的候選衛星池

### 🚀 v1.1 過度篩選修復版本

- **🔧 核心修復**：✅ **解決過度篩選問題**
  - **可見性時間要求**：Starlink從 5.0→1.0 分鐘，OneWeb從 2.0→0.5 分鐘
  - **品質點要求**：從 10→3 個最佳仰角點 (大幅放寬品質要求)
  - **動態門檻**：使用統一仰角管理器的實際門檻值
  - **數據完整性**：確保足夠衛星流向後續階段處理

### 🚀 v3.0 記憶體傳遞模式

- **問題解決**：避免生成 2.4GB 篩選結果檔案
- **傳遞方式**：直接將篩選結果在記憶體中傳遞給階段三
- **效能提升**：消除大檔案I/O，減少磁碟空間使用

## 🌍 地理可見性篩選演算法

### 地理可見性篩選流程

1. **星座分組處理**
   - 分離 Starlink 和 OneWeb 數據
   - 應用星座特定的篩選參數

2. **地理可見性篩選**
   - Starlink: 仰角 ≥5°, 可見時間 ≥1.0分鐘
   - OneWeb: 仰角 ≥10°, 可見時間 ≥0.5分鐘
   - 基於階段一提供的 position_timeseries 數據
   - 篩選方式：pure_geographic_visibility_no_quantity_limits

**篩選結果特點：**
- 基於實際SGP4軌道計算結果
- 無人為數量限制，純基於地理可見性條件
- 保留率依實際軌道條件動態變化

## 🏗️ 核心處理器架構

### 主要實現位置
```bash
# 地理可見性篩選處理器
/netstack/src/stages/satellite_visibility_filter_processor.py
├── SatelliteVisibilityFilterProcessor.process_intelligent_filtering()    # 主篩選邏輯
├── SatelliteVisibilityFilterProcessor.load_orbital_calculation_output()  # 載入軌道數據
└── SatelliteVisibilityFilterProcessor._simple_filtering()                # 地理可見性篩選執行

# 統一智能篩選系統
/netstack/src/services/satellite/intelligent_filtering/unified_intelligent_filter.py
├── UnifiedIntelligentFilter.execute_f2_filtering_workflow()  # F2篩選流程
├── UnifiedIntelligentFilter.geographical_relevance_filter() # 地理相關性篩選
└── UnifiedIntelligentFilter.handover_suitability_scoring()  # 換手適用性評分
/netstack/config/satellite_data_pool_builder.py        # 基礎衛星池建構
```

## 🚨 **學術級篩選標準遵循** (Grade A/B 等級)

### 🟢 **Grade A 強制要求：真實物理參數**

#### 可見性準則 (基於ITU-R標準)
- **仰角門檻**：遵循 [衛星換手仰角門檻標準](../satellite_handover_standards.md)
  - Starlink: 5° (最低服務門檻)
  - OneWeb: 10° (標準服務門檻)  
  - 依據：ITU-R P.618-13 地球-空間路徑衰減標準
- **可見時間要求**：基於軌道動力學計算
  - 最低可見時間：根據實際軌道週期和幾何條件計算
  - 絕不使用任意假設的"15分鐘"等固定值

#### 🟡 **Grade B 可接受：標準模型計算**

#### 信號傳播物理模型 (替代"預估")
- **自由空間路徑損耗**：PL(dB) = 20log₁₀(4πd/λ)
  - d = 精確衛星-地面距離 (基於SGP4計算)
  - λ = 載波波長 (依實際頻段：Ku/Ka頻段)
  - 絕不使用固定的"-110 dBm門檻"等任意值
- **都卜勒頻移計算**：Δf = (v_rel × f_c) / c
  - v_rel = 相對速度向量投影 (基於軌道計算)
  - f_c = 實際載波頻率 (非假設值)

#### 🔴 **Grade C 嚴格禁止項目**
- **❌ 任意RSRP門檻值**：如"-110 dBm"等沒有物理依據的固定值
- **❌ 人為距離限制**：如"2000 km"等非基於物理原理的限制
- **❌ 固定都卜勒限制**：如"±40 kHz"等未經計算驗證的限制
- **❌ 任意負載平衡比例**：如"80%/20%"等非基於實際覆蓋需求的分配
- **❌ 假設的服務窗口數量**：如"至少3個"等未經驗證的要求

### 🎯 **替代方案：基於物理原理的篩選**

#### 真實可見性計算
```python
# ✅ 正確：基於SGP4和球面三角學
def calculate_visibility(satellite_position_eci, observer_position_ecef, time):
    elevation = calculate_elevation_angle(satellite_position_eci, observer_position_ecef)
    return elevation >= threshold_from_itu_standard
    
# ❌ 錯誤：使用假設參數
def assume_visibility_threshold():
    return rsrp > -110  # 任意門檻值
```

#### 動態覆蓋需求分析
```python
# ✅ 正確：基於實際覆蓋需求
coverage_requirements = analyze_coverage_gaps(observer_location, time_window)
satellite_selection = select_by_coverage_contribution(candidates, coverage_requirements)

# ❌ 錯誤：固定比例分配
target_ratios = {'starlink': 0.80, 'oneweb': 0.20}  # 任意比例
```

## 🚨 強制運行時檢查 (新增)

**2025-09-09 重大強化**: 新增階段二專門的運行時架構完整性檢查維度。

### 🔴 零容忍運行時檢查 (任何失敗都會停止執行)

#### 1. 篩選引擎類型強制檢查
```python
# 🚨 嚴格檢查實際使用的篩選引擎類型
assert isinstance(filter_engine, UnifiedIntelligentFilter), f"錯誤篩選引擎: {type(filter_engine)}"
# 原因: 確保使用統一智能篩選系統，而非簡化篩選器
# 影響: 錯誤引擎可能導致篩選邏輯不完整或使用錯誤參數
```

#### 2. 輸入數據完整性檢查  
```python
# 🚨 強制檢查輸入衛星數據完整性
assert input_satellites_count > 8600, f"輸入衛星數量不足: {input_satellites_count}"
assert 'position_timeseries' in input_data[0], "輸入數據缺少軌道時間序列"
# 星座特定時間序列長度檢查 (修正版)
constellation = input_data[0].get('constellation', '').lower() 
expected_points = 192 if constellation == 'starlink' else 218 if constellation == 'oneweb' else None
assert expected_points is not None, f"未知星座: {constellation}"
assert len(input_data[0]['position_timeseries']) == expected_points, f"時間序列長度不符合階段一輸出規格: {len(input_data[0]['position_timeseries'])} vs {expected_points} ({constellation})"
# 原因: 確保階段一的數據完整性已正確傳遞
# 影響: 不完整的輸入會導致篩選結果錯誤或偏差
```

#### 3. 篩選邏輯流程檢查
```python
# 🚨 檢查篩選流程的完整執行
filtering_steps = ['constellation_separation', 'geographical_relevance', 'handover_suitability']
for step in filtering_steps:
    assert step in executed_steps, f"篩選步驟 {step} 未執行"
assert filtering_mode == "pure_geographic_visibility", "篩選模式錯誤"
# 原因: 確保完整的三步驟篩選流程都正確執行
# 影響: 跳過步驟會導致篩選不完整或結果不準確
```

#### 4. 仰角門檻合規檢查
```python
# 🚨 強制檢查仰角門檻符合ITU-R標準
constellation_thresholds = config.get_elevation_thresholds()
assert constellation_thresholds['starlink'] == 5.0, f"Starlink仰角門檻錯誤: {constellation_thresholds['starlink']}"
assert constellation_thresholds['oneweb'] == 10.0, f"OneWeb仰角門檻錯誤: {constellation_thresholds['oneweb']}"
# 原因: 確保使用符合ITU-R P.618標準的仰角門檻
# 影響: 錯誤門檻會影響篩選結果和後續階段的准確性
```

#### 5. 輸出數據結構完整性檢查
```python
# 🚨 強制檢查輸出數據結構完整性
assert 'filtered_satellites' in output_data, "缺少篩選結果"
assert 'starlink' in output_data['filtered_satellites'], "缺少Starlink篩選結果"
assert 'oneweb' in output_data['filtered_satellites'], "缺少OneWeb篩選結果"
# 階段二是真正的篩選階段，應該篩掉大部分不可見的衛星
assert output_data['metadata']['filtering_rate'] >= 0.70, "篩選率過低，可能篩選不足"
assert output_data['metadata']['filtering_rate'] <= 0.95, "篩選率過高，可能篩選過於嚴格"
```

#### 6. 無簡化篩選零容忍檢查
```python
# 🚨 禁止任何形式的簡化篩選算法
forbidden_filtering_modes = [
    "simplified_filter", "basic_elevation_only", "mock_filtering", 
    "random_sampling", "fixed_percentage", "estimated_visibility"
]
for mode in forbidden_filtering_modes:
    assert mode not in str(filter_engine.__class__).lower(), \
        f"檢測到禁用的簡化篩選: {mode}"
```

### 📋 Runtime Check Integration Points

**檢查時機**: 
- **初始化時**: 驗證篩選引擎類型和配置參數
- **輸入處理時**: 檢查階段一數據完整性和格式符合性
- **篩選過程中**: 監控篩選步驟執行和仰角門檻應用
- **輸出前**: 嚴格檢查篩選結果結構和數據完整性

**失敗處理**:
- **立即停止**: 任何runtime check失敗都會立即終止執行
- **數據回溯**: 檢查階段一輸出是否存在問題
- **配置檢查**: 驗證篩選參數配置是否正確
- **無降級處理**: 絕不允許使用簡化篩選算法

### 🛡️ 實施要求

- **跨階段一致性**: 確保與階段一輸出數據格式100%兼容
- **ITU-R標準合規**: 強制執行國際標準的仰角門檻要求  
- **篩選邏輯完整性**: 確保三步驟篩選流程完整執行
- **性能影響控制**: 運行時檢查額外時間開銷 <3%

## ⚡ 性能最佳化

### 記憶體最佳化
- **批次處理**：每次處理500顆衛星
- **記憶體回收**：及時清理中間結果
- **數據壓縮**：使用高效的數據結構

### 演算法最佳化
- **預先排序**：按可見性機率排序
- **早期終止**：達到目標數量即停止
- **並行處理**：支援多執行緒計算

## 📖 **學術標準參考文獻**

### 衛星可見性標準
- **ITU-R P.618-13**: "Propagation data and prediction methods for the design of Earth-space telecommunication systems"
- **ITU-R S.1257-1**: "Sharing criteria for VSAT systems operating in the 14-14.5 GHz band"
- **3GPP TS 38.821**: "Solutions for NR to support non-terrestrial networks (NTN)"

### 仰角門檻標準
- **ITU-R P.618**: 最低仰角建議 (5°-10°)
- **ITU-R P.840**: 雲和霧的衰減模型
- **本項目標準**: [衛星換手仰角門檻標準](../satellite_handover_standards.md)

### 信號傳播模型
- **Friis傳輸公式**: 自由空間路徑損耗計算
- **ITU-R P.676**: 大氣氣體衰減模型  
- **ITU-R P.837**: 降雨衰減統計模型

### 軌道幾何計算
- **球面三角學**: 大圓距離和角度計算
- **WGS84座標系統**: 地心地固座標轉換
- **SGP4軌道模型**: 衛星位置精確計算

### 都卜勒頻移計算
- **相對論都卜勒效應**: f' = f(1 + v·r̂/c)
- **衛星通信系統**: 頻率規劃和補償技術
- **3GPP NTN標準**: 都卜勒補償要求

## 🧪 TDD整合自動化測試 (Phase 5.0 新增)

### 🎯 自動觸發機制

**觸發時機**: 階段二篩選處理完成並生成驗證快照後自動觸發

```python
def execute(self, input_data):
    # 原有的篩選處理流程
    # 1. 星座分離篩選
    # 2. 地理相關性篩選  
    # 3. 換手適用性評分
    # 4. 統計數據收集
    # 5. 數據結構驗證
    # 6. 記憶體傳遞準備
    # 7. 性能指標計算
    
    # 8. ✅ 生成驗證快照 (原有)
    snapshot_success = self.save_validation_snapshot(results)
    
    # 9. 🆕 後置鉤子：自動觸發TDD測試
    if snapshot_success and self.tdd_config.get("enabled", True):
        self._trigger_tdd_tests_after_snapshot()
        
    return filtered_results
```

### 🔧 階段二專用測試配置

#### **基礎測試類型**
- **回歸測試**: 與歷史篩選結果比較，檢測篩選邏輯變化
- **合規測試**: 驗證ITU-R P.618標準符合性 (Grade A 要求)
- **整合測試**: 檢查階段一數據接收和階段三數據傳遞完整性 (開發環境)

#### **階段特定驗證項目**
```yaml
stage2_filtering_tests:
  # 地理可見性篩選驗證
  geographic_visibility:
    - elevation_threshold_compliance      # 仰角門檻合規性檢查
    - visibility_time_requirements       # 可見時間要求驗證
    - observer_coordinate_accuracy       # 觀測點座標精度驗證
    
  # 篩選引擎完整性驗證  
  filtering_engine_integrity:
    - unified_intelligent_filter_usage   # 確保使用統一智能篩選系統
    - three_step_filtering_execution     # 三步驟篩選流程完整性
    - constellation_separation_accuracy  # 星座分離準確性
    
  # 數據流完整性驗證
  data_flow_integrity:
    - input_data_completeness           # 輸入數據完整性 (8,000+顆衛星)
    - position_timeseries_preservation  # 位置時間序列保留驗證
    - memory_transfer_validation        # 記憶體傳遞模式驗證
    
  # 學術標準合規驗證 (Grade A)
  academic_compliance:
    - itu_r_standard_enforcement        # ITU-R P.618標準強制執行
    - physical_parameter_verification   # 物理參數真實性驗證
    - forbidden_simplification_check   # 禁止簡化算法檢查
```

### 📊 性能回歸檢測

#### **關鍵性能基準 (Stage 2 特定)**
```yaml
performance_baselines:
  processing_time:
    target: 25_seconds        # 目標處理時間
    warning: 35_seconds       # 警告門檻
    critical: 50_seconds      # 關鍵門檻
    
  memory_usage:
    target: 300_MB           # 目標記憶體使用
    warning: 500_MB          # 警告門檻
    critical: 800_MB         # 關鍵門檻
    
  filtering_efficiency:
    expected_retention_rate: 0.10_to_0.15    # 預期保留率 10-15%
    min_acceptable_rate: 0.05                # 最低可接受保留率
    max_acceptable_rate: 0.25                # 最高可接受保留率
    
  data_quality:
    min_starlink_satellites: 400             # Starlink最低數量
    min_oneweb_satellites: 150               # OneWeb最低數量
    constellation_balance_tolerance: 0.2     # 星座平衡容差
```

#### **回歸檢測指標**
- **篩選率一致性**: 與歷史基準比較，容差範圍 ±5%
- **星座分佈穩定性**: Starlink/OneWeb比例變化檢測
- **地理覆蓋連續性**: NTPU觀測點覆蓋衛星數量穩定性
- **數據完整性保持**: 位置時間序列數據保留完整性

### 🚨 關鍵錯誤檢測

#### **零容忍錯誤類型 (立即失敗)**
```python
critical_error_checks = {
    "篩選引擎類型錯誤": {
        "check": "isinstance(filter_engine, UnifiedIntelligentFilter)",
        "impact": "可能使用簡化篩選算法，違反學術標準"
    },
    "輸入數據不完整": {
        "check": "input_satellites_count > 8600",
        "impact": "階段一數據傳遞問題，影響後續所有處理"
    },
    "仰角門檻不合規": {
        "check": "starlink_threshold == 5.0 and oneweb_threshold == 10.0",
        "impact": "違反ITU-R P.618標準，影響論文可信度"
    },
    "篩選流程不完整": {
        "check": "all_filtering_steps_executed",
        "impact": "篩選邏輯缺失，可能產生錯誤結果"
    }
}
```

#### **警告級別問題 (記錄但繼續)**
- **篩選數量異常**: 篩選結果數量超出預期範圍 (但未達危險級別)
- **處理時間超出預期**: 超出目標時間但在可接受範圍內
- **記憶體使用偏高**: 記憶體使用超出目標但未達限制

### 🔄 測試執行模式

#### **同步執行模式 (開發環境)**
- 篩選處理 → 驗證快照生成 → TDD測試執行 → 結果回報
- 總執行時間: ~30-40秒 (包含測試時間)
- 立即錯誤反饋，便於開發調試

#### **異步執行模式 (生產環境)**
- 篩選處理 → 驗證快照生成 → 返回結果
- TDD測試在背景異步執行，不影響主要數據流
- 測試結果通過警報系統或日誌回報

#### **混合執行模式 (測試環境)**
- 關鍵檢查同步執行 (零容忍錯誤)
- 性能檢測異步執行 (不影響主流程)
- 平衡反饋速度和系統性能

### 🎯 測試覆蓋目標

#### **功能覆蓋率**: ≥95%
- 所有篩選邏輯分支覆蓋
- 錯誤處理路徑覆蓋  
- 星座特定參數覆蓋

#### **數據覆蓋率**: ≥90%
- 不同衛星數量情境 (7,000-9,000顆)
- 不同星座比例情境 (Starlink/OneWeb變化)
- 不同可見性條件情境 (時間、地理位置)

#### **性能覆蓋率**: ≥85%
- 正常負載性能基準
- 高負載壓力測試
- 記憶體限制情境測試

### 📈 測試結果整合

#### **驗證快照增強 (Stage 2 特定)**
```json
{
  "stage": "stage2_intelligent_filtering",
  "tdd_integration": {
    "enabled": true,
    "execution_mode": "sync|async|hybrid",
    "test_results": {
      "total_tests": 15,
      "passed_tests": 15, 
      "failed_tests": 0,
      "critical_failures": [],
      "performance_regressions": []
    },
    "filtering_quality_metrics": {
      "retention_rate": 0.12,
      "starlink_count": 650,
      "oneweb_count": 180,
      "geographic_coverage_score": 0.92
    }
  }
}
```

#### **階段三數據傳遞驗證**
- **記憶體模式驗證**: 確保篩選結果正確傳遞給階段三
- **數據結構一致性**: 保持與階段三期望的輸入格式一致
- **數據完整性保證**: 所有必要字段和屬性完整保留

### 🔍 故障診斷整合

#### **自動診斷觸發條件**
- TDD測試失敗率 > 10%
- 關鍵性能指標偏離基準 > 20%
- 連續3次測試出現同類型錯誤

#### **診斷數據收集**
- 階段一輸出數據質量檢查
- 篩選引擎配置驗證
- 系統資源使用狀況
- 歷史性能趨勢分析

---

## 📊 篩選結果統計

### 修正後的預期輸出分佈（真正篩選）
```
總計：~800-1200顆衛星 (從8,837顆中篩選出地理可見的衛星)
├── Starlink: ~600-900顆 (通過5°仰角 + 1分鐘可見時間標準)
│   ├── 高仰角 (>30°): ~200顆
│   ├── 中仰角 (15-30°): ~300顆
│   └── 低仰角 (5-15°): ~200顆
└── OneWeb: ~200-300顆 (通過10°仰角 + 0.5分鐘可見時間標準)
    ├── 高仰角 (>30°): ~80顆
    ├── 中仰角 (15-30°): ~120顆
    └── 低仰角 (10-15°): ~100顆
```

**重要說明**: 階段二是真正的篩選階段，將從所有8,837顆衛星中篩選出對NTPU觀測點地理可見且符合ITU-R標準的候選衛星。預期篩選率約80-90%（大部分衛星不可見）。

## 🔧 配置參數

```python
# 篩選參數 (基於LEO衛星物理特性修正)
FILTERING_CONFIG = {
    'starlink': {
        'min_elevation_deg': 5.0,
        'min_visible_time_min': 1.0,    # 修正：LEO衛星單次過境約8-12分鐘，1分鐘是合理門檻
        'target_count': 450
    },
    'oneweb': {
        'min_elevation_deg': 10.0,
        'min_visible_time_min': 0.5,    # 修正：MEO衛星可見時間較長，0.5分鐘是合理門檻
        'target_count': 113
    }
}
```

## 🚨 故障排除

### 常見問題

1. **篩選數量不足**
   - 檢查：降低篩選門檻
   - 解決：調整 min_elevation_deg 或 min_visible_time_min

2. **星座比例失衡**
   - 檢查：各星座原始數據量
   - 解決：調整 target_count 比例

3. **記憶體使用過高**
   - 檢查：batch_size 設定
   - 解決：減少批次處理大小

### 診斷指令

```bash
# 檢查篩選統計
python -c "
from src.services.satellite.preprocessing.satellite_selector import *
print('篩選器模組載入成功')
"

# 驗證記憶體使用
top -p $(pgrep -f satellite_orbit_preprocessor) -n 1
```

## ✅ 階段驗證標準

### 🎯 學術級驗證框架 (8個核心驗證)

#### **基礎驗證 (目前已實現的3個)**
1. **`output_structure_check`** - 數據結構完整性 (data, metadata, statistics)
2. **`filtering_engine_check`** - 篩選引擎類型驗證 (UnifiedIntelligentFilter)  
3. **`itu_r_compliance_check`** - ITU-R合規模式檢查

#### **增強驗證 (新增5個達到學術標準)**
4. **`filtering_rate_reasonableness_check`** - 篩選率合理性驗證 (5%-50%)
5. **`constellation_threshold_compliance_check`** - 星座仰角門檻正確性
6. **`satellite_count_consistency_check`** - 輸入輸出數量一致性
7. **`observer_coordinate_precision_check`** - 觀測點座標精度驗證
8. **`timeseries_continuity_check`** - 位置時間戳連續性檢查

### 🎯 Stage 2 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] 接收Stage 1數據完整性
  - 輸入衛星總數 > 8,000顆
  - Starlink和OneWeb數據都存在
  - 每顆衛星包含完整軌道數據
- [ ] 記憶體傳遞模式檢查
  - 確認使用記憶體傳遞（v3.0模式）
  - 無大型中間文件生成

#### 2. **篩選過程驗證**
- [ ] **地理相關性篩選**
  ```
  NTPU座標: 24°56'39"N 121°22'17"E
  仰角閾值:
  - Starlink: 5度（用戶需求）
  - OneWeb: 10度（用戶需求）
  篩選保留率: 10-15%
  ```
- [ ] **可見性要求**
  - 最低可見時間：Starlink ≥ 1.0分鐘，OneWeb ≥ 0.5分鐘
  - 品質點數量：≥ 3個最佳仰角點
- [ ] **篩選管線完整性**
  1. 星座分離篩選 ✓
  2. 地理相關性篩選 ✓
  3. 換手適用性評分 ✓

#### 3. **輸出驗證**
- [ ] **篩選結果數量**
  ```
  實際結果:
  - Starlink: 2,899顆（約35.6%保留率）
  - OneWeb: 202顆（約31.0%保留率）
  - 總計: 3,101顆（35.3%整體保留率）
  ```
- [ ] **數據結構驗證**
  ```json
  {
    "metadata": {
      "stage": "stage2_intelligent_filtering", 
      "total_input_satellites": 8837,
      "total_filtered_satellites": 900,
      "filtering_rate": 0.898  // 89.8%被篩掉，10.2%通過
    },
    "filtered_satellites": {
      "starlink": [...],  // 包含篩選後的衛星
      "oneweb": [...]     // 包含篩選後的衛星
    }
  }
  ```
- [ ] **衛星數據完整性**
  - 每顆衛星保留完整的 `position_timeseries`
  - 可見性窗口數據正確
  - 信號預估值合理（RSRP > -120 dBm）

#### 4. **性能指標**
- [ ] 處理時間 < 2分鐘
- [ ] 記憶體使用 < 500MB
- [ ] 篩選率在合理範圍（70-95%，大部分衛星不可見被篩掉）

#### 5. **學術級驗證快照標準**

**驗證快照必須包含8個核心檢查**:
```json
{
  "validation": {
    "passed": true,
    "total_checks": 8,
    "passed_checks": 8,
    "failed_checks": 0,
    "critical_checks": [],
    "all_checks": {
      "output_structure_check": true,
      "filtering_engine_check": true, 
      "itu_r_compliance_check": true,
      "filtering_rate_reasonableness_check": true,
      "constellation_threshold_compliance_check": true,
      "satellite_count_consistency_check": true,
      "observer_coordinate_precision_check": true,
      "timeseries_continuity_check": true
    }
  }
}
```

#### 6. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import sys

# 載入驗證快照
try:
    with open('/app/data/validation_snapshots/stage2_validation.json', 'r') as f:
        validation_data = json.load(f)
except:
    print('❌ 無法載入驗證快照')
    sys.exit(1)

validation = validation_data.get('validation', {})

# 檢查是否有8個驗證
required_checks = {
    'output_structure_check': '數據結構完整性',
    'filtering_engine_check': '篩選引擎類型驗證',
    'itu_r_compliance_check': 'ITU-R合規模式檢查',
    'filtering_rate_reasonableness_check': '篩選率合理性驗證',
    'constellation_threshold_compliance_check': '星座仰角門檻正確性',
    'satellite_count_consistency_check': '輸入輸出數量一致性',
    'observer_coordinate_precision_check': '觀測點座標精度驗證',
    'timeseries_continuity_check': '位置時間戳連續性檢查'
}

all_checks = validation.get('all_checks', {})
total_checks = validation.get('total_checks', 0)
passed_checks = validation.get('passed_checks', 0)

print('📊 Stage 2 學術級驗證結果:')
print(f'  驗證總數: {total_checks}/8 (學術標準要求8個)')
print(f'  通過驗證: {passed_checks}/{total_checks}')
print('\\n各項驗證結果:')

missing_checks = []
for check_name, description in required_checks.items():
    if check_name in all_checks:
        status = '✅' if all_checks[check_name] else '❌'
        print(f'  {status} {description}')
    else:
        missing_checks.append(f'{check_name} ({description})')
        print(f'  ⚠️ 缺失: {description}')

if missing_checks:
    print(f'\\n❌ 缺少 {len(missing_checks)} 個必要驗證:')
    for missing in missing_checks:
        print(f'  - {missing}')
    print('\\n系統需要升級驗證框架以符合學術標準')
    sys.exit(1)

if total_checks == 8 and passed_checks == 8:
    print('\\n✅ Stage 2 學術級驗證通過！符合論文發表標準')
else:
    print(f'\\n❌ 驗證不完整或有失敗項目 ({passed_checks}/{total_checks})')
    sys.exit(1)
"
```

### 🚨 驗證失敗處理
1. **篩選數量過少**
   - 降低仰角閾值要求
   - 減少最低可見時間要求
   - 檢查地理位置設定是否正確
2. **篩選數量過多**
   - 提高篩選標準
   - 增加品質要求
3. **時間序列缺失**
   - 確認Stage 1輸出包含完整數據
   - 檢查記憶體傳遞是否正常
4. **星座比例失衡**
   - 調整各星座的篩選參數
   - 檢查原始數據分佈

### 📊 關鍵指標
- **篩選效率**: 保留10-15%的高品質候選衛星
- **地理覆蓋**: 確保NTPU上空有足夠可見衛星
- **數據完整**: 保留完整軌道數據供後續處理

---
**上一階段**: [階段一：TLE載入](./stage1-tle-loading.md)  
**下一階段**: [階段三：信號分析](./stage3-signal.md)  
**相關文檔**: [智能篩選演算法詳解](../algorithms_implementation.md#智能篩選)
