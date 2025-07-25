# 03 - Phase 2: 數據預計算引擎開發

> **上一階段**：[Phase 1 - 數據庫設置](./02-phase1-database-setup.md)  < /dev/null |  **下一階段**：[Phase 3 - API 端點](./04-phase3-api-endpoints.md)

## 🎯 Phase 2 目標
**目標**：開發歷史數據預計算器，實現真實 TLE 數據的 SGP4 軌道計算和批次存儲
**預估時間**: 2-3 天

## 📋 開發任務

### 2.1 歷史數據預計算器
```python
# precompute_satellite_history.py
class SatelliteHistoryPrecomputer:
    def __init__(self, tle_file_path, observer_coords, time_range):
        self.tle_data = self.load_tle_data(tle_file_path)
        self.observer = wgs84.latlon(*observer_coords)
        self.time_range = time_range
        
    def compute_history(self, time_interval_seconds=30):
        """預計算指定時間範圍內的所有衛星位置"""
        results = []
        
        start_time = self.time_range[0] 
        end_time = self.time_range[1]
        
        current_time = start_time
        while current_time <= end_time:
            # 計算所有衛星在當前時間的位置
            visible_satellites = self.compute_visible_satellites(current_time)
            results.extend(visible_satellites)
            
            current_time += timedelta(seconds=time_interval_seconds)
            
        return results
```

### 2.2 批次處理和存儲
```python
# batch_processor.py
class HistoryBatchProcessor:
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        
    async def process_and_store(self, precomputed_data: List[Dict]):
        """批次存儲預計算數據到 PostgreSQL"""
        batch_size = 1000
        
        conn = await asyncpg.connect(self.postgres_url)
        try:
            for i in range(0, len(precomputed_data), batch_size):
                batch = precomputed_data[i:i + batch_size]
                
                # 批次插入到 satellite_orbital_cache
                await conn.executemany("""
                    INSERT INTO satellite_orbital_cache (...)
                    VALUES (...)
                    ON CONFLICT (satellite_id, timestamp) DO UPDATE SET ...
                """, [self._prepare_record(record) for record in batch])
                
                print(f"已存儲 {i + len(batch)}/{len(precomputed_data)} 條記錄到 PostgreSQL")
                
        finally:
            await conn.close()
```

## 📋 實施檢查清單
- [ ] 實現 SatelliteHistoryPrecomputer 類
- [ ] 實現 HistoryBatchProcessor 類
- [ ] TLE 數據下載和解析功能
- [ ] SGP4 軌道計算集成
- [ ] 批次存儲優化

## 🧪 驗證步驟
```bash
# 1. 測試 TLE 數據獲取
curl -X POST "http://localhost:8080/api/v1/satellites/tle/download" | jq

# 2. 啟動軌道預計算作業
curl -X POST "http://localhost:8080/api/v1/satellites/precompute" | jq

# 3. 驗證預計算結果
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, COUNT(*) as total_records
FROM satellite_orbital_cache 
GROUP BY constellation;"
```

**完成標準**：成功預計算 6 小時歷史數據，插入效能 > 1000 條/秒

