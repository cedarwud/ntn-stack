"""
歷史軌道生成器 - 基於真實 TLE 數據生成預計算軌道點
用於當 NetStack 預計算數據不可用時的真實數據 fallback
"""

import logging
import json
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from sgp4.earth_gravity import wgs72
from sgp4.io import twoline2rv

# 引入歷史數據
from app.data.historical_tle_data import get_historical_tle_data

logger = logging.getLogger(__name__)


class HistoricalOrbitGenerator:
    """歷史軌道生成器"""
    
    def __init__(self):
        self.earth_radius_km = 6371.0
        
        # 預設觀測位置 (NTPU)
        self.default_observer = {
            "latitude": 24.94417,
            "longitude": 121.37139,
            "altitude": 50.0,  # 公尺
            "name": "NTPU"
        }
    
    async def generate_precomputed_orbit_data(
        self,
        constellation: str = "starlink",
        duration_hours: int = 24,
        time_step_minutes: int = 1,
        observer_location: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        基於歷史 TLE 數據生成預計算軌道數據
        
        Args:
            constellation: 星座名稱
            duration_hours: 計算持續時間 (小時)
            time_step_minutes: 時間步長 (分鐘)
            observer_location: 觀測位置
            
        Returns:
            預計算軌道數據
        """
        try:
            logger.info(f"🛰️ 開始生成 {constellation} 歷史軌道數據...")
            
            # 使用指定或預設觀測位置
            observer = observer_location or self.default_observer
            
            # 獲取歷史 TLE 數據
            historical_data = get_historical_tle_data(constellation)
            if not historical_data:
                raise ValueError(f"無法獲取 {constellation} 歷史數據")
            
            # 計算時間範圍
            start_time = datetime.utcnow()
            end_time = start_time + timedelta(hours=duration_hours)
            time_step_seconds = time_step_minutes * 60
            
            # 生成軌道數據
            satellites_data = {}
            
            # 處理前5顆衛星的數據
            for i, sat_data in enumerate(historical_data[:5]):
                satellite_id = f"sat_{i+1:03d}"
                
                try:
                    orbit_points = await self._calculate_satellite_orbit(
                        sat_data,
                        start_time,
                        end_time,
                        time_step_seconds,
                        observer
                    )
                    
                    satellites_data[satellite_id] = {
                        "satellite_id": satellite_id,
                        "norad_id": sat_data["norad_id"],
                        "satellite_name": sat_data["name"],
                        "tle_line1": sat_data["line1"],
                        "tle_line2": sat_data["line2"],
                        "visibility_data": orbit_points
                    }
                    
                    logger.info(f"✅ 生成 {sat_data['name']} 軌道數據: {len(orbit_points)} 點")
                    
                except Exception as e:
                    logger.warning(f"❌ 生成 {sat_data['name']} 軌道數據失敗: {e}")
                    continue
            
            # 組裝最終數據結構
            result = {
                "generated_at": datetime.utcnow().isoformat(),
                "computation_type": "historical_tle_fallback",
                "observer_location": {
                    "lat": observer["latitude"],
                    "lon": observer["longitude"],
                    "alt": observer["altitude"],
                    "name": observer["name"]
                },
                "constellations": {
                    constellation: {
                        "name": constellation.upper(),
                        "orbit_data": {
                            "metadata": {
                                "start_time": start_time.isoformat(),
                                "duration_minutes": duration_hours * 60,
                                "time_step_seconds": time_step_seconds,
                                "total_time_points": int(duration_hours * 60 / time_step_minutes),
                                "observer_location": {
                                    "lat": observer["latitude"],
                                    "lon": observer["longitude"],
                                    "alt": observer["altitude"],
                                    "name": observer["name"]
                                }
                            },
                            "satellites": satellites_data
                        }
                    }
                }
            }
            
            logger.info(f"🎉 成功生成 {constellation} 歷史軌道數據，包含 {len(satellites_data)} 顆衛星")
            return result
            
        except Exception as e:
            logger.error(f"❌ 歷史軌道數據生成失敗: {e}")
            raise
    
    async def _calculate_satellite_orbit(
        self,
        sat_data: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        time_step_seconds: int,
        observer: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """計算單顆衛星的軌道數據"""
        try:
            # 初始化 SGP4 衛星模型
            satellite = twoline2rv(sat_data["line1"], sat_data["line2"], wgs72)
            
            orbit_points = []
            current_time = start_time
            
            while current_time <= end_time:
                try:
                    # 計算衛星位置
                    position, velocity = satellite.propagate_datetime(current_time)
                    
                    if position and len(position) == 3:
                        # 轉換為地理坐標
                        lat, lon, alt = self._ecf_to_geodetic(position)
                        
                        # 計算觀測角度
                        elevation, azimuth, distance = self._calculate_look_angles(
                            observer["latitude"],
                            observer["longitude"],
                            observer["altitude"] / 1000.0,
                            lat, lon, alt
                        )
                        
                        # 判斷可見性
                        is_visible = elevation > 10.0  # 10度仰角門檻
                        
                        orbit_point = {
                            "timestamp": current_time.isoformat(),
                            "position": {
                                "latitude": lat,
                                "longitude": lon,
                                "altitude": alt * 1000  # 轉換為公尺
                            },
                            "elevation": elevation,
                            "azimuth": azimuth,
                            "distance": distance * 1000,  # 轉換為公尺
                            "is_visible": is_visible
                        }
                        
                        orbit_points.append(orbit_point)
                
                except Exception as e:
                    logger.debug(f"計算時間點 {current_time} 失敗: {e}")
                    continue
                
                current_time += timedelta(seconds=time_step_seconds)
            
            return orbit_points
            
        except Exception as e:
            logger.error(f"計算衛星 {sat_data['name']} 軌道失敗: {e}")
            raise
    
    def _ecf_to_geodetic(self, position: tuple) -> Tuple[float, float, float]:
        """地心固定坐標轉地理坐標"""
        x, y, z = position
        
        # WGS84 參數
        a = 6378137.0  # 長半軸 (米)
        f = 1 / 298.257223563  # 扁率
        e2 = 2 * f - f * f  # 第一偏心率的平方
        
        # 計算經度
        lon = math.atan2(y, x) * 180.0 / math.pi
        
        # 計算緯度（迭代法）
        p = math.sqrt(x * x + y * y)
        lat = math.atan2(z, p * (1 - e2))
        
        for _ in range(5):
            N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
            h = p / math.cos(lat) - N
            lat = math.atan2(z, p * (1 - e2 * N / (N + h)))
        
        # 計算高度
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        alt = p / math.cos(lat) - N
        
        return (
            lat * 180.0 / math.pi,  # 緯度 (度)
            lon,  # 經度 (度)
            alt / 1000.0  # 高度 (公里)
        )
    
    def _calculate_look_angles(
        self,
        obs_lat: float, obs_lon: float, obs_alt: float,
        sat_lat: float, sat_lon: float, sat_alt: float
    ) -> Tuple[float, float, float]:
        """計算衛星的仰角、方位角和距離"""
        # 將度轉換為弧度
        obs_lat_rad = math.radians(obs_lat)
        obs_lon_rad = math.radians(obs_lon)
        sat_lat_rad = math.radians(sat_lat)
        sat_lon_rad = math.radians(sat_lon)
        
        # 地球半徑 (公里)
        R = self.earth_radius_km
        
        # 觀測者位置 (公里)
        obs_x = (R + obs_alt) * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = (R + obs_alt) * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = (R + obs_alt) * math.sin(obs_lat_rad)
        
        # 衛星位置 (公里)
        sat_x = (R + sat_alt) * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = (R + sat_alt) * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = (R + sat_alt) * math.sin(sat_lat_rad)
        
        # 相對位置向量
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # 距離
        range_km = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 本地坐標系轉換
        # 東方向
        east_x = -math.sin(obs_lon_rad)
        east_y = math.cos(obs_lon_rad)
        east_z = 0
        
        # 北方向
        north_x = -math.sin(obs_lat_rad) * math.cos(obs_lon_rad)
        north_y = -math.sin(obs_lat_rad) * math.sin(obs_lon_rad)
        north_z = math.cos(obs_lat_rad)
        
        # 天頂方向
        up_x = math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        up_y = math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        up_z = math.sin(obs_lat_rad)
        
        # 本地坐標
        east = dx * east_x + dy * east_y + dz * east_z
        north = dx * north_x + dy * north_y + dz * north_z
        up = dx * up_x + dy * up_y + dz * up_z
        
        # 仰角和方位角
        elevation = math.degrees(math.atan2(up, math.sqrt(east*east + north*north)))
        azimuth = math.degrees(math.atan2(east, north))
        if azimuth < 0:
            azimuth += 360
        
        return elevation, azimuth, range_km
    
    async def save_precomputed_data_to_file(
        self, 
        data: Dict[str, Any], 
        output_path: str
    ) -> bool:
        """保存預計算數據到文件"""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 預計算數據已保存到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存預計算數據失敗: {e}")
            return False


# 獨立運行時的測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_generate():
        generator = HistoricalOrbitGenerator()
        
        # 生成 Starlink 預計算數據
        data = await generator.generate_precomputed_orbit_data(
            constellation="starlink",
            duration_hours=6,  # 6小時測試數據
            time_step_minutes=5,  # 5分鐘間隔
        )
        
        # 保存到文件
        await generator.save_precomputed_data_to_file(
            data,
            "/tmp/historical_precomputed_orbits.json"
        )
        
        print(f"生成完成！包含 {len(data['constellations']['starlink']['orbit_data']['satellites'])} 顆衛星")
    
    asyncio.run(test_generate())