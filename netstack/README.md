make dev-up
make test-connectivity
make test-e2e
make test-performance
make test-slice-switch
make test-ntn-latency
make test-ueransim-config
make test-ntn-config-validation
make test-quick-ntn-validation

✅ 使用 make setup-development 進行日常開發
✅ 用戶資料會自動保留，無需重新註冊
✅ 如果遇到問題，make fix-connectivity 自動修復
✅ 完全掌控何時清理數據 (make clean-data-only)

日常開發流程 (推薦)

# 第一次設置

make setup-development

# 日常重啟 (保留用戶資料)

make clean-keep-data && make up && make start-ran

# 如果連線有問題

make fix-connectivity

完全重置流程 (僅在必要時)

# 完全清理並重新設置

make setup-fresh

快速排查流程

# 診斷問題

make diagnose

# 如果有問題，自動修復

make fix-connectivity

1. 新增分層清理命令

# 🛠️ 日常開發使用 (保留數據)

make clean-keep-data

# 🆕 完全清理 (僅在必要時)

make clean

# 🗑️ 僅清理數據 (選擇性)

make clean-data-only

2. 完整工作流程命令

# 🛠️ 開發環境設置 (推薦日常使用)

make setup-development

# 🆕 全新環境設置 (首次使用或完全清理後)

make setup-fresh

# ✅ 驗證環境

make verify-setup 3. 智能診斷與修復

# 🔍 自動診斷問題

make diagnose

# 🔧 一鍵修復連線問題

make fix-connectivity

make down-v # 清理
make up # 啟動核心服務  
make start-ran # 啟動 RAN 模擬器
make register-subscribers # 註冊用戶
make test-connectivity # 測試 UE 網路連線
make test-e2e # 完整 API 業務流程
make test-performance # 系統效能
make test-slice-switch # 網路切片切換
make down-v # 完全清理
make up # 啟動核心服務  
make start-ran # 啟動 RAN 模擬器
make test-ntn-latency # NTN 高延遲場景測試
make test-ueransim-config # UERANSIM 動態配置測試
make test-ntn-config-validation # NTN 配置驗證測試
make test-quick-ntn-validation # 快速功能驗證

# NetStack v1.0 - Open5GS + UERANSIM 雙 Slice 核心網堆疊

🚀 **一鍵部署的 5G 核心網與 RAN 模擬器，支援 eMBB／uRLLC／mMTC 三切片架構**

## 📋 專案概述

