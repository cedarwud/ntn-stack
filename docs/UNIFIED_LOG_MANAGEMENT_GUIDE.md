# 📊 統一日誌管理系統指南

**版本**: 1.0.0  
**建立日期**: 2025-09-07  
**狀態**: ✅ 已實現並整合到六階段處理系統

## 🎯 概述

統一日誌管理系統解決了原有的日誌分散問題，將所有六階段處理的日誌、報告和驗證結果統一輸出到 `@logs/` 目錄中，讓用戶無需手動執行多個指令就能查看完整的執行結果。

## 🔧 核心功能

### ✅ 已解決的問題
- **日誌分散問題**: 原本分散在 `/app/data/`, Docker logs, 各階段輸出目錄
- **手動查詢麻煩**: 需要執行多個指令才能查看完整結果
- **缺乏統一格式**: 不同來源的日誌格式不一致
- **歷史記錄混亂**: 舊日誌和新日誌混在一起

### 🎯 新功能特性
- **統一輸出位置**: 所有結果輸出到 `logs/` 目錄
- **自動清理機制**: 每次執行前自動清理舊日誌
- **詳細執行追蹤**: 記錄每階段執行時間、驗證結果
- **TLE來源追蹤**: 明確記錄使用的TLE檔案來源
- **多格式報告**: JSON詳細報告 + 人類可讀摘要

## 📁 目錄結構

```
logs/
├── execution/                    # 執行日誌
│   └── execution_YYYYMMDD_HHMMSS.log
├── stage_reports/                # 各階段詳細報告
│   ├── stage_1_YYYYMMDD_HHMMSS.json
│   ├── stage_2_YYYYMMDD_HHMMSS.json
│   └── ...
├── validation/                   # 驗證日誌 (預留)
├── summary/                      # 最終綜合報告
│   ├── final_summary_YYYYMMDD_HHMMSS.json
│   └── final_summary_YYYYMMDD_HHMMSS.txt
```

## 🚀 使用方式

### 基本執行
```bash
# 在容器內執行六階段處理
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py
```

### 查看結果
```bash
# 查看最新執行日誌 (人類可讀)
ls -la logs/summary/*.txt | tail -1 | awk '{print $9}' | xargs cat

# 查看詳細JSON報告
ls -la logs/summary/*.json | tail -1 | awk '{print $9}' | xargs cat | jq

# 查看完整執行流程
ls -la logs/execution/*.log | tail -1 | awk '{print $9}' | xargs cat
```

## 📊 報告內容詳解

### 執行日誌 (execution_*.log)
```
📊 六階段數據處理執行日誌
==================================================
🆔 執行ID: 20250907_143022
⏰ 開始時間: 2025-09-07 14:30:22 UTC
🛰️ 使用的TLE數據:
   STARLINK: starlink_20250906.tle
   ONEWEB: oneweb_20250906.tle

🚀 階段1開始: TLE載入與SGP4軌道計算
   開始時間: 2025-09-07 14:30:23 UTC
✅ 階段1完成: TLE載入與SGP4軌道計算
   結束時間: 2025-09-07 14:32:15 UTC
   執行時間: 1.87 分鐘
   驗證結果: 階段1驗證成功
   輸出數量: 5247
```

### 階段報告 (stage_*_*.json)
```json
{
  "execution_id": "20250907_143022",
  "stage_number": 1,
  "stage_name": "TLE載入與SGP4軌道計算",
  "start_time": "2025-09-07T14:30:23Z",
  "end_time": "2025-09-07T14:32:15Z",
  "duration_minutes": 1.87,
  "processing_results_count": 5247,
  "validation": {
    "passed": true,
    "message": "階段1驗證成功"
  },
  "processing_summary": {
    "total_items": 5247,
    "has_data": true,
    "data_type": "satellite_data"
  }
}
```

