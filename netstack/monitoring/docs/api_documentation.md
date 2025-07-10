# NTN Stack API 文檔

## 📋 概覽

NTN Stack API 提供完整的衛星網路決策管理和監控功能，包括 AI 決策引擎、強化學習訓練、系統監控等核心服務。

### 基本資訊
- **Base URL**: `http://localhost:8080`
- **API 版本**: v1
- **認證方式**: API Key (開發環境可選)
- **響應格式**: JSON
- **字符編碼**: UTF-8

---

## 🔧 核心 API 端點

### 1. 系統健康檢查

#### GET /health
檢查系統整體健康狀態

**響應示例**:
```json
{
    "status": "healthy",
    "timestamp": "2024-12-20T10:30:00Z",
    "services": {
        "ai_engine": "running",
        "rl_trainer": "running", 
        "redis": "connected",
        "database": "connected"
    },
    "version": "1.0.0"
}
```

#### GET /metrics
獲取 Prometheus 格式的系統指標

**響應格式**: Prometheus metrics format
```
# HELP ai_decision_latency_seconds AI decision processing latency
ai_decision_latency_seconds{quantile="0.5"} 0.015
ai_decision_latency_seconds{quantile="0.95"} 0.025
ai_decision_latency_seconds{quantile="0.99"} 0.045

# HELP ai_decision_success_rate AI decision success rate
ai_decision_success_rate 0.987
```

---

## 🤖 AI 決策 API

### 2. 衛星決策

#### POST /api/v1/ai_decision_integration/decide
執行衛星切換決策

**請求參數**:
```json
{
    "user_id": "string (required)",
    "current_satellite": "string (required)",
    "candidates": ["string"] (required),
    "context": {
        "signal_strength": "number (optional)",
        "user_location": {
            "latitude": "number",
            "longitude": "number"
        },
        "priority": "high|medium|low (optional, default: medium)"
    }
}
```

**響應示例**:
```json
{
    "decision": {
        "recommended_satellite": "sat_003",
        "confidence": 0.95,
        "reasoning": "最佳信號強度和延遲組合",
        "alternatives": [
            {
                "satellite": "sat_007", 
                "confidence": 0.87,
                "reason": "次佳選擇"
            }
        ]
    },
    "metadata": {
        "processing_time_ms": 12,
        "model_version": "v2.1.0",
        "timestamp": "2024-12-20T10:30:15Z"
    }
}
```

**錯誤響應**:
```json
{
    "error": {
        "code": "AI_002",
        "message": "無可用候選衛星",
        "details": "candidates 陣列為空或所有候選都不可用"
    }
}
```

### 3. 決策歷史

#### GET /api/v1/ai_decision_integration/history
獲取決策歷史記錄

**查詢參數**:
- `user_id`: 用戶ID (optional)
- `start_time`: 開始時間 ISO 8601 (optional)
- `end_time`: 結束時間 ISO 8601 (optional)
- `limit`: 返回記錄數量 (default: 100, max: 1000)
- `offset`: 偏移量 (default: 0)

**響應示例**:
```json
{
    "decisions": [
        {
            "id": "dec_123456",
            "user_id": "user_001",
            "timestamp": "2024-12-20T10:30:15Z",
            "current_satellite": "sat_001",
            "recommended_satellite": "sat_003",
            "confidence": 0.95,
            "processing_time_ms": 12,
            "executed": true
        }
    ],
    "pagination": {
        "total": 1500,
        "limit": 100,
        "offset": 0,
        "has_more": true
    }
}
```

---

## 🧠 強化學習 API

### 4. RL 訓練控制

#### GET /api/v1/rl/status
獲取 RL 訓練狀態

**響應示例**:
```json
{
    "training_status": "running",
    "current_algorithm": "DQN",
    "episode": 2450,
    "total_episodes": 10000,
    "current_reward": 125.7,
    "average_reward": 98.3,
    "epsilon": 0.15,
    "learning_rate": 0.001,
    "training_time": "02:34:12",
    "model_version": "v2.1.0"
}
```

#### POST /api/v1/rl/start
啟動 RL 訓練

**請求參數**:
```json
{
    "algorithm": "DQN|PPO|SAC (required)",
    "episodes": "number (optional, default: 10000)",
    "learning_rate": "number (optional, default: 0.001)",
    "batch_size": "number (optional, default: 64)",
    "config": {
        "exploration_rate": "number (optional)",
        "memory_size": "number (optional)",
        "target_update_frequency": "number (optional)"
    }
}
```

**響應示例**:
```json
{
    "status": "started",
    "training_id": "train_789012",
    "algorithm": "DQN",
    "configuration": {
        "episodes": 10000,
        "learning_rate": 0.001,
        "batch_size": 64
    },
    "estimated_completion": "2024-12-20T14:30:00Z"
}
```

#### POST /api/v1/rl/stop
停止 RL 訓練

