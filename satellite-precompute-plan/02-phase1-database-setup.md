# 02 - Phase 1: PostgreSQL 數據庫架構設置

> **上一階段**：[專案總覽](./01-project-overview.md)  < /dev/null |  **下一階段**：[Phase 2 - 預計算引擎](./03-phase2-precompute-engine.md)

## 🎯 Phase 1 目標

**目標**：建立 PostgreSQL 歷史數據存儲架構，實現容器啟動時立即數據可用

**預估時間**: 1-2 天

## 📋 開發任務

### 1.1 PostgreSQL 歷史數據表設計

#### **擴展現有數據表**
```sql
-- 擴展現有的 satellite_orbital_cache 表以支援歷史數據查詢
-- 表已存在於 NetStack RL PostgreSQL (172.20.0.51:5432/rl_research)

-- 添加台灣觀測者特定的字段
ALTER TABLE satellite_orbital_cache 
ADD COLUMN IF NOT EXISTS observer_latitude FLOAT,
ADD COLUMN IF NOT EXISTS observer_longitude FLOAT,
ADD COLUMN IF NOT EXISTS observer_altitude FLOAT,
ADD COLUMN IF NOT EXISTS signal_strength FLOAT,
ADD COLUMN IF NOT EXISTS path_loss_db FLOAT;

-- 添加歷史數據查詢索引
CREATE INDEX IF NOT EXISTS idx_orbital_observer_time 
ON satellite_orbital_cache (observer_latitude, observer_longitude, timestamp);

CREATE INDEX IF NOT EXISTS idx_orbital_elevation_time 
ON satellite_orbital_cache (elevation_angle, timestamp) 
WHERE elevation_angle >= 10;
```

#### **數據表結構說明**
```sql
-- satellite_orbital_cache 表結構:
-- 現有欄位:
-- id, satellite_id, norad_id, constellation, timestamp
-- position_x, position_y, position_z (ECI 座標)
-- latitude, longitude, altitude (地理座標)  
-- elevation_angle, azimuth_angle (相對觀測者)
-- range_rate, calculation_method, data_quality

-- 新增欄位:
-- observer_latitude, observer_longitude, observer_altitude (觀測者位置)
-- signal_strength, path_loss_db (信號品質計算)
```

### 1.2 容器內預載數據機制

#### **Docker 構建時預載數據**
```dockerfile
# netstack/Dockerfile 添加預載數據生成

# 第1步：構建時預計算歷史數據
RUN python3 generate_precomputed_satellite_data.py \
    --output /app/data/satellite_history_embedded.sql \
    --observer_lat 24.94417 \
    --observer_lon 121.37139 \
    --duration_hours 6 \
    --time_step_seconds 30

# 第2步：啟動時立即載入（無需網路連接）
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh
```

### 1.3 智能數據載入器實現

#### **立即載入服務**
```python
# app/services/instant_satellite_loader.py
import os
import asyncpg
import logging
from datetime import datetime, timedelta

class InstantSatelliteLoader:
    """容器啟動時立即載入衛星數據"""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.embedded_data_path = "/app/data/satellite_history_embedded.sql"
        
    async def ensure_data_available(self) -> bool:
        """確保衛星數據立即可用"""
        
        # 1. 檢查 PostgreSQL 中是否已有數據
        existing_data = await self._check_existing_data()
        
        if existing_data and self._is_data_fresh(existing_data):
            logging.info(f"✅ 發現 {existing_data['count']} 條新鮮的衛星歷史數據，跳過載入")
            return True
            
        # 2. 載入內建預載數據
        logging.info("📡 載入內建衛星歷史數據...")
        success = await self._load_embedded_data()
        
        if success:
            logging.info("✅ 衛星數據載入完成，系統立即可用")
            return True
            
        # 3. 緊急 fallback：生成最小可用數據集
        logging.warning("⚠️ 使用緊急 fallback 數據")
        return await self._generate_emergency_data()
        
    async def _check_existing_data(self):
        """檢查現有數據"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            result = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as count,
                    MAX(timestamp) as latest_time,
                    MIN(timestamp) as earliest_time
                FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417 
                  AND observer_longitude = 121.37139
            """)
            return dict(result) if result else None
        finally:
            await conn.close()
            
    def _is_data_fresh(self, data_info) -> bool:
        """判斷數據是否夠新鮮（7天內）"""
        if not data_info['latest_time']:
            return False
            
        age = datetime.utcnow() - data_info['latest_time'].replace(tzinfo=None)
        return age.days < 7 and data_info['count'] > 1000
        
    async def _load_embedded_data(self) -> bool:
        """載入內建預載數據"""
        if not os.path.exists(self.embedded_data_path):
            logging.error(f"❌ 內建數據文件不存在: {self.embedded_data_path}")
            return False
            
        conn = await asyncpg.connect(self.postgres_url)
        try:
            # 清空舊數據
            await conn.execute("""
                DELETE FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417 AND observer_longitude = 121.37139
            """)
            
            # 載入預載數據
            with open(self.embedded_data_path, 'r') as f:
                sql_content = f.read()
                await conn.execute(sql_content)
                
            # 驗證載入結果
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM satellite_orbital_cache 
                WHERE observer_latitude = 24.94417 AND observer_longitude = 121.37139
            """)
            
            logging.info(f"✅ 成功載入 {count} 條預載衛星數據")
            return count > 0
            
        except Exception as e:
            logging.error(f"❌ 載入內建數據失敗: {e}")
            return False
        finally:
            await conn.close()
            
    async def _generate_emergency_data(self) -> bool:
        """生成緊急最小數據集（1小時數據）"""
        from .emergency_satellite_generator import EmergencySatelliteGenerator
        
        generator = EmergencySatelliteGenerator(self.postgres_url)
        return await generator.generate_minimal_dataset(
            observer_lat=24.94417,
            observer_lon=121.37139,
            duration_hours=1,
            time_step_seconds=60
        )
```

