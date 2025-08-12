# Phase 1 API 規範文檔

**版本**: v1.0.0  
**建立日期**: 2025-08-12  
**接口標準**: Phase 1 → Phase 2 標準化接口  

## 🎯 API 概述

Phase 1 API 提供全量衛星軌道數據的標準化查詢接口，支援：
- **8,715 顆真實衛星軌道數據**
- **完整 SGP4 算法計算結果**
- **標準化 Phase 1 → Phase 2 數據接口**
- **向下兼容原有 API 格式**

## 📊 核心數據格式

### OrbitData 標準格式

```json
{
  "satellite_id": "string",
  "constellation": "string", 
  "timestamp": "ISO 8601 格式",
  "position_eci": [x, y, z],        // km
  "velocity_eci": [vx, vy, vz],     // km/s
  "position_teme": [x, y, z],       // km
  "velocity_teme": [vx, vy, vz],    // km/s
  "calculation_quality": 0.0-1.0,
  "error_code": 0,
  "metadata": {
    "satellite_name": "string",
    "tle_epoch": "ISO 8601 格式",
    "coordinate_system_requested": "eci|teme"
  }
}
```

### QueryRequest 標準格式

```json
{
  "request_id": "UUID",
  "timestamp": "ISO 8601 格式",
  "satellite_ids": ["sat1", "sat2", ...],     // 可選
  "constellations": ["starlink", "oneweb"],   // 可選
  "time_range_start": "ISO 8601 格式",        // 可選
  "time_range_end": "ISO 8601 格式",          // 可選
  "coordinate_system": "eci|teme",
  "data_format": "json|binary|compressed",
  "max_records": 1000,
  "include_metadata": true
}
```

### QueryResponse 標準格式

```json
{
  "request_id": "UUID",
  "success": true,
  "total_matches": 8715,
  "returned_records": 1000,
  "has_more_data": true,
  "response_time": "ISO 8601 格式",
  "performance_metrics": {
    "query_time_seconds": 0.15,
    "records_per_second": 6666.67,
    "data_completeness": 1.0
  },
  "data_batch": {
    "batch_id": "UUID",
    "generation_time": "ISO 8601 格式",
    "time_range": {
      "start": "ISO 8601 格式",
      "end": "ISO 8601 格式"
    },
    "satellite_count": 100,
    "total_records": 1000,
    "quality_metrics": {
      "average_quality": 0.99,
      "min_quality": 0.95,
      "successful_calculations": 995,
      "failed_calculations": 5
    },
    "orbit_data": [/* OrbitData 數組 */]
  },
  "error_message": null
}
```

## 🔗 API 端點規範

### 基本服務端點

#### GET `/`
**功能**: API 服務信息  
**響應**: 
```json
{
  "service": "Phase 1 增強軌道計算 API",
  "version": "1.0.0",
  "interface_version": "1.0",
  "status": "running",
  "endpoints": {/* 端點列表 */}
}
```

#### GET `/health`
**功能**: 服務健康檢查  
**響應**:
```json
{
  "service": "healthy|degraded|error",
  "timestamp": "ISO 8601 格式",
  "interface_version": "1.0",
  "data_integrity": true,
  "components": {
    "standard_interface": "healthy",
    "data_provider": "healthy",
    "available_satellites": 8715
  }
}
```

#### GET `/capabilities`
**功能**: 接口能力查詢  
**響應**:
```json
{
  "interface_capabilities": {
    "interface_version": "1.0",
    "supported_data_formats": ["json", "binary", "compressed"],
    "supported_coordinate_systems": ["eci", "teme"],
    "data_coverage": {/* 數據覆蓋信息 */},
    "available_satellites": {
      "total_count": 8715,
      "satellites": [/* 衛星列表 */]
    },
    "max_records_per_query": 100000,
    "data_integrity_validated": true
  }
}
```

### 衛星數據查詢端點

#### GET `/satellites`
**功能**: 獲取可用衛星列表  
**參數**:
- `constellation` (可選): 星座名稱篩選
- `limit` (可選): 返回數量限制 (1-10000, 默認 100)
- `include_details` (可選): 包含詳細信息 (默認 false)

**響應**:
```json
{
  "total_satellites": 8715,
  "filtered_satellites": 8064,
  "returned_satellites": 100,
  "constellation_filter": "starlink",
  "satellites": ["SAT_001", "SAT_002", ...],
  "satellite_details": [/* 詳細信息數組 (如果 include_details=true) */],
  "timestamp": "ISO 8601 格式"
}
```

#### POST `/orbit/query`
**功能**: 標準軌道數據查詢  
**請求體**: `OrbitQueryModel`
```json
{
  "satellite_ids": ["SAT_001", "SAT_002"],
  "constellations": ["starlink"],
  "time_range_start": "2025-08-12T00:00:00Z",
  "time_range_end": "2025-08-12T01:00:00Z",
  "coordinate_system": "eci",
  "data_format": "json",
  "max_records": 1000,
  "include_metadata": true
}
```

