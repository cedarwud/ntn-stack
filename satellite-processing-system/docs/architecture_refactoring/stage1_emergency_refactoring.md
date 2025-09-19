# 🔥 Stage 1 緊急重構計畫 (Emergency Refactoring Plan)

## 🚨 重構緊急性評估

**Stage 1 是系統中最嚴重的功能越界案例，必須立即重構**

### 現狀問題診斷
- **📏 代碼規模**: 2,178行 (超標 45%，建議<1,500行)
- **🚫 功能越界**: 包含大量Stage 2職責 (觀測者計算、可見性判斷)
- **🔄 重複實現**: 與Stage 2功能重疊，造成維護困難
- **⚠️ 架構風險**: 可能重蹈Stage 2過度複雜化的覆轍

---

## 📊 越界功能詳細分析

### 🚫 需要移除的功能 (移至Stage 2)

| 功能類別 | 方法名稱 | 行數範圍 | 移除原因 |
|----------|----------|----------|----------|
| **觀測者幾何計算** | `_add_observer_geometry()` | 1637-1674 | Stage 2職責 |
| **幾何座標計算** | `_calculate_observer_geometry()` | 1722-1772 | Stage 2職責 |
| **仰角方位角計算** | `_calculate_elevation_azimuth()` | 1774-1796 | Stage 2職責 |
| **觀測者數據增強** | `_enhance_satellite_with_observer_data()` | 1676-1691 | Stage 2職責 |
| **位置數據增強** | `_add_observer_data_to_position()` | 1693-1720 | Stage 2職責 |
| **軌道相位分析** | `_add_orbital_phase_analysis()` | 1819-1862 | Stage 6職責 |
| **時間分析** | `_analyze_temporal_coverage_patterns()` | 2082-2121 | Stage 4職責 |

### 🚫 需要移除的配置參數

```python
# 🚫 移除：觀測者相關配置 (應在Stage 2設定)
self.observer_calculations = config.get('observer_calculations', False)
self.observer_lat = config.get('observer_lat', 24.9441667)
self.observer_lon = config.get('observer_lon', 121.3713889)
self.observer_alt = config.get('observer_alt', 0.1)
```

### 🚫 需要移除的輸出字段

```python
# 🚫 移除：觀測者相關輸出 (Stage 2負責)
- 'elevation_deg'           # 仰角
- 'azimuth_deg'            # 方位角
- 'is_visible'             # 可見性判斷
- 'relative_to_observer'   # 觀測者相對數據
```

---

## ✅ 保留的核心功能 (Stage 1正確職責)

### ✅ TLE數據處理
```python
- scan_tle_data()                    # TLE文件掃描
- load_raw_satellite_data()          # TLE解析和驗證
- _parse_single_tle_file()           # TLE格式解析
```

### ✅ SGP4軌道計算
```python
- calculate_all_orbits()             # 核心SGP4計算
- process_tle_orbital_calculation()  # 主要處理流程
- _estimate_processing_time()        # 性能預估
```

### ✅ 純軌道數據輸出
```python
- save_tle_calculation_output()      # ECI座標輸出
- _format_output_result()           # 數據格式化
- extract_key_metrics()             # 軌道指標提取
```

### ✅ 學術級驗證
```python
- run_validation_checks()           # 10項驗證檢查
- validate_input/output()           # 輸入輸出驗證
- 所有 _check_* 方法               # 學術標準檢查
```

---

## 🛠️ 重構實施方案

### Phase 1A: 功能移除 (1週)

#### 步驟1: 移除觀測者計算方法
```bash
# 移除的方法 (約400行)
- _add_observer_geometry()
- _calculate_observer_geometry()
- _calculate_elevation_azimuth()
- _enhance_satellite_with_observer_data()
- _add_observer_data_to_position()
- _calculate_gmst()
```

#### 步驟2: 移除配置和參數
```python
# 清理 __init__ 方法
# 移除觀測者相關參數
# 簡化初始化邏輯
```

#### 步驟3: 清理輸出格式
```python
# 輸出純ECI數據
{
  "position_timeseries": [
    {
      "timestamp": "2025-09-18T04:00:00Z",
      "position_eci": {"x": 1234.5, "y": -5678.9, "z": 3456.7},
      "velocity_eci": {"x": -1.2, "y": 2.3, "z": -0.8}
      # 🚫 移除: elevation_deg, azimuth_deg, is_visible
    }
  ]
}
```

