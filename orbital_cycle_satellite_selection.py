#!/usr/bin/env python3
"""
完整軌道週期衛星池選擇分析
基於真實歷史數據確保任何時刻都有足夠的可換手和緩衝衛星
分析完整軌道週期 (Starlink 96分鐘, OneWeb 109分鐘)
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from skyfield.api import load, EarthSatellite, wgs84
from skyfield.timelib import Time

class OrbitalCycleSatelliteSelection:
    def __init__(self):
        self.NTPU_LAT = 24.9441667
        self.NTPU_LON = 121.3713889
        
        # 軌道週期 (分鐘)
        self.orbital_periods = {
            'starlink': 96,    # ~96分鐘軌道週期
            'oneweb': 109      # ~109分鐘軌道週期
        }
        
        # 學術研究目標
        self.research_targets = {
            'starlink': {
                'handover_candidates': 8,      # 可換手候選
                'tracking_buffer': 5,          # 追蹤緩衝 (即將可換手)
                'prediction_buffer': 5,        # 預測緩衝 (即將升起)
                'total_scene_target': 18       # 場景總目標
            },
            'oneweb': {
                'handover_candidates': 5,      # 可換手候選
                'tracking_buffer': 3,          # 追蹤緩衝
                'prediction_buffer': 2,        # 預測緩衝 
                'total_scene_target': 10       # 場景總目標
            }
        }
        
        # 仰角門檻 (度)
        self.elevation_thresholds = {
            'starlink': {
                'handover': 15,    # 可換手門檻
                'tracking': 10,    # 追蹤門檻
                'prediction': 5,   # 預測門檻
                'horizon': 0       # 地平線
            },
            'oneweb': {
                'handover': 10,    # 可換手門檻 (OneWeb較低)
                'tracking': 7,     # 追蹤門檻
                'prediction': 4,   # 預測門檻
                'horizon': 0       # 地平線
            }
        }
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # TLE數據
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        self.starlink_satellites = []
        self.oneweb_satellites = []
        
        print("🔄 完整軌道週期衛星池選擇分析系統")
        print("📍 基於真實歷史數據的動態平衡設計")
        
    def load_satellite_data(self):
        """載入衛星數據"""
        print("\n📡 載入衛星軌道數據...")
        
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
                            'constellation': constellation,
                            'participation_score': 0,  # 參與度分數
                            'max_elevation': 0,        # 最大仰角
                            'visibility_time': 0       # 可見時間
                        })
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"❌ 載入失敗 {tle_path}: {e}")
            
        return satellites
    
    def analyze_full_orbital_cycle(self, constellation):
        """分析完整軌道週期"""
        print(f"\n🔄 分析 {constellation.title()} 完整軌道週期...")
        
        satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
        orbital_period = self.orbital_periods[constellation]
        thresholds = self.elevation_thresholds[constellation]
        targets = self.research_targets[constellation]
        
        # 分析時間範圍: 2個完整軌道週期 + 緩衝
        analysis_duration = orbital_period * 2 + 30  # 分鐘
        sample_interval = 3  # 3分鐘採樣間隔
        num_samples = int(analysis_duration / sample_interval)
        
        print(f"   ⏱️ 分析時長: {analysis_duration}分鐘 (~{analysis_duration/60:.1f}小時)")
        print(f"   📊 採樣間隔: {sample_interval}分鐘")
        print(f"   🎯 目標: {targets['handover_candidates']}可換手+{targets['tracking_buffer']}追蹤+{targets['prediction_buffer']}預測")
        
        start_time = datetime.now(timezone.utc)
        
        # 記錄每個時間點的衛星狀態
        cycle_analysis = {
            'time_points': [],
            'satellite_states': [],  # 每個時間點的衛星狀態
            'zone_counts': {
                'handover': [],
                'tracking': [],
                'prediction': [], 
                'approaching': [],
                'total_visible': []
            },
            'satellite_participation': {}  # 每顆衛星的參與統計
        }
        
        # 初始化衛星參與統計
        for sat_data in satellites:
            cycle_analysis['satellite_participation'][sat_data['name']] = {
                'handover_times': 0,
                'tracking_times': 0,
                'prediction_times': 0,
                'max_elevation_seen': 0,
                'total_visible_time': 0,
                'elevation_history': []
            }
        
        print(f"   🚀 開始完整週期分析...")
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval)
            t = self.ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
            
            cycle_analysis['time_points'].append(current_time)
            
            # 當前時刻的衛星狀態
            current_state = {
                'handover_zone': [],      # 可換手區域衛星
                'tracking_zone': [],      # 追蹤區域衛星
                'prediction_zone': [],    # 預測區域衛星
                'approaching': [],        # 地平線上即將進入
                'total_visible': []       # 全部可見衛星
            }
            
            # 分析每顆衛星在當前時刻的狀態
            for sat_data in satellites:
                try:
                    satellite = sat_data['satellite']
                    difference = satellite - self.ntpu
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    elevation = alt.degrees
                    
                    # 記錄衛星信息
                    sat_info = {
                        'name': sat_data['name'],
                        'elevation': elevation,
                        'azimuth': az.degrees,
                        'distance': distance.km
                    }
                    
                    # 更新衛星參與統計
                    participation = cycle_analysis['satellite_participation'][sat_data['name']]
                    participation['elevation_history'].append(elevation)
                    participation['max_elevation_seen'] = max(participation['max_elevation_seen'], elevation)
                    
                    # 分類到不同區域
                    if elevation >= thresholds['handover']:
                        current_state['handover_zone'].append(sat_info)
                        participation['handover_times'] += 1
                    elif elevation >= thresholds['tracking']:
                        current_state['tracking_zone'].append(sat_info)
                        participation['tracking_times'] += 1
                    elif elevation >= thresholds['prediction']:
                        current_state['prediction_zone'].append(sat_info)
                        participation['prediction_times'] += 1
                    elif elevation >= thresholds['horizon']:
                        current_state['approaching'].append(sat_info)
                    
                    if elevation >= 0:
                        current_state['total_visible'].append(sat_info)
                        participation['total_visible_time'] += sample_interval
                        
                except Exception:
                    continue
            
            # 記錄當前狀態
            cycle_analysis['satellite_states'].append(current_state)
            
            # 記錄區域計數
            cycle_analysis['zone_counts']['handover'].append(len(current_state['handover_zone']))
            cycle_analysis['zone_counts']['tracking'].append(len(current_state['tracking_zone']))
            cycle_analysis['zone_counts']['prediction'].append(len(current_state['prediction_zone']))
            cycle_analysis['zone_counts']['approaching'].append(len(current_state['approaching']))
            cycle_analysis['zone_counts']['total_visible'].append(len(current_state['total_visible']))
            
            # 進度報告
            if (i + 1) % 20 == 0:  # 每60分鐘報告一次
                progress = (i + 1) / num_samples * 100
                elapsed_hours = (i + 1) * sample_interval / 60
                print(f"     進度: {progress:.1f}% ({elapsed_hours:.1f}h) "
                      f"- 可換手: {len(current_state['handover_zone'])}, "
                      f"總可見: {len(current_state['total_visible'])}")
        
        return cycle_analysis
    
    def calculate_satellite_scores(self, cycle_analysis, constellation):
        """計算衛星選擇分數"""
        print(f"\n📊 計算 {constellation.title()} 衛星選擇分數...")
        
        targets = self.research_targets[constellation]
        participation_data = cycle_analysis['satellite_participation']
        
        satellite_scores = {}
        
        for sat_name, stats in participation_data.items():
            # 計算綜合分數
            score_components = {
                'handover_frequency': stats['handover_times'],           # 可換手頻率
                'max_elevation': stats['max_elevation_seen'],           # 最大仰角
                'total_visibility': stats['total_visible_time'],        # 總可見時間
                'tracking_participation': stats['tracking_times'],      # 追蹤區參與
                'elevation_stability': self._calculate_stability(stats['elevation_history'])  # 仰角穩定性
            }
            
            # 加權計算總分數
            weights = {
                'handover_frequency': 0.4,      # 40% - 最重要
                'max_elevation': 0.25,          # 25% - 信號品質
                'total_visibility': 0.15,       # 15% - 服務時間
                'tracking_participation': 0.15, # 15% - 緩衝貢獻
                'elevation_stability': 0.05     # 5% - 穩定性
            }
            
            total_score = sum(
                score_components[component] * weights[component] 
                for component in weights.keys()
            )
            
            satellite_scores[sat_name] = {
                'total_score': total_score,
                'components': score_components,
                'rank': 0  # 將在排序後設置
            }
        
        # 排序並設置排名
        sorted_satellites = sorted(satellite_scores.items(), 
                                 key=lambda x: x[1]['total_score'], 
                                 reverse=True)
        
        for rank, (sat_name, score_data) in enumerate(sorted_satellites, 1):
            satellite_scores[sat_name]['rank'] = rank
        
        print(f"   📋 完成 {len(satellite_scores)} 顆衛星評分")
        print(f"   🏆 前5名衛星:")
        for i, (sat_name, score_data) in enumerate(sorted_satellites[:5]):
            print(f"      {i+1}. {sat_name}: {score_data['total_score']:.2f}分")
        
        return satellite_scores
    
    def _calculate_stability(self, elevation_history):
        """計算仰角穩定性分數"""
        if len(elevation_history) < 2:
            return 0
        
        # 計算仰角變化的標準差 (越小越穩定)
        std_dev = np.std(elevation_history)
        # 轉換為0-100分數 (標準差越小分數越高)
        stability_score = max(0, 100 - std_dev * 2)
        return stability_score
    
    def select_optimal_satellite_pool(self, satellite_scores, constellation):
        """選擇最佳衛星池"""
        print(f"\n🎯 選擇 {constellation.title()} 最佳衛星池...")
        
        targets = self.research_targets[constellation]
        
        # 按分數排序
        sorted_satellites = sorted(satellite_scores.items(),
                                 key=lambda x: x[1]['total_score'],
                                 reverse=True)
        
        # 選擇衛星池
        selected_pool = {
            'primary_handover': [],      # 主要換手候選
            'tracking_buffer': [],       # 追蹤緩衝
            'prediction_buffer': [],     # 預測緩衝
            'total_pool': []            # 總衛星池
        }
        
        # 分配衛星到不同類別
        total_needed = targets['total_scene_target']
        handover_needed = targets['handover_candidates']
        tracking_needed = targets['tracking_buffer']
        prediction_needed = targets['prediction_buffer']
        
        # 選擇最佳的衛星作為主要換手候選
        for i in range(min(handover_needed, len(sorted_satellites))):
            sat_name, score_data = sorted_satellites[i]
            selected_pool['primary_handover'].append({
                'name': sat_name,
                'score': score_data['total_score'],
                'rank': i + 1,
                'role': 'primary_handover'
            })
        
        # 選擇追蹤緩衝衛星
        start_idx = handover_needed
        for i in range(start_idx, min(start_idx + tracking_needed, len(sorted_satellites))):
            sat_name, score_data = sorted_satellites[i]
            selected_pool['tracking_buffer'].append({
                'name': sat_name,
                'score': score_data['total_score'],
                'rank': i + 1,
                'role': 'tracking_buffer'
            })
        
        # 選擇預測緩衝衛星
        start_idx = handover_needed + tracking_needed
        for i in range(start_idx, min(start_idx + prediction_needed, len(sorted_satellites))):
            sat_name, score_data = sorted_satellites[i]
            selected_pool['prediction_buffer'].append({
                'name': sat_name,
                'score': score_data['total_score'],
                'rank': i + 1,
                'role': 'prediction_buffer'
            })
        
        # 組合總衛星池
        selected_pool['total_pool'] = (
            selected_pool['primary_handover'] + 
            selected_pool['tracking_buffer'] + 
            selected_pool['prediction_buffer']
        )
        
        # 驗證選擇結果
        selection_summary = {
            'total_selected': len(selected_pool['total_pool']),
            'handover_selected': len(selected_pool['primary_handover']),
            'tracking_selected': len(selected_pool['tracking_buffer']),
            'prediction_selected': len(selected_pool['prediction_buffer']),
            'target_achievement': {
                'handover': len(selected_pool['primary_handover']) >= handover_needed,
                'tracking': len(selected_pool['tracking_buffer']) >= tracking_needed * 0.8,
                'prediction': len(selected_pool['prediction_buffer']) >= prediction_needed * 0.8,
                'total': len(selected_pool['total_pool']) <= total_needed
            }
        }
        
        print(f"   📋 衛星池選擇結果:")
        print(f"      主要換手: {selection_summary['handover_selected']}/{handover_needed}顆")
        print(f"      追蹤緩衝: {selection_summary['tracking_selected']}/{tracking_needed}顆")
        print(f"      預測緩衝: {selection_summary['prediction_selected']}/{prediction_needed}顆")
        print(f"      總計: {selection_summary['total_selected']}/{total_needed}顆")
        
        return selected_pool, selection_summary
    
    def validate_dynamic_balance(self, cycle_analysis, selected_pool, constellation):
        """驗證動態平衡性"""
        print(f"\n✅ 驗證 {constellation.title()} 動態平衡性...")
        
        targets = self.research_targets[constellation]
        thresholds = self.elevation_thresholds[constellation]
        
        # 獲取選中衛星的名稱列表
        selected_names = [sat['name'] for sat in selected_pool['total_pool']]
        
        # 分析每個時間點的表現
        balance_validation = {
            'time_coverage': [],
            'handover_availability': [],
            'buffer_adequacy': [],
            'critical_moments': [],  # 不滿足目標的時刻
            'success_rate': 0
        }
        
        successful_timepoints = 0
        total_timepoints = len(cycle_analysis['time_points'])
        
        for i, state in enumerate(cycle_analysis['satellite_states']):
            time_point = cycle_analysis['time_points'][i]
            
            # 只考慮選中的衛星
            selected_handover = [sat for sat in state['handover_zone'] 
                               if sat['name'] in selected_names]
            selected_tracking = [sat for sat in state['tracking_zone'] 
                               if sat['name'] in selected_names]
            selected_prediction = [sat for sat in state['prediction_zone'] 
                                 if sat['name'] in selected_names]
            
            # 檢查是否滿足目標
            handover_ok = len(selected_handover) >= targets['handover_candidates']
            tracking_ok = len(selected_tracking) >= targets['tracking_buffer'] * 0.7  # 70%容忍度
            prediction_ok = len(selected_prediction) >= targets['prediction_buffer'] * 0.7
            
            overall_ok = handover_ok and (tracking_ok or prediction_ok)  # 緩衝區至少一個OK
            
            if overall_ok:
                successful_timepoints += 1
            else:
                balance_validation['critical_moments'].append({
                    'time': time_point,
                    'handover_count': len(selected_handover),
                    'tracking_count': len(selected_tracking),
                    'prediction_count': len(selected_prediction),
                    'deficiency': 'handover' if not handover_ok else 'buffer'
                })
            
            balance_validation['handover_availability'].append(len(selected_handover))
        
        # 計算成功率
        balance_validation['success_rate'] = successful_timepoints / total_timepoints
        
        # 統計分析
        handover_stats = {
            'min': min(balance_validation['handover_availability']),
            'max': max(balance_validation['handover_availability']),
            'mean': np.mean(balance_validation['handover_availability']),
            'std': np.std(balance_validation['handover_availability'])
        }
        
        print(f"   📊 動態平衡驗證結果:")
        print(f"      成功率: {balance_validation['success_rate']:.1%}")
        print(f"      可換手衛星: {handover_stats['min']}-{handover_stats['max']}顆 (平均{handover_stats['mean']:.1f})")
        print(f"      關鍵時刻: {len(balance_validation['critical_moments'])}個")
        
        if balance_validation['success_rate'] >= 0.95:
            print(f"      ✅ 動態平衡優秀 (成功率≥95%)")
        elif balance_validation['success_rate'] >= 0.85:
            print(f"      ⚠️ 動態平衡良好 (成功率≥85%)")
        else:
            print(f"      ❌ 動態平衡不足 (成功率<85%)")
        
        return balance_validation, handover_stats
    
    def generate_final_report(self, starlink_results, oneweb_results):
        """生成最終報告"""
        print(f"\n" + "="*80)
        print(f"🔄 完整軌道週期衛星池選擇 - 最終報告")
        print(f"="*80)
        print(f"📍 基於真實歷史數據的動態平衡設計")
        
        # Starlink結果
        starlink_pool = starlink_results['selected_pool']
        starlink_balance = starlink_results['balance_validation']
        
        print(f"\n🚀 Starlink 衛星池設計")
        print(f"─────────────────────────────────────────────────")
        print(f"   📋 選中衛星池:")
        print(f"      主要換手候選: {len(starlink_pool['primary_handover'])}顆")
        print(f"      追蹤緩衝衛星: {len(starlink_pool['tracking_buffer'])}顆")
        print(f"      預測緩衝衛星: {len(starlink_pool['prediction_buffer'])}顆")
        print(f"      總衛星池: {len(starlink_pool['total_pool'])}顆")
        
        print(f"   ✅ 動態平衡表現:")
        print(f"      成功率: {starlink_balance[0]['success_rate']:.1%}")
        print(f"      可換手範圍: {starlink_balance[1]['min']}-{starlink_balance[1]['max']}顆")
        print(f"      平均可換手: {starlink_balance[1]['mean']:.1f}顆")
        
        # OneWeb結果
        oneweb_pool = oneweb_results['selected_pool']
        oneweb_balance = oneweb_results['balance_validation']
        
        print(f"\n🛰️ OneWeb 衛星池設計")
        print(f"─────────────────────────────────────────────────")
        print(f"   📋 選中衛星池:")
        print(f"      主要換手候選: {len(oneweb_pool['primary_handover'])}顆")
        print(f"      追蹤緩衝衛星: {len(oneweb_pool['tracking_buffer'])}顆")
        print(f"      預測緩衝衛星: {len(oneweb_pool['prediction_buffer'])}顆")
        print(f"      總衛星池: {len(oneweb_pool['total_pool'])}顆")
        
        print(f"   ✅ 動態平衡表現:")
        print(f"      成功率: {oneweb_balance[0]['success_rate']:.1%}")
        print(f"      可換手範圍: {oneweb_balance[1]['min']}-{oneweb_balance[1]['max']}顆")
        print(f"      平均可換手: {oneweb_balance[1]['mean']:.1f}顆")
        
        # 總結建議
        print(f"\n💡 最終衛星池建議")
        print(f"─────────────────────────────────────────────────")
        
        final_recommendations = {
            'starlink': {
                'total_pool_size': len(starlink_pool['total_pool']),
                'satellite_names': [sat['name'] for sat in starlink_pool['total_pool']],
                'dynamic_balance_score': starlink_balance[0]['success_rate'],
                'recommended': starlink_balance[0]['success_rate'] >= 0.85
            },
            'oneweb': {
                'total_pool_size': len(oneweb_pool['total_pool']),
                'satellite_names': [sat['name'] for sat in oneweb_pool['total_pool']],
                'dynamic_balance_score': oneweb_balance[0]['success_rate'],
                'recommended': oneweb_balance[0]['success_rate'] >= 0.85
            }
        }
        
        print(f"   🚀 Starlink推薦: {len(starlink_pool['total_pool'])}顆衛星池")
        print(f"      動態平衡: {starlink_balance[0]['success_rate']:.1%} {'✅' if final_recommendations['starlink']['recommended'] else '⚠️'}")
        
        print(f"   🛰️ OneWeb推薦: {len(oneweb_pool['total_pool'])}顆衛星池")
        print(f"      動態平衡: {oneweb_balance[0]['success_rate']:.1%} {'✅' if final_recommendations['oneweb']['recommended'] else '⚠️'}")
        
        # 衛星名單
        print(f"\n📋 具體衛星名單:")
        print(f"   Starlink池 ({len(starlink_pool['total_pool'])}顆):")
        for i, sat in enumerate(starlink_pool['total_pool'][:10], 1):  # 顯示前10顆
            print(f"      {i}. {sat['name']} ({sat['role']}) - 分數:{sat['score']:.2f}")
        if len(starlink_pool['total_pool']) > 10:
            print(f"      ... 等共{len(starlink_pool['total_pool'])}顆")
        
        print(f"   OneWeb池 ({len(oneweb_pool['total_pool'])}顆):")
        for i, sat in enumerate(oneweb_pool['total_pool'], 1):
            print(f"      {i}. {sat['name']} ({sat['role']}) - 分數:{sat['score']:.2f}")
        
        return final_recommendations

def main():
    """主執行函數"""
    print("🔄 啟動完整軌道週期衛星池選擇分析")
    
    analyzer = OrbitalCycleSatelliteSelection()
    
    # 載入衛星數據
    analyzer.load_satellite_data()
    
    # 分析Starlink完整週期
    print("\n" + "="*60)
    print("🚀 Starlink 完整週期分析")
    print("="*60)
    
    starlink_cycle = analyzer.analyze_full_orbital_cycle('starlink')
    starlink_scores = analyzer.calculate_satellite_scores(starlink_cycle, 'starlink')
    starlink_pool, starlink_summary = analyzer.select_optimal_satellite_pool(starlink_scores, 'starlink')
    starlink_balance = analyzer.validate_dynamic_balance(starlink_cycle, starlink_pool, 'starlink')
    
    # 分析OneWeb完整週期
    print("\n" + "="*60)
    print("🛰️ OneWeb 完整週期分析")
    print("="*60)
    
    oneweb_cycle = analyzer.analyze_full_orbital_cycle('oneweb')
    oneweb_scores = analyzer.calculate_satellite_scores(oneweb_cycle, 'oneweb')
    oneweb_pool, oneweb_summary = analyzer.select_optimal_satellite_pool(oneweb_scores, 'oneweb')
    oneweb_balance = analyzer.validate_dynamic_balance(oneweb_cycle, oneweb_pool, 'oneweb')
    
    # 整合結果
    starlink_results = {
        'cycle_analysis': starlink_cycle,
        'satellite_scores': starlink_scores,
        'selected_pool': starlink_pool,
        'selection_summary': starlink_summary,
        'balance_validation': starlink_balance
    }
    
    oneweb_results = {
        'cycle_analysis': oneweb_cycle,
        'satellite_scores': oneweb_scores,
        'selected_pool': oneweb_pool,
        'selection_summary': oneweb_summary,
        'balance_validation': oneweb_balance
    }
    
    # 生成最終報告
    final_recommendations = analyzer.generate_final_report(starlink_results, oneweb_results)
    
    # 保存結果 (簡化版避免JSON序列化問題)
    output = {
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'orbital_periods': analyzer.orbital_periods,
        'research_targets': analyzer.research_targets,
        'elevation_thresholds': analyzer.elevation_thresholds,
        'final_recommendations': final_recommendations,
        'starlink': {
            'selected_satellites': [sat['name'] for sat in starlink_pool['total_pool']],
            'pool_size': len(starlink_pool['total_pool']),
            'balance_success_rate': float(starlink_balance[0]['success_rate']),
            'handover_stats': {k: float(v) for k, v in starlink_balance[1].items()}
        },
        'oneweb': {
            'selected_satellites': [sat['name'] for sat in oneweb_pool['total_pool']], 
            'pool_size': len(oneweb_pool['total_pool']),
            'balance_success_rate': float(oneweb_balance[0]['success_rate']),
            'handover_stats': {k: float(v) for k, v in oneweb_balance[1].items()}
        }
    }
    
    with open('orbital_cycle_satellite_selection.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析結果已保存至: orbital_cycle_satellite_selection.json")
    print(f"🎉 完整軌道週期分析完成!")
    
    return analyzer, final_recommendations

if __name__ == "__main__":
    analyzer, recommendations = main()