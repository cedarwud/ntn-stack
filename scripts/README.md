# 🚀 TLE 數據自動下載工具

生產級 LEO 衛星軌道數據收集系統，支援 Starlink 和 OneWeb。

## 🎯 核心特點
- **🤖 全自動排程**: 6 小時間隔，智能更新檢查
- **📅 精確命名**: 基於軌道數據實際日期（非下載日期）
- **🛡️ 生產可靠**: 自動備份、錯誤恢復、日誌管理
- **🚫 API 友善**: 避免頻繁請求被 CelesTrak 封鎖

## ⚡ 快速開始

### 🚀 一鍵啟用（推薦）
```bash
# 1. 安裝自動排程（每 6 小時執行）
./scripts/tle_cron_scheduler.sh install

# 2. 檢查狀態
./scripts/tle_cron_scheduler.sh status

# 3. 測試下載
./scripts/tle_cron_scheduler.sh test
```

### ⏰ 自動執行時間
- **排程**: 每天 02:00, 08:00, 14:00, 20:00 (UTC)
- **頻率**: 每 6 小時（最佳實踐，避免 API 限制）
- **更新策略**: 只在數據更新時下載

### 🔧 管理命令
```bash
./scripts/tle_cron_scheduler.sh remove     # 移除排程
./scripts/tle_cron_scheduler.sh logs 50    # 查看日誌
./scripts/tle_cron_scheduler.sh rotate     # 日誌輪替
./scripts/tle_cron_scheduler.sh help       # 完整說明
```

## 📅 Cron 排程詳解

### 🎯 預設排程設定
```bash
# TLE 數據自動下載（每 6 小時執行一次）
# 分別在 02:00, 08:00, 14:00, 20:00 執行
0 2,8,14,20 * * * /path/to/daily_tle_download_enhanced.sh >> /path/to/logs/tle_download.log 2>> /path/to/logs/tle_error.log
```

### 📋 Cron 時間格式說明
```
分鐘 小時 日期 月份 星期 命令
 │    │   │   │   │
 │    │   │   │   └─── 星期幾 (0-7, 0或7是星期日)
 │    │   │   └────── 月份 (1-12)
 │    │   └─────────── 日期 (1-31)
 │    └────────────── 小時 (0-23)
 └─────────────────── 分鐘 (0-59)
```

### ⏰ 常見時間設定範例
| 描述 | Cron 表達式 | 說明 |
|------|-------------|------|
| 每 6 小時 | `0 */6 * * *` | 00:00, 06:00, 12:00, 18:00 |
| 每 4 小時 | `0 */4 * * *` | 每 4 小時執行一次 |
| 特定時間 | `0 2,8,14,20 * * *` | 02:00, 08:00, 14:00, 20:00 |
| 每天一次 | `0 8 * * *` | 每天 08:00 執行 |
| 工作日執行 | `0 8 * * 1-5` | 週一到週五 08:00 執行 |

### 🛠️ 手動 Cron 管理
```bash
# 編輯 cron 表
crontab -e

# 查看當前 cron 任務
crontab -l

# 刪除所有 cron 任務
crontab -r

# 查看 cron 服務狀態
sudo systemctl status cron

# 重啟 cron 服務
sudo systemctl restart cron
```

### 📊 頻率建議與限制
- **🎯 推薦頻率**: 6 小時（02:00, 08:00, 14:00, 20:00 UTC）
- **⚠️ 最小間隔**: 不少於 4 小時（避免被 CelesTrak API 封鎖）
- **❌ 不建議**: 每小時或更頻繁（可能被 API 限制）
- **💡 最佳時間**: UTC 08:00 後（CelesTrak 在 00:00-06:00 更新數據）

## 🖥️ WSL 環境特殊設定

### ⚠️ WSL Cron 運行條件（重要！）
**WSL 中的 cron 服務需要滿足以下條件才能正常運行：**

1. **WSL 實例必須處於運行狀態**
   - WSL 關閉時，所有 cron 任務停止
   - 電腦休眠/關機時，cron 無法執行

2. **Cron 服務必須手動啟動**
   ```bash
   # 檢查 cron 服務狀態
   sudo service cron status
   
   # 啟動 cron 服務（每次 WSL 重啟後需要執行）
   sudo service cron start
   
   # 設定開機自動啟動（推薦）
   echo 'sudo service cron start' >> ~/.bashrc
   ```

3. **網路連接必須可用**
   - 需要能夠訪問 `celestrak.org`
   - 防火牆或代理設定可能影響下載

### 🔄 自動啟動 Cron 服務
```bash
# 方法1: 加入 .bashrc（每次開啟終端時啟動）
echo 'sudo service cron start > /dev/null 2>&1' >> ~/.bashrc

# 方法2: 創建啟動腳本
cat > ~/start-cron.sh << 'EOF'
#!/bin/bash
sudo service cron start
echo "Cron service started"
EOF
chmod +x ~/start-cron.sh
```

