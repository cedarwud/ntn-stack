# 🏗️ 數據流架構

**文檔編號**: 04  
**主題**: 基於現有系統的衛星數據流設計

## 1. 現有系統架構分析

### 1.1 當前數據流
```
[TLE Data] → [NetStack API] → [SimWorld API] → [Frontend]
     ↓             ↓                ↓              ↓
  CelesTrak    SGP4 計算      統一接口      DataSyncContext
```

### 1.2 現有組件能力
| 組件 | 位置 | 功能 | 狀態 |
|-----|------|------|------|
| **TLE 下載** | `/scripts/` | Cron 驅動自動更新 | ✅ 完成 |
| **SGP4 計算** | `netstack/satellite-ops` | 軌道計算 API | ✅ 完成 |
| **數據統一** | `simworld/api` | 整合 NetStack 數據 | ✅ 完成 |
| **前端同步** | `DataSyncContext` | 統一狀態管理 | ✅ 完成 |
| **衛星篩選** | - | 智能選擇子集 | ❌ 待實現 |
| **事件觸發** | - | A4/A5/D2 檢測 | ❌ 待實現 |

## 2. 優化後的數據流設計

### 2.1 增強型數據流
```
[TLE Data] → [Preprocessing] → [NetStack API+] → [Event Engine] → [Frontend]
     ↓            ↓                  ↓                ↓              ↓
  CelesTrak   智能篩選          增強 SGP4        A4/A5/D2      統一展示
              相位分散          時間窗口優化      事件檢測      換手動畫
```

### 2.2 新增模組設計

#### 預處理模組
```python
# netstack/src/services/satellite/preprocessing/satellite_selector.py

class IntelligentSatelliteSelector:
    """智能衛星選擇器"""
    
    def __init__(self, config):
        self.target_visible = config.target_visible_count  # 8-12
        self.constellation = config.constellation
        self.observer_location = config.observer_location
        
    def select_research_subset(self, all_satellites):
        """從完整星座中選擇研究子集"""
        
        # Step 1: 軌道平面分群
        orbital_groups = self.group_by_orbital_plane(all_satellites)
        
        # Step 2: 相位分散採樣
        phase_distributed = self.sample_with_phase_distribution(orbital_groups)
        
        # Step 3: 可見性評分
        scored_satellites = self.score_visibility(phase_distributed)
        
        # Step 4: 事件潛力評估
        event_aware = self.evaluate_event_potential(scored_satellites)
        
        # Step 5: 最終選擇
        final_subset = self.finalize_selection(event_aware)
        
        return final_subset
```

#### 事件檢測引擎
```python
# netstack/src/services/handover/event_detection_engine.py

class HandoverEventEngine:
    """換手事件檢測引擎"""
    
    def __init__(self):
        self.event_detectors = {
            'A4': EventA4Detector(),
            'A5': EventA5Detector(),
            'D2': EventD2Detector()
        }
        self.event_history = []
        
    def process_frame(self, satellite_states, timestamp):
        """處理單個時間幀的事件檢測"""
        
        detected_events = []
        
        for event_type, detector in self.event_detectors.items():
            events = detector.detect(satellite_states, timestamp)
            detected_events.extend(events)
        
        # 記錄歷史
        self.event_history.append({
            'timestamp': timestamp,
            'events': detected_events
        })
        
        return detected_events
```

## 3. API 端點擴展

### 3.1 現有 API 增強
```python
# 現有端點
GET /api/v1/satellite-ops/visible_satellites

# 增強參數
{
    "count": 120,              # 增加到研究級數量
    "min_elevation_deg": 10,   # 優化仰角門檻
    "observer_lat": 24.9441667,
    "observer_lon": 121.3713889,
    "constellation": "starlink",
    "utc_timestamp": "dynamic", # 新增：動態時間戳
    "selection_mode": "research", # 新增：研究模式
    "include_events": true      # 新增：包含事件信息
}
```

