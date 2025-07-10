# NTN Stack 故障排除指南

## 🔧 快速診斷指令

```bash
# 系統狀態快速檢查
alias ntn-check='curl -s http://localhost:8080/health && echo "API: OK" || echo "API: FAIL"'
alias ntn-metrics='curl -s http://localhost:8080/metrics | grep -E "(decision_latency|success_rate)"'
alias ntn-logs='docker logs netstack-api --tail 50'
alias ntn-status='docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
```

---

## ❌ 常見問題診斷流程

### 1. API 服務無響應

#### 症狀
- HTTP 請求超時
- 連接被拒絕
- 健康檢查失敗

#### 診斷步驟
```bash
# Step 1: 檢查服務狀態
docker ps | grep netstack-api
# 期望: Up 狀態

# Step 2: 檢查端口監聽
netstat -tlnp | grep 8080
# 期望: LISTEN 狀態

# Step 3: 檢查日誌
docker logs netstack-api --tail 100 | grep -i error

# Step 4: 檢查資源使用
docker stats netstack-api --no-stream
```

#### 可能原因和解決方案

| 原因 | 診斷方法 | 解決方案 |
|------|----------|----------|
| 服務未啟動 | `docker ps` | `docker restart netstack-api` |
| 端口被佔用 | `lsof -i :8080` | 終止佔用進程或改端口 |
| 記憶體不足 | `free -h` | 清理記憶體或增加資源 |
| 配置錯誤 | 檢查配置文件 | 修正配置並重啟 |

### 2. 決策延遲過高

#### 症狀
- 決策延遲 > 20ms
- Grafana 顯示延遲告警
- 用戶體驗緩慢

#### 診斷步驟
```bash
# Step 1: 檢查當前延遲
curl -s http://localhost:8080/metrics | grep decision_latency_avg

# Step 2: 檢查 CPU 負載
top -p $(pidof python3)

# Step 3: 檢查記憶體使用
ps aux --sort=-%mem | head -10

# Step 4: 檢查 I/O 等待
iostat -x 1 3
```

#### 性能調優策略

```python
# 調優參數建議
PERFORMANCE_CONFIG = {
    # 增加決策並行度
    "max_concurrent_decisions": 200,
    
    # 優化快取策略
    "cache_size": 50000,
    "cache_ttl_seconds": 300,
    
    # 調整線程池
    "thread_pool_size": 32,
    
    # 優化模型推理
    "batch_inference": True,
    "max_batch_size": 16
}
```

### 3. RL 訓練不收斂

#### 症狀
- 獎勵函數波動大
- 損失函數不下降
- 模型性能無改善

#### 診斷步驟
```bash
# Step 1: 檢查訓練狀態
curl http://localhost:8080/api/v1/rl/status

# Step 2: 查看訓練日誌
docker logs netstack-api | grep -i "training\|reward\|loss"

# Step 3: 檢查 Grafana RL 監控
# 訪問: http://localhost:3000/d/rl-training-monitor

# Step 4: 驗證訓練數據
python3 -c "
import redis
r = redis.Redis()
print('Training samples:', r.llen('rl:training:samples'))
"
```

#### 訓練調優建議

```yaml
# DQN 訓練調優
dqn_troubleshooting:
  # 學習率太高 - 降低學習率
  learning_rate: 0.0001  # 從 0.001 降至 0.0001
  
  # 探索不足 - 增加探索率
  exploration_rate: 0.3  # 從 0.1 增至 0.3
  
  # 目標網路更新太頻繁
  target_update_frequency: 2000  # 從 1000 增至 2000
  
  # 經驗回放緩衝區太小
  memory_size: 500000  # 從 100000 增至 500000

# PPO 訓練調優  
ppo_troubleshooting:
  # 策略更新步長太大
  clip_ratio: 0.1  # 從 0.2 降至 0.1
  
  # 學習率太高
  learning_rate: 0.00001  # 從 0.0003 降至 0.00001
  
  # 價值函數權重過大
  value_loss_coefficient: 0.25  # 從 0.5 降至 0.25
```

### 4. 記憶體洩漏問題

#### 症狀
- 記憶體使用持續增長
- 系統變慢或崩潰
- OOM (Out of Memory) 錯誤

