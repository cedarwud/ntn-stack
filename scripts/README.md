# 🚀 TLE 數據自動下載工具

## 📝 功能描述

自動下載 Starlink 和 OneWeb 的 TLE 和 JSON 數據，支援：
- 智能日期命名（基於數據實際日期，非下載日期）
- 數據完整性驗證
- 智能更新檢查（避免重複下載）
- 自動備份管理和清理
- 詳細執行報告和錯誤處理

## 🕰️ 建議執行時間

**UTC 08:00 (台灣時間 16:00)**

原因：
- CelesTrak 在 UTC 00:00-06:00 更新數據
- UTC 08:00 後確保獲得最新數據
- 避開網路高峰期
- 台灣時間 16:00 適合手動執行

## 🚀 使用方法

### 📦 雙版本腳本說明

| 腳本版本 | 功能特點 | 檔案命名邏輯 |
|---------|---------|---------|
| `daily_tle_download_enhanced.sh` | **智能更新檢查 + 實際日期命名 + 自動備份清理** | **基於 TLE epoch 實際日期** |

**注意**：舊版基礎腳本已移除，統一使用增強版腳本。

### 基本執行
```bash
cd /home/u24/ntn-stack

# 標準執行 - 智能更新 + 實際日期命名 + 自動清理
./scripts/daily_tle_download_enhanced.sh
```

### 🔄 自動化功能
- **智能檔案命名**：基於數據實際日期而非下載日期
- **自動備份管理**：統一備份到 `backups/` 目錄
- **自動清理**：清理散落備份檔案和過期備份（保留7天）
- **重複檢測**：避免下載相同數據

### 增強版本高級選項
```bash
# 強制重新下載所有檔案
./scripts/daily_tle_download_enhanced.sh --force

# 不檢查更新，直接跳過已存在檔案
./scripts/daily_tle_download_enhanced.sh --no-update-check

# 不備份現有檔案
./scripts/daily_tle_download_enhanced.sh --no-backup

# 查看幫助
./scripts/daily_tle_download_enhanced.sh --help
```

## 📊 執行結果

### 成功執行範例
```
🚀 增強版 LEO 衛星 TLE 數據下載工具
📅 目標日期: 20250728 (UTC) - 下載日期
🕐 當前時間: 2025-07-28 08:00:00 UTC

==========================================
📊 增強版每日 TLE 數據下載報告
==========================================
✅ Starlink: 全部成功
✅ OneWeb: 全部成功

📁 本次下載的檔案: (基於數據實際日期命名)
  starlink/tle/starlink_20250727.tle        1,343,328 bytes
  starlink/json/starlink_20250727.json      3,343,319 bytes
  oneweb/tle/oneweb_20250727.tle              109,368 bytes
  oneweb/json/oneweb_20250727.json            270,055 bytes

💾 備份檔案: (自動備份到 backups/20250728/)
  starlink_20250727.tle.backup
  starlink_20250727.json.backup
  oneweb_20250727.tle.backup
  oneweb_20250727.json.backup
==========================================
```

## 📁 檔案命名格式

**重要更新**：檔案名稱現在基於**數據實際日期**而非下載日期

```
tle_data/
├── starlink/
│   ├── tle/starlink_20250727.tle     # 基於 TLE epoch 的實際日期
│   └── json/starlink_20250727.json   # 與 TLE 使用相同日期
└── oneweb/
    ├── tle/oneweb_20250727.tle       # 基於 TLE epoch 的實際日期
    └── json/oneweb_20250727.json     # 與 TLE 使用相同日期
```

### 📅 智能日期命名邏輯
- **自動提取實際日期**：從 TLE 數據的 epoch 欄位提取真實的軌道數據日期
- **檔案名稱一致性**：檔案名稱準確反映數據內容的實際日期
- **避免混淆**：不再使用下載日期，消除檔案名與數據內容不符的問題
- **範例**：下載日期 2025-07-28，但數據實際日期是 2025-07-27，檔案名為 `starlink_20250727.tle`

## 🔄 智能更新檢查機制（增強版專屬）

### 📋 檔案更新判斷邏輯
增強版腳本解決了「當天檔案已存在但可能有更新數據」的問題：

1. **HTTP 標頭檢查**：比較遠端檔案的 `Last-Modified` 和 `Content-Length`
2. **本地檔案比對**：檢查本地檔案大小和修改時間
3. **智能決策**：
   - 檔案大小不同 → 立即更新
   - 遠端檔案較新 → 立即更新  
   - 檔案相同且最新 → 跳過下載

### 🛡️ 安全備份機制
- **自動備份**：更新前備份現有檔案到 `tle_data/backups/下載日期/`
- **原子操作**：先下載到臨時檔案，驗證通過後才覆蓋
- **失敗恢復**：驗證失敗時自動恢復備份檔案
- **自動清理**：保留最近7天的備份，自動刪除過期備份

