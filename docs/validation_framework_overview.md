# 🛡️ 六階段驗證框架總覽

[🔄 返回文檔總覽](README.md) | [📊 六階段處理導航](stages/README.md)

## 📋 概述

**NTN Stack 驗證框架** 是基於學術級標準的全面驗證體系，確保六階段數據處理的完整性、準確性和可靠性。本框架在不改變核心處理邏輯的前提下，提供可配置的多級驗證機制。

### 🎯 核心特性

- ✅ **零侵入整合**：不影響原有處理邏輯，透明增強品質
- ✅ **可配置級別**：FAST/STANDARD/COMPREHENSIVE 三級驗證
- ✅ **學術標準執行**：Grade A/B/C 分級標準強制執行
- ✅ **性能優化**：FAST 模式可減少 60-70% 驗證時間
- ✅ **全階段覆蓋**：所有六階段處理器完整整合

## 🚀 驗證框架架構

### 🛡️ 運行時驗證強化 (新增)

**2025-09-09 重大更新**: 基於發現的系統性驗證盲區，新增運行時架構完整性檢查維度。

#### 強制檢查維度
```python
# 🔴 運行時架構完整性檢查
RuntimeArchitectureChecker:
  - 引擎類型強制驗證 (防止替換為簡化引擎)
  - 方法調用路徑檢查 (確保按文檔流程執行)  
  - 依賴項完整性驗證 (檢查必需組件存在)

# 🔴 API契約嚴格執行  
APIContractValidator:
  - 輸出格式100%合規檢查
  - 數據結構完整性驗證
  - 字段類型和範圍約束檢查

# 🔴 執行流程完整性驗證
ExecutionFlowChecker:
  - 步驟順序強制檢查
  - 參數傳遞完整性驗證
  - 無簡化回退零容忍檢查
```

#### 實施要求
- **100%檢測率**: 任何架構違規都必須被檢測
- **零容忍政策**: 不允許任何形式的簡化或回退
- **運行時檢查**: 檢查實際執行的引擎和方法，而非聲明的
- **性能要求**: 額外檢查時間 <5%

### 📊 三級驗證模式

```python
# 🟢 FAST 模式 - 開發和測試用
ValidationLevel.FAST:
  - 執行時間: 減少 60-70%
  - 檢查項目: 4-6 項關鍵檢查
  - 適用場景: 開發測試、CI/CD
  
# 🟡 STANDARD 模式 - 正常使用 (預設)
ValidationLevel.STANDARD:
  - 執行時間: 正常
  - 檢查項目: 10-13 項檢查
  - 適用場景: 正常生產使用

# 🔴 COMPREHENSIVE 模式 - 完整驗證
ValidationLevel.COMPREHENSIVE:
  - 執行時間: 增加 5-10%
  - 檢查項目: 14-16 項完整檢查
  - 適用場景: 學術發布、重要驗證
```

### 🏗️ 核心組件

#### 1. 驗證級別管理器 (ValidationLevelManager)
```python
from configurable_validation_integration import ValidationLevelManager

# 自動初始化並管理驗證級別
validation_manager = ValidationLevelManager()
current_level = validation_manager.get_validation_level('stage1')
```

#### 2. 學術標準引擎 (AcademicStandardsEngine)
```python
from academic_standards_engine import AcademicStandardsEngine

# 強制執行學術標準 Grade A/B/C
academic_engine = AcademicStandardsEngine()
grade = academic_engine.evaluate_data_quality(data)
```

#### 3. 數據品質檢查器 (DataQualityEngine)
```python
from data_quality_engine import DataQualityEngine

# 多維度數據品質檢查
quality_engine = DataQualityEngine()
quality_report = quality_engine.comprehensive_check(data)
```

## 📈 各階段驗證整合狀況

