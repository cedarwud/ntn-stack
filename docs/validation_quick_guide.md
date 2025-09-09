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

## ✅ 關鍵驗證項目

### 🎯 自動強制檢查 (所有模式)
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

### ❌ OneWeb ECI座標全零
```
錯誤：651顆OneWeb衛星ECI座標全為0
解決：檢查SGP4計算時間基準，確保使用TLE epoch時間而非當前時間
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