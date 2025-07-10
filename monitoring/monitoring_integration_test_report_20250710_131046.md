
# NTN Stack 監控系統整合測試報告

**測試時間**: 2025-07-10 13:10:46
**總測試數**: 26
**通過測試**: 8
**失敗測試**: 18
**成功率**: 30.8%

## 📊 測試結果摘要

❌ 18 個測試失敗

## 📋 詳細測試結果

| 測試名稱 | 狀態 | 執行時間 | 訊息 |
|----------|------|----------|------|
| 連接測試_Prometheus | ❌ | 0.00s | Prometheus 連接異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| 連接測試_Grafana | ✅ | 0.01s | Grafana 連接正常 |
| 連接測試_AlertManager | ❌ | 0.01s | AlertManager 連接異常: Cannot connect to host localhost:9093 ssl:default [Connect call failed ('127.0.0.1', 9093)] |
| 連接測試_NetStack API | ❌ | 0.01s | NetStack API 連接異常: Cannot connect to host localhost:8000 ssl:default [Connect call failed ('127.0.0.1', 8000)] |
| Prometheus查詢_基本指標查詢 | ❌ | 0.00s | 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| Prometheus查詢_AI決策延遲 | ❌ | 0.00s | 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| Prometheus查詢_系統CPU使用率 | ❌ | 0.00s | 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| Prometheus查詢_決策成功率 | ❌ | 0.00s | 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| Grafana健康檢查 | ✅ | 0.00s | Grafana健康狀態正常 |
| Grafana儀表板檢查 | ❌ | 0.00s | 發現 0 個儀表板 |
| AlertManager功能測試 | ❌ | 0.00s | AlertManager測試異常: Cannot connect to host localhost:9093 ssl:default [Connect call failed ('127.0.0.1', 9093)] |
| AI指標_ai_decision_latency_seconds | ❌ | 0.00s | ai_decision_latency_seconds 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| AI指標_ai_decisions_total | ❌ | 0.00s | ai_decisions_total 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| AI指標_ai_decisions_success_total | ❌ | 0.00s | ai_decisions_success_total 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| AI指標_ai_decisions_error_total | ❌ | 0.00s | ai_decisions_error_total 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| AI指標_handover_success_rate | ❌ | 0.00s | handover_success_rate 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| AI指標_rl_training_progress | ❌ | 0.00s | rl_training_progress 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| AI指標_system_health_score | ❌ | 0.00s | system_health_score 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| Prometheus認證檢查 | ❌ | 0.00s | 認證測試異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| 系統資源使用測試 | ✅ | 1.00s | 記憶體使用: 48.47MB, CPU: 0.0% |
| 故障恢復測試 | ✅ | 0.00s | 故障恢復機制正常（模擬測試） |
| 端到端工作流測試 | ❌ | 0.00s | 工作流測試異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)] |
| 合規檢查_資料保留政策 | ✅ | 0.00s | 資料保留政策符合規範 |
| 合規檢查_審計日誌 | ✅ | 0.00s | 審計日誌功能正常 |
| 合規檢查_備份完整性 | ✅ | 0.00s | 備份完整性檢查通過 |
| 合規檢查_安全配置 | ✅ | 0.00s | 安全配置符合標準 |

## ⚠️ 失敗測試詳情

### 連接測試_Prometheus
- **錯誤訊息**: Prometheus 連接異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### 連接測試_AlertManager
- **錯誤訊息**: AlertManager 連接異常: Cannot connect to host localhost:9093 ssl:default [Connect call failed ('127.0.0.1', 9093)]
- **執行時間**: 0.01s

### 連接測試_NetStack API
- **錯誤訊息**: NetStack API 連接異常: Cannot connect to host localhost:8000 ssl:default [Connect call failed ('127.0.0.1', 8000)]
- **執行時間**: 0.01s

### Prometheus查詢_基本指標查詢
- **錯誤訊息**: 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### Prometheus查詢_AI決策延遲
- **錯誤訊息**: 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### Prometheus查詢_系統CPU使用率
- **錯誤訊息**: 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### Prometheus查詢_決策成功率
- **錯誤訊息**: 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### Grafana儀表板檢查
- **錯誤訊息**: 發現 0 個儀表板
- **執行時間**: 0.00s

### AlertManager功能測試
- **錯誤訊息**: AlertManager測試異常: Cannot connect to host localhost:9093 ssl:default [Connect call failed ('127.0.0.1', 9093)]
- **執行時間**: 0.00s

### AI指標_ai_decision_latency_seconds
- **錯誤訊息**: ai_decision_latency_seconds 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### AI指標_ai_decisions_total
- **錯誤訊息**: ai_decisions_total 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### AI指標_ai_decisions_success_total
- **錯誤訊息**: ai_decisions_success_total 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### AI指標_ai_decisions_error_total
- **錯誤訊息**: ai_decisions_error_total 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### AI指標_handover_success_rate
- **錯誤訊息**: handover_success_rate 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### AI指標_rl_training_progress
- **錯誤訊息**: rl_training_progress 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### AI指標_system_health_score
- **錯誤訊息**: system_health_score 查詢異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### Prometheus認證檢查
- **錯誤訊息**: 認證測試異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s

### 端到端工作流測試
- **錯誤訊息**: 工作流測試異常: Cannot connect to host localhost:9090 ssl:default [Connect call failed ('127.0.0.1', 9090)]
- **執行時間**: 0.00s


## 📈 性能指標

### Grafana健康檢查
- **commit**: ff85ec33c5
- **database**: ok
- **version**: 10.1.0

### Grafana儀表板檢查
- **dashboard_count**: 0

### 系統資源使用測試
- **memory_usage_mb**: 48.46875
- **cpu_percent**: 0.0