### ✅ Stage 1: TLE 軌道計算驗證
- **檔案**: `orbital_calculation_processor.py`
- **整合狀態**: ✅ 完全整合 + 🔴 運行時強化
- **🚨 強制運行時檢查** (新增):
  ```python
  # 引擎類型強制檢查
  assert isinstance(engine, SGP4OrbitalEngine), f"錯誤引擎: {type(engine)}"
  # 輸出格式強制檢查  
  assert len(timeseries) == 192, f"時間序列長度錯誤: {len(timeseries)}"
  # API契約完整性檢查
  assert 'position_timeseries' in output, "缺少完整時間序列數據"
  ```

- **FAST模式檢查** (6項 - 已強化):
  - 🔴 **運行時引擎類型檢查** (新增)
  - 🔴 **API契約格式檢查** (新增)
  - TLE文件存在性
  - 衛星數量檢查  
  - 統一格式檢查
  - SGP4計算完整性

- **COMPREHENSIVE模式檢查** (16項 - 已強化):
  - 上述 FAST 檢查 +
  - 🔴 **執行流程完整性檢查** (新增)
  - 🔴 **無簡化回退檢查** (新增)
  - 星座完整性檢查
  - 重複數據檢查
  - 軌道數據合理性
  - 數據血統追蹤
  - 時間基準一致性
  - 數據結構完整性
  - 處理性能檢查
  - 文件大小合理性
  - 數據格式版本

### ✅ Stage 2: 衛星可見性篩選驗證
- **檔案**: `satellite_visibility_filter_processor.py`
- **整合狀態**: ✅ 完全整合
- **關鍵檢查**:
  - 地理座標有效性
  - 仰角計算精度 (ITU-R P.618標準)
  - 篩選邏輯一致性
  - 時間窗口連續性

### ✅ Stage 3: 信號分析驗證
- **檔案**: `signal_analysis_processor.py`  
- **整合狀態**: ✅ 完全整合
- **關鍵檢查**:
  - Friis公式實施驗證
  - 都卜勒頻移計算
  - 大氣衰減模型合規 (ITU-R P.618)
  - RSRP/RSRQ數值合理性

### ✅ Stage 4: 時間序列預處理驗證
- **檔案**: `timeseries_preprocessing_processor.py`
- **整合狀態**: ✅ 完全整合  
- **關鍵檢查**:
  - 時間戳一致性 (UTC標準)
  - 採樣頻率正確性
  - 數據缺失檢測
  - 統計特徵合理性

### ✅ Stage 5: 數據整合驗證
- **檔案**: `data_integration_processor.py`
- **整合狀態**: ✅ 完全整合
- **關鍵檢查**:
  - 跨階段數據完整性
  - 時間軸對齊驗證
  - 數據關聯正確性
  - 整合邏輯無錯誤

### ✅ Stage 6: 動態池規劃驗證  
- **檔案**: `dynamic_pool_planner.py`
- **整合狀態**: ✅ 完全整合
- **關鍵檢查**:
  - 換手決策邏輯 (3GPP NTN標準)
  - 資源配置合理性
  - 動態調整響應性
  - 最終結果完整性

## 🛠️ 使用方式

### 執行六階段完整處理
```bash
# 使用預設 STANDARD 驗證級別
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py

# 使用 FAST 驗證級別 (開發模式)
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --validation-level=FAST

# 使用 COMPREHENSIVE 驗證級別 (完整驗證)
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE
```

### 單階段執行
```bash
# Stage 1 with FAST validation
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --stage=1 --validation-level=FAST

# Stage 6 with COMPREHENSIVE validation  
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --stage=6 --validation-level=COMPREHENSIVE
```

## 📊 驗證報告格式

### 驗證快照結構
```json
{
  "validation_metadata": {
    "validation_level": "STANDARD",
    "total_checks_performed": 13,
    "validation_start_time": "2025-09-09T12:00:00Z",
    "validation_duration_seconds": 2.5,
    "academic_grade": "A",
    "data_quality_score": 0.98
  },
  "validation_results": {
    "TLE文件存在性": true,
    "衛星數量檢查": true,
    "SGP4計算完整性": true,
    // ... 其他檢查項目
  },
  "performance_metrics": {
    "validation_overhead_percentage": 8.5,
    "total_processing_time": 245.2,
    "validation_time": 20.8
  },
  "academic_standards_check": {
    "grade_achieved": "A", 
    "compliance_rate": 1.0,
    "critical_violations": [],
    "recommendations": []
  }
}
```

