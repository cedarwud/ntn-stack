# NTN Stack 測試框架

## 📁 目錄結構

```
tests/
├── unit/                    # 單元測試
│   ├── netstack/           # NetStack 模組測試
│   ├── simworld/           # SimWorld 模組測試
│   ├── deployment/         # 部署模組測試
│   └── monitoring/         # 監控模組測試
├── integration/            # 整合測試
│   ├── api/               # API 整合測試
│   └── services/          # 服務整合測試
├── e2e/                   # 端到端測試
│   └── scenarios/         # 測試場景
├── performance/           # 性能測試
├── reports/              # 測試報告 (統一存放)
├── tools/                # 測試工具
├── configs/              # 測試配置
├── run_tests.py          # 測試執行腳本
├── pytest.ini           # pytest 配置
└── README.md            # 本文件
```

## 🚀 快速開始

### 執行所有測試

```bash
python run_tests.py --type all --html --coverage --summary
```

### 執行特定類型測試

```bash
# 單元測試
python run_tests.py --type unit --html

# 整合測試
python run_tests.py --type integration --html

# 端到端測試
python run_tests.py --type e2e --html

# 性能測試
python run_tests.py --type performance --html
```

### 執行特定模組測試

```bash
# NetStack 模組
python run_tests.py --type unit --module netstack --html

# SimWorld 模組
python run_tests.py --type unit --module simworld --html

# 部署模組
python run_tests.py --type unit --module deployment --html
```

## 📊 測試報告

所有測試報告統一存放在 `reports/` 目錄：

-   **HTML 報告**: `reports/test_report_YYYYMMDD_HHMMSS.html`
-   **JUnit XML**: `reports/junit_YYYYMMDD_HHMMSS.xml`
-   **覆蓋率報告**: `reports/coverage/`
-   **測試摘要**: `reports/test_summary.json`

## 🔧 測試工具

### 測試摘要工具

```bash
python tools/test_summary.py
```

### 測試執行器選項

```bash
python run_tests.py --help
```

## 📋 測試標記

使用 pytest 標記來分類測試：

-   `@pytest.mark.smoke` - 煙霧測試
-   `@pytest.mark.unit` - 單元測試
-   `@pytest.mark.integration` - 整合測試
-   `@pytest.mark.e2e` - 端到端測試
-   `@pytest.mark.performance` - 性能測試
-   `@pytest.mark.slow` - 執行時間較長的測試
-   `@pytest.mark.network` - 需要網路連接的測試

## 🎯 測試最佳實踐

1. **單元測試**: 測試單一功能模組，不依賴外部服務
2. **整合測試**: 測試模組間的交互，可能需要模擬外部服務
3. **端到端測試**: 測試完整的用戶場景，需要真實的服務環境
4. **性能測試**: 測試系統在負載下的表現

## 📈 測試覆蓋率

目標覆蓋率：

-   單元測試：≥ 80%
-   整合測試：≥ 60%
-   端到端測試：≥ 40%

## 🔍 故障排除

### 常見問題

1. **服務連接失敗**: 確保 NetStack 和 SimWorld 服務正在運行
2. **依賴缺失**: 執行 `pip install -r requirements.txt`
3. **權限問題**: 確保有寫入 `reports/` 目錄的權限

### 調試模式

```bash
python run_tests.py --type unit --verbose
```

## 📝 添加新測試

1. 在適當的目錄創建測試文件 (`test_*.py`)
2. 使用適當的 pytest 標記
3. 添加必要的文檔字符串
4. 確保測試可以獨立運行

## 🏗️ 持續整合

測試框架支持 CI/CD 流水線：

```yaml
# 示例 CI 配置
- name: Run Tests
  run: |
      cd tests
      python run_tests.py --type all --html --coverage
```

---

**最後更新**: 2025-05-31  
**版本**: 3.0.0 (極簡扁平化版)