**響應**: `QueryResponse` 標準格式

#### GET `/orbit/simple`
**功能**: 簡化軌道數據查詢 (GET 方法)  
**參數**:
- `satellite_ids` (可選): 衛星 ID，多個用逗號分隔
- `constellation` (可選): 星座名稱
- `timestamp` (可選): 查詢時間 (ISO 格式)
- `coordinate_system` (可選): 坐標系統 (eci|teme, 默認 eci)
- `limit` (可選): 最大返回記錄數 (1-1000, 默認 100)

**響應**: 與 `/orbit/query` 相同格式

#### POST `/orbit/batch`
**功能**: 批量軌道數據查詢  
**請求體**: `BatchQueryModel`
```json
{
  "queries": [/* OrbitQueryModel 數組 */],
  "batch_id": "BATCH_001",
  "priority": "normal|high|low"
}
```

**響應**:
```json
{
  "batch_id": "BATCH_001",
  "total_queries": 5,
  "successful_queries": 4,
  "failed_queries": 1,
  "batch_responses": [/* 每個查詢的響應結果 */],
  "processing_time": "ISO 8601 格式"
}
```

### 統計與監控端點

#### GET `/statistics`
**功能**: 服務統計信息  
**響應**:
```json
{
  "service_info": {
    "name": "Phase 1 增強軌道計算 API",
    "version": "1.0.0",
    "interface_version": "1.0",
    "uptime": "運行中"
  },
  "data_statistics": {/* 數據統計 */},
  "satellite_statistics": {/* 衛星統計 */},
  "interface_capabilities": {/* 接口能力 */},
  "timestamp": "ISO 8601 格式"
}
```

#### GET `/data/coverage`
**功能**: 數據覆蓋範圍  
**響應**:
```json
{
  "data_coverage": {
    "total_satellites": 8715,
    "constellation_distribution": {
      "starlink": 8064,
      "oneweb": 651
    },
    "data_load_time": "ISO 8601 格式",
    "data_source_path": "/netstack/tle_data"
  }
}
```

#### GET `/data/integrity`
**功能**: 數據完整性檢查  
**響應**:
```json
{
  "data_integrity": "valid|invalid",
  "integrity_score": 1.0,
  "check_timestamp": "ISO 8601 格式",
  "details": "數據完整性驗證通過"
}
```

## 🔄 向下兼容 API (原有格式)

### 兼容端點映射

| 原有端點 | 新標準端點 | 功能描述 |
|---------|-----------|---------|
| `/api/v1/phase1/satellite_orbits` | `/orbit/simple` | 衛星軌道數據 |
| `/api/v1/phase1/constellations/info` | `/satellites?include_details=true` | 星座信息 |
| `/api/v1/phase1/satellite/{id}/trajectory` | `/orbit/query` (時間範圍) | 衛星軌跡 |
| `/api/v1/phase1/health` | `/health` | 健康檢查 |
| `/api/v1/phase1/execution/summary` | `/statistics` | 執行摘要 |

### 兼容格式示例

#### GET `/api/v1/phase1/satellite_orbits?constellation=starlink&count=10`

**響應** (兼容格式):
```json
[
  {
    "satellite_id": "SAT_001",
    "satellite_name": "STARLINK-1001",
    "constellation": "starlink",
    "timestamp": "2025-08-12T12:00:00Z",
    "position": {"x": 7000.0, "y": 0.0, "z": 0.0},
    "velocity": {"vx": 0.0, "vy": 7.5, "vz": 0.0},
    "data_source": "phase1_sgp4_full_calculation",
    "algorithm": "complete_sgp4_algorithm"
  }
]
```

## ⚡ 性能規範

### 響應時間要求

| 端點類型 | 響應時間目標 | 最大記錄數 |
|---------|------------|-----------|
| 健康檢查 | < 10ms | N/A |
| 簡單查詢 | < 100ms | 1,000 |
| 標準查詢 | < 500ms | 10,000 |
| 批量查詢 | < 2000ms | 100,000 |
| 統計信息 | < 200ms | N/A |

### 併發處理

- **最大併發請求**: 50 個
- **請求排隊**: 支援 100 個待處理請求
- **超時設置**: 30 秒

### 數據傳輸

- **支援格式**: JSON、Binary、Compressed
- **最大響應大小**: 50MB
- **壓縮支援**: gzip、deflate

## 🔒 錯誤處理

### HTTP 狀態碼

- `200 OK`: 請求成功
- `400 Bad Request`: 請求參數錯誤
- `404 Not Found`: 資源不存在
- `500 Internal Server Error`: 服務器內部錯誤
- `503 Service Unavailable`: 服務不可用

### 錯誤響應格式

