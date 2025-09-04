#!/usr/bin/env python3
"""
衛星數據預處理模組
負責載入和解析 TLE 數據，為可見性計算準備數據
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import numpy as np

# 添加 netstack 路徑
sys.path.append('/home/sat/ntn-stack/netstack')

@dataclass
class SatelliteData:
    """衛星數據結構"""
    name: str
    tle_line1: str
    tle_line2: str
    constellation: str
    
@dataclass
class ObserverLocation:
    """觀測者位置"""
    name: str
    latitude: float  # degrees
    longitude: float  # degrees
    elevation: float  # meters above sea level
    elevation_threshold: float  # minimum elevation angle in degrees

class TLEDataPreprocessor:
    """TLE 數據預處理器"""
    
    def __init__(self):
        self.base_path = "/home/sat/ntn-stack/netstack/tle_data"
        self.ntpu_location = self._init_ntpu_location()
        
    def _init_ntpu_location(self) -> ObserverLocation:
        """初始化 NTPU 座標"""
        # 24°56'39"N = 24.9442°N
        # 121°22'17"E = 121.3714°E
        return ObserverLocation(
            name="NTPU",
            latitude=24.9442,
            longitude=121.3714,
            elevation=50.0,  # 假設海拔 50 米
            elevation_threshold=10.0  # 使用 10° 仰角門檻（根據文檔標準）
        )
    
    def load_tle_file(self, filepath: str) -> List[SatelliteData]:
        """載入 TLE 文件"""
        satellites = []
        constellation = "starlink" if "starlink" in filepath.lower() else "oneweb"
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # TLE 格式：每 3 行為一組（名稱、TLE Line 1、TLE Line 2）
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                tle_line1 = lines[i + 1].strip()
                tle_line2 = lines[i + 2].strip()
                
                # 驗證 TLE 格式
                if tle_line1.startswith("1 ") and tle_line2.startswith("2 "):
                    satellites.append(SatelliteData(
                        name=name,
                        tle_line1=tle_line1,
                        tle_line2=tle_line2,
                        constellation=constellation
                    ))
        
        return satellites
    
    def load_latest_tle_data(self) -> Dict[str, List[SatelliteData]]:
        """載入最新的 TLE 數據"""
        data = {}
        
        # 載入 Starlink 數據
        starlink_path = os.path.join(self.base_path, "starlink/tle")
        starlink_files = sorted([f for f in os.listdir(starlink_path) if f.endswith('.tle')])
        if starlink_files:
            latest_starlink = os.path.join(starlink_path, starlink_files[-1])
            print(f"載入 Starlink TLE: {starlink_files[-1]}")
            data['starlink'] = self.load_tle_file(latest_starlink)
            print(f"  - 載入 {len(data['starlink'])} 顆 Starlink 衛星")
        
        # 載入 OneWeb 數據
        oneweb_path = os.path.join(self.base_path, "oneweb/tle")
        oneweb_files = sorted([f for f in os.listdir(oneweb_path) if f.endswith('.tle')])
        if oneweb_files:
            latest_oneweb = os.path.join(oneweb_path, oneweb_files[-1])
            print(f"載入 OneWeb TLE: {oneweb_files[-1]}")
            data['oneweb'] = self.load_tle_file(latest_oneweb)
            print(f"  - 載入 {len(data['oneweb'])} 顆 OneWeb 衛星")
        
        return data
    
    def analyze_orbital_periods(self, satellites: List[SatelliteData]) -> Dict:
        """分析軌道週期"""
        from sgp4.api import Satrec
        
        periods = []
        for sat in satellites[:min(100, len(satellites))]:  # 抽樣分析前 100 顆
            satellite = Satrec.twoline2rv(sat.tle_line1, sat.tle_line2)
            
            # 從 TLE 第二行提取平均運動（每天繞地球圈數）
            mean_motion = float(sat.tle_line2[52:63])  # revolutions per day
            period_minutes = 1440.0 / mean_motion  # 1440 = 24 * 60 分鐘
            periods.append(period_minutes)
        
        return {
            'min_period': min(periods),
            'max_period': max(periods),
            'avg_period': np.mean(periods),
            'std_period': np.std(periods)
        }
    
    def get_calculation_parameters(self, orbital_periods: Dict[str, float]) -> Dict:
        """獲取計算參數
        
        Args:
            orbital_periods: 各星座的平均軌道週期（分鐘）
        """
        time_settings = {}
        
        # 為每個星座設定一個完整軌道週期的計算參數
        for constellation, period in orbital_periods.items():
            duration_minutes = int(np.ceil(period))  # 向上取整確保完整週期
            time_settings[constellation] = {
                'orbital_period_minutes': period,
                'duration_minutes': duration_minutes,
                'time_step_seconds': 30,  # 每 30 秒計算一次，提高精度
                'total_points': duration_minutes * 2  # 30秒一個點
            }
        
        return {
            'observer': {
                'name': self.ntpu_location.name,
                'latitude': self.ntpu_location.latitude,
                'longitude': self.ntpu_location.longitude,
                'elevation': self.ntpu_location.elevation,
                'elevation_threshold': self.ntpu_location.elevation_threshold
            },
            'time_settings': time_settings,
            'calculation_date': datetime.utcnow().strftime('%Y-%m-%d')
        }
    
    def save_preprocessed_data(self, data: Dict, orbital_periods: Dict[str, float], 
                              output_dir: str = "/tmp/satellite_data"):
        """保存預處理後的數據"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存 TLE 數據
        for constellation, satellites in data.items():
            output_file = os.path.join(output_dir, f"{constellation}_preprocessed.json")
            sat_list = []
            for sat in satellites:
                sat_list.append({
                    'name': sat.name,
                    'tle_line1': sat.tle_line1,
                    'tle_line2': sat.tle_line2
                })
            
            with open(output_file, 'w') as f:
                json.dump(sat_list, f, indent=2)
            print(f"保存 {constellation} 預處理數據: {output_file}")
        
        # 保存計算參數
        params = self.get_calculation_parameters(orbital_periods)
        params_file = os.path.join(output_dir, "calculation_parameters.json")
        with open(params_file, 'w') as f:
            json.dump(params, f, indent=2)
        print(f"保存計算參數: {params_file}")

