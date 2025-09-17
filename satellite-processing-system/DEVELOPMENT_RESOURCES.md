# 🛠️ 開發資源索引

## 📍 關鍵檔案位置指南

### 🧪 測試檔案
- **位置**: `tests/integration/`
- **內容**: 各階段整合測試、學術標準合規測試、Skyfield引擎測試
- **用途**: 六階段開發時的回歸測試和驗證

```bash
# 執行六階段測試
cd tests/integration/
python test_stage1_*.py
python test_stage2_*.py
# ... 其他階段
```

### 📚 開發文檔
- **位置**: `docs/development/`
- **內容**: 
  - `UNIFIED_REFACTORING_PLAN.md` - 統一重構計劃
  - `STAGE6_VIOLATIONS_COMPLETE_AUDIT.md` - Stage 6 違規審計
  - `REFACTORING_PROGRESS_TRACKER.md` - 重構進度追蹤

### 🎓 學術文檔
- **位置**: `docs/academic/`
- **內容**: 學術標準合規報告、六階段分析報告
- **用途**: 論文撰寫、學術驗證

### 🔧 修復後的組件
- **位置**: `src/stages/stage6_dynamic_planning/DYNAMIC_COVERAGE_OPTIMIZER_FIXED.py`
- **內容**: 修復後的動態覆蓋優化器
- **用途**: Stage 6 開發時的參考實現

## 🗂️ 其他測試資料
- **位置**: `/temp_test_files/` (專案根目錄)
- **內容**: 衛星可見性測試數據、文檔草稿、其他臨時檔案
- **說明**: 保留備用，非必要時不會主動使用

---
*更新日期: 2025-09-17*
*用途: 確保六階段開發時能快速找到需要的資源*
