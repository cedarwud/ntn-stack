#!/usr/bin/env python3
"""
優化衛星池選擇器
基於時間窗口、空間分佈和動態互補性的智能衛星選擇算法
確保任何時刻都有足夠的可換手衛星
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from skyfield.api import load, EarthSatellite, wgs84
import itertools

class OptimizedSatellitePoolSelector:
    def __init__(self):
        self.NTPU_LAT = 24.9441667
        self.NTPU_LON = 121.3713889
        
        # 軌道週期和分析參數
        self.orbital_periods = {
            'starlink': 96,    # 96分鐘軌道週期
            'oneweb': 109      # 109分鐘軌道週期
        }
        
        # 學術研究目標 (修正為實際可達成的數量)
        self.research_targets = {
            'starlink': {
                'min_handover_always': 8,      # 任何時刻至少8顆可換手
                'optimal_handover': 10,        # 最佳狀態10顆可換手  
                'total_pool_size': 25          # 總衛星池大小
            },
            'oneweb': {
                'min_handover_always': 5,      # 任何時刻至少5顆可換手
                'optimal_handover': 7,         # 最佳狀態7顆可換手
                'total_pool_size': 15          # 總衛星池大小
            }
        }
        
        # 仰角門檻
        self.elevation_thresholds = {
            'starlink': {'handover': 15, 'tracking': 10, 'prediction': 5},
            'oneweb': {'handover': 10, 'tracking': 7, 'prediction': 4}
        }
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # 衛星數據
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        self.starlink_satellites = []
        self.oneweb_satellites = []
        
        print("🎯 優化衛星池選擇器")
        print("🧠 基於時間窗口和空間分佈的智能選擇算法")
        
    def load_satellite_data(self):
        """載入衛星數據"""
        print("\n📡 載入衛星數據...")
        
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
    
    def analyze_time_window_coverage(self, constellation, window_duration_hours=4):
        """分析時間窗口覆蓋"""
        print(f"\n🕒 分析 {constellation.title()} 時間窗口覆蓋...")
        
        satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
        thresholds = self.elevation_thresholds[constellation]
        targets = self.research_targets[constellation]
        
        # 分析時間參數
        window_duration_minutes = window_duration_hours * 60
        sample_interval = 5  # 5分鐘採樣
        num_samples = int(window_duration_minutes / sample_interval)
        
        start_time = datetime.now(timezone.utc)
        
        print(f"   ⏱️ 時間窗口: {window_duration_hours}小時")
        print(f"   📊 採樣間隔: {sample_interval}分鐘")
        print(f"   🎯 目標: 任何時刻≥{targets['min_handover_always']}顆可換手")
        
        # 記錄每個時間點每顆衛星的狀態
        time_window_data = {
            'time_points': [],
            'satellite_visibility_matrix': {},  # 衛星名 -> [時間點的仰角列表]
            'handover_availability_matrix': {}  # 衛星名 -> [是否可換手的布林列表]
        }
        
        # 初始化矩陣
        for sat_data in satellites:
            sat_name = sat_data['name']
            time_window_data['satellite_visibility_matrix'][sat_name] = []
            time_window_data['handover_availability_matrix'][sat_name] = []
        
        print(f"   🚀 開始時間窗口分析...")
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval)
            t = self.ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
            
            time_window_data['time_points'].append(current_time)
            
            # 分析每顆衛星在當前時刻的狀態
            for sat_data in satellites:
                try:
                    satellite = sat_data['satellite']
                    difference = satellite - self.ntpu
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    elevation = alt.degrees
                    is_handover_ready = elevation >= thresholds['handover']
                    
                    # 記錄到矩陣
                    sat_name = sat_data['name']
                    time_window_data['satellite_visibility_matrix'][sat_name].append(elevation)
                    time_window_data['handover_availability_matrix'][sat_name].append(is_handover_ready)
                    
                except Exception:
                    # 發生錯誤時記錄為不可見
                    sat_name = sat_data['name']
                    time_window_data['satellite_visibility_matrix'][sat_name].append(-90)
                    time_window_data['handover_availability_matrix'][sat_name].append(False)
            
            # 進度報告
            if (i + 1) % 24 == 0:  # 每2小時報告一次
                progress = (i + 1) / num_samples * 100
                elapsed_hours = (i + 1) * sample_interval / 60
                
                # 計算當前時刻的可換手衛星數
                current_handover_count = sum(
                    time_window_data['handover_availability_matrix'][sat_data['name']][-1]
                    for sat_data in satellites
                )
                
                print(f"     進度: {progress:.1f}% ({elapsed_hours:.1f}h) "
                      f"- 當前可換手: {current_handover_count}顆")
        
        print(f"   ✅ 時間窗口分析完成")
        
        return time_window_data
    
    def find_optimal_satellite_combinations(self, time_window_data, constellation):
        """尋找最佳衛星組合"""
        print(f"\n🧩 尋找 {constellation.title()} 最佳衛星組合...")
        
        targets = self.research_targets[constellation]
        handover_matrix = time_window_data['handover_availability_matrix']
        num_timepoints = len(time_window_data['time_points'])
        
        # 計算每顆衛星的基本統計
        satellite_stats = {}
        for sat_name, availability_list in handover_matrix.items():
            handover_count = sum(availability_list)
            handover_ratio = handover_count / num_timepoints
            
            satellite_stats[sat_name] = {
                'handover_count': handover_count,
                'handover_ratio': handover_ratio,
                'coverage_score': handover_count * handover_ratio  # 綜合分數
            }
        
        # 按覆蓋分數排序，選出候選衛星
        sorted_satellites = sorted(satellite_stats.items(), 
                                 key=lambda x: x[1]['coverage_score'], 
                                 reverse=True)
        
        # 初步篩選：選出前N顆作為候選池
        candidate_pool_size = min(targets['total_pool_size'] * 3, len(sorted_satellites))  # 3倍候選池
        candidate_satellites = [sat_name for sat_name, _ in sorted_satellites[:candidate_pool_size]]
        
        print(f"   📋 候選衛星池: {len(candidate_satellites)}顆")
        print(f"   🎯 目標池大小: {targets['total_pool_size']}顆")
        
        # 使用貪婪算法尋找最佳組合
        optimal_combination = self._greedy_combination_search(
            candidate_satellites, handover_matrix, targets, num_timepoints
        )
        
        return optimal_combination, satellite_stats
    
    def _greedy_combination_search(self, candidate_satellites, handover_matrix, targets, num_timepoints):
        """貪婪算法搜尋最佳組合"""
        print(f"   🔍 執行貪婪搜尋算法...")
        
        selected_satellites = []
        min_handover_target = targets['min_handover_always']
        max_pool_size = targets['total_pool_size']
        
        # 貪婪選擇：每次添加能最大改善覆蓋的衛星
        while len(selected_satellites) < max_pool_size:
            best_candidate = None
            best_improvement = -1
            
            for candidate in candidate_satellites:
                if candidate in selected_satellites:
                    continue
                
                # 測試添加這顆衛星的效果
                test_combination = selected_satellites + [candidate]
                improvement_score = self._evaluate_combination_coverage(
                    test_combination, handover_matrix, min_handover_target, num_timepoints
                )
                
                if improvement_score > best_improvement:
                    best_improvement = improvement_score
                    best_candidate = candidate
            
            if best_candidate is None:
                print(f"   ⚠️ 無法找到更多改善衛星，當前選中: {len(selected_satellites)}顆")
                break
            
            selected_satellites.append(best_candidate)
            
            # 評估當前組合
            coverage_score = self._evaluate_combination_coverage(
                selected_satellites, handover_matrix, min_handover_target, num_timepoints
            )
            
            print(f"     添加 {best_candidate}, 總數: {len(selected_satellites)}, 覆蓋分數: {coverage_score:.3f}")
            
            # 如果達到完美覆蓋，可以提前結束
            if coverage_score >= 0.95:  # 95%時間滿足目標
                print(f"   🎉 達到優秀覆蓋 (≥95%)，停止搜尋")
                break
        
        # 最終評估
        final_coverage = self._detailed_coverage_analysis(
            selected_satellites, handover_matrix, min_handover_target, num_timepoints
        )
        
        return {
            'selected_satellites': selected_satellites,
            'coverage_analysis': final_coverage,
            'selection_quality': 'excellent' if final_coverage['success_rate'] >= 0.95 
                               else 'good' if final_coverage['success_rate'] >= 0.85 
                               else 'needs_improvement'
        }
    
    def _evaluate_combination_coverage(self, satellite_combination, handover_matrix, min_target, num_timepoints):
        """評估衛星組合的覆蓋表現"""
        if not satellite_combination:
            return 0
        
        successful_timepoints = 0
        
        for t in range(num_timepoints):
            # 計算在時間點t，這個組合有多少顆衛星可換手
            handover_count = sum(
                handover_matrix[sat_name][t] for sat_name in satellite_combination
            )
            
            if handover_count >= min_target:
                successful_timepoints += 1
        
        return successful_timepoints / num_timepoints
    
    def _detailed_coverage_analysis(self, satellite_combination, handover_matrix, min_target, num_timepoints):
        """詳細覆蓋分析"""
        successful_timepoints = 0
        handover_counts = []
        critical_moments = []
        
        for t in range(num_timepoints):
            handover_count = sum(
                handover_matrix[sat_name][t] for sat_name in satellite_combination
            )
            handover_counts.append(handover_count)
            
            if handover_count >= min_target:
                successful_timepoints += 1
            else:
                critical_moments.append({
                    'timepoint': t,
                    'handover_count': handover_count,
                    'shortage': min_target - handover_count
                })
        
        return {
            'success_rate': successful_timepoints / num_timepoints,
            'handover_stats': {
                'min': min(handover_counts),
                'max': max(handover_counts),
                'mean': np.mean(handover_counts),
                'std': np.std(handover_counts)
            },
            'critical_moments_count': len(critical_moments),
            'critical_moments': critical_moments[:5]  # 只保留前5個關鍵時刻
        }
    
    def validate_spatial_distribution(self, selected_satellites, time_window_data, constellation):
        """驗證空間分佈"""
        print(f"\n🌍 驗證 {constellation.title()} 空間分佈...")
        
        visibility_matrix = time_window_data['satellite_visibility_matrix']
        time_points = time_window_data['time_points']
        
        # 分析方位角分佈
        azimuth_sectors = {
            'North': (315, 45),    # 315° - 45°
            'East': (45, 135),     # 45° - 135°
            'South': (135, 225),   # 135° - 225°
            'West': (225, 315)     # 225° - 315°
        }
        
        sector_coverage = {sector: [] for sector in azimuth_sectors.keys()}
        
        # 分析每個時間點的空間覆蓋
        for t_idx, current_time in enumerate(time_points[::12]):  # 每小時取樣
            t = self.ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
            
            satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
            current_sectors = {sector: 0 for sector in azimuth_sectors.keys()}
            
            for sat_data in satellites:
                if sat_data['name'] not in selected_satellites:
                    continue
                
                try:
                    satellite = sat_data['satellite']
                    difference = satellite - self.ntpu
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    if alt.degrees >= self.elevation_thresholds[constellation]['handover']:
                        azimuth = az.degrees
                        
                        # 判斷屬於哪個方位扇區
                        for sector, (min_az, max_az) in azimuth_sectors.items():
                            if min_az > max_az:  # 跨越0度的情況 (North sector)
                                if azimuth >= min_az or azimuth <= max_az:
                                    current_sectors[sector] += 1
                                    break
                            else:
                                if min_az <= azimuth <= max_az:
                                    current_sectors[sector] += 1
                                    break
                                    
                except Exception:
                    continue
            
            for sector in azimuth_sectors.keys():
                sector_coverage[sector].append(current_sectors[sector])
        
        # 計算空間分佈統計
        spatial_stats = {}
        for sector, counts in sector_coverage.items():
            if counts:
                spatial_stats[sector] = {
                    'mean': np.mean(counts),
                    'max': max(counts),
                    'coverage_ratio': sum(1 for c in counts if c > 0) / len(counts)
                }
            else:
                spatial_stats[sector] = {'mean': 0, 'max': 0, 'coverage_ratio': 0}
        
        # 評估空間分佈品質
        covered_sectors = sum(1 for stats in spatial_stats.values() if stats['coverage_ratio'] > 0.3)
        spatial_quality = 'excellent' if covered_sectors >= 3 else 'good' if covered_sectors >= 2 else 'needs_improvement'
        
        print(f"   📊 空間分佈分析:")
        for sector, stats in spatial_stats.items():
            print(f"      {sector}: 平均{stats['mean']:.1f}顆, 覆蓋率{stats['coverage_ratio']:.1%}")
        print(f"   🎯 空間品質: {spatial_quality}")
        
        return {
            'sector_statistics': spatial_stats,
            'spatial_quality': spatial_quality,
            'covered_sectors': covered_sectors
        }
    
    def generate_final_satellite_pool(self, constellation):
        """生成最終衛星池"""
        print(f"\n🎯 生成 {constellation.title()} 最終衛星池...")
        
        # Step 1: 時間窗口分析
        time_window_data = self.analyze_time_window_coverage(constellation)
        
        # Step 2: 尋找最佳組合
        optimal_result, satellite_stats = self.find_optimal_satellite_combinations(time_window_data, constellation)
        
        # Step 3: 驗證空間分佈
        spatial_analysis = self.validate_spatial_distribution(
            optimal_result['selected_satellites'], time_window_data, constellation
        )
        
        # Step 4: 整合結果
        final_pool_config = {
            'constellation': constellation,
            'selected_satellites': optimal_result['selected_satellites'],
            'pool_size': len(optimal_result['selected_satellites']),
            'performance_metrics': {
                'temporal_coverage': optimal_result['coverage_analysis'],
                'spatial_distribution': spatial_analysis,
                'selection_quality': optimal_result['selection_quality']
            },
            'satellite_details': []
        }
        
        # Step 5: 添加衛星詳細信息
        for sat_name in optimal_result['selected_satellites']:
            if sat_name in satellite_stats:
                stats = satellite_stats[sat_name]
                final_pool_config['satellite_details'].append({
                    'name': sat_name,
                    'handover_ratio': stats['handover_ratio'],
                    'coverage_score': stats['coverage_score']
                })
        
        return final_pool_config
    
    def comprehensive_validation(self, starlink_config, oneweb_config):
        """綜合驗證"""
        print(f"\n✅ 綜合驗證最終配置...")
        
        validation_results = {
            'starlink': self._validate_single_constellation(starlink_config),
            'oneweb': self._validate_single_constellation(oneweb_config),
            'overall_assessment': {}
        }
        
        # 整體評估
        starlink_quality = validation_results['starlink']['overall_quality']
        oneweb_quality = validation_results['oneweb']['overall_quality']
        
        validation_results['overall_assessment'] = {
            'starlink_ready': starlink_quality in ['excellent', 'good'],
            'oneweb_ready': oneweb_quality in ['excellent', 'good'],
            'research_readiness': 'ready' if (starlink_quality in ['excellent', 'good'] and 
                                            oneweb_quality in ['excellent', 'good']) else 'needs_improvement'
        }
        
        return validation_results
    
    def _validate_single_constellation(self, config):
        """單星座驗證"""
        temporal = config['performance_metrics']['temporal_coverage']
        spatial = config['performance_metrics']['spatial_distribution']
        
        # 時間覆蓋評分
        if temporal['success_rate'] >= 0.95:
            temporal_score = 'excellent'
        elif temporal['success_rate'] >= 0.85:
            temporal_score = 'good'
        else:
            temporal_score = 'needs_improvement'
        
        # 空間分佈評分
        spatial_score = spatial['spatial_quality']
        
        # 整體評分
        if temporal_score == 'excellent' and spatial_score in ['excellent', 'good']:
            overall_quality = 'excellent'
        elif temporal_score in ['excellent', 'good'] and spatial_score in ['good', 'excellent']:
            overall_quality = 'good'
        else:
            overall_quality = 'needs_improvement'
        
        return {
            'temporal_score': temporal_score,
            'spatial_score': spatial_score,
            'overall_quality': overall_quality,
            'success_rate': temporal['success_rate'],
            'pool_size': config['pool_size']
        }

def main():
    """主執行函數"""
    print("🎯 啟動優化衛星池選擇器")
    
    selector = OptimizedSatellitePoolSelector()
    
    # 載入數據
    selector.load_satellite_data()
    
    print(f"\n" + "="*70)
    print("🚀 Starlink 衛星池優化")
    print("="*70)
    
    # 生成Starlink衛星池
    starlink_config = selector.generate_final_satellite_pool('starlink')
    
    print(f"\n" + "="*70)
    print("🛰️ OneWeb 衛星池優化")
    print("="*70)
    
    # 生成OneWeb衛星池
    oneweb_config = selector.generate_final_satellite_pool('oneweb')
    
    # 綜合驗證
    validation_results = selector.comprehensive_validation(starlink_config, oneweb_config)
    
    # 生成最終報告
    print(f"\n" + "="*80)
    print("🎉 最終衛星池配置報告")
    print("="*80)
    
    print(f"\n🚀 Starlink 最終配置:")
    starlink_perf = starlink_config['performance_metrics']
    print(f"   衛星池大小: {starlink_config['pool_size']}顆")
    print(f"   時間覆蓋率: {starlink_perf['temporal_coverage']['success_rate']:.1%}")
    print(f"   空間品質: {starlink_perf['spatial_distribution']['spatial_quality']}")
    print(f"   整體評級: {validation_results['starlink']['overall_quality']}")
    
    print(f"\n🛰️ OneWeb 最終配置:")
    oneweb_perf = oneweb_config['performance_metrics']
    print(f"   衛星池大小: {oneweb_config['pool_size']}顆")
    print(f"   時間覆蓋率: {oneweb_perf['temporal_coverage']['success_rate']:.1%}")
    print(f"   空間品質: {oneweb_perf['spatial_distribution']['spatial_quality']}")
    print(f"   整體評級: {validation_results['oneweb']['overall_quality']}")
    
    print(f"\n🎯 研究準備度評估:")
    assessment = validation_results['overall_assessment']
    print(f"   Starlink準備: {'✅' if assessment['starlink_ready'] else '❌'}")
    print(f"   OneWeb準備: {'✅' if assessment['oneweb_ready'] else '❌'}")
    print(f"   整體準備度: {assessment['research_readiness']}")
    
    if assessment['research_readiness'] == 'ready':
        print(f"   🎉 系統已準備就緒，可用於LEO衛星換手強化學習研究！")
    else:
        print(f"   ⚠️ 系統需要進一步優化")
    
    # 詳細衛星名單
    print(f"\n📋 詳細衛星池名單:")
    
    print(f"\n   Starlink池 ({starlink_config['pool_size']}顆):")
    for i, sat_detail in enumerate(starlink_config['satellite_details'][:15], 1):  # 顯示前15顆
        print(f"      {i:2d}. {sat_detail['name']} - 覆蓋率{sat_detail['handover_ratio']:.1%}")
    if starlink_config['pool_size'] > 15:
        print(f"      ... 等共{starlink_config['pool_size']}顆")
    
    print(f"\n   OneWeb池 ({oneweb_config['pool_size']}顆):")
    for i, sat_detail in enumerate(oneweb_config['satellite_details'], 1):
        print(f"      {i:2d}. {sat_detail['name']} - 覆蓋率{sat_detail['handover_ratio']:.1%}")
    
    # 保存結果
    output = {
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'research_targets': selector.research_targets,
        'elevation_thresholds': selector.elevation_thresholds,
        'starlink_config': {
            'selected_satellites': starlink_config['selected_satellites'],
            'pool_size': starlink_config['pool_size'],
            'success_rate': float(starlink_config['performance_metrics']['temporal_coverage']['success_rate']),
            'spatial_quality': starlink_config['performance_metrics']['spatial_distribution']['spatial_quality']
        },
        'oneweb_config': {
            'selected_satellites': oneweb_config['selected_satellites'],
            'pool_size': oneweb_config['pool_size'],
            'success_rate': float(oneweb_config['performance_metrics']['temporal_coverage']['success_rate']),
            'spatial_quality': oneweb_config['performance_metrics']['spatial_distribution']['spatial_quality']
        },
        'validation_results': {
            'starlink_quality': validation_results['starlink']['overall_quality'],
            'oneweb_quality': validation_results['oneweb']['overall_quality'],
            'research_readiness': validation_results['overall_assessment']['research_readiness']
        }
    }
    
    with open('optimized_satellite_pools.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 完整配置已保存至: optimized_satellite_pools.json")
    print(f"🎯 優化衛星池選擇完成！")
    
    return selector, starlink_config, oneweb_config, validation_results

if __name__ == "__main__":
    selector, starlink_config, oneweb_config, validation_results = main()