**響應示例**:
```json
{
    "status": "stopped",
    "training_id": "train_789012",
    "episodes_completed": 2450,
    "final_reward": 125.7,
    "model_saved": true,
    "training_duration": "02:34:12"
}
```

### 5. 參數調優

#### PUT /api/v1/rl/parameters
更新 RL 訓練參數 (熱更新)

**請求參數**:
```json
{
    "learning_rate": "number (optional)",
    "batch_size": "number (optional)", 
    "exploration_rate": "number (optional)",
    "target_update_frequency": "number (optional)"
}
```

**響應示例**:
```json
{
    "status": "updated",
    "updated_parameters": {
        "learning_rate": 0.0005,
        "batch_size": 128
    },
    "restart_required": false,
    "applied_at": "2024-12-20T10:35:00Z"
}
```

---

## ⚠️ 緊急控制 API

### 6. 緊急模式

#### POST /api/v1/emergency/trigger
觸發緊急模式

**請求參數**:
```json
{
    "severity": "WARNING|CRITICAL (required)",
    "reason": "string (required)",
    "duration_minutes": "number (optional, default: 60)",
    "actions": {
        "stop_training": "boolean (optional, default: true)",
        "fallback_mode": "boolean (optional, default: true)",
        "alert_team": "boolean (optional, default: true)"
    }
}
```

**響應示例**:
```json
{
    "emergency_id": "emg_345678",
    "status": "activated",
    "severity": "CRITICAL",
    "activated_at": "2024-12-20T10:40:00Z",
    "expires_at": "2024-12-20T11:40:00Z",
    "actions_taken": [
        "RL training stopped",
        "Fallback decision mode activated",
        "Alert sent to on-call team"
    ]
}
```

#### DELETE /api/v1/emergency/clear
清除緊急模式

**響應示例**:
```json
{
    "status": "cleared",
    "emergency_id": "emg_345678",
    "cleared_at": "2024-12-20T10:50:00Z",
    "duration": "00:10:00",
    "auto_recovery": true
}
```

### 7. 手動決策覆蓋

#### POST /api/v1/override/decision
手動覆蓋 AI 決策

**請求參數**:
```json
{
    "user_id": "string (required)",
    "forced_satellite": "string (required)",
    "duration_minutes": "number (required)",
    "reason": "string (required)",
    "operator_id": "string (required)"
}
```

**響應示例**:
```json
{
    "override_id": "ovr_456789",
    "status": "active",
    "user_id": "user_001",
    "forced_satellite": "sat_005",
    "expires_at": "2024-12-20T11:40:00Z",
    "operator": "ops_admin_001",
    "created_at": "2024-12-20T10:40:00Z"
}
```

---

## 📊 監控和分析 API

### 8. 性能指標

#### GET /api/v1/metrics/performance
獲取詳細性能指標

**查詢參數**:
- `start_time`: 開始時間 ISO 8601
- `end_time`: 結束時間 ISO 8601 
- `granularity`: minute|hour|day (default: hour)

**響應示例**:
```json
{
    "time_range": {
        "start": "2024-12-20T09:00:00Z",
        "end": "2024-12-20T10:00:00Z",
        "granularity": "minute"
    },
    "metrics": {
        "decision_latency": {
            "avg_ms": 15.2,
            "p95_ms": 28.5,
            "p99_ms": 45.3,
            "max_ms": 67.1
        },
        "success_rates": {
            "overall": 0.987,
            "by_algorithm": {
                "DQN": 0.992,
                "PPO": 0.985,
                "SAC": 0.983
            }
        },
        "throughput": {
            "decisions_per_second": 145.3,
            "peak_rps": 200.7
        }
    }
}
```

### 9. 系統狀態

#### GET /api/v1/system/status
獲取詳細系統狀態

**響應示例**:
```json
{
    "system": {
        "cpu_usage_percent": 45.2,
        "memory_usage_percent": 67.8,
        "disk_usage_percent": 34.1,
        "network_io": {
            "bytes_sent": 1048576000,
            "bytes_received": 2097152000
        }
    },
    "services": {
        "ai_engine": {
            "status": "running",
            "uptime_seconds": 86400,
            "version": "v2.1.0",
            "health_score": 0.98
        },
        "rl_trainer": {
            "status": "training", 
            "current_episode": 2450,
            "progress_percent": 24.5
        },
        "database": {
            "redis": {
                "status": "connected",
                "memory_usage_mb": 256.7,
                "connections": 23
            }
        }
    }
}
```

---

## 🔗 WebSocket API

### 10. 即時監控

#### WebSocket /ws/monitoring
即時系統監控數據流

**連接參數**:
- `token`: 認證令牌 (optional)
- `subscribe`: 訂閱類型 system|training|decisions|all

**訊息格式**:
```json
{
    "type": "system_status|training_update|decision_made|alert",
    "timestamp": "2024-12-20T10:30:00Z",
    "data": {
        // 根據類型的具體數據
    }
}
```

**系統狀態訊息**:
```json
{
    "type": "system_status",
    "timestamp": "2024-12-20T10:30:00Z",
    "data": {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "active_connections": 156,
        "decisions_last_minute": 89
    }
}
```

