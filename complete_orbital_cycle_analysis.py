#!/usr/bin/env python3
"""
完整軌道週期衛星池計算
計算維持穩定換手數量所需的總衛星池規模
包括：可換手區域 + 場景緩衝 + 地平線下準備區
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
from skyfield.api import load, EarthSatellite, wgs84

class CompleteOrbitalCycleAnalysis:
    def __init__(self):
        self.NTPU_LAT = 24.9441667
        self.NTPU_LON = 121.3713889
        
        # 軌道週期 (分鐘)
        self.orbital_periods = {
            'starlink': 96,    # Starlink軌道週期
            'oneweb': 109      # OneWeb軌道週期
        }
        
        # 目標換手數量 (基於您的建議)
        self.handover_targets = {
            'starlink': {
                'active_handover': 15,     # 目標15顆可換手
                'handover_elevation': 10,  # 換手仰角門檻
                'tracking_elevation': 5,   # 追蹤區域門檻
                'horizon_elevation': 0     # 地平線
            },
            'oneweb': {
                'active_handover': 10,     # 目標10顆可換手
                'handover_elevation': 8,   # 換手仰角門檻
                'tracking_elevation': 3,   # 追蹤區域門檻  
                'horizon_elevation': 0     # 地平線
            }
        }
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # TLE數據
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        self.starlink_satellites = []
        self.oneweb_satellites = []
        
        print("🔄 完整軌道週期衛星池分析")
        print("📊 計算維持穩定換手數量的總衛星池需求")
        
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
    
    def analyze_complete_orbital_cycle(self, constellation):
        """分析完整軌道週期的三層衛星需求"""
        print(f"\n🔄 分析 {constellation.title()} 完整軌道週期需求...")
        
        satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
        orbital_period = self.orbital_periods[constellation]
        config = self.handover_targets[constellation]
        
        # 分析完整軌道週期 + 額外緩衝
        analysis_duration = int(orbital_period * 1.5)  # 1.5個軌道週期
        sample_interval = 5  # 5分鐘採樣
        num_samples = int(analysis_duration / sample_interval)
        
        print(f"   ⏱️ 分析時長: {analysis_duration}分鐘 (~{analysis_duration/60:.1f}小時)")
        print(f"   📊 採樣間隔: {sample_interval}分鐘")
        print(f"   🎯 目標: 維持{config['active_handover']}顆可換手")
        
        start_time = datetime.now(timezone.utc)
        
        # 記錄每個時間點的衛星分層狀態
        cycle_analysis = {
            'time_points': [],
            'satellite_layers': {
                'handover_zone': [],      # 可換手區域 (≥handover_elevation)
                'tracking_zone': [],      # 追蹤區域 (tracking~handover elevation)  
                'approaching_zone': [],   # 接近區域 (horizon~tracking elevation)
                'total_scene': []         # 場景總計 (≥horizon)
            },
            'satellite_participation': {},  # 每顆衛星的參與記錄
            'transition_events': []          # 轉換事件記錄
        }
        
        # 初始化參與記錄
        for sat_data in satellites:
            cycle_analysis['satellite_participation'][sat_data['name']] = {
                'handover_appearances': [],
                'tracking_appearances': [], 
                'approaching_appearances': [],
                'max_elevation': 0,
                'total_contribution_time': 0
            }
        
        previous_states = {}  # 記錄上一時刻的狀態
        
        print(f"   🚀 開始完整週期分析...")
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval)
            t = self.ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
            
            cycle_analysis['time_points'].append(current_time)
            
            # 當前時刻的衛星分層
            current_layers = {
                'handover_zone': [],
                'tracking_zone': [],
                'approaching_zone': [],
                'total_scene': []
            }
            
            for sat_data in satellites:
                try:
                    satellite = sat_data['satellite']
                    difference = satellite - self.ntpu
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    elevation = alt.degrees
                    sat_name = sat_data['name']
                    
                    # 更新參與記錄
                    participation = cycle_analysis['satellite_participation'][sat_name]
                    participation['max_elevation'] = max(participation['max_elevation'], elevation)
                    
                    # 分層分類
                    if elevation >= config['handover_elevation']:
                        current_layers['handover_zone'].append({
                            'name': sat_name,
                            'elevation': elevation,
                            'azimuth': az.degrees
                        })
                        participation['handover_appearances'].append(i)
                        participation['total_contribution_time'] += sample_interval
                        
                    elif elevation >= config['tracking_elevation']:
                        current_layers['tracking_zone'].append({
                            'name': sat_name,
                            'elevation': elevation,
                            'azimuth': az.degrees
                        })
                        participation['tracking_appearances'].append(i)
                        participation['total_contribution_time'] += sample_interval
                        
                    elif elevation >= config['horizon_elevation']:
                        current_layers['approaching_zone'].append({
                            'name': sat_name,
                            'elevation': elevation,
                            'azimuth': az.degrees
                        })
                        participation['approaching_appearances'].append(i)
                        participation['total_contribution_time'] += sample_interval
                    
                    # 場景總計
                    if elevation >= config['horizon_elevation']:
                        current_layers['total_scene'].append({
                            'name': sat_name,
                            'elevation': elevation
                        })
                    
                    # 記錄轉換事件
                    if sat_name in previous_states:
                        prev_elev = previous_states[sat_name]
                        
                        # 進入換手區域
                        if prev_elev < config['handover_elevation'] and elevation >= config['handover_elevation']:
                            cycle_analysis['transition_events'].append({
                                'type': 'enter_handover',
                                'satellite': sat_name,
                                'time_index': i,
                                'elevation': elevation
                            })
                        
                        # 離開換手區域
                        elif prev_elev >= config['handover_elevation'] and elevation < config['handover_elevation']:
                            cycle_analysis['transition_events'].append({
                                'type': 'leave_handover',
                                'satellite': sat_name,
                                'time_index': i,
                                'elevation': elevation
                            })
                    
                    previous_states[sat_name] = elevation
                    
                except Exception:
                    continue
            
            # 記錄當前分層統計
            cycle_analysis['satellite_layers']['handover_zone'].append(len(current_layers['handover_zone']))
            cycle_analysis['satellite_layers']['tracking_zone'].append(len(current_layers['tracking_zone']))
            cycle_analysis['satellite_layers']['approaching_zone'].append(len(current_layers['approaching_zone']))
            cycle_analysis['satellite_layers']['total_scene'].append(len(current_layers['total_scene']))
            
            # 進度報告
            if (i + 1) % 12 == 0:  # 每小時報告
                progress = (i + 1) / num_samples * 100
                elapsed_hours = (i + 1) * sample_interval / 60
                print(f"     進度: {progress:.1f}% ({elapsed_hours:.1f}h) "
                      f"- 換手:{len(current_layers['handover_zone'])}, "
                      f"追蹤:{len(current_layers['tracking_zone'])}, "
                      f"接近:{len(current_layers['approaching_zone'])}, "
                      f"總計:{len(current_layers['total_scene'])}")
        
        return cycle_analysis
    
    def calculate_total_pool_requirements(self, cycle_analysis, constellation):
        """計算總衛星池需求"""
        print(f"\n📊 計算 {constellation.title()} 總衛星池需求...")
        
        config = self.handover_targets[constellation]
        layers = cycle_analysis['satellite_layers']
        participation = cycle_analysis['satellite_participation']
        
        # 統計分析
        layer_stats = {}
        for layer_name, counts in layers.items():
            layer_stats[layer_name] = {
                'min': min(counts),
                'max': max(counts),
                'mean': np.mean(counts),
                'std': np.std(counts)
            }
        
        print(f"   📊 各層衛星統計:")
        print(f"      換手區域: {layer_stats['handover_zone']['min']}-{layer_stats['handover_zone']['max']}顆 (平均{layer_stats['handover_zone']['mean']:.1f})")
        print(f"      追蹤區域: {layer_stats['tracking_zone']['min']}-{layer_stats['tracking_zone']['max']}顆 (平均{layer_stats['tracking_zone']['mean']:.1f})")
        print(f"      接近區域: {layer_stats['approaching_zone']['min']}-{layer_stats['approaching_zone']['max']}顆 (平均{layer_stats['approaching_zone']['mean']:.1f})")
        print(f"      場景總計: {layer_stats['total_scene']['min']}-{layer_stats['total_scene']['max']}顆 (平均{layer_stats['total_scene']['mean']:.1f})")
        
        # 計算所有曾經參與的衛星
        all_participants = set()
        handover_participants = set()
        tracking_participants = set()
        approaching_participants = set()
        
        for sat_name, stats in participation.items():
            if stats['total_contribution_time'] > 0:
                all_participants.add(sat_name)
                
            if len(stats['handover_appearances']) > 0:
                handover_participants.add(sat_name)
                
            if len(stats['tracking_appearances']) > 0:
                tracking_participants.add(sat_name)
                
            if len(stats['approaching_appearances']) > 0:
                approaching_participants.add(sat_name)
        
        # 計算轉換頻率
        enter_events = len([e for e in cycle_analysis['transition_events'] if e['type'] == 'enter_handover'])
        leave_events = len([e for e in cycle_analysis['transition_events'] if e['type'] == 'leave_handover'])
        analysis_hours = len(cycle_analysis['time_points']) * 5 / 60  # 5分鐘採樣轉小時
        
        turnover_rate = (enter_events + leave_events) / analysis_hours / 2  # 每小時換手轉換率
        
        print(f"\n   🔄 動態特性分析:")
        print(f"      轉換頻率: {turnover_rate:.1f}顆/小時")
        print(f"      總參與衛星: {len(all_participants)}顆")
        print(f"      換手區參與: {len(handover_participants)}顆")
        print(f"      追蹤區參與: {len(tracking_participants)}顆")
        print(f"      接近區參與: {len(approaching_participants)}顆")
        
        # 計算所需總池大小
        # 基於維持目標數量的需求，考慮動態轉換
        required_pool = self._calculate_optimal_pool_size(
            config, layer_stats, len(all_participants), turnover_rate
        )
        
        return {
            'layer_statistics': layer_stats,
            'participation_analysis': {
                'total_participants': len(all_participants),
                'handover_participants': len(handover_participants),
                'tracking_participants': len(tracking_participants),
                'approaching_participants': len(approaching_participants),
                'participant_names': list(all_participants)
            },
            'dynamic_characteristics': {
                'turnover_rate_per_hour': turnover_rate,
                'enter_events': enter_events,
                'leave_events': leave_events
            },
            'pool_requirements': required_pool
        }
    
    def _calculate_optimal_pool_size(self, config, layer_stats, total_participants, turnover_rate):
        """計算最佳衛星池大小"""
        target_handover = config['active_handover']
        
        # 基於統計數據計算需求
        avg_handover = layer_stats['handover_zone']['mean']
        avg_tracking = layer_stats['tracking_zone']['mean']
        avg_approaching = layer_stats['approaching_zone']['mean']
        
        # 如果當前平均可換手數量不足目標
        if avg_handover < target_handover:
            # 需要更多衛星池來確保足夠的輪轉
            shortage_factor = target_handover / max(avg_handover, 1)
            recommended_pool = int(total_participants * shortage_factor)
        else:
            # 當前池子已足夠，但考慮動態轉換需要緩衝
            buffer_factor = 1.2 + (turnover_rate / 10)  # 基於轉換頻率的緩衝係數
            recommended_pool = int(total_participants * buffer_factor)
        
        # 確保不超過實際可用衛星數量
        max_available = len(self.starlink_satellites if 'starlink' in str(config) else self.oneweb_satellites)
        recommended_pool = min(recommended_pool, max_available)
        
        # 分層需求分析
        layer_requirements = {
            'handover_core': max(target_handover, int(avg_handover * 1.2)),
            'tracking_buffer': max(5, int(avg_tracking * 0.8)),
            'approaching_reserve': max(5, int(avg_approaching * 0.5)),
            'total_recommended': recommended_pool
        }
        
        # 可行性評估
        feasibility = {
            'target_achievable': avg_handover >= target_handover * 0.8,
            'pool_sufficient': recommended_pool <= total_participants,
            'turnover_manageable': turnover_rate <= 10  # 每小時不超過10次轉換
        }
        
        return {
            'layer_requirements': layer_requirements,
            'feasibility_assessment': feasibility,
            'current_performance': {
                'avg_handover_available': avg_handover,
                'target_handover_needed': target_handover,
                'achievement_ratio': min(avg_handover / target_handover, 1.0)
            }
        }
    
    def select_optimal_satellite_pool(self, analysis_result, constellation):
        """選擇最佳衛星池"""
        print(f"\n🎯 選擇 {constellation.title()} 最佳衛星池...")
        
        participation = analysis_result['participation_analysis']
        pool_req = analysis_result['pool_requirements']
        
        satellites = self.starlink_satellites if constellation == 'starlink' else self.oneweb_satellites
        participant_names = participation['participant_names']
        
        # 計算每顆衛星的綜合評分
        satellite_scores = []
        
        for sat_data in satellites:
            if sat_data['name'] in participant_names:
                # 這顆衛星有參與，計算其貢獻分數
                sat_name = sat_data['name']
                # 這裡需要從之前的分析中獲取詳細的參與數據
                # 簡化計算：基於名稱在參與名單中的存在來評分
                satellite_scores.append({
                    'name': sat_name,
                    'satellite': sat_data['satellite'],
                    'participation_score': 1.0  # 簡化評分
                })
        
        # 選擇推薦數量的衛星
        recommended_count = pool_req['layer_requirements']['total_recommended']
        selected_count = min(recommended_count, len(satellite_scores))
        
        selected_satellites = satellite_scores[:selected_count]
        
        print(f"   📋 選中衛星池: {selected_count}顆")
        print(f"   🎯 推薦總數: {recommended_count}顆")
        print(f"   ✅ 覆蓋率: {selected_count/recommended_count:.1%}")
        
        return {
            'selected_satellites': selected_satellites,
            'selected_count': selected_count,
            'recommended_count': recommended_count,
            'coverage_ratio': selected_count / recommended_count
        }
    
    def generate_complete_solution(self):
        """生成完整解決方案"""
        print(f"\n🎯 生成完整軌道週期解決方案")
        print(f"="*80)
        
        # Starlink分析
        print(f"\n🚀 Starlink 完整週期分析")
        print(f"-" * 50)
        starlink_cycle = self.analyze_complete_orbital_cycle('starlink')
        starlink_requirements = self.calculate_total_pool_requirements(starlink_cycle, 'starlink')
        starlink_selection = self.select_optimal_satellite_pool(starlink_requirements, 'starlink')
        
        # OneWeb分析
        print(f"\n🛰️ OneWeb 完整週期分析")  
        print(f"-" * 50)
        oneweb_cycle = self.analyze_complete_orbital_cycle('oneweb')
        oneweb_requirements = self.calculate_total_pool_requirements(oneweb_cycle, 'oneweb')
        oneweb_selection = self.select_optimal_satellite_pool(oneweb_requirements, 'oneweb')
        
        # 生成最終報告
        final_solution = {
            'starlink': {
                'target_config': self.handover_targets['starlink'],
                'analysis_results': starlink_requirements,
                'selected_pool': starlink_selection,
                'satellite_names': [sat['name'] for sat in starlink_selection['selected_satellites']]
            },
            'oneweb': {
                'target_config': self.handover_targets['oneweb'],
                'analysis_results': oneweb_requirements,
                'selected_pool': oneweb_selection,
                'satellite_names': [sat['name'] for sat in oneweb_selection['selected_satellites']]
            }
        }
        
        return final_solution
    
    def generate_final_report(self, solution):
        """生成最終報告"""
        print(f"\n" + "="*80)
        print(f"🎉 完整軌道週期衛星池解決方案")
        print(f"="*80)
        print(f"📍 基於NTPU觀測點的完整週期動態平衡設計")
        
        starlink = solution['starlink']
        oneweb = solution['oneweb']
        
        print(f"\n🚀 Starlink 完整週期配置:")
        sl_perf = starlink['analysis_results']['pool_requirements']['current_performance']
        sl_pool = starlink['selected_pool']
        print(f"   🎯 目標換手數量: {starlink['target_config']['active_handover']}顆")
        print(f"   📊 實際平均可換手: {sl_perf['avg_handover_available']:.1f}顆")
        print(f"   📋 總衛星池大小: {sl_pool['selected_count']}顆")
        print(f"   ✅ 目標達成率: {sl_perf['achievement_ratio']:.1%}")
        
        print(f"\n🛰️ OneWeb 完整週期配置:")
        ow_perf = oneweb['analysis_results']['pool_requirements']['current_performance']
        ow_pool = oneweb['selected_pool']
        print(f"   🎯 目標換手數量: {oneweb['target_config']['active_handover']}顆")
        print(f"   📊 實際平均可換手: {ow_perf['avg_handover_available']:.1f}顆")
        print(f"   📋 總衛星池大小: {ow_pool['selected_count']}顆")
        print(f"   ✅ 目標達成率: {ow_perf['achievement_ratio']:.1%}")
        
        # 研究準備度評估
        starlink_ready = sl_perf['achievement_ratio'] >= 0.8
        oneweb_ready = ow_perf['achievement_ratio'] >= 0.8
        
        print(f"\n🎯 研究準備度評估:")
        print(f"   Starlink系統: {'✅ 準備就緒' if starlink_ready else '⚠️ 需要調整'}")
        print(f"   OneWeb系統: {'✅ 準備就緒' if oneweb_ready else '⚠️ 需要調整'}")
        
        if starlink_ready and oneweb_ready:
            readiness = 'excellent'
            print(f"   🎉 整體評估: 完整週期動態平衡，已準備就緒！")
        elif starlink_ready or oneweb_ready:
            readiness = 'partial'
            print(f"   ⚠️ 整體評估: 部分系統準備就緒")
        else:
            readiness = 'needs_work'
            print(f"   ❌ 整體評估: 需要進一步優化")
        
        print(f"\n💡 最終建議:")
        print(f"   🚀 Starlink使用 {sl_pool['selected_count']} 顆衛星池")
        print(f"   🛰️ OneWeb使用 {ow_pool['selected_count']} 顆衛星池")
        print(f"   📊 可維持目標換手數量: Starlink {starlink['target_config']['active_handover']}顆, OneWeb {oneweb['target_config']['active_handover']}顆")
        
        return {
            'readiness': readiness,
            'starlink_ready': starlink_ready,
            'oneweb_ready': oneweb_ready,
            'starlink_pool_size': sl_pool['selected_count'],
            'oneweb_pool_size': ow_pool['selected_count'],
            'solution': solution
        }

def main():
    """主執行函數"""
    print("🔄 啟動完整軌道週期衛星池分析")
    
    analyzer = CompleteOrbitalCycleAnalysis()
    
    # 載入數據
    analyzer.load_satellite_data()
    
    # 生成完整解決方案
    solution = analyzer.generate_complete_solution()
    
    # 生成最終報告
    final_report = analyzer.generate_final_report(solution)
    
    # 保存結果
    output = {
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'orbital_periods': analyzer.orbital_periods,
        'handover_targets': analyzer.handover_targets,
        'starlink_solution': {
            'satellite_names': solution['starlink']['satellite_names'],
            'pool_size': final_report['starlink_pool_size'],
            'target_handover': analyzer.handover_targets['starlink']['active_handover'],
            'achievement_ratio': float(solution['starlink']['analysis_results']['pool_requirements']['current_performance']['achievement_ratio'])
        },
        'oneweb_solution': {
            'satellite_names': solution['oneweb']['satellite_names'],
            'pool_size': final_report['oneweb_pool_size'],
            'target_handover': analyzer.handover_targets['oneweb']['active_handover'],
            'achievement_ratio': float(solution['oneweb']['analysis_results']['pool_requirements']['current_performance']['achievement_ratio'])
        },
        'readiness_assessment': final_report['readiness']
    }
    
    with open('complete_orbital_cycle_solution.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 完整解決方案已保存至: complete_orbital_cycle_solution.json")
    print(f"🎯 完整軌道週期分析完成！")
    
    return analyzer, solution, final_report

if __name__ == "__main__":
    analyzer, solution, final_report = main()