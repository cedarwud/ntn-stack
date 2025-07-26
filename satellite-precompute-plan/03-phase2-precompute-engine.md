# 03 - Phase 2: 數據預計算引擎開發

> **上一階段**：[Phase 1 - 數據庫設置](./02-phase1-database-setup.md)  < /dev/null |  **下一階段**：[Phase 3 - API 端點](./04-phase3-api-endpoints.md)

## 🎯 Phase 2 目標
**目標**：開發歷史數據預計算器，實現真實 TLE 數據的 SGP4 軌道計算和批次存儲
**預估時間**: 2-3 天

## 📋 開發任務

### 2.1 歷史數據預計算器

#### **完整的預計算器實現**
```python
# precompute_satellite_history.py
import math
from datetime import datetime, timedelta
from skyfield.api import load, wgs84, EarthSatellite
from typing import List, Dict, Tuple

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
        
    def compute_visible_satellites(self, timestamp):
        """計算指定時間所有可見衛星位置"""
        visible = []
        ts = load.timescale()
        t = ts.from_datetime(timestamp)
        
        for satellite_data in self.tle_data:
            satellite = EarthSatellite(satellite_data.line1, satellite_data.line2, satellite_data.name, ts)
            
            # SGP4 軌道計算
            difference = satellite - self.observer
            topocentric = difference.at(t)
            alt, az, distance = topocentric.altaz()
            
            if alt.degrees >= -10:  # 可見性閾值
                geocentric = satellite.at(t)
                subpoint = wgs84.subpoint(geocentric)
                
                position_data = {
                    "timestamp": timestamp,
                    "satellite_id": satellite_data.norad_id,
                    "satellite_name": satellite_data.name,
                    "observer_position": {
                        "latitude": self.observer.latitude.degrees,
                        "longitude": self.observer.longitude.degrees,
                        "altitude": self.observer.elevation.km * 1000
                    },
                    "satellite_position": {
                        "latitude": subpoint.latitude.degrees,
                        "longitude": subpoint.longitude.degrees,
                        "altitude": subpoint.elevation.km,
                        "elevation": alt.degrees,
                        "azimuth": az.degrees,
                        "range": distance.km,
                        "velocity": 7.5  # LEO 平均速度
                    },
                    "signal_quality": {
                        "path_loss_db": 120 + 20 * math.log10(distance.km),
                        "signal_strength": max(30, 80 - distance.km / 25)
                    }
                }
                
                visible.append(position_data)
                
        return visible
        
    def load_tle_data(self, tle_file_path):
        """載入 TLE 數據文件"""
        with open(tle_file_path, 'r') as f:
            lines = f.readlines()
            
        tle_data = []
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # 提取 NORAD ID
                norad_id = int(line1[2:7])
                
                tle_data.append({
                    'name': name,
                    'line1': line1,
                    'line2': line2,
                    'norad_id': norad_id
                })
                
        return tle_data
```

