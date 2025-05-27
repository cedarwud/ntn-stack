# NTN Stack 測試系統整理與遷移總結

## 📋 整理目標

將 NTN Stack 的測試系統完全統一到根目錄的 Docker 化框架中，消除對 Python 虛擬環境的依賴，並整合所有散布在各子項目中的測試。

## 🗑️ 已清理的文件

### 根目錄清理

1. **`test_ntn_stack.py`** - ✅ 已刪除

    - **原因**: 功能已在 `tests/test_integration.py` 中重新實現
    - **替代方案**: 使用 `make test-integration`

2. **`test_docker_setup.py`** - ✅ 已移動
    - **新位置**: `tests/test_docker_setup.py`
    - **用途**: 驗證測試環境的 Docker 設置
    - **使用方法**: `cd tests && python test_docker_setup.py`

## 📁 新增的測試文件

### 1. `tests/test_netstack_legacy.py`

**目的**: 將 `netstack/tests/` 中的 shell 腳本測試轉換為 pytest 格式

**包含的測試**:

-   `test_ntn_quick_validation()` - NTN 功能快速驗證
-   `test_e2e_netstack_workflow()` - E2E 工作流程測試
-   `test_performance_metrics()` - 性能指標測試
-   `test_satellite_gnb_integration()` - 衛星 gNodeB 整合測試
-   `test_ueransim_config_generation()` - UERANSIM 配置生成測試

**標記**:

-   `@pytest.mark.legacy` - 傳統測試轉換
-   `@pytest.mark.netstack` - NetStack 特定測試
-   `@pytest.mark.performance` - 性能測試
-   `@pytest.mark.satellite` - 衛星功能測試
-   `@pytest.mark.ueransim` - UERANSIM 配置測試

### 2. `tests/test_docker_setup.py`

**目的**: 驗證測試環境的 Docker 設置是否正確

**檢查項目**:

-   Docker Compose 文件完整性
-   測試目錄結構
-   必要的測試文件
-   NetStack 原有測試文件存在性

## 🔧 Makefile 更新

### 根目錄 Makefile

**更新項目**:

-   `test-legacy` 指令更新為執行 `tests/test_netstack_legacy.py`
-   移除對已刪除的 `test_ntn_stack.py` 的引用

### NetStack Makefile

**主要變更**:

```makefile
# 移除的測試指令
- test-e2e, test-connectivity, test-performance
- test-slice-switch, test-ntn-latency
- test-ueransim-config, test-ntn-config-validation
- test-quick-ntn-validation, test-all-ntn, test-all

# 新增的引導指令
+ test-deprecated: 提示用戶使用根目錄統一測試系統
```

**保留的指令**:

-   `verify-setup` - 更新為使用根目錄測試
-   `fix-connectivity` - 更新為使用根目錄測試
-   所有用戶管理相關指令（register-subscribers, show-subscribers 等）

## 📊 測試標記系統

新增的 pytest 標記:

```ini
legacy: 標記為傳統 shell 腳本轉換的測試
performance: 標記為性能測試
satellite: 標記為衛星功能測試
ueransim: 標記為 UERANSIM 配置測試
```

## 🚀 使用方法

### 完整測試套件

```bash
make test                    # 執行所有測試
```

### 特定類型測試

```bash
make test-netstack          # NetStack API 測試
make test-simworld          # SimWorld API 測試
make test-integration       # 整合測試
make test-legacy           # 傳統測試 (原 shell 腳本功能)
```

### 按標記執行測試

```bash
# 執行性能測試
docker-compose -f docker-compose.test.yml run --rm ntn-stack-tester \
  python -m pytest tests/ -m "performance" -v

# 執行衛星相關測試
docker-compose -f docker-compose.test.yml run --rm ntn-stack-tester \
  python -m pytest tests/ -m "satellite" -v

# 排除慢速測試
docker-compose -f docker-compose.test.yml run --rm ntn-stack-tester \
  python -m pytest tests/ -m "not slow" -v
```

## 📝 NetStack 測試文件映射

| 原 Shell 腳本                       | 對應 pytest 測試                    | 說明              |
| ----------------------------------- | ----------------------------------- | ----------------- |
| `quick_ntn_validation.sh`           | `test_ntn_quick_validation()`       | NTN 功能快速驗證  |
| `e2e_netstack.sh`                   | `test_e2e_netstack_workflow()`      | E2E 工作流程測試  |
| `performance_test.sh`               | `test_performance_metrics()`        | 性能指標測試      |
| `satellite_gnb_integration_test.sh` | `test_satellite_gnb_integration()`  | 衛星 gNodeB 整合  |
| `ueransim_config_test.sh`           | `test_ueransim_config_generation()` | UERANSIM 配置生成 |

**註**: 其他 shell 腳本（如 `slice_switching_test.sh`, `ntn_latency_test.sh` 等）的功能已整合到現有的測試文件中。

## 🎯 整理成果

### ✅ 已達成目標

1. **統一測試框架**: 所有測試現在都使用 Docker 化的 pytest 框架
2. **消除環境依賴**: 不再需要 Python 虛擬環境
3. **一鍵執行**: 使用 `make test` 即可執行完整測試
4. **測試整合**: NetStack 的重要測試功能已轉換為 pytest 格式
5. **清理冗余**: 移除了重複和過時的測試文件

### 📊 測試覆蓋

-   **NetStack API**: 完整的 API 端點測試
-   **SimWorld API**: 場景和軌道服務測試
-   **整合測試**: 跨服務通信和工作流程
-   **傳統功能**: 原 shell 腳本功能的 pytest 版本
-   **性能測試**: 響應時間和並發測試
-   **衛星功能**: gNodeB 映射和星座管理

### 🔄 向後兼容

雖然移除了 NetStack 的直接測試指令，但：

-   所有功能都在根目錄測試中保留
-   提供了清晰的遷移指引 (`test-deprecated`)
-   用戶管理功能完全保留

## 💡 後續建議

1. **監控覆蓋率**: 考慮添加代碼覆蓋率檢查
2. **CI/CD 整合**: 將 Docker 化測試整合到持續集成流程
3. **測試數據**: 為測試創建標準化的測試數據集
4. **定期維護**: 定期檢查和更新測試以確保與代碼同步

## 📞 支援

如果在使用新的測試系統時遇到問題：

1. 檢查 Docker 和 Docker Compose 是否正確安裝
2. 確保所有服務都已啟動 (`make start`)
3. 查看測試報告 (`make test-reports`)
4. 執行環境驗證 (`cd tests && python test_docker_setup.py`)

---

_此文件記錄了 NTN Stack 測試系統的完整整理過程，為未來的維護和開發提供參考。_
