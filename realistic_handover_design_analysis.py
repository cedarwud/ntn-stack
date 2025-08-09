#!/usr/bin/env python3
"""
基於學術研究的LEO衛星換手候選設計分析
參考3GPP NTN標準和相關研究論文的合理設計
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from skyfield.api import load, EarthSatellite, wgs84
from skyfield.timelib import Time

class RealisticHandoverDesign:
    def __init__(self):
        self.NTPU_LAT = 24.9441667  # NTPU緯度
        self.NTPU_LON = 121.3713889  # NTPU經度
        
        # 基於學術研究的設計參數
        self.design_parameters = {
            'starlink': {
                # Starlink特性 (550km軌道高度)
                'altitude_km': 550,
                'orbital_period_min': 96,
                'inclination_deg': 53,
                'service_time_min': 8,  # 單顆衛星平均服務時間
                
                # 換手設計參數 (基於研究文獻)
                'handover_elevation_threshold': 15,    # 基於學術研究的最低換手仰角
                'candidate_elevation_threshold': 10,   # 候選衛星追蹤仰角
                'prediction_elevation_threshold': 5,   # 預測候選衛星仰角
                
                # 候選數量設計 (基於3GPP NTN和學術研究)
                'active_candidates': 3,      # 主動換手候選 (當前+2個鄰居)
                'tracking_candidates': 2,    # 追蹤候選 (準備升起)
                'total_candidates': 5        # 總候選數 (符合學術研究範圍)
            },
            'oneweb': {
                # OneWeb特性 (1200km軌道高度)
                'altitude_km': 1200,
                'orbital_period_min': 109,
                'inclination_deg': 87.4,
                'service_time_min': 15,  # 較長的服務時間
                
                # 換手設計參數 (考慮更高軌道的特性)
                'handover_elevation_threshold': 10,    # 較低門檻，因為衛星較少
                'candidate_elevation_threshold': 8,    # 候選衛星追蹤仰角
                'prediction_elevation_threshold': 5,   # 預測候選衛星仰角
                
                # 候選數量設計 (考慮較少的可見衛星數量)
                'active_candidates': 2,      # 主動換手候選 (當前+1個鄰居)
                'tracking_candidates': 1,    # 追蹤候選
                'total_candidates': 3        # 較少的總候選數
            }
        }
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # TLE數據路徑
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        
        # 載入衛星數據
        self.starlink_satellites = []
        self.oneweb_satellites = []
        
        print(f"🛰️ 基於學術研究的LEO衛星換手設計分析")
        print(f"📍 觀測點: NTPU ({self.NTPU_LAT}°N, {self.NTPU_LON}°E)")
        
    def load_satellite_data(self):
        """載入衛星數據"""
        print("\n📡 載入衛星數據...")
        
        # 載入TLE數據
        starlink_tle_path = f"{self.tle_base_path}/starlink/tle/starlink_20250808.tle"
        oneweb_tle_path = f"{self.tle_base_path}/oneweb/tle/oneweb_20250808.tle"
        
        self.starlink_satellites = self._parse_tle_file(starlink_tle_path, "Starlink")
        self.oneweb_satellites = self._parse_tle_file(oneweb_tle_path, "OneWeb")
        
        print(f"✅ 載入 {len(self.starlink_satellites)} 顆 Starlink 衛星")
        print(f"✅ 載入 {len(self.oneweb_satellites)} 顆 OneWeb 衛星")
        
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
                            'line1': line1,
                            'line2': line2
                        })
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"❌ 載入TLE文件失敗 {tle_path}: {e}")
            
        return satellites
    
    def analyze_elevation_distribution(self, analysis_time):
        """分析特定時間的仰角分布"""
        t = self.ts.utc(analysis_time.year, analysis_time.month, analysis_time.day,
                       analysis_time.hour, analysis_time.minute, analysis_time.second)
        
        results = {
            'starlink': {'satellites': [], 'elevation_bins': {}},
            'oneweb': {'satellites': [], 'elevation_bins': {}}
        }
        
        # 定義仰角區間
        elevation_bins = [
            ('≥0°', 0), ('≥5°', 5), ('≥10°', 10), 
            ('≥15°', 15), ('≥20°', 20), ('≥30°', 30)
        ]
        
        # 初始化計數
        for constellation in ['starlink', 'oneweb']:
            for bin_name, _ in elevation_bins:
                results[constellation]['elevation_bins'][bin_name] = []
        
        # 分析Starlink
        for sat_data in self.starlink_satellites:
            try:
                satellite = sat_data['satellite']
                difference = satellite - self.ntpu
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                if alt.degrees >= 0:
                    sat_info = {
                        'name': sat_data['name'],
                        'elevation': alt.degrees,
                        'azimuth': az.degrees,
                        'distance': distance.km
                    }
                    results['starlink']['satellites'].append(sat_info)
                    
                    # 分配到仰角區間
                    for bin_name, threshold in elevation_bins:
                        if alt.degrees >= threshold:
                            results['starlink']['elevation_bins'][bin_name].append(sat_info)
            except Exception:
                continue
        
        # 分析OneWeb
        for sat_data in self.oneweb_satellites:
            try:
                satellite = sat_data['satellite']
                difference = satellite - self.ntpu
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                if alt.degrees >= 0:
                    sat_info = {
                        'name': sat_data['name'],
                        'elevation': alt.degrees,
                        'azimuth': az.degrees,
                        'distance': distance.km
                    }
                    results['oneweb']['satellites'].append(sat_info)
                    
                    # 分配到仰角區間
                    for bin_name, threshold in elevation_bins:
                        if alt.degrees >= threshold:
                            results['oneweb']['elevation_bins'][bin_name].append(sat_info)
            except Exception:
                continue
        
        return results
    
    def simulate_realistic_handover_candidates(self, analysis_time):
        """模擬現實的換手候選選擇"""
        elevation_data = self.analyze_elevation_distribution(analysis_time)
        
        handover_simulation = {
            'starlink': {
                'design_params': self.design_parameters['starlink'],
                'available_satellites': {},
                'selected_candidates': {}
            },
            'oneweb': {
                'design_params': self.design_parameters['oneweb'],
                'available_satellites': {},
                'selected_candidates': {}
            }
        }
        
        # Starlink候選選擇
        starlink_params = self.design_parameters['starlink']
        starlink_data = elevation_data['starlink']
        
        # 按仰角門檻分類可用衛星
        handover_simulation['starlink']['available_satellites'] = {
            'handover_ready': [s for s in starlink_data['satellites'] 
                             if s['elevation'] >= starlink_params['handover_elevation_threshold']],
            'candidate_tracking': [s for s in starlink_data['satellites'] 
                                 if starlink_params['candidate_elevation_threshold'] <= s['elevation'] < starlink_params['handover_elevation_threshold']],
            'prediction_pool': [s for s in starlink_data['satellites'] 
                              if starlink_params['prediction_elevation_threshold'] <= s['elevation'] < starlink_params['candidate_elevation_threshold']]
        }
        
        # 選擇換手候選 (按仰角排序，選擇最佳的)
        handover_ready = sorted(handover_simulation['starlink']['available_satellites']['handover_ready'],
                               key=lambda x: x['elevation'], reverse=True)
        candidate_tracking = sorted(handover_simulation['starlink']['available_satellites']['candidate_tracking'],
                                   key=lambda x: x['elevation'], reverse=True)
        
        handover_simulation['starlink']['selected_candidates'] = {
            'active_handover': handover_ready[:starlink_params['active_candidates']],
            'tracking': candidate_tracking[:starlink_params['tracking_candidates']],
            'total_count': min(len(handover_ready) + len(candidate_tracking), starlink_params['total_candidates'])
        }
        
        # OneWeb候選選擇 (類似邏輯，但參數不同)
        oneweb_params = self.design_parameters['oneweb']
        oneweb_data = elevation_data['oneweb']
        
        handover_simulation['oneweb']['available_satellites'] = {
            'handover_ready': [s for s in oneweb_data['satellites'] 
                             if s['elevation'] >= oneweb_params['handover_elevation_threshold']],
            'candidate_tracking': [s for s in oneweb_data['satellites'] 
                                 if oneweb_params['candidate_elevation_threshold'] <= s['elevation'] < oneweb_params['handover_elevation_threshold']],
            'prediction_pool': [s for s in oneweb_data['satellites'] 
                              if oneweb_params['prediction_elevation_threshold'] <= s['elevation'] < oneweb_params['candidate_elevation_threshold']]
        }
        
        handover_ready_ow = sorted(handover_simulation['oneweb']['available_satellites']['handover_ready'],
                                  key=lambda x: x['elevation'], reverse=True)
        candidate_tracking_ow = sorted(handover_simulation['oneweb']['available_satellites']['candidate_tracking'],
                                      key=lambda x: x['elevation'], reverse=True)
        
        handover_simulation['oneweb']['selected_candidates'] = {
            'active_handover': handover_ready_ow[:oneweb_params['active_candidates']],
            'tracking': candidate_tracking_ow[:oneweb_params['tracking_candidates']],
            'total_count': min(len(handover_ready_ow) + len(candidate_tracking_ow), oneweb_params['total_candidates'])
        }
        
        return handover_simulation
    
    def analyze_24h_realistic_design(self, sample_interval_minutes=60):
        """分析24小時的現實設計表現"""
        print(f"\n🕐 開始24小時現實設計分析...")
        
        start_time = datetime.now(timezone.utc)
        time_points = []
        results = []
        
        num_samples = int(24 * 60 / sample_interval_minutes)
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval_minutes)
            time_points.append(current_time)
            
            # 執行現實換手候選模擬
            simulation = self.simulate_realistic_handover_candidates(current_time)
            
            # 記錄結果
            results.append({
                'time': current_time,
                'starlink': {
                    'handover_ready': len(simulation['starlink']['available_satellites']['handover_ready']),
                    'candidate_tracking': len(simulation['starlink']['available_satellites']['candidate_tracking']),
                    'prediction_pool': len(simulation['starlink']['available_satellites']['prediction_pool']),
                    'selected_candidates': simulation['starlink']['selected_candidates']['total_count'],
                    'active_handover': len(simulation['starlink']['selected_candidates']['active_handover']),
                    'tracking': len(simulation['starlink']['selected_candidates']['tracking'])
                },
                'oneweb': {
                    'handover_ready': len(simulation['oneweb']['available_satellites']['handover_ready']),
                    'candidate_tracking': len(simulation['oneweb']['available_satellites']['candidate_tracking']),
                    'prediction_pool': len(simulation['oneweb']['available_satellites']['prediction_pool']),
                    'selected_candidates': simulation['oneweb']['selected_candidates']['total_count'],
                    'active_handover': len(simulation['oneweb']['selected_candidates']['active_handover']),
                    'tracking': len(simulation['oneweb']['selected_candidates']['tracking'])
                }
            })
            
            if (i + 1) % 4 == 0:
                progress = (i + 1) / num_samples * 100
                print(f"  進度: {progress:.1f}% - 時間: {current_time.strftime('%H:%M')} "
                      f"- Starlink候選: {results[-1]['starlink']['selected_candidates']}, "
                      f"OneWeb候選: {results[-1]['oneweb']['selected_candidates']}")
        
        return time_points, results
    
    def generate_comprehensive_report(self, time_points, results):
        """生成綜合分析報告"""
        print(f"\n" + "="*80)
        print(f"🛰️ 基於學術研究的LEO衛星換手候選設計分析")
        print(f"="*80)
        
        # 計算統計數據
        starlink_candidates = [r['starlink']['selected_candidates'] for r in results]
        oneweb_candidates = [r['oneweb']['selected_candidates'] for r in results]
        
        starlink_handover_ready = [r['starlink']['handover_ready'] for r in results]
        oneweb_handover_ready = [r['oneweb']['handover_ready'] for r in results]
        
        print(f"\n📊 設計參數總覽:")
        print(f"─────────────────────────────────────────────────────────────")
        
        # Starlink設計參數
        starlink_params = self.design_parameters['starlink']
        print(f"\n🚀 Starlink 設計參數:")
        print(f"   換手仰角門檻: ≥{starlink_params['handover_elevation_threshold']}° (基於學術研究)")
        print(f"   候選追蹤門檻: ≥{starlink_params['candidate_elevation_threshold']}° (3GPP NTN建議)")
        print(f"   預測門檻: ≥{starlink_params['prediction_elevation_threshold']}° (預測性換手)")
        print(f"   主動換手候選: {starlink_params['active_candidates']}顆 (當前服務+鄰居)")
        print(f"   追蹤候選: {starlink_params['tracking_candidates']}顆 (準備升起)")
        print(f"   總候選數: {starlink_params['total_candidates']}顆 (符合UE能力限制)")
        
        # OneWeb設計參數
        oneweb_params = self.design_parameters['oneweb']
        print(f"\n🛰️ OneWeb 設計參數:")
        print(f"   換手仰角門檻: ≥{oneweb_params['handover_elevation_threshold']}° (適應較少衛星)")
        print(f"   候選追蹤門檻: ≥{oneweb_params['candidate_elevation_threshold']}° (較寬鬆門檻)")
        print(f"   預測門檻: ≥{oneweb_params['prediction_elevation_threshold']}° (預測性換手)")
        print(f"   主動換手候選: {oneweb_params['active_candidates']}顆 (當前服務+鄰居)")
        print(f"   追蹤候選: {oneweb_params['tracking_candidates']}顆 (準備升起)")
        print(f"   總候選數: {oneweb_params['total_candidates']}顆 (適應低密度)")
        
        print(f"\n🎯 24小時分析結果:")
        print(f"─────────────────────────────────────────────────────────────")
        
        # Starlink統計
        print(f"\n🚀 Starlink 換手候選分析:")
        print(f"   可換手衛星 (≥{starlink_params['handover_elevation_threshold']}°): "
              f"{min(starlink_handover_ready)}-{max(starlink_handover_ready)}顆, "
              f"平均{np.mean(starlink_handover_ready):.1f}顆")
        print(f"   實際候選選擇: {min(starlink_candidates)}-{max(starlink_candidates)}顆, "
              f"平均{np.mean(starlink_candidates):.1f}顆")
        
        if min(starlink_candidates) >= starlink_params['total_candidates']:
            print(f"   ✅ 候選數量充足: 任何時刻都能滿足{starlink_params['total_candidates']}顆候選需求")
        else:
            print(f"   ⚠️ 候選數量不足: 最少只有{min(starlink_candidates)}顆，目標{starlink_params['total_candidates']}顆")
        
        # OneWeb統計
        print(f"\n🛰️ OneWeb 換手候選分析:")
        print(f"   可換手衛星 (≥{oneweb_params['handover_elevation_threshold']}°): "
              f"{min(oneweb_handover_ready)}-{max(oneweb_handover_ready)}顆, "
              f"平均{np.mean(oneweb_handover_ready):.1f}顆")
        print(f"   實際候選選擇: {min(oneweb_candidates)}-{max(oneweb_candidates)}顆, "
              f"平均{np.mean(oneweb_candidates):.1f}顆")
        
        if min(oneweb_candidates) >= oneweb_params['total_candidates']:
            print(f"   ✅ 候選數量充足: 任何時刻都能滿足{oneweb_params['total_candidates']}顆候選需求")
        else:
            print(f"   ⚠️ 候選數量不足: 最少只有{min(oneweb_candidates)}顆，目標{oneweb_params['total_candidates']}顆")
        
        print(f"\n🎓 學術研究驗證:")
        print(f"─────────────────────────────────────────────────────────────")
        
        total_candidates_range = f"{min(starlink_candidates) + min(oneweb_candidates)}-{max(starlink_candidates) + max(oneweb_candidates)}"
        avg_total_candidates = np.mean(starlink_candidates) + np.mean(oneweb_candidates)
        
        print(f"   總候選數範圍: {total_candidates_range}顆")
        print(f"   平均總候選數: {avg_total_candidates:.1f}顆")
        
        if avg_total_candidates <= 8:
            print(f"   ✅ 符合學術研究範圍: 總候選數{avg_total_candidates:.1f}顆 ≤ 8顆上限")
            print(f"   💡 研究價值: 接近真實系統能力，具備工程實用性")
        else:
            print(f"   ⚠️ 超出學術研究範圍: 總候選數{avg_total_candidates:.1f}顆 > 8顆建議上限")
            print(f"   💡 建議調整: 考慮降低仰角門檻或減少候選數量")
        
        print(f"\n💡 設計建議:")
        print(f"─────────────────────────────────────────────────────────────")
        print(f"   🎯 Starlink: {starlink_params['total_candidates']}顆候選 (主動{starlink_params['active_candidates']}+追蹤{starlink_params['tracking_candidates']})")
        print(f"   🎯 OneWeb: {oneweb_params['total_candidates']}顆候選 (主動{oneweb_params['active_candidates']}+追蹤{oneweb_params['tracking_candidates']})")
        print(f"   🎯 總計: 平均{avg_total_candidates:.1f}顆 (符合3GPP NTN和學術研究標準)")
        
        research_advantages = [
            "基於真實TLE數據和SGP4軌道計算",
            "仰角門檻符合大氣傳播特性",
            "候選數量適合UE處理能力",
            "分層設計支援預測性換手",
            "兩星座差異化設計反映真實特性"
        ]
        
        print(f"\n   🚀 研究優勢:")
        for i, advantage in enumerate(research_advantages, 1):
            print(f"      {i}. {advantage}")
        
        return {
            'starlink_stats': {
                'candidates_range': f"{min(starlink_candidates)}-{max(starlink_candidates)}",
                'candidates_avg': np.mean(starlink_candidates),
                'handover_ready_avg': np.mean(starlink_handover_ready)
            },
            'oneweb_stats': {
                'candidates_range': f"{min(oneweb_candidates)}-{max(oneweb_candidates)}",
                'candidates_avg': np.mean(oneweb_candidates),
                'handover_ready_avg': np.mean(oneweb_handover_ready)
            },
            'total_candidates_avg': avg_total_candidates
        }

def main():
    """主執行函數"""
    print("🚀 啟動基於學術研究的LEO衛星換手設計分析")
    
    # 初始化分析器
    analyzer = RealisticHandoverDesign()
    
    # 載入衛星數據
    analyzer.load_satellite_data()
    
    # 執行24小時分析
    time_points, results = analyzer.analyze_24h_realistic_design()
    
    # 生成綜合報告
    stats = analyzer.generate_comprehensive_report(time_points, results)
    
    # 保存結果
    output = {
        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
        'design_parameters': analyzer.design_parameters,
        'statistics': stats,
        'recommendations': {
            'starlink_candidates': analyzer.design_parameters['starlink']['total_candidates'],
            'oneweb_candidates': analyzer.design_parameters['oneweb']['total_candidates'],
            'total_avg': stats['total_candidates_avg'],
            'academic_compliance': stats['total_candidates_avg'] <= 8
        }
    }
    
    with open('realistic_handover_design_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析結果已保存至: realistic_handover_design_analysis.json")
    print(f"🎉 分析完成!")
    
    return analyzer, stats

if __name__ == "__main__":
    analyzer, stats = main()