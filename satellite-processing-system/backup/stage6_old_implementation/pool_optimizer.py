"""
PoolOptimizer - 資源池優化器

專注於資源池管理相關的優化功能：
- 池配置優化
- 數量精確控制
- 資源分配策略
- 配置驗證

從原始 PoolOptimizationEngine 重構，專注於池資源管理
"""

import json
import logging
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PoolOptimizer:
    """資源池優化器 - 專注於池配置和資源管理"""

    def __init__(self, optimizer_config: Dict[str, Any] = None):
        """初始化池優化器"""
        self.config = optimizer_config or self._get_default_config()
        self.logger = logger

        # 池優化統計
        self.optimization_stats = {
            "pool_optimizations_performed": 0,
            "successful_configurations": 0,
            "quantity_adjustments_made": 0,
            "configuration_improvements": 0,
            "average_pool_efficiency": 0.0
        }

        # 池配置約束
        self.pool_constraints = self._initialize_pool_constraints()

        self.logger.info("🏊 資源池優化器初始化完成")

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設池優化配置"""
        return {
            "pool_configuration": {
                "min_pool_size": 8,
                "max_pool_size": 32,
                "target_pool_size": 16,
                "redundancy_factor": 1.2,
                "balance_threshold": 0.1
            },
            "quantity_management": {
                "constellation_balance_weight": 0.4,
                "coverage_requirement_weight": 0.3,
                "redundancy_weight": 0.2,
                "efficiency_weight": 0.1
            },
            "optimization_criteria": {
                "coverage_continuity_threshold": 0.95,
                "handover_optimality_threshold": 0.8,
                "resource_utilization_threshold": 0.85
            }
        }

    def _initialize_pool_constraints(self) -> Dict[str, Any]:
        """初始化池配置約束"""
        return {
            "constellation_constraints": {
                "starlink": {"min_satellites": 4, "max_satellites": 20, "optimal_ratio": 0.6},
                "oneweb": {"min_satellites": 2, "max_satellites": 12, "optimal_ratio": 0.4}
            },
            "coverage_constraints": {
                "min_elevation_coverage": 10.0,  # degrees
                "required_overlap_time": 30,    # seconds
                "max_coverage_gap": 60          # seconds
            },
            "resource_constraints": {
                "max_computational_load": 1.0,
                "max_bandwidth_usage": 0.9,
                "max_power_consumption": 0.85
            }
        }

    def optimize_pool_configuration(self,
                                  satellite_candidates: List[Dict],
                                  pool_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """執行池配置優化主流程"""

        start_time = datetime.now()
        self.logger.info(f"🏊 開始池配置優化，候選衛星: {len(satellite_candidates)}顆")

        try:
            # 1. 分析當前候選衛星分佈
            distribution_analysis = self._analyze_satellite_distribution(satellite_candidates)

            # 2. 定義優化目標
            optimization_objectives = self._define_pool_optimization_objectives(pool_requirements)

            # 3. 執行配置選擇演算法
            configuration_result = self._execute_pool_configuration_algorithm(
                satellite_candidates, optimization_objectives
            )

            # 4. 精確數量管理
            quantity_result = self._optimize_satellite_quantities(
                configuration_result.get('selected_configuration', []),
                pool_requirements
            )

            # 5. 驗證池配置
            validation_result = self._validate_pool_configuration(quantity_result)

            # 6. 產生池優化報告
            optimization_report = {
                'optimization_type': 'pool_configuration',
                'input_satellites': len(satellite_candidates),
                'optimized_pool': quantity_result.get('optimized_pool', []),
                'distribution_analysis': distribution_analysis,
                'optimization_objectives': optimization_objectives,
                'configuration_metrics': configuration_result.get('configuration_metrics', {}),
                'quantity_metrics': quantity_result.get('quantity_metrics', {}),
                'validation_result': validation_result,
                'optimization_duration': (datetime.now() - start_time).total_seconds(),
                'optimization_timestamp': datetime.now().isoformat()
            }

            # 更新統計
            self.optimization_stats['pool_optimizations_performed'] += 1

            if validation_result.get('configuration_valid', False):
                self.optimization_stats['successful_configurations'] += 1

            if quantity_result.get('quantity_adjustments', 0) > 0:
                self.optimization_stats['quantity_adjustments_made'] += quantity_result['quantity_adjustments']

            pool_efficiency = configuration_result.get('pool_efficiency', 0.0)
            if pool_efficiency > 0:
                self.optimization_stats['configuration_improvements'] += 1
                # 更新平均效率
                total_optimizations = self.optimization_stats['pool_optimizations_performed']
                current_avg = self.optimization_stats['average_pool_efficiency']
                self.optimization_stats['average_pool_efficiency'] = (
                    (current_avg * (total_optimizations - 1) + pool_efficiency) / total_optimizations
                )

            self.logger.info(f"✅ 池配置優化完成，最終池大小: {len(quantity_result.get('optimized_pool', []))}顆")
            return optimization_report

        except Exception as e:
            self.logger.error(f"❌ 池配置優化失敗: {e}")
            return {'error': str(e), 'optimization_type': 'pool_configuration'}

    def evaluate_pool_efficiency(self, satellite_pool: List[Dict]) -> Dict[str, float]:
        """評估池效率"""
        try:
            if not satellite_pool:
                return {'overall_efficiency': 0.0}

            # 計算各項效率指標
            coverage_efficiency = self._calculate_coverage_efficiency(satellite_pool)
            resource_efficiency = self._calculate_resource_efficiency(satellite_pool)
            balance_efficiency = self._calculate_constellation_balance_efficiency(satellite_pool)
            redundancy_efficiency = self._calculate_redundancy_efficiency(satellite_pool)

            # 加權計算整體效率
            weights = self.config['quantity_management']
            overall_efficiency = (
                weights.get('coverage_requirement_weight', 0.3) * coverage_efficiency +
                weights.get('efficiency_weight', 0.1) * resource_efficiency +
                weights.get('constellation_balance_weight', 0.4) * balance_efficiency +
                weights.get('redundancy_weight', 0.2) * redundancy_efficiency
            )

            return {
                'overall_efficiency': overall_efficiency,
                'coverage_efficiency': coverage_efficiency,
                'resource_efficiency': resource_efficiency,
                'balance_efficiency': balance_efficiency,
                'redundancy_efficiency': redundancy_efficiency
            }

        except Exception as e:
            self.logger.error(f"❌ 池效率評估失敗: {e}")
            return {'overall_efficiency': 0.0, 'error': str(e)}

    def optimize_constellation_balance(self,
                                     satellite_pool: List[Dict],
                                     target_ratios: Dict[str, float] = None) -> Dict[str, Any]:
        """優化星座平衡"""
        try:
            if not satellite_pool:
                return {'balanced_pool': [], 'balance_improvement': 0.0}

            # 使用預設或指定的目標比例
            if target_ratios is None:
                target_ratios = {
                    'starlink': 0.6,
                    'oneweb': 0.4
                }

            self.logger.info(f"🎯 優化星座平衡，目標比例: {target_ratios}")

            # 分析當前星座分佈
            current_distribution = self._analyze_constellation_distribution(satellite_pool)

            # 計算當前平衡度
            current_balance = self._calculate_balance_score(current_distribution, target_ratios)

            # 執行平衡優化
            balanced_pool = self._execute_balance_optimization(satellite_pool, target_ratios)

            # 計算優化後平衡度
            optimized_distribution = self._analyze_constellation_distribution(balanced_pool)
            optimized_balance = self._calculate_balance_score(optimized_distribution, target_ratios)

            balance_improvement = optimized_balance - current_balance

            return {
                'balanced_pool': balanced_pool,
                'current_distribution': current_distribution,
                'optimized_distribution': optimized_distribution,
                'current_balance_score': current_balance,
                'optimized_balance_score': optimized_balance,
                'balance_improvement': balance_improvement,
                'target_ratios': target_ratios
            }

        except Exception as e:
            self.logger.error(f"❌ 星座平衡優化失敗: {e}")
            return {'balanced_pool': satellite_pool, 'balance_improvement': 0.0, 'error': str(e)}

    def manage_precise_quantities(self,
                                satellite_pool: List[Dict],
                                quantity_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """管理精確數量"""
        try:
            target_count = quantity_requirements.get('target_satellite_count', 16)
            min_count = quantity_requirements.get('min_satellite_count', 8)
            max_count = quantity_requirements.get('max_satellite_count', 32)

            self.logger.info(f"📊 管理精確數量，目標: {target_count}顆 (範圍: {min_count}-{max_count})")

            current_count = len(satellite_pool)

            # 檢查當前數量是否符合要求
            quantity_status = self._assess_quantity_status(current_count, min_count, max_count, target_count)

            # 執行數量調整
            if quantity_status['adjustment_needed']:
                adjusted_pool = self._execute_quantity_adjustment(
                    satellite_pool, quantity_status, quantity_requirements
                )
            else:
                adjusted_pool = satellite_pool

            # 驗證調整結果
            final_count = len(adjusted_pool)
            adjustment_success = min_count <= final_count <= max_count

            quantity_management_result = {
                'managed_pool': adjusted_pool,
                'original_count': current_count,
                'target_count': target_count,
                'final_count': final_count,
                'quantity_status': quantity_status,
                'adjustment_success': adjustment_success,
                'adjustments_made': abs(final_count - current_count),
                'management_timestamp': datetime.now().isoformat()
            }

            return quantity_management_result

        except Exception as e:
            self.logger.error(f"❌ 精確數量管理失敗: {e}")
            return {'managed_pool': satellite_pool, 'adjustment_success': False, 'error': str(e)}

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """獲取池優化統計資訊"""
        return self.optimization_stats.copy()

    # =============== 私有輔助方法 ===============

    def _analyze_satellite_distribution(self, satellites: List[Dict]) -> Dict[str, Any]:
        """分析衛星分佈"""
        try:
            distribution = {
                'total_satellites': len(satellites),
                'constellation_breakdown': {},
                'orbital_distribution': {},
                'quality_distribution': {}
            }

            # 星座分佈統計
            for satellite in satellites:
                constellation = satellite.get('constellation', 'unknown')
                distribution['constellation_breakdown'][constellation] = (
                    distribution['constellation_breakdown'].get(constellation, 0) + 1
                )

            # 軌道參數分佈（簡化）
            if satellites:
                altitudes = []
                inclinations = []

                for satellite in satellites:
                    # 提取軌道參數（簡化實現）
                    orbital_elements = satellite.get('orbital_elements', {})
                    altitude = orbital_elements.get('altitude', 550)  # 預設550km
                    inclination = orbital_elements.get('inclination', 53)  # 預設53度

                    altitudes.append(altitude)
                    inclinations.append(inclination)

                distribution['orbital_distribution'] = {
                    'altitude_stats': {
                        'mean': np.mean(altitudes),
                        'std': np.std(altitudes),
                        'range': [min(altitudes), max(altitudes)]
                    },
                    'inclination_stats': {
                        'mean': np.mean(inclinations),
                        'std': np.std(inclinations),
                        'range': [min(inclinations), max(inclinations)]
                    }
                }

            return distribution

        except Exception as e:
            self.logger.error(f"❌ 衛星分佈分析失敗: {e}")
            return {'total_satellites': len(satellites), 'error': str(e)}

    def _define_pool_optimization_objectives(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """定義池優化目標"""
        try:
            objectives = {
                'coverage_objectives': {
                    'target_coverage_rate': requirements.get('target_coverage_rate', 0.95),
                    'max_coverage_gap_seconds': requirements.get('max_coverage_gap', 60),
                    'min_elevation_degrees': requirements.get('min_elevation', 10.0)
                },
                'resource_objectives': {
                    'target_pool_size': requirements.get('target_satellite_count', 16),
                    'max_computational_load': 1.0,
                    'target_efficiency': 0.85
                },
                'balance_objectives': {
                    'constellation_balance_target': requirements.get('constellation_balance', {
                        'starlink': 0.6,
                        'oneweb': 0.4
                    }),
                    'redundancy_level': requirements.get('redundancy_level', 'medium')
                },
                'quality_objectives': {
                    'min_satellite_quality': requirements.get('min_quality_threshold', 0.7),
                    'diversity_requirement': requirements.get('diversity_requirement', 0.6)
                }
            }

            return objectives

        except Exception as e:
            self.logger.error(f"❌ 池優化目標定義失敗: {e}")
            return {}

    def _execute_pool_configuration_algorithm(self,
                                            candidates: List[Dict],
                                            objectives: Dict[str, Any]) -> Dict[str, Any]:
        """執行池配置演算法"""
        try:
            target_size = objectives.get('resource_objectives', {}).get('target_pool_size', 16)

            # 1. 篩選符合品質要求的候選衛星
            quality_threshold = objectives.get('quality_objectives', {}).get('min_satellite_quality', 0.7)
            qualified_candidates = self._filter_by_quality(candidates, quality_threshold)

            # 2. 執行多目標優化選擇
            optimal_selection = self._multi_objective_pool_selection(qualified_candidates, objectives, target_size)

            # 3. 計算配置指標
            configuration_metrics = self._calculate_configuration_metrics(optimal_selection, objectives)

            return {
                'selected_configuration': optimal_selection,
                'configuration_metrics': configuration_metrics,
                'qualified_candidates_count': len(qualified_candidates),
                'pool_efficiency': configuration_metrics.get('overall_efficiency', 0.0)
            }

        except Exception as e:
            self.logger.error(f"❌ 池配置演算法執行失敗: {e}")
            return {'selected_configuration': [], 'error': str(e)}

    def _optimize_satellite_quantities(self,
                                     selected_pool: List[Dict],
                                     requirements: Dict[str, Any]) -> Dict[str, Any]:
        """優化衛星數量"""
        try:
            if not selected_pool:
                return {'optimized_pool': [], 'quantity_adjustments': 0}

            # 數量管理
            quantity_management = self.manage_precise_quantities(selected_pool, requirements)

            # 星座平衡優化
            balance_optimization = self.optimize_constellation_balance(
                quantity_management.get('managed_pool', [])
            )

            # 最終優化結果
            optimized_pool = balance_optimization.get('balanced_pool', [])

            quantity_metrics = {
                'original_count': len(selected_pool),
                'managed_count': len(quantity_management.get('managed_pool', [])),
                'final_count': len(optimized_pool),
                'quantity_adjustments': quantity_management.get('adjustments_made', 0),
                'balance_improvement': balance_optimization.get('balance_improvement', 0.0),
                'constellation_distribution': balance_optimization.get('optimized_distribution', {})
            }

            return {
                'optimized_pool': optimized_pool,
                'quantity_metrics': quantity_metrics,
                'quantity_adjustments': quantity_metrics['quantity_adjustments']
            }

        except Exception as e:
            self.logger.error(f"❌ 衛星數量優化失敗: {e}")
            return {'optimized_pool': selected_pool, 'quantity_adjustments': 0, 'error': str(e)}

    def _calculate_coverage_efficiency(self, satellite_pool: List[Dict]) -> float:
        """計算覆蓋效率"""
        try:
            if not satellite_pool:
                return 0.0

            # 簡化實現：基於衛星數量和分佈
            pool_size = len(satellite_pool)
            size_efficiency = min(pool_size / 16, 1.0)  # 16為目標數量

            # 計算星座分佈效率
            distribution = self._analyze_constellation_distribution(satellite_pool)
            distribution_efficiency = self._calculate_distribution_efficiency(distribution)

            coverage_efficiency = (size_efficiency + distribution_efficiency) / 2
            return max(0.0, min(1.0, coverage_efficiency))

        except Exception as e:
            self.logger.error(f"❌ 覆蓋效率計算失敗: {e}")
            return 0.0

    def _calculate_resource_efficiency(self, satellite_pool: List[Dict]) -> float:
        """計算資源效率"""
        try:
            if not satellite_pool:
                return 0.0

            # 簡化實現：基於池大小和資源約束
            pool_size = len(satellite_pool)
            max_size = self.config['pool_configuration']['max_pool_size']
            min_size = self.config['pool_configuration']['min_pool_size']

            if pool_size <= max_size and pool_size >= min_size:
                # 在合理範圍內，計算相對於目標大小的效率
                target_size = self.config['pool_configuration']['target_pool_size']
                size_deviation = abs(pool_size - target_size) / target_size
                resource_efficiency = max(0.0, 1.0 - size_deviation)
            else:
                # 超出範圍，效率較低
                resource_efficiency = 0.5

            return resource_efficiency

        except Exception as e:
            self.logger.error(f"❌ 資源效率計算失敗: {e}")
            return 0.0

    def _calculate_constellation_balance_efficiency(self, satellite_pool: List[Dict]) -> float:
        """計算星座平衡效率"""
        try:
            distribution = self._analyze_constellation_distribution(satellite_pool)
            target_ratios = {'starlink': 0.6, 'oneweb': 0.4}

            balance_score = self._calculate_balance_score(distribution, target_ratios)
            return balance_score

        except Exception as e:
            self.logger.error(f"❌ 星座平衡效率計算失敗: {e}")
            return 0.0

    def _calculate_redundancy_efficiency(self, satellite_pool: List[Dict]) -> float:
        """計算冗餘效率"""
        try:
            if not satellite_pool:
                return 0.0

            # 簡化實現：基於池大小和目標冗餘因子
            pool_size = len(satellite_pool)
            target_size = self.config['pool_configuration']['target_pool_size']
            redundancy_factor = self.config['pool_configuration']['redundancy_factor']

            ideal_redundant_size = target_size * redundancy_factor
            redundancy_efficiency = min(pool_size / ideal_redundant_size, 1.0)

            return redundancy_efficiency

        except Exception as e:
            self.logger.error(f"❌ 冗餘效率計算失敗: {e}")
            return 0.0

    def _analyze_constellation_distribution(self, satellites: List[Dict]) -> Dict[str, float]:
        """分析星座分佈"""
        distribution = {}
        total_satellites = len(satellites)

        if total_satellites == 0:
            return distribution

        for satellite in satellites:
            constellation = satellite.get('constellation', 'unknown')
            distribution[constellation] = distribution.get(constellation, 0) + 1

        # 轉換為比例
        for constellation in distribution:
            distribution[constellation] = distribution[constellation] / total_satellites

        return distribution

    def _calculate_balance_score(self, current_distribution: Dict[str, float], target_ratios: Dict[str, float]) -> float:
        """計算平衡評分"""
        try:
            if not current_distribution or not target_ratios:
                return 0.0

            balance_scores = []

            for constellation, target_ratio in target_ratios.items():
                current_ratio = current_distribution.get(constellation, 0.0)
                deviation = abs(current_ratio - target_ratio)
                constellation_balance = max(0.0, 1.0 - deviation)
                balance_scores.append(constellation_balance)

            overall_balance = sum(balance_scores) / len(balance_scores) if balance_scores else 0.0
            return overall_balance

        except Exception as e:
            self.logger.error(f"❌ 平衡評分計算失敗: {e}")
            return 0.0

    def _execute_balance_optimization(self, satellite_pool: List[Dict], target_ratios: Dict[str, float]) -> List[Dict]:
        """執行平衡優化"""
        try:
            if not satellite_pool:
                return []

            total_satellites = len(satellite_pool)

            # 按星座分組
            constellation_groups = {}
            for satellite in satellite_pool:
                constellation = satellite.get('constellation', 'unknown')
                if constellation not in constellation_groups:
                    constellation_groups[constellation] = []
                constellation_groups[constellation].append(satellite)

            # 計算目標數量
            target_counts = {}
            for constellation, ratio in target_ratios.items():
                target_counts[constellation] = int(total_satellites * ratio)

            # 平衡選擇
            balanced_pool = []
            for constellation, target_count in target_counts.items():
                available_satellites = constellation_groups.get(constellation, [])
                selected_count = min(target_count, len(available_satellites))
                balanced_pool.extend(available_satellites[:selected_count])

            return balanced_pool

        except Exception as e:
            self.logger.error(f"❌ 平衡優化執行失敗: {e}")
            return satellite_pool

    def _assess_quantity_status(self, current_count: int, min_count: int, max_count: int, target_count: int) -> Dict[str, Any]:
        """評估數量狀態"""
        status = {
            'current_count': current_count,
            'target_count': target_count,
            'min_count': min_count,
            'max_count': max_count,
            'within_range': min_count <= current_count <= max_count,
            'at_target': current_count == target_count,
            'adjustment_needed': False,
            'adjustment_type': None
        }

        if current_count < min_count:
            status['adjustment_needed'] = True
            status['adjustment_type'] = 'increase'
        elif current_count > max_count:
            status['adjustment_needed'] = True
            status['adjustment_type'] = 'decrease'
        elif abs(current_count - target_count) > 2:  # 容忍範圍
            status['adjustment_needed'] = True
            status['adjustment_type'] = 'fine_tune'

        return status

    def _execute_quantity_adjustment(self,
                                   satellite_pool: List[Dict],
                                   quantity_status: Dict[str, Any],
                                   requirements: Dict[str, Any]) -> List[Dict]:
        """執行數量調整"""
        try:
            adjustment_type = quantity_status.get('adjustment_type')
            target_count = quantity_status.get('target_count')

            if adjustment_type == 'increase':
                # 需要增加衛星（簡化實現：複製現有衛星）
                current_count = len(satellite_pool)
                needed_count = target_count - current_count
                adjusted_pool = satellite_pool.copy()

                # 簡化增加策略：重複選擇品質最高的衛星
                if satellite_pool:
                    for _ in range(needed_count):
                        # 選擇一個現有衛星進行複製（實際應該從候選池中選擇）
                        selected_satellite = satellite_pool[0]  # 簡化選擇
                        adjusted_pool.append(selected_satellite)

            elif adjustment_type == 'decrease':
                # 需要減少衛星
                adjusted_pool = satellite_pool[:target_count]

            elif adjustment_type == 'fine_tune':
                # 微調數量
                if len(satellite_pool) > target_count:
                    adjusted_pool = satellite_pool[:target_count]
                else:
                    adjusted_pool = satellite_pool.copy()
                    # 微增策略（簡化）
                    while len(adjusted_pool) < target_count and satellite_pool:
                        adjusted_pool.append(satellite_pool[0])

            else:
                adjusted_pool = satellite_pool

            return adjusted_pool

        except Exception as e:
            self.logger.error(f"❌ 數量調整執行失敗: {e}")
            return satellite_pool

    def _filter_by_quality(self, candidates: List[Dict], quality_threshold: float) -> List[Dict]:
        """按品質篩選候選衛星"""
        try:
            qualified = []
            for candidate in candidates:
                # 簡化品質評估
                quality_score = candidate.get('quality_score', 0.7)
                if quality_score >= quality_threshold:
                    qualified.append(candidate)

            return qualified

        except Exception as e:
            self.logger.error(f"❌ 品質篩選失敗: {e}")
            return candidates

    def _multi_objective_pool_selection(self,
                                      candidates: List[Dict],
                                      objectives: Dict[str, Any],
                                      target_size: int) -> List[Dict]:
        """多目標池選擇"""
        try:
            if not candidates:
                return []

            # 簡化實現：基於綜合評分選擇
            candidate_scores = []
            for candidate in candidates:
                score = self._calculate_multi_objective_score(candidate, objectives)
                candidate_scores.append((candidate, score))

            # 按評分排序並選擇前N個
            candidate_scores.sort(key=lambda x: x[1], reverse=True)
            selected_count = min(target_size, len(candidate_scores))
            selected = [item[0] for item in candidate_scores[:selected_count]]

            return selected

        except Exception as e:
            self.logger.error(f"❌ 多目標池選擇失敗: {e}")
            return candidates[:target_size] if candidates else []

    def _calculate_multi_objective_score(self, candidate: Dict, objectives: Dict[str, Any]) -> float:
        """計算多目標評分"""
        try:
            # 簡化實現：基於候選衛星的各項指標
            quality_score = candidate.get('quality_score', 0.7)
            constellation = candidate.get('constellation', 'unknown')

            # 星座偏好評分
            constellation_preferences = objectives.get('balance_objectives', {}).get('constellation_balance_target', {})
            constellation_score = constellation_preferences.get(constellation, 0.5)

            # 綜合評分
            multi_objective_score = (0.6 * quality_score + 0.4 * constellation_score)

            return max(0.0, min(1.0, multi_objective_score))

        except Exception as e:
            self.logger.error(f"❌ 多目標評分計算失敗: {e}")
            return 0.5

    def _calculate_configuration_metrics(self, pool_configuration: List[Dict], objectives: Dict[str, Any]) -> Dict[str, Any]:
        """計算配置指標"""
        try:
            metrics = {
                'pool_size': len(pool_configuration),
                'overall_efficiency': 0.0,
                'configuration_quality': 0.0
            }

            if pool_configuration:
                # 計算池效率
                efficiency_result = self.evaluate_pool_efficiency(pool_configuration)
                metrics['overall_efficiency'] = efficiency_result.get('overall_efficiency', 0.0)

                # 計算配置品質
                quality_scores = [sat.get('quality_score', 0.7) for sat in pool_configuration]
                metrics['configuration_quality'] = sum(quality_scores) / len(quality_scores)

                # 星座分佈指標
                distribution = self._analyze_constellation_distribution(pool_configuration)
                metrics['constellation_distribution'] = distribution

            return metrics

        except Exception as e:
            self.logger.error(f"❌ 配置指標計算失敗: {e}")
            return {'pool_size': len(pool_configuration), 'overall_efficiency': 0.0}

    def _calculate_distribution_efficiency(self, distribution: Dict[str, Any]) -> float:
        """計算分佈效率"""
        # 簡化實現
        return 0.8

    def _validate_pool_configuration(self, pool_result: Dict[str, Any]) -> Dict[str, Any]:
        """驗證池配置"""
        try:
            optimized_pool = pool_result.get('optimized_pool', [])

            validation = {
                'configuration_valid': True,
                'validation_checks': {},
                'validation_timestamp': datetime.now().isoformat()
            }

            # 檢查池大小
            pool_size = len(optimized_pool)
            min_size = self.config['pool_configuration']['min_pool_size']
            max_size = self.config['pool_configuration']['max_pool_size']
            size_valid = min_size <= pool_size <= max_size
            validation['validation_checks']['pool_size'] = size_valid

            # 檢查星座平衡
            if optimized_pool:
                distribution = self._analyze_constellation_distribution(optimized_pool)
                balance_score = self._calculate_balance_score(distribution, {'starlink': 0.6, 'oneweb': 0.4})
                balance_valid = balance_score >= 0.5
                validation['validation_checks']['constellation_balance'] = balance_valid
            else:
                validation['validation_checks']['constellation_balance'] = False

            # 檢查效率
            if optimized_pool:
                efficiency_result = self.evaluate_pool_efficiency(optimized_pool)
                efficiency_valid = efficiency_result.get('overall_efficiency', 0.0) >= 0.6
                validation['validation_checks']['pool_efficiency'] = efficiency_valid
            else:
                validation['validation_checks']['pool_efficiency'] = False

            # 綜合驗證結果
            validation['configuration_valid'] = all(validation['validation_checks'].values())

            return validation

        except Exception as e:
            self.logger.error(f"❌ 池配置驗證失敗: {e}")
            return {'configuration_valid': False, 'error': str(e)}