make test-ntn-validation
make test-config-validation
make test-satellite-gnb
make test-ueransim
make test-latency
make test-e2e
make test-slice-switching
make test-performance
make test-connectivity

# 🛰️ NTN Stack 測試指令手冊

## 🚀 核心測試指令

```bash
make test                    # 執行完整的本地測試套件
make test-core              # 執行核心功能測試
make test-advanced          # 執行進階功能測試
make test-all               # 執行所有 NetStack 測試
```

## 🧪 單項測試指令

```bash
make test-ntn-validation     # NTN 功能快速驗證
make test-config-validation  # NTN 配置驗證測試
make test-satellite-gnb      # 衛星-gNodeB 整合測試
make test-ueransim          # UERANSIM 配置測試
make test-latency           # NTN 延遲測試
make test-e2e               # 端到端測試
make test-slice-switching    # 切片切換測試
make test-performance       # 性能測試
make test-connectivity      # 連接性測試
```

## 🔧 NetStack 管理指令

```bash
make netstack-up            # 啟動 NetStack 核心網
make netstack-down          # 停止 NetStack 核心網
make netstack-status        # 檢查 NetStack 狀態
make netstack-logs          # 查看 NetStack 日誌
make netstack-ping-test     # 執行 Ping 測試
```

## 🧹 清理指令

```bash
make test-clean             # 清理測試結果和臨時文件
```
