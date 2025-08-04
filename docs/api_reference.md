# 🌐 API 接口使用指南

**版本**: 1.0.0  
**建立日期**: 2025-08-04  
**適用於**: LEO 衛星切換研究系統  

## 📋 概述

本文檔提供當前系統所有可用 API 端點的使用指南，包括請求格式、響應格式和使用範例。

## 🚀 快速開始

### 基礎 URL
- **NetStack API**: `http://localhost:8080`
- **SimWorld API**: `http://localhost:8888`

### 認證方式
當前系統為研究環境，無需認證。生產環境可能需要 API Key 或 Token。

### 響應格式
所有 API 響應均為 JSON 格式，包含統一的狀態結構：
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "timestamp": "2025-08-04T12:00:00Z"
}
```

## 🛰️ 衛星數據 API (SimWorld)

### 統一時間序列 API
**基礎路徑**: `/api/v1/satellites/unified/`

#### 獲取時間序列數據
```http
GET /api/v1/satellites/unified/timeseries
```

**參數**:
- `constellation` (string): 星座名稱 (`starlink`, `oneweb`)
- `duration_minutes` (int, 可選): 時間範圍，預設 120
- `interval_seconds` (int, 可選): 採樣間隔，預設 10

**範例請求**:
```bash
curl "http://localhost:8888/api/v1/satellites/unified/timeseries?constellation=starlink&duration_minutes=60"
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "metadata": {
      "constellation": "starlink",
      "satellites_count": 40,
      "time_points": 360,
      "duration_minutes": 60
    },
    "satellites": [
      {
        "satellite_id": "STARLINK-1007",
        "timeseries": [
          {
            "timestamp": "2025-08-04T12:00:00Z",
            "elevation_deg": 45.7,
            "azimuth_deg": 152.3,
            "range_km": 589.2,
            "is_visible": true
          }
        ]
      }
    ]
  }
}
```

#### 服務狀態檢查
```http
GET /api/v1/satellites/unified/status
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "service_status": "healthy",
    "data_freshness": "2025-08-04T10:30:00Z",
    "available_constellations": ["starlink", "oneweb"],
    "preprocess_status": "completed"
  }
}
```

### 衛星位置查詢 API  
**基礎路徑**: `/api/v1/satellites/`

#### 即時衛星位置
```http
GET /api/v1/satellites/positions
```

**參數**:
- `timestamp` (string): ISO 8601 時間戳
- `constellation` (string): 星座名稱
- `min_elevation` (float, 可選): 最小仰角，預設 5.0

**範例請求**:
```bash
curl "http://localhost:8888/api/v1/satellites/positions?timestamp=2025-08-04T12:00:00Z&constellation=starlink&min_elevation=10"
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "satellite_id": "STARLINK-1234",
        "elevation_deg": 67.2,
        "azimuth_deg": 185.4,
        "range_km": 542.8,
        "is_visible": true,
        "signal_strength_dbm": -82.5
      }
    ],
    "total_count": 8,
    "query_time_ms": 45
  }
}
```

## 🎯 切換決策 API (NetStack)

### 切換決策引擎
**基礎路徑**: `/api/v1/handover_decision/`

#### 評估切換候選
```http
POST /api/v1/handover_decision/evaluate_candidates
```

**請求格式**:
```json
{
  "ue_context": {
    "ue_id": "UE_12345",
    "current_satellite": "STARLINK-1234",
    "location": {"lat": 24.9441, "lon": 121.3714}
  },
  "candidates": [
    {
      "satellite_id": "STARLINK-5678",
      "signal_strength_dbm": -85.2,
      "elevation_deg": 45.7,
      "load_factor": 0.6
    }
  ]
}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "recommended_satellite": "STARLINK-5678",
    "decision_score": 87.3,
    "decision_factors": {
      "signal_strength": 0.89,
      "elevation_angle": 0.76,
      "load_balancing": 0.92
    },
    "execution_time_ms": 25.6
  }
}
```

#### 切換歷史查詢
```http
GET /api/v1/handover_decision/history/{ue_id}
```

**參數**:
- `limit` (int, 可選): 返回記錄數量，預設 50
- `start_time` (string, 可選): 開始時間
- `end_time` (string, 可選): 結束時間

**範例響應**:
```json
{
  "success": true,
  "data": {
    "handover_history": [
      {
        "timestamp": "2025-08-04T12:00:00Z",
        "source_satellite": "STARLINK-1234",
        "target_satellite": "STARLINK-5678",
        "decision_score": 87.3,
        "success": true,
        "latency_ms": 28.4
      }
    ],
    "total_handovers": 15,
    "success_rate": 0.93
  }
}
```

## 🧠 ML 預測 API (NetStack)

### ML 驅動預測
**基礎路徑**: `/api/v1/ml_prediction/`

#### 切換預測
```http
POST /api/v1/ml_prediction/predict_handover
```

**請求格式**:
```json
{
  "ue_context": {
    "ue_id": "UE_12345",
    "trajectory": [
      {"timestamp": "2025-08-04T12:00:00Z", "lat": 24.9441, "lon": 121.3714}
    ]
  },
  "prediction_horizon_minutes": 10,
  "model_type": "lstm"
}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "predicted_handovers": [
      {
        "predicted_time": "2025-08-04T12:05:30Z",
        "source_satellite": "STARLINK-1234",
        "target_satellite": "STARLINK-5678",
        "confidence": 0.94
      }
    ],
    "model_accuracy": 0.91,
    "prediction_time_ms": 52.3
  }
}
```

#### 模型性能監控
```http
GET /api/v1/ml_prediction/model_performance
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "models": {
      "lstm_predictor": {
        "accuracy": 0.94,
        "precision": 0.92,
        "recall": 0.89,
        "f1_score": 0.91,
        "last_trained": "2025-08-04T10:00:00Z"
      },
      "transformer_predictor": {
        "accuracy": 0.96,
        "precision": 0.94,
        "recall": 0.93,
        "f1_score": 0.94,
        "last_trained": "2025-08-04T09:30:00Z"
      }
    }
  }
}
```

## ⏰ 時間同步 API (NetStack)

### 時間同步服務
**基礎路徑**: `/api/v1/time_sync/`

#### 同步狀態查詢
```http
GET /api/v1/time_sync/status
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "sync_status": "synchronized",
    "time_accuracy_us": 0.85,
    "frequency_stability_ppb": 0.05,
    "reference_sources": [
      {"source": "gps", "status": "active", "accuracy_us": 0.1},
      {"source": "ntp", "status": "backup", "accuracy_us": 2.5}
    ],
    "last_calibration": "2025-08-04T11:45:00Z"
  }
}
```

#### 都卜勒頻率補償
```http
GET /api/v1/time_sync/doppler_compensation/{satellite_id}
```

**參數**:
- `ue_location` (string): UE 位置 "lat,lon"
- `timestamp` (string, 可選): 計算時間點

**範例請求**:
```bash
curl "http://localhost:8080/api/v1/time_sync/doppler_compensation/STARLINK-1234?ue_location=24.9441,121.3714"
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "satellite_id": "STARLINK-1234",
    "doppler_shift_hz": -1250.3,
    "frequency_correction": 1250.3,
    "relative_velocity_ms": -7234.5,
    "calculation_accuracy": "high"
  }
}
```

## 🔄 狀態同步 API (NetStack)

### 分散式狀態管理
**基礎路徑**: `/api/v1/state_sync/`

#### 創建狀態
```http
POST /api/v1/state_sync/create_state
```

**請求格式**:
```json
{
  "state_id": "ue_context_12345",
  "state_type": "user_context", 
  "data": {
    "ue_id": "UE_12345",
    "current_satellite": "STARLINK-1234",
    "session_info": {...}
  },
  "consistency_level": "eventual"
}
```

#### 狀態查詢
```http
GET /api/v1/state_sync/get_state/{state_id}
```

**範例響應**:
```json
{
  "success": true,
  "data": {
    "state_id": "ue_context_12345",
    "data": {...},
    "version": 3,
    "last_updated": "2025-08-04T12:00:00Z",
    "consistency_level": "eventual",
    "sync_nodes": ["node1", "node2", "node3"]
  }
}
```

## 📊 性能監控 API (NetStack)

### 算法性能監控
**基礎路徑**: `/api/v1/performance/`

#### 性能指標查詢
```http
GET /api/v1/performance/algorithm_metrics
```

**參數**:
- `algorithm` (string, 可選): 算法名稱
- `start_time` (string, 可選): 開始時間  
- `end_time` (string, 可選): 結束時間

**範例響應**:
```json
{
  "success": true,
  "data": {
    "handover_latency": {
      "average_ms": 25.6,
      "p95_ms": 45.2,
      "p99_ms": 67.8,
      "sample_count": 1500
    },
    "prediction_accuracy": {
      "lstm_model": 0.94,
      "transformer_model": 0.96,
      "baseline_model": 0.87
    },
    "system_resources": {
      "cpu_usage_percent": 15.2,
      "memory_usage_mb": 245.7,
      "disk_io_mbps": 12.3
    }
  }
}
```

#### 匯出研究數據
```http
POST /api/v1/performance/export_research_data
```

**請求格式**:
```json
{
  "experiment_name": "handover_algorithm_comparison",
  "start_time": "2025-08-04T10:00:00Z",
  "end_time": "2025-08-04T14:00:00Z",
  "metrics": ["handover_latency", "success_rate", "prediction_accuracy"],
  "format": "csv"
}
```

## 🏥 系統健康檢查

### 整體系統狀態
```http
GET /health
```

**NetStack 健康檢查**:
```bash
curl http://localhost:8080/health
```

**SimWorld 健康檢查**:
```bash
curl http://localhost:8888/api/v1/satellites/unified/health
```

**標準健康響應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-04T12:00:00Z",
  "services": {
    "database": "healthy",
    "cache": "healthy", 
    "algorithms": "healthy",
    "data_processing": "healthy"
  },
  "metrics": {
    "uptime_seconds": 86400,
    "response_time_ms": 12.5,
    "active_connections": 8
  }
}
```