def main():
    """主程式"""
    print("=" * 60)
    print("衛星數據預處理")
    print("=" * 60)
    
    preprocessor = TLEDataPreprocessor()
    
    # 步驟 1-2: 載入和解析 TLE 數據
    print("\n1. 載入 TLE 數據...")
    tle_data = preprocessor.load_latest_tle_data()
    
    # 步驟 3: 分析軌道週期
    print("\n2. 分析軌道週期...")
    orbital_periods = {}
    for constellation, satellites in tle_data.items():
        print(f"\n{constellation.upper()} 軌道週期分析:")
        period_stats = preprocessor.analyze_orbital_periods(satellites)
        orbital_periods[constellation] = period_stats['avg_period']
        print(f"  - 最小週期: {period_stats['min_period']:.2f} 分鐘")
        print(f"  - 最大週期: {period_stats['max_period']:.2f} 分鐘")
        print(f"  - 平均週期: {period_stats['avg_period']:.2f} 分鐘")
        print(f"  - 標準差: {period_stats['std_period']:.2f} 分鐘")
    
    # 步驟 4: 設定計算參數
    print("\n3. 計算參數設定:")
    params = preprocessor.get_calculation_parameters(orbital_periods)
    print(f"  - 觀測點: {params['observer']['name']}")
    print(f"  - 座標: {params['observer']['latitude']:.4f}°N, {params['observer']['longitude']:.4f}°E")
    print(f"  - 仰角門檻: {params['observer']['elevation_threshold']}°")
    
    for constellation, settings in params['time_settings'].items():
        print(f"\n  {constellation.upper()} 計算設定:")
        print(f"    - 軌道週期: {settings['orbital_period_minutes']:.2f} 分鐘")
        print(f"    - 計算時長: {settings['duration_minutes']} 分鐘")
        print(f"    - 時間步長: {settings['time_step_seconds']} 秒")
        print(f"    - 總計算點: {settings['total_points']} 個")
    
    # 保存預處理數據
    print("\n4. 保存預處理數據...")
    preprocessor.save_preprocessed_data(tle_data, orbital_periods)
    
    print("\n預處理完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()