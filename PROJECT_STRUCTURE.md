# NTN Stack 專案結構說明

## 概述

本專案採用 Docker 容器化開發和部署，透過根目錄的 `Makefile` 統一管理多個子專案。

## 目錄結構

```
ntn-stack/
├── netstack/                     # NetStack 核心網路服務
│   ├── netstack_api/             # FastAPI 應用
│   ├── compose/                  # Docker Compose 配置
│   ├── docker/                   # Docker 相關檔案
│   ├── config/                   # 配置檔案
│   ├── requirements.txt          # NetStack 運行依賴
│   ├── requirements-dev.txt      # NetStack 開發依賴
│   └── Makefile                  # NetStack 專案管理
│
├── simworld/                     # SimWorld 衛星模擬服務
│   ├── frontend/                 # React 前端應用
│   ├── backend/                  # FastAPI 後端應用
│   │   ├── app/                  # 應用程式碼
│   │   └── requirements.txt      # SimWorld 運行依賴
│   ├── docker-compose.yml        # SimWorld 服務編排
│   └── Makefile                  # SimWorld 專案管理
│
├── tests/                        # 統一測試目錄
│   ├── tools/                    # 測試和驗證工具
│   │   ├── verify_architecture_status.py
│   │   └── README.md
│   ├── integration/              # 整合測試
│   ├── e2e/                      # 端到端測試
│   ├── performance/              # 性能測試
│   └── reports/                  # 測試報告（Git 忽略）
│
├── deployment/                   # 部署自動化
│   ├── scripts/                  # 部署腳本
│   ├── templates/                # 配置模板
│   ├── config_manager.py         # 配置管理器
│   └── requirements.txt          # 部署工具依賴
│
├── monitoring/                   # 觀測性和監控
│   ├── configs/                  # 監控配置
│   ├── templates/                # 監控模板
│   ├── deploy_observability.py   # 觀測性部署
│   └── README.md
│
├── Makefile                      # 統一專案管理（主要入口）
├── requirements.txt              # 全域測試和開發工具依賴
├── pytest.ini                   # pytest 配置
├── PROJECT_STRUCTURE.md          # 本文件
└── README.md                     # 專案說明
```

## 依賴管理策略

### 分層依賴管理

1. **根目錄 `requirements.txt`** - 全域測試和開發工具

    - pytest 系列測試工具
    - 程式碼品質工具（black, flake8, mypy）
    - Docker 管理工具
    - 整合測試用 HTTP 客戶端

2. **子專案 `requirements.txt`** - 專案特定運行依賴

    - `netstack/requirements.txt` - NetStack API 服務依賴
    - `simworld/backend/requirements.txt` - SimWorld 後端依賴

3. **專用工具 `requirements.txt`** - 特定用途依賴
    - `deployment/requirements.txt` - 部署自動化工具
    - `netstack/requirements-dev.txt` - NetStack 開發時額外依賴

### Docker 優先策略

-   主要開發和部署環境使用 Docker 容器
-   本地 `venv` 目錄已加入 `.gitignore`，不納入版本控制
-   依賴透過 Docker 鏡像管理，確保環境一致性

## 主要命令

### 服務管理

```bash
make up              # 啟動所有服務
make down            # 停止所有服務
make restart         # 重啟所有服務
make status          # 查看服務狀態
```

### 測試相關

```bash
make test-quick      # 快速測試
make test-all        # 完整測試套件
make test-new-architecture  # 新架構測試
make verify-architecture    # 架構驗證
```

### 開發工具

```bash
make dev-setup       # 設置開發環境
make clean           # 清理資源
make logs            # 查看服務日誌
```

## 設計原則

1. **統一管理** - 根目錄 `Makefile` 作為單一入口點
2. **容器化優先** - 所有服務透過 Docker 運行
3. **分層依賴** - 依賴按用途和範圍分層管理
4. **測試整合** - 統一的測試目錄和配置
5. **DevOps 整合** - 內建部署和監控工具

## 注意事項

-   本專案設計為在 Docker 環境中運行，請確保 Docker 和 Docker Compose 已安裝
-   使用 `make help` 查看所有可用命令
-   測試報告會自動生成在 `tests/reports/` 目錄（Git 忽略）
-   開發時建議使用容器內環境，避免本地依賴衝突
