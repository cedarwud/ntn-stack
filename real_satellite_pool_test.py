#!/usr/bin/env python3
"""
真實衛星池測試
使用本地TLE數據，測試NTPU觀測點在96分鐘軌道週期內的真實可見衛星數量
計算需要多少顆衛星來維持穩定的同時可見數量
"""

import re
import json
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from math import radians, degrees, sin, cos, sqrt, atan2, asin, pi
from dataclasses import dataclass

@dataclass
class TLEData:
    """TLE數據結構"""
    name: str
    line1: str
    line2: str
    norad_id: int
    
    @classmethod
    def parse_tle_file(cls, file_path: str) -> List['TLEData']:
        """解析TLE文件"""
        satellites = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # 每3行一組TLE數據
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i]
                    line1 = lines[i + 1]
                    line2 = lines[i + 2]
                    
                    # 提取NORAD ID
                    norad_id = int(line1[2:7])
                    
                    satellites.append(cls(name, line1, line2, norad_id))
            
            print(f"✅ 載入 {len(satellites)} 顆衛星的TLE數據")
            return satellites
            
        except Exception as e:
            print(f"❌ 載入TLE文件失敗: {e}")
            return []

class SGP4Calculator:
    """簡化的SGP4軌道計算器"""
    
    def __init__(self):
        self.earth_radius_km = 6371.0
        self.mu = 398600.4418  # Earth gravitational parameter
    
    def parse_tle_elements(self, tle: TLEData) -> Dict:
        """解析TLE軌道要素"""
        line1 = tle.line1
        line2 = tle.line2
        
        # 從TLE第2行提取軌道要素
        inclination = float(line2[8:16])      # 傾角 (度)
        raan = float(line2[17:25])            # 升交點赤經 (度)
        eccentricity = float("0." + line2[26:33])  # 偏心率
        arg_perigee = float(line2[34:42])     # 近地點幅角 (度)
        mean_anomaly = float(line2[43:51])    # 平近點角 (度)
        mean_motion = float(line2[52:63])     # 平均運動 (轉/日)
        
        return {
            'inclination': inclination,
            'raan': raan,
            'eccentricity': eccentricity,
            'arg_perigee': arg_perigee,
            'mean_anomaly': mean_anomaly,
            'mean_motion': mean_motion
        }
    
    def calculate_position(self, tle: TLEData, target_time: datetime) -> Tuple[float, float, float]:
        """計算衛星在指定時間的地理位置 (簡化計算)"""
        elements = self.parse_tle_elements(tle)
        
        # TLE epoch (第1行第18-32字符)
        epoch_year = int(tle.line1[18:20])
        if epoch_year < 57:
            epoch_year += 2000
        else:
            epoch_year += 1900
        
        epoch_day = float(tle.line1[20:32])
        
        # 計算epoch時間
        epoch_datetime = datetime(epoch_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)
        
        # 時間差 (分鐘)
        time_diff = (target_time - epoch_datetime).total_seconds() / 60.0
        
        # 簡化的軌道傳播
        mean_motion_rad_per_min = elements['mean_motion'] * 2 * pi / (24 * 60)
        
        # 更新平近點角
        mean_anomaly = elements['mean_anomaly'] + mean_motion_rad_per_min * time_diff * 180 / pi
        mean_anomaly = mean_anomaly % 360
        
        # 簡化：假設圓軌道 (eccentricity ≈ 0)
        true_anomaly = mean_anomaly
        
        # 軌道半長軸 (從平均運動計算)
        period_min = 24 * 60 / elements['mean_motion']
        semi_major_axis = ((period_min * 60) ** 2 * self.mu / (4 * pi ** 2)) ** (1/3)
        
        # 軌道座標轉地理座標 (簡化)
        orbit_angle = radians(true_anomaly + elements['arg_perigee'])
        inclination_rad = radians(elements['inclination'])
        raan_rad = radians(elements['raan'] + time_diff * 0.25)  # 地球自轉修正
        
        # 軌道平面內的位置
        x_orbit = semi_major_axis * cos(orbit_angle)
        y_orbit = semi_major_axis * sin(orbit_angle)
        
        # 轉換到地心座標系
        x_earth = x_orbit * cos(raan_rad) - y_orbit * cos(inclination_rad) * sin(raan_rad)
        y_earth = x_orbit * sin(raan_rad) + y_orbit * cos(inclination_rad) * cos(raan_rad)
        z_earth = y_orbit * sin(inclination_rad)
        
        # 轉換為地理座標
        longitude = degrees(atan2(y_earth, x_earth))
        latitude = degrees(asin(z_earth / sqrt(x_earth**2 + y_earth**2 + z_earth**2)))
        altitude = sqrt(x_earth**2 + y_earth**2 + z_earth**2) - self.earth_radius_km
        
        return latitude, longitude, altitude

