# 🛰️ F1: TLE數據載入引擎
"""
TLE Loader Engine - 全量8,735顆衛星處理
功能: 載入、驗證、SGP4計算完整TLE數據集
目標: 支援Starlink ~5,000顆 + OneWeb ~800顆 + 其他星座
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import math

from skyfield.api import Loader, EarthSatellite
from skyfield.timelib import Time
import numpy as np

@dataclass
class SatelliteData:
    """衛星數據結構"""
    satellite_id: str
    name: str
    constellation: str
    norad_id: int
    tle_line1: str
    tle_line2: str
    epoch: datetime
    
    # 軌道參數 (從TLE解析)
    inclination_deg: float
    eccentricity: float
    argument_of_perigee_deg: float
    raan_deg: float  # 升交點赤經
    mean_anomaly_deg: float
    mean_motion_revs_per_day: float
    
    # 計算參數
    orbital_period_minutes: float
    apogee_km: float
    perigee_km: float

@dataclass
class OrbitPosition:
    """軌道位置數據"""
    timestamp: datetime
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_per_s: float
    
    # NTPU觀測點相關
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    is_visible: bool

class TLELoaderEngine:
    """TLE載入引擎 - 處理全量衛星數據"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # NTPU觀測點座標
        self.observer_lat = 24.9441667  # NTPU緯度
        self.observer_lon = 121.3713889  # NTPU經度
        self.observer_alt_km = 0.05  # NTPU海拔50米
        
        # Skyfield載入器
        self.skyfield_loader = Loader('/tmp/skyfield_data')
        self.earth = None
        self.timescale = None
        
        # 數據統計
        self.load_statistics = {
            'total_satellites': 0,
            'starlink_count': 0,
            'oneweb_count': 0,
            'other_constellation_count': 0,
            'successful_calculations': 0,
            'failed_calculations': 0
        }
    
    async def initialize(self):
        """初始化Skyfield組件"""
        try:
            self.earth = self.skyfield_loader('de421.bsp')['earth']
            self.timescale = self.skyfield_loader.timescale()
            self.logger.info("✅ TLE載入引擎初始化完成")
        except Exception as e:
            self.logger.error(f"❌ TLE載入引擎初始化失敗: {e}")
            raise
    
    async def load_full_satellite_data(self) -> Dict[str, List[SatelliteData]]:
        """載入8,735顆衛星的完整TLE數據"""
        self.logger.info("🚀 開始載入全量衛星TLE數據...")
        
        satellite_data = {
            'starlink': [],
            'oneweb': [],
            'other_constellations': []
        }
        
        try:
            # 1. 載入Starlink TLE數據 (~5,000顆)
            starlink_data = await self._load_starlink_tle_data()
            satellite_data['starlink'] = starlink_data
            self.load_statistics['starlink_count'] = len(starlink_data)
            
            # 2. 載入OneWeb TLE數據 (~800顆)
            oneweb_data = await self._load_oneweb_tle_data()
            satellite_data['oneweb'] = oneweb_data
            self.load_statistics['oneweb_count'] = len(oneweb_data)
            
            # 3. 載入其他星座數據 (其餘~2,935顆)
            other_data = await self._load_other_constellation_data()
            satellite_data['other_constellations'] = other_data
            self.load_statistics['other_constellation_count'] = len(other_data)
            
            total_count = (self.load_statistics['starlink_count'] + 
                          self.load_statistics['oneweb_count'] + 
                          self.load_statistics['other_constellation_count'])
            
            self.load_statistics['total_satellites'] = total_count
            
            self.logger.info(f"✅ TLE數據載入完成:")
            self.logger.info(f"   Starlink: {self.load_statistics['starlink_count']} 顆")
            self.logger.info(f"   OneWeb: {self.load_statistics['oneweb_count']} 顆")
            self.logger.info(f"   其他星座: {self.load_statistics['other_constellation_count']} 顆")
            self.logger.info(f"   總計: {total_count} 顆")
            
            return satellite_data
            
        except Exception as e:
            self.logger.error(f"❌ TLE數據載入失敗: {e}")
            raise
    
    async def calculate_orbital_positions(self, 
                                        satellites: List[SatelliteData], 
                                        time_range_minutes: int = 200) -> Dict[str, List[OrbitPosition]]:
        """使用SGP4計算200個時間點的軌道位置"""
        self.logger.info(f"🧮 開始計算 {len(satellites)} 顆衛星的軌道位置 ({time_range_minutes}分鐘)")
        
        orbital_positions = {}
        
        # 生成時間點 (30秒間隔)
        start_time = datetime.now(timezone.utc)
        time_points = []
        for i in range(0, time_range_minutes * 60, 30):  # 30秒間隔
            time_points.append(start_time + timedelta(seconds=i))
        
        self.logger.info(f"📊 時間點數量: {len(time_points)} (30秒間隔)")
        
        for satellite in satellites:
            try:
                positions = await self._calculate_satellite_orbit(satellite, time_points)
                orbital_positions[satellite.satellite_id] = positions
                self.load_statistics['successful_calculations'] += 1
                
                # 每100顆衛星記錄進度
                if self.load_statistics['successful_calculations'] % 100 == 0:
                    self.logger.info(f"🔄 已計算 {self.load_statistics['successful_calculations']} 顆衛星軌道")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 衛星 {satellite.satellite_id} 軌道計算失敗: {e}")
                self.load_statistics['failed_calculations'] += 1
                continue
        
        success_rate = (self.load_statistics['successful_calculations'] / 
                       (self.load_statistics['successful_calculations'] + self.load_statistics['failed_calculations']) * 100)
        
        self.logger.info(f"✅ 軌道計算完成:")
        self.logger.info(f"   成功: {self.load_statistics['successful_calculations']} 顆")
        self.logger.info(f"   失敗: {self.load_statistics['failed_calculations']} 顆")
        self.logger.info(f"   成功率: {success_rate:.1f}%")
        
        return orbital_positions
    
    async def _load_starlink_tle_data(self) -> List[SatelliteData]:
        """載入Starlink TLE數據"""
        # 實際應從CelesTrak或本地TLE文件載入
        # 這裡提供框架結構
        starlink_satellites = []
        
        # TODO: 實現從實際TLE源載入Starlink數據
        # 來源: https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink
        
        self.logger.info("📡 載入Starlink TLE數據...")
        return starlink_satellites
    
    async def _load_oneweb_tle_data(self) -> List[SatelliteData]:
        """載入OneWeb TLE數據"""
        oneweb_satellites = []
        
        # TODO: 實現從實際TLE源載入OneWeb數據
        # 來源: https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb
        
        self.logger.info("📡 載入OneWeb TLE數據...")
        return oneweb_satellites
    
    async def _load_other_constellation_data(self) -> List[SatelliteData]:
        """載入其他星座數據"""
        other_satellites = []
        
        # TODO: 載入其他LEO星座 (如Amazon Kuiper, GlobalStar等)
        
        self.logger.info("📡 載入其他星座TLE數據...")
        return other_satellites
    
    async def _calculate_satellite_orbit(self, 
                                       satellite: SatelliteData, 
                                       time_points: List[datetime]) -> List[OrbitPosition]:
        """計算單顆衛星的軌道位置"""
        
        # 創建Skyfield衛星對象
        sat = EarthSatellite(satellite.tle_line1, satellite.tle_line2, 
                           satellite.name, self.timescale)
        
        # 創建NTPU觀測點
        ntpu_observer = self.earth + (
            satellite.name, 
            self.observer_lat, 
            self.observer_lon,
            self.observer_alt_km
        )
        
        positions = []
        
        for timestamp in time_points:
            try:
                # 轉換為Skyfield時間
                skyfield_time = self.timescale.from_datetime(timestamp)
                
                # 計算地心座標
                geocentric = sat.at(skyfield_time)
                lat, lon = geocentric.subpoint().latitude.degrees, geocentric.subpoint().longitude.degrees
                altitude = geocentric.subpoint().elevation.km
                
                # 計算速度
                velocity = np.linalg.norm(geocentric.velocity.km_per_s)
                
                # 計算相對NTPU觀測點的位置
                observer_sat = (sat - ntpu_observer).at(skyfield_time)
                elevation, azimuth, distance = observer_sat.altaz()
                
                # 判斷可見性 (根據星座設定不同仰角閾值)
                elevation_threshold = self._get_elevation_threshold(satellite.constellation)
                is_visible = elevation.degrees >= elevation_threshold
                
                position = OrbitPosition(
                    timestamp=timestamp,
                    latitude=lat,
                    longitude=lon,
                    altitude_km=altitude,
                    velocity_km_per_s=velocity,
                    elevation_deg=elevation.degrees,
                    azimuth_deg=azimuth.degrees,
                    distance_km=distance.km,
                    is_visible=is_visible
                )
                
                positions.append(position)
                
            except Exception as e:
                self.logger.warning(f"⚠️ 時間點 {timestamp} 計算失敗: {e}")
                continue
        
        return positions
    
    def _get_elevation_threshold(self, constellation: str) -> float:
        """獲取星座特定的仰角閾值"""
        thresholds = {
            'starlink': 5.0,   # Starlink使用5度仰角閾值
            'oneweb': 10.0,    # OneWeb使用10度仰角閾值
            'default': 10.0    # 其他星座預設10度
        }
        return thresholds.get(constellation.lower(), thresholds['default'])
    
    def _parse_tle_parameters(self, line1: str, line2: str) -> Dict:
        """解析TLE參數"""
        try:
            # TLE Line 1: 1 NNNNNC NNNNNAAA NNNNN.NNNNNNNN +.NNNNNNNN +NNNNN-N +NNNNN-N N NNNNN
            # TLE Line 2: 2 NNNNN NNN.NNNN NNN.NNNN NNNNNNN NNN.NNNN NNN.NNNN NN.NNNNNNNNNNNNNN
            
            # 從Line 2解析軌道參數
            inclination = float(line2[8:16])  # 軌道傾角
            raan = float(line2[17:25])        # 升交點赤經
            eccentricity = float('0.' + line2[26:33])  # 軌道偏心率
            arg_perigee = float(line2[34:42])  # 近地點幅角
            mean_anomaly = float(line2[43:51])  # 平近點角
            mean_motion = float(line2[52:63])   # 平均運動 (圈/天)
            
            # 計算軌道週期
            orbital_period_minutes = (24 * 60) / mean_motion
            
            # 計算軌道高度 (簡化計算)
            mu = 398600.4418  # 地球重力參數 km³/s²
            n = mean_motion * 2 * math.pi / (24 * 3600)  # 平均運動 rad/s
            a = (mu / (n**2))**(1/3)  # 半長軸 km
            
            perigee = a * (1 - eccentricity) - 6371  # 近地點高度
            apogee = a * (1 + eccentricity) - 6371   # 遠地點高度
            
            return {
                'inclination_deg': inclination,
                'eccentricity': eccentricity,
                'argument_of_perigee_deg': arg_perigee,
                'raan_deg': raan,
                'mean_anomaly_deg': mean_anomaly,
                'mean_motion_revs_per_day': mean_motion,
                'orbital_period_minutes': orbital_period_minutes,
                'perigee_km': perigee,
                'apogee_km': apogee
            }
            
        except Exception as e:
            self.logger.warning(f"⚠️ TLE參數解析失敗: {e}")
            return {}
    
    async def export_load_statistics(self, output_path: str):
        """匯出載入統計數據"""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.load_statistics, f, indent=2)
            self.logger.info(f"📊 載入統計已匯出至: {output_path}")
        except Exception as e:
            self.logger.error(f"❌ 載入統計匯出失敗: {e}")

# 使用範例
async def main():
    """F1_TLE_Loader使用範例"""
    
    config = {
        'data_sources': {
            'starlink_tle_url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink',
            'oneweb_tle_url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb'
        },
        'calculation_params': {
            'time_range_minutes': 200,
            'time_resolution_seconds': 30
        }
    }
    
    # 初始化TLE載入引擎
    tle_loader = TLELoaderEngine(config)
    await tle_loader.initialize()
    
    # 載入全量衛星數據
    satellite_data = await tle_loader.load_full_satellite_data()
    
    # 計算軌道位置 (選擇前100顆進行測試)
    test_satellites = satellite_data['starlink'][:100]
    orbital_positions = await tle_loader.calculate_orbital_positions(test_satellites)
    
    # 匯出統計數據
    await tle_loader.export_load_statistics('/tmp/f1_load_statistics.json')
    
    print(f"✅ F1_TLE_Loader測試完成")
    print(f"   載入衛星總數: {tle_loader.load_statistics['total_satellites']}")
    print(f"   軌道計算成功: {tle_loader.load_statistics['successful_calculations']}")

if __name__ == "__main__":
    asyncio.run(main())