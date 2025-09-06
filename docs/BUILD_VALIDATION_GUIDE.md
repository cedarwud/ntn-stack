# 🏗️ 建構時六階段驗證指南

**版本**: 1.0.0  
**更新日期**: 2025-09-06  
**適用於**: NTN Stack 即時驗證架構 (v4.1+)

## 🎯 解決的問題

**核心問題**: "當我在映像檔建構階段執行六階段資料預處理錯誤時，我要怎麼才能知道有發生錯誤或是有正確的執行完六階段產生最後正確的結果?"

**解決方案**: 
- 建構完成後自動執行狀態檢查腳本
- 生成三種格式的詳細建構報告
- 提供明確的錯誤定位和修復建議
- 確保每次建構前清理舊報告

## 🚀 快速檢查方法

### 建構完成後立即檢查
```bash
# 方法1: 用戶友好的建構結果檢查 (推薦)
docker exec netstack-api bash /app/scripts/check_build_result.sh

# 方法2: 直接查看文本摘要
docker exec netstack-api cat /app/data/.build_summary.txt

# 方法3: 查看JSON詳細報告
docker exec netstack-api cat /app/data/.final_build_report.json | jq '.'
```

## 📊 三種建構報告格式

### 1. JSON詳細報告 (`.final_build_report.json`)
```json
{
  "build_validation_metadata": {
    "report_version": "1.0.0",
    "validation_framework": "immediate_stage_validation",
    "report_generation_time": "2025-09-06T07:03:46.117009+00:00"
  },
  "overall_status": {
    "status": "SUCCESS", 
    "status_message": "完全成功",
    "completed_stages": 6,
    "total_expected_stages": 6,
    "valid_outputs": 6,
    "total_processing_time_minutes": 12.5
  },
  "stage_validation_details": {
    "1": {
      "stage_name": "SGP4軌道計算與時間序列生成",
      "status": "success",
      "duration_seconds": 224.9,
      "validation_passed": true,
      "timestamp": "2025-09-06T06:50:08.390240+00:00"
    }
  }
}
```

### 2. 狀態檔案 (`.build_status`)
```bash
BUILD_OVERALL_STATUS=SUCCESS
BUILD_SUCCESS=true
BUILD_IMMEDIATE_VALIDATION_PASSED=true
BUILD_VALIDATION_MODE=immediate
BUILD_TIMESTAMP=2025-09-06T07:03:46.117009+00:00
BUILD_PROCESSING_TIME_SECONDS=750.2
BUILD_VALID_OUTPUTS=6
```

### 3. 文本摘要 (`.build_summary.txt`)
```
NTN Stack 映像檔建構狀態報告
==================================================
報告生成時間: 2025-09-06 07:03:46 UTC
建構狀態: ✅ 完全成功
完成階段: 6/6
有效輸出: 6/6
總處理時間: 750.2 秒 (12.5 分鐘)

建議操作:
  ✅ 建構完全成功，所有六階段處理完成
  🎉 系統已就緒，無需額外操作
```

## 🔍 狀態判斷邏輯

### ✅ 完全成功 (SUCCESS)
**指標**:
- 所有6個階段驗證快照存在且通過
- 所有6個輸出檔案存在且大小符合預期
- `BUILD_SUCCESS=true`
- `BUILD_IMMEDIATE_VALIDATION_PASSED=true`

### ⚠️ 部分成功 (PARTIAL)
**指標**:
- 至少1個階段成功完成
- 某個階段驗證失敗，後續階段自動停止
- `BUILD_PARTIAL_SUCCESS=true`
- `RUNTIME_PROCESSING_REQUIRED=true`

**處理方法**:
```bash
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py
```

### ❌ 建構失敗 (FAILED)
**指標**:
- 沒有任何階段成功完成
- 沒有有效的輸出檔案
- `BUILD_FAILED=true`

**處理方法**: 檢查並修復問題後重新建構

## 🛠️ 整合到建構流程

### Docker 建構後驗證
```dockerfile
# 在 Dockerfile 最後階段加入
COPY scripts/enhanced_build_validation.sh /app/scripts/
COPY scripts/final_build_validation.py /app/scripts/
RUN chmod +x /app/scripts/enhanced_build_validation.sh

# 執行建構驗證 (自動清理舊報告 + 生成新報告)
RUN /app/scripts/enhanced_build_validation.sh
```

### 建構腳本整合
```bash
#!/bin/bash
# build.sh
docker build -t ntn-stack ./netstack/

# 檢查建構結果
docker exec netstack-api bash /app/scripts/check_build_result.sh

# 根據結果決定下一步
BUILD_STATUS=$(docker exec netstack-api cat /app/data/.build_status | grep "BUILD_OVERALL_STATUS" | cut -d'=' -f2)

if [ "$BUILD_STATUS" = "SUCCESS" ]; then
    echo "✅ 建構完全成功"
elif [ "$BUILD_STATUS" = "PARTIAL" ]; then
    echo "⚠️ 建構部分成功，需要運行時處理"
else
    echo "❌ 建構失敗，請檢查日誌"
    exit 1
fi
```

## 🎯 即時驗證架構特色

### 階段即時驗證 (Stage Immediate Validation)
- 每個階段完成後立即驗證
- 驗證失敗時自動停止後續階段
- 避免基於錯誤數據的無意義計算
- 提供精確的錯誤定位

### 自動報告清理
- 每次建構前自動清理舊報告
- 確保報告內容是當前建構的結果
- 包含明確的執行時間戳

### ValidationSnapshotBase 框架
- 每階段自動生成驗證快照
- 7項核心檢查項目全面驗證
- 數據完整性、質量、性能指標
- 支援下游階段準備狀態檢查

## 📈 性能基準

### 正常建構時間
- **階段1**: 3-4分鐘 (SGP4計算8791顆衛星)
- **階段2**: 1-2分鐘 (智能篩選)
- **階段3**: 1-2分鐘 (信號分析)
- **階段4**: 1-2分鐘 (時間序列)
- **階段5**: 30-60秒 (數據整合)
- **階段6**: 10-30秒 (動態池)
- **總計**: 8-12分鐘

### 異常指標
- **超過15分鐘**: 可能記憶體不足或I/O瓶頸
- **階段1超過5分鐘**: TLE數據載入問題
- **階段2立即失敗**: 路徑配置錯誤

## 🔗 相關工具

### 檢查工具
- `check_build_result.sh` - 用戶友好的報告查看
- `quick_build_check.sh` - 快速狀態檢查
- `check_build_status.py` - 詳細狀態分析

### 處理工具
- `run_six_stages_with_validation.py` - 即時驗證管道
- `final_build_validation.py` - 建構最終驗證
- `enhanced_build_validation.sh` - 整合建構腳本

---

**這個建構驗證系統確保你在映像檔建構完成後立即獲得準確、詳細的狀態報告，包含明確的執行時間和具體的修復建議，完全解決了建構狀態不明確的問題。**

*版本 1.0.0 | 文檔整合到 @docs/ | 2025-09-06*