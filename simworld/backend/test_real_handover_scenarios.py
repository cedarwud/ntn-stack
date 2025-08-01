#!/usr/bin/env python3
"""
測試篩選後衛星的真實換手決策場景
驗證在座標 24.9441°N, 121.3714°E 能否產生合理的衛星換手決策
"""

import json
import math
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import numpy as np

from rl_optimized_satellite_filter import RLOptimizedSatelliteFilter

class RealHandoverScenarioTester:
    """真實換手場景測試器"""
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        self.earth_radius = 6371.0  # 地球半徑（公里）
        
        # 仰角門檻 (使用衛星換手標準)
        self.elevation_thresholds = {
            'critical': 5.0,    # 臨界門檻
            'execution': 10.0,  # 執行門檻
            'preparation': 15.0 # 預備門檻
        }
    
    def test_handover_scenarios(self, satellites: List[Dict], test_duration_hours: int = 24) -> Dict[str, Any]:
        """
        測試真實的換手場景
        """
        print(f"🔄 測試 {len(satellites)} 顆衛星的換手場景 ({test_duration_hours} 小時)")
        
        results = {
            'test_parameters': {
                'target_coordinate': f"{self.target_lat:.4f}°N, {self.target_lon:.4f}°E",
                'test_duration_hours': test_duration_hours,
                'elevation_thresholds': self.elevation_thresholds
            },
            'handover_events': [],
            'visibility_analysis': {},
            'decision_quality': {},
            'scenario_summary': {}
        }
        
        # 生成測試時間序列
        start_time = datetime.utcnow()
        time_steps = [start_time + timedelta(minutes=m) for m in range(0, test_duration_hours * 60, 5)]
        
        # 分析衛星可見性時間線
        visibility_timeline = self._calculate_visibility_timeline(satellites[:20], time_steps)
        results['visibility_analysis'] = visibility_timeline
        
        # 識別換手事件
        handover_events = self._identify_handover_events(visibility_timeline, time_steps)
        results['handover_events'] = handover_events
        
        # 評估決策品質
        decision_quality = self._evaluate_decision_quality(handover_events, visibility_timeline)
        results['decision_quality'] = decision_quality
        
        # 生成場景摘要
        scenario_summary = self._generate_scenario_summary(handover_events, decision_quality)
        results['scenario_summary'] = scenario_summary
        
        return results
    
    def _calculate_visibility_timeline(self, satellites: List[Dict], time_steps: List[datetime]) -> Dict[str, Any]:
        """
        計算衛星可見性時間線
        """
        print("📡 計算衛星可見性時間線...")
        
        timeline = {
            'timestamps': [t.isoformat() for t in time_steps],
            'satellite_visibility': {},
            'visible_count_per_time': [],
            'max_elevation_per_time': []
        }
        
        for sat_data in satellites:
            sat_name = sat_data.get('name', f"SAT-{sat_data.get('norad_id', 'unknown')}")
            sat_visibility = []
            
            try:
                inclination = float(sat_data['INCLINATION'])
                raan = float(sat_data['RA_OF_ASC_NODE'])
                mean_motion = float(sat_data['MEAN_MOTION'])
                mean_anomaly = float(sat_data['MEAN_ANOMALY'])
                
                for i, timestamp in enumerate(time_steps):
                    # 簡化的軌道計算
                    visibility_info = self._calculate_satellite_position_simplified(
                        inclination, raan, mean_motion, mean_anomaly, timestamp, i
                    )
                    sat_visibility.append(visibility_info)
                
                timeline['satellite_visibility'][sat_name] = sat_visibility
                
            except Exception as e:
                print(f"⚠️ 衛星 {sat_name} 計算錯誤: {e}")
                continue
        
        # 計算每個時間點的可見衛星數量和最大仰角
        for i in range(len(time_steps)):
            visible_sats = 0
            max_elevation = 0
            
            for sat_name, visibility_data in timeline['satellite_visibility'].items():
                if i < len(visibility_data) and visibility_data[i]['visible']:
                    visible_sats += 1
                    max_elevation = max(max_elevation, visibility_data[i]['elevation'])
            
            timeline['visible_count_per_time'].append(visible_sats)
            timeline['max_elevation_per_time'].append(max_elevation)
        
        return timeline
    
    def _calculate_satellite_position_simplified(self, inclination: float, raan: float, 
                                               mean_motion: float, mean_anomaly: float,
                                               timestamp: datetime, time_index: int) -> Dict[str, Any]:
        """
        簡化的衛星位置計算
        """
        # 計算時間差（分鐘）
        minutes_elapsed = time_index * 5
        
        # 更新平近點角
        current_mean_anomaly = (mean_anomaly + mean_motion * minutes_elapsed / (24 * 60) * 360) % 360
        
        # 簡化的位置計算（假設圓軌道）
        # 這裡使用簡化模型，實際應該使用SGP4
        orbital_radius = 7000  # 假設 LEO 軌道半徑 700km
        
        # 計算地心坐標
        true_anomaly = current_mean_anomaly  # 簡化：忽略離心率影響
        
        # 軌道平面坐標
        x_orbital = orbital_radius * math.cos(math.radians(true_anomaly))
        y_orbital = orbital_radius * math.sin(math.radians(true_anomaly))
        z_orbital = 0
        
        # 轉換到地心坐標系（簡化版）
        # 考慮傾角和升交點赤經
        inc_rad = math.radians(inclination)
        raan_rad = math.radians(raan)
        
        # 地心直角坐標
        x_geo = x_orbital * math.cos(raan_rad) - y_orbital * math.cos(inc_rad) * math.sin(raan_rad)
        y_geo = x_orbital * math.sin(raan_rad) + y_orbital * math.cos(inc_rad) * math.cos(raan_rad)
        z_geo = y_orbital * math.sin(inc_rad)
        
        # 轉換為地理坐標（緯度、經度、高度）
        # 避免數學域錯誤
        z_normalized = max(-0.99, min(0.99, z_geo / orbital_radius))
        lat_sat = math.degrees(math.asin(z_normalized))
        lon_sat = math.degrees(math.atan2(y_geo, x_geo))
        alt_sat = orbital_radius - self.earth_radius
        
        # 計算方位角和仰角
        azimuth, elevation = self._calculate_look_angles(lat_sat, lon_sat, alt_sat)
        
        # 計算距離
        distance = self._calculate_distance(lat_sat, lon_sat, alt_sat)
        
        # 判斷是否可見
        visible = elevation >= self.elevation_thresholds['critical']
        
        return {
            'timestamp': timestamp.isoformat(),
            'satellite_lat': lat_sat,
            'satellite_lon': lon_sat,
            'satellite_alt': alt_sat,
            'azimuth': azimuth,
            'elevation': elevation,
            'distance': distance,
            'visible': visible,
            'threshold_status': self._get_threshold_status(elevation)
        }
    
    def _calculate_look_angles(self, sat_lat: float, sat_lon: float, sat_alt: float) -> Tuple[float, float]:
        """
        計算方位角和仰角
        """
        # 將度轉換為弧度
        lat1_rad = math.radians(self.target_lat)
        lon1_rad = math.radians(self.target_lon)
        lat2_rad = math.radians(sat_lat)
        lon2_rad = math.radians(sat_lon)
        
        # 計算方位角
        dlon = lon2_rad - lon1_rad
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        azimuth = math.degrees(math.atan2(y, x))
        azimuth = (azimuth + 360) % 360  # 確保為正值
        
        # 計算距離
        distance = self._calculate_distance(sat_lat, sat_lon, sat_alt)
        
        # 計算仰角
        earth_center_angle = math.acos((self.earth_radius**2 + distance**2 - (self.earth_radius + sat_alt)**2) / (2 * self.earth_radius * distance))
        elevation = 90 - math.degrees(earth_center_angle)
        
        return azimuth, elevation
    
    def _calculate_distance(self, sat_lat: float, sat_lon: float, sat_alt: float) -> float:
        """
        計算到衛星的距離
        """
        # 使用球面距離公式
        lat1_rad = math.radians(self.target_lat)
        lon1_rad = math.radians(self.target_lon)
        lat2_rad = math.radians(sat_lat)
        lon2_rad = math.radians(sat_lon)
        
        # Haversine 公式
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        surface_distance = self.earth_radius * c
        
        # 3D 距離
        distance = math.sqrt(surface_distance**2 + sat_alt**2)
        
        return distance
    
    def _get_threshold_status(self, elevation: float) -> str:
        """
        獲取仰角門檻狀態
        """
        if elevation >= self.elevation_thresholds['preparation']:
            return 'preparation'
        elif elevation >= self.elevation_thresholds['execution']:
            return 'execution'
        elif elevation >= self.elevation_thresholds['critical']:
            return 'critical'
        else:
            return 'below_horizon'
    
    def _identify_handover_events(self, visibility_timeline: Dict, time_steps: List[datetime]) -> List[Dict[str, Any]]:
        """
        識別換手事件
        """
        print("🔄 識別換手事件...")
        
        handover_events = []
        
        # 分析每個時間步的衛星變化
        for i in range(1, len(time_steps)):
            current_time = time_steps[i]
            
            # 獲取當前和前一時刻的可見衛星
            current_visible = self._get_visible_satellites(visibility_timeline, i)
            previous_visible = self._get_visible_satellites(visibility_timeline, i-1)
            
            # 檢測新出現的衛星
            new_satellites = current_visible - previous_visible
            lost_satellites = previous_visible - current_visible
            
            # 如果有衛星變化，記錄換手事件
            if new_satellites or lost_satellites:
                # 選擇最佳服務衛星
                best_satellite = self._select_best_satellite(visibility_timeline, i)
                
                handover_event = {
                    'timestamp': current_time.isoformat(),
                    'time_index': i,
                    'event_type': 'handover',
                    'new_satellites': list(new_satellites),
                    'lost_satellites': list(lost_satellites),
                    'total_visible': len(current_visible),
                    'selected_satellite': best_satellite,
                    'decision_reason': self._get_selection_reason(visibility_timeline, i, best_satellite)
                }
                
                handover_events.append(handover_event)
        
        return handover_events
    
    def _get_visible_satellites(self, visibility_timeline: Dict, time_index: int) -> set:
        """
        獲取指定時間的可見衛星集合
        """
        visible_sats = set()
        
        for sat_name, visibility_data in visibility_timeline['satellite_visibility'].items():
            if time_index < len(visibility_data) and visibility_data[time_index]['visible']:
                visible_sats.add(sat_name)
        
        return visible_sats
    
    def _select_best_satellite(self, visibility_timeline: Dict, time_index: int) -> str:
        """
        選擇最佳服務衛星
        """
        best_satellite = None
        best_elevation = -1
        
        for sat_name, visibility_data in visibility_timeline['satellite_visibility'].items():
            if time_index < len(visibility_data) and visibility_data[time_index]['visible']:
                elevation = visibility_data[time_index]['elevation']
                if elevation > best_elevation:
                    best_elevation = elevation
                    best_satellite = sat_name
        
        return best_satellite or "none"
    
    def _get_selection_reason(self, visibility_timeline: Dict, time_index: int, selected_satellite: str) -> str:
        """
        獲取選擇理由
        """
        if selected_satellite == "none":
            return "No visible satellites"
        
        if selected_satellite in visibility_timeline['satellite_visibility']:
            visibility_data = visibility_timeline['satellite_visibility'][selected_satellite]
            if time_index < len(visibility_data):
                elevation = visibility_data[time_index]['elevation']
                return f"Highest elevation: {elevation:.1f}°"
        
        return "Unknown"
    
    def _evaluate_decision_quality(self, handover_events: List[Dict], visibility_timeline: Dict) -> Dict[str, Any]:
        """
        評估決策品質
        """
        print("📊 評估換手決策品質...")
        
        if not handover_events:
            return {
                'total_events': 0,
                'quality_score': 0,
                'average_elevation': 0,
                'handover_frequency': 0,
                'decision_rationale': 'No handover events detected'
            }
        
        quality_metrics = {
            'total_events': len(handover_events),
            'successful_handovers': 0,
            'elevation_scores': [],
            'timing_scores': [],
            'decision_rationale': []
        }
        
        for event in handover_events:
            # 評估仰角品質
            selected_sat = event['selected_satellite']
            time_index = event['time_index']
            
            if (selected_sat != "none" and 
                selected_sat in visibility_timeline['satellite_visibility'] and
                time_index < len(visibility_timeline['satellite_visibility'][selected_sat])):
                
                elevation = visibility_timeline['satellite_visibility'][selected_sat][time_index]['elevation']
                quality_metrics['elevation_scores'].append(elevation)
                
                # 評估為成功換手如果仰角 >= 10°
                if elevation >= self.elevation_thresholds['execution']:
                    quality_metrics['successful_handovers'] += 1
                
                # 記錄決策理由
                quality_metrics['decision_rationale'].append(event['decision_reason'])
        
        # 計算綜合品質分數
        avg_elevation = np.mean(quality_metrics['elevation_scores']) if quality_metrics['elevation_scores'] else 0
        success_rate = quality_metrics['successful_handovers'] / len(handover_events) if handover_events else 0
        
        quality_score = (avg_elevation / 90) * 0.6 + success_rate * 0.4  # 加權評分
        
        return {
            'total_events': quality_metrics['total_events'],
            'successful_handovers': quality_metrics['successful_handovers'],
            'success_rate': success_rate * 100,
            'quality_score': quality_score * 100,
            'average_elevation': avg_elevation,
            'handover_frequency': len(handover_events) / 24,  # 每小時換手次數
            'decision_rationale': quality_metrics['decision_rationale'][:5]  # 前5個決策理由
        }
    
    def _generate_scenario_summary(self, handover_events: List[Dict], decision_quality: Dict) -> Dict[str, Any]:
        """
        生成場景摘要
        """
        summary = {
            'handover_feasibility': 'unknown',
            'scenario_realism': 'unknown',
            'training_value': 'unknown',
            'key_findings': [],
            'recommendations': []
        }
        
        total_events = decision_quality['total_events']
        quality_score = decision_quality['quality_score']
        success_rate = decision_quality.get('success_rate', 0)
        
        # 評估換手可行性
        if total_events >= 10 and quality_score >= 70:
            summary['handover_feasibility'] = 'excellent'
        elif total_events >= 5 and quality_score >= 50:
            summary['handover_feasibility'] = 'good'
        elif total_events >= 2 and quality_score >= 30:
            summary['handover_feasibility'] = 'acceptable'
        else:
            summary['handover_feasibility'] = 'poor'
        
        # 評估場景真實性
        if success_rate >= 80 and decision_quality['average_elevation'] >= 25:
            summary['scenario_realism'] = 'high'
        elif success_rate >= 60 and decision_quality['average_elevation'] >= 15:
            summary['scenario_realism'] = 'medium'
        else:
            summary['scenario_realism'] = 'low'
        
        # 評估訓練價值
        if (summary['handover_feasibility'] in ['excellent', 'good'] and 
            summary['scenario_realism'] in ['high', 'medium']):
            summary['training_value'] = 'high'
        elif summary['handover_feasibility'] == 'acceptable':
            summary['training_value'] = 'medium'
        else:
            summary['training_value'] = 'low'
        
        # 關鍵發現
        summary['key_findings'] = [
            f"24小時內發生 {total_events} 次換手事件",
            f"換手成功率: {success_rate:.1f}%",
            f"平均仰角: {decision_quality['average_elevation']:.1f}°",
            f"換手頻率: {decision_quality['handover_frequency']:.1f} 次/小時"
        ]
        
        # 建議
        if summary['training_value'] == 'high':
            summary['recommendations'].append("衛星篩選品質優秀，適合進行強化學習訓練")
        elif summary['training_value'] == 'medium':
            summary['recommendations'].append("考慮增加更多極地軌道衛星以提高換手頻率")
        else:
            summary['recommendations'].append("需要重新調整篩選參數以改善換手場景品質")
        
        return summary

