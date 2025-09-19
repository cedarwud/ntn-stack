# 🔧 跨階段功能清理計畫 (Cross-Stage Function Cleanup Plan)

## 🎯 清理目標

**基於階段職責分析發現的功能重複和越界問題，制定系統性清理計畫，消除跨階段功能重複，確保每個階段功能邊界清晰。**

### 📊 功能重複問題概覽

| 重複功能類別 | 涉及階段 | 重複嚴重度 | 清理優先級 | 影響範圍 |
|------------|----------|------------|------------|----------|
| **強化學習預處理** | Stage 3,4,6 | 🔴 高 | 🔥 緊急 | 系統架構 |
| **觀測者計算** | Stage 1,2 | 🔴 高 | 🔥 緊急 | 數據流 |
| **物理標準計算** | Stage 2,3 | 🟡 中 | 🟡 中期 | 計算精度 |
| **座標轉換** | Stage 1,2,3 | 🟡 中 | 🟡 中期 | 性能 |
| **時間基準處理** | Stage 1,4,5 | 🟡 中 | 🟡 中期 | 時序同步 |

---

## 🔥 緊急清理項目

### 1. 強化學習預處理功能統一

#### 📋 問題現狀
- **Stage 3**: 包含 RL 預處理邏輯
- **Stage 4**: 主要 RL 預處理實現
- **Stage 6**: 重複的 RL 預處理功能

#### 🎯 清理目標
```
Stage 3 → 移除 RL 預處理 → 專注信號分析
Stage 4 → 保留核心 RL 預處理 → 標準化介面
Stage 6 → 移除重複 RL 預處理 → 專注動態規劃
```

#### 🛠️ 實施步驟

**Step 1: Stage 3 清理**
```python
# 🚫 移除：Stage 3 中的 RL 預處理代碼
# 文件：stage3_signal_analysis_processor.py
- _prepare_rl_features()
- _normalize_rl_data()
- _create_rl_state_vectors()

# ✅ 保留：純信號分析功能
- calculate_rsrp()
- calculate_rsrq()
- analyze_3gpp_events()
```

**Step 2: Stage 4 標準化**
```python
# ✅ 統一：Stage 4 RL 預處理介面
class UnifiedRLPreprocessor:
    def preprocess_for_handover(self, signal_data):
        """標準化換手 RL 預處理"""
        pass

    def preprocess_for_coverage(self, coverage_data):
        """標準化覆蓋 RL 預處理"""
        pass
```

**Step 3: Stage 6 清理**
```python
# 🚫 移除：Stage 6 中重複的 RL 預處理
# 改為：調用 Stage 4 的標準化介面
from stages.stage4.unified_rl_preprocessor import UnifiedRLPreprocessor

rl_processor = UnifiedRLPreprocessor()
processed_data = rl_processor.preprocess_for_coverage(data)
```

### 2. 觀測者計算功能邊界清理

#### 📋 問題現狀
- **Stage 1**: 包含觀測者幾何計算 (越界)
- **Stage 2**: 重複實現觀測者計算

#### 🎯 清理目標
```
Stage 1 → 移除所有觀測者計算 → 純 ECI 輸出
Stage 2 → 統一觀測者計算實現 → 標準化介面
```

#### 🛠️ 實施步驟

**Step 1: Stage 1 觀測者功能移除**
```python
# 🚫 完全移除的方法 (約400行代碼)
- _add_observer_geometry()           # 1637-1674行
- _calculate_observer_geometry()     # 1722-1772行
- _calculate_elevation_azimuth()     # 1774-1796行
- _enhance_satellite_with_observer_data()  # 1676-1691行
- _add_observer_data_to_position()   # 1693-1720行
```

**Step 2: Stage 2 觀測者計算標準化**
```python
# ✅ 統一觀測者計算介面
class StandardObserverCalculator:
    def calculate_elevation_azimuth(self, eci_position, observer_location):
        """標準仰角方位角計算"""
        pass

    def determine_visibility(self, elevation_deg, constellation):
        """標準可見性判斷"""
        pass
```

---

## 🟡 中期清理項目

### 3. 物理標準計算統一

#### 📋 問題現狀
- **Stage 2**: 基本物理計算 (距離、仰角)
- **Stage 3**: 高級物理計算 (信號傳播、衰減)

#### 🎯 清理目標
建立統一的物理計算庫，避免重複實現基礎物理公式

#### 🛠️ 實施方案
```python
# 建立：shared/physics_library.py
class UnifiedPhysicsCalculator:
    @staticmethod
    def calculate_distance(pos1, pos2):
        """統一距離計算"""
        pass

    @staticmethod
    def calculate_elevation_angle(satellite_pos, observer_pos):
        """統一仰角計算"""
        pass

    @staticmethod
    def calculate_path_loss(distance_km, frequency_ghz):
        """統一路徑損耗計算"""
        pass
```

### 4. 座標轉換功能統一

#### 📋 問題現狀
- **Stage 1**: ECI 座標計算
- **Stage 2**: ECI → 地平座標轉換
- **Stage 3**: 座標系統間轉換

