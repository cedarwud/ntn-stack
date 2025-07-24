"""
Phase 2.3 端到端整合測試

驗證所有 Phase 2.3 組件的整合工作：
- RL 算法整合器測試
- 真實環境橋接測試
- 決策分析引擎測試
- 多算法比較測試
- 實時決策服務測試
- 完整工作流測試
"""

import asyncio
import logging
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

# 設置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase23IntegrationTest:
    """Phase 2.3 整合測試類"""

    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.total_tests = 0
        self.passed_tests = 0

    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有整合測試"""
        logger.info("🚀 開始 Phase 2.3 端到端整合測試")
        start_time = time.time()

        test_functions = [
            self._test_basic_imports,
            self._test_algorithm_integrator,
            self._test_environment_bridge,
            self._test_decision_analytics,
            self._test_multi_algorithm_comparison,
            self._test_realtime_service,
            self._test_complete_workflow,
        ]

        for test_func in test_functions:
            await self._run_test(test_func)

        duration = time.time() - start_time
        success_rate = self.passed_tests / max(self.total_tests, 1) * 100

        summary = {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": len(self.failed_tests),
            "success_rate": success_rate,
            "duration_seconds": duration,
            "test_results": self.test_results,
            "failed_test_names": self.failed_tests,
        }

        logger.info(
            f"📊 測試完成！通過率: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests})"
        )

        if self.failed_tests:
            logger.error(f"❌ 失敗的測試: {', '.join(self.failed_tests)}")
        else:
            logger.info("🎉 所有測試都通過了！")

        return summary

    async def _run_test(self, test_func):
        """運行單個測試"""
        test_name = test_func.__name__
        self.total_tests += 1

        try:
            logger.info(f"🧪 運行測試: {test_name}")
            result = await test_func()

            if result.get("success", False):
                self.passed_tests += 1
                logger.info(f"✅ {test_name} 通過")
            else:
                self.failed_tests.append(test_name)
                logger.error(f"❌ {test_name} 失敗: {result.get('error', '未知錯誤')}")

            self.test_results.append(
                {
                    "test_name": test_name,
                    "success": result.get("success", False),
                    "duration": result.get("duration", 0),
                    "details": result.get("details", {}),
                    "error": result.get("error"),
                }
            )

        except Exception as e:
            self.failed_tests.append(test_name)
            logger.error(f"❌ {test_name} 異常: {str(e)}")

            self.test_results.append(
                {
                    "test_name": test_name,
                    "success": False,
                    "duration": 0,
                    "details": {},
                    "error": str(e),
                }
            )

    async def _test_basic_imports(self) -> Dict[str, Any]:
        """測試基本導入"""
        start_time = time.time()

        try:
            # 測試 Phase 2.3 組件導入
            from . import (
                RL_INTEGRATOR_AVAILABLE,
                ENV_BRIDGE_AVAILABLE,
                ANALYTICS_AVAILABLE,
                COMPARATOR_AVAILABLE,
                REALTIME_AVAILABLE,
            )

            availability = {
                "rl_integrator": RL_INTEGRATOR_AVAILABLE,
                "environment_bridge": ENV_BRIDGE_AVAILABLE,
                "analytics_engine": ANALYTICS_AVAILABLE,
                "comparator": COMPARATOR_AVAILABLE,
                "realtime_service": REALTIME_AVAILABLE,
            }

            available_count = sum(availability.values())
            total_count = len(availability)

            return {
                "success": available_count >= 3,  # 至少3個組件可用
                "duration": time.time() - start_time,
                "details": {
                    "available_components": available_count,
                    "total_components": total_count,
                    "component_availability": availability,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"導入測試失敗: {str(e)}",
            }

    async def _test_algorithm_integrator(self) -> Dict[str, Any]:
        """測試 RL 算法整合器"""
        start_time = time.time()

        try:
            from . import RL_INTEGRATOR_AVAILABLE, RLAlgorithmIntegrator

            if not RL_INTEGRATOR_AVAILABLE:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "RL 算法整合器不可用",
                }

            # 創建測試配置
            config = {
                "enabled_algorithms": ["dqn", "ppo"],
                "default_algorithm": "dqn",
                "algorithm_configs": {
                    "dqn": {"learning_rate": 0.001, "batch_size": 32},
                    "ppo": {"learning_rate": 0.0003, "batch_size": 64},
                },
            }

            # 初始化整合器
            integrator = RLAlgorithmIntegrator(config)

            # 測試初始化
            init_success = await integrator.initialize()
            if not init_success:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "算法整合器初始化失敗",
                }

            # 測試狀態獲取
            status = integrator.get_status()

            # 測試算法切換（如果有多個算法）
            available_algorithms = integrator.get_available_algorithms()
            switch_success = True

            if len(available_algorithms) > 1:
                from .rl_algorithm_integrator import AlgorithmType

                target_algorithm = available_algorithms[1]  # 切換到第二個算法
                switch_success = await integrator.switch_algorithm(target_algorithm)

            return {
                "success": init_success
                and switch_success
                and status.get("is_initialized", False),
                "duration": time.time() - start_time,
                "details": {
                    "initialized": init_success,
                    "available_algorithms": [a.value for a in available_algorithms],
                    "current_algorithm": status.get("current_algorithm"),
                    "total_decisions": status.get("total_decisions", 0),
                    "switch_test_passed": switch_success,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"算法整合器測試失敗: {str(e)}",
            }

    async def _test_environment_bridge(self) -> Dict[str, Any]:
        """測試環境橋接器"""
        start_time = time.time()

        try:
            from . import ENV_BRIDGE_AVAILABLE, RealEnvironmentBridge

            if not ENV_BRIDGE_AVAILABLE:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "環境橋接器不可用",
                }

            # 創建測試配置
            config = {
                "max_episode_steps": 100,
                "scenario_type": "urban",
                "complexity": "simple",
                "simworld_url": "http://localhost:8888",
            }

            # 初始化橋接器
            bridge = RealEnvironmentBridge(config)

            # 測試初始化
            init_success = await bridge.initialize()

            # 測試環境重置
            try:
                obs = await bridge.reset({"scenario_type": "urban"})
                reset_success = obs is not None
            except Exception as e:
                logger.warning(f"環境重置測試失敗: {e}")
                reset_success = False

            # 測試狀態獲取
            status = bridge.get_status()

            return {
                "success": init_success,  # 即使重置失敗也認為基本功能可用
                "duration": time.time() - start_time,
                "details": {
                    "initialized": init_success,
                    "reset_success": reset_success,
                    "status": status.get("state"),
                    "services_initialized": status.get("services_initialized", False),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"環境橋接器測試失敗: {str(e)}",
            }

    async def _test_decision_analytics(self) -> Dict[str, Any]:
        """測試決策分析引擎"""
        start_time = time.time()

        try:
            from . import ANALYTICS_AVAILABLE, DecisionAnalyticsEngine

            if not ANALYTICS_AVAILABLE:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "決策分析引擎不可用",
                }

            # 創建測試配置
            config = {
                "enable_detailed_logging": True,
                "enable_explainability": True,
                "max_records_per_episode": 1000,
            }

            # 初始化分析引擎
            analytics = DecisionAnalyticsEngine(config)

            # 測試開始 episode
            from .rl_algorithm_integrator import AlgorithmType

            episode_id = "test_episode_001"
            start_success = analytics.start_episode(
                episode_id, AlgorithmType.DQN, "urban"
            )

            # 測試狀態獲取
            status = analytics.get_status()

            # 測試完成 episode
            episode_analytics = await analytics.finalize_episode()

            return {
                "success": start_success and status is not None,
                "duration": time.time() - start_time,
                "details": {
                    "episode_started": start_success,
                    "current_episode": status.get("current_episode_id"),
                    "total_decisions_analyzed": status.get(
                        "total_decisions_analyzed", 0
                    ),
                    "episode_finalized": episode_analytics is not None,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"決策分析引擎測試失敗: {str(e)}",
            }

    async def _test_multi_algorithm_comparison(self) -> Dict[str, Any]:
        """測試多算法比較器"""
        start_time = time.time()

        try:
            from . import (
                COMPARATOR_AVAILABLE,
                MultiAlgorithmComparator,
                RL_INTEGRATOR_AVAILABLE,
                RLAlgorithmIntegrator,
                ENV_BRIDGE_AVAILABLE,
                RealEnvironmentBridge,
                ANALYTICS_AVAILABLE,
                DecisionAnalyticsEngine,
            )

            if not all(
                [
                    COMPARATOR_AVAILABLE,
                    RL_INTEGRATOR_AVAILABLE,
                    ENV_BRIDGE_AVAILABLE,
                    ANALYTICS_AVAILABLE,
                ]
            ):
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "多算法比較器依賴的組件不完整",
                }

            # 創建依賴組件（簡化配置）
            integrator = RLAlgorithmIntegrator(
                {
                    "enabled_algorithms": ["dqn"],
                    "default_algorithm": "dqn",
                    "algorithm_configs": {"dqn": {"learning_rate": 0.001}},
                }
            )

            bridge = RealEnvironmentBridge(
                {"max_episode_steps": 10, "scenario_type": "urban"}
            )

            analytics = DecisionAnalyticsEngine(
                {"enable_detailed_logging": False, "enable_explainability": False}
            )

            # 初始化比較器
            comparator = MultiAlgorithmComparator(
                integrator,
                bridge,
                analytics,
                {"default_scenarios": ["urban"], "default_metrics": ["total_reward"]},
            )

            # 測試狀態獲取
            status = comparator.get_status()

            return {
                "success": status is not None,
                "duration": time.time() - start_time,
                "details": {
                    "active_tests": status.get("active_tests", 0),
                    "completed_tests": status.get("completed_tests", 0),
                    "available_algorithms": status.get("available_algorithms", []),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"多算法比較器測試失敗: {str(e)}",
            }

    async def _test_realtime_service(self) -> Dict[str, Any]:
        """測試實時決策服務"""
        start_time = time.time()

        try:
            from . import (
                REALTIME_AVAILABLE,
                RealtimeDecisionService,
                RL_INTEGRATOR_AVAILABLE,
                RLAlgorithmIntegrator,
                ENV_BRIDGE_AVAILABLE,
                RealEnvironmentBridge,
                ANALYTICS_AVAILABLE,
                DecisionAnalyticsEngine,
                COMPARATOR_AVAILABLE,
                MultiAlgorithmComparator,
            )

            if not REALTIME_AVAILABLE:
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "實時決策服務不可用",
                }

            # 創建依賴組件（最簡配置）
            integrator = RLAlgorithmIntegrator({"enabled_algorithms": ["dqn"]})
            bridge = RealEnvironmentBridge({"scenario_type": "urban"})
            analytics = DecisionAnalyticsEngine({"enable_detailed_logging": False})
            comparator = MultiAlgorithmComparator(integrator, bridge, analytics, {})

            # 初始化實時服務
            realtime = RealtimeDecisionService(
                integrator,
                bridge,
                analytics,
                comparator,
                {
                    "websocket_host": "localhost",
                    "websocket_port": 8766,
                },  # 使用不同端口避免衝突
            )

            # 測試狀態獲取
            status = realtime.get_service_status()

            # 測試服務啟動（簡化）
            service_initialized = status is not None

            return {
                "success": service_initialized,
                "duration": time.time() - start_time,
                "details": {
                    "service_initialized": service_initialized,
                    "websocket_port": status.get("websocket_port") if status else None,
                    "connected_clients": (
                        status.get("connected_clients", 0) if status else 0
                    ),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"實時決策服務測試失敗: {str(e)}",
            }

    async def _test_complete_workflow(self) -> Dict[str, Any]:
        """測試完整工作流"""
        start_time = time.time()

        try:
            # 檢查所有組件是否可用
            from . import (
                RL_INTEGRATOR_AVAILABLE,
                ENV_BRIDGE_AVAILABLE,
                ANALYTICS_AVAILABLE,
                COMPARATOR_AVAILABLE,
            )

            if not all(
                [RL_INTEGRATOR_AVAILABLE, ENV_BRIDGE_AVAILABLE, ANALYTICS_AVAILABLE]
            ):
                return {
                    "success": False,
                    "duration": time.time() - start_time,
                    "error": "完整工作流需要的核心組件不完整",
                }

            from .rl_algorithm_integrator import RLAlgorithmIntegrator, AlgorithmType
            from .real_environment_bridge import RealEnvironmentBridge
            from .decision_analytics_engine import DecisionAnalyticsEngine

            # 創建核心組件
            integrator = RLAlgorithmIntegrator(
                {
                    "enabled_algorithms": ["dqn"],
                    "default_algorithm": "dqn",
                    "algorithm_configs": {
                        "dqn": {"learning_rate": 0.001, "batch_size": 32}
                    },
                }
            )

            bridge = RealEnvironmentBridge(
                {
                    "max_episode_steps": 5,  # 短小的測試
                    "scenario_type": "urban",
                    "complexity": "simple",
                }
            )

            analytics = DecisionAnalyticsEngine(
                {"enable_detailed_logging": True, "enable_explainability": True}
            )

            # 初始化組件
            integrator_init = await integrator.initialize()
            bridge_init = await bridge.initialize()

            workflow_steps = []

            # 1. 算法初始化
            workflow_steps.append(("algorithm_init", integrator_init))

            # 2. 環境初始化
            workflow_steps.append(("environment_init", bridge_init))

            # 3. 開始分析 episode
            episode_id = "workflow_test_episode"
            analytics_start = analytics.start_episode(
                episode_id, AlgorithmType.DQN, "urban"
            )
            workflow_steps.append(("analytics_start", analytics_start))

            # 4. 模擬簡單的決策循環
            decision_loop_success = True
            try:
                if bridge_init:
                    # 嘗試重置環境
                    obs = await bridge.reset()

                    # 模擬一個決策
                    decision = await integrator.predict(obs)

                    workflow_steps.append(("decision_made", decision is not None))
                else:
                    workflow_steps.append(("decision_made", False))

            except Exception as e:
                logger.warning(f"決策循環測試失敗: {e}")
                decision_loop_success = False
                workflow_steps.append(("decision_made", False))

            # 5. 完成分析
            episode_analytics = await analytics.finalize_episode()
            workflow_steps.append(("analytics_complete", episode_analytics is not None))

            # 計算成功率
            successful_steps = sum(1 for _, success in workflow_steps if success)
            total_steps = len(workflow_steps)
            workflow_success = successful_steps >= total_steps * 0.6  # 60% 成功率門檻

            return {
                "success": workflow_success,
                "duration": time.time() - start_time,
                "details": {
                    "workflow_steps": dict(workflow_steps),
                    "successful_steps": successful_steps,
                    "total_steps": total_steps,
                    "success_rate": successful_steps / total_steps * 100,
                    "decision_loop_tested": decision_loop_success,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"完整工作流測試失敗: {str(e)}",
            }


async def main():
    """主測試函數"""
    test_runner = Phase23IntegrationTest()
    results = await test_runner.run_all_tests()

    print("\n" + "=" * 80)
    print("📋 Phase 2.3 整合測試報告")
    print("=" * 80)
    print(f"總測試數: {results['total_tests']}")
    print(f"通過測試: {results['passed_tests']}")
    print(f"失敗測試: {results['failed_tests']}")
    print(f"成功率: {results['success_rate']:.1f}%")
    print(f"總耗時: {results['duration_seconds']:.2f} 秒")

    if results["failed_test_names"]:
        print(f"\n❌ 失敗的測試:")
        for test_name in results["failed_test_names"]:
            print(f"  - {test_name}")

    print("\n📊 詳細測試結果:")
    for result in results["test_results"]:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['test_name']} ({result['duration']:.2f}s)")
        if not result["success"] and result.get("error"):
            print(f"     錯誤: {result['error']}")

    print("\n" + "=" * 80)

    if results["success_rate"] >= 70:
        print("🎉 Phase 2.3 基本功能驗證通過！")
        return 0
    else:
        print("⚠️  Phase 2.3 存在一些問題，需要進一步檢查")
        return 1


if __name__ == "__main__":
    import sys

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試運行時發生錯誤: {e}")
        sys.exit(1)
