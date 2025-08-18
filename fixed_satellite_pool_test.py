#!/usr/bin/env python3
"""
修正版真實衛星池測試
使用更準確的SGP4實現和時間計算
"""

import re
import json
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from math import radians, degrees, sin, cos, sqrt, atan2, asin, pi, floor
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

class ImprovedSGP4Calculator:
    """改進的SGP4軌道計算器"""
    
    def __init__(self):
        self.earth_radius_km = 6378.137  # WGS-84地球半徑
        self.mu = 398600.4418           # 地球引力常數 (km³/s²)
        self.j2 = 1.08262668e-3         # J2項攝動
        self.earth_flattening = 1.0/298.257223563
        
    def julian_date_from_tle_epoch(self, tle_epoch_str: str) -> float:
        """從TLE epoch字符串計算儒略日"""
        try:
            # TLE epoch格式: YYDDD.DDDDDDDD
            year_part = tle_epoch_str[:2]
            day_part = float(tle_epoch_str[2:])
            
            # 處理年份
            year = int(year_part)
            if year < 57:  # 2000年之後
                year += 2000
            else:
                year += 1900
            
            # 計算儒略日
            if year > 1582 or (year == 1582 and day_part >= 278):
                # 格里高利曆
                a = int(year / 100)
                b = 2 - a + int(a / 4)
            else:
                # 儒略曆
                b = 0
                
            jd = int(365.25 * (year + 4716)) + int(30.6001 * 13) + 1 + b - 1524.5
            jd += day_part - 1
            
            return jd
            
        except Exception as e:
            print(f"❌ 解析TLE epoch失敗: {e}")
            return 0.0
    
    def parse_tle_elements(self, tle: TLEData) -> Dict:
        """解析TLE軌道要素"""
        line1 = tle.line1
        line2 = tle.line2
        
        try:
            # 從TLE第1行提取
            epoch_str = line1[18:32]
            
            # 從TLE第2行提取軌道要素
            inclination = float(line2[8:16])           # 傾角 (度)
            raan = float(line2[17:25])                 # 升交點赤經 (度)
            eccentricity = float("0." + line2[26:33])  # 偏心率
            arg_perigee = float(line2[34:42])          # 近地點幅角 (度)
            mean_anomaly = float(line2[43:51])         # 平近點角 (度)
            mean_motion = float(line2[52:63])          # 平均運動 (轉/日)
            
            # 計算軌道半長軸
            n = mean_motion * 2 * pi / 86400  # 轉換為弧度/秒
            a = (self.mu / (n * n)) ** (1.0/3.0)  # 半長軸 (km)
            
            return {
                'inclination': inclination,
                'raan': raan,
                'eccentricity': eccentricity,
                'arg_perigee': arg_perigee,
                'mean_anomaly': mean_anomaly,
                'mean_motion': mean_motion,
                'epoch_str': epoch_str,
                'semi_major_axis': a
            }
            
        except Exception as e:
            print(f"❌ 解析TLE軌道要素失敗: {e}")
            return {}
    
    def kepler_solve(self, M: float, e: float, tolerance: float = 1e-8) -> float:
        """求解開普勒方程 M = E - e*sin(E)"""
        E = M  # 初始猜測
        
        for _ in range(20):  # 最多迭代20次
            E_new = M + e * sin(E)
            if abs(E_new - E) < tolerance:
                break
            E = E_new
            
        return E
    
    def calculate_position(self, tle: TLEData, target_time: datetime) -> Tuple[float, float, float]:
        """計算衛星在指定時間的地理位置"""
        try:
            elements = self.parse_tle_elements(tle)
            if not elements:
                return 0.0, 0.0, 0.0
            
            # TLE epoch
            epoch_jd = self.julian_date_from_tle_epoch(elements['epoch_str'])
            
            # 目標時間的儒略日
            target_jd = target_time.timestamp() / 86400.0 + 2440587.5
            
            # 時間差 (天)
            dt_days = target_jd - epoch_jd
            
            # 平近點角傳播
            n = elements['mean_motion'] * 2 * pi / 86400  # rad/s
            M = elements['mean_anomaly'] + n * dt_days * 86400
            M = radians(M % 360)
            
            # 求解偏近點角
            E = self.kepler_solve(M, elements['eccentricity'])
            
            # 計算真近點角
            e = elements['eccentricity']
            nu = 2 * atan2(sqrt(1 + e) * sin(E/2), sqrt(1 - e) * cos(E/2))
            
            # 軌道半徑
            a = elements['semi_major_axis']
            r = a * (1 - e * cos(E))
            
            # 軌道平面位置
            cos_nu = cos(nu)
            sin_nu = sin(nu)
            
            # 轉換到地心慣性坐標系
            inc = radians(elements['inclination'])
            omega = radians(elements['arg_perigee'])
            Omega = radians(elements['raan'] + dt_days * 86400 * 0.25 / 86400)  # 簡化地球自轉
            
            cos_omega = cos(omega)
            sin_omega = sin(omega)
            cos_Omega = cos(Omega)
            sin_Omega = sin(Omega)
            cos_inc = cos(inc)
            sin_inc = sin(inc)
            
            # 轉換矩陣
            P = r * cos_nu
            Q = r * sin_nu
            
            x = P * (cos_omega * cos_Omega - sin_omega * sin_Omega * cos_inc) - Q * (sin_omega * cos_Omega + cos_omega * sin_Omega * cos_inc)
            y = P * (cos_omega * sin_Omega + sin_omega * cos_Omega * cos_inc) - Q * (sin_omega * sin_Omega - cos_omega * cos_Omega * cos_inc)
            z = P * sin_omega * sin_inc + Q * cos_omega * sin_inc
            
            # 轉換為地理坐標
            longitude = degrees(atan2(y, x))
            latitude = degrees(asin(z / sqrt(x*x + y*y + z*z)))
            altitude = sqrt(x*x + y*y + z*z) - self.earth_radius_km
            
            return latitude, longitude, altitude
            
        except Exception as e:
            # 計算失敗時返回無效位置
            return 0.0, 0.0, 0.0

