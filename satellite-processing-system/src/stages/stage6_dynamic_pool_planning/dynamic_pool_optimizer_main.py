#!/usr/bin/env python3
"""
動態池優化主協調器 - 重構後的精簡版本

專責功能：
1. 協調各子模組運作
2. 提供統一接口
3. 管理優化流程
4. 生成最終結果

作者: Claude & Human
創建日期: 2025年
版本: v1.0 - 模組化重構專用
"""

import logging
from typing import Dict, Any, List, Optional
from .satellite_candidate_generator import SatelliteCandidateGenerator
from .quantity_maintenance_engine import QuantityMaintenanceEngine

logger = logging.getLogger(__name__)

class DynamicPoolOptimizerMain:
    """
    動態池優化主協調器 - 精簡版

    整合候選生成、數量維護等子模組
    提供簡潔的優化接口
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化主協調器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.config = config or {}

        # 初始化子模組
        self.candidate_generator = SatelliteCandidateGenerator(config)
        self.quantity_maintenance = QuantityMaintenanceEngine(config)

        # 優化統計
        self.optimization_statistics = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'failed_optimizations': 0,
            'total_processing_time': 0.0
        }

        self.logger.info("✅ 動態池優化主協調器初始化完成")

    def optimize_satellite_pools(self, satellites: List[Dict[str, Any]],
                                requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        優化衛星池 - 主要接口

        Args:
            satellites: 衛星數據列表
            requirements: 優化需求

        Returns:
            優化結果
        """
        try:
            self.logger.info("🚀 開始衛星池優化")
            self.optimization_statistics['total_optimizations'] += 1

            # Step 1: 生成候選池
            strategy = requirements.get('strategy', 'rl_driven')
            candidate_pools = self.candidate_generator.generate_candidate_pools(satellites, strategy)

            if not candidate_pools:
                self.logger.warning("⚠️ 未生成任何候選池")
                return self._create_empty_result()

            # Step 2: 數量維護
            coverage_requirements = requirements.get('coverage_requirements', {})
            optimized_pools = self.quantity_maintenance.maintain_precise_satellite_quantities(
                candidate_pools, coverage_requirements
            )

            # Step 3: 選擇最佳配置
            best_configuration = self._select_best_configuration(optimized_pools, requirements)

            # Step 4: 生成最終結果
            final_result = self._generate_optimization_result(best_configuration, optimized_pools)

            self.optimization_statistics['successful_optimizations'] += 1
            self.logger.info("✅ 衛星池優化完成")

            return final_result

        except Exception as e:
            self.logger.error(f"❌ 衛星池優化失敗: {e}")
            self.optimization_statistics['failed_optimizations'] += 1
            return self._create_error_result(str(e))

    def _select_best_configuration(self, pools: List[Dict[str, Any]],
                                 requirements: Dict[str, Any]) -> Dict[str, Any]:
        """選擇最佳配置"""
        if not pools:
            return {}

        # 簡單選擇第一個池作為最佳（可以後續優化評分邏輯）
        best_pool = pools[0]

        # 計算綜合評分
        candidates = best_pool.get('candidates', [])
        if candidates:
            total_rl_score = sum(c.get('rl_score', 0) for c in candidates)
            avg_rl_score = total_rl_score / len(candidates)
            best_pool['overall_score'] = avg_rl_score

        return best_pool

    def _generate_optimization_result(self, best_configuration: Dict[str, Any],
                                    all_pools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成優化結果"""
        result = {
            'success': True,
            'optimization_completed': True,
            'best_configuration': best_configuration,
            'alternative_pools': all_pools[1:] if len(all_pools) > 1 else [],
            'total_pools_generated': len(all_pools),
            'selected_satellites': best_configuration.get('candidates', []),
            'total_selected_satellites': len(best_configuration.get('candidates', [])),
            'optimization_metadata': {
                'strategy_used': best_configuration.get('pool_type', 'unknown'),
                'rebalancing_applied': best_configuration.get('rebalancing_applied', False),
                'optimization_timestamp': '2025-09-18'
            },
            'statistics': self.get_optimization_statistics()
        }

        return result

    def _create_empty_result(self) -> Dict[str, Any]:
        """創建空結果"""
        return {
            'success': False,
            'optimization_completed': False,
            'reason': 'no_candidate_pools_generated',
            'best_configuration': {},
            'selected_satellites': [],
            'total_selected_satellites': 0,
            'statistics': self.get_optimization_statistics()
        }

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """創建錯誤結果"""
        return {
            'success': False,
            'optimization_completed': False,
            'error': error_message,
            'best_configuration': {},
            'selected_satellites': [],
            'total_selected_satellites': 0,
            'statistics': self.get_optimization_statistics()
        }

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """獲取優化統計"""
        stats = self.optimization_statistics.copy()

        # 添加子模組統計
        stats['candidate_generation'] = self.candidate_generator.get_generation_statistics()
        stats['quantity_maintenance'] = self.quantity_maintenance.get_maintenance_statistics()

        return stats

    def generate_optimization_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成優化報告"""
        successful_optimizations = [r for r in results if r.get('success', False)]

        report = {
            'timestamp': '2025-09-18',
            'total_optimization_requests': len(results),
            'successful_optimizations': len(successful_optimizations),
            'success_rate': len(successful_optimizations) / len(results) if results else 0,
            'average_satellites_selected': 0,
            'most_used_strategy': 'unknown',
            'recommendations': []
        }

        if successful_optimizations:
            total_satellites = sum(r.get('total_selected_satellites', 0) for r in successful_optimizations)
            report['average_satellites_selected'] = total_satellites / len(successful_optimizations)

            # 找出最常用的策略
            strategies = [r.get('optimization_metadata', {}).get('strategy_used', 'unknown')
                         for r in successful_optimizations]
            if strategies:
                most_common = max(set(strategies), key=strategies.count)
                report['most_used_strategy'] = most_common

        # 生成建議
        if report['success_rate'] < 0.8:
            report['recommendations'].append("優化成功率偏低，建議檢查輸入數據品質")

        if report['average_satellites_selected'] < 10:
            report['recommendations'].append("選中衛星數量偏少，建議調整候選生成策略")

        return report