### 💡 WSL 使用建議

#### 🎯 最佳實踐
1. **保持 WSL 運行**: 
   - 不要完全關閉 WSL
   - 可以關閉 VSCode，但保持 WSL 實例運行

2. **檢查運行狀態**:
   ```bash
   # 檢查 WSL 是否運行
   wsl --list --running
   
   # 檢查 cron 服務
   sudo service cron status
   
   # 檢查排程任務
   ./scripts/tle_cron_scheduler.sh status
   ```

### 🚨 常見問題排解

| 問題 | 症狀 | 解決方案 |
|------|------|----------|
| **Cron 未執行** | 排程時間到了但沒有執行 | `sudo service cron start` |
| **WSL 自動關閉** | 一段時間後 WSL 自動休眠 | 設定 Windows 電源管理，保持 WSL 運行 |
| **網路問題** | 下載失敗 | 檢查防火牆、代理設定 |
| **權限問題** | 無法寫入日誌或數據 | 檢查文件夾權限 `chmod 755` |

### 🎯 實際使用場景

#### ✅ 可以正常運行
- 開啟 WSL，關閉 VSCode
- 電腦正常使用，WSL 在背景運行
- 設定 `.bashrc` 自動啟動 cron 服務

#### ❌ 會停止運行  
- 完全關閉 WSL
- 電腦休眠/關機
- 重啟 WSL 但忘記啟動 cron 服務

### 💡 最佳實踐建議
```bash
# 設定自動啟動 cron（推薦）
echo 'sudo service cron start > /dev/null 2>&1' >> ~/.bashrc

# 檢查 WSL 和 cron 狀態
wsl --list --running
sudo service cron status
./scripts/tle_cron_scheduler.sh status
```

### 📝 重要提醒
- **❌ 不需要 VSCode 開啟**: 只要 WSL 實例運行即可
- **⚠️ 電腦可以休眠**: 但 WSL 會暫停，cron 也會暫停
- **🔄 重啟後重新設定**: 每次重啟 WSL 後需要重新啟動 cron 服務

## 📦 系統架構

| 腳本 | 功能 |
|------|------|
| `tle_cron_scheduler.sh` | **排程管理系統** - cron 設置、日誌管理、狀態監控 |
| `daily_tle_download_enhanced.sh` | **核心下載引擎** - 智能更新、實際日期命名、自動備份 |

## 🔄 智能更新機制
- **HTTP 標頭檢查**: 比較遠端 `Last-Modified` 和 `Content-Length`
- **本地檔案比對**: 大小和修改時間比較
- **智能決策**: 只在數據更新時下載，避免重複請求
- **自動備份**: 更新前備份，失敗自動恢復

## 🛠️ 手動執行選項

### 下載引擎選項
```bash
./scripts/daily_tle_download_enhanced.sh --force        # 強制重新下載
./scripts/daily_tle_download_enhanced.sh --no-backup   # 不備份現有檔案
./scripts/daily_tle_download_enhanced.sh --help        # 查看所有選項
```

### 最佳執行時間
**UTC 08:00 (台灣 16:00)** - CelesTrak 在 UTC 00:00-06:00 更新，此時確保獲得最新數據

## 📁 檔案結構

基於**軌道數據實際日期**命名（非下載日期）：

```
tle_data/
├── starlink/
│   ├── tle/starlink_20250802.tle     # 基於 TLE epoch 實際日期
│   └── json/starlink_20250802.json   # 與 TLE 使用相同日期
├── oneweb/
│   ├── tle/oneweb_20250802.tle
│   └── json/oneweb_20250802.json
└── backups/
    └── 20250803/                     # 按日期組織的備份目錄
        ├── starlink_20250802.tle.old
        └── oneweb_20250802.json.old
```

## 📊 執行結果範例

### 排程狀態檢查
```bash
$ ./scripts/tle_cron_scheduler.sh status

===== TLE 下載排程狀態 =====
✅ 排程狀態: 已啟用

Cron 條目:
0 2,8,14,20 * * * /path/to/daily_tle_download_enhanced.sh

日誌文件: tle_download.log (2.1K, 最後修改: 2025-08-03 08:00:15)
錯誤日誌: 尚未創建

下次執行時間:
  今天: 2025-08-03 14:00, 20:00
  明天: 2025-08-04 02:00
============================
```

### 下載執行結果
```
===== TLE 數據下載完成 =====
✅ Starlink: 已下載/更新
  📥 新下載檔案:
    • Starlink TLE: starlink_20250802.tle
    • Starlink JSON: starlink_20250802.json

✅ OneWeb: 已下載/更新
  📥 新下載檔案:
    • OneWeb TLE: oneweb_20250802.tle
    • OneWeb JSON: oneweb_20250802.json
=============================
```

## 📈 數據驗證機制

### TLE 數據驗證
- **格式檢查**: 驗證 TLE 標準格式（Line 1/2 格式）
- **Epoch 驗證**: 檢查年份和天數有效性
- **衛星數量**: 確認下載的衛星數量合理

