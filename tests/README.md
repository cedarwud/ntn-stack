# NTN Stack 測試管理架構

## 📋 測試架構概覽

本專案採用**分層統一**的測試管理架構，既保持各子專案的獨立性，又提供統一的測試入口和管理。

```
ntn-stack/
├── tests/                          # 🎯 統一測試管理中心
│   ├── integration/                # 整合測試
│   │   ├── sionna_integration/     # Sionna 整合測試
│   │   ├── e2e/                    # 端到端測試
│   │   └── cross_service/          # 跨服務測試
│   ├── unit/                       # 根層級單元測試
│   ├── performance/                # 效能測試
│   ├── acceptance/                 # 驗收測試
│   ├── reports/                    # 測試報告
│   ├── fixtures/                   # 測試夾具
│   ├── helpers/                    # 測試助手
│   └── configs/                    # 測試配置
├── netstack/tests/                 # NetStack 專用測試
└── simworld/backend/tests/         # SimWorld 專用測試
```

## 🎯 測試分類與職責

### 1. **根目錄 tests/ - 統一測試中心**

```bash
tests/
├── integration/                    # 🔗 整合測試
│   ├── sionna_integration.py      # Sionna 完整整合
│   ├── netstack_simworld_test.py  # NetStack ↔ SimWorld
│   ├── e2e_ntn_stack.py          # 端到端 NTN 測試
│   └── satellite_ecosystem.py     # 衛星生態系統測試
├── unit/                           # 🧩 跨服務單元測試
│   ├── common_models_test.py      # 共享模型測試
│   └── api_contracts_test.py      # API 合約測試
├── performance/                    # ⚡ 效能測試
│   ├── load_test.py               # 負載測試
│   ├── stress_test.py             # 壓力測試
│   └── latency_benchmark.py       # 延遲基準測試
├── acceptance/                     # ✅ 驗收測試
│   ├── user_stories/              # 用戶故事測試
│   └── business_scenarios/        # 業務場景測試
└── configs/                        # ⚙️ 測試配置
    ├── test_environments.yaml     # 測試環境配置
    ├── test_data.json             # 測試數據
    └── coverage.ini               # 覆蓋率配置
```

### 2. **NetStack 專用測試**

```bash
netstack/tests/
├── unit/                          # NetStack 單元測試
│   ├── services/                  # 服務層測試
│   ├── adapters/                  # 適配器測試
│   └── models/                    # 模型測試
├── integration/                   # NetStack 整合測試
│   ├── open5gs_integration/       # Open5GS 整合
│   ├── ueransim_integration/      # UERANSIM 整合
│   └── database_integration/      # 數據庫整合
└── shell_scripts/                 # 現有的 Shell 測試腳本
    ├── e2e_netstack.sh
    ├── performance_test.sh
    └── ...
```

### 3. **SimWorld 專用測試**

```bash
simworld/backend/tests/
├── unit/                          # SimWorld 單元測試
│   ├── domains/                   # 各領域單元測試
│   │   ├── wireless/
│   │   ├── satellite/
│   │   └── ...
│   └── services/                  # 服務測試
├── integration/                   # SimWorld 整合測試
│   ├── sionna_service/            # Sionna 服務整合
│   └── domain_integration/        # 領域間整合
└── fixtures/                      # SimWorld 測試夾具
```

## 🎪 測試執行策略

### **分級測試執行**

```makefile
# 1. 快速測試（開發時）
make test-quick          # 核心功能 + 健康檢查
make test-unit           # 所有單元測試
make test-netstack-only  # 僅 NetStack 測試
make test-simworld-only  # 僅 SimWorld 測試

# 2. 標準測試（CI/CD）
make test-integration    # 整合測試
make test-core          # 核心功能測試
make test-sionna        # Sionna 相關測試

# 3. 完整測試（發布前）
make test-all           # 所有測試
make test-performance   # 效能測試
make test-acceptance    # 驗收測試
```

### **並行測試執行**

```yaml
# tests/configs/parallel_config.yaml
parallel_execution:
    max_workers: 4
    test_groups:
        - name: 'netstack_unit'
          path: 'netstack/tests/unit/'
          timeout: 300
        - name: 'simworld_unit'
          path: 'simworld/backend/tests/unit/'
          timeout: 600
        - name: 'integration'
          path: 'tests/integration/'
          timeout: 900
        - name: 'performance'
          path: 'tests/performance/'
          timeout: 1200
```

## 📊 測試報告與覆蓋率

### **統一測試報告**

```bash
tests/reports/
├── coverage/                      # 覆蓋率報告
│   ├── netstack_coverage.html
│   ├── simworld_coverage.html
│   └── overall_coverage.html
├── test_results/                  # 測試結果
│   ├── junit_results.xml
│   ├── pytest_results.html
│   └── performance_report.json
└── metrics/                       # 測試指標
    ├── test_trends.json
    └── quality_metrics.json
```

### **覆蓋率目標**

-   **NetStack**: 85% (重點在適配器和服務)
-   **SimWorld**: 90% (重點在領域邏輯)
-   **整體**: 87% (跨服務整合)

## 🚀 實施建議

### **Phase 1: 結構重組**

1. 創建統一 tests/ 目錄
2. 遷移現有測試到新結構
3. 更新 Makefile 命令

### **Phase 2: 測試增強**

1. 補充缺失的單元測試
2. 擴展整合測試覆蓋
3. 建立效能基準測試

### **Phase 3: 自動化優化**

1. CI/CD 管道整合
2. 自動化測試報告
3. 品質門禁設置

## 🔧 開發工作流程

### **本地開發**

```bash
# 開發前運行快速測試
make test-quick

# 功能開發完成後
make test-unit test-integration

# 提交前完整檢查
make test-all
```

### **CI/CD 管道**

```yaml
stages:
    - unit_tests # 並行執行各服務單元測試
    - integration_tests # 服務間整合測試
    - e2e_tests # 端到端測試
    - performance_tests # 效能測試（可選）
    - acceptance_tests # 驗收測試（發布分支）
```

## 📝 測試規範

### **命名規範**

-   單元測試: `test_<function_name>.py`
-   整合測試: `<service>_<target>_integration_test.py`
-   端到端測試: `e2e_<scenario>_test.py`

### **測試數據管理**

-   使用 fixtures 管理測試數據
-   環境隔離（dev/test/staging）
-   數據清理和重置機制

### **測試文檔**

-   每個測試文件包含功能說明
-   複雜測試場景提供流程圖
-   測試數據來源和期望結果說明