#### **TLE 數據下載器**
```python
# app/services/tle_downloader.py
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Dict, List

class TLEDataDownloader:
    """真實 TLE 數據下載器"""
    
    def __init__(self):
        self.tle_sources = {
            "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            "oneweb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle"
        }
        
    async def download_constellation_data(self, constellation: str) -> Dict:
        """下載指定星座的 TLE 數據"""
        if constellation not in self.tle_sources:
            raise ValueError(f"不支援的星座: {constellation}")
            
        url = self.tle_sources[constellation]
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        tle_content = await response.text()
                        parsed_data = self._parse_tle_content(tle_content, constellation)
                        
                        logging.info(f"✅ 成功下載 {constellation} TLE 數據：{len(parsed_data)} 顆衛星")
                        
                        return {
                            "constellation": constellation,
                            "download_time": datetime.utcnow(),
                            "satellite_count": len(parsed_data),
                            "tle_data": parsed_data
                        }
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            logging.error(f"❌ 下載 {constellation} TLE 數據失敗: {e}")
            raise
            
    def _parse_tle_content(self, content: str, constellation: str) -> List[Dict]:
        """解析 TLE 格式數據"""
        lines = content.strip().split('\n')
        satellites = []
        
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # 驗證 TLE 格式
                if len(line1) == 69 and len(line2) == 69 and line1[0] == '1' and line2[0] == '2':
                    norad_id = int(line1[2:7])
                    epoch = self._parse_epoch(line1[18:32])
                    
                    satellites.append({
                        "name": name,
                        "norad_id": norad_id,
                        "constellation": constellation,
                        "line1": line1,
                        "line2": line2,
                        "epoch": epoch,
                        "is_active": True
                    })
                    
        return satellites
        
    def _parse_epoch(self, epoch_str: str) -> datetime:
        """解析 TLE epoch 時間"""
        year = int(epoch_str[:2])
        if year < 57:
            year += 2000
        else:
            year += 1900
            
        day_of_year = float(epoch_str[2:])
        
        # 轉換為 datetime
        base_date = datetime(year, 1, 1)
        epoch_date = base_date + timedelta(days=day_of_year - 1)
        
        return epoch_date
    
    async def download_multiple_constellations(self, constellations: List[str]) -> Dict:
        """並行下載多個星座數據"""
        tasks = [self.download_constellation_data(const) for const in constellations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_downloads = {}
        failed_downloads = {}
        
        for i, result in enumerate(results):
            constellation = constellations[i]
            if isinstance(result, Exception):
                failed_downloads[constellation] = str(result)
            else:
                successful_downloads[constellation] = result
                
        return {
            "successful": successful_downloads,
            "failed": failed_downloads,
            "total_satellites": sum(data["satellite_count"] for data in successful_downloads.values())
        }
```

### 2.2 批次處理和存儲