### JSON 數據驗證
- **語法檢查**: 確保 JSON 格式正確
- **數組長度**: 驗證衛星數據數量
- **EPOCH 欄位**: 檢查時間戳有效性

### 安全備份策略
- **更新前備份**: 自動備份到 `tle_data/backups/日期/`
- **原子操作**: 臨時文件→驗證→覆蓋
- **失敗恢復**: 驗證失敗時自動恢復
- **自動清理**: 保留 7 天備份，過期自動刪除

## 📝 日誌系統

### 自動日誌管理
- **執行日誌**: `/logs/tle_scheduler/tle_download.log`
- **錯誤日誌**: `/logs/tle_scheduler/tle_error.log`
- **自動輪替**: 超過 1MB 自動壓縮歸檔
- **自動清理**: 保留 30 天壓縮日誌

### 查看日誌
```bash
./scripts/tle_cron_scheduler.sh logs      # 最近 20 行
./scripts/tle_cron_scheduler.sh logs 50   # 指定行數
```

## 🛠️ 故障排除

### 快速診斷
```bash
./scripts/tle_cron_scheduler.sh status    # 檢查排程狀態
./scripts/tle_cron_scheduler.sh logs 50   # 查看錯誤日誌
./scripts/tle_cron_scheduler.sh test      # 測試下載功能
```

### 常見問題

| 問題 | 解決方法 |
|------|----------|
| **排程未執行** | `sudo systemctl status cron`<br>重新安裝: `remove` → `install` |
| **網路連接失敗** | `ping celestrak.org`<br>`curl -I https://celestrak.org` |
| **強制重新下載** | `--force` 參數或 `test` 命令 |
| **權限問題** | `chmod +x scripts/*.sh`<br>`chmod 755 tle_data/` |

## 📈 最佳實踐

### 🎯 推薦工作流程

#### 生產環境
```bash
./scripts/tle_cron_scheduler.sh install   # 一次設置
./scripts/tle_cron_scheduler.sh status    # 定期監控
./scripts/tle_cron_scheduler.sh logs      # 問題排查
```

#### 開發環境
```bash
./scripts/tle_cron_scheduler.sh test      # 測試下載
./scripts/daily_tle_download_enhanced.sh --force  # 強制更新
```

### 🔧 維護建議
- **日誌輪替**: 自動執行，可手動 `rotate`
- **數據備份**: 系統自動備份，可額外手動備份
- **監控頻率**: 每週檢查狀態和日誌
- **API 限制**: 最小間隔 4 小時，推薦 6 小時

---

## 🎯 使用場景

### 新用戶（推薦）
```bash
./scripts/tle_cron_scheduler.sh install   # 一鍵啟用
./scripts/tle_cron_scheduler.sh test      # 驗證運行
./scripts/tle_cron_scheduler.sh status    # 檢查狀態
```

### 升級用戶
```bash
crontab -e  # 手動移除舊條目
./scripts/tle_cron_scheduler.sh install   # 安裝新系統
```

---

**🎯 目標**: 全自動收集高品質 LEO 衛星軌道數據，支援 LEO 衛星切換學術研究  
**🆕 特色**: 學術研究級自動化系统，支援碩士論文研究數據需求

## 🎓 學術研究支援

### 數據品質保證
- **研究級精度**: TLE 數據基於實際軌道歷程，非模擬數據
- **時間一致性**: 所有數據使用統一時間戳，確保實驗可重現性
- **數據完整性**: 自動驗證機制確保下載數據的完整性和正確性

### 論文研究價值
- **真實數據源**: 來自 CelesTrak 官方數據，具備學術引用價值
- **可重現性**: 基於固定時間點的歷史數據，支援研究結果重現
- **標準合規**: 符合 3GPP NTN 標準的衛星星座配置

### 與主系統整合
- **自動觸發**: TLE 數據更新後自動觸發 SimWorld 預處理
- **Docker 整合**: 數據自動同步到容器內，支援即時研究需求
- **API 準備**: 更新完成後立即可用於算法測試和性能評估

## 📊 研究數據統計

### 當前支援星座
| 星座 | 衛星數量 | 更新頻率 | 軌道高度 | 研究價值 |
|------|---------|---------|---------|----------|
| **Starlink** | ~8,000 顆 | 每 6 小時 | 340-570 km | ⭐⭐⭐⭐⭐ 主要研究對象 |
| **OneWeb** | ~650 顆 | 每 6 小時 | 1,200 km | ⭐⭐⭐⭐ 對比研究 |

### 數據覆蓋範圍
- **全球覆蓋**: 支援不同地理位置的衛星可見性研究
- **時間連續**: 提供 24/7 連續軌道數據
- **精度等級**: 米級位置精度，適合學術研究需求

---

**研究應用**: 支援 LEO 衛星切換優化碩士論文，提供可靠的實驗數據基礎