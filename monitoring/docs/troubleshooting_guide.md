# 🔧 NTN Stack AI決策引擎故障排除指南

## 📋 目錄

1. [快速診斷流程](#快速診斷流程)
2. [常見問題解決方案](#常見問題解決方案)
3. [錯誤代碼參考](#錯誤代碼參考)
4. [性能問題診斷](#性能問題診斷)
5. [網絡連接問題](#網絡連接問題)
6. [日誌分析指南](#日誌分析指南)
7. [緊急故障處理](#緊急故障處理)

---

## 🚀 快速診斷流程

### 🔍 第一步：系統健康檢查 (2分鐘)

```bash
#!/bin/bash
# 快速系統診斷腳本
echo "🔍 NTN Stack 快速診斷..."

# 1. 檢查服務狀態
echo "1. 檢查服務狀態:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep ntn

# 2. 檢查關鍵端點
echo -e "\n2. 檢查關鍵端點:"
services=("localhost:8080/health" "localhost:3000/api/health" "localhost:9090/-/healthy")
for service in "${services[@]}"; do
    if curl -s -f "http://$service" > /dev/null; then
        echo "✅ $service - OK"
    else
        echo "❌ $service - FAIL"
    fi
done

# 3. 檢查關鍵指標
echo -e "\n3. 檢查關鍵指標:"
LATENCY=$(curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(ai_decision_latency_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1]' 2>/dev/null)
SUCCESS_RATE=$(curl -s "http://localhost:9090/api/v1/query?query=rate(ntn_decisions_success_total[5m])/rate(ntn_decisions_total[5m])" | jq -r '.data.result[0].value[1]' 2>/dev/null)

echo "決策延遲 (95%): ${LATENCY:-"N/A"} 秒"
echo "成功率: ${SUCCESS_RATE:-"N/A"}"

# 4. 檢查活躍告警
echo -e "\n4. 活躍告警:"
ALERTS=$(curl -s "http://localhost:9093/api/v1/alerts" | jq -r '.data[] | select(.state=="firing") | .labels.alertname' 2>/dev/null)
if [[ -n "$ALERTS" ]]; then
    echo "$ALERTS"
else
    echo "✅ 無活躍告警"
fi
```

### 🎯 診斷決策樹

```
系統問題 
├── 服務無響應？
│   ├── Yes → 檢查服務狀態 → 重啟服務
│   └── No → 繼續檢查
├── 性能問題？
│   ├── 延遲過高 → 檢查資源使用 → 調優參數
│   ├── 成功率低 → 檢查錯誤日誌 → 修復錯誤
│   └── 吞吐量低 → 檢查瓶頸 → 擴容
└── 告警觸發？
    ├── Critical → 緊急處理程序
    ├── Warning → 調查根本原因
    └── Info → 記錄並監控
```

---

## 🛠️ 常見問題解決方案

### 🚨 問題1：AI決策延遲過高

**症狀**:
- Grafana儀表板顯示延遲 > 20ms
- 告警: `AIDecisionLatencyCritical`
- 用戶報告衛星切換慢

**診斷步驟**:
```bash
# 1. 檢查當前延遲
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(ai_decision_latency_seconds_bucket[5m]))" | jq '.data.result[0].value[1]'

# 2. 檢查系統資源
docker stats netstack-api --no-stream
top -p $(pgrep -f netstack-api)

# 3. 檢查決策隊列
curl http://localhost:8080/api/v1/ai_decision_integration/metrics | grep -E "(queue|pending)"

# 4. 檢查資料庫連接
psql -d ntn_stack -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"
```

**解決方案**:

1. **增加決策引擎並發數**:
```bash
# 調整worker數量
redis-cli HSET ai_decision_config worker_threads 8
redis-cli HSET ai_decision_config batch_size 64
```

2. **優化資料庫查詢**:
```sql
-- 檢查慢查詢
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 5;

-- 添加索引 (如果需要)
CREATE INDEX CONCURRENTLY idx_satellites_elevation ON satellites(elevation);
```

3. **增加系統資源**:
```yaml
# docker-compose.yml
services:
  netstack-api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
```

4. **啟用決策緩存**:
```bash
redis-cli HSET ai_decision_config enable_cache true
redis-cli HSET ai_decision_config cache_ttl_seconds 300
```

### 🔄 問題2：RL訓練停滯

**症狀**:
- 告警: `RLTrainingStalled`
- 訓練進度不變超過10分鐘
- GPU使用率異常

**診斷步驟**:
```bash
# 1. 檢查訓練狀態
curl http://localhost:8080/api/v1/rl/status | jq '.'

# 2. 檢查GPU狀態
nvidia-smi
nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits

# 3. 檢查訓練日誌
docker logs netstack-rl-trainer --tail=100 | grep -E "(error|warning|epoch|loss)"

# 4. 檢查數據流
curl http://localhost:8080/api/v1/rl/metrics | jq '.training_data_flow'
```

**解決方案**:

1. **重啟訓練進程**:
```bash
# 優雅重啟
curl -X POST http://localhost:8080/api/v1/rl/control \
  -H "Content-Type: application/json" \
  -d '{"action": "restart", "algorithm": "dqn", "graceful": true}'
```

2. **調整學習率**:
```python
# 通過API動態調整
import requests
config = {
    "learning_rate": 0.0001,  # 降低學習率
    "batch_size": 32,         # 減小批次大小
    "epsilon": 0.05           # 降低探索率
}
requests.put("http://localhost:8080/api/v1/rl/config", json=config)
```

3. **清理訓練數據**:
```bash
# 清理損壞的checkpoints
docker exec netstack-rl-trainer rm -rf /app/checkpoints/corrupted_*

# 重置訓練狀態
redis-cli DEL rl_training_state:dqn
```

### 📊 問題3：Grafana儀表板無數據

**症狀**:
- 儀表板顯示"No data"
- Prometheus有數據但Grafana看不到
- 查詢超時

**診斷步驟**:
```bash
# 1. 檢查Prometheus數據源
curl http://localhost:3000/api/datasources | jq '.[] | select(.type=="prometheus")'

# 2. 檢查Prometheus指標
curl "http://localhost:9090/api/v1/label/__name__/values" | jq '.data' | grep ai_decision

# 3. 檢查查詢語法
curl -G "http://localhost:9090/api/v1/query" \
  --data-urlencode 'query=ai_decision_latency_seconds' | jq '.data.result'

# 4. 檢查時間範圍
curl -G "http://localhost:9090/api/v1/query_range" \
  --data-urlencode 'query=ai_decision_latency_seconds' \
  --data-urlencode 'start=2024-12-20T00:00:00Z' \
  --data-urlencode 'end=2024-12-20T23:59:59Z' \
  --data-urlencode 'step=60s'
```

**解決方案**:

1. **修復數據源連接**:
```bash
# 重啟Grafana
docker-compose restart grafana

# 檢查數據源配置
curl -X GET http://admin:ntn-admin-2024@localhost:3000/api/datasources/1
```

2. **修復查詢語法**:
```promql
# 正確的查詢語法示例
histogram_quantile(0.95, rate(ai_decision_latency_seconds_bucket[5m]))
rate(ntn_decisions_total[1m])
increase(ntn_decisions_error_total[5m])
```

3. **檢查指標標籤**:
```bash
# 查看可用標籤
curl "http://localhost:9090/api/v1/series?match[]=ai_decision_latency_seconds" | jq '.data[0]'
```

### 🗄️ 問題4：資料庫連接問題

**症狀**:
- 錯誤: "connection refused"
- 大量超時錯誤
- 連接池耗盡

**診斷步驟**:
```bash
# 1. 檢查PostgreSQL狀態
docker ps | grep postgres
docker logs postgres-container --tail=50

# 2. 檢查連接數
psql -d ntn_stack -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 3. 檢查慢查詢
psql -d ntn_stack -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5;"

# 4. 檢查鎖等待
psql -d ntn_stack -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

**解決方案**:

1. **調整連接池設置**:
```python
# 在應用配置中
DATABASE_CONFIG = {
    "max_connections": 100,
    "min_connections": 10,
    "connection_timeout": 30,
    "idle_timeout": 300,
    "max_lifetime": 3600
}
```

2. **優化PostgreSQL配置**:
```sql
-- 調整連接相關參數
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
```

3. **清理殭屍連接**:
```sql
-- 終止閒置連接
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND state_change < now() - interval '1 hour';
```

---

## 📟 錯誤代碼參考

### AI決策引擎錯誤代碼

| 錯誤代碼 | 描述 | 解決方案 |
|----------|------|----------|
| `AI_001` | 決策超時 | 增加timeout設置，檢查系統負載 |
| `AI_002` | 候選衛星為空 | 檢查衛星數據源，驗證篩選條件 |
| `AI_003` | RL模型加載失敗 | 檢查模型文件完整性，重新訓練 |
| `AI_004` | 參數驗證失敗 | 檢查輸入參數格式和範圍 |
| `AI_005` | 資源不足 | 增加系統資源，優化內存使用 |

### 系統級錯誤代碼

| 錯誤代碼 | 描述 | 解決方案 |
|----------|------|----------|
| `SYS_001` | 服務啟動失敗 | 檢查配置文件，查看詳細日誌 |
| `SYS_002` | 內存不足 | 清理緩存，增加系統內存 |
| `SYS_003` | 磁碟空間不足 | 清理日誌文件，擴展磁碟 |
| `SYS_004` | 網絡連接失敗 | 檢查網絡配置，防火牆設置 |
| `SYS_005` | 權限拒絕 | 檢查文件權限，用戶權限 |

### API錯誤代碼

| HTTP狀態碼 | 錯誤類型 | 常見原因 | 解決方案 |
|------------|----------|----------|----------|
| 400 | Bad Request | 請求參數錯誤 | 檢查API文檔，驗證參數格式 |
| 401 | Unauthorized | 認證失敗 | 檢查API密鑰，重新認證 |
| 403 | Forbidden | 權限不足 | 檢查用戶權限設置 |
| 404 | Not Found | 端點不存在 | 檢查URL路徑，API版本 |
| 429 | Too Many Requests | 請求過於頻繁 | 實施請求限流，增加延遲 |
| 500 | Internal Server Error | 服務器內部錯誤 | 檢查服務器日誌，重啟服務 |
| 503 | Service Unavailable | 服務不可用 | 檢查服務狀態，等待恢復 |

---

## 📊 性能問題診斷

### 🎯 延遲問題診斷

**診斷命令**:
```bash
# 1. 端到端延遲測試
for i in {1..10}; do
    start_time=$(date +%s.%N)
    curl -s http://localhost:8080/api/v1/ai_decision_integration/decide \
      -H "Content-Type: application/json" \
      -d '{"ue_id": "test_'$i'", "current_satellite": "sat_1"}' > /dev/null
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    echo "Request $i: ${duration}s"
done

# 2. 各階段延遲分析
curl http://localhost:8080/api/v1/ai_decision_integration/metrics | jq '.latency_breakdown'

# 3. 資源瓶頸檢查
iostat -x 1 5
sar -u 1 5
```

**性能閾值**:
- **目標延遲**: < 15ms (95%百分位)
- **警告閾值**: 15-20ms
- **嚴重閾值**: > 20ms
- **緊急閾值**: > 50ms

### 💾 內存問題診斷

**檢查內存使用**:
```bash
# 1. 系統內存使用
free -h
cat /proc/meminfo | grep -E "(MemTotal|MemAvailable|MemFree)"

# 2. Docker容器內存
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# 3. Python進程內存（如果適用）
pip install psutil
python3 -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# 4. 檢查內存洩漏
valgrind --tool=memcheck --leak-check=full python3 app.py
```

**內存優化建議**:
```python
# 設置Python內存限制
import resource
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))  # 2GB

# 啟用垃圾回收
import gc
gc.set_threshold(700, 10, 10)
gc.collect()
```

### 🔄 吞吐量問題診斷

**壓力測試**:
```bash
# 1. 使用ab進行壓力測試
ab -n 1000 -c 10 -T application/json -p test_payload.json \
  http://localhost:8080/api/v1/ai_decision_integration/decide

# 2. 使用wrk進行更詳細的測試
wrk -t12 -c400 -d30s --script=post.lua \
  http://localhost:8080/api/v1/ai_decision_integration/decide

# 3. 監控吞吐量指標
watch -n 1 'curl -s "http://localhost:9090/api/v1/query?query=rate(ntn_decisions_total[1m])" | jq ".data.result[0].value[1]"'
```

---

## 🌐 網絡連接問題

### 🔗 服務間通信診斷

**檢查服務連接**:
```bash
# 1. 檢查端口監聽
netstat -tlnp | grep -E "(8080|9090|3000|6379)"

# 2. 測試服務間連接
docker exec netstack-api curl -I http://prometheus:9090/api/v1/status/config
docker exec grafana curl -I http://prometheus:9090/api/v1/label/__name__/values

# 3. 檢查DNS解析
docker exec netstack-api nslookup prometheus
docker exec netstack-api ping -c 3 redis

# 4. 檢查防火牆規則
iptables -L -n | grep -E "(8080|9090|3000)"
```

**網絡配置檢查**:
```bash
# 1. Docker網絡檢查
docker network ls
docker network inspect ntn-monitoring

# 2. 檢查容器網絡配置
docker inspect netstack-api | jq '.[0].NetworkSettings'

# 3. 測試外部連接
curl -I http://localhost:8080/health
curl -I http://localhost:9090/-/healthy
curl -I http://localhost:3000/api/health
```

### 🛡️ 防火牆和安全診斷

**安全檢查**:
```bash
# 1. 檢查iptables規則
sudo iptables -L -n -v

# 2. 檢查SELinux狀態
sestatus
getenforce

# 3. 檢查Docker守護進程日誌
journalctl -u docker.service --since "1 hour ago"

# 4. 檢查SSL證書（如果使用HTTPS）
openssl s_client -connect localhost:443 -servername localhost
```

---

## 📋 日誌分析指南

### 📂 關鍵日誌文件位置

```bash
# 主要服務日誌
NETSTACK_LOGS="docker logs netstack-api"
RL_LOGS="docker logs netstack-rl-trainer"
PROMETHEUS_LOGS="docker logs ntn-prometheus"
GRAFANA_LOGS="docker logs ntn-grafana"
ALERTMANAGER_LOGS="docker logs ntn-alertmanager"

# 系統日誌
SYSTEM_LOGS="/var/log/messages"
DOCKER_LOGS="journalctl -u docker.service"
```

### 🔍 日誌搜索模式

**錯誤搜索**:
```bash
# 1. 搜索關鍵錯誤
docker logs netstack-api 2>&1 | grep -E "(ERROR|CRITICAL|FATAL)" | tail -20

# 2. 搜索特定時間範圍
docker logs netstack-api --since="2024-12-20T10:00:00" --until="2024-12-20T11:00:00"

# 3. 搜索決策相關錯誤
docker logs netstack-api 2>&1 | grep -E "(decision|timeout|failed)" | tail -10

# 4. 搜索性能相關日誌
docker logs netstack-api 2>&1 | grep -E "(latency|slow|performance)" | tail -10
```

**日誌分析腳本**:
```bash
#!/bin/bash
# log_analyzer.sh - 自動日誌分析腳本

LOG_FILE="${1:-netstack-api}"
TIME_RANGE="${2:-1h}"

echo "🔍 分析 $LOG_FILE 最近 $TIME_RANGE 的日誌..."

# 錯誤統計
echo -e "\n📊 錯誤統計:"
docker logs $LOG_FILE --since="$TIME_RANGE" 2>&1 | \
grep -E "(ERROR|WARN)" | \
awk '{print $3}' | sort | uniq -c | sort -nr

# 性能指標
echo -e "\n⚡ 性能指標:"
docker logs $LOG_FILE --since="$TIME_RANGE" 2>&1 | \
grep -E "latency|duration" | \
awk '{print $NF}' | sort -n | tail -10

# 頻繁錯誤
echo -e "\n🚨 頻繁錯誤 (Top 5):"
docker logs $LOG_FILE --since="$TIME_RANGE" 2>&1 | \
grep ERROR | \
cut -d' ' -f4- | sort | uniq -c | sort -nr | head -5
```

### 📈 日誌監控指標

**設置日誌告警**:
```yaml
# prometheus.yml
- job_name: 'log-monitoring'
  static_configs:
    - targets: ['localhost:9090']
  metric_relabel_configs:
    - source_labels: [__name__]
      regex: '.*_log_errors_total'
      target_label: log_level
      replacement: 'error'
```

**日誌輪轉設置**:
```bash
# /etc/logrotate.d/ntn-stack
/var/log/ntn-stack/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ntn-stack ntn-stack
    postrotate
        docker kill -s USR1 netstack-api
    endscript
}
```

---

## 🚑 緊急故障處理

### 🔥 緊急處理檢查清單

**Level 1 - 立即響應 (0-5分鐘)**:
- [ ] 確認故障影響範圍
- [ ] 通知關鍵人員
- [ ] 啟動緊急模式
- [ ] 切換到備用系統

**Level 2 - 快速修復 (5-30分鐘)**:
- [ ] 收集故障信息
- [ ] 嘗試快速修復
- [ ] 監控系統恢復
- [ ] 準備回滾計劃

**Level 3 - 根本修復 (30分鐘-2小時)**:
- [ ] 深入根本原因分析
- [ ] 實施永久修復
- [ ] 進行全面測試
- [ ] 更新文檔和流程

### 🛠️ 緊急修復腳本

**快速重啟腳本**:
```bash
#!/bin/bash
# emergency_restart.sh - 緊急重啟腳本

echo "🚨 執行緊急重啟程序..."

# 1. 保存當前狀態
docker-compose logs > /tmp/ntn-stack-emergency-$(date +%Y%m%d_%H%M%S).log

# 2. 優雅停止服務
echo "⏸️  停止服務..."
docker-compose stop

# 3. 清理可能的殭屍進程
echo "🧹 清理進程..."
docker system prune -f

# 4. 重啟服務
echo "🚀 重啟服務..."
docker-compose up -d

# 5. 驗證服務健康
echo "✅ 驗證服務健康..."
sleep 30
./scripts/health_check.sh
```

**數據備份腳本**:
```bash
#!/bin/bash
# emergency_backup.sh - 緊急數據備份

BACKUP_DIR="/tmp/emergency_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "💾 執行緊急數據備份到 $BACKUP_DIR"

# 1. 備份PostgreSQL
pg_dump ntn_stack > $BACKUP_DIR/postgres_emergency.sql

# 2. 備份Redis
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/

# 3. 備份關鍵配置
tar -czf $BACKUP_DIR/configs_emergency.tar.gz \
  monitoring/ netstack/config/ simworld/config/

# 4. 備份日誌
docker-compose logs > $BACKUP_DIR/docker_logs_emergency.log

echo "✅ 緊急備份完成: $BACKUP_DIR"
```

### 📞 升級程序

**升級條件**:
1. **Level 1 → Level 2**: 超過15分鐘無法恢復
2. **Level 2 → Level 3**: 超過1小時無法完全修復
3. **Level 3 → 管理層**: 超過4小時或影響重大

**通知模板**:
```bash
# 發送緊急通知
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-type: application/json' \
  --data '{
    "text": "🚨 NTN Stack 緊急故障",
    "attachments": [{
      "color": "danger",
      "fields": [{
        "title": "故障描述",
        "value": "'$INCIDENT_DESCRIPTION'",
        "short": false
      },{
        "title": "影響範圍", 
        "value": "'$IMPACT_SCOPE'",
        "short": true
      },{
        "title": "預計修復時間",
        "value": "'$ETA'",
        "short": true
      }]
    }]
  }'
```

---

## 📚 相關資源

### 🔗 有用鏈接
- [Prometheus查詢語法](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana文檔](https://grafana.com/docs/)
- [Docker故障排除](https://docs.docker.com/config/daemon/troubleshoot/)
- [PostgreSQL性能調優](https://wiki.postgresql.org/wiki/Performance_Optimization)

### 📋 檢查清單模板
- [日常健康檢查清單](checklists/daily_health_check.md)
- [性能調優檢查清單](checklists/performance_tuning.md)
- [故障處理檢查清單](checklists/incident_response.md)

---

**文檔版本**: v1.0  
**最後更新**: 2024-12-20  
**維護者**: NTN Stack 技術支援團隊  
**緊急聯絡**: emergency@ntn-stack.com 