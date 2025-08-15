# 🛰️ A1: 模擬退火動態池最佳化器
"""
Simulated Annealing Dynamic Pool Optimizer - 核心最佳化演算法
功能: 使用模擬退火演算法規劃時空分散的衛星池
目標: Starlink 96顆 + OneWeb 38顆，確保10-15/3-6顆隨時可見
"""

import asyncio
import logging
import random
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json
import numpy as np

class ConstraintType(Enum):
    """約束類型"""
    HARD = "HARD"    # 硬約束 - 必須滿足
    SOFT = "SOFT"    # 軟約束 - 優化目標

@dataclass
class SatellitePoolSolution:
    """衛星池解決方案"""
    starlink_satellites: List[str]  # Starlink衛星ID列表
    oneweb_satellites: List[str]    # OneWeb衛星ID列表
    
    # 評估指標
    cost: float
    visibility_compliance: float    # 可見性合規度
    temporal_distribution: float    # 時空分佈品質
    signal_quality: float          # 信號品質
    
    # 約束滿足情況
    constraints_satisfied: Dict[str, bool]
    
    def get_total_satellites(self) -> int:
        return len(self.starlink_satellites) + len(self.oneweb_satellites)

@dataclass
class VisibilityWindow:
    """可見時間窗口"""
    satellite_id: str
    start_minute: int
    end_minute: int
    duration: int
    peak_elevation: float
    average_rsrp: float

@dataclass
class CoverageMetrics:
    """覆蓋指標"""
    timestamp: datetime
    visible_starlink_count: int
    visible_oneweb_count: int
    total_visible_count: int
    meets_starlink_target: bool  # 10-15顆
    meets_oneweb_target: bool    # 3-6顆
    meets_overall_target: bool

