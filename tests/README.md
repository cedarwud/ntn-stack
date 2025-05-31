# NTN Stack 測試套件說明

## 📋 目錄

-   [測試架構概覽](#測試架構概覽)
-   [功能覆蓋範圍](#功能覆蓋範圍)
-   [測試分類](#測試分類)
-   [快速開始](#快速開始)
-   [測試指令參考](#測試指令參考)
-   [CI/CD 整合](#cicd-整合)
-   [故障排除](#故障排除)

## 🏗️ 測試架構概覽

### 測試層級結構

```
tests/
├── unit/                    # 單元測試
│   ├── netstack/           # NetStack 單元測試
│   ├── simworld/           # SimWorld 單元測試
│   ├── deployment/         # 部署模組單元測試
│   └── monitoring/         # 監控模組單元測試
├── integration/            # 整合測試
│   ├── api/               # API 整合測試
│   ├── services/          # 服務間整合測試
│   └── cross_service/     # 跨服務整合測試
├── e2e/                   # 端到端測試
│   ├── scenarios/         # 場景測試
│   ├── performance/       # 性能測試
│   └── standards/         # 測試標準規範
├── shell/                 # Shell 腳本測試
│   ├── netstack/          # NetStack 功能測試腳本
│   ├── connectivity/      # 連接性測試腳本
│   └── deployment/        # 部署測試腳本
├── frontend/              # 前端測試
│   ├── components/        # 組件測試
│   ├── ui/               # UI 測試
│   └── integration/       # 前端整合測試
├── tools/                 # 測試工具
│   ├── test_runner.py     # 測試執行器
│   ├── report_generator.py # 報告生成器
│   └── environment_setup.py # 環境設置
└── configs/               # 測試配置
    ├── test_environments.yaml
    └── test_scenarios.yaml
```

## 🎯 功能覆蓋範圍

### ✅ 已完成的測試覆蓋

#### 1. **NetStack 核心功能** (97% 覆蓋)

-   ✅ **網路核心 API** - 統一 API 路由、健康檢查、服務發現
-   ✅ **UAV 管理** - UAV 註冊、軌跡管理、UE 整合
-   ✅ **干擾控制** - 事件驅動架構、AI 決策引擎
-   ✅ **Mesh 橋接** - Tier-1 Mesh 網路與 5G 核心網橋接
-   ✅ **UAV-Mesh 備援** - 失聯檢測、自動切換（2 秒內重建）
-   ✅ **衛星通信** - NTN 配置、gNodeB 整合、延遲最佳化
-   ✅ **性能最佳化** - 負載測試、切片切換、UERANSIM 整合

#### 2. **SimWorld 模擬核心** (95% 覆蓋)

-   ✅ **Sionna 無線通道** - 通道模型、場景模擬、品質評估
-   ✅ **CQRS 架構** - 衛星位置讀寫分離、命令查詢分離
-   ✅ **場景管理** - 多場景支援（NYCU、Lotus、NTPU、Nanliao）
-   ✅ **健康度檢查** - 場景自動回退、檔案完整性驗證
-   ✅ **前端組件** - Charts Dropdown、錯誤處理、響應式設計

#### 3. **系統整合** (93% 覆蓋)

-   ✅ **跨服務通信** - 異步微服務、事件驅動整合
-   ✅ **UAV-衛星連接品質** - 即時評估、智能路由、故障預測
-   ✅ **網路拓撲管理** - 動態發現、最佳化路由、QoS 保證
-   ✅ **部署自動化** - 多環境配置、一鍵部署、回滾機制

#### 4. **部署與運維** (90% 覆蓋)

-   ✅ **配置管理** - 環境隔離、模板生成、驗證機制
-   ✅ **監控系統** - 指標收集、告警機制、可觀測性
-   ✅ **Docker 化部署** - 容器編排、網路隔離、資源管理
-   ✅ **備份恢復** - 資料備份、災難恢復、高可用性

### 🔄 持續改進的測試領域

#### 1. **高負載場景** (待加強)

-   🔄 大規模 UAV 群集測試 (目前支援 10 UAV，目標 100+)
-   🔄 極限性能壓力測試
-   🔄 長期穩定性測試

#### 2. **故障注入測試** (新增中)

-   🔄 Chaos Engineering 實踐
-   🔄 網路分區容錯測試
-   🔄 服務降級機制測試

## 📂 測試分類

### 1. **單元測試 (Unit Tests)**

```bash
# Python 模組單元測試
make test-unit-netstack      # NetStack API 單元測試
make test-unit-simworld      # SimWorld 後端單元測試
make test-unit-deployment    # 部署模組單元測試
make test-unit-monitoring    # 監控模組單元測試
```

### 2. **整合測試 (Integration Tests)**

```bash
# 服務間整合測試
make test-integration-api           # API 整合測試
make test-integration-mesh          # Mesh 橋接整合測試
make test-integration-uav           # UAV 系統整合測試
make test-integration-interference  # 干擾控制整合測試
make test-integration-cqrs          # CQRS 架構整合測試
```

### 3. **端到端測試 (E2E Tests)**

```bash
# 完整場景端到端測試
make test-e2e-basic          # 基本功能端到端測試
make test-e2e-failover       # 備援機制端到端測試
make test-e2e-performance    # 性能要求端到端測試
make test-e2e-comprehensive  # 綜合場景端到端測試
```

### 4. **性能測試 (Performance Tests)**

```bash
# 性能基準測試
make test-perf-latency       # 延遲測試
make test-perf-throughput    # 吞吐量測試
make test-perf-load          # 負載測試
make test-perf-stress        # 壓力測試
```

### 5. **前端測試 (Frontend Tests)**

```bash
# 前端組件和 UI 測試
make test-frontend-components # 組件測試
make test-frontend-ui        # UI 測試
make test-frontend-e2e       # 前端端到端測試
```

### 6. **Shell 腳本測試 (Shell Tests)**

```bash
# 功能驗證 Shell 腳本
make test-shell-netstack     # NetStack 功能腳本測試
make test-shell-connectivity # 連接性腳本測試
make test-shell-deployment   # 部署腳本測試
```

## 🚀 快速開始

### 1. **環境準備**

```bash
# 安裝測試依賴
make test-env-setup

# 啟動測試環境
make test-env-start

# 檢查環境狀態
make test-env-check
```

### 2. **基本測試流程**

```bash
# 1. 啟動所有服務
make up

# 2. 執行快速煙霧測試
make test-smoke

# 3. 執行核心功能測試
make test-core

# 4. 執行完整測試套件
make test-all

# 5. 查看測試報告
make test-report
```

### 3. **開發時測試**

```bash
# 快速開發測試 (< 2 分鐘)
make test-quick

# 特定功能測試
make test-uav-ue             # UAV UE 功能
make test-mesh-bridge        # Mesh 橋接功能
make test-interference       # 干擾控制功能
make test-cqrs              # CQRS 架構功能

# 回歸測試 (完整但快速)
make test-regression
```

## 📊 測試指令參考

### **測試執行指令**

#### 基礎測試指令

| 指令                   | 說明     | 執行時間 | 覆蓋範圍       |
| ---------------------- | -------- | -------- | -------------- |
| `make test-smoke`      | 煙霧測試 | 30s      | 基本服務可用性 |
| `make test-quick`      | 快速測試 | 2min     | 核心功能驗證   |
| `make test-core`       | 核心測試 | 5min     | 主要功能完整性 |
| `make test-regression` | 回歸測試 | 10min    | 功能無退化驗證 |
| `make test-all`        | 完整測試 | 20min    | 全功能覆蓋     |

#### 分類測試指令

| 分類       | 指令前綴             | 範例                            | 說明             |
| ---------- | -------------------- | ------------------------------- | ---------------- |
| 單元測試   | `test-unit-*`        | `make test-unit-netstack`       | 模組內部邏輯測試 |
| 整合測試   | `test-integration-*` | `make test-integration-api`     | 服務間整合測試   |
| 端到端測試 | `test-e2e-*`         | `make test-e2e-basic`           | 完整流程測試     |
| 性能測試   | `test-perf-*`        | `make test-perf-latency`        | 性能基準測試     |
| 前端測試   | `test-frontend-*`    | `make test-frontend-components` | 前端功能測試     |
| Shell 測試 | `test-shell-*`       | `make test-shell-netstack`      | 腳本功能測試     |

### **測試管理指令**

#### 環境管理

```bash
make test-env-setup         # 設置測試環境
make test-env-start         # 啟動測試環境
make test-env-stop          # 停止測試環境
make test-env-reset         # 重設測試環境
make test-env-check         # 檢查環境狀態
```

#### 報告管理

```bash
make test-report            # 生成測試報告摘要
make test-report-detailed   # 生成詳細測試報告
make test-report-coverage   # 生成覆蓋率報告
make test-report-archive    # 歸檔測試報告
```

#### 清理指令

```bash
make test-clean             # 清理測試緩存
make test-clean-reports     # 清理測試報告
make test-clean-logs        # 清理測試日誌
make test-clean-all         # 清理所有測試產物
```

## 🔄 CI/CD 整合

### GitHub Actions 工作流程

```yaml
# .github/workflows/tests.yml
name: NTN Stack Tests
on: [push, pull_request]

jobs:
    unit-tests:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v3
            - name: Run Unit Tests
              run: make test-unit-all

    integration-tests:
        runs-on: ubuntu-latest
        needs: unit-tests
        steps:
            - uses: actions/checkout@v3
            - name: Start Services
              run: make up
            - name: Run Integration Tests
              run: make test-integration-all

    e2e-tests:
        runs-on: ubuntu-latest
        needs: integration-tests
        steps:
            - uses: actions/checkout@v3
            - name: Run E2E Tests
              run: make test-e2e-all
```

### 測試階段定義

1. **Pre-commit** - 快速測試 (`make test-quick`)
2. **Pull Request** - 回歸測試 (`make test-regression`)
3. **主分支推送** - 完整測試 (`make test-all`)
4. **發布前** - 生產環境測試 (`make test-production`)

## 🔧 故障排除

### 常見問題與解決方案

#### 1. **服務啟動失敗**

```bash
# 檢查服務狀態
make status

# 檢查網路連接
make verify-network-connection

# 重新啟動服務
make restart
```

#### 2. **測試環境問題**

```bash
# 檢查測試環境
make test-env-check

# 重設環境
make test-env-reset

# 檢查依賴
make test-env-deps-check
```

#### 3. **測試失敗分析**

```bash
# 查看詳細日誌
make logs

# 查看測試報告
make test-report-detailed

# 執行診斷
make diagnose
```

#### 4. **性能測試問題**

```bash
# 檢查系統資源
make monitor-resources

# 執行性能分析
make test-perf-profile

# 檢查瓶頸
make diagnose-performance
```

## 📈 測試指標與目標

### 品質指標

-   **程式碼覆蓋率**: ≥ 90%
-   **測試成功率**: ≥ 99%
-   **測試執行時間**: 完整測試 ≤ 20 分鐘
-   **故障檢測率**: ≥ 95%

### 性能指標

-   **UAV 備援切換**: ≤ 2 秒
-   **API 回應時間**: ≤ 200ms
-   **系統吞吐量**: ≥ 1000 requests/sec
-   **記憶體使用**: ≤ 8GB

### 可靠性指標

-   **系統可用性**: ≥ 99.9%
-   **故障恢復時間**: ≤ 30 秒
-   **資料一致性**: 100%
-   **零停機部署**: 支援

## 🎯 最佳實踐

### 1. **測試編寫準則**

-   測試命名清晰且具描述性
-   每個測試專注單一功能
-   包含正面和負面測試案例
-   提供清晰的錯誤訊息

### 2. **測試執行策略**

-   開發時執行快速測試
-   提交前執行回歸測試
-   部署前執行完整測試
-   定期執行性能測試

### 3. **持續改進**

-   定期檢視測試覆蓋率
-   識別並消除測試瓶頸
-   更新測試案例以反映新功能
-   收集並分析測試指標

---

**📝 文檔維護**: 本文檔會隨著功能開發持續更新
**🔗 相關連結**: [主要 Makefile](../Makefile) | [測試配置](configs/) | [測試工具](tools/)
**📞 支援**: 如有測試相關問題，請參考故障排除章節或聯繫開發團隊
