# 04 - Phase 3: API 端點實現

> **上一階段**：[Phase 2 - 預計算引擎](./03-phase2-precompute-engine.md)  < /dev/null |  **下一階段**：[Phase 4 - 前端時間軸](./05-phase4-frontend-timeline.md)

## 🎯 Phase 3 目標
**目標**：實現時間軸查詢 API 和時間控制 API
**預估時間**: 1-2 天

## 📋 開發任務

### 3.1 時間軸查詢 API
```python
@router.get("/satellites/history/at_time")
async def get_satellites_at_time(
    target_time: datetime,
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139,
    min_elevation: float = 10.0,
    count: int = 10
):
    """獲取指定時間點的衛星位置"""
    
    # 查詢預計算數據 (PostgreSQL)
    conn = await asyncpg.connect(RL_DATABASE_URL)
    try:
        satellites = await conn.fetch("""
            SELECT satellite_id, constellation, timestamp,
                   latitude, longitude, altitude, elevation_angle,
                   azimuth_angle, signal_strength, path_loss_db
            FROM satellite_orbital_cache 
            WHERE timestamp = $1 
              AND observer_latitude = $2 
              AND observer_longitude = $3
              AND elevation_angle >= $4
            ORDER BY elevation_angle DESC 
            LIMIT $5
        """, target_time, observer_lat, observer_lon, min_elevation, count)
    finally:
        await conn.close()
    
    return {
        "success": True,
        "timestamp": target_time.isoformat(),
        "satellites": satellites,
        "count": len(satellites)
    }
```

### 3.2 時間控制 API
```python
@router.get("/satellites/history/timeline_info")
async def get_timeline_info():
    """獲取可用的歷史數據時間範圍"""
    
    result = await query_timeline_range()
    
    return {
        "available_time_range": {
            "start": result["earliest_time"].isoformat(),
            "end": result["latest_time"].isoformat(),
            "total_duration_hours": result["duration_hours"],
            "total_timepoints": result["timepoints"]
        },
        "recommended_playback_speeds": [1, 2, 5, 10, 30, 60],
        "time_step_seconds": 30
    }
```

## 📋 實施檢查清單
- [ ] 實現時間點查詢端點
- [ ] 實現時間軸資訊端點
- [ ] 實現軌跡查詢端點
- [ ] 實現 D2 事件端點
- [ ] API 性能優化

## 🧪 驗證步驟
```bash
# 測試時間點查詢
curl -X GET "http://localhost:8080/api/v1/satellites/positions?timestamp=2025-01-23T12:00:00Z" | jq

# 測試時間軸資訊
curl -X GET "http://localhost:8080/api/v1/satellites/timeline/starlink" | jq
```

**完成標準**：API 響應時間 < 100ms，數據準確