### 3.2 新增 API 端點
```python
# 新端點 1: 最佳時間窗口
GET /api/v1/satellite-ops/optimal_time_window
Response: {
    "start_time": "2025-01-23T00:00:00Z",
    "end_time": "2025-01-24T00:00:00Z",
    "quality_score": 95,
    "expected_visible_range": [8, 12]
}

# 新端點 2: 預處理衛星池
POST /api/v1/satellite-ops/preprocess_pool
Request: {
    "constellation": "starlink",
    "target_count": 120,
    "optimization_mode": "event_diversity"
}
Response: {
    "selected_satellites": [...],
    "event_coverage": {
        "A4": 45,
        "A5": 23,
        "D2": 67
    }
}

# 新端點 3: 換手事件流
GET /api/v1/handover/event_stream
Response: {
    "events": [
        {
            "timestamp": "2025-01-23T10:30:00Z",
            "type": "A4",
            "serving_satellite": "STARLINK-1234",
            "candidate_satellite": "STARLINK-5678",
            "trigger_data": {...}
        }
    ]
}
```

## 4. 數據存儲優化

### 4.1 預計算數據結構
```python
# PostgreSQL 表結構
CREATE TABLE preprocessed_satellite_pool (
    id SERIAL PRIMARY KEY,
    constellation VARCHAR(50),
    satellite_id VARCHAR(50),
    selection_score FLOAT,
    event_potential JSONB,
    orbital_parameters JSONB,
    created_at TIMESTAMP,
    valid_until TIMESTAMP
);

CREATE TABLE satellite_timeseries_cache (
    id SERIAL PRIMARY KEY,
    satellite_id VARCHAR(50),
    timestamp TIMESTAMP,
    position JSONB,  -- {lat, lon, alt}
    relative JSONB,   -- {elevation, azimuth, distance}
    signal JSONB,     -- {rsrp, doppler}
    events JSONB,     -- [detected events]
    INDEX idx_timestamp (timestamp),
    INDEX idx_satellite (satellite_id)
);
```

### 4.2 Redis 快取策略
```python
# Redis 快取鍵設計
cache_keys = {
    "visible_satellites": "sat:visible:{timestamp}:{location}",
    "optimal_window": "sat:window:{date}:{constellation}",
    "event_timeline": "sat:events:{start}:{end}",
    "preprocessed_pool": "sat:pool:{constellation}:{version}"
}

# 快取 TTL 設定
cache_ttl = {
    "visible_satellites": 30,     # 30 秒
    "optimal_window": 3600,       # 1 小時
    "event_timeline": 1800,       # 30 分鐘
    "preprocessed_pool": 21600    # 6 小時
}
```

## 5. 數據同步機制

### 5.1 前端數據同步優化
```typescript
// simworld/frontend/src/contexts/DataSyncContext.tsx 擴展

interface EnhancedSatelliteData {
    // 原有欄位
    satellites: SatellitePosition[]
    
    // 新增欄位
    events: HandoverEvent[]
    optimalWindow: TimeWindow
    preprocessedPool: SatellitePool
    statistics: {
        visibleCount: number
        eventRate: number
        handoverReadiness: boolean
    }
}

class EnhancedDataSyncContext {
    // 新增：智能數據預載
    async preloadTimeSegment(startTime: Date, duration: number) {
        const segments = this.splitIntoSegments(startTime, duration, 60) // 60秒段
        
        for (const segment of segments) {
            await this.loadSegmentData(segment)
        }
    }
    
    // 新增：事件驅動更新
    subscribeToEvents() {
        this.eventSource = new EventSource('/api/v1/handover/event_stream')
        
        this.eventSource.onmessage = (event) => {
            const handoverEvent = JSON.parse(event.data)
            this.handleHandoverEvent(handoverEvent)
        }
    }
}
```

### 5.2 WebSocket 即時更新
```javascript
// 建立 WebSocket 連接
const ws = new WebSocket('ws://localhost:8080/ws/satellite_updates')

ws.onmessage = (event) => {
    const update = JSON.parse(event.data)
    
    switch(update.type) {
        case 'POSITION_UPDATE':
            updateSatellitePositions(update.data)
            break
        case 'EVENT_TRIGGER':
            handleEventTrigger(update.data)
            break
        case 'HANDOVER_INITIATE':
            startHandoverAnimation(update.data)
            break
    }
}
```

## 6. 性能優化策略

