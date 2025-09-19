# 🧪 TDD重構指南 - v6.0版本

## 📋 文檔概述

**目的**: 為重構後的satellite-processing-system提供TDD測試開發指南
**版本**: 6.0.0 (Phase 3重構完成版)
**更新日期**: 2025-09-18
**適用範圍**: 重構後的六階段處理系統

## 🎯 重構後TDD策略

### ✅ 重構驗證重點

#### 1. Stage 1 重構驗證
- **觀測者計算移除**: 確認不包含任何觀測者相關功能
- **純軌道計算**: 驗證只輸出ECI位置和速度
- **TLE時間基準**: 確認使用TLE epoch時間而非當前時間
- **代碼減少**: 從2,178行減少到~800行

#### 2. Stage 3 重構驗證
- **觀測者座標動態載入**: 從Stage 2輸入數據載入
- **硬編碼移除**: 初始化時observer_coordinates為None
- **職責專注**: 專注信號分析，不再計算觀測者幾何

#### 3. 跨階段重構驗證
- **文件歸屬**: 確認文件在正確的Stage目錄
- **功能重複**: 確認沒有跨Stage功能重複
- **數據流**: 驗證Stage間正確的數據傳遞

## 🧪 TDD測試文件結構

### 📁 測試目錄組織
```
tests/
├── unit/                           # 單元測試
│   ├── algorithms/                 # 核心算法測試
│   │   ├── test_sgp4_orbital_engine_tdd.py      # SGP4軌道計算
│   │   └── test_signal_quality_calculator_tdd.py # 信號品質計算
│   ├── stages/                     # 各階段測試
│   │   ├── test_stage1_refactored.py            # Stage 1重構驗證
│   │   ├── test_stage3_refactored.py            # Stage 3重構驗證
│   │   └── ...                     # 其他階段測試
│   └── shared/                     # 共享組件測試
├── integration/                    # 整合測試
├── snapshots/                      # 驗證快照
│   └── post_refactoring_validation_snapshot.md
└── fixtures/                       # 測試固件
```

## 🏷️ pytest標記系統

### 標記分類
- `@pytest.mark.unit` - 單元測試
- `@pytest.mark.integration` - 整合測試
- `@pytest.mark.refactored` - 重構後測試
- `@pytest.mark.snapshot` - 快照驗證測試
- `@pytest.mark.critical` - 關鍵功能測試
- `@pytest.mark.stage1` / `@pytest.mark.stage3` - 特定階段測試
- `@pytest.mark.sgp4` / `@pytest.mark.signal` - 特定算法測試
- `@pytest.mark.compliance` - 學術合規測試
- `@pytest.mark.performance` - 性能測試

### 執行範例
```bash
# 執行重構驗證測試
pytest -m "refactored"

# 執行Stage 1重構測試
pytest -m "stage1 and refactored"

# 執行關鍵功能測試
pytest -m "critical"

# 執行所有重構相關測試
pytest tests/unit/stages/test_stage1_refactored.py tests/unit/stages/test_stage3_refactored.py
```

## 🔬 重構驗證測試案例

### Stage 1重構驗證
```python
def test_removed_observer_methods(self, processor):
    """驗證觀測者計算方法已被移除"""
    removed_methods = [
        '_add_observer_geometry',
        '_calculate_observer_geometry',
        '_validate_observer_coordinates'
    ]
    for method_name in removed_methods:
        assert not hasattr(processor, method_name)

def test_tle_epoch_time_usage(self, processor):
    """驗證使用TLE epoch時間而非當前時間進行計算"""
    # 測試時間基準正確性
    assert metadata["tle_epoch_used"] is True
```

### Stage 3重構驗證
```python
def test_observer_coordinates_loading_from_stage2(self, processor):
    """測試從Stage 2載入觀測者座標的新邏輯"""
    processor.input_data = mock_stage2_input
    result = processor.execute()
    # 驗證觀測者座標從Stage 2載入
    assert processor.observer_coordinates == expected_coordinates

def test_removed_hardcoded_observer_coordinates(self, processor):
    """驗證移除了硬編碼的觀測者座標"""
    assert processor.observer_coordinates is None
```

## 📊 測試覆蓋率目標

### 覆蓋率要求
- **總體覆蓋率**: 85% (重構後優化目標)
- **重構相關代碼**: 95% (關鍵變更必須全覆蓋)
- **核心算法**: 90% (SGP4, 信號計算)
- **Stage處理器**: 90% (各階段主要邏輯)

### 覆蓋率檢查
```bash
# 生成覆蓋率報告
pytest --cov=src --cov-report=html

# 檢查重構相關文件覆蓋率
pytest --cov=src/stages/stage1_orbital_calculation --cov=src/stages/stage3_signal_analysis --cov-report=term-missing
```

## 🚀 性能測試指南

### 重構後性能驗證
- **Stage 1**: 軌道計算性能提升驗證
- **批量處理**: 100顆衛星 < 10秒
- **記憶體使用**: 重構後記憶體優化驗證

### 性能測試案例
```python
@pytest.mark.performance
def test_refactored_performance_improvement(self, processor):
    """驗證重構後性能提升"""
    execution_time = measure_execution_time(processor)
    assert execution_time < expected_time_limit
```

## 🎯 學術合規測試

### Grade A標準驗證
- **真實數據使用**: 確認使用真實TLE數據
- **標準算法**: 確認使用標準SGP4實現
- **物理約束**: 驗證計算結果符合物理約束
- **時間基準**: 確認使用TLE epoch時間

### 合規測試案例
```python
@pytest.mark.compliance
def test_academic_compliance_standards(self, processor):
    """驗證學術合規性標準"""
    compliance_checks = {
        "uses_real_tle_data": True,
        "uses_tle_epoch_time": True,
        "sgp4_algorithm": True,
        "no_simplified_model": True
    }
    for check, status in compliance_checks.items():
        assert status, f"學術合規檢查失敗: {check}"
```

## 📋 重構驗證清單

### 必須通過的驗證項目
- [ ] **Stage 1**: 無觀測者計算功能
- [ ] **Stage 3**: observer_coordinates動態載入
- [ ] **跨階段**: 無功能重複
- [ ] **數據流**: Stage間正確傳遞
- [ ] **TLE時間**: 使用epoch時間基準
- [ ] **測試覆蓋**: 重構代碼95%覆蓋
- [ ] **性能**: 重構後性能無回歸
- [ ] **學術標準**: 完全符合Grade A要求

## 🔧 開發工作流

### TDD開發流程
1. **編寫失敗測試**: 針對重構需求編寫測試
2. **最小實現**: 讓測試通過的最小代碼實現
3. **重構優化**: 在測試保護下重構代碼
4. **驗證覆蓋**: 確保測試覆蓋率達標
5. **整合驗證**: 執行完整測試套件

### 持續集成
```bash
# 完整測試套件執行
pytest tests/ --cov=src --cov-fail-under=85

# 重構驗證專用測試
pytest -m "refactored or critical" --cov=src --cov-report=term-missing
```

---

**文檔版本**: v6.0.0
**最後更新**: 2025-09-18
**維護者**: Claude Code Assistant
**相關文檔**: [Phase 3重構完成報告](./architecture_refactoring/phase3_refactoring_completion_report.md)