### Phase 1B: v6.0 Skyfield整合 (1週)

#### 步驟4: 採用Skyfield標準庫
```python
# ✅ 新增：標準庫導入
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time

# ✅ 替換：自實現SGP4 → Skyfield
# 參考 satellite_visibility_calculator.py 實現
```

#### 步驟5: 時間基準標準化
```python
# ✅ v6.0要求：時間基準繼承機制
{
  "metadata": {
    "calculation_base_time": "2025-09-02T12:34:56.789Z",
    "tle_epoch_time": "2025-09-02T12:34:56.789Z",
    "stage1_time_inheritance": {
      "exported_time_base": "2025-09-02T12:34:56.789Z",
      "inheritance_ready": true,
      "calculation_reference": "tle_epoch_based"
    }
  }
}
```

---

## 📏 重構後預期結果

### 代碼規模優化
- **目標行數**: ~800行 (減少63%)
- **檔案結構**:
  ```
  tle_orbital_calculation_processor.py  # ~800行 (核心處理器)
  orbital_calculator.py                 # ~373行 (保持不變)
  tle_data_loader.py                   # ~273行 (保持不變)
  __init__.py                          # ~13行 (保持不變)
  ```

### 功能邊界清晰化
- **Stage 1**: 純軌道計算 (TLE + SGP4 + ECI)
- **Stage 2**: 觀測者計算 (ECI→仰角/方位角 + 可見性)
- **無功能重疊**: 完全分離的職責

### 性能改善
- **處理時間**: 預期減少20-30% (移除不必要計算)
- **記憶體使用**: 減少觀測者數據結構的記憶體開銷
- **Skyfield優勢**: 更精確、更快速的標準庫實現

---

## 🧪 重構驗證計畫

### 功能完整性驗證
```python
# ✅ 必須通過的驗證項目
- 10/10 學術級驗證檢查通過
- 8,932顆衛星 100%處理成功率
- ECI座標精度維持或提升
- TLE epoch時間基準正確使用
```

### 性能基準測試
```bash
# 重構前基準
處理時間: 272秒
記憶體峰值: ~756MB
成功率: 100%

# 重構後目標
處理時間: <200秒 (目標26%提升)
記憶體峰值: <600MB (目標20%減少)
成功率: 100% (維持)
```

### Stage 1→Stage 2 數據流驗證
```python
# ✅ 確保數據傳遞完整性
- ECI座標格式正確
- 時間戳一致性
- 衛星數量無損失
- Stage 2能正確接收並處理
```

---

## ⚠️ 風險控制措施

### 重構風險評估
- **🔴 高風險**: 影響整個系統數據流
- **🟡 中風險**: Stage 2需要相應調整
- **🟢 低風險**: 功能邏輯明確，可控性高

### 風險緩解策略
1. **分步實施**: 先移除功能，再整合Skyfield
2. **完整備份**: 重構前完整備份現有實現
3. **回歸測試**: 每步完成後進行完整測試
4. **回退計畫**: 保留回退到原實現的能力

### 品質保證檢查點
- [ ] Phase 1A完成: 功能移除無錯誤
- [ ] Phase 1B完成: Skyfield整合成功
- [ ] 驗證通過: 10/10驗證檢查
- [ ] 性能達標: 處理時間<200秒
- [ ] 數據流正常: Stage 2正確接收

---

## 📅 實施時間表

### Week 1: 功能移除
- Day 1-2: 移除觀測者計算方法
- Day 3-4: 清理配置和輸出格式
- Day 5: Phase 1A驗證測試

### Week 2: Skyfield整合
- Day 1-3: 整合Skyfield標準庫
- Day 4: 時間基準標準化
- Day 5: Phase 1B驗證測試

**目標完成日期**: 2週內完成所有重構

---

## 🔄 後續步驟

### 重構完成後
1. **📋 更新文檔**: 修訂stage1-tle-loading.md
2. **🔧 調整Stage 2**: 確保正確接收Stage 1數據
3. **🧪 系統測試**: 完整的六階段回歸測試
4. **📊 性能報告**: 重構前後性能對比

### 經驗總結
- 記錄重構過程中的關鍵決策
- 總結功能邊界劃分的最佳實踐
- 為後續階段重構提供參考

---

**下一步**: 開始Phase 1A功能移除
**相關文檔**: [跨階段功能清理](./cross_stage_function_cleanup.md)

---
**文檔版本**: v1.0
**最後更新**: 2025-09-18
**狀態**: 待執行