#### **緊急數據生成器**
```python
# app/services/emergency_satellite_generator.py
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import math

class EmergencySatelliteGenerator:
    """緊急情況下生成最小可用衛星數據集"""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        
    async def generate_minimal_dataset(
        self, 
        observer_lat: float, 
        observer_lon: float,
        duration_hours: int = 1,
        time_step_seconds: int = 60
    ) -> bool:
        """生成最小數據集以確保系統可用"""
        
        try:
            # 生成簡化的衛星軌跡數據（基於數學模型）
            emergency_data = self._generate_simplified_orbits(
                observer_lat, observer_lon, duration_hours, time_step_seconds
            )
            
            # 存儲到數據庫
            success = await self._store_emergency_data(emergency_data)
            
            if success:
                logging.info(f"✅ 緊急數據生成完成，共 {len(emergency_data)} 條記錄")
                return True
            else:
                logging.error("❌ 緊急數據存儲失敗")
                return False
                
        except Exception as e:
            logging.error(f"❌ 緊急數據生成失敗: {e}")
            return False
            
    def _generate_simplified_orbits(
        self, 
        observer_lat: float, 
        observer_lon: float,
        duration_hours: int,
        time_step_seconds: int
    ) -> List[Dict]:
        """生成簡化軌道數據（數學模型，非真實 TLE）"""
        
        data = []
        start_time = datetime.utcnow()
        
        # 模擬 6 顆 LEO 衛星的軌道
        satellites = [
            {"id": f"EMERGENCY-SAT-{i+1}", "norad_id": 50000 + i, "orbit_offset": i * 60}
            for i in range(6)
        ]
        
        time_points = int(duration_hours * 3600 / time_step_seconds)
        
        for t in range(time_points):
            current_time = start_time + timedelta(seconds=t * time_step_seconds)
            
            for sat in satellites:
                # 簡化的圓軌道計算
                orbit_period = 90 * 60  # 90 分鐘軌道週期
                angular_velocity = 2 * math.pi / orbit_period
                
                # 軌道角度（考慮時間和衛星偏移）
                angle = (angular_velocity * t * time_step_seconds + 
                        math.radians(sat["orbit_offset"])) % (2 * math.pi)
                
                # 簡化的衛星位置計算
                sat_lat = 30 * math.sin(angle)  # ±30度緯度範圍
                sat_lon = (observer_lon + 180 * math.cos(angle)) % 360
                if sat_lon > 180:
                    sat_lon -= 360
                    
                # 計算相對觀測者的方位和仰角
                lat_diff = math.radians(sat_lat - observer_lat)
                lon_diff = math.radians(sat_lon - observer_lon)
                
                distance = 6371 * math.acos(
                    math.sin(math.radians(observer_lat)) * math.sin(math.radians(sat_lat)) +
                    math.cos(math.radians(observer_lat)) * math.cos(math.radians(sat_lat)) * 
                    math.cos(lon_diff)
                )
                
                # 簡化仰角計算
                elevation = max(-10, 90 - distance * 0.3)  # 簡化模型
                azimuth = (math.degrees(math.atan2(lon_diff, lat_diff)) + 360) % 360
                
                # 只保留仰角 > -5 度的數據點
                if elevation > -5:
                    record = {
                        "satellite_id": sat["id"],
                        "norad_id": sat["norad_id"],
                        "constellation": "emergency",
                        "timestamp": current_time,
                        "latitude": sat_lat,
                        "longitude": sat_lon,
                        "altitude": 550,  # 固定高度
                        "elevation_angle": elevation,
                        "azimuth_angle": azimuth,
                        "observer_latitude": observer_lat,
                        "observer_longitude": observer_lon,
                        "observer_altitude": 100,
                        "signal_strength": max(20, 80 - distance),
                        "path_loss_db": 120 + 20 * math.log10(max(1, distance)),
                        "calculation_method": "emergency_simplified",
                        "data_quality": 0.5  # 標記為低品質數據
                    }
                    data.append(record)
                    
        return data
        
    async def _store_emergency_data(self, data: List[Dict]) -> bool:
        """存儲緊急數據到數據庫"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            # 清空現有緊急數據
            await conn.execute("""
                DELETE FROM satellite_orbital_cache 
                WHERE constellation = 'emergency'
            """)
            
            # 批次插入
            records = [
                (
                    record["satellite_id"], record["norad_id"], record["constellation"],
                    record["timestamp"], 0, 0, 0,  # position_x, y, z 設為 0
                    record["latitude"], record["longitude"], record["altitude"],
                    record["elevation_angle"], record["azimuth_angle"], 0,  # range_rate
                    record["observer_latitude"], record["observer_longitude"], 
                    record["observer_altitude"], record["signal_strength"],
                    record["path_loss_db"], record["calculation_method"], 
                    record["data_quality"]
                )
                for record in data
            ]
            
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
            """, records)
            
            return True
            
        except Exception as e:
            logging.error(f"❌ 緊急數據存儲失敗: {e}")
            return False
        finally:
            await conn.close()
```

