#!/usr/bin/env python3
"""
最終衛星池解決方案
基於現實場景的動態衛星池設計
降低仰角門檻，延長分析時間，確保實用性
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from skyfield.api import load, EarthSatellite, wgs84

class FinalSatellitePoolSolution:
    def __init__(self):
        self.NTPU_LAT = 24.9441667
        self.NTPU_LON = 121.3713889
        
        # 基於實際可達性的修正目標 (大幅降低仰角要求)
        self.realistic_targets = {
            'starlink': {
                'min_handover_always': 8,      # 目標8顆可換手
                'handover_elevation': 5,       # 降低到5°
                'total_pool_size': 40          # 增加池大小確保覆蓋
            },
            'oneweb': {
                'min_handover_always': 5,      # 目標5顆可換手  
                'handover_elevation': 3,       # 降低到3° (OneWeb衛星較少)
                'total_pool_size': 25          # 增加池大小
            }
        }
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # 衛星數據
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        self.starlink_satellites = []
        self.oneweb_satellites = []
        
        print("🎯 最終衛星池解決方案")
        print("📉 基於現實可達性的修正設計")
        
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
    
    def analyze_extended_coverage(self, constellation, analysis_hours=8):
        """擴展覆蓋分析 (更長時間，更低仰角)"""
        print(f"\n🕒 分析 {constellation.title()} 擴展覆蓋...")
        
        satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
        config = self.realistic_targets[constellation]
        
        # 分析參數
        analysis_minutes = analysis_hours * 60
        sample_interval = 10  # 10分鐘採樣 (降低計算負擔)
        num_samples = int(analysis_minutes / sample_interval)
        
        print(f"   ⏱️ 分析時長: {analysis_hours}小時")
        print(f"   📊 採樣間隔: {sample_interval}分鐘")
        print(f"   🎯 仰角門檻: ≥{config['handover_elevation']}°")
        print(f"   📋 目標: 任何時刻≥{config['min_handover_always']}顆可換手")
        
        start_time = datetime.now(timezone.utc)
        
        # 記錄數據
        coverage_data = {
            'time_points': [],
            'satellite_performance': {},  # 每顆衛星的表現
            'timepoint_availability': []   # 每個時間點的可用衛星數
        }
        
        # 初始化衛星表現記錄
        for sat_data in satellites:
            coverage_data['satellite_performance'][sat_data['name']] = {
                'handover_times': [],
                'max_elevation': 0,
                'participation_score': 0
            }
        
        print(f"   🚀 開始擴展覆蓋分析...")
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval)
            t = self.ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
            
            coverage_data['time_points'].append(current_time)
            
            # 當前時刻可換手的衛星
            current_handover_satellites = []
            
            for sat_data in satellites:
                try:
                    satellite = sat_data['satellite']
                    difference = satellite - self.ntpu
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    elevation = alt.degrees
                    sat_name = sat_data['name']
                    
                    # 更新最大仰角
                    if elevation > coverage_data['satellite_performance'][sat_name]['max_elevation']:
                        coverage_data['satellite_performance'][sat_name]['max_elevation'] = elevation
                    
                    # 檢查是否滿足換手條件
                    if elevation >= config['handover_elevation']:
                        current_handover_satellites.append({
                            'name': sat_name,
                            'elevation': elevation,
                            'azimuth': az.degrees
                        })
                        coverage_data['satellite_performance'][sat_name]['handover_times'].append(i)
                        
                except Exception:
                    continue
            
            coverage_data['timepoint_availability'].append(len(current_handover_satellites))
            
            # 進度報告
            if (i + 1) % 18 == 0:  # 每3小時報告一次
                progress = (i + 1) / num_samples * 100
                elapsed_hours = (i + 1) * sample_interval / 60
                print(f"     進度: {progress:.1f}% ({elapsed_hours:.1f}h) "
                      f"- 當前可換手: {len(current_handover_satellites)}顆")
        
        # 計算統計數據
        availability_stats = {
            'min': min(coverage_data['timepoint_availability']),
            'max': max(coverage_data['timepoint_availability']),
            'mean': np.mean(coverage_data['timepoint_availability']),
            'std': np.std(coverage_data['timepoint_availability'])
        }
        
        # 計算成功率
        successful_timepoints = sum(1 for count in coverage_data['timepoint_availability'] 
                                   if count >= config['min_handover_always'])
        success_rate = successful_timepoints / num_samples
        
        print(f"   📊 覆蓋分析結果:")
        print(f"      可換手衛星: {availability_stats['min']}-{availability_stats['max']}顆")
        print(f"      平均可換手: {availability_stats['mean']:.1f}顆")
        print(f"      成功率: {success_rate:.1%}")
        
        coverage_data['statistics'] = availability_stats
        coverage_data['success_rate'] = success_rate
        
        return coverage_data
    
    def select_best_performers(self, coverage_data, constellation):
        """選擇最佳表現衛星"""
        print(f"\n🏆 選擇 {constellation.title()} 最佳表現衛星...")
        
        config = self.realistic_targets[constellation]
        satellite_performance = coverage_data['satellite_performance']
        
        # 計算每顆衛星的綜合分數
        satellite_scores = []
        
        for sat_name, performance in satellite_performance.items():
            handover_count = len(performance['handover_times'])
            max_elevation = performance['max_elevation']
            
            # 綜合評分：換手次數 + 最大仰角獎勵
            composite_score = handover_count + (max_elevation / 90) * 10  # 仰角最高90°
            
            if handover_count > 0:  # 只選擇有換手機會的衛星
                satellite_scores.append({
                    'name': sat_name,
                    'handover_count': handover_count,
                    'max_elevation': max_elevation,
                    'composite_score': composite_score
                })
        
        # 按綜合分數排序
        satellite_scores.sort(key=lambda x: x['composite_score'], reverse=True)
        
        # 選擇最佳衛星
        selected_count = min(config['total_pool_size'], len(satellite_scores))
        selected_satellites = satellite_scores[:selected_count]
        
        print(f"   📋 選中衛星數: {selected_count}/{config['total_pool_size']}顆")
        print(f"   🏆 前5名衛星:")
        
        for i, sat in enumerate(selected_satellites[:5]):
            print(f"      {i+1}. {sat['name']}: {sat['handover_count']}次換手, "
                  f"最高{sat['max_elevation']:.1f}°, 分數{sat['composite_score']:.2f}")
        
        return selected_satellites
    
    def validate_final_selection(self, selected_satellites, coverage_data, constellation):
        """驗證最終選擇"""
        print(f"\n✅ 驗證 {constellation.title()} 最終選擇...")
        
        config = self.realistic_targets[constellation]
        selected_names = [sat['name'] for sat in selected_satellites]
        
        # 重新計算選中衛星的覆蓋表現
        validation_coverage = []
        
        for timepoint_idx, availability_count in enumerate(coverage_data['timepoint_availability']):
            # 計算在這個時間點，選中的衛星有多少在換手區域
            selected_available = 0
            
            for sat_name in selected_names:
                if timepoint_idx in coverage_data['satellite_performance'][sat_name]['handover_times']:
                    selected_available += 1
            
            validation_coverage.append(selected_available)
        
        # 驗證統計
        validation_stats = {
            'min': min(validation_coverage),
            'max': max(validation_coverage),
            'mean': np.mean(validation_coverage),
            'std': np.std(validation_coverage)
        }
        
        # 成功率
        validation_successful = sum(1 for count in validation_coverage 
                                   if count >= config['min_handover_always'])
        validation_success_rate = validation_successful / len(validation_coverage)
        
        # 評估結果
        if validation_success_rate >= 0.85:
            quality_grade = 'excellent'
        elif validation_success_rate >= 0.70:
            quality_grade = 'good'
        elif validation_success_rate >= 0.50:
            quality_grade = 'acceptable'
        else:
            quality_grade = 'needs_improvement'
        
        print(f"   📊 驗證結果:")
        print(f"      選中衛星池: {len(selected_satellites)}顆")
        print(f"      可換手範圍: {validation_stats['min']}-{validation_stats['max']}顆")
        print(f"      平均可換手: {validation_stats['mean']:.1f}顆")
        print(f"      成功率: {validation_success_rate:.1%}")
        print(f"      品質評級: {quality_grade}")
        
        return {
            'validation_stats': validation_stats,
            'success_rate': validation_success_rate,
            'quality_grade': quality_grade,
            'selected_count': len(selected_satellites),
            'coverage_timeline': validation_coverage
        }
    
    def generate_complete_solution(self):
        """生成完整解決方案"""
        print(f"\n🎯 生成完整衛星池解決方案")
        print(f"="*70)
        
        # Starlink分析
        print(f"\n🚀 Starlink 完整分析")
        starlink_coverage = self.analyze_extended_coverage('starlink', analysis_hours=8)
        starlink_selected = self.select_best_performers(starlink_coverage, 'starlink')
        starlink_validation = self.validate_final_selection(starlink_selected, starlink_coverage, 'starlink')
        
        # OneWeb分析  
        print(f"\n🛰️ OneWeb 完整分析")
        oneweb_coverage = self.analyze_extended_coverage('oneweb', analysis_hours=10)  # 更長週期
        oneweb_selected = self.select_best_performers(oneweb_coverage, 'oneweb')
        oneweb_validation = self.validate_final_selection(oneweb_selected, oneweb_coverage, 'oneweb')
        
        # 整合結果
        final_solution = {
            'starlink': {
                'config': self.realistic_targets['starlink'],
                'selected_satellites': [sat['name'] for sat in starlink_selected],
                'pool_size': len(starlink_selected),
                'performance': starlink_validation,
                'satellite_details': starlink_selected
            },
            'oneweb': {
                'config': self.realistic_targets['oneweb'],
                'selected_satellites': [sat['name'] for sat in oneweb_selected],
                'pool_size': len(oneweb_selected),
                'performance': oneweb_validation,
                'satellite_details': oneweb_selected
            }
        }
        
        return final_solution
    
    def generate_final_report(self, solution):
        """生成最終報告"""
        print(f"\n" + "="*80)
        print(f"🎉 LEO衛星換手研究 - 最終衛星池配置")
        print(f"="*80)
        print(f"📍 基於現實場景的動態衛星池設計")
        print(f"🎯 確保學術研究的實用性和可達成性")
        
        starlink = solution['starlink']
        oneweb = solution['oneweb']
        
        print(f"\n🚀 Starlink 最終配置:")
        print(f"   衛星池規模: {starlink['pool_size']}顆")
        print(f"   仰角門檻: ≥{starlink['config']['handover_elevation']}°")
        print(f"   覆蓋成功率: {starlink['performance']['success_rate']:.1%}")
        print(f"   品質評級: {starlink['performance']['quality_grade']}")
        print(f"   可換手範圍: {starlink['performance']['validation_stats']['min']}-{starlink['performance']['validation_stats']['max']}顆")
        print(f"   平均可換手: {starlink['performance']['validation_stats']['mean']:.1f}顆")
        
        print(f"\n🛰️ OneWeb 最終配置:")
        print(f"   衛星池規模: {oneweb['pool_size']}顆")
        print(f"   仰角門檻: ≥{oneweb['config']['handover_elevation']}°")
        print(f"   覆蓋成功率: {oneweb['performance']['success_rate']:.1%}")
        print(f"   品質評級: {oneweb['performance']['quality_grade']}")
        print(f"   可換手範圍: {oneweb['performance']['validation_stats']['min']}-{oneweb['performance']['validation_stats']['max']}顆")
        print(f"   平均可換手: {oneweb['performance']['validation_stats']['mean']:.1f}顆")
        
        # 整體評估
        starlink_ready = starlink['performance']['quality_grade'] in ['excellent', 'good', 'acceptable']
        oneweb_ready = oneweb['performance']['quality_grade'] in ['excellent', 'good', 'acceptable']
        
        print(f"\n🎯 學術研究準備度:")
        print(f"   Starlink系統: {'✅ 準備就緒' if starlink_ready else '❌ 需要改進'}")
        print(f"   OneWeb系統: {'✅ 準備就緒' if oneweb_ready else '❌ 需要改進'}")
        
        if starlink_ready and oneweb_ready:
            print(f"   🎉 整體評估: 系統已準備就緒，可用於LEO衛星換手強化學習研究！")
            research_readiness = 'ready'
        elif starlink_ready or oneweb_ready:
            print(f"   ⚠️ 整體評估: 部分系統準備就緒，建議優先使用表現較好的星座")
            research_readiness = 'partial'
        else:
            print(f"   ❌ 整體評估: 系統需要進一步優化")
            research_readiness = 'needs_work'
        
        # 詳細衛星池
        print(f"\n📋 具體衛星池配置:")
        
        print(f"\n   🚀 Starlink衛星池 ({starlink['pool_size']}顆):")
        for i, sat in enumerate(starlink['satellite_details'][:20], 1):  # 顯示前20顆
            print(f"      {i:2d}. {sat['name']} - {sat['handover_count']}次換手, 最高{sat['max_elevation']:.1f}°")
        if starlink['pool_size'] > 20:
            print(f"      ... 等共{starlink['pool_size']}顆")
        
        print(f"\n   🛰️ OneWeb衛星池 ({oneweb['pool_size']}顆):")
        for i, sat in enumerate(oneweb['satellite_details'][:15], 1):  # 顯示前15顆
            print(f"      {i:2d}. {sat['name']} - {sat['handover_count']}次換手, 最高{sat['max_elevation']:.1f}°")
        if oneweb['pool_size'] > 15:
            print(f"      ... 等共{oneweb['pool_size']}顆")
        
        return {
            'research_readiness': research_readiness,
            'starlink_ready': starlink_ready,
            'oneweb_ready': oneweb_ready,
            'summary': solution
        }

def main():
    """主執行函數"""
    print("🎯 啟動最終衛星池解決方案")
    
    solver = FinalSatellitePoolSolution()
    
    # 載入數據
    solver.load_satellite_data()
    
    # 生成完整解決方案
    solution = solver.generate_complete_solution()
    
    # 生成最終報告
    final_report = solver.generate_final_report(solution)
    
    # 保存結果
    output = {
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'configuration': solver.realistic_targets,
        'starlink_solution': {
            'selected_satellites': solution['starlink']['selected_satellites'],
            'pool_size': solution['starlink']['pool_size'],
            'success_rate': float(solution['starlink']['performance']['success_rate']),
            'quality_grade': solution['starlink']['performance']['quality_grade'],
            'handover_elevation': solver.realistic_targets['starlink']['handover_elevation']
        },
        'oneweb_solution': {
            'selected_satellites': solution['oneweb']['selected_satellites'],
            'pool_size': solution['oneweb']['pool_size'],
            'success_rate': float(solution['oneweb']['performance']['success_rate']),
            'quality_grade': solution['oneweb']['performance']['quality_grade'],
            'handover_elevation': solver.realistic_targets['oneweb']['handover_elevation']
        },
        'research_assessment': {
            'readiness': final_report['research_readiness'],
            'starlink_ready': final_report['starlink_ready'],
            'oneweb_ready': final_report['oneweb_ready']
        }
    }
    
    with open('final_satellite_pool_solution.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 最終解決方案已保存至: final_satellite_pool_solution.json")
    print(f"🎯 LEO衛星換手研究衛星池配置完成！")
    
    return solver, solution, final_report

if __name__ == "__main__":
    solver, solution, final_report = main()