# ⏰ 重構執行時間線 (Refactoring Execution Timeline)

## 🎯 時間線目標

**制定詳細的重構實施時間表，確保六階段處理系統重構有序進行，最小化系統中斷，最大化重構效益。**

### 📅 總體時間規劃

| 階段 | 重構項目 | 預計時間 | 開始日期 | 完成日期 | 依賴關係 |
|------|----------|----------|----------|----------|----------|
| **Phase 1A** | Stage 1 緊急重構 | 2週 | 2025-09-18 | 2025-10-02 | 無 |
| **Phase 1B** | Stage 2 完成重構 | 2週 | 2025-09-18 | 2025-10-02 | 與1A並行 |
| **Phase 2** | 跨階段功能清理 | 3週 | 2025-10-02 | 2025-10-23 | Phase 1完成 |
| **Phase 3** | RL功能整合 | 2週 | 2025-10-09 | 2025-10-23 | 與Phase 2並行 |
| **Phase 4** | 系統整合驗證 | 1週 | 2025-10-23 | 2025-10-30 | Phase 2,3完成 |

**總計時間**: 6週 (含並行執行)
**目標完成日期**: 2025-10-30

---

## 🔥 Phase 1A: Stage 1 緊急重構 (2週)

## 🔧 Phase 1B: Stage 2 完成重構 (2週) - 並行執行

### Week 1: 模組遷移 (2025-09-18 → 2025-09-25)

#### Day 1-2 (週三-週四): Stage 1 模組遷移
**並行執行策略**: 與Phase 1A的Stage 1重構協調進行
```bash
# 將Stage 2的軌道相關模組遷移到Stage 1
mv skyfield_visibility_engine.py → stage1_orbital_calculation/skyfield_orbit_engine.py
mv orbital_data_loader.py → stage1_orbital_calculation/enhanced_orbital_loader.py

# 協調整合到Phase 1A的Skyfield整合工作
```

#### Day 3-4 (週五-週六): Stage 3 模組遷移
```bash
# 將Stage 2的分析模組遷移到Stage 3
mv visibility_analyzer.py → stage3_signal_analysis/advanced_visibility_analyzer.py
mv scientific_validation_engine.py → stage3_signal_analysis/scientific_validator.py
mv academic_standards_validator.py → stage3_signal_analysis/academic_validator.py
```

#### Day 5 (週日): Stage 6 和系統級遷移
```bash
# 遷移覆蓋保證引擎到Stage 6
mv coverage_guarantee_engine.py → stage6_dynamic_pool_planning/coverage_guarantee_engine.py

# 遷移學術警告管理器到系統級
mv academic_warning_manager.py → shared/academic_warning_manager.py
```

### Week 2: 清理和驗證 (2025-09-25 → 2025-10-02)

#### Day 1-2 (週一-週二): 重複檔案分析
```python
# 確認要刪除的重複模組
重複檔案清理清單 = [
    'visibility_calculator.py',           # 39,146行
    'elevation_filter.py',                # 23,513行
    'unified_intelligent_filter.py',      # 27,581行
    'temporal_spatial_filter.py',         # 21,723行
    'result_formatter.py',                # 23,026行
    'satellite_visibility_filter_processor.py.backup_complex'  # 1,401行
]
總清理行數 = 136,390行
```

#### Day 3-4 (週三-週四): 執行清理
```bash
# 1. 安全備份
mkdir -p backup/stage2_deleted_modules_20250925

# 2. 執行刪除
rm visibility_calculator.py elevation_filter.py unified_intelligent_filter.py \
   temporal_spatial_filter.py result_formatter.py \
   satellite_visibility_filter_processor.py.backup_complex

# 3. 更新__init__.py
# 只保留簡化模組的導入
```

#### Day 5 (週五): Phase 1B驗收
```bash
# 1. 驗證Stage 2簡化版本正常運行
python -c "from stage2_visibility_filter import SimpleStage2Processor; print('✅ Stage 2簡化版本正常')"

# 2. 驗證遷移模組在目標階段正常工作
# 3. 確認重複檔案清理完成
# 4. Stage 2重構完成報告
```

### Week 1: 功能移除 (2025-09-18 → 2025-09-25)
**注意**: 這是Phase 1A的內容，保持原有規劃