### 最終綜合報告 (final_summary_*.txt)
```
📊 六階段數據處理執行摘要報告
============================================================
🆔 執行ID: 20250907_143022
⏰ 執行時間: 2025-09-07T14:30:22Z ~ 2025-09-07T14:45:33Z
⏱️ 總耗時: 15.18 分鐘
📊 整體狀態: FULLY_SUCCESS

🛰️ 使用的TLE數據源:
   STARLINK: starlink_20250906.tle
   ONEWEB: oneweb_20250906.tle

⚡ 各階段執行詳情:
----------------------------------------
✅ 階段1: TLE載入與SGP4軌道計算 (1.87分鐘)
✅ 階段2: 地理可見性篩選 (2.34分鐘)
✅ 階段3: 信號品質分析與3GPP事件 (3.12分鐘)
✅ 階段4: 時間序列預處理 (2.89分鐘)
✅ 階段5: 數據整合 (3.45分鐘)
✅ 階段6: 動態池規劃 (1.51分鐘)

📈 執行統計:
   完成階段: 6/6
   驗證通過: 6/6
   平均耗時: 2.53 分鐘/階段
```

## 🔧 技術實現

### 核心組件
- **`UnifiedLogManager`**: 統一日誌管理器類
- **`run_six_stages_with_validation.py`**: 已整合統一日誌的六階段處理腳本

### 關鍵方法
```python
# 初始化和清理
log_manager = UnifiedLogManager()
log_manager.clear_old_logs()

# 記錄TLE來源和執行開始
log_manager.initialize_execution_log(tle_sources)

# 記錄每階段開始和完成
log_manager.log_stage_start(stage_num, stage_name)
log_manager.log_stage_completion(stage_num, stage_name, results, validation_passed, message)

# 生成最終報告
log_manager.generate_final_summary_report()
```

## 🛠️ 自動清理機制

### 清理範圍
- **`logs/`** 目錄下的所有子目錄和文件
- **`/app/data/`** 目錄下的建構報告文件:
  - `.build_status`
  - `.build_validation_status`
  - `.final_build_report.json`
  - `.build_summary.txt`

### 清理時機
- 每次執行六階段處理前自動清理
- 確保每次執行都有全新的日誌環境

## 📈 優勢與改進

### ✅ 用戶體驗改進
- **一目了然**: 所有信息集中在 `logs/` 目錄
- **無需手動**: 不再需要執行多個查詢指令
- **時間追蹤**: 清楚知道每階段執行時間
- **TLE透明**: 明確知道使用了哪些TLE檔案

### ✅ 開發維護改進
- **統一格式**: 所有日誌使用統一的JSON+文本格式
- **易於調試**: 完整的執行流程追蹤
- **歷史清晰**: 每次執行都有獨立的時間戳標識
- **擴展性強**: 易於添加新的日誌類型和報告格式

## 🔍 故障排除

### 常見問題
1. **日誌目錄權限問題**
   ```bash
   # 檢查權限
   ls -la logs/
   
   # 修復權限
   sudo chown -R $USER:$USER logs/
   chmod -R 755 logs/
   ```

2. **統一日誌管理器導入失敗**
   ```bash
   # 檢查模組路徑
   docker exec netstack-api python -c "import sys; print(sys.path)"
   
   # 檢查文件存在
   docker exec netstack-api ls -la /app/src/shared_core/unified_log_manager.py
   ```

3. **舊格式報告混用**
   - 統一日誌系統會自動清理舊格式報告
   - 如果仍有問題，手動清理 `/app/data/` 下的報告文件

## 🚦 與現有系統的兼容性

- ✅ **完全向下兼容**: 原有的驗證機制保持不變
- ✅ **優雅降級**: 如果統一日誌管理器不可用，自動回退到原始日誌模式
- ✅ **無破壞性**: 不影響任何現有的API或數據處理邏輯

## 🎯 未來擴展計劃

- **實時監控**: 添加WebSocket實時日誌推送
- **日誌聚合**: 整合到中央日誌系統
- **性能指標**: 添加更詳細的性能監控和分析
- **告警機制**: 基於日誌內容的自動告警

---

**📝 說明**: 此功能已完全整合到六階段處理系統中，用戶無需任何額外配置即可使用。