#### 診斷步驟
```bash
# Step 1: 監控記憶體趨勢
watch -n 5 'free -h && ps aux --sort=-%mem | head -5'

# Step 2: 檢查 Python 對象
python3 -c "
import psutil, os
process = psutil.Process(os.getpid())
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Step 3: 使用記憶體分析工具
pip install memory_profiler
python -m memory_profiler netstack_api/main.py

# Step 4: 檢查 Redis 記憶體
redis-cli info memory | grep used_memory_human
```

#### 記憶體優化方案
```python
# 記憶體優化配置
MEMORY_CONFIG = {
    # 限制快取大小
    "max_cache_size": "1GB",
    
    # 定期清理
    "cache_cleanup_interval": 3600,
    
    # 限制訓練批次
    "max_training_batch_size": 64,
    
    # 垃圾回收調優
    "gc_threshold": (700, 10, 10)
}

# Python 代碼優化
import gc
import threading

def memory_cleanup():
    """定期記憶體清理"""
    while True:
        gc.collect()
        time.sleep(300)  # 每5分鐘清理一次

threading.Thread(target=memory_cleanup, daemon=True).start()
```

### 5. 資料庫連接問題

#### 症狀
- Redis 連接失敗
- 資料讀取錯誤
- 連接池耗盡

#### 診斷步驟
```bash
# Step 1: 檢查 Redis 服務
docker ps | grep redis
redis-cli ping

# Step 2: 檢查連接數
redis-cli info clients | grep connected_clients

# Step 3: 檢查記憶體使用
redis-cli info memory

# Step 4: 測試連接性能
redis-cli --latency -i 1
```

#### 連接優化方案
```python
# Redis 連接池優化
REDIS_CONFIG = {
    "max_connections": 50,
    "connection_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True,
    "health_check_interval": 30
}

# 連接重試機制
import redis
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_redis_connection():
    return redis.Redis(
        host='localhost',
        port=6379,
        **REDIS_CONFIG
    )
```

---

## 🔍 錯誤代碼解析

### AI 決策引擎錯誤

| 錯誤代碼 | 描述 | 原因 | 解決方案 |
|----------|------|------|----------|
| `AI_001` | 決策超時 | 模型推理時間過長 | 優化模型或增加超時時間 |
| `AI_002` | 候選為空 | 沒有可用的衛星候選 | 檢查衛星狀態和覆蓋範圍 |
| `AI_003` | 模型載入失敗 | 模型文件損壞或路徑錯誤 | 重新載入備份模型 |
| `AI_004` | 參數驗證失敗 | 輸入參數格式錯誤 | 檢查API調用參數 |

### RL 訓練錯誤

| 錯誤代碼 | 描述 | 原因 | 解決方案 |
|----------|------|------|----------|
| `RL_001` | 訓練數據不足 | 經驗回放緩衝區為空 | 增加數據收集時間 |
| `RL_002` | 梯度爆炸 | 學習率過高 | 降低學習率或使用梯度裁剪 |
| `RL_003` | 模型發散 | 訓練不穩定 | 調整超參數或重新初始化 |
| `RL_004` | 環境重置失敗 | 模擬環境異常 | 重啟模擬環境 |

### 系統級錯誤

| 錯誤代碼 | 描述 | 原因 | 解決方案 |
|----------|------|------|----------|
| `SYS_001` | 記憶體不足 | 系統資源耗盡 | 清理記憶體或重啟服務 |
| `SYS_002` | 磁盤空間不足 | 日誌或數據文件過大 | 清理磁盤空間 |
| `SYS_003` | 網路連接失敗 | 網路配置或防火牆問題 | 檢查網路設置 |
| `SYS_004` | 權限拒絕 | 文件或目錄權限問題 | 調整文件權限 |

---

## 🔧 診斷工具腳本

