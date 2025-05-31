# NTN Stack 測試套件

## 📁 目錄結構

```
tests/
├── unit/                    # 單元測試
│   ├── netstack/           # NetStack 單元測試
│   ├── simworld/           # SimWorld 單元測試
│   └── deployment/         # 部署模組單元測試
├── integration/            # 整合測試
│   ├── api/               # API 整合測試
│   └── services/          # 服務整合測試
├── e2e/                   # 端到端測試
├── api/                   # API 專項測試
├── performance/           # 性能測試
├── reports/               # 測試報告 (自動生成)
│   ├── test_results/      # 測試結果
│   └── coverage/          # 覆蓋率報告
├── tools/                 # 測試工具
├── configs/               # 測試配置
├── pytest.ini            # pytest 配置
├── requirements.txt       # 測試依賴
├── run_tests.py          # 測試執行腳本
├── Makefile              # 構建配置
└── README.md             # 本檔案
```

## 🚀 快速開始

### 安裝測試依賴

```bash
cd tests
pip install -r requirements.txt
```

### 執行測試

#### 使用測試執行腳本（推薦）

```bash
# 執行所有測試
python run_tests.py

# 執行特定類型測試
python run_tests.py --type unit         # 單元測試
python run_tests.py --type integration  # 整合測試
python run_tests.py --type e2e          # 端到端測試
python run_tests.py --type api          # API 測試
python run_tests.py --type performance  # 性能測試

# 執行特定模組的單元測試
python run_tests.py --type unit --module simworld

# 生成報告
python run_tests.py --coverage --html --summary
```

#### 直接使用 pytest

```bash
# 執行所有測試
pytest

# 執行特定類型測試
pytest unit/                # 單元測試
pytest integration/         # 整合測試
pytest e2e/                 # 端到端測試
pytest api/                 # API 測試
pytest performance/         # 性能測試

# 生成報告
pytest --html=reports/test_results/report.html --cov=unit
```

#### 使用 Makefile（推薦）

```bash
# 執行所有測試
make test

# 執行特定類型測試
make test-unit           # 單元測試
make test-integration    # 整合測試
make test-e2e           # 端到端測試
make test-api           # API 測試
make test-performance   # 性能測試

# 執行特定模組測試
make test-netstack      # NetStack 模組
make test-simworld      # SimWorld 模組
make test-deployment    # 部署模組

# 生成覆蓋率報告
make coverage

# 查看所有可用指令
make help
```

## 📊 測試報告

### 自動生成的報告

-   **HTML 報告**: `reports/test_results/*.html`
-   **JUnit XML**: `reports/test_results/junit.xml`
-   **覆蓋率報告**: `reports/coverage/`
-   **測試摘要**: `reports/test_summary.json`

### 查看測試摘要

```bash
python tools/test_summary.py
# 或
make report
```

## 🧪 測試類型

| 類型           | 目錄           | 用途                 | 特點                       |
| -------------- | -------------- | -------------------- | -------------------------- |
| **單元測試**   | `unit/`        | 測試個別模組和函數   | 快速執行，不依賴外部服務   |
| **整合測試**   | `integration/` | 測試模組間的整合     | 可能需要外部服務運行       |
| **端到端測試** | `e2e/`         | 測試完整的使用者流程 | 需要完整的系統環境         |
| **API 測試**   | `api/`         | 專門測試 API 端點    | 專注於 API 介面驗證        |
| **性能測試**   | `performance/` | 測試系統性能和負載   | 執行時間較長，需要特殊環境 |

## 🔧 配置

### 測試標記 (Markers)

使用 `@pytest.mark.*` 標記測試：

-   `@pytest.mark.smoke`: 煙霧測試
-   `@pytest.mark.unit`: 單元測試
-   `@pytest.mark.integration`: 整合測試
-   `@pytest.mark.e2e`: 端到端測試
-   `@pytest.mark.api`: API 測試
-   `@pytest.mark.performance`: 性能測試
-   `@pytest.mark.slow`: 執行時間較長的測試
-   `@pytest.mark.network`: 需要網路連接的測試

### 執行特定標記的測試

```bash
pytest -m "smoke"              # 只執行煙霧測試
pytest -m "unit and not slow"  # 執行快速的單元測試
pytest -m "not network"        # 跳過需要網路的測試
```

## 📈 測試統計

最新測試執行結果：

-   **總測試數**: 12
-   **通過率**: 100%
-   **執行時間**: < 0.1 秒
-   **覆蓋率**: 12% (持續改善中)

## 🛠️ 開發指南

### 新增測試

1. **單元測試**: 在 `unit/模組名/` 目錄下創建 `test_*.py` 檔案
2. **整合測試**: 在 `integration/` 目錄下創建測試檔案
3. **API 測試**: 在 `api/` 目錄下創建測試檔案
4. **端到端測試**: 在 `e2e/` 目錄下創建測試檔案
5. **性能測試**: 在 `performance/` 目錄下創建測試檔案

### 測試命名規範

-   檔案名: `test_*.py` 或 `*_test.py` 或 `*_tests.py`
-   函數名: `test_*`
-   類別名: `Test*`

### 最佳實踐

1. **獨立性**: 每個測試應該獨立執行
2. **清晰性**: 測試名稱應該清楚描述測試內容
3. **快速性**: 單元測試應該快速執行
4. **可靠性**: 測試結果應該一致且可重現
5. **簡潔性**: 保持測試目錄結構簡單扁平

## 🔍 故障排除

### 常見問題

1. **模組導入錯誤**: 檢查 Python 路徑設定
2. **服務連接失敗**: 確認相關服務已啟動
3. **權限問題**: 檢查檔案和目錄權限

### 除錯技巧

```bash
pytest -v -s          # 詳細輸出
pytest --lf           # 只執行失敗的測試
pytest -x             # 停在第一個失敗
pytest --pdb          # 除錯模式
make test-debug       # 使用 Makefile 進行除錯
```

### 獲取協助

如有問題，請：

1. 檢查測試日誌: `reports/test_results/pytest.log`
2. 查看測試摘要: `python tools/test_summary.py` 或 `make report`
3. 聯繫開發團隊

---

**最後更新**: 2025-05-31  
**版本**: 3.0.0 (極簡扁平化版)
