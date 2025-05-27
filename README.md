# NTN Stack - 非地面網路堆疊

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

完整的 5G 非地面網路 (NTN) 模擬和測試平台，整合衛星軌道計算、無線網路模擬和 gNodeB 配置管理。

## 🌟 專案特色

### 🛰️ 衛星位置轉換為 gNodeB 參數（第 4 項任務）

-   **實時軌道計算**：使用 Skyfield 進行精確的衛星軌道傳播
-   **動態配置生成**：自動將衛星位置轉換為 5G NTN gNodeB 參數
-   **多普勒效應補償**：計算並補償衛星移動造成的多普勒偏移
-   **傳播延遲優化**：根據衛星高度動態調整傳播延遲參數
-   **批量處理支援**：支援多個衛星的批量位置轉換
-   **持續追蹤機制**：實時追蹤衛星位置變化並更新配置

### 🌐 OneWeb 衛星作為 gNodeB 的模擬（第 5 項任務）

-   **OneWeb 星座模擬**：完整的 OneWeb LEO 衛星群模擬
-   **動態波束管理**：模擬衛星波束覆蓋和切換
-   **NTN 特性優化**：針對 LEO 衛星的 5G NTN 參數優化
-   **UERANSIM 整合**：自動生成和部署 UERANSIM gNodeB 配置
-   **軌道追蹤系統**：實時同步衛星軌道數據
-   **覆蓋區域計算**：動態計算衛星服務覆蓋區域

## 🏗️ 系統架構

```
NTN Stack
├── netstack/          # 5G 核心網和 NTN 管理
│   ├── netstack_api/   # FastAPI 後端服務
│   ├── compose/        # Docker Compose 配置
│   └── config/         # 核心網配置文件
├── simworld/          # 衛星軌道模擬
│   ├── backend/        # 軌道計算後端
│   ├── frontend/       # 可視化前端
│   └── docker-compose.yml
├── test_ntn_stack.py  # 完整功能測試
├── Makefile           # 統一管理工具
└── README.md          # 專案說明
```

## 🚀 快速開始

### 前置需求

-   Docker >= 20.10
-   Docker Compose >= 2.0
-   Make (可選，用於便捷命令)

### 一鍵啟動

```bash
# 啟動所有服務
make start

# 或者手動啟動
docker-compose up -d
```

### 一鍵測試

```bash
# 執行完整測試套件
make test

# 執行快速測試
make test-quick

# 執行特定測試
make test-netstack      # 測試 NetStack API
make test-simworld      # 測試 SimWorld API
make test-integration   # 測試整合功能
```

## 🏗️ 架構概覽

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SimWorld      │    │   NetStack      │    │   測試框架      │
│                 │    │                 │    │                 │
│ • 衛星軌道計算  │◄──►│ • gNodeB 配置   │◄──►│ • Docker 化測試 │
│ • 場景模擬      │    │ • UERANSIM 整合 │    │ • 自動化報告    │
│ • 座標轉換      │    │ • OneWeb 星座   │    │ • CI/CD 支援    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 功能特色

### ✅ 已完成功能

#### 🛰️ 衛星軌道服務 (SimWorld)

-   Skyfield 基礎軌道計算
-   TLE 數據處理和更新
-   實時衛星位置追蹤
-   多種座標系統轉換 (ECEF, Geodetic, ECI)
-   場景健康度檢查和自動回退

#### 🔧 網路配置服務 (NetStack)

-   動態 gNodeB 配置生成
-   UERANSIM 整合和部署
-   多切片網路支援 (eMBB, URLLC, mMTC)
-   Redis 緩存和 MongoDB 持久化
-   Prometheus 監控指標

#### 🌐 OneWeb 星座模擬

-   648 顆衛星完整星座
-   18 個軌道平面，87.4° 傾角
-   實時軌道追蹤和配置更新
-   NTN 特性優化 (都卜勒效應、傳播延遲)
-   動態波束覆蓋計算

#### 🔗 衛星-gNodeB 映射

-   衛星位置到 gNodeB 參數轉換
-   批量處理和持續追蹤
-   UAV 位置考量和優化
-   自動配置部署

#### 🧪 Docker 化測試框架

-   完整的容器化測試環境
-   pytest 基礎的現代測試框架
-   自動化測試報告生成
-   整合和單元測試分離
-   一鍵測試和清理

## 🛠️ 使用指南

### 服務管理

```bash
# 啟動服務
make start              # 啟動所有服務
make netstack-start     # 只啟動 NetStack
make simworld-start     # 只啟動 SimWorld

# 停止服務
make stop               # 停止所有服務
make netstack-stop      # 只停止 NetStack
make simworld-stop      # 只停止 SimWorld

# 重啟服務
make restart            # 重啟所有服務
make netstack-restart   # 重啟 NetStack
make simworld-restart   # 重啟 SimWorld

# 查看狀態
make status             # 查看所有服務狀態
make logs               # 查看服務日誌
```

### 測試管理