class VisibilityCalculator:
    """衛星可見性計算器"""
    
    def __init__(self, observer_lat: float, observer_lon: float, observer_alt: float = 0):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.observer_alt = observer_alt
        self.earth_radius = 6371.0
    
    def calculate_elevation_azimuth(self, sat_lat: float, sat_lon: float, sat_alt: float) -> Tuple[float, float]:
        """計算衛星的仰角和方位角"""
        # 轉換為弧度
        obs_lat_rad = radians(self.observer_lat)
        obs_lon_rad = radians(self.observer_lon)
        sat_lat_rad = radians(sat_lat)
        sat_lon_rad = radians(sat_lon)
        
        # 計算地心角距離
        delta_lat = sat_lat_rad - obs_lat_rad
        delta_lon = sat_lon_rad - obs_lon_rad
        
        angular_distance = 2 * asin(sqrt(
            sin(delta_lat/2)**2 + 
            cos(obs_lat_rad) * cos(sat_lat_rad) * sin(delta_lon/2)**2
        ))
        
        # 計算仰角
        ground_distance = angular_distance * self.earth_radius
        height_diff = sat_alt
        
        # 使用幾何關係計算仰角
        if ground_distance > 0:
            elevation_rad = atan2(height_diff, ground_distance) - asin(self.earth_radius / (self.earth_radius + sat_alt))
            elevation = max(-90, degrees(elevation_rad))
        else:
            elevation = 90
        
        # 計算方位角
        azimuth_rad = atan2(
            sin(delta_lon) * cos(sat_lat_rad),
            cos(obs_lat_rad) * sin(sat_lat_rad) - sin(obs_lat_rad) * cos(sat_lat_rad) * cos(delta_lon)
        )
        azimuth = (degrees(azimuth_rad) + 360) % 360
        
        return elevation, azimuth