### 自動診斷腳本
```bash
#!/bin/bash
# ntn_diagnosis.sh - NTN Stack 自動診斷工具

echo "=== NTN Stack 系統診斷 ==="
echo "開始時間: $(date)"
echo

# 1. 基本服務檢查
echo "1. 服務狀態檢查"
services=("netstack-api" "redis" "prometheus" "grafana")
for service in "${services[@]}"; do
    if docker ps | grep -q $service; then
        echo "  ✅ $service: 運行中"
    else
        echo "  ❌ $service: 未運行"
    fi
done
echo

# 2. API 健康檢查
echo "2. API 健康檢查"
if curl -s http://localhost:8080/health > /dev/null; then
    echo "  ✅ API 健康檢查: 通過"
else
    echo "  ❌ API 健康檢查: 失敗"
fi
echo

# 3. 資源使用檢查
echo "3. 系統資源檢查"
cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
memory_usage=$(free | grep Mem | awk '{printf("%.1f", $3/$2 * 100.0)}')

echo "  CPU 使用率: ${cpu_usage}%"
echo "  記憶體使用率: ${memory_usage}%"

if (( $(echo "$cpu_usage > 80" | bc -l) )); then
    echo "  ⚠️ CPU 使用率過高"
fi

if (( $(echo "$memory_usage > 90" | bc -l) )); then
    echo "  ⚠️ 記憶體使用率過高"
fi
echo

# 4. 決策性能檢查
echo "4. AI 決策性能檢查"
if command -v curl > /dev/null; then
    latency=$(curl -s http://localhost:8080/metrics | grep decision_latency_avg | awk '{print $2}')
    if [ ! -z "$latency" ]; then
        echo "  平均決策延遲: ${latency}s"
        if (( $(echo "$latency > 0.02" | bc -l) )); then
            echo "  ⚠️ 決策延遲過高"
        fi
    else
        echo "  ❌ 無法獲取決策延遲指標"
    fi
fi
echo

# 5. 錯誤日誌檢查
echo "5. 錯誤日誌檢查"
error_count=$(docker logs netstack-api --since=1h | grep -i error | wc -l)
echo "  過去1小時錯誤數量: $error_count"
if [ $error_count -gt 10 ]; then
    echo "  ⚠️ 錯誤數量過多，建議檢查日誌"
fi

echo
echo "=== 診斷完成 ==="
echo "結束時間: $(date)"
```

### 性能基準測試腳本
```bash
#!/bin/bash
# performance_benchmark.sh - 性能基準測試

echo "=== NTN Stack 性能基準測試 ==="

# 1. API 響應時間測試
echo "1. API 響應時間測試"
for i in {1..10}; do
    response_time=$(curl -w "%{time_total}" -s -o /dev/null http://localhost:8080/health)
    echo "  測試 $i: ${response_time}s"
done
echo

# 2. 決策處理能力測試
echo "2. 決策處理能力測試"
start_time=$(date +%s)
for i in {1..100}; do
    curl -s http://localhost:8080/api/v1/ai_decision_integration/decide \
         -H "Content-Type: application/json" \
         -d '{"user_id": "test", "current_satellite": "sat1", "candidates": ["sat2", "sat3"]}' \
         > /dev/null
done
end_time=$(date +%s)
duration=$((end_time - start_time))
throughput=$((100 / duration))
echo "  處理100個決策請求用時: ${duration}s"
echo "  決策處理吞吐量: ${throughput} 決策/秒"
```

---

## 📋 問題報告模板

當遇到問題時，請使用以下模板報告：

```markdown
## 問題報告

**問題標題**: [簡短描述問題]

**發生時間**: [具體時間]

**影響範圍**: [受影響的功能或用戶]

**問題描述**: 
[詳細描述問題現象]

**錯誤訊息**:
```
[貼上相關錯誤訊息]
```

**重現步驟**:
1. 
2. 
3. 

**系統環境**:
- OS版本: 
- Docker版本: 
- NTN Stack版本: 

**已嘗試的解決方案**:
- [ ] 重啟服務
- [ ] 檢查日誌
- [ ] 清理緩存
- [ ] 其他: 

**相關截圖**: [如有請附上]

**聯繫資訊**: [報告人員資訊]
```

---

## 🆘 緊急聯繫資訊

- **一般技術支援**: support@ntn-stack.com
- **緊急故障熱線**: +886-2-xxxx-xxxx
- **線上支援**: https://support.ntn-stack.com
- **文檔問題回報**: docs@ntn-stack.com

**文檔版本**: v1.0.0  
**最後更新**: 2024年12月  
**維護團隊**: NTN Stack 技術支援團隊