#### Day 1 (週三): 準備工作
**上午 (2小時)**:
```bash
# 1. 建立重構分支
git checkout -b stage1-emergency-refactor
git checkout -b stage1-backup-20250918

# 2. 完整備份現有實現
cp -r src/stages/stage1_orbital_calculation/ backup/stage1_pre_refactor/
```

**下午 (4小時)**:
```python
# 3. 詳細分析要移除的方法
# 移除清單確認:
- _add_observer_geometry()           # 1637-1674行 (38行)
- _calculate_observer_geometry()     # 1722-1772行 (51行)
- _calculate_elevation_azimuth()     # 1774-1796行 (23行)
- _enhance_satellite_with_observer_data()  # 1676-1691行 (16行)
- _add_observer_data_to_position()   # 1693-1720行 (28行)
- _calculate_gmst()                  # 相關輔助方法 (15行)
# 總計: ~171行移除
```

#### Day 2 (週四): 觀測者計算移除
**上午 (3小時)**:
```python
# 1. 移除觀測者幾何計算方法
# 檔案: tle_orbital_calculation_processor.py
# 移除方法: _add_observer_geometry(), _calculate_observer_geometry()
```

**下午 (3小時)**:
```python
# 2. 移除仰角方位角計算
# 移除方法: _calculate_elevation_azimuth(), _enhance_satellite_with_observer_data()
```

#### Day 3 (週五): 配置和輸出清理
**上午 (2小時)**:
```python
# 1. 清理 __init__ 方法中的觀測者配置
# 移除:
self.observer_calculations = config.get('observer_calculations', False)
self.observer_lat = config.get('observer_lat', 24.9441667)
self.observer_lon = config.get('observer_lon', 121.3713889)
self.observer_alt = config.get('observer_alt', 0.1)
```

**下午 (4小時)**:
```python
# 2. 清理輸出格式，移除觀測者相關字段
# 移除輸出字段:
- 'elevation_deg'
- 'azimuth_deg'
- 'is_visible'
- 'relative_to_observer'
```

#### Day 4 (週六): 第一輪測試
**全天 (6小時)**:
```bash
# 1. 執行第一輪測試
docker exec satellite-dev python scripts/run_single_stage.py --stage=1

# 2. 驗證輸出格式
# 確認只包含 ECI 座標，無觀測者數據

# 3. 性能基準測試
# 記錄移除功能後的執行時間和記憶體使用
```

#### Day 5 (週日): 問題修復
**全天 (6小時)**:
```python
# 1. 修復移除功能導致的錯誤
# 2. 調整相關測試案例
# 3. 確保 Stage 1 → Stage 2 數據流正常
```

### Week 2: Skyfield整合 (2025-09-25 → 2025-10-02)

#### Day 1 (週一): Skyfield庫整合
**上午 (3小時)**:
```python
# 1. 安裝和配置 Skyfield
pip install skyfield

# 2. 替換 SGP4 實現
from skyfield.api import load, EarthSatellite
from skyfield.timelib import Time
```

**下午 (3小時)**:
```python
# 3. 重構軌道計算核心邏輯
# 參考 satellite_visibility_calculator.py 實現
class SkyfieldOrbitCalculator:
    def calculate_satellite_position(self, tle_line1, tle_line2, time_points):
        """使用 Skyfield 計算衛星位置"""
        pass
```

#### Day 2 (週二): 時間基準標準化
**全天 (6小時)**:
```python
# 1. 實現 v6.0 時間基準繼承機制
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

# 2. 確保時間計算一致性
```

#### Day 3 (週三): 性能優化
**全天 (6小時)**:
```python
# 1. 優化 Skyfield 計算性能
# 2. 批量處理優化
# 3. 記憶體使用優化
```

#### Day 4 (週四): 完整測試
**全天 (6小時)**:
```bash
# 1. 完整六階段管道測試
python scripts/run_six_stages_with_validation.py

# 2. 驗證所有 10/10 檢查通過
# 3. 性能基準比較
```

#### Day 5 (週五): Phase 1 驗收
**全天 (6小時)**:
```bash
# 1. 最終驗收測試
# 2. 文檔更新
# 3. Phase 1 完成報告
```

---

## 🟡 Phase 2: 跨階段功能清理 (3週)

### Week 3: 強化學習功能統一 (2025-10-02 → 2025-10-09)