```json
{
  "error": {
    "code": "INVALID_CONSTELLATION",
    "message": "星座 'invalid' 不存在。可用星座: ['starlink', 'oneweb']",
    "timestamp": "2025-08-12T12:00:00Z",
    "request_id": "req_12345"
  }
}
```

### 常見錯誤碼

- `INVALID_SATELLITE_ID`: 無效的衛星 ID
- `INVALID_CONSTELLATION`: 無效的星座名稱
- `INVALID_TIME_FORMAT`: 時間格式錯誤
- `INVALID_TIME_RANGE`: 時間範圍錯誤
- `MAX_RECORDS_EXCEEDED`: 超過最大記錄數限制
- `DATA_NOT_AVAILABLE`: 數據不可用
- `CALCULATION_FAILED`: 軌道計算失敗

## 📝 使用範例

### Python 客戶端範例

```python
import requests
import json

# API 基礎 URL
BASE_URL = "http://localhost:8001"

# 查詢 Starlink 衛星軌道數據
def query_starlink_orbits():
    query_data = {
        "constellations": ["starlink"],
        "coordinate_system": "eci",
        "max_records": 100,
        "include_metadata": True
    }
    
    response = requests.post(f"{BASE_URL}/orbit/query", json=query_data)
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"查詢成功: {data['returned_records']} 條記錄")
            return data["data_batch"]["orbit_data"]
        else:
            print(f"查詢失敗: {data['error_message']}")
    else:
        print(f"HTTP 錯誤: {response.status_code}")

# 檢查服務健康狀態
def check_health():
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"服務狀態: {health['service']}")
        print(f"可用衛星: {health['components']['available_satellites']}")
    else:
        print("健康檢查失敗")

# 獲取衛星列表
def get_satellites(constellation=None, limit=10):
    params = {"limit": limit}
    if constellation:
        params["constellation"] = constellation
    
    response = requests.get(f"{BASE_URL}/satellites", params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data["satellites"]
    else:
        print(f"獲取衛星列表失敗: {response.status_code}")

# 使用示例
if __name__ == "__main__":
    # 檢查服務健康
    check_health()
    
    # 獲取前10顆 Starlink 衛星
    satellites = get_satellites("starlink", 10)
    print(f"前10顆 Starlink 衛星: {satellites}")
    
    # 查詢軌道數據
    orbits = query_starlink_orbits()
    if orbits:
        print(f"第一顆衛星軌道數據: {orbits[0]}")
```

### JavaScript 客戶端範例

```javascript
const BASE_URL = "http://localhost:8001";

// 查詢軌道數據
async function queryOrbitData(constellations, maxRecords = 100) {
    const queryData = {
        constellations: constellations,
        coordinate_system: "eci",
        max_records: maxRecords,
        include_metadata: true
    };
    
    try {
        const response = await fetch(`${BASE_URL}/orbit/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(queryData)
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                console.log(`查詢成功: ${data.returned_records} 條記錄`);
                return data.data_batch.orbit_data;
            } else {
                console.error(`查詢失敗: ${data.error_message}`);
            }
        } else {
            console.error(`HTTP 錯誤: ${response.status}`);
        }
    } catch (error) {
        console.error('請求失敗:', error);
    }
}

// 檢查服務健康
async function checkHealth() {
    try {
        const response = await fetch(`${BASE_URL}/health`);
        if (response.ok) {
            const health = await response.json();
            console.log(`服務狀態: ${health.service}`);
            console.log(`可用衛星: ${health.components.available_satellites}`);
        }
    } catch (error) {
        console.error('健康檢查失敗:', error);
    }
}

// 使用示例
(async () => {
    // 檢查服務健康
    await checkHealth();
    
    // 查詢 Starlink 軌道數據
    const orbits = await queryOrbitData(["starlink"], 10);
    if (orbits && orbits.length > 0) {
        console.log('第一顆衛星軌道數據:', orbits[0]);
    }
})();
```

## 📋 版本管理

### API 版本策略

- **主版本**: 重大架構變更
- **次版本**: 新增功能，保持向下兼容
- **修補版本**: Bug 修復

### 版本標識

- **接口版本**: HTTP Header `API-Version: 1.0`
- **響應版本**: 響應體中 `interface_version` 字段
- **兼容支援**: 保持至少兩個主版本的向下兼容

## 🔮 未來擴展

### 規劃的功能

1. **實時數據更新**: WebSocket 支援
2. **高級過濾**: 軌道參數、可見性篩選
3. **數據分析**: 軌道統計、趨勢分析
4. **緩存優化**: Redis 緩存支援
5. **API 密鑰認證**: 安全訪問控制

### 性能優化方向

1. **並行計算**: 多線程 SGP4 計算
2. **數據壓縮**: 更高效的數據傳輸
3. **智能緩存**: 預測性數據預載
4. **負載均衡**: 多實例部署支援

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-08-12  
**維護團隊**: Phase 1 重構專案團隊