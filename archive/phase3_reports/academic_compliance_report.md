# 學術標準術語合規檢查報告
==================================================

## 📊 檢查摘要
- 處理文件數: 10
- 發現違規數: 136
- 已修正數量: 8
- 需手動處理: 120

## 🚨 發現的違規項目

### 📄 netstack/src/stages/timeseries_preprocessing_processor.py

#### 🟡 中等優先級違規
**行 42**: `預設`
   上下文: self.sample_mode = False  # 預設為全量模式

**行 829**: `簡化`
   上下文: # 3. 處理簡化時間序列（來自原始 timeseries）

### 📄 netstack/src/stages/orbit_calculation_coordinator.py

#### 🟡 中等優先級違規
**行 340**: `simplified`
   上下文: "simplified_algorithms_used": False,

### 📄 netstack/src/stages/signal_analysis_processor.py

#### 🔴 高優先級違規
**行 446**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 粗略估計：假設發射功率為40dBm，接收天線增益為0dBi

**行 449**: `estimated_rsrp`
   建議替換: computed_rsrp
   上下文: estimated_rsrp = estimated_eirp_dbm - theoretical_path_loss_db

**行 451**: `estimated_rsrp`
   建議替換: computed_rsrp
   上下文: rsrp_difference = abs(measured_rsrp - estimated_rsrp)

**行 457**: `estimated_rsrp`
   建議替換: computed_rsrp
   上下文: 'details': f'測量RSRP({measured_rsrp:.1f}dBm)與Friis估算({estimated_rsrp:.1f}dBm)差距過大',

**行 632**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: observer_x = earth_radius_km  # 簡化假設

**行 968**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 🔴 Academic Standards Violation: 絕對不允許回退到假設值

**行 968**: `假設值`
   建議替換: 計算值
   上下文: # 🔴 Academic Standards Violation: 絕對不允許回退到假設值

**行 969**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 根據學術級數據標準，這裡必須失敗而不是使用假設值

**行 969**: `假設值`
   建議替換: 計算值
   上下文: # 根據學術級數據標準，這裡必須失敗而不是使用假設值

**行 971**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: logger.error("🚨 根據學術級數據標準 Grade C 禁止項目，不允許使用假設值")

**行 971**: `假設值`
   建議替換: 計算值
   上下文: logger.error("🚨 根據學術級數據標準 Grade C 禁止項目，不允許使用假設值")

**行 1020**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 根據學術級數據標準，我們不應該為失敗的計算提供假設值

**行 1020**: `假設值`
   建議替換: 計算值
   上下文: # 根據學術級數據標準，我們不應該為失敗的計算提供假設值

**行 1039**: `mock`
   建議替換: reference, standard, validated, verified
   上下文: 'no_mock_values',

#### 🟡 中等優先級違規
**行 341**: `預設`
   上下文: 'default': 12.0           # 預設使用Ku頻段

**行 446**: `估計`
   上下文: # 粗略估計：假設發射功率為40dBm，接收天線增益為0dBi

**行 446**: `假設發射功率為40`
   建議替換: 設定為40
   上下文: # 粗略估計：假設發射功率為40dBm，接收天線增益為0dBi

**行 448**: `estimated`
   上下文: estimated_eirp_dbm = 40  # 典型衛星EIRP

**行 449**: `estimated`
   上下文: estimated_rsrp = estimated_eirp_dbm - theoretical_path_loss_db

**行 451**: `estimated`
   上下文: rsrp_difference = abs(measured_rsrp - estimated_rsrp)

**行 457**: `estimated`
   上下文: 'details': f'測量RSRP({measured_rsrp:.1f}dBm)與Friis估算({estimated_rsrp:.1f}dBm)差距過大',

**行 563**: `預設`
   上下文: 'default': 12e9               # 預設頻率

**行 630**: `簡化`
   上下文: # 計算觀測者位置向量（簡化為地心到觀測者）

**行 632**: `簡化`
   上下文: observer_x = earth_radius_km  # 簡化假設

**行 1042**: `simplified`
   上下文: 'no_simplified_algorithms'

### 📄 netstack/src/stages/satellite_visibility_filter_processor.py

#### 🔴 高優先級違規
**行 33**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - Grade A: 嚴格基於物理參數，無假設值或回退機制

**行 33**: `假設值`
   建議替換: 計算值
   上下文: - Grade A: 嚴格基於物理參數，無假設值或回退機制

**行 34**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - 零容忍政策: 數據不足時直接排除，不使用假設