#### **完整的批次處理器實現**
```python
# batch_processor.py
import asyncpg
import logging
from typing import List, Dict
from datetime import datetime

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
                    INSERT INTO satellite_orbital_cache (
                        satellite_id, norad_id, constellation, timestamp,
                        position_x, position_y, position_z,
                        latitude, longitude, altitude,
                        elevation_angle, azimuth_angle, range_rate,
                        observer_latitude, observer_longitude, observer_altitude,
                        signal_strength, path_loss_db,
                        calculation_method, data_quality
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                    ON CONFLICT (satellite_id, timestamp) DO UPDATE SET
                        elevation_angle = EXCLUDED.elevation_angle,
                        azimuth_angle = EXCLUDED.azimuth_angle,
                        signal_strength = EXCLUDED.signal_strength,
                        path_loss_db = EXCLUDED.path_loss_db
                """, [self._prepare_record(record) for record in batch])
                
                logging.info(f"已存儲 {i + len(batch)}/{len(precomputed_data)} 條記錄到 PostgreSQL")
                
        finally:
            await conn.close()
            
    def _prepare_record(self, record: Dict) -> tuple:
        """準備 PostgreSQL 插入記錄"""
        return (
            record["satellite_id"], record["norad_id"], record["constellation"],
            record["timestamp"], record["position_x"], record["position_y"], record["position_z"],
            record["satellite_position"]["latitude"], record["satellite_position"]["longitude"], 
            record["satellite_position"]["altitude"], record["satellite_position"]["elevation"],
            record["satellite_position"]["azimuth"], record["satellite_position"]["range_rate"],
            record["observer_position"]["latitude"], record["observer_position"]["longitude"], 
            record["observer_position"]["altitude"], record["signal_quality"]["signal_strength"],
            record["signal_quality"]["path_loss_db"], "SGP4", 1.0
        )
        
    async def incremental_update(self, new_data: List[Dict]):
        """增量更新數據（用於背景更新）"""
        if not new_data:
            logging.info("⏭️ 沒有新數據需要更新")
            return
            
        conn = await asyncpg.connect(self.postgres_url)
        try:
            # 獲取現有數據的時間範圍
            latest_time = await conn.fetchval("""
                SELECT MAX(timestamp) FROM satellite_orbital_cache 
                WHERE observer_latitude = $1 AND observer_longitude = $2
            """, new_data[0]["observer_position"]["latitude"], 
                 new_data[0]["observer_position"]["longitude"])
            
            if latest_time:
                # 只插入比現有數據更新的記錄
                new_records = [
                    record for record in new_data 
                    if record["timestamp"] > latest_time.replace(tzinfo=None)
                ]
                
                if new_records:
                    await self.process_and_store(new_records)
                    logging.info(f"✅ 增量更新 {len(new_records)} 條新記錄")
                else:
                    logging.info("⏭️ 數據已是最新，無需更新")
            else:
                # 沒有現有數據，全部插入
                await self.process_and_store(new_data)
                logging.info(f"✅ 初次載入 {len(new_data)} 條記錄")
                
        finally:
            await conn.close()
            
    async def cleanup_old_data(self, cutoff_date: datetime, observer_coords: tuple):
        """清理過期數據（保留指定日期之後的數據）"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            deleted_count = await conn.fetchval("""
                DELETE FROM satellite_orbital_cache 
                WHERE timestamp < $1 
                  AND observer_latitude = $2 
                  AND observer_longitude = $3
                RETURNING COUNT(*)
            """, cutoff_date, observer_coords[0], observer_coords[1])
            
            logging.info(f"🗑️ 清理了 {deleted_count or 0} 條過期數據（{cutoff_date} 之前）")
            return deleted_count or 0
            
        finally:
            await conn.close()
            
    async def get_data_statistics(self, observer_coords: tuple) -> Dict:
        """獲取數據統計信息"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT satellite_id) as unique_satellites,
                    COUNT(DISTINCT constellation) as constellations,
                    MIN(timestamp) as earliest_time,
                    MAX(timestamp) as latest_time,
                    AVG(signal_strength) as avg_signal_strength,
                    AVG(elevation_angle) as avg_elevation
                FROM satellite_orbital_cache 
                WHERE observer_latitude = $1 AND observer_longitude = $2
            """, observer_coords[0], observer_coords[1])
            
            if stats and stats['total_records'] > 0:
                duration_hours = (
                    stats['latest_time'] - stats['earliest_time']
                ).total_seconds() / 3600 if stats['latest_time'] and stats['earliest_time'] else 0
                
                return {
                    "total_records": stats['total_records'],
                    "unique_satellites": stats['unique_satellites'],
                    "constellations": stats['constellations'],
                    "time_range": {
                        "start": stats['earliest_time'].isoformat() if stats['earliest_time'] else None,
                        "end": stats['latest_time'].isoformat() if stats['latest_time'] else None,
                        "duration_hours": round(duration_hours, 2)
                    },
                    "signal_quality": {
                        "avg_signal_strength": round(stats['avg_signal_strength'], 2) if stats['avg_signal_strength'] else 0,
                        "avg_elevation": round(stats['avg_elevation'], 2) if stats['avg_elevation'] else 0
                    }
                }
            else:
                return {
                    "total_records": 0,
                    "message": "無歷史數據"
                }
                
        finally:
            await conn.close()
```

