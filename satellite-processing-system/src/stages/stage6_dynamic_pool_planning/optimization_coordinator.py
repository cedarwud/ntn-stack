"""
OptimizationCoordinator - 優化協調器

統一管理三層優化架構：
1. CoverageOptimizer - 空間覆蓋優化
2. TemporalOptimizer - 時域優化
3. PoolOptimizer - 資源池優化

職責劃分：
- 協調各優化引擎執行順序
- 整合優化結果
- 提供統一的優化介面
- 避免模組間功能重複
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class OptimizationCoordinator:
    """優化協調器 - 統一管理三層優化架構"""

    def __init__(self, coordinator_config: Dict[str, Any] = None):
        """初始化優化協調器"""
        self.config = coordinator_config or self._get_default_config()

        # 初始化三個優化器
        self._initialize_optimizers()

        # 協調統計
        self.coordination_stats = {
            "total_optimization_rounds": 0,
            "coverage_optimizations": 0,
            "temporal_optimizations": 0,
            "pool_optimizations": 0,
            "coordination_start_time": None,
            "total_coordination_time": 0.0,
            "optimization_sequence": []
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設協調配置"""
        return {
            "optimization_sequence": ["coverage", "temporal", "pool"],  # 預設執行順序
            "enable_iterative_optimization": True,  # 啟用迭代優化
            "max_iterations": 3,  # 最大迭代次數
            "convergence_threshold": 0.95,  # 收斂門檻
            "enable_cross_validation": True,  # 啟用交叉驗證
            "optimization_timeout": 300  # 優化超時（秒）
        }

    def _initialize_optimizers(self):
        """初始化三個優化引擎"""
        try:
            # 嘗試相對導入
            try:
                from .coverage_optimizer import CoverageOptimizer
                from .temporal_optimizer import TemporalOptimizer
                from .pool_optimizer import PoolOptimizer
            except ImportError:
                # 回退到絕對導入
                from stages.stage6_dynamic_pool_planning.coverage_optimizer import CoverageOptimizer
                from stages.stage6_dynamic_pool_planning.temporal_optimizer import TemporalOptimizer
                from stages.stage6_dynamic_pool_planning.pool_optimizer import PoolOptimizer

            # 初始化優化器
            self.coverage_optimizer = CoverageOptimizer(self.config.get("coverage_config", {}))
            self.temporal_optimizer = TemporalOptimizer(self.config.get("temporal_config", {}))
            self.pool_optimizer = PoolOptimizer(self.config.get("pool_config", {}))

            logger.info("已成功初始化三個重構後的優化引擎")

        except ImportError as e:
            logger.error(f"導入優化引擎失敗: {e}")
            raise

    def execute_coordinated_optimization(self,
                                       satellite_candidates: List[Dict],
                                       optimization_objectives: Dict[str, Any]) -> Dict[str, Any]:
        """執行協調優化流程"""

        self.coordination_stats["coordination_start_time"] = datetime.now()
        start_time = datetime.now()

        logger.info(f"開始協調優化流程，候選衛星數量: {len(satellite_candidates)}")

        try:
            # 初始化優化結果
            optimization_results = {
                "input_candidates": satellite_candidates,
                "objectives": optimization_objectives,
                "optimization_sequence": [],
                "final_selected_satellites": [],
                "optimization_performance": {},
                "coordination_metadata": {}
            }

            # 根據配置執行優化序列
            current_candidates = satellite_candidates

            for iteration in range(self.config.get("max_iterations", 3)):
                logger.info(f"執行第 {iteration + 1} 輪優化迭代")

                iteration_results = self._execute_optimization_iteration(
                    current_candidates,
                    optimization_objectives,
                    iteration
                )

                optimization_results["optimization_sequence"].append(iteration_results)
                current_candidates = iteration_results.get("optimized_candidates", current_candidates)

                # 檢查收斂條件
                if self._check_convergence(iteration_results):
                    logger.info(f"優化在第 {iteration + 1} 輪達到收斂")
                    break

            # 設定最終結果
            optimization_results["final_selected_satellites"] = current_candidates
            optimization_results["coordination_metadata"] = self._generate_coordination_metadata()

            # 更新統計
            self.coordination_stats["total_coordination_time"] = (datetime.now() - start_time).total_seconds()
            self.coordination_stats["total_optimization_rounds"] += 1

            logger.info(f"協調優化完成，最終選擇 {len(current_candidates)} 顆衛星")

            return optimization_results

        except Exception as e:
            logger.error(f"協調優化失敗: {e}")
            raise

    def _execute_optimization_iteration(self,
                                      candidates: List[Dict],
                                      objectives: Dict[str, Any],
                                      iteration: int) -> Dict[str, Any]:
        """執行單次優化迭代"""

        iteration_results = {
            "iteration": iteration,
            "input_count": len(candidates),
            "optimization_steps": [],
            "optimized_candidates": candidates,
            "iteration_performance": {}
        }

        current_candidates = candidates

        # 按照配置的順序執行優化
        for optimizer_type in self.config.get("optimization_sequence", ["coverage", "temporal", "pool"]):

            step_start_time = datetime.now()

            if optimizer_type == "coverage":
                step_results = self._execute_coverage_optimization(current_candidates, objectives)
                self.coordination_stats["coverage_optimizations"] += 1

            elif optimizer_type == "temporal":
                step_results = self._execute_temporal_optimization(current_candidates, objectives)
                self.coordination_stats["temporal_optimizations"] += 1

            elif optimizer_type == "pool":
                step_results = self._execute_pool_optimization(current_candidates, objectives)
                self.coordination_stats["pool_optimizations"] += 1

            else:
                logger.warning(f"未知的優化類型: {optimizer_type}")
                continue

            # 記錄步驟結果
            step_duration = (datetime.now() - step_start_time).total_seconds()
            step_results["optimization_duration"] = step_duration
            step_results["optimizer_type"] = optimizer_type

            iteration_results["optimization_steps"].append(step_results)
            current_candidates = step_results.get("optimized_satellites", current_candidates)

            logger.info(f"完成 {optimizer_type} 優化，處理時間: {step_duration:.2f}秒")

        iteration_results["optimized_candidates"] = current_candidates
        iteration_results["output_count"] = len(current_candidates)

        return iteration_results

    def _execute_coverage_optimization(self,
                                     candidates: List[Dict],
                                     objectives: Dict[str, Any]) -> Dict[str, Any]:
        """執行空間覆蓋優化"""
        try:
            # 調用新的覆蓋優化器
            coverage_results = self.coverage_optimizer.optimize_spatial_coverage(
                candidates, objectives.get("coverage_requirements", {})
            )

            return {
                "optimizer": "coverage",
                "optimized_satellites": coverage_results.get("selected_satellites", candidates),
                "optimization_metrics": coverage_results.get("spatial_analysis", {}),
                "coverage_improvement": coverage_results.get("optimization_duration", 0.0)
            }

        except Exception as e:
            logger.error(f"覆蓋優化失敗: {e}")
            return {"optimizer": "coverage", "optimized_satellites": candidates, "error": str(e)}

    def _execute_temporal_optimization(self,
                                     candidates: List[Dict],
                                     objectives: Dict[str, Any]) -> Dict[str, Any]:
        """執行時域優化"""
        try:
            # 調用新的時域優化器
            temporal_results = self.temporal_optimizer.optimize_temporal_coverage(
                candidates, objectives.get("temporal_requirements", {})
            )

            return {
                "optimizer": "temporal",
                "optimized_satellites": temporal_results.get("optimized_satellites", candidates),
                "optimization_metrics": temporal_results.get("efficiency_metrics", {}),
                "temporal_improvement": temporal_results.get("optimization_duration", 0.0)
            }

        except Exception as e:
            logger.error(f"時域優化失敗: {e}")
            return {"optimizer": "temporal", "optimized_satellites": candidates, "error": str(e)}

    def _execute_pool_optimization(self,
                                 candidates: List[Dict],
                                 objectives: Dict[str, Any]) -> Dict[str, Any]:
        """執行資源池優化"""
        try:
            # 調用新的池優化器
            pool_results = self.pool_optimizer.optimize_pool_configuration(
                candidates, objectives.get("pool_requirements", {})
            )

            return {
                "optimizer": "pool",
                "optimized_satellites": pool_results.get("optimized_pool", candidates),
                "optimization_metrics": pool_results.get("quantity_metrics", {}),
                "pool_improvement": pool_results.get("optimization_duration", 0.0)
            }

        except Exception as e:
            logger.error(f"池優化失敗: {e}")
            return {"optimizer": "pool", "optimized_satellites": candidates, "error": str(e)}

    def _check_convergence(self, iteration_results: Dict[str, Any]) -> bool:
        """檢查優化收斂條件"""
        # 簡化的收斂檢查邏輯
        convergence_threshold = self.config.get("convergence_threshold", 0.95)

        # 檢查各優化步驟的改善程度
        total_improvement = 0.0
        improvement_count = 0

        for step in iteration_results.get("optimization_steps", []):
            if "coverage_improvement" in step:
                total_improvement += step["coverage_improvement"]
                improvement_count += 1
            if "temporal_improvement" in step:
                total_improvement += step["temporal_improvement"]
                improvement_count += 1
            if "pool_improvement" in step:
                total_improvement += step["pool_improvement"]
                improvement_count += 1

        if improvement_count > 0:
            average_improvement = total_improvement / improvement_count
            return average_improvement >= convergence_threshold

        return False

    def _generate_coordination_metadata(self) -> Dict[str, Any]:
        """產生協調後設資料"""
        return {
            "coordination_timestamp": datetime.now().isoformat(),
            "coordination_statistics": self.coordination_stats.copy(),
            "optimization_configuration": self.config.copy(),
            "optimizer_versions": {
                "coverage_optimizer": "1.0.0",
                "temporal_optimizer": "1.0.0",
                "pool_optimizer": "1.0.0"
            }
        }

    def get_coordination_statistics(self) -> Dict[str, Any]:
        """獲取協調統計資訊"""
        return self.coordination_stats.copy()

    def reset_coordination_statistics(self):
        """重置協調統計"""
        self.coordination_stats = {
            "total_optimization_rounds": 0,
            "coverage_optimizations": 0,
            "temporal_optimizations": 0,
            "pool_optimizations": 0,
            "coordination_start_time": None,
            "total_coordination_time": 0.0,
            "optimization_sequence": []
        }
        logger.info("已重置協調統計")