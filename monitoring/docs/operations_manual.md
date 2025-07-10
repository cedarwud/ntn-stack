# 🚀 NTN Stack AI決策引擎營運手冊

## 📋 目錄

1. [系統架構概覽](#系統架構概覽)
2. [日常營運檢查清單](#日常營運檢查清單)
3. [性能調優指南](#性能調優指南)
4. [監控與告警](#監控與告警)
5. [備份與恢復流程](#備份與恢復流程)
6. [故障排除](#故障排除)
7. [緊急應變程序](#緊急應變程序)

---

## 🏗️ 系統架構概覽

### 核心組件架構

```
┌─────────────────────────────────────────────────────────────┐
│                    監控與營運層                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Prometheus      │  │ Grafana         │  │ AlertManager    │ │
│  │ (指標收集)      │  │ (視覺化儀表板)  │  │ (告警管理)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────┐
│                   AI決策引擎層                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ DecisionOrchestrator │  │ EventProcessor  │  │ CandidateSelector │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ RLDecisionEngine│  │ DecisionExecutor│  │ DecisionMonitor │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────────────────────────────────┐
│                     基礎設施層                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Redis           │  │ PostgreSQL      │  │ Docker          │ │
│  │ (緩存/配置)     │  │ (持久化數據)    │  │ (容器化)        │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 關鍵服務說明

| 服務 | 端口 | 責任 | 關鍵指標 |
|------|------|------|----------|
| NetStack API | 8080 | AI決策引擎主服務 | decision_latency, success_rate |
| SimWorld Backend | 8000 | 模擬環境 | simulation_fps, load_factor |
| Prometheus | 9090 | 指標收集 | targets_up, scrape_duration |
| Grafana | 3000 | 監控儀表板 | dashboard_load_time |
| AlertManager | 9093 | 告警管理 | alerts_firing, notifications |
| Redis | 6379 | 緩存和配置 | memory_usage, hit_rate |

---

## ✅ 日常營運檢查清單

### 🌅 每日檢查 (08:00)

#### 1. 系統健康檢查
```bash
# 檢查所有服務狀態
make status

# 檢查關鍵指標
curl -s http://localhost:9090/api/v1/query?query=up | jq '.data.result'

# 檢查AI決策延遲
curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(ai_decision_latency_seconds_bucket[5m]))" | jq '.data.result[0].value[1]'
```

**✅ 檢查項目**:
- [ ] 所有服務運行正常 (up=1)
- [ ] AI決策延遲 < 15ms (95%百分位)
- [ ] 決策成功率 > 95%
- [ ] 系統吞吐量 > 1000 decisions/sec
- [ ] 無嚴重告警

#### 2. 資源使用檢查
```bash
# 檢查系統資源
docker stats --no-stream

# 檢查磁碟空間
df -h | grep -E "(/$|/var|/tmp)"

# 檢查內存使用
free -h
```

**⚠️ 閾值警告**:
- CPU使用率 > 80%
- 內存使用率 > 85%
- 磁碟使用率 > 90%

#### 3. 日誌檢查
```bash
# 檢查錯誤日誌
make logs | grep -i error | tail -20

# 檢查告警狀態
curl -s http://localhost:9093/api/v1/alerts | jq '.data[] | select(.state=="firing")'
```

### 📊 每週檢查 (週一 09:00)

#### 1. 性能趨勢分析
- 查看過去7天的性能趨勢報告
- 分析RL算法收斂性
- 檢查衛星切換成功率趨勢
- 評估系統資源使用趨勢

#### 2. 告警分析
- 統計過去一週的告警數量和類型
- 分析告警根本原因
- 更新告警規則（如有需要）

#### 3. 備份驗證
```bash
# 驗證數據備份完整性
make backup-verify

# 檢查備份文件
ls -la /backup/ntn-stack/
```

### 🗓️ 每月檢查 (每月1日)

#### 1. 容量規劃
- 評估系統容量需求
- 預測未來3個月的資源需求
- 更新擴容計劃

#### 2. 安全檢查
- 更新系統補丁
- 檢查安全配置
- 審查訪問權限

#### 3. 文檔更新
- 更新營運手冊
- 更新故障排除指南
- 更新聯絡人信息

---

## ⚡ 性能調優指南

### 🎯 AI決策引擎調優

#### 1. 決策延遲優化

**目標**: 95%百分位延遲 < 15ms

**調優參數**:
```python
# 在Redis中設置參數
redis-cli HSET ai_decision_config decision_timeout_ms 10
redis-cli HSET ai_decision_config batch_size 32
redis-cli HSET ai_decision_config worker_threads 4
```

**監控指標**:
```promql
# 決策延遲
histogram_quantile(0.95, rate(ai_decision_latency_seconds_bucket[5m]))

# 吞吐量
rate(ntn_decisions_total[1m])
```

#### 2. RL訓練優化

**參數調整**:
```yaml
# RL配置優化
rl_config:
  learning_rate: 0.001
  batch_size: 64
  replay_buffer_size: 100000
  target_update_freq: 1000
  exploration_rate: 0.1
```

**性能監控**:
```promql
# 訓練收斂速度
rl_training_progress_percent

# 策略損失
rl_policy_loss
```

### 🗄️ 數據庫調優

#### PostgreSQL優化
```sql
-- 檢查查詢性能
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- 調整連接池
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
```

#### Redis優化
```bash
# 設置內存淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET maxmemory 1gb

# 檢查記憶體使用
redis-cli INFO memory
```

### 🐳 Docker容器調優

**資源限制設置**:
```yaml
# docker-compose.yml
services:
  netstack-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

---

## 📊 監控與告警

### 📈 關鍵儀表板

#### 1. NTN Stack 總覽儀表板
- **URL**: http://localhost:3000/d/ntn-ai-overview
- **更新頻率**: 30秒
- **關鍵面板**:
  - AI決策延遲趨勢
  - 決策成功率
  - 系統吞吐量
  - RL算法性能比較

#### 2. 系統健康儀表板
- **URL**: http://localhost:3000/d/system-health
- **監控內容**:
  - 服務可用性
  - 資源使用率
  - 錯誤率統計
  - 告警狀態

### 🚨 告警級別與響應時間

| 級別 | 響應時間 | 通知方式 | 負責團隊 |
|------|----------|----------|----------|
| 🔥 Emergency | 立即 | 電話 + SMS + Email | AI團隊 + CTO |
| 🚨 Critical | 5分鐘內 | SMS + Email + Slack | AI團隊 |
| ⚠️ Warning | 30分鐘內 | Email + Slack | 相關團隊 |
| ℹ️ Info | 4小時內 | Email | 監控團隊 |

### 📱 告警通知配置

**Slack整合**:
```bash
# 設置Slack Webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# 測試告警通知
curl -X POST -H 'Content-type: application/json' \
  --data '{"text":"🚨 測試告警通知"}' \
  $SLACK_WEBHOOK_URL
```

**Email配置**:
```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'ntn-alerts@company.com'
```

---

## 💾 備份與恢復流程

### 📦 備份策略

#### 1. 數據備份
```bash
# 每日備份腳本
#!/bin/bash
BACKUP_DIR="/backup/ntn-stack/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# PostgreSQL備份
pg_dump ntn_stack > $BACKUP_DIR/postgres_backup.sql

# Redis備份
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb $BACKUP_DIR/

# 配置文件備份
tar -czf $BACKUP_DIR/configs.tar.gz \
  monitoring/ \
  netstack/config/ \
  simworld/config/
```

#### 2. 備份驗證
```bash
# 驗證PostgreSQL備份
psql -d test_restore < $BACKUP_DIR/postgres_backup.sql

# 驗證Redis備份
redis-server --dbfilename $BACKUP_DIR/dump.rdb --dir $BACKUP_DIR --port 6380
```

### 🔄 恢復程序

#### 1. 完整系統恢復
```bash
# 1. 停止所有服務
make stop

# 2. 恢復數據庫
psql -d ntn_stack < /backup/latest/postgres_backup.sql

# 3. 恢復Redis
cp /backup/latest/dump.rdb /var/lib/redis/
sudo systemctl restart redis

# 4. 恢復配置
tar -xzf /backup/latest/configs.tar.gz

# 5. 重啟服務
make start
```

#### 2. 單服務恢復
```bash
# 恢復AI決策引擎
docker-compose restart netstack-api

# 檢查服務健康
curl http://localhost:8080/health
```

---

## 🔧 故障排除

### 🚨 常見故障及解決方案

#### 1. AI決策延遲過高 (>20ms)

**症狀**:
- 告警: `AIDecisionLatencyCritical`
- 用戶體驗: 衛星切換延遲

**診斷步驟**:
```bash
# 檢查CPU/內存使用
top -p $(pgrep -f netstack-api)

# 檢查決策隊列長度
curl http://localhost:8080/api/v1/ai_decision_integration/metrics | grep queue

# 檢查資料庫連接
psql -d ntn_stack -c "SELECT count(*) FROM pg_stat_activity;"
```

**解決方案**:
1. 增加決策引擎worker數量
2. 優化資料庫查詢
3. 增加系統資源
4. 啟用決策緩存

#### 2. RL訓練停滯

**症狀**:
- 告警: `RLTrainingStalled`
- 訓練進度不變

**診斷步驟**:
```bash
# 檢查GPU使用率
nvidia-smi

# 檢查訓練日誌
docker logs ntn-rl-trainer | tail -100

# 檢查數據流
curl http://localhost:8080/api/v1/rl/status
```

**解決方案**:
1. 重啟RL訓練進程
2. 調整學習率參數
3. 清理訓練數據
4. 檢查模型收斂條件

#### 3. 服務無響應

**症狀**:
- 告警: `ServiceUnavailable`
- API調用超時

**快速恢復**:
```bash
# 1. 確認服務狀態
docker ps | grep ntn

# 2. 重啟失效服務
docker-compose restart <service-name>

# 3. 檢查網絡連接
netstat -tlnp | grep :8080

# 4. 檢查資源限制
docker stats
```

### 🔍 日誌分析指南

#### 關鍵日誌文件
```bash
# AI決策引擎日誌
docker logs netstack-api | grep "ai_decision"

# RL訓練日誌
docker logs rl-trainer | grep "training"

# 系統錯誤日誌
journalctl -u docker | grep ERROR

# 告警日誌
docker logs alertmanager | tail -50
```

#### 常見錯誤模式
```bash
# 內存不足
grep "OutOfMemory\|OOM" /var/log/messages

# 數據庫連接問題
grep "connection refused\|timeout" /app/logs/*.log

# GPU問題
grep "CUDA\|GPU" /app/logs/rl_training.log
```

---

## 🚑 緊急應變程序

### 🔥 Level 1: 系統嚴重故障

**觸發條件**:
- AI決策成功率 < 90%
- 系統延遲 > 50ms
- 多個關鍵服務宕機

**立即行動** (5分鐘內):
```bash
# 1. 啟動緊急模式
python3 netstack/monitoring/operations/emergency_mode.py --activate

# 2. 切換到備用算法
curl -X POST http://localhost:8080/api/v1/ai_decision_integration/emergency \
  -d '{"mode": "fallback", "algorithm": "rule_based"}'

# 3. 通知關鍵人員
python3 scripts/emergency_notification.py --level=critical
```

**後續行動** (30分鐘內):
1. 分析故障根本原因
2. 制定修復計劃
3. 準備回滾方案
4. 與業務團隊溝通影響

### ⚠️ Level 2: 性能降級

**觸發條件**:
- 決策延遲 20-50ms
- 成功率 90-95%
- 單一服務問題

**應對措施**:
```bash
# 1. 增加監控頻率
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# 2. 調整系統參數
redis-cli HSET ai_config decision_timeout_ms 15

# 3. 準備擴容
docker-compose up --scale netstack-api=3
```

### 📞 緊急聯絡清單

| 角色 | 姓名 | 電話 | Email | 責任範圍 |
|------|------|------|-------|----------|
| AI團隊主管 | 張三 | +886-912-345-678 | ai-lead@company.com | AI決策引擎 |
| 系統管理員 | 李四 | +886-923-456-789 | sysadmin@company.com | 基礎設施 |
| 資料庫管理員 | 王五 | +886-934-567-890 | dba@company.com | 數據庫 |
| 值班經理 | 陳六 | +886-945-678-901 | oncall@company.com | 總體協調 |

### 📋 事故處理流程

1. **事故發現** (0-5分鐘)
   - 自動告警觸發
   - 值班人員確認
   - 初步影響評估

2. **緊急響應** (5-15分鐘)
   - 通知相關團隊
   - 啟動緊急程序
   - 實施臨時修復

3. **問題解決** (15分鐘-2小時)
   - 根本原因分析
   - 永久修復方案
   - 系統恢復驗證

4. **事後檢討** (24-48小時)
   - 事故總結報告
   - 改進措施制定
   - 文檔和流程更新

---

## 📚 相關文檔

- [故障排除指南](troubleshooting_guide.md)
- [API參考文檔](../api/README.md)
- [系統架構文檔](../architecture/README.md)
- [監控配置指南](monitoring_configuration.md)

---

**文檔版本**: v1.0  
**最後更新**: 2024-12-20  
**維護者**: NTN Stack 營運團隊  
**審核者**: AI決策引擎團隊主管 