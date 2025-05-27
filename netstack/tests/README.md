# NetStack Shell 測試腳本

## 🎯 **測試腳本角色分工**

### **根目錄 `tests/` (Python pytest)**

-   **API 測試**：單元測試、整合測試
-   **Docker 化測試**：容器環境測試
-   **自動化 CI/CD 測試**

### **`netstack/tests/` (Shell 腳本)**

-   **功能驗證測試**：實際網絡功能測試
-   **性能基準測試**：延遲、吞吐量測試
-   **端到端場景測試**：完整工作流測試
-   **運維診斷腳本**：故障排除、狀態檢查

## 📝 **測試腳本說明**

| 腳本                                | 用途                   | 執行時機         |
| ----------------------------------- | ---------------------- | ---------------- |
| `satellite_gnb_integration_test.sh` | 衛星與 gNodeB 整合測試 | 功能開發後驗證   |
| `ueransim_config_test.sh`           | UERANSIM 配置生成測試  | 配置變更後驗證   |
| `ntn_latency_test.sh`               | NTN 網絡延遲測試       | 性能優化驗證     |
| `e2e_netstack.sh`                   | 端到端工作流測試       | 部署前全流程驗證 |
| `slice_switching_test.sh`           | 網絡切片切換測試       | 切片功能驗證     |
| `ntn_config_validation_test.sh`     | NTN 配置驗證測試       | 配置完整性檢查   |
| `performance_test.sh`               | 性能基準測試           | 性能回歸測試     |
| `quick_ntn_validation.sh`           | 快速功能驗證           | 日常開發驗證     |
| `test_connectivity.sh`              | 連接性測試             | 網絡連通性檢查   |

## 🔧 **使用方式**

### **1. 單一測試執行**

```bash
cd netstack/tests
./quick_ntn_validation.sh
```

### **2. 整合到 Makefile**

```bash
# 在根目錄執行
make test-netstack-shell  # 執行所有 shell 腳本測試
```

### **3. Docker 化執行** (推薦)

```bash
# 透過 Docker 執行，確保環境一致性
docker compose -f docker-compose.test.yml run --rm ntn-stack-tester \
  bash -c "cd netstack/tests && ./e2e_netstack.sh"
```

## ⚠️ **注意事項**

1. **Shell 腳本專注於功能性和性能測試**
2. **Python pytest 專注於 API 和邏輯測試**
3. **兩者互補，不重複**
4. **Shell 腳本可被 Makefile 和 CI/CD 調用**
