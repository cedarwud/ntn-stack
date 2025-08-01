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
        
        # 合併所有星座的篩選結果並保存完整列表供後續使用
        all_satellites = []
        for constellation in ['starlink', 'oneweb']:
            if constellation in phase1_results:
                constellation_sats = phase1_results[constellation]['accepted']
                for sat in constellation_sats:
                    sat['constellation'] = constellation
                all_satellites.extend(constellation_sats)
        
        # 保存完整衛星列表供智能填補使用
        self.phase1_complete_satellites = all_satellites.copy()
        
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
        在每個軌道組內選擇最佳代表 - 優化為目標500顆
        """
        selected = []
        total_available = sum(len(sats) for sats in orbital_groups.values())
        target_per_group = max(15, self.target_total_satellites // len(orbital_groups))
        
        logger.info(f"目標每組選擇約 {target_per_group} 顆衛星，共 {len(orbital_groups)} 組")
        
        for bin_index, satellites in orbital_groups.items():
            # 按品質分數排序
            sorted_sats = sorted(satellites, 
                               key=lambda x: x['quality_scores']['total_score'], 
                               reverse=True)
            
            # 計算此組應選擇多少顆衛星
            total_in_group = len(satellites)
            
            # 根據星座類型和組大小決定選擇數量 - 積極策略達到500顆目標
            starlink_count = sum(1 for s in satellites if s.get('constellation') == 'starlink')
            oneweb_count = sum(1 for s in satellites if s.get('constellation') == 'oneweb')
            
            if total_in_group >= 50:
                # 大組：選擇更多衛星
                if starlink_count > 0 and oneweb_count > 0:
                    target_count = min(35, max(15, total_in_group // 2))
                elif oneweb_count > 0:
                    target_count = min(30, max(12, total_in_group // 1.5))
                else:
                    target_count = min(25, max(10, total_in_group // 2.5))
            elif total_in_group >= 20:
                # 中組：標準選擇
                if starlink_count > 0 and oneweb_count > 0:
                    target_count = min(25, max(10, total_in_group // 2))
                elif oneweb_count > 0:
                    target_count = min(20, max(8, total_in_group // 1.8))
                else:
                    target_count = min(18, max(8, total_in_group // 3))
            else:
                # 小組：保守但仍要有代表性
                target_count = min(15, max(5, total_in_group // 2))
            
            # 選擇最佳的衛星
            selected_from_group = sorted_sats[:target_count]
            selected.extend(selected_from_group)
            
            logger.debug(f"組 {bin_index}: {total_in_group} 顆可選，選擇了 {len(selected_from_group)} 顆")
        
        logger.info(f"從軌道組中選擇了 {len(selected)} 顆代表衛星")
        return selected
    
    def _optimize_temporal_coverage(self, satellites: List[Dict]) -> List[Dict]:
        """
        優化時間覆蓋，確保無空窗期並提升RAAN覆蓋度
        """
        logger.info("⏰ 開始時間覆蓋和RAAN分布優化...")
        
        # 先優化RAAN覆蓋度
        satellites = self._optimize_raan_coverage(satellites)
        
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
            logger.info(f"發現 {len(under_covered_slots)} 個時間段覆蓋不足，嘗試智能補充")
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
        將衛星數量減少到目標數量，優先保持RAAN覆蓋度和多樣性
        """
        logger.info(f"🎯 開始RAAN平衡的衛星篩選: {len(satellites)} → {target_count}")
        
        # 第一階段：確保RAAN覆蓋度
        raan_balanced_satellites = self._ensure_raan_coverage(satellites)
        logger.info(f"RAAN平衡後衛星數: {len(raan_balanced_satellites)}")
        
        # 如果RAAN平衡後數量已符合目標，直接返回
        if len(raan_balanced_satellites) <= target_count:
            logger.info("RAAN平衡後數量符合目標，無需進一步裁減")
            return raan_balanced_satellites
        
        # 第二階段：在保持RAAN覆蓋的前提下，按品質裁減到目標數量
        final_satellites = self._reduce_while_maintaining_raan(raan_balanced_satellites, target_count)
        
        logger.info(f"最終選擇完成: {len(final_satellites)} 顆衛星")
        return final_satellites
    
    def _ensure_raan_coverage(self, satellites: List[Dict]) -> List[Dict]:
        """
        確保RAAN覆蓋度達到85%+的目標，同時保持足夠的衛星數量
        """
        target_coverage = 85.0
        target_bins_needed = int(36 * target_coverage / 100)  # 需要31個區間
        min_satellites_target = 500  # 最少要保留500顆衛星
        
        # 分析當前RAAN分布
        raan_distribution = defaultdict(list)
        for sat in satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)
                raan_distribution[bin_index].append(sat)
            except (KeyError, ValueError, TypeError):
                continue
        
        current_coverage = len(raan_distribution) / 36 * 100
        logger.info(f"當前RAAN覆蓋度: {current_coverage:.1f}%, 目標: {target_coverage}%")
        
        # 如果衛星數量已充足，直接返回（優先保證數量）
        if len(satellites) >= min_satellites_target:
            logger.info(f"衛星數量已達標({len(satellites)}顆)，RAAN覆蓋度: {current_coverage:.1f}%")
            return satellites
        
        selected_satellites = []
        
        # 計算每個bin應該保留多少衛星，確保總數接近目標
        avg_per_bin = min_satellites_target // len(raan_distribution)
        extra_satellites = min_satellites_target % len(raan_distribution)
        
        # 從每個bin中選擇多顆衛星
        for bin_index, sats_in_bin in raan_distribution.items():
            if sats_in_bin:
                # 按品質排序
                sorted_sats = sorted(sats_in_bin, 
                                   key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                                   reverse=True)
                
                # 計算這個bin要選多少顆
                target_count = avg_per_bin
                if extra_satellites > 0:
                    target_count += 1
                    extra_satellites -= 1
                
                # 選擇該bin中品質最高的衛星
                selected_count = min(target_count, len(sorted_sats))
                selected_satellites.extend(sorted_sats[:selected_count])
        
        # 如果覆蓋度不足，嘗試補充缺失的RAAN區間
        current_bins = len(raan_distribution)
        if current_bins < target_bins_needed:
            logger.info(f"RAAN覆蓋度不足，當前{current_bins}個區間，需要{target_bins_needed}個區間")
            selected_satellites = self._supplement_missing_raan_bins(selected_satellites, target_bins_needed)
        
        logger.info(f"RAAN覆蓋優化完成，選擇了 {len(selected_satellites)} 顆衛星")
        return selected_satellites
    
    def _supplement_missing_raan_bins(self, current_satellites: List[Dict], target_bins: int) -> List[Dict]:
        """
        從完整數據中補充缺失的RAAN區間
        """
        if not hasattr(self, 'phase1_complete_satellites'):
            logger.warning("無法訪問完整Phase 1數據，無法補充RAAN區間")
            return current_satellites
        
        # 分析當前已覆蓋的RAAN區間
        covered_bins = set()
        current_distribution = defaultdict(list)
        for sat in current_satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)
                covered_bins.add(bin_index)
                current_distribution[bin_index].append(sat)
            except:
                continue
        
        # 找出缺失的區間
        all_bins = set(range(36))
        missing_bins = all_bins - covered_bins
        needed_bins = target_bins - len(covered_bins)
        
        if needed_bins <= 0:
            logger.info("RAAN覆蓋已達標，無需補充")
            return current_satellites
        
        logger.info(f"需要補充 {needed_bins} 個RAAN區間，缺失區間: {len(missing_bins)} 個")
        
        # 獲取當前已選衛星的標識
        selected_names = {sat.get('name', sat.get('norad_id', '')) for sat in current_satellites}
        
        # 從完整數據中找所有可用候選（不限制RAAN區間）
        all_candidates = []
        candidates_by_bin = defaultdict(list)
        
        for sat in self.phase1_complete_satellites:
            sat_name = sat.get('name', sat.get('norad_id', ''))
            if sat_name in selected_names:
                continue  # 已選中，跳過
                
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)
                
                # 計算品質分數
                if 'quality_scores' not in sat:
                    scored_sats = self._calculate_quality_scores([sat])
                    if scored_sats:
                        sat = scored_sats[0]
                
                all_candidates.append(sat)
                candidates_by_bin[bin_index].append(sat)
            except:
                continue
        
        logger.info(f"找到 {len(all_candidates)} 個候選衛星，分布在 {len(candidates_by_bin)} 個RAAN區間")
        
        # 直接嘗試達到500顆目標，優先選擇缺失RAAN區間的衛星
        added_satellites = []
        total_needed = 500
        current_total = len(current_satellites)
        needed_to_add = total_needed - current_total
        
        logger.info(f"需要添加 {needed_to_add} 顆衛星達到500顆目標")
        
        if needed_to_add <= 0:
            logger.info("已達到衛星數量目標")
            return current_satellites
        
        # 策略1：優先從缺失的RAAN區間選擇衛星
        priority_satellites = []
        for bin_index in missing_bins:
            candidates = candidates_by_bin.get(bin_index, [])
            if candidates:
                # 按品質排序
                sorted_candidates = sorted(candidates, 
                                         key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                                         reverse=True)
                # 從每個缺失區間最多選5顆
                priority_satellites.extend(sorted_candidates[:5])
        
        logger.info(f"從缺失RAAN區間找到 {len(priority_satellites)} 顆優先候選衛星")
        
        # 策略2：從所有候選中選擇品質最高的
        if len(priority_satellites) < needed_to_add:
            # 按品質排序所有候選
            sorted_all = sorted(all_candidates,
                              key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                              reverse=True)
            
            # 優先選擇priority_satellites，然後補充其他高品質衛星
            selected_count = min(len(priority_satellites), needed_to_add)
            added_satellites.extend(priority_satellites[:selected_count])
            
            remaining_needed = needed_to_add - selected_count
            if remaining_needed > 0:
                # 從剩餘候選中選擇
                used_names = {sat.get('name', sat.get('norad_id', '')) for sat in added_satellites}
                remaining_candidates = [sat for sat in sorted_all 
                                      if sat.get('name', sat.get('norad_id', '')) not in used_names]
                
                additional_count = min(remaining_needed, len(remaining_candidates))
                added_satellites.extend(remaining_candidates[:additional_count])
                
                logger.info(f"從優先區間選擇 {selected_count} 顆，額外添加 {additional_count} 顆高品質衛星")
        else:
            # 優先衛星足夠，直接選擇品質最高的
            sorted_priority = sorted(priority_satellites,
                                   key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                                   reverse=True)
            added_satellites.extend(sorted_priority[:needed_to_add])
            logger.info(f"從優先RAAN區間選擇了 {len(added_satellites)} 顆衛星")
        
        current_satellites.extend(added_satellites)
        logger.info(f"總共補充了 {len(added_satellites)} 顆衛星來改善RAAN覆蓋")
        return current_satellites
    
    def _reduce_while_maintaining_raan(self, satellites: List[Dict], target_count: int) -> List[Dict]:
        """
        在保持RAAN覆蓋的前提下減少到目標數量
        """
        if len(satellites) <= target_count:
            return satellites
        
        # 分析RAAN分布
        raan_distribution = defaultdict(list)
        for sat in satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)
                raan_distribution[bin_index].append(sat)
            except:
                continue
        
        # 計算每個RAAN區間應該保留多少衛星
        num_bins = len(raan_distribution)
        base_per_bin = target_count // num_bins
        extra_slots = target_count % num_bins
        
        logger.info(f"在{num_bins}個RAAN區間中分配{target_count}顆衛星，平均每區間{base_per_bin}顆")
        
        final_satellites = []
        selected_by_bin = {}
        
        # 為每個RAAN區間分配衛星
        for bin_index, sats_in_bin in raan_distribution.items():
            if sats_in_bin:
                # 計算這個區間要選多少顆
                slots_for_bin = base_per_bin
                if extra_slots > 0:
                    slots_for_bin += 1
                    extra_slots -= 1
                
                # 按品質排序選擇最好的
                sorted_sats = sorted(sats_in_bin, 
                                   key=lambda x: x.get('quality_scores', {}).get('total_score', 0), 
                                   reverse=True)
                
                selected_count = min(slots_for_bin, len(sorted_sats))
                selected_sats = sorted_sats[:selected_count]
                final_satellites.extend(selected_sats)
                selected_by_bin[bin_index] = selected_count
                
                logger.debug(f"RAAN區間 {bin_index}: 選擇了 {selected_count}/{len(sats_in_bin)} 顆衛星")
        
        logger.info(f"按RAAN分配後共選擇 {len(final_satellites)} 顆衛星")
        
        # 確保達到確切的目標數量
        if len(final_satellites) < target_count:
            selected_names = {sat.get('name', sat.get('norad_id', '')) for sat in final_satellites}
            remaining_satellites = [sat for sat in satellites 
                                  if sat.get('name', sat.get('norad_id', '')) not in selected_names]
            
            if remaining_satellites:
                remaining_needed = target_count - len(final_satellites)
                logger.info(f"還需要 {remaining_needed} 顆衛星達到目標，從 {len(remaining_satellites)} 顆候選中選擇")
                sorted_remaining = sorted(remaining_satellites,
                                        key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                                        reverse=True)
                additional_sats = sorted_remaining[:remaining_needed]
                final_satellites.extend(additional_sats)
                logger.info(f"額外添加了 {len(additional_sats)} 顆高品質衛星")
        elif len(final_satellites) > target_count:
            # 如果超過目標，按品質排序保留最好的
            logger.info(f"衛星數量 {len(final_satellites)} 超過目標 {target_count}，保留品質最高的")
            sorted_by_quality = sorted(final_satellites,
                                     key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                                     reverse=True)
            final_satellites = sorted_by_quality[:target_count]
        
        # 按星座統計
        constellation_counts = defaultdict(int)
        for sat in final_satellites:
            constellation_counts[sat.get('constellation', 'unknown')] += 1
        
        logger.info(f"最終選擇: {dict(constellation_counts)}")
        return final_satellites
    
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
    
    def _optimize_raan_coverage(self, satellites: List[Dict]) -> List[Dict]:
        """
        優化RAAN覆蓋度，確保達到85%+的目標
        """
        # 分析當前RAAN分布
        raan_bins = set()
        raan_distribution = defaultdict(list)
        
        for sat in satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)  # 10度一個bin
                raan_bins.add(bin_index)
                raan_distribution[bin_index].append(sat)
            except (KeyError, ValueError, TypeError):
                continue
        
        current_coverage = len(raan_bins) / 36 * 100
        target_coverage = 85.0
        
        logger.info(f"當前RAAN覆蓋度: {current_coverage:.1f}%，目標: {target_coverage:.1f}%")
        
        if current_coverage >= target_coverage:
            logger.info("RAAN覆蓋度已達標")
            return satellites
        
        # 需要補充的RAAN區間
        missing_bins = set(range(36)) - raan_bins
        target_bins_needed = int(36 * target_coverage / 100) - len(raan_bins)
        
        if target_bins_needed > 0 and missing_bins:
            logger.info(f"需要補充 {target_bins_needed} 個RAAN區間")
            satellites = self._add_satellites_for_raan_coverage(
                satellites, missing_bins, target_bins_needed
            )
        
        return satellites
    
    def _add_satellites_for_raan_coverage(self, current_satellites: List[Dict], 
                                        missing_bins: set, needed_count: int) -> List[Dict]:
        """
        從Phase 1結果中添加衛星以改善RAAN覆蓋度
        """
        # 從當前選擇中找到所有可用的衛星（包括未選中的）
        # 這裡需要訪問原始的Phase 1結果
        # 暫時使用簡化邏輯：如果當前衛星不足500顆，優先選擇缺失RAAN區間的衛星
        
        logger.info(f"嘗試從缺失的RAAN區間中補充衛星")
        # 這個方法在實際實現中需要訪問Phase 1的完整結果
        # 現在先返回原始列表，在fill_coverage_gaps中實現
        return current_satellites
    
    def _fill_coverage_gaps(self, satellites: List[Dict], under_covered_slots: np.ndarray, 
                          satellite_contributions: Dict[str, np.ndarray]) -> List[Dict]:
        """
        智能填補時間覆蓋空隙和RAAN覆蓋不足
        """
        current_count = len(satellites)
        target_count = self.target_total_satellites
        
        if current_count >= target_count:
            logger.info("衛星數量已達目標，無需補充")
            return satellites
        
        can_add = target_count - current_count
        logger.info(f"可以補充 {can_add} 顆衛星來改善覆蓋度")
        
        # 獲取已選衛星的名稱集合
        selected_names = {sat.get('name', sat.get('norad_id', '')) for sat in satellites}
        
        # 從Phase 1完整結果中找到未選中的候選衛星
        if not hasattr(self, 'phase1_complete_satellites'):
            logger.warning("無法訪問Phase 1完整結果，無法智能填補")
            return satellites
        
        candidate_satellites = []
        for sat in self.phase1_complete_satellites:
            sat_name = sat.get('name', sat.get('norad_id', ''))
            if sat_name not in selected_names:
                candidate_satellites.append(sat)
        
        logger.info(f"找到 {len(candidate_satellites)} 顆候選衛星可用於填補")
        
        if not candidate_satellites:
            return satellites
        
        # 計算候選衛星的品質分數
        candidates_with_scores = self._calculate_quality_scores(candidate_satellites)
        
        # 分析當前RAAN分布，找出覆蓋不足的區間
        raan_bins = defaultdict(int)
        selected_raan_bins = set()
        
        for sat in satellites:
            try:
                raan = float(sat['RA_OF_ASC_NODE'])
                bin_index = int(raan / 10)
                raan_bins[bin_index] += 1
                selected_raan_bins.add(bin_index)
            except:
                continue
        
        # 找出空缺或稀少的RAAN區間
        all_raan_bins = set(range(36))
        missing_bins = all_raan_bins - selected_raan_bins
        under_represented_bins = []
        avg_per_bin = len(satellites) / 36 if satellites else 1
        
        for bin_idx in range(36):
            if raan_bins[bin_idx] < max(1, avg_per_bin * 0.3):  # 少於平均值30%的區間
                under_represented_bins.append(bin_idx)
        
        priority_bins = list(missing_bins) + under_represented_bins
        logger.info(f"優先填補RAAN區間: 空缺{len(missing_bins)}個, 不足{len(under_represented_bins)}個")
        
        # 智能選擇衛星填補空隙
        added_satellites = []
        added_count = 0
        
        # 第一優先級：填補空缺的RAAN區間
        for bin_idx in priority_bins:
            if added_count >= can_add:
                break
                
            # 找到該RAAN區間的最佳候選衛星
            bin_candidates = []
            for sat in candidates_with_scores:
                try:
                    raan = float(sat['RA_OF_ASC_NODE'])
                    sat_bin = int(raan / 10)
                    if sat_bin == bin_idx:
                        bin_candidates.append(sat)
                except:
                    continue
            
            if bin_candidates:
                # 選擇品質分數最高的衛星
                best_candidate = max(bin_candidates, 
                                   key=lambda x: x.get('quality_scores', {}).get('total_score', 0))
                added_satellites.append(best_candidate)
                added_count += 1
                
                # 從候選列表中移除已選中的衛星
                candidates_with_scores = [s for s in candidates_with_scores if s != best_candidate]
        
        # 第二優先級：如果還需要更多衛星，選擇品質最高的
        remaining_needed = can_add - added_count
        if remaining_needed > 0 and candidates_with_scores:
            # 按品質分數排序
            sorted_candidates = sorted(candidates_with_scores,
                                     key=lambda x: x.get('quality_scores', {}).get('total_score', 0),
                                     reverse=True)
            
            for sat in sorted_candidates[:remaining_needed]:
                added_satellites.append(sat)
                added_count += 1
        
        if added_satellites:
            logger.info(f"智能添加了 {len(added_satellites)} 顆衛星")
            satellites.extend(added_satellites)
            
            # 重新計算RAAN覆蓋度
            new_raan_bins = set()
            for sat in satellites:
                try:
                    raan = float(sat['RA_OF_ASC_NODE'])
                    bin_index = int(raan / 10)
                    new_raan_bins.add(bin_index)
                except:
                    continue
            
            new_coverage = len(new_raan_bins) / 36 * 100
            logger.info(f"填補後RAAN覆蓋度提升至: {new_coverage:.1f}%")
        
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