#### **預計算作業管理器**
```python
# app/services/precompute_job_manager.py
import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PrecomputeJobManager:
    """預計算作業管理器"""
    
    def __init__(self):
        self.active_jobs: Dict[str, Dict] = {}
        
    async def create_precompute_job(
        self, 
        constellation: str,
        start_time: datetime,
        end_time: datetime,
        observer_coords: tuple,
        time_step_seconds: int = 30
    ) -> str:
        """創建預計算作業"""
        
        job_id = f"precompute_{constellation}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 估算總計算量
        duration_seconds = (end_time - start_time).total_seconds()
        total_timepoints = int(duration_seconds / time_step_seconds)
        estimated_duration_minutes = max(1, total_timepoints / 1000)  # 估算：1000 個時間點/分鐘
        
        job_info = {
            "job_id": job_id,
            "constellation": constellation,
            "start_time": start_time,
            "end_time": end_time,
            "observer_coords": observer_coords,
            "time_step_seconds": time_step_seconds,
            "total_calculations": total_timepoints,
            "estimated_duration_minutes": estimated_duration_minutes,
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow(),
            "progress": 0.0,
            "error_message": None
        }
        
        self.active_jobs[job_id] = job_info
        
        # 異步啟動作業
        asyncio.create_task(self._execute_precompute_job(job_id))
        
        logging.info(f"📋 創建預計算作業 {job_id}：{constellation} 星座，{total_timepoints} 個計算點")
        
        return job_id
        
    async def get_job_status(self, job_id: str) -> Optional[Dict]:
        """獲取作業狀態"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id].copy()
            job['status'] = job['status'].value
            
            # 移除內部使用的對象
            if 'start_time' in job:
                job['start_time'] = job['start_time'].isoformat()
            if 'end_time' in job:
                job['end_time'] = job['end_time'].isoformat()
            if 'created_at' in job:
                job['created_at'] = job['created_at'].isoformat()
                
            return job
        return None
        
    async def cancel_job(self, job_id: str) -> bool:
        """取消作業"""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job['status'] in [JobStatus.PENDING, JobStatus.RUNNING]:
                job['status'] = JobStatus.CANCELLED
                logging.info(f"❌ 取消預計算作業 {job_id}")
                return True
        return False
        
    async def _execute_precompute_job(self, job_id: str):
        """執行預計算作業"""
        job = self.active_jobs[job_id]
        
        try:
            job['status'] = JobStatus.RUNNING
            job['started_at'] = datetime.utcnow()
            
            logging.info(f"🚀 開始執行預計算作業 {job_id}")
            
            # 下載 TLE 數據
            from .tle_downloader import TLEDataDownloader
            downloader = TLEDataDownloader()
            tle_data = await downloader.download_constellation_data(job['constellation'])
            
            # 執行預計算
            from ..precompute_satellite_history import SatelliteHistoryPrecomputer
            precomputer = SatelliteHistoryPrecomputer(
                tle_data=tle_data['tle_data'],
                observer_coords=job['observer_coords'],
                time_range=(job['start_time'], job['end_time'])
            )
            
            # 分批計算以便更新進度
            batch_duration = timedelta(hours=1)  # 每次計算 1 小時的數據
            current_time = job['start_time']
            all_results = []
            
            while current_time < job['end_time']:
                if job['status'] == JobStatus.CANCELLED:
                    logging.info(f"⏹️ 作業 {job_id} 已被取消")
                    return
                    
                batch_end = min(current_time + batch_duration, job['end_time'])
                
                # 計算當前批次
                batch_precomputer = SatelliteHistoryPrecomputer(
                    tle_data=tle_data['tle_data'],
                    observer_coords=job['observer_coords'],
                    time_range=(current_time, batch_end)
                )
                
                batch_results = batch_precomputer.compute_history(job['time_step_seconds'])
                all_results.extend(batch_results)
                
                # 更新進度
                progress = (current_time - job['start_time']).total_seconds() / (job['end_time'] - job['start_time']).total_seconds()
                job['progress'] = min(progress * 100, 100.0)
                
                logging.info(f"📊 作業 {job_id} 進度: {job['progress']:.1f}%")
                
                current_time = batch_end
                
            # 存儲結果
            from .batch_processor import HistoryBatchProcessor
            processor = HistoryBatchProcessor(os.getenv('RL_DATABASE_URL'))
            await processor.process_and_store(all_results)
            
            # 作業完成
            job['status'] = JobStatus.COMPLETED
            job['completed_at'] = datetime.utcnow()
            job['progress'] = 100.0
            job['total_records'] = len(all_results)
            
            logging.info(f"✅ 預計算作業 {job_id} 完成：處理了 {len(all_results)} 條記錄")
            
        except Exception as e:
            job['status'] = JobStatus.FAILED
            job['error_message'] = str(e)
            job['failed_at'] = datetime.utcnow()
            
            logging.error(f"❌ 預計算作業 {job_id} 失敗: {e}")
            
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """清理完成的作業記錄"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if job['status'] in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                job_time = job.get('completed_at') or job.get('failed_at') or job['created_at']
                if job_time < cutoff_time:
                    jobs_to_remove.append(job_id)
                    
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            
        if jobs_to_remove:
            logging.info(f"🗑️ 清理了 {len(jobs_to_remove)} 個過期作業記錄")

# 全域作業管理器實例
job_manager = PrecomputeJobManager()
```

