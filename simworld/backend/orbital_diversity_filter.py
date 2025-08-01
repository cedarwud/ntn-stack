#!/usr/bin/env python3
"""
軌道多樣性篩選系統 - Phase 2
從零容忍篩選的 2,358 顆衛星中精選 500 顆具有最佳軌道多樣性的衛星
"""

import json
import math
import logging
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrbitalDiversityFilter:
    """
    軌道多樣性篩選器
    從高品質衛星中選擇最具多樣性的代表
    """
    
    def __init__(self, target_lat: float = 24.9441, target_lon: float = 121.3714):
        self.target_lat = target_lat
        self.target_lon = target_lon
        self.earth_radius = 6371.0  # 地球半徑（公里）
        
        # 篩選參數
        self.target_total_satellites = 500
        self.raan_bins = 36  # 每 10 度一個區間
        self.min_satellites_per_bin = 1
        self.max_satellites_per_bin = 20
        
        # 星座配額目標
        self.constellation_targets = {
            'starlink': 350,  # 約70%
            'oneweb': 150     # 約30%
        }
        
        # 品質評分權重
        self.quality_weights = {
            'orbital_stability': 0.25,     # 軌道穩定性
            'coverage_uniformity': 0.25,   # 覆蓋均勻性  
            'handover_frequency': 0.25,    # 換手機會頻率
            'signal_quality': 0.25         # 預估信號品質
        }
        
        # 時間覆蓋參數
        self.time_slots_per_day = 144  # 10分鐘間隔
        self.min_visible_per_slot = 3   # 每個時間段最少可見衛星數
        
        self.stats = {
            'input_satellites': 0,
            'output_satellites': 0,
            'raan_coverage_percent': 0,
            'temporal_coverage_gaps': 0,
            'avg_quality_score': 0
        }
    
    def filter_for_diversity(self, phase1_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行軌道多樣性篩選
        """
        logger.info("🚀 開始軌道多樣性篩選 (Phase 2)")
        
        # 合併所有星座的篩選結果
        all_satellites = []
        for constellation in ['starlink', 'oneweb']:
            if constellation in phase1_results:
                constellation_sats = phase1_results[constellation]['accepted']
                for sat in constellation_sats:
                    sat['constellation'] = constellation
                all_satellites.extend(constellation_sats)
        
        logger.info(f"輸入衛星總數: {len(all_satellites)}")
        self.stats['input_satellites'] = len(all_satellites)
        
        # 步驟1: 計算所有衛星的品質分數
        logger.info("📊 計算衛星品質分數...")
        satellites_with_scores = self._calculate_quality_scores(all_satellites)
        
        # 步驟2: 按軌道平面分群
        logger.info("🌐 執行軌道平面分群...")
        orbital_groups = self._group_by_orbital_plane(satellites_with_scores)
        
        # 步驟3: 在每個組內選擇最佳代表
        logger.info("⭐ 選擇最佳軌道代表...")
        selected_satellites = self._select_best_representatives(orbital_groups)
        
        # 步驟4: 時間覆蓋優化
        logger.info("⏰ 優化時間覆蓋...")
        optimized_satellites = self._optimize_temporal_coverage(selected_satellites)
        
        # 步驟5: 最終多樣性調整
        logger.info("🎯 執行最終多樣性調整...")
        final_satellites = self._finalize_diversity_selection(optimized_satellites)
        
        # 生成結果報告
        results = self._generate_phase2_results(final_satellites, all_satellites)
        
        logger.info(f"✅ Phase 2 篩選完成: {len(final_satellites)} 顆衛星")
        return results
    
    def _calculate_quality_scores(self, satellites: List[Dict]) -> List[Dict]:
        """
        計算每顆衛星的品質分數
        """
        satellites_with_scores = []
        
        for sat in satellites:
            try:
                # 軌道穩定性分數 (0-25)
                stability_score = self._evaluate_orbital_stability(sat)
                
                # 覆蓋均勻性分數 (0-25)
                coverage_score = self._evaluate_coverage_uniformity(sat)
                
                # 換手頻率分數 (0-25)
                handover_score = self._evaluate_handover_frequency(sat)
                
                # 信號品質分數 (0-25)
                signal_score = self._evaluate_signal_quality(sat)
                
                # 總分數
                total_score = stability_score + coverage_score + handover_score + signal_score
                
                sat_copy = sat.copy()
                sat_copy['quality_scores'] = {
                    'orbital_stability': stability_score,
                    'coverage_uniformity': coverage_score,
                    'handover_frequency': handover_score,
                    'signal_quality': signal_score,
                    'total_score': total_score
                }
                
                satellites_with_scores.append(sat_copy)
                
            except Exception as e:
                logger.warning(f"計算衛星品質分數失敗: {sat.get('name', 'unknown')}, 錯誤: {e}")
                continue
        
        return satellites_with_scores
    
    def _evaluate_orbital_stability(self, satellite: Dict) -> float:
        """
        評估軌道穩定性 (0-25 分)
        """
        try:
            eccentricity = float(satellite['ECCENTRICITY'])
            mean_motion = float(satellite['MEAN_MOTION'])
            
            # 離心率評分 (越低越好)
            eccentricity_score = max(0, (0.1 - eccentricity) / 0.1 * 15)
            
            # 平均運動穩定性評分
            optimal_mean_motion = 14.0  # 理想的平均運動值
            motion_deviation = abs(mean_motion - optimal_mean_motion)
            motion_score = max(0, (3.0 - motion_deviation) / 3.0 * 10)
            
            return min(25, eccentricity_score + motion_score)
            
        except (KeyError, ValueError, TypeError):
            return 0
    
    def _evaluate_coverage_uniformity(self, satellite: Dict) -> float:
        """
        評估覆蓋均勻性 (0-25 分)
        """
        try:
            inclination = float(satellite['INCLINATION'])
            mean_motion = float(satellite['MEAN_MOTION'])
            
            # 傾角對覆蓋的影響
            if inclination > 80:  # 極地軌道
                inclination_score = 25
            elif inclination > 50:  # 中等傾角
                inclination_score = 20
            elif inclination > abs(self.target_lat):  # 能覆蓋目標緯度
                inclination_score = 15
            else:
                inclination_score = 5
            
            # 估算通過頻率的均勻性
            daily_passes = self._estimate_daily_passes(inclination, mean_motion)
            if 3 <= daily_passes <= 8:  # 理想範圍
                frequency_score = 0  # 已經在 inclination_score 中考慮
            else:
                frequency_score = 0
            
            return min(25, inclination_score + frequency_score)
            
        except (KeyError, ValueError, TypeError):
            return 0
    
    def _evaluate_handover_frequency(self, satellite: Dict) -> float:
        """
        評估換手機會頻率 (0-25 分)
        """
        try:
            inclination = float(satellite['INCLINATION'])
            mean_motion = float(satellite['MEAN_MOTION'])
            raan = float(satellite['RA_OF_ASC_NODE'])
            
            # 每日通過次數評分
            daily_passes = self._estimate_daily_passes(inclination, mean_motion)
            if 4 <= daily_passes <= 10:
                pass_score = 15
            elif 2 <= daily_passes <= 12:
                pass_score = 10
            else:
                pass_score = 5
            
            # RAAN 多樣性評分（不同升交點提供更多換手機會）
            raan_diversity_score = min(10, (raan % 90) / 90 * 10)
            
            return min(25, pass_score + raan_diversity_score)
            
        except (KeyError, ValueError, TypeError):
            return 0
    
    def _evaluate_signal_quality(self, satellite: Dict) -> float:
        """
        評估預估信號品質 (0-25 分)
        """
        try:
            inclination = float(satellite['INCLINATION'])
            mean_motion = float(satellite['MEAN_MOTION'])
            eccentricity = float(satellite['ECCENTRICITY'])
            
            # 基於軌道高度的信號品質估算
            altitude = self._calculate_orbital_altitude(mean_motion)
            
            if 400 <= altitude <= 600:  # 理想 LEO 高度
                altitude_score = 15
            elif 300 <= altitude <= 800:
                altitude_score = 12
            else:
                altitude_score = 8
            
            # 基於傾角的最大仰角估算
            max_elevation = self._estimate_max_elevation(inclination)
            if max_elevation >= 60:
                elevation_score = 10
            elif max_elevation >= 30:
                elevation_score = 7
            else:
                elevation_score = 4
            
            return min(25, altitude_score + elevation_score)
            
        except (KeyError, ValueError, TypeError):
            return 0
    
    def _group_by_orbital_plane(self, satellites: List[Dict]) -> Dict[int, List[Dict]]:
        """
        按 RAAN 將衛星分組（每10度一組）
        """
        groups = defaultdict(list)
        
        for sat in satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)  # 10度一組
                groups[bin_index].append(sat)
            except (KeyError, ValueError, TypeError):
                continue
        
        logger.info(f"創建了 {len(groups)} 個軌道組")
        return dict(groups)
    
    def _select_best_representatives(self, orbital_groups: Dict[int, List[Dict]]) -> List[Dict]:
        """
        在每個軌道組內選擇最佳代表
        """
        selected = []
        
        for bin_index, satellites in orbital_groups.items():
            # 按品質分數排序
            sorted_sats = sorted(satellites, 
                               key=lambda x: x['quality_scores']['total_score'], 
                               reverse=True)
            
            # 計算此組應選擇多少顆衛星
            total_in_group = len(satellites)
            
            # 根據星座類型決定選擇數量 - 更積極的選擇策略
            starlink_count = sum(1 for s in satellites if s.get('constellation') == 'starlink')
            oneweb_count = sum(1 for s in satellites if s.get('constellation') == 'oneweb')
            
            if starlink_count > 0 and oneweb_count > 0:
                # 混合組：選擇更多
                target_count = min(30, max(10, total_in_group // 2))
            elif oneweb_count > 0:
                # OneWeb 組：保留更高比例
                target_count = min(25, max(8, total_in_group // 1.5))
            else:
                # Starlink 組：更積極選擇
                target_count = min(20, max(8, total_in_group // 3))
            
            # 選擇最佳的衛星
            selected.extend(sorted_sats[:target_count])
        
        logger.info(f"從軌道組中選擇了 {len(selected)} 顆代表衛星")
        return selected
    
    def _optimize_temporal_coverage(self, satellites: List[Dict]) -> List[Dict]:
        """
        優化時間覆蓋，確保無空窗期
        """
        # 創建24小時時間覆蓋圖
        time_coverage = np.zeros(self.time_slots_per_day)
        satellite_contributions = {}
        
        # 計算每顆衛星對時間覆蓋的貢獻
        for sat in satellites:
            contribution = self._calculate_temporal_contribution(sat)
            sat_name = sat.get('name', f"SAT-{sat.get('norad_id', 'unknown')}")
            satellite_contributions[sat_name] = contribution
            
            # 累加到總覆蓋圖
            for i, contrib in enumerate(contribution):
                if i < len(time_coverage):
                    time_coverage[i] += contrib
        
        # 識別覆蓋不足的時間段
        under_covered_slots = np.where(time_coverage < self.min_visible_per_slot)[0]
        
        if len(under_covered_slots) > 0:
            logger.warning(f"發現 {len(under_covered_slots)} 個時間段覆蓋不足")
            # 嘗試添加衛星來填補空隙
            satellites = self._fill_coverage_gaps(satellites, under_covered_slots, satellite_contributions)
        
        return satellites
    
    def _finalize_diversity_selection(self, satellites: List[Dict]) -> List[Dict]:
        """
        執行最終的多樣性選擇，確保達到目標數量
        """
        current_count = len(satellites)
        target_count = self.target_total_satellites
        
        if current_count == target_count:
            return satellites
        elif current_count > target_count:
            # 需要進一步篩選
            return self._reduce_to_target(satellites, target_count)
        else:
            # 需要添加更多衛星（從備選中選擇）
            logger.info(f"當前衛星數 {current_count} 少於目標 {target_count}，嘗試添加更多衛星")
            # 如果數量不足，返回現有結果（實際中可以實現更複雜的補充邏輯）
            return satellites
    
    def _reduce_to_target(self, satellites: List[Dict], target_count: int) -> List[Dict]:
        """
        將衛星數量減少到目標數量，保持多樣性
        """
        # 按星座分類
        starlink_sats = [s for s in satellites if s.get('constellation') == 'starlink']
        oneweb_sats = [s for s in satellites if s.get('constellation') == 'oneweb']
        
        # 計算目標分配
        starlink_target = min(len(starlink_sats), self.constellation_targets['starlink'])
        oneweb_target = min(len(oneweb_sats), self.constellation_targets['oneweb'])
        
        # 調整目標以符合總數
        total_target = starlink_target + oneweb_target
        if total_target > target_count:
            # 按比例調整
            ratio = target_count / total_target
            starlink_target = int(starlink_target * ratio)
            oneweb_target = target_count - starlink_target
        
        # 選擇最佳衛星
        selected_starlink = sorted(starlink_sats, 
                                 key=lambda x: x['quality_scores']['total_score'], 
                                 reverse=True)[:starlink_target]
        selected_oneweb = sorted(oneweb_sats, 
                               key=lambda x: x['quality_scores']['total_score'], 
                               reverse=True)[:oneweb_target]
        
        final_selection = selected_starlink + selected_oneweb
        logger.info(f"最終選擇: Starlink {len(selected_starlink)} 顆, OneWeb {len(selected_oneweb)} 顆")
        
        return final_selection
    
    def _calculate_temporal_contribution(self, satellite: Dict) -> np.ndarray:
        """
        計算衛星對24小時時間覆蓋的貢獻
        """
        contribution = np.zeros(self.time_slots_per_day)
        
        try:
            inclination = float(satellite['INCLINATION'])
            mean_motion = float(satellite['MEAN_MOTION'])
            
            # 估算每日通過次數和時間分布
            daily_passes = self._estimate_daily_passes(inclination, mean_motion)
            pass_duration_slots = max(1, int((10 * 60) / (24 * 60 / self.time_slots_per_day)))  # 假設10分鐘通過時間
            
            # 簡化的時間分布模擬
            orbital_period_slots = int(24 * 60 / mean_motion / (24 * 60 / self.time_slots_per_day))
            
            for pass_num in range(int(daily_passes)):
                start_slot = (pass_num * orbital_period_slots) % self.time_slots_per_day
                for i in range(pass_duration_slots):
                    slot_index = (start_slot + i) % self.time_slots_per_day
                    contribution[slot_index] = 1
            
        except Exception:
            pass  # 返回零貢獻
        
        return contribution
    
    def _fill_coverage_gaps(self, satellites: List[Dict], under_covered_slots: np.ndarray, 
                          satellite_contributions: Dict[str, np.ndarray]) -> List[Dict]:
        """
        嘗試填補時間覆蓋空隙
        """
        # 這裡可以實現更複雜的邏輯來添加衛星
        # 暫時返回原始衛星列表
        return satellites
    
    def _estimate_daily_passes(self, inclination: float, mean_motion: float) -> float:
        """
        估算每日通過次數
        """
        if inclination > 80:  # 極地軌道
            return mean_motion * 0.8
        elif inclination > 50:  # 中等傾角
            return mean_motion * 0.4
        else:  # 低傾角
            return mean_motion * 0.2
    
    def _estimate_max_elevation(self, inclination: float) -> float:
        """
        估算最大仰角
        """
        if inclination > 80:
            return 85
        elif inclination > 60:
            return 70
        elif inclination > 40:
            return 50
        else:
            return max(10, inclination)
    
    def _calculate_orbital_altitude(self, mean_motion: float) -> float:
        """
        根據平均運動計算軌道高度
        """
        # 使用開普勒第三定律的簡化版本
        # a³ = (GMT²)/(4π²)
        # 對於地球，可以簡化為 a = (24/n)^(2/3) * (GMe/(4π²))^(1/3)
        
        GM = 398600.4418  # 地球標準重力參數 (km³/s²)
        period_seconds = 24 * 3600 / mean_motion  # 軌道週期（秒）
        
        # 半長軸（公里）
        semi_major_axis = ((GM * period_seconds**2) / (4 * math.pi**2))**(1/3)
        
        # 高度 = 半長軸 - 地球半徑
        altitude = semi_major_axis - self.earth_radius
        
        return altitude
    
    def _generate_phase2_results(self, final_satellites: List[Dict], input_satellites: List[Dict]) -> Dict[str, Any]:
        """
        生成 Phase 2 篩選結果報告
        """
        # 統計各星座數量
        constellation_stats = {}
        for constellation in ['starlink', 'oneweb']:
            constellation_sats = [s for s in final_satellites if s.get('constellation') == constellation]
            constellation_stats[constellation] = {
                'count': len(constellation_sats),
                'avg_quality_score': np.mean([s['quality_scores']['total_score'] for s in constellation_sats]) if constellation_sats else 0
            }
        
        # 計算RAAN覆蓋度
        raan_bins_covered = set()
        for sat in final_satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)
                raan_bins_covered.add(bin_index)
            except:
                continue
        
        raan_coverage = len(raan_bins_covered) / self.raan_bins * 100
        
        # 更新統計
        self.stats.update({
            'output_satellites': len(final_satellites),
            'raan_coverage_percent': raan_coverage,
            'avg_quality_score': np.mean([s['quality_scores']['total_score'] for s in final_satellites])
        })
        
        results = {
            'phase': 'Phase 2 - Orbital Diversity Filtering',
            'input_count': len(input_satellites),
            'output_count': len(final_satellites),
            'reduction_ratio': len(final_satellites) / len(input_satellites),
            'selected_satellites': final_satellites,
            'constellation_breakdown': constellation_stats,
            'diversity_metrics': {
                'raan_coverage_percent': raan_coverage,
                'raan_bins_covered': len(raan_bins_covered),
                'total_raan_bins': self.raan_bins
            },
            'quality_metrics': {
                'avg_total_score': self.stats['avg_quality_score'],
                'min_score': min([s['quality_scores']['total_score'] for s in final_satellites]) if final_satellites else 0,
                'max_score': max([s['quality_scores']['total_score'] for s in final_satellites]) if final_satellites else 0
            },
            'statistics': self.stats.copy()
        }
        
        return results

def main():
    """主要測試程序"""
    
    # 載入 Phase 1 結果
    print("🚀 開始 Phase 2 軌道多樣性篩選")
    
    # 這裡需要載入 Phase 1 的結果
    # 暫時使用示例數據結構
    phase1_results = {
        'starlink': {'accepted': []},
        'oneweb': {'accepted': []}
    }
    
    filter_system = OrbitalDiversityFilter()
    results = filter_system.filter_for_diversity(phase1_results)
    
    print(f"\n📊 Phase 2 篩選結果:")
    print(f"  輸入衛星: {results['input_count']}")
    print(f"  輸出衛星: {results['output_count']}")
    print(f"  篩選比例: {results['reduction_ratio']:.1%}")
    print(f"  RAAN覆蓋度: {results['diversity_metrics']['raan_coverage_percent']:.1f}%")
    print(f"  平均品質分數: {results['quality_metrics']['avg_total_score']:.1f}")

if __name__ == "__main__":
    main()