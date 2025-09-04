#!/usr/bin/env python3
"""
衛星可見性計算模組
計算指定位置上空的衛星數量統計
"""

import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# 添加 netstack 路徑
sys.path.append('/home/sat/ntn-stack/netstack')

# 導入 SGP4 庫
from sgp4.api import Satrec, jday
from sgp4.conveniences import sat_epoch_datetime

@dataclass
class VisibilityStats:
    """可見性統計結果"""
    constellation: str
    orbital_period_minutes: float
    max_visible: int
    min_visible: int
    avg_visible: float
    std_visible: float
    max_time: str
    min_time: str
    total_satellites: int
    calculation_points: int

class SatelliteVisibilityCalculator:
    """衛星可見性計算器"""
    
    def __init__(self, data_dir: str = "/tmp/satellite_data"):
        self.data_dir = data_dir
        self.params = self._load_parameters()
        self.earth_radius_km = 6371.0
        
    def _load_parameters(self) -> Dict:
        """載入計算參數"""
        params_file = os.path.join(self.data_dir, "calculation_parameters.json")
        with open(params_file, 'r') as f:
            return json.load(f)
    
    def _load_satellite_data(self, constellation: str) -> List[Dict]:
        """載入預處理的衛星數據"""
        data_file = os.path.join(self.data_dir, f"{constellation}_preprocessed.json")
        with open(data_file, 'r') as f:
            return json.load(f)
    
    def _calculate_elevation_angle(self, sat_pos_eci: np.ndarray, obs_lat: float, obs_lon: float, 
                                  obs_alt: float, jd: float, fr: float) -> float:
        """計算衛星相對於觀測者的仰角
        
        Args:
            sat_pos_eci: 衛星在 ECI 坐標系中的位置 (km)
            obs_lat: 觀測者緯度 (degrees)
            obs_lon: 觀測者經度 (degrees)
            obs_alt: 觀測者海拔 (m)
            jd: Julian day
            fr: Fraction of day
            
        Returns:
            仰角 (degrees)，如果衛星在地平線以下則返回負值
        """
        # 轉換觀測者位置到 ECEF
        obs_lat_rad = np.radians(obs_lat)
        obs_lon_rad = np.radians(obs_lon)
        
        # 計算 GMST (Greenwich Mean Sidereal Time)
        tu = (jd - 2451545.0) / 36525.0
        gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0 + fr) + \
               0.000387933 * tu * tu - tu * tu * tu / 38710000.0
        gmst = np.radians(gmst % 360)
        
        # 將 ECI 轉換為 ECEF
        cos_gmst = np.cos(gmst)
        sin_gmst = np.sin(gmst)
        sat_ecef_x = sat_pos_eci[0] * cos_gmst + sat_pos_eci[1] * sin_gmst
        sat_ecef_y = -sat_pos_eci[0] * sin_gmst + sat_pos_eci[1] * cos_gmst
        sat_ecef_z = sat_pos_eci[2]
        
        # 計算觀測者在 ECEF 中的位置
        obs_radius = self.earth_radius_km + obs_alt / 1000.0
        obs_ecef_x = obs_radius * np.cos(obs_lat_rad) * np.cos(obs_lon_rad)
        obs_ecef_y = obs_radius * np.cos(obs_lat_rad) * np.sin(obs_lon_rad)
        obs_ecef_z = obs_radius * np.sin(obs_lat_rad)
        
        # 計算從觀測者到衛星的向量
        range_x = sat_ecef_x - obs_ecef_x
        range_y = sat_ecef_y - obs_ecef_y
        range_z = sat_ecef_z - obs_ecef_z
        range_mag = np.sqrt(range_x**2 + range_y**2 + range_z**2)
        
        # 轉換到局部水平坐標系 (ENU - East North Up)
        sin_lat = np.sin(obs_lat_rad)
        cos_lat = np.cos(obs_lat_rad)
        sin_lon = np.sin(obs_lon_rad)
        cos_lon = np.cos(obs_lon_rad)
        
        east = -sin_lon * range_x + cos_lon * range_y
        north = -sin_lat * cos_lon * range_x - sin_lat * sin_lon * range_y + cos_lat * range_z
        up = cos_lat * cos_lon * range_x + cos_lat * sin_lon * range_y + sin_lat * range_z
        
        # 計算仰角
        horizontal_range = np.sqrt(east**2 + north**2)
        elevation_rad = np.arctan2(up, horizontal_range)
        elevation_deg = np.degrees(elevation_rad)
        
        return elevation_deg
    
    def calculate_visibility_for_constellation(self, constellation: str) -> VisibilityStats:
        """計算單一星座的可見性統計"""
        
        print(f"\n開始計算 {constellation.upper()} 可見性...")
        
        # 載入衛星數據
        satellites_data = self._load_satellite_data(constellation)
        total_sats = len(satellites_data)
        print(f"  載入 {total_sats} 顆衛星")
        
        # 創建 SGP4 衛星對象
        satellites = []
        for sat_data in satellites_data:
            try:
                satellite = Satrec.twoline2rv(sat_data['tle_line1'], sat_data['tle_line2'])
                satellites.append((sat_data['name'], satellite))
            except:
                continue
        
        # 獲取觀測者位置和時間設定
        observer = self.params['observer']
        time_settings = self.params['time_settings'][constellation]
        
        # 生成時間序列
        start_time = datetime.utcnow()
        time_points = []
        for i in range(time_settings['total_points']):
            time_offset = i * time_settings['time_step_seconds'] / 60.0  # 轉換為分鐘
            time_points.append(start_time + timedelta(minutes=time_offset))
        
        # 計算每個時間點的可見衛星數
        visible_counts = []
        max_visible = 0
        min_visible = total_sats
        max_time = None
        min_time = None
        
        print(f"  計算 {len(time_points)} 個時間點...")
        
        for idx, current_time in enumerate(time_points):
            # 計算 Julian date
            jd, fr = jday(current_time.year, current_time.month, current_time.day,
                         current_time.hour, current_time.minute, 
                         current_time.second + current_time.microsecond / 1e6)
            
            visible_count = 0
            
            # 檢查每顆衛星的可見性
            for sat_name, satellite in satellites:
                # 計算衛星位置
                e, r, v = satellite.sgp4(jd, fr)
                
                if e == 0:  # 成功計算位置
                    # 計算仰角
                    elevation = self._calculate_elevation_angle(
                        r, observer['latitude'], observer['longitude'],
                        observer['elevation'], jd, fr
                    )
                    
                    # 檢查是否高於仰角門檻
                    if elevation >= observer['elevation_threshold']:
                        visible_count += 1
            
            visible_counts.append(visible_count)
            
            # 更新最大最小值
            if visible_count > max_visible:
                max_visible = visible_count
                max_time = current_time
            if visible_count < min_visible:
                min_visible = visible_count
                min_time = current_time
            
            # 進度顯示
            if (idx + 1) % 50 == 0:
                print(f"    已完成 {idx + 1}/{len(time_points)} 個時間點")
        
        # 計算統計數據
        avg_visible = np.mean(visible_counts)
        std_visible = np.std(visible_counts)
        
        return VisibilityStats(
            constellation=constellation,
            orbital_period_minutes=time_settings['orbital_period_minutes'],
            max_visible=max_visible,
            min_visible=min_visible,
            avg_visible=avg_visible,
            std_visible=std_visible,
            max_time=max_time.strftime('%Y-%m-%d %H:%M:%S UTC') if max_time else '',
            min_time=min_time.strftime('%Y-%m-%d %H:%M:%S UTC') if min_time else '',
            total_satellites=total_sats,
            calculation_points=len(time_points)
        )
    
    def generate_report(self, stats_list: List[VisibilityStats]):
        """生成統計報告"""
        
        print("\n" + "=" * 70)
        print("衛星可見性統計報告")
        print("=" * 70)
        print(f"\n觀測位置: {self.params['observer']['name']}")
        print(f"座標: {self.params['observer']['latitude']:.4f}°N, {self.params['observer']['longitude']:.4f}°E")
        print(f"仰角門檻: {self.params['observer']['elevation_threshold']}°")
        print(f"計算日期: {self.params['calculation_date']}")
        
        for stats in stats_list:
            print(f"\n{'='*35} {stats.constellation.upper()} {'='*35}")
            print(f"總衛星數量: {stats.total_satellites} 顆")
            print(f"軌道週期: {stats.orbital_period_minutes:.2f} 分鐘")
            print(f"計算點數: {stats.calculation_points} 個")
            print(f"\n可見衛星數量統計:")
            print(f"  最多: {stats.max_visible} 顆 (時間: {stats.max_time})")
            print(f"  最少: {stats.min_visible} 顆 (時間: {stats.min_time})")
            print(f"  平均: {stats.avg_visible:.2f} 顆")
            print(f"  標準差: {stats.std_visible:.2f}")
            print(f"  可見率: {stats.avg_visible/stats.total_satellites*100:.2f}%")
        
        # 保存報告
        report_file = os.path.join(self.data_dir, "visibility_report.json")
        report_data = []
        for stats in stats_list:
            report_data.append({
                'constellation': stats.constellation,
                'total_satellites': stats.total_satellites,
                'orbital_period_minutes': stats.orbital_period_minutes,
                'max_visible': stats.max_visible,
                'min_visible': stats.min_visible,
                'avg_visible': stats.avg_visible,
                'std_visible': stats.std_visible,
                'max_time': stats.max_time,
                'min_time': stats.min_time,
                'visibility_rate': stats.avg_visible/stats.total_satellites*100
            })
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\n報告已保存至: {report_file}")

def main():
    """主程式"""
    print("=" * 60)
    print("衛星可見性計算")
    print("=" * 60)
    
    calculator = SatelliteVisibilityCalculator()
    stats_list = []
    
    # 計算每個星座的可見性
    for constellation in ['starlink', 'oneweb']:
        try:
            stats = calculator.calculate_visibility_for_constellation(constellation)
            stats_list.append(stats)
        except Exception as e:
            print(f"計算 {constellation} 時發生錯誤: {e}")
    
    # 生成報告
    if stats_list:
        calculator.generate_report(stats_list)
    
    print("\n計算完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()