#### Day 1-2: Stage 3 RL功能移除
```python
# 移除 Stage 3 中的 RL 預處理功能
# 檔案: stage3_signal_analysis_processor.py
# 移除方法: _prepare_rl_features(), _normalize_rl_data(), _create_rl_state_vectors()
```

#### Day 3-4: Stage 4 RL引擎強化
```python
# 建立統一 RL 預處理引擎
# 檔案: stage4/unified_rl_preprocessor.py
class UnifiedRLPreprocessor:
    def preprocess_for_handover(self, signal_data):
        pass
    def preprocess_for_coverage(self, coverage_data):
        pass
```

#### Day 5: Stage 6 RL重複清理
```python
# 移除 Stage 6 中重複的 RL 預處理
# 改為調用 Stage 4 的統一介面
```

### Week 4: 物理計算庫建立 (2025-10-09 → 2025-10-16)

#### Day 1-2: 統一物理計算庫
```python
# 建立: shared/physics_library.py
class UnifiedPhysicsCalculator:
    @staticmethod
    def calculate_distance(pos1, pos2):
        pass
    @staticmethod
    def calculate_elevation_angle(satellite_pos, observer_pos):
        pass
    @staticmethod
    def calculate_path_loss(distance_km, frequency_ghz):
        pass
```

#### Day 3-4: 座標轉換庫統一
```python
# 建立: shared/coordinate_transformer.py
class StandardCoordinateTransformer:
    @staticmethod
    def eci_to_local_horizontal(eci_pos, observer_location, timestamp):
        pass
```

#### Day 5: Stage 2,3 調用標準庫
```python
# 重構 Stage 2,3 使用統一物理計算庫
```

### Week 5: 時間基準系統統一 (2025-10-16 → 2025-10-23)

#### Day 1-2: 時間基準管理系統
```python
# 建立: shared/time_base_manager.py
class UnifiedTimeBaseManager:
    @staticmethod
    def get_calculation_base_time(tle_epoch):
        pass
    @staticmethod
    def synchronize_stage_timestamps(stage_data):
        pass
```

#### Day 3-4: Stage 1,4,5 時間統一
```python
# 重構各階段使用統一時間基準
```

#### Day 5: Phase 2 整合測試
```bash
# 完整功能清理驗證測試
```

---

## 🤖 Phase 3: RL功能整合 (2週) - 與Phase 2並行

### Week 3-4: RL數據流重設計 (2025-10-09 → 2025-10-23)

#### 並行執行策略
- **與 Week 4 並行**: RL功能整合不影響物理計算庫建立
- **與 Week 5 並行**: RL時序處理與時間基準統一同步進行

#### 具體任務分配
```bash
# Week 3: RL架構設計
Day 1-2: 設計統一RL數據流
Day 3-4: 實現RL預處理標準化
Day 5: RL介面測試

# Week 4: RL模型整合
Day 1-2: 換手決策RL整合
Day 3-4: 覆蓋優化RL整合
Day 5: RL訓練驗證
```

---

## ✅ Phase 4: 系統整合驗證 (1週)

### Week 6: 最終整合 (2025-10-23 → 2025-10-30)

#### Day 1 (週一): 系統整合
**全天 (8小時)**:
```bash
# 1. 合併所有重構分支
git checkout main
git merge stage1-emergency-refactor
git merge cross-stage-cleanup
git merge rl-consolidation

# 2. 解決合併衝突
# 3. 系統完整性檢查
```

#### Day 2 (週二): 性能基準測試
**全天 (8小時)**:
```bash
# 1. 重構前後性能對比
# 處理時間、記憶體使用、成功率對比

# 2. 學術級驗證檢查
# 確保 10/10 驗證通過

# 3. 負載測試
# 大規模數據處理驗證
```

#### Day 3 (週三): 回歸測試
**全天 (8小時)**:
```bash
# 1. 完整六階段管道測試
# 2. 各階段單獨測試
# 3. 數據流完整性驗證
# 4. 邊界案例測試
```

#### Day 4 (週四): 文檔和訓練
**全天 (8小時)**:
```bash
# 1. 更新所有相關文檔
# 2. 建立重構後操作指南
# 3. 團隊培訓材料準備
# 4. 部署指南更新
```

#### Day 5 (週五): 最終驗收
**全天 (8小時)**:
```bash
# 1. 最終驗收測試
# 2. 重構完成報告
# 3. 經驗總結文檔
# 4. 後續維護計畫
```

---

## 📊 里程碑和檢查點

