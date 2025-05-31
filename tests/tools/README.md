# 測試工具目錄

此目錄包含 NTN Stack 專案的各種測試和驗證工具。

## 工具清單

### `verify_architecture_status.py`

架構驗證腳本，用於檢查三個重構目標的達成情況：

1. NetStack 事件驅動架構（干擾檢測異步化）
2. SimWorld CQRS 模式（衛星位置讀寫分離）
3. 全面異步微服務架構

**使用方法：**

```bash
# 從根目錄執行
python3 tests/tools/verify_architecture_status.py

# 或使用 Makefile 命令
make verify-architecture
```

## 目錄結構

```
tests/
├── tools/                    # 測試和驗證工具
│   ├── README.md            # 本文件
│   └── verify_architecture_status.py
├── integration/             # 整合測試
├── e2e/                     # 端到端測試
└── reports/                 # 測試報告
```
