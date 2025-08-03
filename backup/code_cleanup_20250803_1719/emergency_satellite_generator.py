import asyncpg
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math

logger = logging.getLogger(__name__)

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
                logger.info(f"✅ 緊急數據生成完成，共 {len(emergency_data)} 條記錄")
                return True
            else:
                logger.error("❌ 緊急數據存儲失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 緊急數據生成失敗: {e}")
            return False
            
    def _generate_simplified_orbits(
        self, 
        observer_lat: float, 
        observer_lon: float,
        duration_hours: int,
        time_step_seconds: int
    ) -> List[Dict[str, Any]]:
        """生成簡化軌道數據（數學模型，非真實 TLE）"""
        
        data = []
        start_time = datetime.utcnow()
        
        # 使用預載數據相同的 NORAD ID 範圍來避免外鍵約束問題
        emergency_norad_ids = [50000, 50001, 50002, 50003, 50004, 50005]
        satellites = [
            {"id": f"EMERGENCY-SAT-{i+1}", "norad_id": emergency_norad_ids[i], "orbit_offset": i * 30}
            for i in range(6)
        ]
        
        time_points = int(duration_hours * 3600 / time_step_seconds)
        
        for t in range(time_points):
            current_time = start_time + timedelta(seconds=t * time_step_seconds)
            
            for sat in satellites:
                # LEO 衛星軌道計算（550km，類似 Starlink）
                orbit_period = 95 * 60  # 95 分鐘軌道週期
                angular_velocity = 2 * math.pi / orbit_period
                
                # 軌道角度（考慮時間和衛星偏移）
                orbit_angle = (angular_velocity * t * time_step_seconds + 
                              math.radians(sat["orbit_offset"])) % (2 * math.pi)
                
                # 軌道傾斜角 53 度（類似 Starlink）
                inclination = math.radians(53.0)
                
                # 計算衛星緯度（基於軌道傾斜角）
                sat_lat = math.degrees(math.asin(math.sin(inclination) * math.sin(orbit_angle)))
                
                # 計算衛星經度（考慮地球自轉和軌道運動）
                earth_rotation = 2 * math.pi / (24 * 3600)  # 地球自轉角速度
                lon_drift = math.degrees(earth_rotation * t * time_step_seconds)
                sat_lon = (observer_lon + 30 * math.cos(orbit_angle) - lon_drift) % 360
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
                
                # 計算實際仰角（考慮衛星高度）
                if distance > 0:
                    elevation = math.degrees(math.atan2(550, distance))  # 550km 高度的衛星
                else:
                    elevation = 90.0
                    
                azimuth = (math.degrees(math.atan2(lon_diff, lat_diff)) + 360) % 360
                
                # 保留仰角 > 5 度的可見衛星（比較寬鬆的標準）
                if elevation > 5:
                    record = {
                        "satellite_id": sat["id"],
                        "norad_id": sat["norad_id"],
                        "constellation": "emergency",
                        "timestamp": current_time,
                        "latitude": sat_lat,
                        "longitude": sat_lon,
                        "altitude": 550000,  # 550km 轉換為米
                        "elevation_angle": elevation,
                        "azimuth_angle": azimuth,
                        "calculation_method": "emergency_simplified",
                        "data_quality": 0.5  # 標記為低品質數據
                    }
                    data.append(record)
                    
        return data
        
    async def _store_emergency_data(self, data: List[Dict[str, Any]]) -> bool:
        """存儲緊急數據到數據庫"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            # 清空現有緊急數據
            await conn.execute("""
                DELETE FROM satellite_orbital_cache 
                WHERE constellation = 'emergency'
            """)
            
            # 清空並創建緊急 TLE 數據
            await conn.execute("""
                DELETE FROM satellite_tle_data 
                WHERE constellation = 'emergency'
            """)
            
            # 為緊急衛星創建 TLE 數據
            from datetime import datetime
            emergency_norad_ids = [50000, 50001, 50002, 50003, 50004, 50005]
            for i, norad_id in enumerate(emergency_norad_ids):
                sat_id = f"EMERGENCY-SAT-{i+1}"
                await conn.execute("""
                    INSERT INTO satellite_tle_data (
                        satellite_id, norad_id, satellite_name, constellation,
                        line1, line2, epoch, orbital_period
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (norad_id) DO NOTHING
                """, sat_id, norad_id, sat_id, "emergency",
                    f"1 {norad_id}U 24001A   24001.00000000  .00000000  00000-0  00000-0 0  9990",
                    f"2 {norad_id}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000",
                    datetime(2024, 1, 1), 95.0)
            
            # 批次插入
            records = []
            for record in data:
                records.append((
                    record["satellite_id"], record["norad_id"], record["constellation"],
                    record["timestamp"], 0, 0, 0,  # position_x, y, z 設為 0
                    record["latitude"], record["longitude"], record["altitude"],
                    0, 0, 0,  # velocity_x, y, z 設為 0
                    None,  # orbital_period
                    record["elevation_angle"], record["azimuth_angle"], 0,  # range_rate
                    record["calculation_method"], record["data_quality"]
                ))
            
            await conn.executemany("""
                INSERT INTO satellite_orbital_cache (
                    satellite_id, norad_id, constellation, timestamp,
                    position_x, position_y, position_z,
                    latitude, longitude, altitude,
                    velocity_x, velocity_y, velocity_z, orbital_period,
                    elevation_angle, azimuth_angle, range_rate,
                    calculation_method, data_quality
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            """, records)
            
            logger.info(f"✅ 成功存儲 {len(records)} 條緊急衛星數據")
            return True
            
        except Exception as e:
            logger.error(f"❌ 緊急數據存儲失敗: {e}")
            return False
        finally:
            await conn.close()