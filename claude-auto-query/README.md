# Claude API 智能重試自動查詢系統

## 🎯 功能特色

### 🧠 智能重試機制
- **一次性執行**: 每個任務只執行一次，成功即完成
- **自動重試**: 失敗時自動設定重試任務
- **遞增間隔**: 每次重試間隔遞增 (1小時、2小時、3小時...)
- **持續重試**: 直到收到 "OK" 回應才停止
- **狀態追蹤**: 完整的重試狀態管理
- **預設查詢**: 自動使用會讓 Claude 回應 "OK" 的查詢
- **任務清理**: 成功時自動清除所有相關任務

### 📊 適用場景
- 定時健康檢查
- 定時系統監控
- 需要確保執行完成的重要任務
- 網路不穩定環境下的可靠查詢
- 需要記錄實際執行成功時間的場景

## 📁 檔案結構

```
claude-auto-query/
├── claude_api_caller.py        # 基礎 API 調用程式
├── claude_retry_system.py      # 智能重試系統 (核心)
├── claude_auto_query.sh        # 主要包裝腳本
├── setup_claude_cron.sh        # Cron 設定腳本
├── README.md                   # 本說明文件
├── claude_cron.log            # 主要執行日誌 (自動生成)
├── claude_retry.log           # 重試系統日誌 (自動生成)
├── retry_state.json           # 重試狀態檔案 (自動生成)
└── original_cron.backup       # 原始 crontab 備份 (自動生成)

../logs/
└── cron.log                   # 成功時間記錄檔案 (自動生成)
```

## 🚀 快速開始

### 1. 設定環境變數
```bash
export ANTHROPIC_BASE_URL="https://claude-relay.kh2u.com/api/"
export ANTHROPIC_AUTH_TOKEN="your_token_here"
```

### 2. 測試基本功能
```bash
cd /home/sat/ntn-stack/claude-auto-query

# 使用預設查詢 (會讓 Claude 回應 "OK")
python3 claude_retry_system.py

# 或者直接執行包裝腳本
./claude_auto_query.sh

# 如果需要自訂查詢 (需確保 Claude 會回應 "OK")
python3 claude_retry_system.py "Please respond with exactly 'OK' and nothing else."
```

### 3. 設定定時任務
```bash
./setup_claude_cron.sh
```

按照提示設定：
- 觸發頻率
- 查詢內容 (預設會使用確保成功的查詢)

## 🔄 重試機制詳解

### 觸發條件
系統會在以下情況觸發重試：
1. **API 調用失敗** (網路錯誤、伺服器錯誤等)
2. **未收到 "OK" 回應** (收到其他內容)

### 重試邏輯
```
初始查詢 → 失敗 → 1小時後重試
             ↓
          仍失敗 → 2小時後重試
             ↓
          仍失敗 → 3小時後重試
             ⋮
          直到收到 "OK" 為止
```

### 狀態管理
- `retry_state.json` 記錄重試次數和狀態
- 成功時自動清除狀態和重試任務
- 可手動查看重試狀態: `cat retry_state.json`
- **成功時間自動記錄到 `/home/sat/ntn-stack/logs/cron.log`**

## 💡 使用範例

### 基本測試
```bash
# 使用預設查詢 (會立即成功)
./claude_auto_query.sh

# 或者直接使用 Python 腳本
python3 claude_retry_system.py

# 自訂查詢 (需要確保會回應 "OK")
./claude_auto_query.sh "Please respond with exactly 'OK' and nothing else."
```

### 實際應用
```bash
# 使用預設查詢進行定時健康檢查
./claude_auto_query.sh

# 自訂查詢 (需要確保 Claude 會回應 "OK")
./claude_auto_query.sh "System health check - please respond with 'OK' if all systems are operational"
```

### 定時任務範例
```bash
# 每天早上 9 點執行預設查詢，失敗會持續重試
0 9 * * * cd /home/sat/ntn-stack/claude-auto-query && ANTHROPIC_BASE_URL='...' ANTHROPIC_AUTH_TOKEN='...' ./claude_auto_query.sh

# 每小時執行健康檢查
0 * * * * cd /home/sat/ntn-stack/claude-auto-query && ANTHROPIC_BASE_URL='...' ANTHROPIC_AUTH_TOKEN='...' ./claude_auto_query.sh
```

## 📝 日誌管理

### 日誌檔案
- **claude_cron.log**: 主要執行日誌
- **claude_retry.log**: 重試系統詳細日誌
- **/home/sat/ntn-stack/logs/cron.log**: **成功時間記錄檔案** ⭐

### 常用指令
```bash
# 查看即時日誌
tail -f claude_cron.log
tail -f claude_retry.log

# 查看成功時間記錄 ⭐ 重要！
tail -f /home/sat/ntn-stack/logs/cron.log
cat /home/sat/ntn-stack/logs/cron.log

# 查看重試狀態
cat retry_state.json

# 查看當前 cron 任務
crontab -l
```

## ⏰ 成功時間記錄

### 📝 記錄格式
當查詢成功時，系統會自動在 `/home/sat/ntn-stack/logs/cron.log` 中記錄：

```
[2025-08-03 12:00:16] ✅ Claude 查詢成功 (首次) - 查詢: "OK"
[2025-08-03 14:30:45] ✅ Claude 查詢成功 (重試 2 次後) - 查詢: "請檢查系統狀態"
```

### 📊 記錄內容
- **時間戳**: 精確到秒的成功時間
- **狀態**: 首次成功 或 重試 N 次後成功
- **查詢內容**: 完整查詢 (超過100字元會截斷)

### 🔍 查看方式
```bash
# 查看所有成功記錄
cat /home/sat/ntn-stack/logs/cron.log

# 即時監控成功記錄
tail -f /home/sat/ntn-stack/logs/cron.log

# 統計成功次數
grep "查詢成功" /home/sat/ntn-stack/logs/cron.log | wc -l

# 查看今天的成功記錄
grep "$(date +%Y-%m-%d)" /home/sat/ntn-stack/logs/cron.log
```

## 🔧 進階管理

### 手動清除重試
```bash
# 移除所有重試任務
crontab -l | grep -v claude_retry_system | crontab -

# 清除重試狀態
rm -f retry_state.json
```

### 修改重試間隔
編輯 `claude_retry_system.py` 中的 `schedule_retry` 函數：
```python
# 當前: retry_count 小時後重試
next_run = datetime.now() + timedelta(hours=retry_count)

# 修改為: 固定 30 分鐘間隔
next_run = datetime.now() + timedelta(minutes=30)
```

### 自訂成功條件
修改 `claude_retry_system.py` 中的成功判斷：
```python
# 當前: 只認 "OK"
'is_ok_response': claude_response.upper() == 'OK'

# 修改為: 認 "完成" 或 "OK"
'is_ok_response': claude_response.upper() in ['OK', '完成', 'DONE']
```

## 🛡️ 安全考量

### 環境變數保護
```bash
# 設定在 ~/.bashrc 或 ~/.profile 中
echo 'export ANTHROPIC_BASE_URL="your_url"' >> ~/.bashrc
echo 'export ANTHROPIC_AUTH_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

### 日誌輪替
```bash
# 設定 logrotate 自動清理日誌
sudo tee /etc/logrotate.d/claude-auto-query << EOF
/home/sat/ntn-stack/claude-auto-query/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