## 🚨 錯誤處理

### 標準錯誤響應
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETERS",
    "message": "星座名稱無效",
    "details": {
      "parameter": "constellation",
      "provided_value": "invalid_constellation",
      "valid_values": ["starlink", "oneweb"]
    }
  },
  "timestamp": "2025-08-04T12:00:00Z"
}
```

### 常見錯誤碼
| 錯誤碼 | HTTP 狀態 | 說明 |
|--------|-----------|------|
| `INVALID_PARAMETERS` | 400 | 請求參數無效 |
| `NOT_FOUND` | 404 | 資源不存在 |
| `SERVICE_UNAVAILABLE` | 503 | 服務暫時不可用 |
| `CALCULATION_ERROR` | 500 | 算法計算錯誤 |
| `DATA_NOT_READY` | 425 | 數據尚未準備完成 |

## 🔧 使用最佳實踐

### 1. 批次查詢優化
```python
# 推薦：批次查詢多個時間點
timestamps = ["2025-08-04T12:00:00Z", "2025-08-04T12:05:00Z", "2025-08-04T12:10:00Z"]
response = requests.post(
    "http://localhost:8888/api/v1/satellites/batch_positions",
    json={"timestamps": timestamps, "constellation": "starlink"}
)
```

### 2. 異步處理  
```python
import asyncio
import aiohttp