## 📋 實施檢查清單

### **核心組件實現檢查**
- [ ] 實現完整的 SatelliteHistoryPrecomputer 類
- [ ] 實現完整的 HistoryBatchProcessor 類  
- [ ] 實現 TLEDataDownloader 數據下載器
- [ ] 實現 PrecomputeJobManager 作業管理器
- [ ] SGP4 軌道計算集成和信號強度計算
- [ ] 批次存儲優化和衝突處理

### **功能特性檢查**
- [ ] TLE 數據下載和格式驗證
- [ ] 多星座並行下載支援
- [ ] 預計算作業進度追蹤
- [ ] 增量數據更新機制
- [ ] 過期數據自動清理
- [ ] 數據統計和監控功能

### **錯誤處理檢查**
- [ ] TLE 下載失敗處理
- [ ] 預計算作業取消機制
- [ ] 數據庫連接錯誤處理
- [ ] 記憶體不足保護措施

## 🧪 驗證步驟

### **2.1 TLE 數據下載驗證**
```bash
# 1. 測試單一星座 TLE 數據獲取
curl -X POST "http://localhost:8080/api/v1/satellites/tle/download" \
  -H "Content-Type: application/json" \
  -d '{
    "constellations": ["starlink"],
    "force_update": false
  }' | jq

# 預期響應：
# {
#   "success": true,
#   "downloaded": {
#     "starlink": 6
#   },
#   "total_satellites": 6,
#   "download_time_ms": 1500
# }

# 2. 測試多星座並行下載
curl -X POST "http://localhost:8080/api/v1/satellites/tle/download" \
  -H "Content-Type: application/json" \
  -d '{
    "constellations": ["starlink", "oneweb"],
    "force_update": true
  }' | jq
```

### **2.2 預計算作業驗證**
```bash
# 1. 啟動軌道預計算作業
curl -X POST "http://localhost:8080/api/v1/satellites/precompute" \
  -H "Content-Type: application/json" \
  -d '{
    "constellation": "starlink",
    "start_time": "2025-01-23T00:00:00Z",
    "end_time": "2025-01-23T06:00:00Z",
    "time_step_seconds": 30,
    "observer_location": {
      "latitude": 24.94417,
      "longitude": 121.37139,
      "altitude": 100
    }
  }' | jq

# 預期響應：
# {
#   "job_id": "precompute_starlink_20250123",
#   "status": "running",
#   "estimated_duration_minutes": 5,
#   "total_calculations": 2880
# }

# 2. 檢查預計算進度
JOB_ID="precompute_starlink_20250123_abcd1234"
curl -X GET "http://localhost:8080/api/v1/satellites/precompute/$JOB_ID/status" | jq

# 3. 取消作業（如需要）
curl -X DELETE "http://localhost:8080/api/v1/satellites/precompute/$JOB_ID" | jq
```