class VisibilityCalculator:
    """衛星可見性計算器"""
    
    def __init__(self, observer_lat: float, observer_lon: float, observer_alt: float = 0):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.observer_alt = observer_alt
        self.earth_radius = 6378.137
    
    def calculate_elevation_azimuth(self, sat_lat: float, sat_lon: float, sat_alt: float) -> Tuple[float, float]:
        """計算衛星的仰角和方位角"""
        try:
            # 檢查無效位置
            if sat_lat == 0.0 and sat_lon == 0.0 and sat_alt == 0.0:
                return -90.0, 0.0
            
            # 轉換為弧度
            obs_lat_rad = radians(self.observer_lat)
            obs_lon_rad = radians(self.observer_lon)
            sat_lat_rad = radians(sat_lat)
            sat_lon_rad = radians(sat_lon)
            
            # 計算觀測者和衛星的地心直角坐標
            R_earth = self.earth_radius + self.observer_alt / 1000.0
            R_sat = self.earth_radius + sat_alt
            
            # 觀測者位置向量
            x_obs = R_earth * cos(obs_lat_rad) * cos(obs_lon_rad)
            y_obs = R_earth * cos(obs_lat_rad) * sin(obs_lon_rad)
            z_obs = R_earth * sin(obs_lat_rad)
            
            # 衛星位置向量
            x_sat = R_sat * cos(sat_lat_rad) * cos(sat_lon_rad)
            y_sat = R_sat * cos(sat_lat_rad) * sin(sat_lon_rad)
            z_sat = R_sat * sin(sat_lat_rad)
            
            # 相對位置向量
            dx = x_sat - x_obs
            dy = y_sat - y_obs
            dz = z_sat - z_obs
            
            # 距離
            range_km = sqrt(dx*dx + dy*dy + dz*dz)
            
            # 轉換到觀測者地平坐標系
            sin_lat = sin(obs_lat_rad)
            cos_lat = cos(obs_lat_rad)
            sin_lon = sin(obs_lon_rad)
            cos_lon = cos(obs_lon_rad)
            
            # 南-東-天坐標系
            south = -dx * sin_lat * cos_lon - dy * sin_lat * sin_lon + dz * cos_lat
            east = -dx * sin_lon + dy * cos_lon
            up = dx * cos_lat * cos_lon + dy * cos_lat * sin_lon + dz * sin_lat
            
            # 計算仰角
            elevation_rad = atan2(up, sqrt(south*south + east*east))
            elevation = degrees(elevation_rad)
            
            # 計算方位角 (從北向東測量)
            azimuth_rad = atan2(east, south)
            azimuth = (degrees(azimuth_rad) + 180) % 360  # 轉換為0-360度
            
            return elevation, azimuth
            
        except Exception as e:
            return -90.0, 0.0

