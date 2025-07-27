#!/usr/bin/env python3
"""
🛰️ Starlink NTPU 可見性篩選工具 (Starlink NTPU Visibility Finder)

功能：
1. 下載當下最新的 Starlink TLE 數據
2. 計算 96 分鐘軌道週期內從 NTPU 觀測點可見的衛星
3. 找出最佳的 LEO 衛星換手時間點（6-8顆同時可見，仰角≥5°）
4. 支援不同觀測點座標（方便未來修改位置）

作者：Claude Code Assistant
日期：2025-07-27
用途：LEO 衛星換手研究，學術論文數據準備

使用方法：
    python starlink_ntpu_visibility_finder.py
    python starlink_ntpu_visibility_finder.py --lat 25.0 --lon 120.0  # 自定義座標

依賴套件：
    pip install requests skyfield numpy
"""

import argparse
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional, Any
import requests
from skyfield.api import load, wgs84, EarthSatellite
from skyfield.timelib import Time
import numpy as np

# NTPU 精確座標 (國立臺北大學)
DEFAULT_NTPU_LAT = 24.9441667  # 24°56'39"N = 24 + 56/60 + 39/3600
DEFAULT_NTPU_LON = 121.3713889  # 121°22'17"E = 121 + 22/60 + 17/3600
DEFAULT_NTPU_ALT = 0.0  # 海拔高度 (米)

# Starlink TLE 數據源
STARLINK_TLE_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle"