NetStack 是基於 [Open5GS](https://github.com/open5gs/open5gs) 和 [UERANSIM](https://github.com/aligungr/UERANSIM) 的完整 5G 核心網堆疊，提供：

-   **三 Network Slice 支援**：eMBB (sst=1, sd=0x111111)、uRLLC (sst=2, sd=0x222222) 和 mMTC (sst=3, sd=0x333333)
-   **FastAPI 管理介面**：RESTful API 用於 UE 管理和 Slice 切換
-   **容器化部署**：`docker compose up -d` 一鍵啟動
-   **自動化測試**：E2E 測試腳本與效能指標收集
-   **CI/CD 整合**：GitHub Actions 自動化建置與部署

## 🏗️ 架構設計

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SimWorld      │◄──►│   NetStack API   │◄──►│   Open5GS Core  │
│   (外部系統)     │    │   (FastAPI)      │    │   (5GC Network) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   監控與指標     │    │   UERANSIM RAN  │
                       │   (Prometheus)   │    │   (gNB + UE)    │
                       └──────────────────┘    └─────────────────┘
```

### 核心組件

-   **Open5GS 5GC**：AMF, SMF, UPF, NSSF, PCF, UDM, UDR, AUSF, BSF, NRF, SCP
-   **UERANSIM**：模擬 gNodeB 和 UE 設備
-   **NetStack API**：基於 Hexagonal Architecture 的管理 API
-   **MongoDB**：用戶資料庫與配置儲存
-   **Prometheus**：效能指標收集

## 🚀 快速開始

### 前置需求

-   Docker 24.0+
-   Docker Compose 2.0+
-   Linux 系統 (推薦 Ubuntu 22.04+)

### 1. 啟動 NetStack

```bash
# 複製專案
git clone https://github.com/yourlorg/netstack.git
cd netstack

# 🆕 全新環境 (首次使用或需要完全清理)
make setup-fresh

# 🛠️ 開發環境 (保留數據庫資料，適合日常開發)
make setup-development

# ✅ 驗證環境是否正確設置
make verify-setup
```

### 2. 日常開發流程

```bash
# 保留數據的重啟 (推薦用於日常開發)
make clean-keep-data && make up && make start-ran

# 如果 UE 連線失敗，重新註冊用戶 (會自動重啟相關服務)
make register-subscribers

# 測試連線
make test-connectivity
```

### 3. 完全清理 (僅在必要時使用)

```bash
# ⚠️ 注意：這會刪除所有數據，包括用戶註冊資料
make clean

# 清理後需要重新設置
make setup-fresh
```

### 4. API 介面

NetStack API 可在 http://localhost:8080 取得：

-   **Swagger UI**: http://localhost:8080/docs
-   **健康檢查**: http://localhost:8080/health
-   **指標端點**: http://localhost:9090/metrics

## 📋 API 端點

### 🏥 健康檢查

```http
GET /health
```

### 👤 UE 管理

```http
# 取得 UE 資訊
GET /api/v1/ue/{imsi}

# 取得 UE 統計
GET /api/v1/ue/{imsi}/stats
```

### 🔀 Slice 管理

```http
# 切換 UE Slice
POST /api/v1/slice/switch
Content-Type: application/json

{
  "imsi": "999700000000001",
  "target_slice": "uRLLC"  // 可選 "eMBB", "uRLLC" 或 "mMTC"
}
```

## 📊 測試與驗證

### 效能指標

| 指標     | eMBB   | uRLLC   | mMTC   | 說明             |
| -------- | ------ | ------- | ------ | ---------------- |
| RTT      | ~100ms | <50ms   | ~200ms | 往返延遲         |
| 頻寬     | 高     | 中等    | 低     | 資料傳輸率       |
| 可靠性   | 99%    | 99.999% | 95%    | 封包成功率       |
| 連接密度 | 中     | 低      | 超高   | 每平方公里設備數 |
| 能源效率 | 中     | 高      | 超高   | 設備電池壽命     |

### 測試腳本

```bash
# 完整 E2E 測試
./tests/e2e_netstack.sh

# 效能測試
./tests/performance_test.sh

# Slice 切換測試
./tests/slice_switching_test.sh
```

## 🛠️ 開發指南

### 專案結構

```
netstack/
├── compose/                # Docker Compose 配置
│   ├── core.yaml          # 核心網服務
│   ├── ran.yaml           # RAN 模擬器
│   └── dev.yaml           # 開發環境
├── docker/                # Dockerfile 與建置腳本
├── netstack_api/          # FastAPI 源碼
│   ├── adapters/          # 外部服務適配器
│   ├── services/          # 業務邏輯層
│   ├── models/            # 資料模型
│   └── main.py           # 應用程式入口
├── config/                # Open5GS 配置檔
├── scripts/               # 自動化腳本
├── tests/                 # 測試程式碼
│   ├── unit/             # 單元測試
│   ├── integration/      # 整合測試
│   └── e2e/              # 端到端測試
└── docs/                 # 文件
```

### 本地開發

```bash
# 安裝開發依賴
pip install -r requirements-dev.txt

# 啟動開發環境
make dev-up

# 執行單元測試
make test-unit

# 程式碼檢查
make lint
```

## 🔧 配置說明

### Network Slice 配置

在 `config/amf.yaml` 中定義的雙 Slice：

```yaml
plmn_support:
    - plmn_id:
          mcc: 999
          mnc: 70
      s_nssai:
          - sd: 0x111111 # eMBB Slice
            sst: 1
          - sd: 0x222222 # uRLLC Slice
            sst: 2
          - sd: 0x333333 # mMTC Slice
            sst: 3
```

### UE 註冊

透過 `scripts/register_subscriber.sh` 註冊用戶：

```bash
# eMBB 用戶 (IMSI: 999700000000001-003)
# uRLLC 用戶 (IMSI: 999700000000011-013)
# mMTC 用戶 (IMSI: 999700000000021-023)
# 衛星-無人機用戶 (IMSI: 999700000000050-052)
```

## 📈 監控與指標

### Prometheus 指標

-   `netstack_slice_rtt_seconds` - Slice RTT 延遲
-   `netstack_ue_attach_total` - UE 連接統計
-   `netstack_slice_switch_total` - Slice 切換次數

### 查看即時指標

```bash
# Prometheus Web UI
open http://localhost:9090

# 查看 API 指標
curl http://localhost:8080/metrics
```

## 🚢 部署與整合

### 與 SimWorld 整合

```bash
# 拉取 NetStack 映像
docker pull ghcr.io/yourorg/netstack:latest

# 在 SimWorld compose 中引用
services:
  netstack-api:
    image: ghcr.io/yourorg/netstack:latest
    environment:
      - DATABASE_URL=mongodb://mongo:27017/open5gs
    ports:
      - "8080:8080"
```

### 生產環境部署

```bash
# 使用 Helm Chart (Kubernetes)
helm install netstack ./charts/netstack

# 或使用 Docker Swarm
docker stack deploy -c compose/production.yaml netstack
```

## 🔍 疑難排解

### 常見問題

1. **UE 無法連接**

    ```bash
    # 檢查核心網狀態
    make status

    # 查看日誌
    docker compose logs amf
    ```

2. **Slice 切換失敗**

    ```bash
    # 檢查 NSSF 配置
    docker compose logs nssf

    # 驗證用戶配置
    make show-subscribers
    ```

3. **API 無回應**

    ```bash
    # 重啟 API 服務
    docker compose restart netstack-api

    # 檢查健康狀態
    curl http://localhost:8080/health
    ```

## 📚 文件與資源

-   [架構設計文件](docs/architecture.md)
-   [API 規格文件](docs/api.md)
-   [測試結果解讀指南](docs/how_to_read_tests.md)
-   [貢獻指南](CONTRIBUTING.md)

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！請閱讀 [貢獻指南](CONTRIBUTING.md) 了解詳細資訊。

## 📄 授權

本專案採用 [Apache License 2.0](LICENSE) 授權。

## 📞 聯絡方式

-   **技術支援**: netstack-support@yourorg.com
-   **Issue 回報**: https://github.com/yourorg/netstack/issues
-   **討論區**: https://github.com/yourorg/netstack/discussions

---

🌟 **NetStack v1.0** - 讓 5G 核心網部署變得簡單！