### 6.1 批量處理
```python
class BatchProcessor:
    """批量處理優化器"""
    
    def __init__(self):
        self.batch_size = 100
        self.worker_count = 4
        
    async def process_satellite_batch(self, satellites, timestamp):
        """批量處理衛星計算"""
        
        batches = [
            satellites[i:i+self.batch_size] 
            for i in range(0, len(satellites), self.batch_size)
        ]
        
        tasks = []
        for batch in batches:
            task = asyncio.create_task(
                self.calculate_batch_positions(batch, timestamp)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return self.merge_results(results)
```

### 6.2 增量更新
```python
def incremental_update_strategy():
    """增量更新策略"""
    
    return {
        "full_update_interval": 3600,    # 每小時完整更新
        "incremental_interval": 30,      # 每30秒增量更新
        "delta_threshold": 0.1,          # 位置變化門檻
        "event_driven": True,            # 事件驅動立即更新
        "predictive_loading": True       # 預測性載入
    }
```

## 7. 預處理資料流重設計

### 7.1 資料流架構
```
[TLE更新] → [變化檢測] → [增量計算] → [分層存儲] → [API服務]
    ↓           ↓            ↓            ↓           ↓
 每6小時    比對差異     只算變化    熱/溫/冷層   快速響應
```

### 7.2 預處理更新機制
| 更新類型 | 觸發時機 | 範圍 | 計算量 |
|---------|----------|------|--------|
| **增量更新** | TLE 更新後 | 變化的衛星 | 小 (10-20%) |
| **滑動窗口** | 每小時 | 新增1小時數據 | 中 (全部衛星) |
| **完整刷新** | 每日凌晨 | 全部重算 | 大 (48小時) |
| **動態調整** | 驗證失敗時 | 增減衛星 | 視需求 |

### 7.3 存儲容量規劃
```python
capacity_planning = {
    "Redis (熱)": {
        "內容": "1小時預處理數據",
        "大小": "~10MB",
        "更新": "每30秒"
    },
    "PostgreSQL (溫)": {
        "內容": "48小時軌跡+事件",
        "大小": "~120MB",
        "更新": "每6小時"
    },
    "文件系統 (冷)": {
        "內容": "歷史存檔",
        "大小": "~600MB/月",
        "格式": "Parquet壓縮"
    }
}
```

## 8. 錯誤處理與降級

### 8.1 降級策略
```python
class GracefulDegradation:
    """優雅降級處理"""
    
    def handle_data_unavailable(self, error_type):
        """處理數據不可用情況"""
        
        if error_type == "TLE_OUTDATED":
            # 使用緩存的 TLE，添加警告
            return self.use_cached_tle_with_warning()
            
        elif error_type == "SGP4_FAILURE":
            # 降級到簡化軌道模型
            return self.fallback_to_simple_orbit()
            
        elif error_type == "EVENT_ENGINE_ERROR":
            # 禁用事件檢測，保持基本功能
            return self.disable_event_detection()
            
        elif error_type == "INSUFFICIENT_SATELLITES":
            # 降低可見性要求
            return self.reduce_visibility_requirements()
```

### 8.2 監控與告警
```python
monitoring_metrics = {
    "satellite_pool_size": "gauge",
    "visible_satellite_count": "histogram",
    "event_detection_rate": "counter",
    "api_response_time": "histogram",
    "sgp4_calculation_time": "histogram",
    "cache_hit_rate": "gauge",
    "data_freshness": "gauge"
}

alert_rules = {
    "low_visibility": "visible_satellites < 6 for 5 minutes",
    "high_latency": "api_response_time > 500ms for 1 minute",
    "stale_data": "data_age > 30 minutes",
    "event_detection_failure": "event_rate == 0 for 10 minutes"
}
```

## 8. 整合檢查清單

### 8.1 後端整合
- [ ] 擴展 NetStack satellite-ops API
- [ ] 實現智能衛星選擇器
- [ ] 添加事件檢測引擎
- [ ] 設置預計算任務
- [ ] 配置 Redis 快取

### 8.2 前端整合
- [ ] 更新 DataSyncContext
- [ ] 實現事件訂閱機制
- [ ] 添加預載入邏輯
- [ ] 整合 WebSocket 更新

### 8.3 數據庫整合
- [ ] 創建預處理表
- [ ] 設置時間序列快取
- [ ] 配置索引優化
- [ ] 實現清理策略

---

**下一步**: 查看 [實施計畫](./05-implementation-plan.md) 了解開發步驟