class SimulatedAnnealingOptimizer:
    """模擬退火動態池最佳化器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # NTPU觀測點座標
        self.observer_lat = 24.9441667
        self.observer_lon = 121.3713889
        
        # 目標規格 (⚠️ 池大小為預估值，待程式驗證)
        self.targets = {
            'starlink': {
                'pool_size': 96,  # ⚠️ 預估值，實際數量待模擬退火驗證
                'visible_range': (10, 15),
                'elevation_threshold': 5.0,
                'orbit_period_minutes': 96
            },
            'oneweb': {
                'pool_size': 38,  # ⚠️ 預估值，實際數量待模擬退火驗證
                'visible_range': (3, 6),
                'elevation_threshold': 10.0,
                'orbit_period_minutes': 109
            }
        }
        
        # 模擬退火參數
        self.annealing_params = {
            'initial_temperature': 1000.0,
            'cooling_rate': 0.95,
            'min_temperature': 1.0,
            'max_iterations': 10000,
            'plateau_tolerance': 100,  # 停滯容忍次數
            'acceptance_probability_threshold': 0.01
        }
        
        # 約束權重
        self.constraint_weights = {
            # 硬約束 (高懲罰)
            'visibility_violation': 10000.0,
            'temporal_clustering': 5000.0,
            'pool_size_violation': 8000.0,
            
            # 軟約束 (優化目標)
            'signal_quality': 100.0,
            'orbital_diversity': 50.0,
            'handover_opportunity': 75.0
        }
        
        # 最佳化統計
        self.optimization_stats = {
            'iterations': 0,
            'temperature_history': [],
            'cost_history': [],
            'best_cost': float('inf'),
            'best_iteration': 0,
            'acceptance_rate': 0.0,
            'constraint_violations': {}
        }
    
    async def optimize_satellite_pools(self, 
                                     starlink_candidates: List,
                                     oneweb_candidates: List,
                                     orbital_positions: Dict) -> SatellitePoolSolution:
        """使用模擬退火最佳化衛星池"""
        self.logger.info("🔥 開始模擬退火最佳化...")
        
        # 1. 生成初始解
        initial_solution = await self._generate_initial_solution(
            starlink_candidates, oneweb_candidates
        )
        
        self.logger.info(f"🎯 初始解: Starlink {len(initial_solution.starlink_satellites)}顆, OneWeb {len(initial_solution.oneweb_satellites)}顆")
        
        # 2. 執行模擬退火最佳化
        best_solution = await self._simulated_annealing_optimization(
            initial_solution, starlink_candidates, oneweb_candidates, orbital_positions
        )
        
        # 3. 驗證最終解
        final_verification = await self._verify_final_solution(best_solution, orbital_positions)
        
        self.logger.info(f"✅ 最佳化完成:")
        self.logger.info(f"   最佳成本: {best_solution.cost:.2f}")
        self.logger.info(f"   可見性合規: {best_solution.visibility_compliance:.1%}")
        self.logger.info(f"   時空分佈: {best_solution.temporal_distribution:.1%}")
        self.logger.info(f"   最佳化迭代: {self.optimization_stats['best_iteration']}")
        
        return best_solution
    
    async def _generate_initial_solution(self, 
                                       starlink_candidates: List,
                                       oneweb_candidates: List) -> SatellitePoolSolution:
        """生成初始解決方案"""
        
        # 隨機選擇初始衛星池
        starlink_pool = random.sample(
            starlink_candidates, 
            min(self.targets['starlink']['pool_size'], len(starlink_candidates))
        )
        oneweb_pool = random.sample(
            oneweb_candidates,
            min(self.targets['oneweb']['pool_size'], len(oneweb_candidates))
        )
        
        # 評估初始解
        initial_cost = await self._evaluate_solution_cost(
            starlink_pool, oneweb_pool, {}  # 簡化初始評估
        )
        
        return SatellitePoolSolution(
            starlink_satellites=[sat.satellite_id for sat in starlink_pool],
            oneweb_satellites=[sat.satellite_id for sat in oneweb_pool],
            cost=initial_cost,
            visibility_compliance=0.0,
            temporal_distribution=0.0,
            signal_quality=0.0,
            constraints_satisfied={}
        )
    
    async def _simulated_annealing_optimization(self,
                                              initial_solution: SatellitePoolSolution,
                                              starlink_candidates: List,
                                              oneweb_candidates: List,
                                              orbital_positions: Dict) -> SatellitePoolSolution:
        """模擬退火最佳化核心演算法"""
        
        current_solution = initial_solution
        best_solution = initial_solution
        
        current_cost = current_solution.cost
        best_cost = current_cost
        
        temperature = self.annealing_params['initial_temperature']
        cooling_rate = self.annealing_params['cooling_rate']
        min_temperature = self.annealing_params['min_temperature']
        max_iterations = self.annealing_params['max_iterations']
        
        iteration = 0
        accepted_moves = 0
        plateau_counter = 0
        
        self.logger.info(f"🌡️ 開始模擬退火: 初始溫度={temperature}, 冷卻率={cooling_rate}")
        
        while temperature > min_temperature and iteration < max_iterations:
            # 生成鄰域解
            neighbor_solution = await self._generate_neighbor_solution(
                current_solution, starlink_candidates, oneweb_candidates
            )
            
            # 評估鄰域解
            neighbor_cost = await self._evaluate_solution_cost(
                neighbor_solution.starlink_satellites,
                neighbor_solution.oneweb_satellites,
                orbital_positions
            )
            neighbor_solution.cost = neighbor_cost
            
            # 接受準則 (Metropolis準則)
            if self._accept_solution(current_cost, neighbor_cost, temperature):
                current_solution = neighbor_solution
                current_cost = neighbor_cost
                accepted_moves += 1
                
                # 更新最佳解
                if current_cost < best_cost:
                    best_solution = current_solution
                    best_cost = current_cost
                    self.optimization_stats['best_iteration'] = iteration
                    plateau_counter = 0  # 重置停滯計數
                    
                    self.logger.info(f"🏆 新最佳解! 迭代{iteration}, 成本={best_cost:.2f}, 溫度={temperature:.1f}")
                else:
                    plateau_counter += 1
            else:
                plateau_counter += 1
            
            # 溫度冷卻
            temperature *= cooling_rate
            iteration += 1
            
            # 記錄統計
            if iteration % 100 == 0:
                acceptance_rate = accepted_moves / 100 if iteration >= 100 else accepted_moves / iteration
                self.logger.info(f"🔄 迭代{iteration}: 成本={current_cost:.2f}, 溫度={temperature:.1f}, 接受率={acceptance_rate:.1%}")
                self.optimization_stats['temperature_history'].append(temperature)
                self.optimization_stats['cost_history'].append(current_cost)
                accepted_moves = 0  # 重置計數
            
            # 停滯檢查
            if plateau_counter > self.annealing_params['plateau_tolerance']:
                self.logger.info(f"⏹️ 檢測到停滯，提前結束最佳化 (迭代{iteration})")
                break
        
        self.optimization_stats['iterations'] = iteration
        self.optimization_stats['best_cost'] = best_cost
        
        # 計算最終指標
        best_solution = await self._calculate_solution_metrics(best_solution, orbital_positions)
        
        return best_solution
    
    async def _generate_neighbor_solution(self,
                                        current: SatellitePoolSolution,
                                        starlink_candidates: List,
                                        oneweb_candidates: List) -> SatellitePoolSolution:
        """生成鄰域解決方案"""
        
        # 複製當前解
        new_starlink = current.starlink_satellites.copy()
        new_oneweb = current.oneweb_satellites.copy()
        
        # 隨機選擇操作類型
        operation = random.choice(['replace_starlink', 'replace_oneweb', 'swap_within_constellation'])
        
        try:
            if operation == 'replace_starlink' and starlink_candidates:
                # 替換一顆Starlink衛星
                if new_starlink:
                    old_sat = random.choice(new_starlink)
                    new_starlink.remove(old_sat)
                    
                    # 選擇新衛星 (排除已選中的)
                    available = [sat.satellite_id for sat in starlink_candidates 
                               if sat.satellite_id not in new_starlink]
                    if available:
                        new_sat = random.choice(available)
                        new_starlink.append(new_sat)
            
            elif operation == 'replace_oneweb' and oneweb_candidates:
                # 替換一顆OneWeb衛星
                if new_oneweb:
                    old_sat = random.choice(new_oneweb)
                    new_oneweb.remove(old_sat)
                    
                    available = [sat.satellite_id for sat in oneweb_candidates 
                               if sat.satellite_id not in new_oneweb]
                    if available:
                        new_sat = random.choice(available)
                        new_oneweb.append(new_sat)
            
            elif operation == 'swap_within_constellation':
                # 星座內衛星交換
                if random.choice([True, False]) and len(new_starlink) >= 2:
                    # Starlink內交換
                    idx1, idx2 = random.sample(range(len(new_starlink)), 2)
                    new_starlink[idx1], new_starlink[idx2] = new_starlink[idx2], new_starlink[idx1]
                elif len(new_oneweb) >= 2:
                    # OneWeb內交換
                    idx1, idx2 = random.sample(range(len(new_oneweb)), 2)
                    new_oneweb[idx1], new_oneweb[idx2] = new_oneweb[idx2], new_oneweb[idx1]
                    
        except Exception as e:
            self.logger.warning(f"⚠️ 鄰域解生成失敗: {e}")
            # 返回原解
            pass
        
        return SatellitePoolSolution(
            starlink_satellites=new_starlink,
            oneweb_satellites=new_oneweb,
            cost=float('inf'),  # 待計算
            visibility_compliance=0.0,
            temporal_distribution=0.0,
            signal_quality=0.0,
            constraints_satisfied={}
        )
    
    def _accept_solution(self, current_cost: float, neighbor_cost: float, temperature: float) -> bool:
        """模擬退火接受準則"""
        
        if neighbor_cost < current_cost:
            return True  # 更好的解直接接受
        else:
            # 較差的解以一定機率接受 (避免局部最優)
            delta_cost = neighbor_cost - current_cost
            probability = math.exp(-delta_cost / temperature)
            
            # 避免溫度過低時的數值溢出
            if probability > self.annealing_params['acceptance_probability_threshold']:
                return random.random() < probability
            else:
                return False
    
    async def _evaluate_solution_cost(self,
                                    starlink_satellites: List[str],
                                    oneweb_satellites: List[str],
                                    orbital_positions: Dict) -> float:
        """評估解決方案成本"""
        
        total_cost = 0.0
        
        try:
            # 1. 硬約束檢查
            visibility_cost = await self._evaluate_visibility_constraints(
                starlink_satellites, oneweb_satellites, orbital_positions
            )
            total_cost += visibility_cost * self.constraint_weights['visibility_violation']
            
            # 2. 時空分佈約束
            temporal_cost = await self._evaluate_temporal_distribution(
                starlink_satellites, oneweb_satellites, orbital_positions
            )
            total_cost += temporal_cost * self.constraint_weights['temporal_clustering']
            
            # 3. 池大小約束
            size_cost = self._evaluate_pool_size_constraints(
                starlink_satellites, oneweb_satellites
            )
            total_cost += size_cost * self.constraint_weights['pool_size_violation']
            
            # 4. 軟約束優化
            signal_cost = await self._evaluate_signal_quality(
                starlink_satellites, oneweb_satellites, orbital_positions
            )
            total_cost += signal_cost * self.constraint_weights['signal_quality']
            
            orbital_cost = await self._evaluate_orbital_diversity(
                starlink_satellites, oneweb_satellites
            )
            total_cost += orbital_cost * self.constraint_weights['orbital_diversity']
            
        except Exception as e:
            self.logger.warning(f"⚠️ 成本評估失敗: {e}")
            return float('inf')  # 評估失敗的解給予無限大成本
        
        return total_cost
    
    async def _evaluate_visibility_constraints(self,
                                             starlink_sats: List[str],
                                             oneweb_sats: List[str],
                                             orbital_positions: Dict) -> float:
        """評估可見性約束違反程度"""
        
        violation_cost = 0.0
        
        try:
            # 模擬96分鐘時間軸
            time_points = 192  # 96分鐘 × 2個時間點/分鐘
            
            for time_idx in range(time_points):
                # 計算每個時間點的可見衛星數
                visible_starlink = 0
                visible_oneweb = 0
                
                for sat_id in starlink_sats:
                    if self._is_satellite_visible(sat_id, time_idx, orbital_positions, 5.0):
                        visible_starlink += 1
                
                for sat_id in oneweb_sats:
                    if self._is_satellite_visible(sat_id, time_idx, orbital_positions, 10.0):
                        visible_oneweb += 1
                
                # 檢查可見性約束
                starlink_target = self.targets['starlink']['visible_range']
                oneweb_target = self.targets['oneweb']['visible_range']
                
                if not (starlink_target[0] <= visible_starlink <= starlink_target[1]):
                    violation_cost += 1.0  # 每個違反時間點懲罰1分
                
                if not (oneweb_target[0] <= visible_oneweb <= oneweb_target[1]):
                    violation_cost += 1.0
            
            # 正規化為違反比例
            return violation_cost / (time_points * 2)  # 最大違反數 = time_points * 2 (starlink + oneweb)
            
        except Exception as e:
            self.logger.warning(f"⚠️ 可見性約束評估失敗: {e}")
            return 10.0  # 返回高懲罰值
    
    async def _evaluate_temporal_distribution(self,
                                            starlink_sats: List[str],
                                            oneweb_sats: List[str],
                                            orbital_positions: Dict) -> float:
        """評估時空分佈品質"""
        
        clustering_penalty = 0.0
        
        try:
            # 分析衛星出現時間的聚集程度
            starlink_appearances = []
            oneweb_appearances = []
            
            for sat_id in starlink_sats + oneweb_sats:
                # 找到衛星首次可見的時間點
                for time_idx in range(192):
                    threshold = 5.0 if sat_id in starlink_sats else 10.0
                    if self._is_satellite_visible(sat_id, time_idx, orbital_positions, threshold):
                        if sat_id in starlink_sats:
                            starlink_appearances.append(time_idx)
                        else:
                            oneweb_appearances.append(time_idx)
                        break
            
            # 計算時間聚集懲罰
            for constellation_appearances in [starlink_appearances, oneweb_appearances]:
                if len(constellation_appearances) > 1:
                    constellation_appearances.sort()
                    
                    # 檢查相鄰衛星的時間間隔
                    for i in range(len(constellation_appearances) - 1):
                        time_gap = constellation_appearances[i + 1] - constellation_appearances[i]
                        
                        # 如果間隔太小（<15個時間點，約7.5分鐘），給予懲罰
                        if time_gap < 15:
                            clustering_penalty += (15 - time_gap) / 15.0
            
            return clustering_penalty
            
        except Exception as e:
            self.logger.warning(f"⚠️ 時空分佈評估失敗: {e}")
            return 5.0
    
    def _evaluate_pool_size_constraints(self,
                                      starlink_sats: List[str],
                                      oneweb_sats: List[str]) -> float:
        """評估池大小約束"""
        
        size_violation = 0.0
        
        # Starlink池大小約束
        starlink_target = self.targets['starlink']['pool_size']
        starlink_actual = len(starlink_sats)
        starlink_diff = abs(starlink_actual - starlink_target)
        size_violation += starlink_diff / starlink_target
        
        # OneWeb池大小約束
        oneweb_target = self.targets['oneweb']['pool_size']
        oneweb_actual = len(oneweb_sats)
        oneweb_diff = abs(oneweb_actual - oneweb_target)
        size_violation += oneweb_diff / oneweb_target
        
        return size_violation
    
    async def _evaluate_signal_quality(self,
                                     starlink_sats: List[str],
                                     oneweb_sats: List[str],
                                     orbital_positions: Dict) -> float:
        """評估信號品質"""
        
        # 簡化信號品質評估
        # 實際實現需要考慮RSRP、SINR等指標
        quality_score = 0.0
        
        try:
            total_satellites = len(starlink_sats) + len(oneweb_sats)
            if total_satellites == 0:
                return 1.0  # 沒有衛星返回懲罰
            
            # 基於衛星數量的簡化評分
            expected_total = self.targets['starlink']['pool_size'] + self.targets['oneweb']['pool_size']
            quality_score = abs(total_satellites - expected_total) / expected_total
            
            return quality_score
            
        except Exception as e:
            self.logger.warning(f"⚠️ 信號品質評估失敗: {e}")
            return 1.0
    
    async def _evaluate_orbital_diversity(self,
                                        starlink_sats: List[str],
                                        oneweb_sats: List[str]) -> float:
        """評估軌道多樣性"""
        
        # 簡化軌道多樣性評估
        # 實際實現需要考慮軌道傾角、RAAN等參數分佈
        diversity_score = 0.0
        
        # 基於衛星數量分佈的簡化評分
        total_sats = len(starlink_sats) + len(oneweb_sats)
        if total_sats == 0:
            return 1.0
        
        # 星座平衡度評估
        starlink_ratio = len(starlink_sats) / total_sats
        expected_starlink_ratio = self.targets['starlink']['pool_size'] / (
            self.targets['starlink']['pool_size'] + self.targets['oneweb']['pool_size']
        )
        
        diversity_score = abs(starlink_ratio - expected_starlink_ratio)
        
        return diversity_score
    
    def _is_satellite_visible(self,
                            satellite_id: str,
                            time_index: int,
                            orbital_positions: Dict,
                            elevation_threshold: float) -> bool:
        """檢查衛星在指定時間點是否可見"""
        
        try:
            if satellite_id not in orbital_positions:
                return False
            
            positions = orbital_positions[satellite_id]
            if time_index >= len(positions):
                return False
            
            position = positions[time_index]
            return position.elevation_deg >= elevation_threshold
            
        except Exception:
            return False
    
    async def _calculate_solution_metrics(self,
                                        solution: SatellitePoolSolution,
                                        orbital_positions: Dict) -> SatellitePoolSolution:
        """計算解決方案的詳細指標"""
        
        try:
            # 計算可見性合規度
            compliance = await self._calculate_visibility_compliance(
                solution.starlink_satellites, solution.oneweb_satellites, orbital_positions
            )
            solution.visibility_compliance = compliance
            
            # 計算時空分佈品質
            distribution = await self._calculate_temporal_distribution_quality(
                solution.starlink_satellites, solution.oneweb_satellites, orbital_positions
            )
            solution.temporal_distribution = distribution
            
            # 計算信號品質
            signal_quality = await self._calculate_signal_quality_score(
                solution.starlink_satellites, solution.oneweb_satellites, orbital_positions
            )
            solution.signal_quality = signal_quality
            
        except Exception as e:
            self.logger.warning(f"⚠️ 解決方案指標計算失敗: {e}")
        
        return solution
    
    async def _calculate_visibility_compliance(self,
                                             starlink_sats: List[str],
                                             oneweb_sats: List[str],
                                             orbital_positions: Dict) -> float:
        """計算可見性合規度"""
        
        compliant_points = 0
        total_points = 192  # 96分鐘 × 2個時間點/分鐘
        
        for time_idx in range(total_points):
            visible_starlink = sum(1 for sat in starlink_sats 
                                 if self._is_satellite_visible(sat, time_idx, orbital_positions, 5.0))
            visible_oneweb = sum(1 for sat in oneweb_sats 
                               if self._is_satellite_visible(sat, time_idx, orbital_positions, 10.0))
            
            starlink_ok = 10 <= visible_starlink <= 15
            oneweb_ok = 3 <= visible_oneweb <= 6
            
            if starlink_ok and oneweb_ok:
                compliant_points += 1
        
        return compliant_points / total_points
    
    async def _calculate_temporal_distribution_quality(self,
                                                     starlink_sats: List[str],
                                                     oneweb_sats: List[str],
                                                     orbital_positions: Dict) -> float:
        """計算時空分佈品質"""
        
        # 簡化分佈品質計算
        # 基於衛星出現時間的方差
        try:
            all_appearances = []
            
            for sat_id in starlink_sats + oneweb_sats:
                for time_idx in range(192):
                    threshold = 5.0 if sat_id in starlink_sats else 10.0
                    if self._is_satellite_visible(sat_id, time_idx, orbital_positions, threshold):
                        all_appearances.append(time_idx)
                        break
            
            if len(all_appearances) <= 1:
                return 0.0
            
            # 計算分佈均勻度 (基於標準差)
            mean_time = np.mean(all_appearances)
            std_time = np.std(all_appearances)
            
            # 正規化分佈品質 (標準差越大，分佈越好)
            max_possible_std = 192 / 4  # 理論最大標準差
            distribution_quality = min(1.0, std_time / max_possible_std)
            
            return distribution_quality
            
        except Exception as e:
            self.logger.warning(f"⚠️ 時空分佈品質計算失敗: {e}")
            return 0.0
    
    async def _calculate_signal_quality_score(self,
                                            starlink_sats: List[str],
                                            oneweb_sats: List[str],
                                            orbital_positions: Dict) -> float:
        """計算信號品質評分"""
        
        # 簡化信號品質評分
        # 實際實現需要考慮RSRP分佈、SINR等指標
        
        try:
            total_satellites = len(starlink_sats) + len(oneweb_sats)
            expected_total = self.targets['starlink']['pool_size'] + self.targets['oneweb']['pool_size']
            
            if expected_total == 0:
                return 0.0
            
            # 基於衛星數量完整度的評分
            completeness = total_satellites / expected_total
            quality_score = min(1.0, completeness)
            
            return quality_score
            
        except Exception as e:
            self.logger.warning(f"⚠️ 信號品質評分計算失敗: {e}")
            return 0.0
    
    async def _verify_final_solution(self,
                                   solution: SatellitePoolSolution,
                                   orbital_positions: Dict) -> Dict[str, bool]:
        """驗證最終解決方案"""
        
        verification_results = {
            'starlink_pool_size_ok': len(solution.starlink_satellites) == self.targets['starlink']['pool_size'],
            'oneweb_pool_size_ok': len(solution.oneweb_satellites) == self.targets['oneweb']['pool_size'],
            'visibility_compliance_ok': solution.visibility_compliance >= 0.90,
            'temporal_distribution_ok': solution.temporal_distribution >= 0.70,
            'signal_quality_ok': solution.signal_quality >= 0.80
        }
        
        solution.constraints_satisfied = verification_results
        
        all_constraints_satisfied = all(verification_results.values())
        
        if all_constraints_satisfied:
            self.logger.info("✅ 所有約束條件滿足")
        else:
            failed_constraints = [k for k, v in verification_results.items() if not v]
            self.logger.warning(f"⚠️ 未滿足的約束: {failed_constraints}")
        
        return verification_results
    
    async def export_optimization_results(self,
                                        solution: SatellitePoolSolution,
                                        output_path: str):
        """匯出最佳化結果"""
        try:
            export_data = {
                'optimization_metadata': {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'algorithm': 'simulated_annealing',
                    'targets': self.targets,
                    'annealing_params': self.annealing_params
                },
                'optimization_statistics': self.optimization_stats,
                'final_solution': {
                    'starlink_satellites': solution.starlink_satellites,
                    'oneweb_satellites': solution.oneweb_satellites,
                    'total_satellites': solution.get_total_satellites(),
                    'cost': solution.cost,
                    'visibility_compliance': solution.visibility_compliance,
                    'temporal_distribution': solution.temporal_distribution,
                    'signal_quality': solution.signal_quality,
                    'constraints_satisfied': solution.constraints_satisfied
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"📊 最佳化結果已匯出至: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 最佳化結果匯出失敗: {e}")

# 使用範例
async def main():
    """A1_SimulatedAnnealing最佳化器使用範例"""
    
    config = {
        'optimization_params': {
            'max_iterations': 5000,
            'initial_temperature': 1000.0,
            'cooling_rate': 0.95
        },
        'targets': {
            'starlink_pool_size': 96,
            'oneweb_pool_size': 38
        }
    }
    
    # 初始化最佳化器
    optimizer = SimulatedAnnealingOptimizer(config)
    
    # 模擬候選衛星數據 (實際應來自F2)
    starlink_candidates = []  # 來自F2的Starlink候選
    oneweb_candidates = []    # 來自F2的OneWeb候選
    orbital_positions = {}    # 來自F1的軌道位置數據
    
    # 執行最佳化
    optimal_solution = await optimizer.optimize_satellite_pools(
        starlink_candidates, oneweb_candidates, orbital_positions
    )
    
    # 匯出結果
    await optimizer.export_optimization_results(
        optimal_solution, '/tmp/a1_optimization_results.json'
    )
    
    print(f"✅ A1_SimulatedAnnealing最佳化完成")
    print(f"   最佳衛星池: Starlink {len(optimal_solution.starlink_satellites)}顆, OneWeb {len(optimal_solution.oneweb_satellites)}顆")
    print(f"   可見性合規: {optimal_solution.visibility_compliance:.1%}")

if __name__ == "__main__":
    asyncio.run(main())