async def get_satellite_data(session, timestamp):
    url = f"http://localhost:8888/api/v1/satellites/positions?timestamp={timestamp}"
    async with session.get(url) as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [get_satellite_data(session, ts) for ts in timestamps]
        results = await asyncio.gather(*tasks)
```

### 3. 錯誤重試機制
```python
import time
import requests

def api_call_with_retry(url, max_retries=3, delay=1.0):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(delay * (2 ** attempt))  # 指數退避
```

### 4. 性能監控整合
```python
# 在實驗代碼中加入性能監控
start_time = time.time()
response = requests.get("http://localhost:8080/api/v1/handover_decision/evaluate_candidates")
execution_time = time.time() - start_time

# 記錄到性能監控系統
monitor.record_api_call("handover_decision", execution_time, response.status_code == 200)
```

## 📚 SDK 和工具

### Python SDK (推薦)
```python
# 安裝 (將來可能提供)
# pip install ntn-stack-sdk

from ntn_stack import NetStackClient, SimWorldClient

# 初始化客戶端
netstack = NetStackClient("http://localhost:8080")
simworld = SimWorldClient("http://localhost:8888")

# 使用高層 API
satellites = simworld.get_visible_satellites("starlink", min_elevation=10)
decision = netstack.evaluate_handover(ue_context, candidates)
```

### 命令列工具
```bash
# 安裝 CLI 工具 (將來可能提供)
# pip install ntn-stack-cli

# 快速查詢
ntn-cli satellites list --constellation starlink
ntn-cli handover evaluate --ue-id UE_12345 --candidates STARLINK-1234,STARLINK-5678
ntn-cli performance report --algorithm handover_decision
```

---

**本文檔涵蓋了系統所有主要 API 端點的使用方法，為研究實驗和系統整合提供完整的介面參考。**