```bash
# 完整測試
make test               # 執行完整 Docker 化測試套件
make test-integration   # 執行整合測試
make test-unit          # 執行單元測試

# 功能測試
make test-netstack      # 測試 NetStack API
make test-simworld      # 測試 SimWorld API
make test-satellite-mapping  # 測試衛星映射
make test-oneweb        # 測試 OneWeb 星座

# 測試報告
make test-reports       # 啟動測試報告服務器 (http://localhost:8090)
make test-clean         # 清理測試環境
```

### 開發工具

```bash
# 開發環境
make dev-setup          # 設置開發環境
make dev-start          # 啟動開發環境
make health-check       # 健康檢查

# 監控和診斷
make metrics            # 查看系統指標
make api-docs           # 打開 API 文檔
make top                # 查看容器資源使用

# 維護
make clean              # 清理所有資源
make backup             # 備份重要數據
make prune              # 清理 Docker 系統
```

## 🌐 API 端點

### NetStack API (http://localhost:8080)

#### 衛星映射

-   `POST /api/v1/satellite-gnb/mapping` - 單個衛星映射
-   `GET /api/v1/satellite-gnb/batch-mapping` - 批量衛星映射
-   `POST /api/v1/satellite-gnb/start-tracking` - 啟動持續追蹤

#### OneWeb 星座

-   `POST /api/v1/oneweb/constellation/initialize` - 初始化星座
-   `POST /api/v1/oneweb/orbital-tracking/start` - 啟動軌道追蹤
-   `GET /api/v1/oneweb/constellation/status` - 查看星座狀態
-   `POST /api/v1/oneweb/ueransim/deploy` - 部署 UERANSIM 配置

#### UERANSIM 配置

-   `POST /api/v1/ueransim/config/generate` - 生成配置
-   `GET /api/v1/ueransim/templates` - 獲取模板
-   `GET /api/v1/ueransim/scenarios` - 獲取場景

### SimWorld API (http://localhost:8000)

#### 軌道服務

-   `GET /api/v1/orbit/satellite/{id}/position` - 獲取衛星位置
-   `GET /api/v1/orbit/satellites` - 獲取衛星列表
-   `GET /api/v1/orbit/tle/list` - 獲取 TLE 數據

#### 模擬服務

-   `GET /api/v1/simulation/scenes` - 獲取場景列表
-   `POST /api/v1/simulation/scene/load` - 載入場景

## 📊 測試報告

測試完成後，可以通過以下方式查看報告：

```bash
# 啟動報告服務器
make test-reports

# 訪問報告
open http://localhost:8090
```

報告包含：

-   HTML 格式的詳細測試結果
-   JUnit XML 格式 (適用於 CI/CD)
-   JSON 格式的結構化數據
-   性能基準測試結果

## 🔧 配置說明

### 環境變數

```bash
# 服務 URL
NETSTACK_URL=http://localhost:8080
SIMWORLD_URL=http://localhost:8000

# 測試配置
TEST_TIMEOUT=60
PYTEST_ARGS=--verbose --tb=short

# Docker 配置
COMPOSE_PROJECT_NAME=ntn-stack
```

### 端口配置

| 服務         | 端口  | 說明            |
| ------------ | ----- | --------------- |
| NetStack API | 8080  | 主要 API 服務   |
| SimWorld API | 8000  | 模擬服務        |
| 測試報告     | 8090  | 測試結果查看    |
| Redis        | 6379  | 緩存服務        |
| MongoDB      | 27017 | 數據庫          |
| PostgreSQL   | 5432  | SimWorld 數據庫 |

## 🚨 故障排除

### 常見問題

1. **服務啟動失敗**

    ```bash
    make clean && make build && make start
    ```

2. **測試失敗**

    ```bash
    make test-clean && make test-quick
    ```

3. **端口衝突**

    - 檢查 `docker-compose.yml` 中的端口配置
    - 使用 `docker ps` 查看端口使用情況

4. **記憶體不足**
    - 增加 Docker 記憶體限制
    - 使用 `make prune` 清理未使用的資源

### 日誌查看

```bash
# 查看所有服務日誌
make logs

# 查看特定服務日誌
make netstack-logs
make simworld-logs

# 查看測試日誌
docker-compose -f docker-compose.test.yml logs ntn-stack-tester
```

## 🤝 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

### 開發流程

```bash
# 設置開發環境
make dev-setup

# 啟動開發服務
make dev-start

# 執行測試
make test

# 清理環境
make clean
```

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件

## 🙏 致謝

-   [UERANSIM](https://github.com/aligungr/UERANSIM) - 5G 網路模擬器
-   [Skyfield](https://rhodesmill.org/skyfield/) - 天體力學計算
-   [Sionna](https://nvlabs.github.io/sionna/) - 無線通信模擬
-   [FastAPI](https://fastapi.tiangolo.com/) - 現代 Python Web 框架

---

**NTN Stack** - 讓衛星通信變得簡單 🛰️✨