### **2.3 數據存儲驗證**
```bash
# 1. 驗證預計算結果存儲
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, 
       COUNT(*) as total_records,
       COUNT(DISTINCT satellite_id) as unique_satellites,
       MIN(timestamp) as earliest_time,
       MAX(timestamp) as latest_time
FROM satellite_orbital_cache 
WHERE constellation = 'starlink'
GROUP BY constellation;"

# 2. 檢查數據品質
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation,
       AVG(signal_strength) as avg_signal,
       AVG(elevation_angle) as avg_elevation,
       COUNT(*) FILTER (WHERE elevation_angle >= 10) as visible_count
FROM satellite_orbital_cache 
WHERE observer_latitude = 24.94417 AND observer_longitude = 121.37139
GROUP BY constellation;"

# 3. 驗證索引效能
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
EXPLAIN ANALYZE SELECT * FROM satellite_orbital_cache 
WHERE observer_latitude = 24.94417 
  AND observer_longitude = 121.37139 
  AND timestamp = '2025-01-23T12:00:00Z'
  AND elevation_angle >= 10
ORDER BY elevation_angle DESC LIMIT 10;"
```

### **2.4 效能基準測試**
```bash
# 1. 批量插入效能測試
curl -X POST "http://localhost:8080/api/v1/satellites/benchmark/batch_insert" \
  -H "Content-Type: application/json" \
  -d '{
    "record_count": 10000,
    "constellation": "starlink"
  }' | jq

# 預期：throughput > 1000 records/second

# 2. 查詢效能測試
curl -X POST "http://localhost:8080/api/v1/satellites/benchmark/query_performance" \
  -H "Content-Type: application/json" \
  -d '{
    "query_count": 100,
    "timestamp": "2025-01-23T12:00:00Z"
  }' | jq

# 預期：平均查詢時間 < 50ms
```

### **2.5 數據統計驗證**
```bash
# 獲取數據統計報告
curl -X GET "http://localhost:8080/api/v1/satellites/statistics" \
  -G \
  -d "observer_lat=24.94417" \
  -d "observer_lon=121.37139" | jq

# 預期響應：
# {
#   "total_records": 15840,
#   "unique_satellites": 6,
#   "constellations": 1,
#   "time_range": {
#     "start": "2025-01-23T00:00:00Z",
#     "end": "2025-01-23T06:00:00Z",
#     "duration_hours": 6.0
#   },
#   "signal_quality": {
#     "avg_signal_strength": 65.2,
#     "avg_elevation": 25.8
#   }
# }
```

## ⚠️ 注意事項

### **性能考量**
1. **記憶體管理**：大型預計算作業應使用分批處理，避免記憶體溢出
2. **網路超時**：TLE 下載設置合適的超時時間（建議 30 秒）
3. **數據庫連接**：使用連接池，避免頻繁建立/關閉連接
4. **並發控制**：同時運行的預計算作業不超過 2 個

### **數據品質保證**
1. **TLE 驗證**：確保 TLE 格式正確，epoch 時間合理
2. **軌道計算驗證**：與 Skyfield 基準比較，位置誤差 < 1km
3. **信號強度合理性**：確保信號強度在合理範圍內
4. **數據完整性**：檢查時間序列是否連續，無遺漏點

### **容錯機制**
1. **分批恢復**：作業失敗時能從最後成功的批次恢復
2. **降級策略**：TLE 下載失敗時使用緩存數據
3. **監控告警**：關鍵錯誤應觸發監控告警
4. **數據備份**：重要數據定期備份到外部存儲

---

**🎯 完成標準**：
- 成功預計算 6 小時歷史數據，包含 6-8 顆可見衛星
- 批次插入效能 > 1000 條/秒
- 查詢響應時間 < 50ms
- 位置計算精度誤差 < 1km（與 Skyfield 基準比較）
- 所有錯誤情況都有適當的處理和日誌記錄

