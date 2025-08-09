#!/usr/bin/env python3
"""
LEO衛星換手研究 - 全量衛星綜合分析
使用最新TLE數據分析NTPU觀測點的衛星可見性
"""

import os
import sys
import json
import math
import numpy as np
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import matplotlib.pyplot as plt
from skyfield.api import load, EarthSatellite, wgs84
from skyfield.timelib import Time
import pandas as pd

class ComprehensiveLEOAnalysis:
    def __init__(self):
        self.NTPU_LAT = 24.9441667  # NTPU緯度
        self.NTPU_LON = 121.3713889  # NTPU經度
        self.NTPU_ALT = 0.05  # NTPU海拔 (km)
        
        # 時間系統
        self.ts = load.timescale()
        self.ntpu = wgs84.latlon(self.NTPU_LAT, self.NTPU_LON, elevation_m=50)
        
        # TLE數據路徑
        self.tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        
        # 分析結果存儲
        self.starlink_satellites = []
        self.oneweb_satellites = []
        self.analysis_results = {}
        
        print(f"🛰️ 初始化LEO衛星分析系統")
        print(f"📍 觀測點: NTPU ({self.NTPU_LAT}°N, {self.NTPU_LON}°E)")
        
    def load_latest_tle_data(self):
        """載入最新的TLE數據"""
        print("\n📡 載入最新TLE數據...")
        
        # 載入Starlink TLE
        starlink_tle_path = f"{self.tle_base_path}/starlink/tle/starlink_20250808.tle"
        oneweb_tle_path = f"{self.tle_base_path}/oneweb/tle/oneweb_20250808.tle"
        
        # 解析Starlink TLE
        self.starlink_satellites = self._parse_tle_file(starlink_tle_path, "Starlink")
        print(f"✅ 載入 {len(self.starlink_satellites)} 顆 Starlink 衛星")
        
        # 解析OneWeb TLE  
        self.oneweb_satellites = self._parse_tle_file(oneweb_tle_path, "OneWeb")
        print(f"✅ 載入 {len(self.oneweb_satellites)} 顆 OneWeb 衛星")
        
        print(f"🎯 總計載入 {len(self.starlink_satellites) + len(self.oneweb_satellites)} 顆衛星")
        
    def _parse_tle_file(self, tle_path, constellation):
        """解析TLE文件"""
        satellites = []
        
        try:
            with open(tle_path, 'r') as f:
                lines = f.readlines()
            
            # 每3行為一組 (名稱, TLE第1行, TLE第2行)
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    # 創建衛星物件
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
                        print(f"⚠️ 無法解析衛星 {name}: {e}")
                        
        except Exception as e:
            print(f"❌ 載入TLE文件失敗 {tle_path}: {e}")
            
        return satellites
    
    def analyze_visibility_at_time(self, analysis_time):
        """分析特定時間的衛星可見性"""
        t = self.ts.utc(analysis_time.year, analysis_time.month, analysis_time.day,
                       analysis_time.hour, analysis_time.minute, analysis_time.second)
        
        visible_starlink = []
        visible_oneweb = []
        
        # 分析Starlink可見性
        for sat_data in self.starlink_satellites:
            try:
                satellite = sat_data['satellite']
                difference = satellite - self.ntpu
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                if alt.degrees >= 0:  # 地平線以上
                    visible_starlink.append({
                        'name': sat_data['name'],
                        'elevation': alt.degrees,
                        'azimuth': az.degrees,
                        'distance': distance.km,
                        'constellation': 'Starlink'
                    })
            except Exception as e:
                continue
        
        # 分析OneWeb可見性
        for sat_data in self.oneweb_satellites:
            try:
                satellite = sat_data['satellite']
                difference = satellite - self.ntpu
                topocentric = difference.at(t)
                alt, az, distance = topocentric.altaz()
                
                if alt.degrees >= 0:  # 地平線以上
                    visible_oneweb.append({
                        'name': sat_data['name'],
                        'elevation': alt.degrees,
                        'azimuth': az.degrees,
                        'distance': distance.km,
                        'constellation': 'OneWeb'
                    })
            except Exception as e:
                continue
        
        return visible_starlink, visible_oneweb
    
    def analyze_24h_coverage(self, start_time=None, sample_interval_minutes=30):
        """分析24小時覆蓋情況"""
        if start_time is None:
            start_time = datetime.now(timezone.utc)
        
        print(f"\n🕐 開始24小時覆蓋分析...")
        print(f"📅 開始時間: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"⏱️ 採樣間隔: {sample_interval_minutes} 分鐘")
        
        # 24小時分析點
        time_points = []
        starlink_counts = []
        oneweb_counts = []
        total_counts = []
        
        detailed_results = []
        
        num_samples = int(24 * 60 / sample_interval_minutes)
        
        for i in range(num_samples):
            current_time = start_time + timedelta(minutes=i * sample_interval_minutes)
            time_points.append(current_time)
            
            # 分析當前時間點
            visible_starlink, visible_oneweb = self.analyze_visibility_at_time(current_time)
            
            # 分別統計不同仰角門檻的數量
            starlink_5deg = len([s for s in visible_starlink if s['elevation'] >= 5])
            starlink_10deg = len([s for s in visible_starlink if s['elevation'] >= 10])
            starlink_15deg = len([s for s in visible_starlink if s['elevation'] >= 15])
            
            oneweb_5deg = len([s for s in visible_oneweb if s['elevation'] >= 5])
            oneweb_10deg = len([s for s in visible_oneweb if s['elevation'] >= 10])
            oneweb_15deg = len([s for s in visible_oneweb if s['elevation'] >= 15])
            
            starlink_counts.append(starlink_5deg)
            oneweb_counts.append(oneweb_5deg)
            total_counts.append(starlink_5deg + oneweb_5deg)
            
            detailed_results.append({
                'time': current_time,
                'starlink': {
                    'total_visible': len(visible_starlink),
                    '>=5deg': starlink_5deg,
                    '>=10deg': starlink_10deg,
                    '>=15deg': starlink_15deg,
                    'satellites': visible_starlink[:10]  # 前10顆詳細信息
                },
                'oneweb': {
                    'total_visible': len(visible_oneweb),
                    '>=5deg': oneweb_5deg,
                    '>=10deg': oneweb_10deg,
                    '>=15deg': oneweb_15deg,
                    'satellites': visible_oneweb[:10]  # 前10顆詳細信息
                }
            })
            
            if (i + 1) % 10 == 0:
                progress = (i + 1) / num_samples * 100
                print(f"  進度: {progress:.1f}% - 時間: {current_time.strftime('%H:%M')} "
                      f"- Starlink ≥5°: {starlink_5deg}, OneWeb ≥5°: {oneweb_5deg}")
        
        # 統計分析
        self.analysis_results = {
            'time_points': time_points,
            'starlink_counts': starlink_counts,
            'oneweb_counts': oneweb_counts,
            'total_counts': total_counts,
            'detailed_results': detailed_results,
            'statistics': self._calculate_statistics(starlink_counts, oneweb_counts, total_counts)
        }
        
        return self.analysis_results
    
    def _calculate_statistics(self, starlink_counts, oneweb_counts, total_counts):
        """計算統計數據"""
        stats = {
            'starlink': {
                'min': min(starlink_counts),
                'max': max(starlink_counts),
                'mean': np.mean(starlink_counts),
                'median': np.median(starlink_counts),
                'std': np.std(starlink_counts)
            },
            'oneweb': {
                'min': min(oneweb_counts),
                'max': max(oneweb_counts),
                'mean': np.mean(oneweb_counts),
                'median': np.median(oneweb_counts),
                'std': np.std(oneweb_counts)
            },
            'total': {
                'min': min(total_counts),
                'max': max(total_counts),
                'mean': np.mean(total_counts),
                'median': np.median(total_counts),
                'std': np.std(total_counts)
            }
        }
        return stats
    
    def analyze_selection_strategies(self):
        """分析衛星選擇策略"""
        print(f"\n🎯 衛星選擇策略分析...")
        
        # 使用第一個時間點作為基準分析
        base_time = datetime.now(timezone.utc)
        visible_starlink, visible_oneweb = self.analyze_visibility_at_time(base_time)
        
        # 按仰角排序
        starlink_5deg = sorted([s for s in visible_starlink if s['elevation'] >= 5], 
                              key=lambda x: x['elevation'], reverse=True)
        starlink_10deg = sorted([s for s in visible_starlink if s['elevation'] >= 10], 
                               key=lambda x: x['elevation'], reverse=True)
        starlink_15deg = sorted([s for s in visible_starlink if s['elevation'] >= 15], 
                               key=lambda x: x['elevation'], reverse=True)
        
        oneweb_5deg = sorted([s for s in visible_oneweb if s['elevation'] >= 5], 
                            key=lambda x: x['elevation'], reverse=True)
        oneweb_10deg = sorted([s for s in visible_oneweb if s['elevation'] >= 10], 
                             key=lambda x: x['elevation'], reverse=True)
        
        # 策略1: 從高仰角選擇40顆Starlink
        strategy_1_starlink_40 = starlink_15deg[:40] if len(starlink_15deg) >= 40 else starlink_10deg[:40]
        
        # 策略2: 從所有可見選擇8-12顆
        strategy_2_starlink_best = starlink_5deg[:12]
        strategy_2_oneweb_best = oneweb_5deg[:12]
        
        return {
            'base_analysis': {
                'starlink_total_visible': len(visible_starlink),
                'starlink_5deg': len(starlink_5deg),
                'starlink_10deg': len(starlink_10deg), 
                'starlink_15deg': len(starlink_15deg),
                'oneweb_total_visible': len(visible_oneweb),
                'oneweb_5deg': len(oneweb_5deg),
                'oneweb_10deg': len(oneweb_10deg)
            },
            'strategy_1': {
                'description': 'Starlink從205顆中選40顆場景衛星',
                'selected_count': len(strategy_1_starlink_40),
                'satellites': strategy_1_starlink_40
            },
            'strategy_2': {
                'description': '每個星座選擇最佳8-12顆',
                'starlink_selected': len(strategy_2_starlink_best),
                'oneweb_selected': len(strategy_2_oneweb_best),
                'starlink_satellites': strategy_2_starlink_best,
                'oneweb_satellites': strategy_2_oneweb_best
            }
        }
    
    def generate_comprehensive_report(self):
        """生成綜合分析報告"""
        if not self.analysis_results:
            print("❌ 請先執行24小時覆蓋分析")
            return
        
        stats = self.analysis_results['statistics']
        
        print(f"\n" + "="*80)
        print(f"🛰️ LEO衛星換手研究 - 全量衛星綜合分析報告")
        print(f"="*80)
        print(f"📍 觀測點: NTPU ({self.NTPU_LAT}°N, {self.NTPU_LON}°E)")
        print(f"📊 分析數據: {len(self.starlink_satellites)} Starlink + {len(self.oneweb_satellites)} OneWeb")
        print(f"⏰ 分析週期: 24小時 (30分鐘採樣)")
        
        print(f"\n🎯 關鍵發現:")
        print(f"─────────────────────────────────────────────────────────────")
        
        # 問題1分析
        print(f"\n❓ 問題1: Starlink 40顆場景衛星能否保證8-12顆持續可見?")
        if stats['starlink']['min'] >= 8 and stats['starlink']['max'] <= 12:
            print(f"✅ 是的! Starlink可見範圍: {stats['starlink']['min']:.0f}-{stats['starlink']['max']:.0f}顆")
        elif stats['starlink']['min'] >= 8:
            print(f"⚠️ 部分符合: 最少{stats['starlink']['min']:.0f}顆，最多{stats['starlink']['max']:.0f}顆 (超過12顆)")
        else:
            print(f"❌ 不符合: 最少只有{stats['starlink']['min']:.0f}顆 (低於8顆)")
        
        print(f"   📊 Starlink統計 (≥5°): 平均{stats['starlink']['mean']:.1f}顆, "
              f"標準差{stats['starlink']['std']:.1f}")
        
        # 問題2分析  
        print(f"\n❓ 問題2: OneWeb平均29顆可見，如何選擇8-12顆?")
        print(f"✅ OneWeb統計 (≥5°): 平均{stats['oneweb']['mean']:.1f}顆, "
              f"範圍{stats['oneweb']['min']:.0f}-{stats['oneweb']['max']:.0f}顆")
        
        if stats['oneweb']['min'] >= 8:
            print(f"✅ 可行! 任何時刻都有足夠衛星供選擇 (最少{stats['oneweb']['min']:.0f}顆)")
            print(f"💡 建議策略: 動態選擇仰角最高的8-12顆")
        else:
            print(f"⚠️ 挑戰: 某些時段只有{stats['oneweb']['min']:.0f}顆，需要降低仰角門檻或擴大選擇")
        
        # 問題3分析
        print(f"\n❓ 問題3: 兩星座都8-12顆對LEO換手強化學習研究的意義?")
        print(f"🤔 研究設計考量分析:")
        
        total_candidates = stats['starlink']['mean'] + stats['oneweb']['mean']
        print(f"   📈 總候選池: 平均{total_candidates:.1f}顆衛星")
        
        if total_candidates > 50:
            print(f"   🚀 優勢: 豐富的換手候選集，支援複雜RL算法")
            print(f"   ⚡ 挑戰: 狀態空間龐大，計算複雜度高")
        else:
            print(f"   ⚖️ 均衡: 適中的候選集規模，便於RL訓練")
        
        print(f"\n🎓 學術研究建議:")
        print(f"─────────────────────────────────────────────────────────────")
        
        # 根據數據給出建議
        if stats['starlink']['mean'] > 12 and stats['oneweb']['mean'] < 12:
            print(f"💡 建議1: Starlink採用動態篩選(從{stats['starlink']['mean']:.0f}顆中選12顆)")
            print(f"💡 建議2: OneWeb全部採用(平均{stats['oneweb']['mean']:.0f}顆)")
            print(f"🎯 研究價值: 不對稱設計反映真實星座特性")
        
        print(f"📊 RL狀態空間分析:")
        action_space_symmetric = 24  # 12+12顆
        action_space_asymmetric = int(stats['starlink']['mean'] + stats['oneweb']['mean'])
        
        print(f"   對稱設計(8-12+8-12): 動作空間 ~{action_space_symmetric}")
        print(f"   非對稱設計(實際可見): 動作空間 ~{action_space_asymmetric}")
        
        if action_space_asymmetric > 30:
            print(f"   ⚠️ 建議: 考慮分階段RL訓練或智能預篩選")
        else:
            print(f"   ✅ 適合: 動作空間大小適合RL算法訓練")
        
        return self.analysis_results
    
    def save_results(self, filename="leo_analysis_results.json"):
        """保存分析結果"""
        if not self.analysis_results:
            print("❌ 沒有分析結果可保存")
            return
            
        # 準備可序列化的數據
        serializable_results = {
            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'observation_point': {
                'latitude': self.NTPU_LAT,
                'longitude': self.NTPU_LON,
                'name': 'NTPU'
            },
            'satellite_counts': {
                'starlink_total': len(self.starlink_satellites),
                'oneweb_total': len(self.oneweb_satellites)
            },
            'statistics': self.analysis_results['statistics'],
            'sample_data': []
        }
        
        # 添加樣本數據點
        for i in range(0, len(self.analysis_results['time_points']), 6):  # 每3小時一個點
            result = self.analysis_results['detailed_results'][i]
            serializable_results['sample_data'].append({
                'time': result['time'].isoformat(),
                'starlink_5deg': result['starlink']['>=5deg'],
                'oneweb_5deg': result['oneweb']['>=5deg'],
                'total_5deg': result['starlink']['>=5deg'] + result['oneweb']['>=5deg']
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 分析結果已保存至: {filename}")

def main():
    """主要執行函數"""
    print("🚀 啟動LEO衛星換手研究 - 全量衛星分析")
    
    # 初始化分析器
    analyzer = ComprehensiveLEOAnalysis()
    
    # 載入TLE數據
    analyzer.load_latest_tle_data()
    
    # 執行24小時覆蓋分析
    print(f"\n⏳ 開始執行24小時全量分析...")
    results = analyzer.analyze_24h_coverage()
    
    # 分析選擇策略
    selection_analysis = analyzer.analyze_selection_strategies()
    
    # 生成綜合報告
    analyzer.generate_comprehensive_report()
    
    # 保存結果
    analyzer.save_results("leo_handover_analysis_full.json")
    
    print(f"\n🎉 分析完成!")
    print(f"─────────────────────────────────────────────────────────────")
    
    return analyzer, results

if __name__ == "__main__":
    analyzer, results = main()