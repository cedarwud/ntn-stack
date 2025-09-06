# ⚡ 六階段建構狀態快速檢查

**用途**: 映像檔建構完成後，快速檢查六階段處理是否成功

## 🚀 一鍵檢查

```bash
# 建構完成後執行這個指令就知道結果
docker exec netstack-api bash /app/scripts/check_build_result.sh
```

## 📊 可能的結果

### ✅ 完全成功
```
🎉 狀態: 完全成功
✅ 建構成功: 是
✅ 驗證通過: 全部6階段
✅ 輸出檔案: 全部6個關鍵檔案
💡 建議: 無需額外操作，系統已就緒
```
**→ 什麼都不用做，可以直接使用**

### ⚠️ 部分成功 (常見)
```
⚠️ 狀態: 部分成功
⚠️ 完成階段: 1/6
❌ 失敗於階段: 2
💡 建議: 在容器啟動後執行運行時重新處理
```
**→ 執行修復指令:**
```bash
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py
```

### ❌ 完全失敗
```
❌ 狀態: 建構失敗
❌ 完成階段: 0/6
💡 建議: 重新建構映像檔
```
**→ 需要重新建構或檢查 TLE 數據**

## 🔍 詳細報告 (可選)

如果需要更多細節，可以查看：
```bash
# 文本摘要
docker exec netstack-api cat /app/data/.build_summary.txt

# JSON詳細報告
docker exec netstack-api cat /app/data/.final_build_report.json
```

## 🎯 常見問題快速解決

**階段1失敗** → 檢查 TLE 數據:
```bash
docker exec netstack-api ls -la /app/tle_data/starlink/tle/
docker exec netstack-api ls -la /app/tle_data/oneweb/tle/
```

**階段2失敗** → 路徑問題，執行運行時修復:
```bash
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py
```

---

**就這麼簡單！一個指令知道狀態，一個指令修復問題。**