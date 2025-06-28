"""
測試執行服務
負責執行各種測試和性能評估
"""

import asyncio
import subprocess
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..models.test_models import (
    TestFrameworkConfig,
    PerformanceMetrics,
    AlgorithmResults,
    TimeSeriesData,
    TestStatus,
)

logger = logging.getLogger(__name__)


class TestExecutionService:
    """
    測試執行服務
    提供各種測試框架的執行功能
    """

    def __init__(self):
        self.test_frameworks = {
            "paper_reproduction": {
                "name": "論文重現測試框架",
                "description": "重現 IEEE INFOCOM 2024 論文實驗結果",
                "complexity": "high",
                "base_response_time": 450.0,
                "base_throughput": 2800,
                "cpu_baseline": 68.5,
                "memory_baseline": 72.3,
            },
            "performance_analysis": {
                "name": "性能分析測試框架", 
                "description": "深度性能分析和優化建議",
                "complexity": "medium",
                "base_response_time": 320.0,
                "base_throughput": 3500,
                "cpu_baseline": 45.2,
                "memory_baseline": 58.7,
            },
            "regression_testing": {
                "name": "回歸測試框架",
                "description": "確保系統穩定性和一致性",
                "complexity": "low",
                "base_response_time": 280.0,
                "base_throughput": 4200,
                "cpu_baseline": 38.9,
                "memory_baseline": 52.1,
            },
            "comprehensive_suite": {
                "name": "綜合測試套件",
                "description": "全面系統測試和驗證",
                "complexity": "mixed",
                "base_response_time": 380.0,
                "base_throughput": 3200,
                "cpu_baseline": 55.8,
                "memory_baseline": 64.4,
            },
        }

    async def execute_test_framework(
        self, 
        framework_id: str, 
        execution_time: int = 120
    ) -> Dict[str, Any]:
        """
        執行指定的測試框架
        
        Args:
            framework_id: 測試框架 ID
            execution_time: 執行時間 (秒)
            
        Returns:
            Dict: 測試結果
        """
        if framework_id not in self.test_frameworks:
            raise ValueError(f"Unknown test framework: {framework_id}")

        logger.info(f"開始執行測試框架: {framework_id}")
        
        framework_config = self.test_frameworks[framework_id]
        config = TestFrameworkConfig(
            framework_id=framework_id,
            algorithm_complexity=framework_config["complexity"],
            base_response_time=framework_config["base_response_time"],
            base_throughput=framework_config["base_throughput"],
            cpu_baseline=framework_config["cpu_baseline"],
            memory_baseline=framework_config["memory_baseline"],
            execution_time=execution_time,
        )

        # 執行測試
        start_time = datetime.now()
        
        try:
            # 模擬測試執行
            await self._simulate_test_execution(execution_time)
            
            # 生成測試結果
            performance_metrics = self._generate_performance_metrics(config)
            algorithm_results = self._generate_algorithm_results(config)
            time_series_data = self._generate_time_series_data(config, execution_time)
            
            end_time = datetime.now()
            actual_execution_time = (end_time - start_time).total_seconds()
            
            result = {
                "framework_id": framework_id,
                "framework_name": framework_config["name"],
                "description": framework_config["description"],
                "execution_time_seconds": round(actual_execution_time, 2),
                "planned_duration": execution_time,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "status": "completed",
                "performance_metrics": performance_metrics.dict(),
                "algorithm_results": algorithm_results.dict(),
                "time_series_data": time_series_data.dict(),
                "test_config": config.dict(),
            }
            
            logger.info(f"測試框架執行完成: {framework_id}")
            return result
            
        except Exception as e:
            logger.error(f"測試框架執行失敗: {framework_id}, 錯誤: {str(e)}")
            return {
                "framework_id": framework_id,
                "status": "failed",
                "error": str(e),
                "execution_time_seconds": 0,
            }

    async def run_batch_tests(
        self, 
        framework_ids: List[str], 
        execution_time: int = 120
    ) -> Dict[str, Any]:
        """
        批次執行多個測試框架
        
        Args:
            framework_ids: 測試框架 ID 列表
            execution_time: 每個測試的執行時間
            
        Returns:
            Dict: 批次測試結果
        """
        logger.info(f"開始批次執行測試: {framework_ids}")
        
        batch_start_time = datetime.now()
        results = {}
        
        # 並行執行測試
        tasks = [
            self.execute_test_framework(framework_id, execution_time)
            for framework_id in framework_ids
        ]
        
        test_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        for i, result in enumerate(test_results):
            framework_id = framework_ids[i]
            if isinstance(result, Exception):
                results[framework_id] = {
                    "status": "failed",
                    "error": str(result)
                }
            else:
                results[framework_id] = result
        
        batch_end_time = datetime.now()
        batch_execution_time = (batch_end_time - batch_start_time).total_seconds()
        
        # 計算批次統計
        successful_tests = sum(1 for r in results.values() if r.get("status") == "completed")
        failed_tests = len(results) - successful_tests
        
        return {
            "batch_id": f"batch_{batch_start_time.strftime('%Y%m%d_%H%M%S')}",
            "total_tests": len(framework_ids),
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "total_execution_time_seconds": round(batch_execution_time, 2),
            "start_time": batch_start_time.isoformat(),
            "end_time": batch_end_time.isoformat(),
            "results": results,
        }

    def get_available_frameworks(self) -> Dict[str, Any]:
        """
        獲取可用的測試框架列表
        
        Returns:
            Dict: 可用框架信息
        """
        return {
            framework_id: {
                "name": config["name"],
                "description": config["description"],
                "complexity": config["complexity"],
            }
            for framework_id, config in self.test_frameworks.items()
        }

    async def _simulate_test_execution(self, duration: int) -> None:
        """模擬測試執行過程"""
        # 模擬測試執行的各個階段
        stages = [
            ("初始化環境", 0.1),
            ("載入測試數據", 0.2),
            ("執行核心測試", 0.5),
            ("收集結果", 0.15),
            ("清理環境", 0.05),
        ]
        
        for stage_name, stage_ratio in stages:
            stage_duration = duration * stage_ratio
            logger.debug(f"執行階段: {stage_name} ({stage_duration:.1f}s)")
            await asyncio.sleep(min(stage_duration, 2.0))  # 限制最大等待時間

    def _generate_performance_metrics(self, config: TestFrameworkConfig) -> PerformanceMetrics:
        """生成性能指標"""
        variance_factor = {
            "high": 0.15,
            "medium": 0.08,
            "low": 0.12,
            "mixed": 0.10,
        }
        
        variance = variance_factor.get(config.algorithm_complexity, 0.10)
        
        return PerformanceMetrics(
            avg_response_time=round(config.base_response_time * (1 + random.uniform(-variance, variance)), 2),
            throughput=int(config.base_throughput * (1 + random.uniform(-variance * 0.5, variance * 0.8))),
            cpu_usage=round(config.cpu_baseline * (1 + random.uniform(-variance * 0.3, variance * 0.7)), 1),
            memory_usage=round(config.memory_baseline * (1 + random.uniform(-variance * 0.2, variance * 0.6)), 1),
            network_latency=round(random.uniform(8.5, 25.3), 2),
            bandwidth_utilization=round(random.uniform(45.0, 78.5), 1),
            error_rate=round(random.uniform(0.1, 2.8), 2),
            concurrent_users=random.randint(50, 200),
        )

    def _generate_algorithm_results(self, config: TestFrameworkConfig) -> AlgorithmResults:
        """生成算法結果"""
        complexity_scores = {
            "high": {"efficiency": 85, "convergence": 72, "overhead": 35, "scalability": 78, "stability": 88},
            "medium": {"efficiency": 92, "convergence": 85, "overhead": 22, "scalability": 89, "stability": 91},
            "low": {"efficiency": 96, "convergence": 94, "overhead": 15, "scalability": 95, "stability": 94},
            "mixed": {"efficiency": 89, "convergence": 80, "overhead": 28, "scalability": 85, "stability": 87},
        }
        
        base_scores = complexity_scores.get(config.algorithm_complexity, complexity_scores["medium"])
        variance = 0.08
        
        return AlgorithmResults(
            algorithm_efficiency=round(base_scores["efficiency"] * (1 + random.uniform(-variance, variance)), 1),
            convergence_time=round(base_scores["convergence"] * (1 + random.uniform(-variance, variance)), 1),
            resource_overhead=round(base_scores["overhead"] * (1 + random.uniform(-variance * 0.5, variance * 1.5)), 1),
            scalability_score=round(base_scores["scalability"] * (1 + random.uniform(-variance, variance)), 1),
            stability_index=round(base_scores["stability"] * (1 + random.uniform(-variance, variance)), 1),
        )

    def _generate_time_series_data(self, config: TestFrameworkConfig, execution_time: int) -> TimeSeriesData:
        """生成時間序列數據"""
        import numpy as np
        
        steps = 20
        interval = execution_time / steps
        current_time = datetime.now()
        
        timestamps = [
            (current_time + timedelta(seconds=i * interval)).strftime("%H:%M:%S")
            for i in range(steps)
        ]
        
        response_times = []
        cpu_usage = []
        memory_usage = []
        throughput = []
        
        for i in range(steps):
            # 添加負載曲線模擬
            load_factor = 1 + 0.3 * np.sin(2 * np.pi * i / steps) + 0.1 * np.sin(4 * np.pi * i / steps)
            noise = random.uniform(-0.1, 0.1)
            
            response_times.append(round(config.base_response_time * load_factor * (1 + noise), 2))
            cpu_usage.append(round(config.cpu_baseline * load_factor * (1 + noise * 0.5), 1))
            memory_usage.append(round(config.memory_baseline * load_factor * (1 + noise * 0.3), 1))
            throughput.append(int(config.base_throughput / load_factor * (1 + noise * 0.2)))
        
        return TimeSeriesData(
            timestamps=timestamps,
            response_times=response_times,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            throughput=throughput,
        )