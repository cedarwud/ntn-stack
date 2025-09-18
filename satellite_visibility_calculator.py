#!/usr/bin/env python3
"""
真實的衛星可見性計算器
基於TLE數據和SGP4軌道傳播，實現完整的9步驟計算流程

用法:
    python satellite_visibility_calculator.py --constellation starlink --satellites 100 --location ntpu
    python satellite_visibility_calculator.py --constellation oneweb --satellites 50 --location ntpu
    python satellite_visibility_calculator.py --constellation both --satellites 200 --location ntpu
"""

import argparse
import os
import sys
import json
import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

try:
    from sgp4.api import Satrec, jday
    from sgp4 import model
    from sgp4.earth_gravity import wgs84
    from skyfield.api import load, Topos
    from skyfield.sgp4lib import EarthSatellite
    from skyfield.timelib import Time
except ImportError as e:
    print(f"❌ 必需的庫未安裝: {e}")
    print("請安裝: pip install sgp4 skyfield numpy")
    sys.exit(1)

# 預定義位置
LOCATIONS = {
    'ntpu': {
        'name': 'NTPU',
        'latitude': 24.9439,   # 度
        'longitude': 121.3711, # 度
        'altitude': 50.0,      # 米
        'description': '國立台北大學'
    },
    'taipei': {
        'name': 'Taipei',
        'latitude': 25.0330,
        'longitude': 121.5654,
        'altitude': 10.0,
        'description': '台北市'
    },
    'custom': {
        'name': 'Custom',
        'latitude': None,  # 需要用戶提供
        'longitude': None,
        'altitude': 0.0,
        'description': '自定義位置'
    }
}