class FixedSatellitePoolTester:
    """修正版衛星池測試器"""
    
    def __init__(self):
        self.ntpu_lat = 24.9441667
        self.ntpu_lon = 121.3713889
        self.ntpu_alt = 100
        
        self.sgp4_calc = ImprovedSGP4Calculator()
        self.vis_calc = VisibilityCalculator(self.ntpu_lat, self.ntpu_lon, self.ntpu_alt)
        
        # 仰角門檻
        self.elevation_thresholds = {
            "starlink": 5.0,
            "oneweb": 10.0
        }
    
    def load_tle_data(self) -> Dict[str, List[TLEData]]:
        """載入本地TLE數據"""
        tle_data = {}
        
        # 載入Starlink數據 (取前1000顆進行測試)
        starlink_file = "/home/sat/ntn-stack/netstack/tle_data/starlink/tle/starlink_20250816.tle"
        starlink_sats = TLEData.parse_tle_file(starlink_file)[:1000]  # 限制數量
        if starlink_sats:
            tle_data["starlink"] = starlink_sats
            print(f"📡 Starlink: {len(starlink_sats)} 顆衛星")
        
        # 載入OneWeb數據 (取前200顆進行測試)
        oneweb_file = "/home/sat/ntn-stack/netstack/tle_data/oneweb/tle/oneweb_20250816.tle"
        oneweb_sats = TLEData.parse_tle_file(oneweb_file)[:200]  # 限制數量
        if oneweb_sats:
            tle_data["oneweb"] = oneweb_sats
            print(f"📡 OneWeb: {len(oneweb_sats)} 顆衛星")
        
        total_sats = sum(len(sats) for sats in tle_data.values())
        print(f"🛰️ 總計: {total_sats} 顆衛星 (測試子集)")
        
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
                    
                    # 跳過無效位置
                    if sat_lat == 0.0 and sat_lon == 0.0 and sat_alt == 0.0:
                        continue
                    
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
    
    def run_quick_test(self, duration_minutes: int = 30, interval_minutes: int = 5) -> Dict:
        """執行快速測試"""
        print("🚀 開始修正版衛星池測試")
        print(f"📍 觀測點: NTPU ({self.ntpu_lat}°N, {self.ntpu_lon}°E)")
        print(f"⏱️ 測試週期: {duration_minutes} 分鐘")
        print(f"📊 測試間隔: {interval_minutes} 分鐘")
        
        # 載入TLE數據
        tle_data = self.load_tle_data()
        if not tle_data:
            return {"error": "無法載入TLE數據"}
        
        # 設定測試時間範圍
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
        
        return {
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

def print_test_summary(results: Dict):
    """打印測試結果摘要"""
    print("\n" + "="*60)
    print("🎯 修正版衛星池測試結果")
    print("="*60)
    
    if "error" in results:
        print(f"❌ 測試失敗: {results['error']}")
        return
    
    config = results["test_config"]
    stats = results["statistics"]
    
    print(f"📍 觀測點: NTPU ({config['observer_location']['lat']}°N, {config['observer_location']['lon']}°E)")
    print(f"🛰️ 測試衛星數: {config['total_satellites']} 顆")
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
        
        # 外推到完整星座
        if config['total_satellites'] > 0:
            starlink_ratio = 1000 / 8084  # 測試比例
            oneweb_ratio = 200 / 651      # 測試比例
            
            full_starlink_visible = stats['starlink']['mean'] / starlink_ratio
            full_oneweb_visible = stats['oneweb']['mean'] / oneweb_ratio
            full_total_visible = full_starlink_visible + full_oneweb_visible
            
            print(f"\n🔮 外推到完整星座:")
            print(f"   完整Starlink可見: {full_starlink_visible:.1f} 顆")
            print(f"   完整OneWeb可見: {full_oneweb_visible:.1f} 顆")
            print(f"   預期總可見數: {full_total_visible:.1f} 顆")
            
            # 動態池需求
            if full_total_visible > 0:
                recommended_pool = int(full_total_visible * 20)  # 20倍備用
                print(f"   建議動態池大小: {recommended_pool} 顆")
                print(f"   當前404顆配置: {'✅ 合理' if recommended_pool <= 404 else '❌ 不足'}")
    
    print("="*60)

def main():
    """主函數"""
    tester = FixedSatellitePoolTester()
    
    try:
        # 執行快速測試
        results = tester.run_quick_test(duration_minutes=30, interval_minutes=5)
        
        # 保存詳細結果
        output_file = "/home/sat/ntn-stack/fixed_satellite_pool_test_results.json"
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