**行 48**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - 無假設值或回退機制

**行 48**: `假設值`
   建議替換: 計算值
   上下文: - 無假設值或回退機制

**行 106**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 學術標準：錯誤時排除該衛星，不使用假設

**行 107**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: return False  # 錯誤時假設可見

#### 🟡 中等優先級違規
**行 28**: `simplified`
   上下文: class SimplifiedVisibilityPreFilter:

**行 157**: `simplified`
   上下文: self.visibility_prefilter = SimplifiedVisibilityPreFilter(

**行 455**: `簡化`
   上下文: # 簡化篩選（避免過度篩選）

**行 583**: `簡化`
   上下文: # 簡化篩選（避免過度篩選）

### 📄 netstack/src/stages/dynamic_pool_planner.py

#### 🔴 高優先級違規
**行 1034**: `mock`
   建議替換: reference, standard, validated, verified
   上下文: # 🚨 CRITICAL FIX: Replace mock RSRP with physics-based calculation

**行 1042**: `mock`
   建議替換: reference, standard, validated, verified
   上下文: # 🚨 CRITICAL FIX: Replace mock values with physics-based calculations

**行 1127**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # ✅ Grade A: 完整鏈路預算 (不使用任何假設值)

**行 1127**: `假設值`
   建議替換: 計算值
   上下文: # ✅ Grade A: 完整鏈路預算 (不使用任何假設值)

**行 1211**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: """✅ Grade A: 基於物理原理的保守估計 (非固定假設值)"""

**行 1211**: `假設值`
   建議替換: 計算值
   上下文: """✅ Grade A: 基於物理原理的保守估計 (非固定假設值)"""

**行 1349**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 假設從TLE數據中獲取軌道要素 (實際應從TLE解析獲得)

**行 2051**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: """✅ Grade A: 基於物理原理的保守估計 (非固定假設值)"""

**行 2051**: `假設值`
   建議替換: 計算值
   上下文: """✅ Grade A: 基於物理原理的保守估計 (非固定假設值)"""

#### 🟡 中等優先級違規
**行 2**: `模擬`
   上下文: 🛰️ 增強動態衛星池規劃器 (模擬退火優化版)

**行 5**: `模擬`
   上下文: 目標：整合模擬退火優化器，實現更高效的動態衛星池規劃

**行 7**: `模擬`
   上下文: 輸出：模擬退火優化的動態衛星池規劃結果

**行 9**: `模擬`
   上下文: 技術升級：整合shared_core數據模型和模擬退火演算法

**行 41**: `簡化`
   上下文: # 簡化的性能監控裝飾器

**行 43**: `簡化`
   上下文: """簡化的性能監控裝飾器"""

**行 53**: `模擬`
   上下文: # 整合模擬退火優化器

**行 79**: `estimated`
   上下文: estimated_pool_size: int

**行 95**: `模擬`
   上下文: """增強動態衛星池規劃器 - 整合模擬退火優化和shared_core技術棧"""

**行 1012**: `模擬`
   上下文: norad_id=sat_data.get('norad_id', hash(sat_id) % 100000)  # 模擬NORAD ID

**行 1066**: `模擬`
   上下文: distribution_score=0.5,  # 模擬分數

**行 1154**: `估計`
   上下文: # ✅ Grade A: 即使出錯也不使用固定值，而是基於物理原理的最保守估計

**行 1211**: `估計`
   上下文: """✅ Grade A: 基於物理原理的保守估計 (非固定假設值)"""

**行 1218**: `估計`
   上下文: eirp = self._get_official_satellite_eirp(constellation) - 3.0  # 保守估計-3dB

**行 1669**: `簡化`
   上下文: # 簡化的多樣性計算：基於時間點的分散程度

**行 1680**: `預設`
   上下文: return 0.5  # 返回預設值

**行 2051**: `估計`
   上下文: """✅ Grade A: 基於物理原理的保守估計 (非固定假設值)"""

**行 2058**: `估計`
   上下文: eirp = self._get_official_satellite_eirp(constellation) - 3.0  # 保守估計-3dB

**行 2280**: `模擬`
   上下文: """模擬整個軌道週期的覆蓋時間軸 - 恢復被刪除的時間線模擬功能"""

**行 2284**: `模擬`
   上下文: self.logger.info(f"🔄 模擬覆蓋時間軸: {total_timepoints}個時間點")

**行 2498**: `預設`
   上下文: # 修復：使用正確的容器內路徑作為預設

### 📄 netstack/src/stages/orbital_phase_displacement.py

#### 🔴 高優先級違規
**行 323**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: 'starlink': len(selected_satellites.get('starlink', [])) * 0.6,  # 假設60%同時可見

**行 324**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: 'oneweb': len(selected_satellites.get('oneweb', [])) * 0.4     # 假設40%同時可見

#### 🟡 中等優先級違規
**行 168**: `簡化`
   上下文: # 簡化版：偏好特定相位範圍以實現錯開

**行 315**: `簡化`
   上下文: # 簡化的覆蓋分析

**行 320**: `簡化`
   上下文: 'coverage_continuity_score': 0.85,  # 簡化分數

**行 323**: `假設60`
   建議替換: 設定為60
   上下文: 'starlink': len(selected_satellites.get('starlink', [])) * 0.6,  # 假設60%同時可見

**行 324**: `假設40`
   建議替換: 設定為40
   上下文: 'oneweb': len(selected_satellites.get('oneweb', [])) * 0.4     # 假設40%同時可見

**行 329**: `簡化`
   上下文: 'phase_distribution_score': 0.9  # 簡化分數

### 📄 netstack/src/stages/orbital_calculation_processor.py

#### 🔴 高優先級違規
**行 1137**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: # 近似計算軌道高度（假設觀測者在海平面）

**行 1274**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - 零容忍政策：任何數據缺失直接失敗，不使用假設值

**行 1274**: `假設值`
   建議替換: 計算值
   上下文: - 零容忍政策：任何數據缺失直接失敗，不使用假設值

#### 🟡 中等優先級違規
**行 304**: `預設`
   上下文: - Grade A: 絕不使用預設軌道週期或回退機制

**行 491**: `預設`
   上下文: raise ValueError(f"Academic Standards Violation: 星座 {constellation} 缺乏Grade A驗證的軌道參數，拒絕使用預設值")

**行 1138**: `estimated`
   上下文: estimated_altitude = range_km - 6371  # 地球半徑

**行 1139**: `estimated`
   上下文: if estimated_altitude > 0:

**行 1140**: `estimated`
   上下文: if not (PHYSICAL_BOUNDARIES['altitude_km']['min'] <= estimated_altitude <= PHYSICAL_BOUNDARIES['altitude_km']['max']):

**行 1142**: `estimated`
   上下文: 'parameter': 'estimated_altitude_km',

**行 1143**: `estimated`
   上下文: 'value': estimated_altitude,

**行 1272**: `預設`
   上下文: - Grade A: 使用真實TLE數據，絕不使用預設值或回退機制

**行 1614**: `estimated`
   上下文: estimated_file_size_mb = 0

**行 1619**: `estimated`
   上下文: estimated_satellite_size_kb = avg_timeseries_points * 0.2

**行 1620**: `estimated`
   上下文: estimated_file_size_mb = (len(all_satellites) * estimated_satellite_size_kb) / 1024

**行 1623**: `estimated`
   上下文: file_size_reasonable = 1000 <= estimated_file_size_mb <= 3000  # 1-3GB

**行 1656**: `estimated`
   上下文: "estimated_file_size_mb": round(estimated_file_size_mb, 2),

### 📄 netstack/src/stages/timeseries_preprocessing_processor_academic_attempt.py

#### 🟡 中等優先級違規
**行 43**: `預設`
   上下文: self.sample_mode = False  # 預設為全量模式

### 📄 netstack/src/stages/sgp4_orbital_engine.py

#### 🟡 中等優先級違規
**行 218**: `簡化`
   上下文: range_rate_km_s = 0.0  # 簡化版本，可以通過數值微分計算

### 📄 netstack/src/stages/data_integration_processor.py

#### 🔴 高優先級違規
**行 892**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - 不使用任何模擬或假設的閾值

**行 2060**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - 不使用估算或假設

**行 2564**: `mock`
   建議替換: reference, standard, validated, verified
   上下文: # 🚨 CRITICAL FIX: Replace mock RSRP with physics-based calculation

**行 2776**: `mock`
   建議替換: reference, standard, validated, verified
   上下文: # 🚨 CRITICAL FIX: Replace mock RSRP with 3GPP-compliant trigger thresholds

**行 2962**: `假設`
   建議替換: 根據, 基於, 使用, 採用
   上下文: - 不使用模擬或假設的性能數值

#### 🟡 中等優先級違規
**行 3**: `簡化`
   上下文: 階段五：數據整合與接口準備處理器 - 簡化修復版本

**行 74**: `預設`
   上下文: self.sample_mode = False  # 預設為全量模式

**行 423**: `簡化`
   上下文: # 🎯 修復：簡化版本暫時跳過存儲平衡檢查，主要驗證數據整合功能

**行 424**: `簡化`
   上下文: storage_balance_ok = True  # 簡化版本先通過

**行 727**: `estimated`
   上下文: estimated_pg_size_mb = max(0.5, pg_records * 0.001) if pg_connected else 0  # 每筆記錄約1KB

**行 747**: `estimated`
   上下文: "postgresql_size_mb": round(estimated_pg_size_mb, 2),

**行 785**: `estimated`
   上下文: self.logger.info(f"🗃️ PostgreSQL (輕量版): {estimated_pg_size_mb:.1f}MB, Volume (詳細數據): {volume_size_mb:.1f}MB")

**行 786**: `estimated`
   上下文: total_storage = estimated_pg_size_mb + volume_size_mb

**行 788**: `estimated`
   上下文: pg_percentage = (estimated_pg_size_mb / total_storage) * 100

**行 892**: `模擬`
   上下文: - 不使用任何模擬或假設的閾值

**行 1392**: `預設`
   上下文: return 300  # 預設5分鐘

**行 1430**: `簡化`
   上下文: "signal_strength": 0.7,  # 簡化版

**行 1445**: `簡化`
   上下文: "signal_strength": 0.7,  # 簡化版

**行 1485**: `簡化`
   上下文: "avg_signal_quality": 0.75,  # 簡化版

**行 1516**: `簡化`
   上下文: "overall_score": 0.8 - (i * 0.1),  # 簡化版

**行 1650**: `simplified`
   上下文: f.write("sha256:simplified_checksum_placeholder")

**行 1650**: `placeholder`
   上下文: f.write("sha256:simplified_checksum_placeholder")

**行 1654**: `simplified`
   上下文: "checksum": "simplified_checksum_placeholder"

**行 1654**: `placeholder`
   上下文: "checksum": "simplified_checksum_placeholder"

**行 1876**: `estimated`
   上下文: 0.5  # estimated file size

**行 2051**: `預設`
   上下文: return 1.0  # 預設1MB

**行 2154**: `預設`
   上下文: # 預設SSD性能：~500MB/s

**行 2510**: `預設`
   上下文: mean_altitude = 550  # 預設高度

**行 2559**: `簡化`
   上下文: max_elevation = max([p.get('alt', 0) - 500 for p in visible_points])  # 簡化仰角計算

**行 2633**: `預設`
   上下文: # 使用3GPP NTN標準預設值

**行 2647**: `簡化`
   上下文: # 使用球面三角學計算斜距（非簡化公式）

**行 2898**: `預設`
   上下文: # 未定義事件類型 - 使用3GPP預設值

**行 2899**: `預設`
   上下文: self.logger.warning(f"未知3GPP事件類型: {event_type}, 使用預設閾值")

**行 2900**: `預設`
   上下文: return -100.0  # 3GPP TS 38.331預設RSRP閾值

**行 2962**: `模擬`
   上下文: - 不使用模擬或假設的性能數值

**行 3095**: `模擬`
   上下文: # 3. 混合查詢性能模擬 (基於實際連接狀態)

**行 3116**: `estimated`
   上下文: estimated_postgresql_mb = max(1, pg_records * 0.002) if pg_connected else 0  # 每筆記錄約2KB

**行 3118**: `estimated`
   上下文: total_storage_mb = estimated_postgresql_mb + actual_volume_mb

**行 3121**: `estimated`
   上下文: postgresql_percentage = (estimated_postgresql_mb / total_storage_mb) * 100

**行 3141**: `estimated`
   上下文: "postgresql_mb": round(estimated_postgresql_mb, 2),

**行 3166**: `estimated`
   上下文: self.logger.info(f"   PostgreSQL: {estimated_postgresql_mb:.1f}MB ({postgresql_percentage:.1f}%)")

## 💡 改進建議

1. **術語標準化**: 建立項目術語詞彙表
2. **代碼審查**: 在 PR 流程中加入術語檢查
3. **文檔更新**: 更新註釋和變量命名
4. **培訓教育**: 提供學術寫作標準培訓

## 🤖 自動化建議

```bash
# 設置 pre-commit hook
pip install pre-commit
echo 'python academic_compliance_cleaner.py --check' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```