class StarlinkVisibilityFinder:
    """Starlink 衛星可見性篩選器"""
    
    def __init__(self, observer_lat: float, observer_lon: float, observer_alt: float = 0.0):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon  
        self.observer_alt = observer_alt
        self.ts = load.timescale()
        self.observer = wgs84.latlon(observer_lat, observer_lon, elevation_m=observer_alt)
        
        print(f"🌍 觀測點設定: {observer_lat:.6f}°N, {observer_lon:.6f}°E, {observer_alt}m")
        
    def download_latest_starlink_tle(self) -> List[str]:
        """下載當下最新的 Starlink TLE 數據"""
        print(f"🔄 正在下載最新 Starlink TLE 數據...")
        print(f"📡 數據源: {STARLINK_TLE_URL}")
        
        try:
            response = requests.get(STARLINK_TLE_URL, timeout=30)
            response.raise_for_status()
            
            tle_lines = response.text.strip().split('\n')
            tle_lines = [line.strip() for line in tle_lines if line.strip()]
            
            # 驗證 TLE 格式：應該是 3 的倍數 (名稱 + line1 + line2)
            if len(tle_lines) % 3 != 0:
                raise ValueError(f"TLE 數據格式錯誤：行數 {len(tle_lines)} 不是 3 的倍數")
            
            satellite_count = len(tle_lines) // 3
            print(f"✅ 成功下載 {satellite_count} 顆 Starlink 衛星的 TLE 數據")
            print(f"📊 數據大小: {len(response.text)} bytes")
            
            return tle_lines
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 下載 TLE 數據失敗: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 處理 TLE 數據失敗: {e}")
            sys.exit(1)
    
    def parse_tle_data(self, tle_lines: List[str]) -> List[Dict[str, Any]]:
        """解析 TLE 數據為衛星物件"""
        satellites = []
        
        for i in range(0, len(tle_lines), 3):
            try:
                name = tle_lines[i].strip()
                line1 = tle_lines[i + 1].strip()
                line2 = tle_lines[i + 2].strip()
                
                # 創建 Skyfield 衛星物件
                satellite = EarthSatellite(line1, line2, name, self.ts)
                
                # 提取 NORAD ID
                norad_id = int(line1.split()[1][:5])
                
                satellites.append({
                    'name': name,
                    'norad_id': norad_id,
                    'satellite': satellite,
                    'line1': line1,
                    'line2': line2
                })
                
            except Exception as e:
                print(f"⚠️ 跳過無效的 TLE 數據: {name if 'name' in locals() else f'Index {i}'} - {e}")
                continue
        
        print(f"✅ 成功解析 {len(satellites)} 顆衛星")
        return satellites
    
    def calculate_visibility_over_period(self, satellites: List[Dict], duration_minutes: int = 96, 
                                       time_step_seconds: int = 30) -> Dict[str, Any]:
        """計算指定時間段內的衛星可見性"""
        
        print(f"⏰ 開始計算 {duration_minutes} 分鐘內的衛星可見性...")
        print(f"📊 時間解析度: {time_step_seconds} 秒")
        print(f"🔢 總計算點數: {duration_minutes * 60 // time_step_seconds}")
        
        # 使用當前時間作為起始點
        start_time = self.ts.now()
        end_time = self.ts.tt_jd(start_time.tt + duration_minutes / (24 * 60))
        
        # 生成時間點
        time_points = []
        current_tt = start_time.tt
        time_step_days = time_step_seconds / (24 * 3600)
        
        while current_tt <= end_time.tt:
            time_points.append(self.ts.tt_jd(current_tt))
            current_tt += time_step_days
        
        print(f"⏳ 正在計算 {len(satellites)} 顆衛星在 {len(time_points)} 個時間點的位置...")
        
        visibility_data = []
        
        # 批次計算所有衛星在所有時間點的位置
        for time_point in time_points:
            visible_satellites = []
            
            for sat_data in satellites:
                try:
                    satellite = sat_data['satellite']
                    
                    # 計算衛星相對於觀測點的位置
                    difference = satellite - self.observer
                    topocentric = difference.at(time_point)
                    
                    # 計算仰角和方位角
                    elevation, azimuth, distance = topocentric.altaz()
                    
                    elevation_deg = elevation.degrees
                    azimuth_deg = azimuth.degrees
                    distance_km = distance.km
                    
                    # 只記錄仰角 ≥ 5° 的衛星（適合換手的候選）
                    if elevation_deg >= 5.0:
                        # 計算衛星的地理位置
                        geocentric = satellite.at(time_point)
                        subpoint = wgs84.subpoint(geocentric)
                        
                        visible_satellites.append({
                            'name': sat_data['name'],
                            'norad_id': sat_data['norad_id'],
                            'elevation_deg': round(elevation_deg, 2),
                            'azimuth_deg': round(azimuth_deg, 2),
                            'distance_km': round(distance_km, 2),
                            'satellite_lat': round(subpoint.latitude.degrees, 4),
                            'satellite_lon': round(subpoint.longitude.degrees, 4),
                            'satellite_alt_km': round(subpoint.elevation.km, 2)
                        })
                        
                except Exception as e:
                    # 跳過計算失敗的衛星
                    continue
            
            if visible_satellites:
                visibility_data.append({
                    'timestamp': time_point.utc_datetime(),
                    'timestamp_iso': time_point.utc_datetime().isoformat() + 'Z',
                    'visible_count': len(visible_satellites),
                    'satellites': visible_satellites
                })
        
        print(f"✅ 計算完成！找到 {len(visibility_data)} 個有可見衛星的時間點")
        
        return {
            'observer_location': {
                'latitude': self.observer_lat,
                'longitude': self.observer_lon,
                'altitude_m': self.observer_alt
            },
            'calculation_period': {
                'start_time': start_time.utc_datetime().isoformat() + 'Z',
                'duration_minutes': duration_minutes,
                'time_step_seconds': time_step_seconds
            },
            'total_satellites_analyzed': len(satellites),
            'visibility_data': visibility_data
        }
    
    def find_optimal_handover_times(self, visibility_data: Dict[str, Any], 
                                   target_count_min: int = 6, target_count_max: int = 8) -> List[Dict]:
        """找出最佳的換手時間點（6-8顆衛星同時可見）"""
        
        optimal_times = []
        
        for data_point in visibility_data['visibility_data']:
            visible_count = data_point['visible_count']
            
            # 篩選符合換手條件的時間點
            if target_count_min <= visible_count <= target_count_max:
                optimal_times.append({
                    'timestamp': data_point['timestamp_iso'],
                    'visible_count': visible_count,
                    'satellites': data_point['satellites'],
                    'max_elevation': max(sat['elevation_deg'] for sat in data_point['satellites']),
                    'min_elevation': min(sat['elevation_deg'] for sat in data_point['satellites']),
                    'avg_elevation': round(sum(sat['elevation_deg'] for sat in data_point['satellites']) / visible_count, 2)
                })
        
        # 按可見衛星數量和平均仰角排序
        optimal_times.sort(key=lambda x: (x['visible_count'], x['avg_elevation']), reverse=True)
        
        return optimal_times
    
    def generate_report(self, visibility_data: Dict[str, Any], optimal_times: List[Dict]) -> str:
        """生成分析報告"""
        
        report = []
        report.append("🛰️ Starlink NTPU 可見性分析報告")
        report.append("=" * 50)
        report.append(f"📅 分析時間: {datetime.now(timezone.utc).isoformat()}")
        report.append(f"🌍 觀測點: {self.observer_lat:.6f}°N, {self.observer_lon:.6f}°E")
        report.append(f"🔢 分析衛星總數: {visibility_data['total_satellites_analyzed']}")
        report.append(f"⏰ 分析時間段: {visibility_data['calculation_period']['duration_minutes']} 分鐘")
        report.append("")
        
        # 統計資訊
        all_visible_counts = [dp['visible_count'] for dp in visibility_data['visibility_data']]
        if all_visible_counts:
            report.append("📊 可見性統計:")
            report.append(f"   最大同時可見衛星數: {max(all_visible_counts)} 顆")
            report.append(f"   平均同時可見衛星數: {sum(all_visible_counts) / len(all_visible_counts):.1f} 顆")
            report.append(f"   有可見衛星的時間點: {len(all_visible_counts)} 個")
        report.append("")
        
        # 最佳換手時間點
        if optimal_times:
            report.append(f"🎯 最佳換手時間點 (6-8顆衛星同時可見):")
            report.append(f"   找到 {len(optimal_times)} 個理想時間點")
            report.append("")
            
            for i, time_data in enumerate(optimal_times[:5], 1):  # 顯示前5個最佳時間點
                report.append(f"   #{i} {time_data['timestamp']}")
                report.append(f"       可見衛星: {time_data['visible_count']} 顆")
                report.append(f"       仰角範圍: {time_data['min_elevation']}° - {time_data['max_elevation']}°")
                report.append(f"       平均仰角: {time_data['avg_elevation']}°")
                
                # 顯示衛星列表
                sat_names = [sat['name'] for sat in time_data['satellites']]
                report.append(f"       衛星: {', '.join(sat_names[:3])}...")
                report.append("")
        else:
            report.append("⚠️ 在分析時間段內未找到理想的換手時間點 (6-8顆衛星)")
            report.append("   建議: 擴大時間範圍或降低衛星數量要求")
            report.append("")
        
        report.append("🔗 數據來源: CelesTrak Starlink TLE")
        report.append("⚙️ 計算引擎: Skyfield + SGP4")
        report.append("🎓 用途: LEO 衛星換手研究")
        
        return "\n".join(report)

