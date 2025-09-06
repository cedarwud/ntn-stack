# 六階段管道同步執行指南

## 問題描述
目前各階段的執行時間不同步：
- 階段1-4: 2025-09-05 06:30 左右
- 階段5: 2025-09-05 10:19 
- 階段6: 2025-09-03 14:15

這導致數據不一致和時間戳不匹配的問題。

## 解決方案

### 1. 使用統一管道執行腳本
```bash
cd /home/sat/ntn-stack/netstack
docker exec netstack-api python scripts/run_leo_preprocessing.py
```

### 2. 自動化定期執行
建議設置 cron job 來定期同步執行：
```bash
# 每天凌晨 2:00 執行
0 2 * * * cd /home/sat/ntn-stack/netstack && docker exec netstack-api python scripts/run_leo_preprocessing.py
```

### 3. 手動立即同步
如果需要立即同步所有階段的時間戳：
```bash
# 執行完整六階段處理
docker exec netstack-api python scripts/run_leo_preprocessing.py

# 檢查執行結果
curl -s http://localhost:8080/api/v1/pipeline/statistics | jq '.stages[] | {stage: .stage, execution_time: .execution_time}'
```

### 4. 前端改進建議
在前端管道統計介面中：
- 顯示整體管道的執行時間範圍
- 標記時間不一致的階段
- 提供手動觸發同步的按鈕

## 預期效果
執行後所有階段將有相近的時間戳，確保數據一致性。