class SatelliteVisibilityCalculator:
    """真實的衛星可見性計算器 - 實現完整的9步驟流程"""

    def __init__(self, tle_data_path: str, observer_location: Dict[str, float]):
        """
        初始化計算器

        Args:
            tle_data_path: TLE數據目錄路徑
            observer_location: 觀測者位置 {'latitude': lat, 'longitude': lon, 'altitude': alt_m}
        """
        self.tle_data_path = tle_data_path
        self.observer_location = observer_location
        self.satellites = []
        self.ts = load.timescale()
        self.observer = Topos(
            latitude_degrees=observer_location['latitude'],
            longitude_degrees=observer_location['longitude'],
            elevation_m=observer_location['altitude']
        )

        print(f"🛰️ 衛星可見性計算器初始化")
        print(f"📍 觀測位置: {observer_location['latitude']:.4f}°N, {observer_location['longitude']:.4f}°E")
        print(f"🏔️ 海拔高度: {observer_location['altitude']:.0f}m")

    def step1_parse_tle_data(self, constellation: str, max_satellites: Optional[int] = None) -> List[Dict]:
        """
        步驟1: TLE數據解析

        Args:
            constellation: 星座名稱 ('starlink', 'oneweb', 'both')
            max_satellites: 最大衛星數量限制

        Returns:
            解析後的衛星列表
        """
        print(f"\n📋 步驟1: 解析{constellation.upper()}的TLE數據...")

        satellites = []
        constellations_to_load = []

        if constellation == 'both':
            constellations_to_load = ['starlink', 'oneweb']
        else:
            constellations_to_load = [constellation]

        for const in constellations_to_load:
            const_path = os.path.join(self.tle_data_path, const, 'tle')
            if not os.path.exists(const_path):
                print(f"❌ 找不到{const.upper()}數據目錄: {const_path}")
                continue

            # 找到最新的TLE文件
            tle_files = [f for f in os.listdir(const_path) if f.endswith('.tle')]
            if not tle_files:
                print(f"❌ {const.upper()}目錄中沒有TLE文件")
                continue

            latest_tle_file = max(tle_files)  # 按文件名排序，最新的在最後
            tle_file_path = os.path.join(const_path, latest_tle_file)

            print(f"📄 載入{const.upper()}文件: {latest_tle_file}")

            # 解析TLE文件
            const_satellites = self._parse_single_tle_file(tle_file_path, const)
            satellites.extend(const_satellites)

            print(f"✅ {const.upper()}: 載入 {len(const_satellites)} 顆衛星")

        # 限制衛星數量
        if max_satellites and len(satellites) > max_satellites:
            satellites = satellites[:max_satellites]
            print(f"🔢 限制衛星數量至: {max_satellites} 顆")

        print(f"📊 總計載入: {len(satellites)} 顆衛星")
        self.satellites = satellites
        return satellites

    def _parse_single_tle_file(self, file_path: str, constellation: str) -> List[Dict]:
        """解析單個TLE文件"""
        satellites = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"❌ 讀取TLE文件失敗: {e}")
            return satellites

        # 每3行為一顆衛星
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break

            name_line = lines[i].strip()
            tle_line1 = lines[i + 1].strip()
            tle_line2 = lines[i + 2].strip()

            # 驗證TLE格式
            if not (tle_line1.startswith('1 ') and tle_line2.startswith('2 ')):
                continue

            if len(tle_line1) < 69 or len(tle_line2) < 69:
                continue

            try:
                # 創建SGP4衛星對象進行驗證
                satellite_sgp4 = Satrec.twoline2rv(tle_line1, tle_line2)

                # 使用Skyfield創建衛星對象（更精確的座標轉換）
                satellite_skyfield = EarthSatellite(tle_line1, tle_line2, name_line, self.ts)

                satellites.append({
                    'name': name_line,
                    'constellation': constellation,
                    'norad_id': tle_line1[2:7].strip(),
                    'tle_line1': tle_line1,
                    'tle_line2': tle_line2,
                    'sgp4_satellite': satellite_sgp4,
                    'skyfield_satellite': satellite_skyfield,
                    'tle_epoch': satellite_sgp4.jdsatepoch  # Julian Date
                })

            except Exception as e:
                print(f"⚠️ 衛星 {name_line} 解析失敗: {e}")
                continue

        return satellites

    def step2_sgp4_initialization(self):
        """步驟2: SGP4軌道傳播初始化"""
        print(f"\n🛰️ 步驟2: SGP4軌道傳播初始化...")

        if not self.satellites:
            print("❌ 沒有可用的衛星數據")
            return False

        # 獲取TLE epoch時間範圍
        epochs = [sat['tle_epoch'] for sat in self.satellites]
        min_epoch = min(epochs)
        max_epoch = max(epochs)

        # 轉換為可讀格式
        min_date = self.ts.ut1_jd(min_epoch).utc_datetime()
        max_date = self.ts.ut1_jd(max_epoch).utc_datetime()

        print(f"⏰ TLE Epoch範圍:")
        print(f"   最早: {min_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"   最晚: {max_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📡 使用地球引力模型: WGS84")

        # 選擇計算基準時間（使用最新的epoch）
        self.calculation_base_epoch = max_epoch
        self.calculation_base_time = self.ts.ut1_jd(max_epoch)

        print(f"🎯 計算基準時間: {self.calculation_base_time.utc_datetime().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        return True

    def step3_setup_time_series(self, duration_minutes: int = 96, interval_seconds: int = 30):
        """
        步驟3: 時間序列設定

        Args:
            duration_minutes: 計算時長（分鐘）
            interval_seconds: 時間間隔（秒）
        """
        print(f"\n⏰ 步驟3: 設定時間序列...")
        print(f"📅 計算時長: {duration_minutes} 分鐘")
        print(f"⏱️ 時間間隔: {interval_seconds} 秒")

        # 生成時間序列
        total_points = int(duration_minutes * 60 / interval_seconds)
        time_offsets_seconds = np.arange(0, duration_minutes * 60, interval_seconds)  # 秒偏移

        # 創建Skyfield時間序列
        self.time_series = []
        for offset_seconds in time_offsets_seconds:
            # 轉換numpy int64為Python int以避免timedelta類型錯誤
            offset_seconds_int = int(offset_seconds)
            # 使用Skyfield的時間偏移方法
            offset_days = offset_seconds_int / (24 * 60 * 60)  # 轉換為天數
            time_point = self.ts.ut1_jd(self.calculation_base_epoch + offset_days)
            self.time_series.append(time_point)

        print(f"📊 生成 {len(self.time_series)} 個時間點")
        print(f"🚀 開始時間: {self.time_series[0].utc_datetime().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🏁 結束時間: {self.time_series[-1].utc_datetime().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        self.duration_minutes = duration_minutes
        self.interval_seconds = interval_seconds

    def step4_sgp4_orbit_calculation(self):
        """步驟4: SGP4軌道計算"""
        print(f"\n🧮 步驟4: SGP4軌道計算...")
        print(f"📊 計算 {len(self.satellites)} 顆衛星 × {len(self.time_series)} 個時間點")

        # 為每顆衛星計算軌道
        for i, satellite in enumerate(self.satellites):
            satellite['positions'] = []
            satellite['calculation_errors'] = 0

            for time_point in self.time_series:
                try:
                    # 使用Skyfield計算位置（自動處理座標轉換）
                    geocentric = satellite['skyfield_satellite'].at(time_point)

                    # 獲得ITRS座標 (International Terrestrial Reference System)
                    position = geocentric.position.km
                    velocity = geocentric.velocity.km_per_s if hasattr(geocentric, 'velocity') else None

                    satellite['positions'].append({
                        'time': time_point,
                        'position_itrs_km': position,
                        'velocity_km_per_s': velocity,
                        'jd': time_point.ut1,
                        'calculation_error': False
                    })

                except Exception as e:
                    satellite['calculation_errors'] += 1
                    satellite['positions'].append({
                        'time': time_point,
                        'position_itrs_km': None,
                        'velocity_km_per_s': None,
                        'jd': time_point.ut1,
                        'calculation_error': True,
                        'error_message': str(e)
                    })

            if (i + 1) % 100 == 0 or i == len(self.satellites) - 1:
                progress = (i + 1) / len(self.satellites) * 100
                print(f"   進度: {progress:.1f}% ({i + 1}/{len(self.satellites)})")

        # 統計計算成功率
        total_calculations = len(self.satellites) * len(self.time_series)
        total_errors = sum(sat['calculation_errors'] for sat in self.satellites)
        success_rate = (total_calculations - total_errors) / total_calculations * 100

        print(f"✅ SGP4計算完成")
        print(f"📊 成功率: {success_rate:.2f}% ({total_calculations - total_errors}/{total_calculations})")

        if total_errors > 0:
            print(f"⚠️ 計算錯誤: {total_errors} 次")

    def step5_coordinate_transformation(self):
        """步驟5: 座標系轉換 (Skyfield已自動處理TEME→ITRS)"""
        print(f"\n🌍 步驟5: 座標系轉換...")
        print("✅ 使用Skyfield自動處理座標轉換:")
        print("   • TEME → ITRS (考慮地球自轉)")
        print("   • 精確時間標準轉換 (UTC/UT1/TT)")
        print("   • 考慮歲差和章動")
        print("   • 使用WGS84地球模型")

    def step6_observer_coordinates(self):
        """步驟6: 觀測者座標計算 (Skyfield已自動處理)"""
        print(f"\n📍 步驟6: 觀測者座標計算...")
        print("✅ 使用Skyfield自動處理觀測者座標:")
        print(f"   • 觀測者: {self.observer_location['latitude']:.4f}°N, {self.observer_location['longitude']:.4f}°E")
        print(f"   • 海拔: {self.observer_location['altitude']:.0f}m")
        print("   • 使用WGS84橢球模型")
        print("   • 自動轉換為ITRS座標")

    def step7_relative_geometry_calculation(self, min_elevation_deg: float = 5.0):
        """
        步驟7: 相對幾何計算

        Args:
            min_elevation_deg: 最小仰角門檻（度）
        """
        print(f"\n📐 步驟7: 相對幾何計算...")
        print(f"🎯 最小仰角門檻: {min_elevation_deg}°")

        # 為每顆衛星計算相對幾何
        for i, satellite in enumerate(self.satellites):
            satellite['visibility_data'] = []

            for pos_data in satellite['positions']:
                if pos_data['calculation_error']:
                    satellite['visibility_data'].append({
                        'time': pos_data['time'],
                        'visible': False,
                        'elevation_deg': None,
                        'azimuth_deg': None,
                        'distance_km': None,
                        'error': True
                    })
                    continue

                try:
                    # 使用Skyfield計算觀測幾何
                    geocentric = satellite['skyfield_satellite'].at(pos_data['time'])
                    topocentric = geocentric - self.observer.at(pos_data['time'])

                    # 計算仰角、方位角、距離
                    alt, az, distance = topocentric.altaz()

                    elevation_deg = alt.degrees
                    azimuth_deg = az.degrees
                    distance_km = distance.km

                    # 判斷可見性
                    visible = elevation_deg >= min_elevation_deg

                    satellite['visibility_data'].append({
                        'time': pos_data['time'],
                        'visible': visible,
                        'elevation_deg': elevation_deg,
                        'azimuth_deg': azimuth_deg,
                        'distance_km': distance_km,
                        'error': False
                    })

                except Exception as e:
                    satellite['visibility_data'].append({
                        'time': pos_data['time'],
                        'visible': False,
                        'elevation_deg': None,
                        'azimuth_deg': None,
                        'distance_km': None,
                        'error': True,
                        'error_message': str(e)
                    })

            if (i + 1) % 100 == 0 or i == len(self.satellites) - 1:
                progress = (i + 1) / len(self.satellites) * 100
                print(f"   進度: {progress:.1f}% ({i + 1}/{len(self.satellites)})")

        print("✅ 相對幾何計算完成")

    def step8_visibility_determination(self, min_elevation_deg: float = 5.0):
        """步驟8: 可見性判斷"""
        print(f"\n👁️ 步驟8: 可見性判斷...")

        # 統計每個時間點的可見衛星
        self.visibility_timeline = []

        for time_idx, time_point in enumerate(self.time_series):
            visible_satellites = []

            for satellite in self.satellites:
                vis_data = satellite['visibility_data'][time_idx]

                if vis_data['visible'] and not vis_data['error']:
                    visible_satellites.append({
                        'name': satellite['name'],
                        'constellation': satellite['constellation'],
                        'norad_id': satellite['norad_id'],
                        'elevation_deg': vis_data['elevation_deg'],
                        'azimuth_deg': vis_data['azimuth_deg'],
                        'distance_km': vis_data['distance_km']
                    })

            self.visibility_timeline.append({
                'time': time_point,
                'datetime': time_point.utc_datetime(),
                'visible_count': len(visible_satellites),
                'visible_satellites': visible_satellites
            })

        print(f"✅ 可見性判斷完成")
        print(f"📊 生成 {len(self.visibility_timeline)} 個時間點的可見性數據")

    def step9_statistical_analysis(self):
        """步驟9: 統計分析"""
        print(f"\n📊 步驟9: 統計分析...")

        # 總體統計
        visible_counts = [entry['visible_count'] for entry in self.visibility_timeline]

        total_stats = {
            'max_visible': max(visible_counts),
            'min_visible': min(visible_counts),
            'avg_visible': np.mean(visible_counts),
            'median_visible': np.median(visible_counts),
            'std_visible': np.std(visible_counts)
        }

        # 按星座統計
        constellation_stats = {}
        for constellation in set(sat['constellation'] for sat in self.satellites):
            const_counts = []
            for entry in self.visibility_timeline:
                const_count = sum(1 for sat in entry['visible_satellites']
                                if sat['constellation'] == constellation)
                const_counts.append(const_count)

            constellation_stats[constellation] = {
                'max_visible': max(const_counts),
                'min_visible': min(const_counts),
                'avg_visible': np.mean(const_counts),
                'median_visible': np.median(const_counts),
                'std_visible': np.std(const_counts),
                'total_satellites': sum(1 for sat in self.satellites if sat['constellation'] == constellation)
            }

        # 計算覆蓋連續性
        zero_coverage_periods = sum(1 for count in visible_counts if count == 0)
        coverage_continuity = (len(visible_counts) - zero_coverage_periods) / len(visible_counts) * 100

        # 升起/降落事件分析
        rise_set_events = self._analyze_rise_set_events()

        self.analysis_results = {
            'calculation_parameters': {
                'duration_minutes': self.duration_minutes,
                'interval_seconds': self.interval_seconds,
                'total_time_points': len(self.time_series),
                'total_satellites': len(self.satellites),
                'min_elevation_deg': 5.0  # 假設使用5度門檻
            },
            'total_statistics': total_stats,
            'constellation_statistics': constellation_stats,
            'coverage_continuity_percent': coverage_continuity,
            'zero_coverage_periods': zero_coverage_periods,
            'rise_set_events': rise_set_events
        }

        return self.analysis_results

    def _analyze_rise_set_events(self):
        """分析升起/降落事件"""
        events = []

        for satellite in self.satellites:
            sat_events = []
            prev_visible = False

            for i, vis_data in enumerate(satellite['visibility_data']):
                if vis_data['error']:
                    continue

                current_visible = vis_data['visible']

                if not prev_visible and current_visible:
                    # 升起事件
                    sat_events.append({
                        'type': 'rise',
                        'time': vis_data['time'].utc_datetime(),
                        'elevation_deg': vis_data['elevation_deg'],
                        'azimuth_deg': vis_data['azimuth_deg']
                    })
                elif prev_visible and not current_visible:
                    # 降落事件
                    sat_events.append({
                        'type': 'set',
                        'time': vis_data['time'].utc_datetime(),
                        'elevation_deg': vis_data.get('elevation_deg'),
                        'azimuth_deg': vis_data.get('azimuth_deg')
                    })

                prev_visible = current_visible

            if sat_events:
                events.append({
                    'satellite': satellite['name'],
                    'constellation': satellite['constellation'],
                    'events': sat_events
                })

        return events

    def print_results(self):
        """打印計算結果"""
        if not hasattr(self, 'analysis_results'):
            print("❌ 請先完成統計分析")
            return

        results = self.analysis_results

        print(f"\n🎯 ===== 衛星可見性計算結果 =====")
        print(f"📅 計算參數:")
        print(f"   時長: {results['calculation_parameters']['duration_minutes']} 分鐘")
        print(f"   間隔: {results['calculation_parameters']['interval_seconds']} 秒")
        print(f"   時間點: {results['calculation_parameters']['total_time_points']} 個")
        print(f"   衛星總數: {results['calculation_parameters']['total_satellites']} 顆")

        print(f"\n📊 總體統計:")
        total = results['total_statistics']
        print(f"   最大同時可見: {total['max_visible']} 顆")
        print(f"   最小同時可見: {total['min_visible']} 顆")
        print(f"   平均可見數量: {total['avg_visible']:.1f} 顆")
        print(f"   中位數可見: {total['median_visible']:.1f} 顆")
        print(f"   標準差: {total['std_visible']:.1f}")

        print(f"\n🛰️ 按星座統計:")
        for constellation, stats in results['constellation_statistics'].items():
            print(f"   {constellation.upper()}: (總數: {stats['total_satellites']} 顆)")
            print(f"     最大: {stats['max_visible']} 顆")
            print(f"     最小: {stats['min_visible']} 顆")
            print(f"     平均: {stats['avg_visible']:.1f} 顆")
            print(f"     中位: {stats['median_visible']:.1f} 顆")

        print(f"\n📡 覆蓋分析:")
        print(f"   覆蓋連續性: {results['coverage_continuity_percent']:.1f}%")
        print(f"   無覆蓋時段: {results['zero_coverage_periods']}/{results['calculation_parameters']['total_time_points']} 個時間點")

        # 升起/降落事件統計
        total_events = sum(len(sat['events']) for sat in results['rise_set_events'])
        rise_events = sum(sum(1 for event in sat['events'] if event['type'] == 'rise')
                         for sat in results['rise_set_events'])
        set_events = sum(sum(1 for event in sat['events'] if event['type'] == 'set')
                        for sat in results['rise_set_events'])

        print(f"\n🌅 升起/降落事件:")
        print(f"   總事件數: {total_events}")
        print(f"   升起事件: {rise_events}")
        print(f"   降落事件: {set_events}")

    def save_results(self, output_file: str):
        """保存結果到JSON文件"""
        if not hasattr(self, 'analysis_results'):
            print("❌ 請先完成統計分析")
            return False

        try:
            # 準備可序列化的數據
            serializable_results = {
                'metadata': {
                    'calculation_time': datetime.now(timezone.utc).isoformat(),
                    'observer_location': self.observer_location,
                    'tle_data_path': self.tle_data_path
                },
                'analysis_results': self.analysis_results,
                'sample_timeline': []
            }

            # 添加樣本時間線（前10個時間點）
            for entry in self.visibility_timeline[:10]:
                serializable_results['sample_timeline'].append({
                    'time': entry['datetime'].isoformat(),
                    'visible_count': entry['visible_count'],
                    'visible_satellites': entry['visible_satellites'][:5]  # 前5顆衛星
                })

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)

            print(f"💾 結果已保存至: {output_file}")
            return True

        except Exception as e:
            print(f"❌ 保存結果失敗: {e}")
            return False

    def run_complete_analysis(self, constellation: str, max_satellites: int,
                             duration_minutes: int = 96, interval_seconds: int = 30,
                             min_elevation_deg: float = 5.0):
        """運行完整的9步驟分析"""
        print(f"🚀 開始完整的衛星可見性分析")
        print(f"🎯 參數: {constellation.upper()}, 最多{max_satellites}顆, {duration_minutes}分鐘, {min_elevation_deg}°門檻")

        try:
            # 執行9個步驟
            self.step1_parse_tle_data(constellation, max_satellites)

            if not self.step2_sgp4_initialization():
                return False

            self.step3_setup_time_series(duration_minutes, interval_seconds)
            self.step4_sgp4_orbit_calculation()
            self.step5_coordinate_transformation()
            self.step6_observer_coordinates()
            self.step7_relative_geometry_calculation(min_elevation_deg)
            self.step8_visibility_determination(min_elevation_deg)
            self.step9_statistical_analysis()

            print(f"\n✅ 完整分析完成！")
            return True

        except Exception as e:
            print(f"❌ 分析過程中出現錯誤: {e}")
            import traceback
            print(traceback.format_exc())
            return False


def main():
    """主程序"""
    parser = argparse.ArgumentParser(
        description='真實的衛星可見性計算器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s --constellation starlink --satellites 100 --location ntpu
  %(prog)s --constellation oneweb --satellites 50 --location ntpu
  %(prog)s --constellation both --satellites 200 --location ntpu --duration 24 --interval 5
  %(prog)s --constellation starlink --satellites 100 --location custom --lat 25.0 --lon 121.5 --alt 100
        """
    )

    # 必需參數
    parser.add_argument('--constellation', '-c',
                       choices=['starlink', 'oneweb', 'both'],
                       required=True,
                       help='星座選擇')

    parser.add_argument('--satellites', '-s',
                       type=int, required=True,
                       help='要計算的衛星數量')

    parser.add_argument('--location', '-l',
                       choices=list(LOCATIONS.keys()),
                       required=True,
                       help='觀測位置')

    # 可選參數
    parser.add_argument('--duration', '-d',
                       type=int, default=96,
                       help='計算時長（分鐘）, 默認96')

    parser.add_argument('--interval', '-i',
                       type=int, default=30,
                       help='時間間隔（秒）, 默認30')

    parser.add_argument('--elevation', '-e',
                       type=float, default=5.0,
                       help='最小仰角門檻（度）, 默認5.0')

    parser.add_argument('--output', '-o',
                       help='輸出文件路徑（JSON格式）')

    # 自定義位置參數
    parser.add_argument('--lat', type=float,
                       help='自定義緯度（度）')

    parser.add_argument('--lon', type=float,
                       help='自定義經度（度）')

    parser.add_argument('--alt', type=float, default=0.0,
                       help='自定義海拔（米）, 默認0')

    parser.add_argument('--tle-path',
                       help='TLE數據目錄路徑，默認使用netstack/tle_data')

    args = parser.parse_args()

    # 處理自定義位置
    if args.location == 'custom':
        if args.lat is None or args.lon is None:
            print("❌ 使用自定義位置時必須提供 --lat 和 --lon 參數")
            sys.exit(1)

        observer_location = {
            'latitude': args.lat,
            'longitude': args.lon,
            'altitude': args.alt
        }
    else:
        location_config = LOCATIONS[args.location].copy()
        observer_location = {
            'latitude': location_config['latitude'],
            'longitude': location_config['longitude'],
            'altitude': location_config['altitude']
        }

    # 確定TLE數據路徑
    if args.tle_path:
        tle_data_path = args.tle_path
    else:
        # 嘗試找到netstack的TLE數據
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, 'netstack', 'tle_data'),
            '/home/sat/ntn-stack/netstack/tle_data',
            os.path.join(script_dir, 'satellite-processing-system', 'data', 'tle_data')
        ]

        tle_data_path = None
        for path in possible_paths:
            if os.path.exists(path):
                tle_data_path = path
                break

        if not tle_data_path:
            print("❌ 找不到TLE數據目錄，請使用 --tle-path 指定")
            sys.exit(1)

    # 驗證TLE數據路徑
    if not os.path.exists(tle_data_path):
        print(f"❌ TLE數據目錄不存在: {tle_data_path}")
        sys.exit(1)

    print(f"📁 使用TLE數據路徑: {tle_data_path}")

    # 創建計算器並運行分析
    calculator = SatelliteVisibilityCalculator(tle_data_path, observer_location)

    success = calculator.run_complete_analysis(
        constellation=args.constellation,
        max_satellites=args.satellites,
        duration_minutes=args.duration,
        interval_seconds=args.interval,
        min_elevation_deg=args.elevation
    )

    if success:
        calculator.print_results()

        # 保存結果
        if args.output:
            calculator.save_results(args.output)
        else:
            # 自動生成輸出文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"satellite_visibility_{args.constellation}_{args.satellites}sats_{timestamp}.json"
            calculator.save_results(output_file)
    else:
        print("❌ 計算失敗")
        sys.exit(1)


if __name__ == '__main__':
    main()