## 📋 實施檢查清單

### **數據庫設置檢查**
- [ ] 擴展 `satellite_orbital_cache` 表字段
- [ ] 創建觀測者位置索引
- [ ] 創建仰角時間索引
- [ ] 測試索引查詢性能

### **容器預載機制檢查**
- [ ] 修改 `netstack/Dockerfile` 添加預載步驟
- [ ] 創建 `docker-entrypoint.sh` 啟動腳本
- [ ] 實現 `InstantSatelliteLoader` 類
- [ ] 實現 `EmergencySatelliteGenerator` 類

### **系統整合檢查**
- [ ] 容器啟動時自動載入數據
- [ ] 數據載入失敗時啟用緊急模式
- [ ] 日誌記錄完整且清晰
- [ ] 數據品質標記正確

## 🧪 驗證步驟

### **基本功能驗證**
```bash
# 1. 檢查數據表結構
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "\d satellite_orbital_cache"

# 2. 檢查索引創建
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'satellite_orbital_cache';"

# 3. 測試數據載入
docker restart netstack-api
docker logs netstack-api | grep -E "(衛星數據|satellite.*load)"
```

### **數據完整性驗證**
```bash
# 檢查載入的數據量
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT constellation, COUNT(*) as record_count, 
       MIN(timestamp) as earliest, MAX(timestamp) as latest
FROM satellite_orbital_cache 
WHERE observer_latitude = 24.94417
GROUP BY constellation;"
```

### **API 可用性驗證**
```bash
# 測試 API 是否立即可用
curl -X GET "http://localhost:8080/api/v1/satellites/health" | jq

# 預期響應：
# {
#   "status": "healthy",
#   "database": "postgresql",
#   "data_loaded": true,
#   "record_count": 2000
# }
```

## ⚠️ 注意事項

1. **數據品質標記**：緊急數據必須標記 `data_quality < 1.0`
2. **索引優化**：確保查詢索引覆蓋常用查詢模式
3. **錯誤處理**：數據載入失敗時不應導致容器啟動失敗
4. **日誌記錄**：所有載入步驟都要有清晰的日誌
5. **資源限制**：預載數據不應超過 10MB 以避免影響構建時間

---

**🎯 完成標準**：容器啟動後 30 秒內 API 可用且有衛星數據返回

**下一階段**：[Phase 2 - 預計算引擎開發](./03-phase2-precompute-engine.md)

