# NTN-Stack API 文檔

## 概述

NTN-Stack 提供了一套完整的 RESTful API，用於管理和監控非地面網路 (NTN) 的測量事件系統。本文檔詳細描述了所有可用的 API 端點、請求格式和響應結構。

## 基礎資訊

- **基礎 URL**: `http://localhost:8000`
- **API 版本**: v1.0
- **內容類型**: `application/json`
- **字符編碼**: UTF-8

## 認證

目前 API 不需要認證，但建議在生產環境中實施適當的認證機制。

## 錯誤處理

所有 API 錯誤都會返回標準的 HTTP 狀態碼和 JSON 格式的錯誤資訊：

```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "參數驗證失敗",
    "details": "event_type 必須是 A4, D1, D2, T1 之一"
  }
}
```

## API 端點

### 1. 系統健康檢查

#### GET /health

檢查系統健康狀態。

**響應**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-20T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "orbit_engine": "running",
    "measurement_service": "active"
  }
}
```

### 2. SIB19 系統資訊廣播

#### GET /api/sib19/current

獲取當前的 SIB19 系統資訊。

**響應**:
```json
{
  "broadcast_time": "2025-07-20T10:30:00Z",
  "reference_location": {
    "latitude": 25.0,
    "longitude": 121.0,
    "altitude": 0.1
  },
  "time_correction": {
    "epoch_time": 1721469000,
    "gnss_time_offset": 18.0,
    "current_accuracy_ms": 5.2,
    "sync_accuracy_ms": 10.0
  },
  "satellite_list": [
    {
      "satellite_id": "SAT_001",
      "tle_line1": "1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990",
      "tle_line2": "2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456",
      "validity_time": 7200
    }
  ],
  "ephemeris_data": {
    "update_interval": 3600,
    "next_update": "2025-07-20T11:30:00Z",
    "validity_period": 7200
  }
}
```

#### GET /api/sib19/history

獲取 SIB19 歷史資料。

**查詢參數**:
- `start_time`: 開始時間 (ISO 8601 格式)
- `end_time`: 結束時間 (ISO 8601 格式)
- `limit`: 返回記錄數量限制 (預設: 100)

#### POST /api/sib19/validate

驗證 SIB19 數據的完整性和有效性。

**請求體**:
```json
{
  "sib19_data": {
    "broadcast_time": "2025-07-20T10:30:00Z",
    "reference_location": {...},
    "time_correction": {...}
  }
}
```

### 3. 測量事件管理

#### POST /api/measurement-events/start

啟動測量事件。

**請求體**:
```json
{
  "event_type": "A4",
  "config": {
    "measurement_interval": 1000,
    "reporting_interval": 5000,
    "threshold_1": 50.0,
    "threshold_2": 100.0,
    "hysteresis": 0.5
  }
}
```

**響應**:
```json
{
  "status": "started",
  "event_id": "evt_123456",
  "event_type": "A4",
  "start_time": "2025-07-20T10:30:00Z"
}
```

#### POST /api/measurement-events/stop

停止測量事件。

**請求體**:
```json
{
  "event_type": "A4"
}
```

#### GET /api/measurement-events/{event_type}/data

獲取指定事件類型的測量數據。

**路徑參數**:
- `event_type`: 事件類型 (A4, D1, D2, T1)

**查詢參數**:
- `start_time`: 開始時間
- `end_time`: 結束時間
- `limit`: 數據點數量限制

**響應**:
```json
{
  "event_type": "A4",
  "data_points": [
    {
      "timestamp": "2025-07-20T10:30:00Z",
      "measurement_value": 45.2,
      "threshold_status": "below",
      "triggered": false,
      "metadata": {
        "satellite_id": "SAT_001",
        "signal_strength": -95.5
      }
    }
  ],
  "total_count": 150,
  "has_more": true
}
```

#### POST /api/measurement-events/configure

配置測量事件參數。

**請求體**:
```json
{
  "event_type": "A4",
  "config": {
    "measurement_interval": 2000,
    "reporting_interval": 10000,
    "threshold_1": 60.0,
    "threshold_2": 120.0
  }
}
```

### 4. 軌道計算

#### POST /api/orbit/calculate-position

計算衛星在指定時間的位置。

**請求體**:
```json
{
  "tle_line1": "1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990",
  "tle_line2": "2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456",
  "prediction_time": "2025-07-20T10:30:00Z"
}
```

**響應**:
```json
{
  "latitude": 25.123,
  "longitude": 121.456,
  "altitude": 408.2,
  "velocity": {
    "x": 7.5,
    "y": 0.0,
    "z": 0.0
  },
  "calculation_time": "2025-07-20T10:30:00Z",
  "accuracy_estimate": "< 1 km"
}
```

#### POST /api/orbit/calculate-batch

批量計算多顆衛星的位置。

**請求體**:
```json
{
  "satellites": [
    {
      "satellite_id": "SAT_001",
      "tle_line1": "...",
      "tle_line2": "..."
    },
    {
      "satellite_id": "SAT_002",
      "tle_line1": "...",
      "tle_line2": "..."
    }
  ],
  "prediction_time": "2025-07-20T10:30:00Z"
}
```

#### GET /api/orbit/trajectory

獲取衛星軌跡預測。

**查詢參數**:
- `satellite_id`: 衛星 ID
- `start_time`: 開始時間
- `duration`: 預測持續時間 (秒)
- `step`: 時間步長 (秒)

### 5. 數據分析

#### GET /api/analysis/statistics

獲取測量事件統計資訊。

**查詢參數**:
- `event_type`: 事件類型
- `time_range`: 時間範圍 (1h, 24h, 7d, 30d)

**響應**:
```json
{
  "event_type": "A4",
  "time_range": "24h",
  "statistics": {
    "total_measurements": 8640,
    "triggered_events": 23,
    "trigger_rate": 0.27,
    "avg_measurement_value": 45.8,
    "min_value": 12.3,
    "max_value": 156.7
  }
}
```

#### GET /api/analysis/performance

獲取系統性能指標。

**響應**:
```json
{
  "api_performance": {
    "avg_response_time_ms": 125,
    "requests_per_second": 45.2,
    "error_rate": 0.01
  },
  "cache_performance": {
    "hit_rate": 0.85,
    "memory_usage_mb": 256.7,
    "efficiency": 0.92
  },
  "system_resources": {
    "cpu_usage_percent": 35.2,
    "memory_usage_percent": 68.4,
    "disk_usage_percent": 42.1
  }
}
```

## 狀態碼

- `200 OK`: 請求成功
- `201 Created`: 資源創建成功
- `400 Bad Request`: 請求參數錯誤
- `404 Not Found`: 資源不存在
- `500 Internal Server Error`: 服務器內部錯誤
- `503 Service Unavailable`: 服務暫時不可用

## 速率限制

- 每個 IP 每分鐘最多 1000 次請求
- 批量操作每分鐘最多 100 次請求
- 超出限制將返回 `429 Too Many Requests`

## 版本控制

API 使用 URL 路徑版本控制：
- 當前版本: `/api/v1/`
- 未來版本: `/api/v2/`

## 示例代碼

### Python 示例

```python
import requests
import json

# 獲取 SIB19 數據
response = requests.get('http://localhost:8000/api/sib19/current')
sib19_data = response.json()

# 啟動 A4 測量事件
config = {
    "event_type": "A4",
    "config": {
        "measurement_interval": 1000,
        "reporting_interval": 5000
    }
}
response = requests.post('http://localhost:8000/api/measurement-events/start', 
                        json=config)
```

### JavaScript 示例

```javascript
// 獲取測量數據
fetch('/api/measurement-events/A4/data')
  .then(response => response.json())
  .then(data => {
    console.log('測量數據:', data);
  });

// 計算軌道位置
const orbitRequest = {
  tle_line1: "1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990",
  tle_line2: "2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456",
  prediction_time: new Date().toISOString()
};

fetch('/api/orbit/calculate-position', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(orbitRequest)
})
.then(response => response.json())
.then(position => {
  console.log('衛星位置:', position);
});
```

## 支援

如有問題或建議，請聯繫：
- 技術支援: support@ntn-stack.com
- 文檔問題: docs@ntn-stack.com
- GitHub Issues: https://github.com/ntn-stack/issues