**訓練更新訊息**:
```json
{
    "type": "training_update",
    "timestamp": "2024-12-20T10:30:00Z", 
    "data": {
        "algorithm": "DQN",
        "episode": 2451,
        "reward": 127.3,
        "epsilon": 0.149,
        "loss": 0.0045
    }
}
```

---

## 📝 API 使用範例

### Python 客戶端範例

```python
import requests
import json
from datetime import datetime

class NTNStackClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self):
        """檢查系統健康狀態"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def make_decision(self, user_id, current_satellite, candidates, context=None):
        """執行衛星決策"""
        payload = {
            "user_id": user_id,
            "current_satellite": current_satellite,
            "candidates": candidates
        }
        if context:
            payload["context"] = context
            
        response = self.session.post(
            f"{self.base_url}/api/v1/ai_decision_integration/decide",
            json=payload
        )
        return response.json()
    
    def start_training(self, algorithm="DQN", episodes=10000, **config):
        """啟動 RL 訓練"""
        payload = {
            "algorithm": algorithm,
            "episodes": episodes,
            "config": config
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/rl/start",
            json=payload
        )
        return response.json()
    
    def get_training_status(self):
        """獲取訓練狀態"""
        response = self.session.get(f"{self.base_url}/api/v1/rl/status")
        return response.json()
    
    def trigger_emergency(self, severity, reason, duration_minutes=60):
        """觸發緊急模式"""
        payload = {
            "severity": severity,
            "reason": reason,
            "duration_minutes": duration_minutes
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/emergency/trigger",
            json=payload
        )
        return response.json()

# 使用範例
client = NTNStackClient()

# 檢查系統健康
health = client.health_check()
print(f"系統狀態: {health['status']}")

# 執行決策
decision = client.make_decision(
    user_id="user_001",
    current_satellite="sat_001", 
    candidates=["sat_002", "sat_003", "sat_004"],
    context={"priority": "high"}
)
print(f"推薦衛星: {decision['decision']['recommended_satellite']}")

# 啟動訓練
training = client.start_training(
    algorithm="DQN",
    episodes=5000,
    learning_rate=0.001
)
print(f"訓練ID: {training['training_id']}")
```

### JavaScript 客戶端範例

```javascript
class NTNStackClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
    }
    
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        return await response.json();
    }
    
    async makeDecision(userId, currentSatellite, candidates, context = null) {
        const payload = {
            user_id: userId,
            current_satellite: currentSatellite,
            candidates: candidates
        };
        if (context) payload.context = context;
        
        const response = await fetch(`${this.baseUrl}/api/v1/ai_decision_integration/decide`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        return await response.json();
    }
    
    async connectWebSocket(subscribeType = 'all') {
        const ws = new WebSocket(`ws://localhost:8080/ws/monitoring?subscribe=${subscribeType}`);
        
        ws.onopen = () => {
            console.log('WebSocket 連接已建立');
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('收到更新:', data);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket 錯誤:', error);
        };
        
        return ws;
    }
}

// 使用範例
const client = new NTNStackClient();

// 檢查健康狀態
client.healthCheck().then(health => {
    console.log('系統狀態:', health.status);
});

// 建立 WebSocket 連接
const ws = client.connectWebSocket('system');
```

---

## ⚠️ 錯誤處理

### HTTP 狀態碼

| 狀態碼 | 說明 | 常見原因 |
|--------|------|----------|
| 200 | 成功 | 請求處理成功 |
| 400 | 請求錯誤 | 參數格式錯誤或缺少必要參數 |
| 401 | 未授權 | API Key 無效或過期 |
| 403 | 權限不足 | 無權限訪問該資源 |
| 404 | 資源不存在 | 請求的端點或資源不存在 |
| 429 | 請求過於頻繁 | 超過速率限制 |
| 500 | 伺服器錯誤 | 內部系統錯誤 |
| 503 | 服務不可用 | 系統維護或過載 |

### 錯誤響應格式

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "錯誤描述",
        "details": "詳細錯誤信息",
        "timestamp": "2024-12-20T10:30:00Z",
        "request_id": "req_123456789"
    }
}
```

---

## 🔒 安全性

### API Key 認證
```bash
# 請求頭中包含 API Key
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8080/api/v1/rl/status
```

### 速率限制
- **預設限制**: 每分鐘 1000 請求
- **決策 API**: 每秒 100 請求
- **訓練控制**: 每分鐘 10 請求

### 安全標頭
所有響應都包含安全標頭：
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000
```

---

## 📞 支援資訊

- **技術文檔**: https://docs.ntn-stack.com
- **API 測試工具**: https://api.ntn-stack.com/playground
- **問題回報**: https://github.com/ntn-stack/issues
- **開發者社群**: https://discord.gg/ntn-stack

**文檔版本**: v1.0.0  
**最後更新**: 2024年12月  
**維護團隊**: NTN Stack API 開發團隊