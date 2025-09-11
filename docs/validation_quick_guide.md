# ⚡ 驗證框架快速指南

[🔄 返回文檔總覽](README.md) | [🛡️ 完整驗證框架說明](validation_framework_overview.md)

## 🎯 5分鐘快速上手

### 🚀 基本執行
```bash
# 預設驗證模式執行 (推薦)
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py

# 快速開發模式 (60-70% 時間節省)  
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --validation-level=FAST

# 學術發布模式 (完整驗證)
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --validation-level=COMPREHENSIVE
```

### 🔍 單階段測試
```bash
# 測試 Stage 1 軌道計算
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --stage=1 --validation-level=FAST

# 測試最終 Stage 6 動態池規劃
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py --stage=6 --validation-level=COMPREHENSIVE
```

## 📊 三級驗證模式對照

| 模式 | 檢查項目 | 時間開銷 | 適用場景 |
|------|----------|----------|----------|
| 🟢 **FAST** | 4-6項核心檢查 | +5-8% | 開發測試、CI/CD |
| 🟡 **STANDARD** | 10-13項檢查 | +10-15% | 日常生產使用 |
| 🔴 **COMPREHENSIVE** | 14-16項完整檢查 | +15-20% | 學術發布、重要驗證 |

## ⚡ 運行時檢查清單 (新增)

### 🚨 每個階段必須檢查 (零容忍)
**2025-09-09 重大強化**: 基於系統性驗證盲區發現，新增強制運行時檢查

- [ ] **使用的引擎類符合文檔規格** (檢查實際類型，非聲明類型)
- [ ] **輸出格式完全符合API契約** (嚴格檢查數據結構)
- [ ] **無任何未授權的簡化或回退** (零容忍簡化算法)
- [ ] **執行流程按照文檔順序** (檢查方法調用路徑)

### 📋 Stage 1 運行時檢查範例
```python
# 🔴 強制檢查 - 任何失敗都會停止執行
assert isinstance(engine, SGP4OrbitalEngine), f"錯誤引擎: {type(engine)}"
assert len(timeseries) == 192, f"時間序列長度錯誤: {len(timeseries)}"  
assert 'position_timeseries' in output, "缺少完整時間序列數據"
assert method_name == "calculate_position_timeseries", "錯誤計算方法"
```

## ✅ 關鍵驗證項目

### 🎯 自動強制檢查 (所有模式)
- 🔴 **運行時架構完整性檢查** (新增) - 檢查實際使用的引擎
- 🔴 **API契約嚴格執行** (新增) - 輸出格式100%合規
- ❌ **零容忍OneWeb ECI座標為零** - 立即失敗
- ✅ **SGP4時間基準檢查** - 必須使用TLE epoch時間
- ✅ **學術標準Grade評級** - 強制達到設定標準
- ✅ **物理合理性驗證** - 軌道參數符合物理定律

### 📈 驗證報告查看
```bash
# 查看最新驗證快照
ls -la /app/data/validation_snapshots/

# 檢查特定階段驗證結果
cat /app/data/validation_snapshots/stage1_validation.json | jq '.validation_results'
```

## 🚨 常見問題解決

### 🔴 運行時架構違規 (新增)
```
錯誤：assert isinstance(engine, SGP4OrbitalEngine) 失敗
原因：階段使用了CoordinateSpecificOrbitEngine而非SGP4OrbitalEngine  
解決：檢查階段處理器的引擎初始化，修復為正確引擎類型
```

### 🔴 API契約違規 (新增)
```
錯誤：assert len(timeseries) == 192 失敗
原因：輸出了218點而非規定的192點時間序列
解決：檢查軌道週期設置，確保使用96分鐘標準週期
```

### 🔴 執行流程違規 (新增)
```
錯誤：檢測到未授權的簡化回退機制
原因：代碼中包含了簡化算法或模擬數據
解決：移除所有簡化算法，使用完整的學術標準實現
```

### ❌ OneWeb ECI座標全零
```
錯誤：651顆OneWeb衛星ECI座標全為0
解決：檢查SGP4計算時間基準，確保使用TLE epoch時間進行軌道計算
```

### ⚠️ 驗證級別初始化失敗  
```
錯誤：ValidationLevelManager初始化失敗
解決：檢查configurable_validation_integration模組路徑
```

### 📉 學術標準檢查失敗
```
錯誤：數據品質未達Grade A標準  
解決：檢查academic_standards_engine報告，修復品質問題
```

## 🎯 最佳實踐

### 👨‍💻 開發階段
1. **日常開發**: 使用 `--validation-level=FAST`
2. **功能測試**: 使用 `--validation-level=STANDARD` 
3. **提交前檢查**: 使用 `--validation-level=COMPREHENSIVE`

### 🏭 生產環境
1. **日常處理**: 預設 `STANDARD` 模式
2. **學術發布**: 強制 `COMPREHENSIVE` 模式
3. **緊急修復**: 可暫時使用 `FAST` 模式

### 📊 監控建議
```bash
# 監控驗證失敗率
grep "驗證失敗" /app/logs/*.log | wc -l

# 查看驗證時間開銷
grep "validation_duration_seconds" /app/data/validation_snapshots/*.json

# 檢查學術標準合規率  
grep "academic_grade.*A" /app/data/validation_snapshots/*.json | wc -l
```

## 🔗 深入了解

- 📖 [完整驗證框架說明](validation_framework_overview.md) - 詳細架構和配置
- 📚 [學術數據標準](academic_data_standards.md) - Grade A/B/C分級標準  
- 📊 [六階段處理文檔](stages/) - 各階段具體驗證要求
- 🏗️ [系統架構說明](system_architecture.md) - 整體系統設計

---

**⚡ 記住**: 驗證框架是**透明增強**，不會改變原有處理邏輯，只會提升數據品質和可靠性！

*最後更新: 2025-09-09 | 快速指南 v1.0*