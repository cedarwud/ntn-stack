#!/usr/bin/env python3
"""
動態場景衛星設計分析
基於真實軌道數據計算場景中需要的衛星總數
考慮衛星進入/離開換手區域的動態過程
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from skyfield.api import load, EarthSatellite, wgs84

class DynamicSceneSatelliteDesign:
    def __init__(self):
        self.NTPU_LAT = 24.9441667
        self.NTPU_LON = 121.3713889
        
        # 換手仰角門檻設計 (基於學術研究)
        self.elevation_thresholds = {
            'starlink': {
                'handover_active': 15,    # 可換手區域 ≥15°
                'tracking_zone': 10,      # 追蹤區域 10-15°  
                'prediction_zone': 5,     # 預測區域 5-10°
                'scene_horizon': 0        # 場景地平線 ≥0°
            },
            'oneweb': {
                'handover_active': 10,    # 可換手區域 ≥10°
                'tracking_zone': 7,       # 追蹤區域 7-10°
                'prediction_zone': 4,     # 預測區域 4-7°  
                'scene_horizon': 0        # 場景地平線 ≥0°
            }
        }
        
        # 學術研究目標候選數 (基於per.md)
        self.target_candidates = {
            'starlink': {
                'active_handover': 8,     # 當前可換手 8顆
                'total_scene': None       # 場景總數 (待計算)
            },
            'oneweb': {
                'active_handover': 5,     # 當前可換手 5顆  
                'total_scene': None       # 場景總數 (待計算)
            }
        }
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # TLE數據
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        self.starlink_satellites = []
        self.oneweb_satellites = []
        
        print("🎬 動態場景衛星設計分析系統")
        print("📍 基於真實軌道數據的場景衛星數量設計")
        
    def load_satellite_data(self):
        """載入衛星數據"""
        print("\n📡 載入最新衛星軌道數據...")
        
        starlink_tle_path = f"{self.tle_base_path}/starlink/tle/starlink_20250808.tle"
        oneweb_tle_path = f"{self.tle_base_path}/oneweb/tle/oneweb_20250808.tle"
        
        self.starlink_satellites = self._parse_tle_file(starlink_tle_path, "Starlink")
        self.oneweb_satellites = self._parse_tle_file(oneweb_tle_path, "OneWeb")
        
        print(f"✅ 載入 {len(self.starlink_satellites)} 顆 Starlink")
        print(f"✅ 載入 {len(self.oneweb_satellites)} 顆 OneWeb")
        
    def _parse_tle_file(self, tle_path, constellation):
        """解析TLE文件"""
        satellites = []
        
        try:
            with open(tle_path, 'r') as f:
                lines = f.readlines()
            
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    try:
                        sat = EarthSatellite(line1, line2, name, self.ts)
                        satellites.append({
                            'name': name,
                            'satellite': sat,
                            'constellation': constellation
                        })
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"❌ 載入失敗 {tle_path}: {e}")
            
        return satellites
    
    def analyze_satellite_lifecycle(self, constellation, analysis_duration_hours=3):
        """分析衛星生命週期 - 進入/停留/離開換手區域"""
        print(f"\n🔄 分析 {constellation.title()} 衛星動態生命週期...")
        
        satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
        thresholds = self.elevation_thresholds[constellation]
        
        start_time = datetime.now(timezone.utc)
        sample_interval_minutes = 5  # 5分鐘採樣
        num_samples = int(analysis_duration_hours * 60 / sample_interval_minutes)
        
        lifecycle_analysis = {
            'time_points': [],
            'elevation_zones': {
                'handover_active': [],      # ≥換手仰角
                'tracking_zone': [],        # 換手仰角到追蹤仰角
                'prediction_zone': [],      # 追蹤仰角到預測仰角
                'approaching': [],          # 0°到預測仰角 (即將進入)
                'total_visible': []         # 所有≥0°衛星
            },
            'transition_events': {
                'entering_handover': [],    # 進入換手區域
                'leaving_handover': [],     # 離開換手區域
                'entering_scene': [],       # 進入場景 (升起)
                'leaving_scene': []         # 離開場景 (下沉)
            }
        }
        
        previous_states = {}  # 記錄上一次的狀態
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval_minutes)
            t = self.ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
            
            lifecycle_analysis['time_points'].append(current_time)
            
            # 當前時刻的衛星分布
            current_distribution = {
                'handover_active': [],
                'tracking_zone': [],
                'prediction_zone': [], 
                'approaching': [],
                'total_visible': []
            }
            
            # 分析每顆衛星
            for sat_data in satellites:
                try:
                    satellite = sat_data['satellite']
                    difference = satellite - self.ntpu
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    sat_info = {
                        'name': sat_data['name'],
                        'elevation': alt.degrees,
                        'azimuth': az.degrees,
                        'distance': distance.km
                    }
                    
                    # 分類到不同區域
                    if alt.degrees >= thresholds['handover_active']:
                        current_distribution['handover_active'].append(sat_info)
                    elif alt.degrees >= thresholds['tracking_zone']:
                        current_distribution['tracking_zone'].append(sat_info)
                    elif alt.degrees >= thresholds['prediction_zone']:
                        current_distribution['prediction_zone'].append(sat_info)
                    elif alt.degrees >= thresholds['scene_horizon']:
                        current_distribution['approaching'].append(sat_info)
                    
                    if alt.degrees >= 0:
                        current_distribution['total_visible'].append(sat_info)
                    
                    # 檢測轉換事件
                    sat_name = sat_data['name']
                    if sat_name in previous_states:
                        prev_elev = previous_states[sat_name]
                        curr_elev = alt.degrees
                        
                        # 進入換手區域
                        if prev_elev < thresholds['handover_active'] and curr_elev >= thresholds['handover_active']:
                            lifecycle_analysis['transition_events']['entering_handover'].append({
                                'time': current_time,
                                'satellite': sat_name,
                                'elevation': curr_elev
                            })
                        
                        # 離開換手區域  
                        if prev_elev >= thresholds['handover_active'] and curr_elev < thresholds['handover_active']:
                            lifecycle_analysis['transition_events']['leaving_handover'].append({
                                'time': current_time,
                                'satellite': sat_name,
                                'elevation': curr_elev
                            })
                        
                        # 進入場景 (升起)
                        if prev_elev < 0 and curr_elev >= 0:
                            lifecycle_analysis['transition_events']['entering_scene'].append({
                                'time': current_time,
                                'satellite': sat_name,
                                'elevation': curr_elev
                            })
                        
                        # 離開場景 (下沉)
                        if prev_elev >= 0 and curr_elev < 0:
                            lifecycle_analysis['transition_events']['leaving_scene'].append({
                                'time': current_time,
                                'satellite': sat_name,
                                'elevation': curr_elev
                            })
                    
                    # 更新狀態記錄
                    previous_states[sat_name] = alt.degrees
                    
                except Exception:
                    continue
            
            # 記錄當前分布
            for zone, sats in current_distribution.items():
                lifecycle_analysis['elevation_zones'][zone].append(len(sats))
            
            if (i + 1) % 12 == 0:  # 每小時報告一次
                progress = (i + 1) / num_samples * 100
                print(f"  進度: {progress:.1f}% - 時間: {current_time.strftime('%H:%M')} "
                      f"- 可換手: {len(current_distribution['handover_active'])}, "
                      f"場景總計: {len(current_distribution['total_visible'])}")
        
        return lifecycle_analysis
    
    def calculate_scene_requirements(self, lifecycle_data, constellation):
        """計算場景衛星需求"""
        print(f"\n📊 計算 {constellation.title()} 場景衛星需求...")
        
        target_active = self.target_candidates[constellation]['active_handover']
        
        # 統計數據
        handover_counts = lifecycle_data['elevation_zones']['handover_active']
        tracking_counts = lifecycle_data['elevation_zones']['tracking_zone']  
        prediction_counts = lifecycle_data['elevation_zones']['prediction_zone']
        approaching_counts = lifecycle_data['elevation_zones']['approaching']
        total_counts = lifecycle_data['elevation_zones']['total_visible']
        
        # 計算統計量
        stats = {
            'handover_active': {
                'min': min(handover_counts),
                'max': max(handover_counts),
                'mean': np.mean(handover_counts),
                'std': np.std(handover_counts)
            },
            'tracking_zone': {
                'min': min(tracking_counts),
                'max': max(tracking_counts), 
                'mean': np.mean(tracking_counts),
                'std': np.std(tracking_counts)
            },
            'prediction_zone': {
                'min': min(prediction_counts),
                'max': max(prediction_counts),
                'mean': np.mean(prediction_counts),
                'std': np.std(prediction_counts)
            },
            'approaching': {
                'min': min(approaching_counts),
                'max': max(approaching_counts),
                'mean': np.mean(approaching_counts),
                'std': np.std(approaching_counts)
            },
            'total_scene': {
                'min': min(total_counts),
                'max': max(total_counts),
                'mean': np.mean(total_counts),
                'std': np.std(total_counts)
            }
        }
        
        # 分析轉換事件頻率
        transition_stats = {}
        for event_type, events in lifecycle_data['transition_events'].items():
            transition_stats[event_type] = {
                'count': len(events),
                'frequency_per_hour': len(events) / 3  # 3小時分析
            }
        
        # 計算場景設計需求
        scene_requirements = self._calculate_optimal_scene_size(
            stats, target_active, constellation, transition_stats
        )
        
        return {
            'statistics': stats,
            'transition_events': transition_stats,
            'scene_requirements': scene_requirements,
            'target_active_handover': target_active
        }
    
    def _calculate_optimal_scene_size(self, stats, target_active, constellation, transitions):
        """計算最佳場景規模"""
        
        # 當前可換手衛星統計
        current_handover_mean = stats['handover_active']['mean']
        current_handover_std = stats['handover_active']['std']
        
        # 如果當前可換手數量不足目標，需要從其他區域補充
        if current_handover_mean < target_active:
            shortage = target_active - current_handover_mean
            print(f"   ⚠️ 可換手衛星不足: 平均{current_handover_mean:.1f}顆 < 目標{target_active}顆")
            print(f"   📋 需要從其他區域補充: {shortage:.1f}顆")
        else:
            shortage = 0
            print(f"   ✅ 可換手衛星充足: 平均{current_handover_mean:.1f}顆 ≥ 目標{target_active}顆")
        
        # 計算緩衝區需求
        entering_rate = transitions['entering_handover']['frequency_per_hour']
        leaving_rate = transitions['leaving_handover']['frequency_per_hour']
        
        print(f"   🔄 換手區域轉換頻率: 進入{entering_rate:.1f}/小時, 離開{leaving_rate:.1f}/小時")
        
        # 場景設計建議
        tracking_buffer = max(3, int(stats['tracking_zone']['mean']))  # 追蹤緩衝區
        prediction_buffer = max(2, int(stats['prediction_zone']['mean'] * 0.5))  # 預測緩衝區
        
        recommended_scene_size = {
            'handover_active': max(target_active, int(current_handover_mean + current_handover_std)),
            'tracking_zone': tracking_buffer,
            'prediction_zone': prediction_buffer,
            'total_scene': 0  # 將在下面計算
        }
        
        recommended_scene_size['total_scene'] = (
            recommended_scene_size['handover_active'] + 
            recommended_scene_size['tracking_zone'] + 
            recommended_scene_size['prediction_zone']
        )
        
        # 與實際統計對比
        actual_total_mean = stats['total_scene']['mean']
        
        return {
            'recommended': recommended_scene_size,
            'actual_available': {
                'handover_active': current_handover_mean,
                'total_scene': actual_total_mean
            },
            'feasibility': {
                'handover_achievable': current_handover_mean >= target_active * 0.8,
                'scene_size_reasonable': recommended_scene_size['total_scene'] <= actual_total_mean,
                'buffer_adequate': tracking_buffer >= 2 and prediction_buffer >= 2
            },
            'transition_dynamics': {
                'entering_rate_per_hour': entering_rate,
                'leaving_rate_per_hour': leaving_rate,
                'turnover_stability': abs(entering_rate - leaving_rate) < 2
            }
        }
    
    def generate_comprehensive_report(self, starlink_analysis, oneweb_analysis):
        """生成綜合設計報告"""
        print(f"\n" + "="*80)
        print(f"🎬 動態場景衛星設計 - 綜合分析報告")
        print(f"="*80)
        print(f"📍 基於真實軌道數據的NTPU場景設計")
        print(f"🎯 目標: 符合學術研究標準的動態場景")
        
        # Starlink設計建議
        print(f"\n🚀 Starlink 動態場景設計")
        print(f"─────────────────────────────────────────────────")
        
        starlink_req = starlink_analysis['scene_requirements']['recommended']
        starlink_stats = starlink_analysis['statistics']
        
        print(f"   學術研究目標: {starlink_analysis['target_active_handover']}顆可換手衛星")
        print(f"   實際可用統計: {starlink_stats['handover_active']['mean']:.1f}±{starlink_stats['handover_active']['std']:.1f}顆")
        
        print(f"\n   📋 推薦場景設計:")
        print(f"      可換手區域 (≥15°): {starlink_req['handover_active']}顆")
        print(f"      追蹤區域 (10-15°): {starlink_req['tracking_zone']}顆")  
        print(f"      預測區域 (5-10°): {starlink_req['prediction_zone']}顆")
        print(f"      場景總計: {starlink_req['total_scene']}顆")
        
        # OneWeb設計建議
        print(f"\n🛰️ OneWeb 動態場景設計")
        print(f"─────────────────────────────────────────────────")
        
        oneweb_req = oneweb_analysis['scene_requirements']['recommended']
        oneweb_stats = oneweb_analysis['statistics']
        
        print(f"   學術研究目標: {oneweb_analysis['target_active_handover']}顆可換手衛星")
        print(f"   實際可用統計: {oneweb_stats['handover_active']['mean']:.1f}±{oneweb_stats['handover_active']['std']:.1f}顆")
        
        print(f"\n   📋 推薦場景設計:")
        print(f"      可換手區域 (≥10°): {oneweb_req['handover_active']}顆")
        print(f"      追蹤區域 (7-10°): {oneweb_req['tracking_zone']}顆")
        print(f"      預測區域 (4-7°): {oneweb_req['prediction_zone']}顆") 
        print(f"      場景總計: {oneweb_req['total_scene']}顆")
        
        # 可行性分析
        print(f"\n✅ 設計可行性分析")
        print(f"─────────────────────────────────────────────────")
        
        starlink_feasible = starlink_analysis['scene_requirements']['feasibility']
        oneweb_feasible = oneweb_analysis['scene_requirements']['feasibility']
        
        print(f"   Starlink設計可行性:")
        print(f"      換手目標可達成: {'✅' if starlink_feasible['handover_achievable'] else '❌'}")
        print(f"      場景規模合理: {'✅' if starlink_feasible['scene_size_reasonable'] else '❌'}")
        print(f"      緩衝區充足: {'✅' if starlink_feasible['buffer_adequate'] else '❌'}")
        
        print(f"   OneWeb設計可行性:")
        print(f"      換手目標可達成: {'✅' if oneweb_feasible['handover_achievable'] else '❌'}")
        print(f"      場景規模合理: {'✅' if oneweb_feasible['scene_size_reasonable'] else '❌'}")
        print(f"      緩衝區充足: {'✅' if oneweb_feasible['buffer_adequate'] else '❌'}")
        
        # 動態特性分析
        print(f"\n🔄 動態場景特性")
        print(f"─────────────────────────────────────────────────")
        
        starlink_dynamics = starlink_analysis['scene_requirements']['transition_dynamics']
        oneweb_dynamics = oneweb_analysis['scene_requirements']['transition_dynamics']
        
        print(f"   Starlink動態特性:")
        print(f"      進入換手區: {starlink_dynamics['entering_rate_per_hour']:.1f}顆/小時")
        print(f"      離開換手區: {starlink_dynamics['leaving_rate_per_hour']:.1f}顆/小時")
        print(f"      流動穩定性: {'✅' if starlink_dynamics['turnover_stability'] else '⚠️'}")
        
        print(f"   OneWeb動態特性:")
        print(f"      進入換手區: {oneweb_dynamics['entering_rate_per_hour']:.1f}顆/小時")
        print(f"      離開換手區: {oneweb_dynamics['leaving_rate_per_hour']:.1f}顆/小時")
        print(f"      流動穩定性: {'✅' if oneweb_dynamics['turnover_stability'] else '⚠️'}")
        
        # 最終設計建議
        print(f"\n💡 最終場景設計建議")
        print(f"─────────────────────────────────────────────────")
        
        final_design = {
            'starlink': {
                'scene_total': starlink_req['total_scene'],
                'handover_active': starlink_req['handover_active'],
                'buffer_zones': starlink_req['tracking_zone'] + starlink_req['prediction_zone']
            },
            'oneweb': {
                'scene_total': oneweb_req['total_scene'],
                'handover_active': oneweb_req['handover_active'], 
                'buffer_zones': oneweb_req['tracking_zone'] + oneweb_req['prediction_zone']
            }
        }
        
        print(f"   🚀 Starlink場景配置:")
        print(f"      場景總衛星數: {final_design['starlink']['scene_total']}顆")
        print(f"      其中可換手: {final_design['starlink']['handover_active']}顆 (符合學術目標)")
        print(f"      緩衝區衛星: {final_design['starlink']['buffer_zones']}顆 (動態補充)")
        
        print(f"   🛰️ OneWeb場景配置:")
        print(f"      場景總衛星數: {final_design['oneweb']['scene_total']}顆")
        print(f"      其中可換手: {final_design['oneweb']['handover_active']}顆 (符合學術目標)")
        print(f"      緩衝區衛星: {final_design['oneweb']['buffer_zones']}顆 (動態補充)")
        
        return final_design

def main():
    """主執行函數"""
    print("🎬 啟動動態場景衛星設計分析")
    
    analyzer = DynamicSceneSatelliteDesign()
    
    # 載入衛星數據
    analyzer.load_satellite_data()
    
    # 分析Starlink生命週期 (3小時動態分析)
    starlink_lifecycle = analyzer.analyze_satellite_lifecycle('starlink', analysis_duration_hours=3)
    starlink_analysis = analyzer.calculate_scene_requirements(starlink_lifecycle, 'starlink')
    
    # 分析OneWeb生命週期
    oneweb_lifecycle = analyzer.analyze_satellite_lifecycle('oneweb', analysis_duration_hours=3)
    oneweb_analysis = analyzer.calculate_scene_requirements(oneweb_lifecycle, 'oneweb')
    
    # 生成綜合報告
    final_design = analyzer.generate_comprehensive_report(starlink_analysis, oneweb_analysis)
    
    # 保存結果
    output = {
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'elevation_thresholds': analyzer.elevation_thresholds,
        'target_candidates': analyzer.target_candidates,
        'starlink_analysis': {
            'lifecycle_stats': starlink_analysis['statistics'],
            'transition_events': starlink_analysis['transition_events'],
            'scene_requirements': starlink_analysis['scene_requirements']
        },
        'oneweb_analysis': {
            'lifecycle_stats': oneweb_analysis['statistics'], 
            'transition_events': oneweb_analysis['transition_events'],
            'scene_requirements': oneweb_analysis['scene_requirements']
        },
        'final_design': final_design
    }
    
    with open('dynamic_scene_satellite_design.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析結果已保存至: dynamic_scene_satellite_design.json")
    print(f"🎉 動態場景設計分析完成!")
    
    return analyzer, final_design

if __name__ == "__main__":
    analyzer, design = main()