class SatellitePoolTester:
    """衛星池測試器"""
    
    def __init__(self):
        self.ntpu_lat = 24.9441667
        self.ntpu_lon = 121.3713889
        self.ntpu_alt = 100
        
        self.sgp4_calc = SGP4Calculator()
        self.vis_calc = VisibilityCalculator(self.ntpu_lat, self.ntpu_lon, self.ntpu_alt)
        
        # 仰角門檻
        self.elevation_thresholds = {
            "starlink": 5.0,
            "oneweb": 10.0
        }
    
    def load_tle_data(self) -> Dict[str, List[TLEData]]:
        """載入本地TLE數據"""
        tle_data = {}
        
        # 載入Starlink數據
        starlink_file = "/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_20250816.tle"
        starlink_sats = TLEData.parse_tle_file(starlink_file)
        if starlink_sats:
            tle_data["starlink"] = starlink_sats
            print(f"📡 Starlink: {len(starlink_sats)} 顆衛星")
        
        # 載入OneWeb數據
        oneweb_file = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_20250816.tle"
        oneweb_sats = TLEData.parse_tle_file(oneweb_file)
        if oneweb_sats:
            tle_data["oneweb"] = oneweb_sats
            print(f"📡 OneWeb: {len(oneweb_sats)} 顆衛星")
        
        total_sats = sum(len(sats) for sats in tle_data.values())
        print(f"🛰️ 總計: {total_sats} 顆衛星")
        
        return tle_data
    
    def test_visibility_at_time(self, tle_data: Dict[str, List[TLEData]], test_time: datetime) -> Dict:
        """測試指定時間的可見性"""
        results = {
            "timestamp": test_time.isoformat(),
            "visible_satellites": {"starlink": [], "oneweb": []},
            "counts": {"starlink": 0, "oneweb": 0, "total": 0}
        }
        
        for constellation, satellites in tle_data.items():
            threshold = self.elevation_thresholds.get(constellation, 5.0)
            visible_count = 0
            
            for satellite in satellites:
                try:
                    # 計算衛星位置
                    sat_lat, sat_lon, sat_alt = self.sgp4_calc.calculate_position(satellite, test_time)
                    
                    # 計算可見性
                    elevation, azimuth = self.vis_calc.calculate_elevation_azimuth(sat_lat, sat_lon, sat_alt)
                    
                    # 檢查是否可見
                    if elevation >= threshold:
                        results["visible_satellites"][constellation].append({
                            "name": satellite.name,
                            "norad_id": satellite.norad_id,
                            "elevation": elevation,
                            "azimuth": azimuth,
                            "latitude": sat_lat,
                            "longitude": sat_lon,
                            "altitude": sat_alt
                        })
                        visible_count += 1
                
                except Exception as e:
                    # 單顆衛星計算失敗不影響整體
                    continue
            
            results["counts"][constellation] = visible_count
            results["counts"]["total"] += visible_count
        
        return results
    
    def run_orbit_cycle_test(self, duration_minutes: int = 96, interval_minutes: int = 2) -> Dict:
        """執行完整軌道週期測試"""
        print("🚀 開始真實衛星池測試")
        print(f"📍 觀測點: NTPU ({self.ntpu_lat}°N, {self.ntpu_lon}°E)")
        print(f"⏱️ 測試週期: {duration_minutes} 分鐘")
        print(f"📊 測試間隔: {interval_minutes} 分鐘")
        
        # 載入TLE數據
        tle_data = self.load_tle_data()
        if not tle_data:
            return {"error": "無法載入TLE數據"}
        
        # 設定測試時間範圍 (使用TLE數據的時間)
        start_time = datetime(2025, 8, 16, 12, 0, 0, tzinfo=timezone.utc)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        print(f"⏰ 測試時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"⏰ 結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        
        # 生成測試時間點
        test_times = []
        current_time = start_time
        while current_time <= end_time:
            test_times.append(current_time)
            current_time += timedelta(minutes=interval_minutes)
        
        print(f"📊 測試點數: {len(test_times)} 個時間點")
        
        # 執行可見性測試
        all_results = []
        starlink_counts = []
        oneweb_counts = []
        total_counts = []
        
        for i, test_time in enumerate(test_times):
            print(f"🔍 進度: {i+1}/{len(test_times)} ({(i+1)/len(test_times)*100:.1f}%) - {test_time.strftime('%H:%M')}")
            
            result = self.test_visibility_at_time(tle_data, test_time)
            all_results.append(result)
            
            starlink_counts.append(result["counts"]["starlink"])
            oneweb_counts.append(result["counts"]["oneweb"])
            total_counts.append(result["counts"]["total"])
            
            # 每10個點顯示一次結果
            if i % 10 == 0:
                print(f"   可見: Starlink {result['counts']['starlink']} + OneWeb {result['counts']['oneweb']} = 總計 {result['counts']['total']} 顆")
        
        # 計算統計數據
        if total_counts:
            statistics_data = {
                "starlink": {
                    "mean": statistics.mean(starlink_counts),
                    "median": statistics.median(starlink_counts),
                    "min": min(starlink_counts),
                    "max": max(starlink_counts),
                    "std_dev": statistics.stdev(starlink_counts) if len(starlink_counts) > 1 else 0
                },
                "oneweb": {
                    "mean": statistics.mean(oneweb_counts),
                    "median": statistics.median(oneweb_counts),
                    "min": min(oneweb_counts),
                    "max": max(oneweb_counts),
                    "std_dev": statistics.stdev(oneweb_counts) if len(oneweb_counts) > 1 else 0
                },
                "total": {
                    "mean": statistics.mean(total_counts),
                    "median": statistics.median(total_counts),
                    "min": min(total_counts),
                    "max": max(total_counts),
                    "std_dev": statistics.stdev(total_counts) if len(total_counts) > 1 else 0
                }
            }
        else:
            statistics_data = {"error": "無有效數據"}
        
        # 組裝最終結果
        final_results = {
            "test_config": {
                "observer_location": {"lat": self.ntpu_lat, "lon": self.ntpu_lon, "alt": self.ntpu_alt},
                "elevation_thresholds": self.elevation_thresholds,
                "duration_minutes": duration_minutes,
                "interval_minutes": interval_minutes,
                "total_satellites": sum(len(sats) for sats in tle_data.values())
            },
            "timeline_results": all_results,
            "statistics": statistics_data
        }
        
        return final_results

def print_test_summary(results: Dict):
    """打印測試結果摘要"""
    print("\n" + "="*60)
    print("🎯 真實衛星池測試結果")
    print("="*60)
    
    if "error" in results:
        print(f"❌ 測試失敗: {results['error']}")
        return
    
    config = results["test_config"]
    stats = results["statistics"]
    
    print(f"📍 觀測點: NTPU ({config['observer_location']['lat']}°N, {config['observer_location']['lon']}°E)")
    print(f"🛰️ 總衛星數: {config['total_satellites']} 顆")
    print(f"⏱️ 測試週期: {config['duration_minutes']} 分鐘")
    
    print("\n🎯 仰角門檻:")
    for constellation, threshold in config["elevation_thresholds"].items():
        print(f"   {constellation.upper()}: {threshold}°")
    
    if "error" not in stats:
        print("\n📊 平均同時可見衛星數量:")
        print(f"   Starlink (5°): {stats['starlink']['mean']:.1f} 顆 (範圍: {stats['starlink']['min']}-{stats['starlink']['max']})")
        print(f"   OneWeb (10°): {stats['oneweb']['mean']:.1f} 顆 (範圍: {stats['oneweb']['min']}-{stats['oneweb']['max']})")
        print(f"   總計: {stats['total']['mean']:.1f} 顆 (範圍: {stats['total']['min']}-{stats['total']['max']})")
        
        print("\n🎯 關鍵結論:")
        total_mean = stats['total']['mean']
        print(f"   在 {config['total_satellites']} 顆衛星中，")
        print(f"   NTPU觀測點平均同時可見 {total_mean:.0f} 顆衛星")
        
        # 衛星池規劃建議
        coverage_multiplier = config['total_satellites'] / total_mean if total_mean > 0 else 0
        print(f"   衛星池倍數: {coverage_multiplier:.0f}x")
        
        # 基於結果給出建議
        if total_mean >= 15 and total_mean <= 30:
            print(f"   ✅ 這個結果合理，符合LEO衛星網絡設計預期")
            suggested_pool = int(total_mean * 20)  # 20倍備用係數
            print(f"   💡 建議動態池大小: {suggested_pool} 顆 (20倍備用係數)")
        else:
            print(f"   ⚠️ 結果需要進一步驗證")
    
    print("="*60)

def main():
    """主函數"""
    tester = SatellitePoolTester()
    
    try:
        # 執行96分鐘軌道週期測試
        results = tester.run_orbit_cycle_test(duration_minutes=96, interval_minutes=2)
        
        # 保存詳細結果
        output_file = "/home/sat/ntn-stack/real_satellite_pool_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 詳細結果已保存到: {output_file}")
        
        # 打印摘要
        print_test_summary(results)
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()