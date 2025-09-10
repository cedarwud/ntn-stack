# TLE 數據管理腳本集合

這個目錄包含了完整的 TLE (Two-Line Element) 數據管理工具，支援自動下載、更新檢查、數據清理和增量處理。

## 🚀 核心腳本

### 1. tle_cron_scheduler.sh - 排程管理系統
**用途**: 設置和管理 TLE 數據自動下載排程（每6小時執行一次）

```bash
# 安裝排程（每天 02:00, 08:00, 14:00, 20:00 執行）
./tle_cron_scheduler.sh install

# 檢查排程狀態
./tle_cron_scheduler.sh status

# 手動測試下載
./tle_cron_scheduler.sh test

# 查看日誌
./tle_cron_scheduler.sh logs 50

# 移除排程
./tle_cron_scheduler.sh remove
```

### 2. daily_tle_download_enhanced.sh - 核心下載引擎
**用途**: 智能下載 Starlink 和 OneWeb TLE 數據，支援更新檢查和自動備份

```bash
# 正常下載（智能更新檢查）
./daily_tle_download_enhanced.sh

# 強制重新下載
./daily_tle_download_enhanced.sh --force

# 不檢查更新
./daily_tle_download_enhanced.sh --no-update-check

# 不備份現有檔案
./daily_tle_download_enhanced.sh --no-backup
```

**特色功能**:
- 基於 TLE epoch 實際日期命名檔案
- 智能更新檢查（比較檔案大小和修改時間）
- 自動備份舊檔案到 `tle_data/backups/日期/`
- 完整的驗證和錯誤處理

### 3. incremental_data_processor.sh - 增量更新處理器
**用途**: 檢測 TLE 數據變更並觸發增量衛星軌道重計算

```bash
# 智能增量處理
./incremental_data_processor.sh

# 檢查模式（只分析不處理）
./incremental_data_processor.sh --check-only
```

**功能**:
- 檢測 TLE 檔案變更
- 只重新計算變更的衛星數據
- 觸發相應的數據處理管道

### 4. intelligent_data_cleanup.sh - 智能數據清理
**用途**: 清理過期的 TLE 檔案和日誌，維護系統存儲效率

```bash
# 執行智能清理
./intelligent_data_cleanup.sh

# 查看清理策略
./intelligent_data_cleanup.sh --show-strategy

# 緊急清理模式
./intelligent_data_cleanup.sh --emergency
```

**清理策略**:
- Starlink TLE: 保留 30 天，最多 50 個檔案
- OneWeb TLE: 保留 30 天，最多 30 個檔案
- 備份檔案: 保留 7 天
- 日誌檔案: 保留 15 天

## 📁 數據組織結構

```
tle_data/
├── starlink/
│   ├── tle/starlink_20250802.tle     # 基於 TLE epoch 實際日期
│   └── json/starlink_20250802.json   # 與 TLE 使用相同日期
├── oneweb/
│   ├── tle/oneweb_20250802.tle
│   └── json/oneweb_20250802.json
└── backups/
    └── 20250802/
        ├── starlink_20250801.tle.old
        └── oneweb_20250801.tle.old
```

## 🔄 典型工作流程

### 自動化設置（推薦）
```bash
# 1. 安裝自動排程
./tle_cron_scheduler.sh install

# 2. 驗證運行
./tle_cron_scheduler.sh test

# 3. 監控狀態
./tle_cron_scheduler.sh status
```

### 手動管理
```bash
# 1. 手動下載最新數據
./daily_tle_download_enhanced.sh

# 2. 處理增量更新
./incremental_data_processor.sh

# 3. 定期清理
./intelligent_data_cleanup.sh
```

# 檢查現有數據
./tle_cron_scheduler.sh status
./tle_cron_scheduler.sh logs 100
```

## ⚙️ 容器化集成

這些腳本完全兼容容器化環境：

```dockerfile
# 在 Dockerfile 中
COPY scripts/tle_management/ /app/scripts/tle_management/
RUN chmod +x /app/scripts/tle_management/*.sh

# Volume 掛載
VOLUME ["/app/data/tle_data"]
```

## 📊 監控和診斷

### 日誌位置
- **執行日誌**: `/logs/tle_scheduler/tle_download.log`
- **錯誤日誌**: `/logs/tle_scheduler/tle_error.log`
- **增量處理日誌**: `/logs/tle_scheduler/incremental_processor.log`

### 健康檢查
```bash
# 檢查數據完整性
ls -la tle_data/*/tle/*.tle | wc -l  # 應該有檔案

# 檢查最新數據日期
find tle_data/ -name "*.tle" -printf '%T+ %p\n' | sort -r | head -5

# 檢查排程狀態
./tle_cron_scheduler.sh status
```

## 🛡️ 安全和權限

- 所有腳本使用 `set -euo pipefail` 嚴格錯誤處理
- 支援原子性檔案操作（臨時檔案 + 移動）
- 自動備份機制防止數據丟失
- 完整的日誌記錄用於審計

## 🔧 自定義配置

可以通過環境變數自定義行為：

```bash
# GitHub 配置
export GITHUB_TLE_REPO="myuser/tle-data"
export GITHUB_TLE_BRANCH="production"
export GITHUB_TLE_TOKEN="ghp_xxxxxxxxxxxx"

# 清理配置
export TLE_RETENTION_DAYS=45
export MAX_TLE_FILES=100
```

---
**重要**: 這些腳本是衛星處理系統的基礎設施，負責提供高質量的軌道數據給六階段處理管道使用。