### 主要里程碑

| 里程碑 | 日期 | 驗收標準 | 責任人 |
|--------|------|----------|---------|
| **M1: Stage 1 重構完成** | 2025-10-02 | 代碼行數減少63%，Skyfield整合完成 | 架構師 |
| **M2: 功能清理完成** | 2025-10-23 | 無功能重複，統一介面實現 | 系統工程師 |
| **M3: RL整合完成** | 2025-10-23 | 統一RL數據流，性能提升15% | AI工程師 |
| **M4: 系統驗收完成** | 2025-10-30 | 10/10驗證通過，性能達標 | 品質保證 |

### 每週檢查點

**每週五下午**: 進度檢查會議
- 完成度評估
- 風險識別和緩解
- 下週工作計畫調整
- 資源分配檢討

**檢查內容**:
```bash
# 1. 代碼品質檢查
npm run lint
python -m pylint src/

# 2. 測試覆蓋率檢查
npm run test:coverage
pytest --cov=src/

# 3. 性能基準檢查
python scripts/performance_benchmark.py

# 4. 文檔同步檢查
# 確保文檔與實現一致
```

---

## 🛡️ 風險管理時間線

### 風險監控點

| 週次 | 主要風險 | 監控指標 | 緩解措施 |
|------|----------|----------|----------|
| **Week 1** | Stage 1功能移除影響數據流 | 數據完整性 | 每日備份和回歸測試 |
| **Week 2** | Skyfield整合性能問題 | 處理時間 | 性能監控和優化 |
| **Week 3** | RL功能移除影響模型訓練 | 模型精度 | A/B測試驗證 |
| **Week 4** | 多個階段同時修改引起衝突 | 系統穩定性 | 分支隔離和逐步合併 |
| **Week 5** | 時間基準統一影響時序計算 | 時間精度 | 時間戳驗證測試 |
| **Week 6** | 系統整合出現未預期問題 | 整體功能 | 完整回歸測試 |

### 緊急回退計畫

**回退條件**:
- 關鍵功能測試失敗
- 性能嚴重回歸 (>20%)
- 學術級驗證失敗 (<8/10)

**回退流程**:
```bash
# 1. 立即停止當前重構
git stash

# 2. 回退到備份分支
git checkout stage1-backup-20250918

# 3. 快速驗證原功能
python scripts/run_six_stages_with_validation.py

# 4. 分析失敗原因
# 5. 重新制定重構計畫
```

---

## 📈 成功指標和驗收標準

### 量化目標

| 指標 | 重構前 | 目標 | 驗收標準 |
|------|--------|------|----------|
| **Stage 1 代碼行數** | 2,178行 | ~800行 | 減少63% |
| **處理時間** | 272秒 | <200秒 | 提升26% |
| **記憶體使用** | ~756MB | <600MB | 減少20% |
| **功能重複率** | 35% | <10% | 減少71% |
| **驗證通過率** | 10/10 | 10/10 | 維持100% |

### 質化目標

**架構清晰度**:
- [ ] 每個階段職責邊界清晰
- [ ] 無跨階段功能重複
- [ ] 統一的介面和數據格式

**維護性提升**:
- [ ] 代碼可讀性提升
- [ ] 測試覆蓋率提升
- [ ] 文檔完整性提升

**擴展性增強**:
- [ ] 易於添加新功能
- [ ] 支援多種RL框架
- [ ] 模組化設計完善

---

## 🔄 後續維護計畫

### 重構後第一個月 (2025-11-01 → 2025-11-30)

**Week 1**: 穩定性監控
- 每日系統健康檢查
- 性能指標監控
- 用戶反饋收集

**Week 2-3**: 優化調整
- 根據監控數據進行微調
- 處理任何發現的問題
- 文檔更新和完善

**Week 4**: 經驗總結
- 重構效果評估報告
- 最佳實踐文檔撰寫
- 後續重構計畫制定

### 長期維護策略

**季度檢查** (每3個月):
- 架構健康度評估
- 功能邊界檢查
- 性能基準更新

**年度重審** (每12個月):
- 完整架構回顧
- 技術債務評估
- 下一次重構規劃

---

**執行開始**: 2025-09-18 (本週三)
**目標完成**: 2025-10-30
**總投入時間**: 6週

---
**文檔版本**: v1.0
**最後更新**: 2025-09-18
**狀態**: 準備執行