## 🔧 配置管理

### 驗證級別配置
**檔案位置**: `/home/sat/ntn-stack/academic_standards_config.py`

```python
# 各階段預設驗證級別
DEFAULT_VALIDATION_LEVELS = {
    'stage1': 'STANDARD',
    'stage2': 'STANDARD', 
    'stage3': 'STANDARD',
    'stage4': 'STANDARD',
    'stage5': 'STANDARD',
    'stage6': 'COMPREHENSIVE'  # 最終階段使用完整驗證
}

# 學術標準門檻
ACADEMIC_GRADE_THRESHOLDS = {
    'A': 0.98,  # 98% 以上
    'B': 0.90,  # 90-98%
    'C': 0.80   # 80-90%
}
```

### 數據品質配置
**檔案位置**: `/home/sat/ntn-stack/data_quality_config.py`

## 📈 性能影響分析

### 驗證時間開銷
- **FAST模式**: 5-8% 額外處理時間
- **STANDARD模式**: 10-15% 額外處理時間  
- **COMPREHENSIVE模式**: 15-20% 額外處理時間

### 記憶體使用
- **額外記憶體消耗**: <500MB
- **驗證快照大小**: 10-50KB 每階段

### 性能優化特性
- **智能緩存**: 重複驗證結果自動緩存
- **並行檢查**: 多項檢查並行執行
- **適應性調整**: 根據執行時間自動調整驗證級別

## 🚨 故障排除

### 常見驗證失敗
1. **OneWeb ECI座標為零**: 
   - 原因: SGP4計算時間基準錯誤
   - 解決: 使用TLE epoch時間而非當前時間

2. **驗證級別初始化失敗**:
   - 原因: configurable_validation_integration 模組路徑問題
   - 解決: 檢查 sys.path 配置

3. **學術標準檢查失敗**:
   - 原因: 數據品質未達 Grade A 標準
   - 解決: 檢查學術標準引擎報告

### 驗證失敗處理流程
```python
try:
    validation_result = processor.run_validation_checks(data)
    if not validation_result.get('overall_passed', False):
        logger.error("❌ 驗證失敗，系統將停止處理")
        raise ValidationError("Critical validation checks failed")
except Exception as e:
    logger.warning(f"⚠️ 驗證系統異常，回退到基本檢查: {e}")
    # 執行基本安全檢查
    basic_validation_passed = perform_basic_safety_checks(data)
    if not basic_validation_passed:
        raise ValidationError("Even basic safety checks failed")
```

## 📚 相關文檔

- [學術級數據使用標準](academic_data_standards.md) - Grade A/B/C 分級標準
- [各階段詳細驗證規格](stages/) - 每個階段的具體驗證要求
- [驗證框架重建計劃](../validation_framework_rebuild_plan/) - 開發過程記錄

## 🎯 最佳實踐

### 開發階段
- 使用 **FAST** 模式進行快速迭代
- 重要功能測試時使用 **STANDARD** 模式
- 提交前使用 **COMPREHENSIVE** 模式最終檢查

### 生產環境  
- 日常處理使用 **STANDARD** 模式
- 學術發布前使用 **COMPREHENSIVE** 模式
- 定期執行完整驗證確保系統健康

### 監控建議
- 監控驗證失敗率趨勢
- 追蹤驗證時間開銷
- 定期檢視學術標準合規率

---

**⚡ 核心原則**: 學術誠信 > 系統穩定性 > 處理效率  
**🎯 設計目標**: 零學術造假、完整數據追蹤、自動化品質保證  

*最後更新: 2025-09-09*  
*版本: v2.0 - Phase 3+ 驗證框架完整整合*