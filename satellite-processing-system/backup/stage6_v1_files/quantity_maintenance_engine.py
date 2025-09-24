#!/usr/bin/env python3
"""
數量維護引擎 - 從dynamic_pool_optimizer_engine.py拆分

專責功能：
1. 精確衛星數量控制
2. 星座分布平衡
3. 數量約束檢查
4. 動態調整策略

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 模組化重構專用
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class QuantityMaintenanceEngine:
    """
    數量維護引擎

    專責維護衛星池的精確數量和分布平衡
    確保滿足覆蓋需求同時優化資源使用
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化數量維護引擎"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 預設數量約束
        self.precise_satellite_constraints = {
            'total_satellites': self.config.get('total_satellites', 20),
            'min_starlink': self.config.get('min_starlink', 8),
            'max_starlink': self.config.get('max_starlink', 12),
            'min_oneweb': self.config.get('min_oneweb', 8),
            'max_oneweb': self.config.get('max_oneweb', 12),
            'coverage_threshold': self.config.get('coverage_threshold', 0.85),
            'gap_tolerance': self.config.get('gap_tolerance', 300)  # 秒
        }

        self.maintenance_stats = {
            'rebalancing_operations': 0,
            'quantity_adjustments': 0,
            'constraint_violations': 0,
            'optimization_cycles': 0
        }

        self.logger.info("✅ 數量維護引擎初始化完成")

    def maintain_precise_satellite_quantities(self, candidate_pools: List[Dict[str, Any]],
                                             coverage_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        維護精確的衛星數量

        Args:
            candidate_pools: 候選衛星池列表
            coverage_requirements: 覆蓋需求

        Returns:
            優化後的衛星池列表
        """
        try:
            self.logger.info("🎯 開始精確數量維護")

            optimized_pools = []

            for pool in candidate_pools:
                # 分析當前分布
                distribution = self._analyze_current_satellite_distribution(pool)

                # 檢查約束
                constraint_check = self._check_quantity_constraints(distribution)

                if constraint_check['needs_adjustment']:
                    # 執行數量調整
                    adjusted_pool = self._execute_constellation_rebalancing(pool, constraint_check)
                    optimized_pools.append(adjusted_pool)
                    self.maintenance_stats['quantity_adjustments'] += 1
                else:
                    optimized_pools.append(pool)

            # 驗證覆蓋性能
            for pool in optimized_pools:
                self._validate_coverage_performance(pool, coverage_requirements)

            self.maintenance_stats['optimization_cycles'] += 1
            self.logger.info(f"✅ 數量維護完成，處理 {len(optimized_pools)} 個池")

            return optimized_pools

        except Exception as e:
            self.logger.error(f"❌ 數量維護失敗: {e}")
            return candidate_pools

    def _analyze_current_satellite_distribution(self, pool: Dict[str, Any]) -> Dict[str, Any]:
        """分析當前衛星分布"""
        candidates = pool.get('candidates', [])

        distribution = {
            'total_count': len(candidates),
            'starlink_count': 0,
            'oneweb_count': 0,
            'constellation_ratio': {},
            'avg_coverage_score': 0.0,
            'avg_signal_quality': 0.0
        }

        starlink_candidates = [c for c in candidates if c.get('constellation') == 'starlink']
        oneweb_candidates = [c for c in candidates if c.get('constellation') == 'oneweb']

        distribution['starlink_count'] = len(starlink_candidates)
        distribution['oneweb_count'] = len(oneweb_candidates)

        if distribution['total_count'] > 0:
            distribution['constellation_ratio'] = {
                'starlink': distribution['starlink_count'] / distribution['total_count'],
                'oneweb': distribution['oneweb_count'] / distribution['total_count']
            }

            # 計算平均分數
            total_coverage = sum(c.get('coverage_score', 0) for c in candidates)
            total_signal = sum(c.get('signal_quality_score', 0) for c in candidates)

            distribution['avg_coverage_score'] = total_coverage / distribution['total_count']
            distribution['avg_signal_quality'] = total_signal / distribution['total_count']

        return distribution

    def _check_quantity_constraints(self, distribution: Dict[str, Any]) -> Dict[str, Any]:
        """檢查數量約束"""
        constraints = self.precise_satellite_constraints

        check_result = {
            'needs_adjustment': False,
            'total_violation': False,
            'starlink_violation': False,
            'oneweb_violation': False,
            'adjustments_needed': {}
        }

        total_count = distribution['total_count']
        starlink_count = distribution['starlink_count']
        oneweb_count = distribution['oneweb_count']

        # 檢查總數約束
        target_total = constraints['total_satellites']
        if total_count != target_total:
            check_result['total_violation'] = True
            check_result['needs_adjustment'] = True
            check_result['adjustments_needed']['total_adjustment'] = target_total - total_count

        # 檢查Starlink約束
        min_starlink = constraints['min_starlink']
        max_starlink = constraints['max_starlink']
        if starlink_count < min_starlink or starlink_count > max_starlink:
            check_result['starlink_violation'] = True
            check_result['needs_adjustment'] = True
            if starlink_count < min_starlink:
                check_result['adjustments_needed']['starlink_shortage'] = min_starlink - starlink_count
            else:
                check_result['adjustments_needed']['starlink_excess'] = starlink_count - max_starlink

        # 檢查OneWeb約束
        min_oneweb = constraints['min_oneweb']
        max_oneweb = constraints['max_oneweb']
        if oneweb_count < min_oneweb or oneweb_count > max_oneweb:
            check_result['oneweb_violation'] = True
            check_result['needs_adjustment'] = True
            if oneweb_count < min_oneweb:
                check_result['adjustments_needed']['oneweb_shortage'] = min_oneweb - oneweb_count
            else:
                check_result['adjustments_needed']['oneweb_excess'] = oneweb_count - max_oneweb

        if check_result['needs_adjustment']:
            self.maintenance_stats['constraint_violations'] += 1

        return check_result

    def _execute_constellation_rebalancing(self, pool: Dict[str, Any],
                                         constraint_check: Dict[str, Any]) -> Dict[str, Any]:
        """執行星座重平衡"""
        try:
            self.logger.info("⚖️ 執行星座重平衡")

            candidates = pool.get('candidates', [])
            adjustments = constraint_check.get('adjustments_needed', {})

            # 分離星座候選
            starlink_candidates = [c for c in candidates if c.get('constellation') == 'starlink']
            oneweb_candidates = [c for c in candidates if c.get('constellation') == 'oneweb']

            # 按評分排序
            starlink_candidates.sort(key=lambda x: x.get('rl_score', 0), reverse=True)
            oneweb_candidates.sort(key=lambda x: x.get('rl_score', 0), reverse=True)

            # 執行調整
            target_starlink = self._calculate_optimal_starlink_count(adjustments)
            target_oneweb = self._calculate_optimal_oneweb_count(adjustments)

            # 選擇最佳候選
            selected_starlink = self._select_optimal_starlink_satellites(starlink_candidates, target_starlink)
            selected_oneweb = self._select_optimal_oneweb_satellites(oneweb_candidates, target_oneweb)

            # 創建新池
            rebalanced_pool = pool.copy()
            rebalanced_pool['candidates'] = selected_starlink + selected_oneweb
            rebalanced_pool['rebalancing_applied'] = True
            rebalanced_pool['original_count'] = len(candidates)
            rebalanced_pool['adjusted_count'] = len(rebalanced_pool['candidates'])

            self.maintenance_stats['rebalancing_operations'] += 1

            self.logger.info(f"✅ 重平衡完成: {len(candidates)} → {len(rebalanced_pool['candidates'])} 顆衛星")
            return rebalanced_pool

        except Exception as e:
            self.logger.error(f"❌ 星座重平衡失敗: {e}")
            return pool

    def _calculate_optimal_starlink_count(self, adjustments: Dict[str, Any]) -> int:
        """計算最佳Starlink數量"""
        constraints = self.precise_satellite_constraints

        if 'starlink_shortage' in adjustments:
            return constraints['min_starlink']
        elif 'starlink_excess' in adjustments:
            return constraints['max_starlink']
        else:
            # 預設為約束範圍的中值
            return (constraints['min_starlink'] + constraints['max_starlink']) // 2

    def _calculate_optimal_oneweb_count(self, adjustments: Dict[str, Any]) -> int:
        """計算最佳OneWeb數量"""
        constraints = self.precise_satellite_constraints

        if 'oneweb_shortage' in adjustments:
            return constraints['min_oneweb']
        elif 'oneweb_excess' in adjustments:
            return constraints['max_oneweb']
        else:
            # 預設為約束範圍的中值
            return (constraints['min_oneweb'] + constraints['max_oneweb']) // 2

    def _select_optimal_starlink_satellites(self, candidates: List[Dict[str, Any]],
                                          target_count: int) -> List[Dict[str, Any]]:
        """選擇最佳Starlink衛星"""
        if not candidates:
            return []

        # 按綜合評分排序並選擇前target_count個
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_satellite_selection_score(candidate)
            scored_candidates.append((candidate, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        selected = [candidate for candidate, score in scored_candidates[:target_count]]

        return selected

    def _select_optimal_oneweb_satellites(self, candidates: List[Dict[str, Any]],
                                        target_count: int) -> List[Dict[str, Any]]:
        """選擇最佳OneWeb衛星"""
        if not candidates:
            return []

        # 同樣的選擇邏輯
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_satellite_selection_score(candidate)
            scored_candidates.append((candidate, score))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        selected = [candidate for candidate, score in scored_candidates[:target_count]]

        return selected

    def _calculate_satellite_selection_score(self, candidate: Dict[str, Any]) -> float:
        """計算衛星選擇評分"""
        # 綜合多項指標
        coverage_score = candidate.get('coverage_score', 0.0)
        signal_quality_score = candidate.get('signal_quality_score', 0.0)
        stability_score = candidate.get('stability_score', 0.0)
        rl_score = candidate.get('rl_score', 0.0)

        # 加權平均
        weights = {
            'coverage': 0.3,
            'signal_quality': 0.25,
            'stability': 0.25,
            'rl': 0.2
        }

        total_score = (
            coverage_score * weights['coverage'] +
            signal_quality_score * weights['signal_quality'] +
            stability_score * weights['stability'] +
            rl_score * weights['rl']
        )

        return total_score

    def _validate_coverage_performance(self, pool: Dict[str, Any],
                                     coverage_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """驗證覆蓋性能"""
        candidates = pool.get('candidates', [])

        if not candidates:
            return {'validation_passed': False, 'reason': 'no_candidates'}

        # 計算覆蓋指標
        total_coverage_score = sum(c.get('coverage_score', 0) for c in candidates)
        avg_coverage_score = total_coverage_score / len(candidates)

        # 檢查是否滿足需求
        required_coverage = coverage_requirements.get('min_coverage_score', 0.8)
        validation_passed = avg_coverage_score >= required_coverage

        validation_result = {
            'validation_passed': validation_passed,
            'avg_coverage_score': avg_coverage_score,
            'required_coverage': required_coverage,
            'total_candidates': len(candidates),
            'coverage_deficit': max(0, required_coverage - avg_coverage_score)
        }

        if not validation_passed:
            self.logger.warning(f"⚠️ 覆蓋性能驗證失敗: {avg_coverage_score:.3f} < {required_coverage:.3f}")

        return validation_result

    def update_constraints(self, new_constraints: Dict[str, Any]) -> None:
        """更新數量約束"""
        self.precise_satellite_constraints.update(new_constraints)
        self.logger.info("✅ 數量約束已更新")

    def get_maintenance_statistics(self) -> Dict[str, Any]:
        """獲取維護統計"""
        return self.maintenance_stats.copy()

    def generate_quantity_maintenance_report(self, pools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成數量維護報告"""
        report = {
            'timestamp': '2025-09-18',
            'total_pools_processed': len(pools),
            'maintenance_statistics': self.get_maintenance_statistics(),
            'constraint_compliance': {},
            'recommendations': []
        }

        # 分析約束合規性
        total_compliant = 0
        for pool in pools:
            distribution = self._analyze_current_satellite_distribution(pool)
            constraint_check = self._check_quantity_constraints(distribution)

            if not constraint_check['needs_adjustment']:
                total_compliant += 1

        compliance_rate = total_compliant / len(pools) if pools else 0
        report['constraint_compliance'] = {
            'compliant_pools': total_compliant,
            'total_pools': len(pools),
            'compliance_rate': compliance_rate
        }

        # 生成建議
        if compliance_rate < 0.8:
            report['recommendations'].append("建議檢查數量約束設定是否過於嚴格")

        if self.maintenance_stats['constraint_violations'] > 5:
            report['recommendations'].append("頻繁的約束違規，建議優化候選生成策略")

        return report