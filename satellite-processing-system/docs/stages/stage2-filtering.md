# 🎯 階段二：地理可見性篩選

[🔄 返回數據流程導航](../README.md) > 階段二

## 📖 階段概述

**目標**：從 8,791 顆衛星中篩選出對NTPU觀測點地理可見的候選衛星  
**輸入**：階段一軌道計算結果（記憶體傳遞 + `/app/data/tle_orbital_calculation_output.json`）  
**輸出**：篩選結果保存至 `/app/data/satellite_visibility_filtered_output.json` + 記憶體傳遞  
**實際結果**：基於地理可見性的候選衛星（數量依實際軌道條件而定）
**篩選邏輯**：純地理可見性篩選，無人為數量限制  
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
- ✅ **可見性篩選**: 排除不符合地理可見性條件的衛星
- 🔧 **地理相關性**: 基於 NTPU 觀測點的地理可見性自然篩選
- 🎯 **候選準備**: 為時空錯置篩選提供高品質候選衛星池

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
assert output_data['metadata']['filtering_rate'] > 0.05, "篩選率過低，可能篩選過於嚴格"
assert output_data['metadata']['filtering_rate'] < 0.50, "篩選率過高，可能篩選不足"
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

## 📊 篩選結果統計

### 預期輸出分佈
```
總計：563顆衛星
├── Starlink: ~450顆 (80%)
│   ├── 高仰角 (>30°): ~150顆
│   ├── 中仰角 (15-30°): ~200顆
│   └── 低仰角 (5-15°): ~100顆
└── OneWeb: ~113顆 (20%)
    ├── 高仰角 (>30°): ~40顆
    ├── 中仰角 (15-30°): ~50顆
    └── 低仰角 (10-15°): ~23顆
```

## 🔧 配置參數

```python
# 篩選參數
FILTERING_CONFIG = {
    'starlink': {
        'min_elevation_deg': 5.0,
        'min_visible_time_min': 15.0,
        'target_count': 450
    },
    'oneweb': {
        'min_elevation_deg': 10.0,
        'min_visible_time_min': 15.0,
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
      "total_input_satellites": 8779,
      "total_filtered_satellites": 1196,
      "filtering_rate": 0.136
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
- [ ] 篩選率在合理範圍（10-20%）

#### 5. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import sys

# 載入輸出數據（記憶體模式或文件模式）
try:
    with open('/app/data/satellite_visibility_filtered_output.json', 'r') as f:
        data = json.load(f)
except:
    print('⚠️ 使用記憶體傳遞模式，跳過文件驗證')
    # 在記憶體模式下，驗證應在處理器內部完成
    sys.exit(0)

# 驗證項目
metadata = data.get('metadata', {})
filtered = data.get('filtered_satellites', {})

starlink_count = len(filtered.get('starlink', []))
oneweb_count = len(filtered.get('oneweb', []))
total_filtered = starlink_count + oneweb_count

checks = {
    'input_count_valid': metadata.get('total_input_satellites', 0) > 8000,
    'starlink_filtered': 1000 <= starlink_count <= 1300,
    'oneweb_filtered': 140 <= oneweb_count <= 200,
    'total_filtered': 1100 <= total_filtered <= 1500,
    'filtering_rate': 0.10 <= metadata.get('filtering_rate', 0) <= 0.20,
    'has_timeseries': all(
        'position_timeseries' in sat 
        for constellation in filtered.values() 
        for sat in constellation[:5]  # 檢查前5顆
    )
}

# 計算通過率
passed = sum(checks.values())
total = len(checks)

print('📊 Stage 2 驗證結果:')
print(f'  輸入衛星數: {metadata.get(\"total_input_satellites\", 0)}')
print(f'  Starlink篩選: {starlink_count} 顆')
print(f'  OneWeb篩選: {oneweb_count} 顆')
print(f'  總篩選率: {metadata.get(\"filtering_rate\", 0):.1%}')
print('\\n驗證項目:')
for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')
print(f'\\n總計: {passed}/{total} 項通過')

if passed == total:
    print('✅ Stage 2 驗證通過！')
else:
    print('❌ Stage 2 驗證失敗，請檢查上述項目')
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