#### 🎯 清理目標
建立標準座標轉換庫，避免重複實現轉換邏輯

#### 🛠️ 實施方案
```python
# 建立：shared/coordinate_transformer.py
class StandardCoordinateTransformer:
    @staticmethod
    def eci_to_local_horizontal(eci_pos, observer_location, timestamp):
        """ECI → 地平座標系轉換"""
        pass

    @staticmethod
    def calculate_relative_geometry(satellite_eci, observer_eci):
        """相對幾何計算"""
        pass
```

### 5. 時間基準處理統一

#### 📋 問題現狀
- **Stage 1**: TLE epoch 時間處理
- **Stage 4**: 時序數據時間處理
- **Stage 5**: 跨階段時間同步

#### 🎯 清理目標
建立統一時間基準管理系統

#### 🛠️ 實施方案
```python
# 建立：shared/time_base_manager.py
class UnifiedTimeBaseManager:
    @staticmethod
    def get_calculation_base_time(tle_epoch):
        """統一計算基準時間"""
        pass

    @staticmethod
    def synchronize_stage_timestamps(stage_data):
        """階段間時間戳同步"""
        pass
```

---

## 📋 清理實施路線圖

### Phase 1: 緊急功能清理 (2週)

**Week 1: 強化學習預處理統一**
- Day 1-2: Stage 3 RL 功能移除
- Day 3-4: Stage 4 RL 預處理標準化
- Day 5: Stage 6 RL 重複功能清理

**Week 2: 觀測者計算邊界清理**
- Day 1-3: Stage 1 觀測者功能完全移除
- Day 4-5: Stage 2 觀測者計算標準化

### Phase 2: 中期功能統一 (3週)

**Week 3: 物理計算庫建立**
- 統一物理計算實現
- Stage 2,3 調用標準庫

**Week 4: 座標轉換庫建立**
- 統一座標轉換實現
- Stage 1,2,3 調用標準庫

**Week 5: 時間基準系統統一**
- 統一時間處理實現
- Stage 1,4,5 調用標準庫

---

## 🧪 清理驗證標準

### 功能完整性驗證
```python
# ✅ 必須通過的驗證項目
- 10/10 學術級驗證檢查通過
- 8,932顆衛星 100%處理成功率
- 數據流完整性保證
- 階段間介面穩定性
```

### 性能改善目標
```bash
# 重複功能清理後預期改善
代碼重複率: 降低40%
記憶體使用: 減少25%
處理時間: 提升15%
維護複雜度: 降低50%
```

### 架構清晰度驗證
```python
# ✅ 確保架構邊界清晰
- 無跨階段功能重複
- 標準化介面調用
- 統一的共享庫實現
- 清晰的職責分離
```

---

## 🛡️ 風險控制措施

### 清理風險評估
- **🔴 高風險**: 可能影響多個階段的數據流
- **🟡 中風險**: 需要調整階段間介面
- **🟢 低風險**: 內部實現重構，介面不變

### 風險緩解策略
1. **分階段實施**: 先清理單個階段，再調整介面
2. **完整備份**: 清理前完整備份所有相關代碼
3. **回歸測試**: 每步完成後進行完整功能測試
4. **介面穩定**: 保持對外介面穩定，只調整內部實現

### 品質保證檢查點
- [ ] Phase 1完成: 緊急功能清理無錯誤
- [ ] Phase 2完成: 中期功能統一成功
- [ ] 驗證通過: 10/10驗證檢查
- [ ] 性能達標: 處理時間提升15%
- [ ] 架構清晰: 無功能重複

---

## 📊 清理後預期效果

### 代碼品質提升
- **功能重複**: 消除4個主要重複項目
- **代碼重複率**: 從35%降至<10%
- **維護複雜度**: 降低50%

### 架構清晰度
- **職責邊界**: 嚴格遵循STAGE_RESPONSIBILITIES.md
- **標準介面**: 統一的跨階段介面
- **共享庫**: 標準化的共享功能實現

### 性能改善
- **處理時間**: 提升15% (減少重複計算)
- **記憶體使用**: 減少25% (統一數據結構)
- **維護成本**: 降低40% (單一實現維護)

---

## 🔄 後續維護策略

### 防止重複機制
```python
# 建立：shared/function_registry.py
class FunctionRegistry:
    """防止功能重複的註冊機制"""

    @staticmethod
    def register_function(func_name, stage, description):
        """註冊階段功能"""
        pass

    @staticmethod
    def check_duplicates():
        """檢查功能重複"""
        pass
```

### 持續監控
- **代碼審查**: 新功能開發前檢查重複
- **自動檢測**: CI/CD 中加入重複檢測工具
- **文檔更新**: 同步更新 STAGE_RESPONSIBILITIES.md

---

**下一步**: 開始Phase 1緊急功能清理
**相關文檔**: [強化學習功能整合](./rl_preprocessing_consolidation.md)

---
**文檔版本**: v1.0
**最後更新**: 2025-09-18
**狀態**: 待執行