### 🎯 實際應用場景
```bash
# 場景1：早上8點首次下載
./scripts/daily_tle_download_enhanced.sh
# 結果：下載新檔案

# 場景2：下午再次執行，CelesTrak有更新
./scripts/daily_tle_download_enhanced.sh  
# 結果：檢測到更新，備份舊檔案並下載新版本

# 場景3：晚上再次執行，無更新
./scripts/daily_tle_download_enhanced.sh
# 結果：檢測到檔案最新，跳過下載
```

## 🔍 數據驗證機制

### TLE 數據驗證
- 檢查檔案格式（第2、3行必須以"1 "和"2 "開頭）
- 驗證 epoch 年份是否合理
- 確認衛星數量 > 0
- 檢查檔案大小 > 100 bytes

### JSON 數據驗證
- 驗證 JSON 格式正確性
- 確認數組長度 > 0
- 檢查第一個元素的 EPOCH 欄位
- 確認檔案大小合理

## 📝 日誌功能

### 日誌位置
```
/home/sat/ntn-stack/logs/tle_download.log
```

### 日誌內容
- 下載開始/結束時間
- 成功/失敗狀態
- 檔案大小和衛星數量
- 錯誤訊息和警告

### 查看日誌
```bash
# 查看最新日誌
tail -f /home/sat/ntn-stack/logs/tle_download.log

# 查看今天的日誌
grep "$(date -u '+%Y-%m-%d')" /home/sat/ntn-stack/logs/tle_download.log

# 查看錯誤日誌
grep "ERROR" /home/sat/ntn-stack/logs/tle_download.log
```

## 🛠️ 故障排除

### 常見問題

#### 1. 網路連接失敗
```bash
# 檢查網路連接
ping celestrak.org
curl -I https://celestrak.org
```

#### 2. 檔案更新檢查（增強版）
```bash
# 如果懷疑更新檢查有問題，可以：

# 強制重新下載
./scripts/daily_tle_download_enhanced.sh --force

# 手動檢查遠端檔案信息
curl -I https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle

# 比較本地檔案時間（注意：檔案名基於數據實際日期，非當前日期）
find tle_data/starlink/tle/ -name "starlink_*.tle" -exec stat {} \;
```

#### 3. 檔案已存在
- 腳本會進行智能更新檢查
- 如需強制重新下載，使用 `--force` 參數

#### 4. 數據驗證失敗
- 腳本會自動刪除驗證失敗的檔案
- 檢查日誌了解具體失敗原因

#### 5. 權限問題
```bash
# 確保腳本可執行
chmod +x /home/sat/ntn-stack/scripts/daily_tle_download.sh
chmod +x /home/sat/ntn-stack/scripts/daily_tle_download_enhanced.sh

# 確保目錄可寫
chmod 755 /home/sat/ntn-stack/tle_data
```

## 📈 使用建議

### 每日執行流程（推薦使用增強版）
1. **UTC 08:00** 執行增強版腳本 `./scripts/daily_tle_download_enhanced.sh`
2. 檢查執行報告確認成功
3. 如有失敗，查看日誌並重新執行  
4. **可重複執行**：一天內多次執行會自動檢查更新
5. 定期備份 tle_data 目錄（增強版有自動備份功能）

### 自動化選項
可以設定 cron job 自動執行：
```bash
# 編輯 crontab
crontab -e

# 每日自動執行
0 8 * * * /home/u24/ntn-stack/scripts/daily_tle_download_enhanced.sh >> /home/u24/ntn-stack/logs/cron.log 2>&1
```

### 數據備份
```bash
# 每週備份數據
tar -czf "tle_backup_$(date +%Y%m%d).tar.gz" tle_data/

# 同步到遠端
rsync -av tle_data/ backup_server:/path/to/backup/
```

## 🔧 自動化管理

### 備份管理
- **自動備份**：每次更新前自動備份到 `backups/下載日期/`
- **自動清理**：保留最近7天的備份，自動刪除過期備份
- **統一管理**：所有備份集中在 `backups/` 目錄，不再散落各處

## 🎯 使用建議

1. **每日例行下載**：直接執行腳本，自動處理所有細節
2. **強制更新**：使用 `--force` 參數強制重新下載
3. **自動維護**：腳本會自動清理備份，無需手動維護
4. **生產環境**：提供完整的錯誤處理、日誌記錄和備份機制

## 🎯 下一步

執行腳本後，收集的數據將自動支援：
- RL 強化學習訓練數據生成
- 軌道演化分析
- Starlink vs OneWeb 對比研究
- 學術論文數據來源

---

**🎯 目標**: 每天收集高品質的 LEO 衛星軌道數據，支援換手優化研究