def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="Starlink NTPU 可見性篩選工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python starlink_ntpu_visibility_finder.py                    # 使用預設 NTPU 座標
  python starlink_ntpu_visibility_finder.py --lat 25.0 --lon 120.0  # 自定義座標
  python starlink_ntpu_visibility_finder.py --duration 120    # 擴大分析時間到120分鐘
  python starlink_ntpu_visibility_finder.py --output results.json    # 輸出結果到檔案
        """)
    
    parser.add_argument('--lat', type=float, default=DEFAULT_NTPU_LAT,
                       help=f'觀測點緯度 (預設: {DEFAULT_NTPU_LAT}°N NTPU)')
    parser.add_argument('--lon', type=float, default=DEFAULT_NTPU_LON,
                       help=f'觀測點經度 (預設: {DEFAULT_NTPU_LON}°E NTPU)')
    parser.add_argument('--alt', type=float, default=DEFAULT_NTPU_ALT,
                       help=f'觀測點海拔高度 (米，預設: {DEFAULT_NTPU_ALT})')
    parser.add_argument('--duration', type=int, default=96,
                       help='分析時間長度 (分鐘，預設: 96 = 一個軌道週期)')
    parser.add_argument('--time-step', type=int, default=30,
                       help='時間解析度 (秒，預設: 30)')
    parser.add_argument('--min-satellites', type=int, default=6,
                       help='最佳換手的最少衛星數 (預設: 6)')
    parser.add_argument('--max-satellites', type=int, default=8,
                       help='最佳換手的最多衛星數 (預設: 8)')
    parser.add_argument('--output', type=str,
                       help='輸出結果到 JSON 檔案 (可選)')
    
    args = parser.parse_args()
    
    print("🛰️ Starlink NTPU 可見性篩選工具")
    print("=" * 50)
    
    # 創建篩選器
    finder = StarlinkVisibilityFinder(args.lat, args.lon, args.alt)
    
    # 下載最新 TLE 數據
    tle_lines = finder.download_latest_starlink_tle()
    
    # 解析衛星數據
    satellites = finder.parse_tle_data(tle_lines)
    
    if not satellites:
        print("❌ 未能解析到任何衛星數據")
        sys.exit(1)
    
    # 計算可見性
    visibility_data = finder.calculate_visibility_over_period(
        satellites, args.duration, args.time_step
    )
    
    # 找出最佳換手時間點
    optimal_times = finder.find_optimal_handover_times(
        visibility_data, args.min_satellites, args.max_satellites
    )
    
    # 生成報告
    report = finder.generate_report(visibility_data, optimal_times)
    print("\n" + report)
    
    # 輸出結果到檔案 (如果指定)
    if args.output:
        output_data = {
            'analysis_info': {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'observer_location': {
                    'latitude': args.lat,
                    'longitude': args.lon,
                    'altitude_m': args.alt
                }
            },
            'visibility_data': visibility_data,
            'optimal_handover_times': optimal_times,
            'report': report
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 結果已保存到: {args.output}")

if __name__ == "__main__":
    main()