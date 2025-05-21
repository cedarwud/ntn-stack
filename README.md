# NTN-Stack: 非地面網絡 5G 通信系統

NTN-Stack 是一個為非地面網絡(NTN)場景優化的 5G 通信系統，專為高延遲環境下的衛星通信設計。本系統基於 Open5GS 核心網和 UERANSIM RAN 模擬器，針對衛星通信環境進行了深度優化。

## 項目概述

本項目旨在「完成一套可部署於 30 km 營級作戰範圍的 Two-Tier BLOS 通訊系統」，已實現以下關鍵功能：

-   **Open5GS 核心網優化** - 適配高延遲衛星通信環境（250ms-750ms）
-   **UERANSIM 動態配置機制** - 根據網絡環境動態調整參數
-   **完整的監控系統** - 全面的網絡監控和診斷能力
-   **自動化測試框架** - 確保系統功能穩定運行

## 系統架構

```
ntn-stack/
├── config/                    # 配置文件目錄
├── scripts/                   # 腳本目錄
│   ├── config/                # 配置生成腳本
│   ├── diagnostic/            # 網絡診斷腳本
│   ├── network/               # 網絡管理腳本
│   ├── proxy/                 # 代理服務腳本
│   ├── recovery/              # 自動恢復腳本
│   ├── startup/               # 系統啟動腳本
│   └── testing/               # 測試腳本
├── services/                  # 服務組件
│   ├── config_api/            # 配置API服務
│   ├── monitor_api/           # 監控API服務
│   └── proxy/                 # 代理服務
├── docker-compose.yml         # Docker容器配置
└── ONE.md                     # 項目詳細文檔
```

## 快速開始

### 系統啟動

```bash
# 啟動整個系統
./scripts/startup/ntn_setup.sh start

# 設置網絡模式（地面/LEO/MEO/GEO）
./scripts/startup/ntn_setup.sh mode leo

# 檢查系統狀態
./scripts/startup/ntn_setup.sh status
```

### 執行測試

```bash
# 執行所有測試並生成測試報告
./scripts/testing/run_all_tests.sh

# 測試特定模塊
./scripts/testing/test_ueransim_config.sh    # 測試UERANSIM動態配置
./scripts/testing/test_monitor_system.sh     # 測試監控系統
./scripts/testing/test_system_integration.sh # 測試系統整合
```

### 自動化測試報告解讀

執行測試後會生成標準格式報告，包含：

-   測試時間戳
-   各測試模塊結果
-   系統容器運行狀態
-   總體測試結果

測試報告格式示例：

```
===== 基礎 5G 網絡功能擴展測試報告 =====
測試時間: 2023-05-20 15:30:45

測試項目結果:
- UERANSIM動態配置機制: 通過
- 5G網絡監控系統: 通過
- 系統整合: 通過

系統狀態:
NAMES               STATUS
mongodb             Up 3 hours
open5gs-amf         Up 3 hours
open5gs-smf         Up 3 hours
...

總體結果: 通過 - 基礎 5G 網絡功能擴展已全部完成
```

## 測試腳本修復 (2023-12-01)

### 問題說明

我們發現測試腳本在執行過程中有以下問題：

1. 測試在 PDU 會話穩定性測試環節卡住不動
2. 需要使用 Ctrl+C 強制中斷測試
3. 報告中顯示部分測試未執行
4. 產生大量測試配置文件但未清理

### 解決方案

我們進行了以下修改：

1. **test_open5gs_config.sh**:
    - 確保所有 docker exec 命令不使用-it 參數，避免等待交互輸入
    - 為所有命令添加超時控制，防止命令卡住
2. **test_ueransim_config.sh**:
    - 改進配置文件查找邏輯，使用多種模式和多個目錄查找配置
    - 添加查找超時控制，避免卡在文件搜索過程
    - 改進腳本查找邏輯，支持多種可能位置
3. **test_subscriber_management.sh**:
    - 增加對多種容器命名支持
    - 支持多種 MongoDB 命令格式
    - 支持多種 IMSI 格式，增強兼容性
    - 添加多個網絡目標測試，提高成功率
4. **run_all_tests.sh**:
    - 增強清理功能，可徹底清理測試生成的文件
    - 改進測試運行機制，防止測試卡住
    - 添加日誌記錄，方便診斷問題
    - 增強超時控制，自動終止卡住的測試

### 使用方法

```bash
# 執行所有測試
./scripts/testing/run_all_tests.sh all

# 只執行必要測試
./scripts/testing/run_all_tests.sh essential

# 清理測試產生的文件
./scripts/testing/run_all_tests.sh clean
```

## 腳本分類

NTN-Stack 系統腳本已按照功能進行分類整理：

### 配置腳本 (`scripts/config/`)

-   `config_generator.py` - 生成配置文件
-   `apply_config.sh` - 應用配置到容器
-   `register_subscriber.sh` - 註冊用戶到核心網
-   `mongo_init.js` - MongoDB 初始化
-   `open5gs-dbctl` - Open5GS 資料庫控制工具

### 診斷腳本 (`scripts/diagnostic/`)

-   `network_diagnostic.sh` - 網絡診斷工具
-   `gtp_fix.sh` - GTP 通信修復工具
-   `fix_gtp_tunnel.sh` - GTP 隧道修復工具

### 網絡腳本 (`scripts/network/`)

-   `ntn_simulator.sh` - 衛星網絡環境模擬器
-   `network_bridge.sh` - 網絡橋接工具
-   `proxy_ue_traffic.sh` - UE 流量代理

### 代理腳本 (`scripts/proxy/`)

-   `setup_proxy_api.sh` - 設置代理 API 服務

### 恢復腳本 (`scripts/recovery/`)

-   `ntn_sat_ue_fix.sh` - 衛星環境 UE 連接修復
-   `ue_auto_recovery.sh` - UE 自動恢復工具

### 啟動腳本 (`scripts/startup/`)

-   `ntn_setup.sh` - 系統管理主腳本
-   `ntn_startup.sh` - 系統啟動流程
-   `ue_setup.sh` - UE 設置工具
-   `upf_setup.sh` - UPF 設置工具

### 測試腳本 (`scripts/testing/`)

-   `run_all_tests.sh` - 執行所有測試
-   `test_ueransim_config.sh` - 測試 UERANSIM 配置
-   `test_monitor_system.sh` - 測試監控系統
-   `test_system_integration.sh` - 測試系統整合
-   `performance_test.sh` - 性能測試工具

## 故障排除

如果測試未通過，請遵循以下故障排除流程：

1. 查看測試報告中的失敗項目
2. 檢查腳本執行過程中輸出的詳細錯誤信息
3. 查看相關容器的日誌：`docker logs <容器名稱>`
4. 使用診斷工具進行系統診斷：`./scripts/diagnostic/network_diagnostic.sh`
5. 嘗試重啟特定服務：`docker restart <容器名稱>`
6. 如果問題持續存在，可能需要重置系統：`./scripts/startup/ntn_setup.sh reset`

## 文檔

更詳細的系統文檔請參閱：

-   `ONE.md` - 詳細的系統設計和實現報告
-   `docker-compose.yml` - 容器配置文件