def main():
    """主要測試程序"""
    
    # 載入 TLE 數據並執行篩選
    tle_dir = Path("/home/sat/ntn-stack/netstack/tle_data")
    filter_system = RLOptimizedSatelliteFilter()
    tester = RealHandoverScenarioTester()
    
    print("🛰️ 測試真實衛星換手場景")
    print(f"📍 目標座標: {tester.target_lat:.4f}°N, {tester.target_lon:.4f}°E")
    print(f"🎯 仰角門檻: {tester.elevation_thresholds}")
    
    # 測試 Starlink 篩選結果
    starlink_file = tle_dir / "starlink/json/starlink_20250731.json"
    if starlink_file.exists():
        with open(starlink_file, 'r') as f:
            starlink_data = json.load(f)
        
        # 執行篩選
        starlink_results = filter_system.filter_constellation(starlink_data, "starlink")
        accepted_starlink = starlink_results['accepted']
        
        print(f"\n📡 Starlink 換手場景測試:")
        print(f"  篩選後衛星數量: {len(accepted_starlink)}")
        
        # 測試換手場景
        handover_results = tester.test_handover_scenarios(accepted_starlink, test_duration_hours=6)
        
        print(f"\n📊 換手場景測試結果:")
        print(f"  測試時長: {handover_results['test_parameters']['test_duration_hours']} 小時")
        print(f"  換手事件總數: {handover_results['decision_quality']['total_events']}")
        print(f"  成功換手次數: {handover_results['decision_quality']['successful_handovers']}")
        print(f"  換手成功率: {handover_results['decision_quality']['success_rate']:.1f}%")
        print(f"  品質分數: {handover_results['decision_quality']['quality_score']:.1f}")
        print(f"  平均仰角: {handover_results['decision_quality']['average_elevation']:.1f}°")
        print(f"  換手頻率: {handover_results['decision_quality']['handover_frequency']:.1f} 次/小時")
        
        summary = handover_results['scenario_summary']
        print(f"\n💡 場景評估:")
        print(f"  換手可行性: {summary['handover_feasibility']}")
        print(f"  場景真實性: {summary['scenario_realism']}")
        print(f"  訓練價值: {summary['training_value']}")
        
        print(f"\n🔍 關鍵發現:")
        for finding in summary['key_findings']:
            print(f"    - {finding}")
        
        print(f"\n📋 建議:")
        for recommendation in summary['recommendations']:
            print(f"    - {recommendation}")

if __name__ == "__main__":
    main()