"""
🌐 算法生態系統管理器

統一管理算法生態系統的所有組件，提供一站式的接口。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import yaml

from .interfaces import HandoverAlgorithm, HandoverContext, HandoverDecision
from .registry import AlgorithmRegistry

# 嘗試導入協調器
try:
    from .orchestrator import HandoverOrchestrator, OrchestratorConfig

    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    try:
        # 嘗試從其他位置導入
        import sys
        import os

        # 添加算法生態系統路徑
        current_dir = os.path.dirname(__file__)
        sys.path.insert(0, current_dir)
        from orchestrator import HandoverOrchestrator, OrchestratorConfig

        ORCHESTRATOR_AVAILABLE = True
    except ImportError:
        # 創建佔位符類
        class HandoverOrchestrator:
            def __init__(self, *args, **kwargs):
                self.initialized = False

            async def initialize(self):
                pass

            async def predict_handover(self, *args, **kwargs):
                return None

        class OrchestratorConfig:
            def __init__(self, *args, **kwargs):
                pass

        ORCHESTRATOR_AVAILABLE = False
from .environment_manager import EnvironmentManager

# 可選依賴導入
try:
    from .analysis_engine import PerformanceAnalysisEngine

    ANALYSIS_ENGINE_AVAILABLE = True
except ImportError:

    class PerformanceAnalysisEngine:
        def __init__(self, *args, **kwargs):
            pass

    ANALYSIS_ENGINE_AVAILABLE = False

try:
    from .training_pipeline import RLTrainingPipeline

    TRAINING_PIPELINE_AVAILABLE = True
except ImportError:

    class RLTrainingPipeline:
        def __init__(self, *args, **kwargs):
            pass

    TRAINING_PIPELINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class AlgorithmEcosystemManager:
    """算法生態系統管理器

    統一管理和協調算法生態系統的所有組件：
    - 算法註冊和管理
    - 環境配置和管理
    - 協調器配置和監控
    - 性能分析和 A/B 測試
    - RL 算法訓練和管理
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化生態系統管理器

        Args:
            config_path: 配置文件路徑
        """
        self.config_path = config_path or "algorithm_ecosystem_config.yml"
        self.config = {}

        # 核心組件
        self.algorithm_registry = AlgorithmRegistry()
        self.environment_manager = None
        self.orchestrator = None
        self.analysis_engine = None
        self.training_pipeline = None

        # 狀態管理
        self.is_initialized = False
        self.startup_time = None

        logger.info("算法生態系統管理器創建完成")

    async def initialize(self) -> bool:
        """初始化生態系統

        Returns:
            bool: 初始化是否成功
        """
        if self.is_initialized:
            logger.info("生態系統已經初始化")
            return True

        try:
            self.startup_time = datetime.now()
            logger.info("🚀 開始初始化算法生態系統...")

            # 1. 載入配置
            success = await self._load_configuration()
            if not success:
                logger.error("配置載入失敗")
                return False

            # 2. 初始化核心組件
            success = await self._initialize_core_components()
            if not success:
                logger.error("核心組件初始化失敗")
                return False

            # 3. 註冊算法
            success = await self._register_algorithms()
            if not success:
                logger.error("算法註冊失敗")
                return False

            # 4. 配置協調器
            success = await self._configure_orchestrator()
            if not success:
                logger.error("協調器配置失敗")
                return False

            # 5. 設置分析引擎
            success = await self._setup_analysis_engine()
            if not success:
                logger.error("分析引擎設置失敗")
                return False

            self.is_initialized = True
            initialization_time = (datetime.now() - self.startup_time).total_seconds()

            logger.info(f"✅ 算法生態系統初始化完成，耗時 {initialization_time:.2f} 秒")

            # 生成初始化報告
            await self._generate_initialization_report()

            return True

        except Exception as e:
            logger.error(f"生態系統初始化失敗: {e}")
            return False

    async def _load_configuration(self) -> bool:
        """載入配置文件"""
        try:
            if not Path(self.config_path).exists():
                logger.warning(f"配置文件不存在: {self.config_path}，使用默認配置")
                self.config = self._get_default_config()
                return True

            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

            logger.info(f"配置文件載入成功: {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"載入配置文件失敗: {e}")
            return False

    async def _initialize_core_components(self) -> bool:
        """初始化核心組件"""
        try:
            # 初始化環境管理器
            env_config = self.config.get("environment", {})
            self.environment_manager = EnvironmentManager()
            await self.environment_manager.initialize()  # 傳遞 None，使用默認配置

            # 初始化算法註冊中心
            await self.algorithm_registry.initialize()

            # 初始化協調器
            orchestrator_config = self._create_orchestrator_config()
            self.orchestrator = HandoverOrchestrator(
                self.algorithm_registry, self.environment_manager, orchestrator_config
            )
            await self.orchestrator.initialize()

            logger.info("核心組件初始化完成")
            return True

        except Exception as e:
            logger.error(f"核心組件初始化失敗: {e}")
            return False

    async def _register_algorithms(self) -> bool:
        """註冊所有算法"""
        try:
            algorithms_config = self.config.get("handover_algorithms", {})

            registered_count = 0
            failed_count = 0

            for category, algorithms in algorithms_config.items():
                logger.info(f"註冊 {category} 算法...")

                for algorithm_name, algorithm_config in algorithms.items():
                    if not algorithm_config.get("enabled", False):
                        logger.info(f"跳過未啟用的算法: {algorithm_name}")
                        continue

                    try:
                        success = await self._register_single_algorithm(
                            algorithm_name, algorithm_config
                        )
                        if success:
                            registered_count += 1
                            logger.info(f"✅ 算法 '{algorithm_name}' 註冊成功")
                        else:
                            failed_count += 1
                            logger.warning(f"❌ 算法 '{algorithm_name}' 註冊失敗")

                    except Exception as e:
                        failed_count += 1
                        logger.error(f"算法 '{algorithm_name}' 註冊異常: {e}")

            logger.info(f"算法註冊完成: {registered_count} 成功, {failed_count} 失敗")

            # 修改邏輯：即使沒有算法也允許繼續初始化（開發模式下）
            if registered_count == 0:
                logger.warning("⚠️ 沒有成功註冊任何算法，但允許系統在基本模式下運行")

            return True  # 總是返回 True，允許系統在沒有算法的情況下運行

        except Exception as e:
            logger.error(f"算法註冊過程失敗: {e}")
            return False

    async def _register_single_algorithm(
        self, name: str, config: Dict[str, Any]
    ) -> bool:
        """註冊單個算法"""
        try:
            algorithm_class_path = config.get("class")
            if not algorithm_class_path:
                logger.error(f"算法 '{name}' 缺少 class 配置")
                return False

            # 動態導入算法類
            module_path, class_name = algorithm_class_path.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            algorithm_class = getattr(module, class_name)

            # 創建算法實例
            algorithm_config = {
                "priority": config.get("priority", 10),
                "description": config.get("description", ""),
                "author": config.get("author", ""),
                "supported_scenarios": config.get("supported_scenarios", []),
                **config.get("config", {}),
                **config.get("training_config", {}),
                **config.get("inference_config", {}),
            }

            algorithm_instance = algorithm_class(name, algorithm_config)

            # 註冊算法
            return await self.algorithm_registry.register_algorithm(
                name, algorithm_instance, algorithm_config
            )

        except Exception as e:
            logger.error(f"註冊算法 '{name}' 失敗: {e}")
            return False

    async def _configure_orchestrator(self) -> bool:
        """配置協調器"""
        try:
            orchestrator_config = self.config.get("orchestrator", {})

            # 設置默認算法
            default_algorithm = orchestrator_config.get("default_algorithm")
            if default_algorithm and self.algorithm_registry.is_registered(
                default_algorithm
            ):
                logger.info(f"設置默認算法: {default_algorithm}")

            # 如果啟用了 A/B 測試
            experiments_config = self.config.get("experiments", {})
            if experiments_config.get("enable_ab_testing", False):
                await self._setup_ab_testing(
                    experiments_config.get("ab_test_config", {})
                )

            logger.info("協調器配置完成")
            return True

        except Exception as e:
            logger.error(f"協調器配置失敗: {e}")
            return False

    async def _setup_analysis_engine(self) -> bool:
        """設置分析引擎"""
        try:
            analysis_config = self.config.get("monitoring", {})

            self.analysis_engine = PerformanceAnalysisEngine(analysis_config)
            # 嘗試設置組件，如果方法不存在就跳過
            if hasattr(self.analysis_engine, "set_components"):
                self.analysis_engine.set_components(
                    self.algorithm_registry, self.orchestrator
                )

            logger.info("分析引擎設置完成")
            return True

        except Exception as e:
            logger.error(f"分析引擎設置失敗: {e}")
            return False

    async def _setup_ab_testing(self, ab_config: Dict[str, Any]) -> None:
        """設置 A/B 測試"""
        try:
            traffic_split = ab_config.get("traffic_split", {})
            if traffic_split:
                test_id = f"auto_ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                if self.analysis_engine:
                    success = self.analysis_engine.start_ab_test(
                        test_id=test_id,
                        algorithms=list(traffic_split.keys()),
                        traffic_split=traffic_split,
                    )

                    if success:
                        logger.info(f"A/B 測試啟動成功: {test_id}")
                    else:
                        logger.error("A/B 測試啟動失敗")

        except Exception as e:
            logger.error(f"A/B 測試設置失敗: {e}")

    def _create_orchestrator_config(self) -> OrchestratorConfig:
        """創建協調器配置"""
        from .orchestrator import OrchestratorMode, DecisionStrategy

        orchestrator_config = self.config.get("orchestrator", {})

        mode_mapping = {
            "single_algorithm": OrchestratorMode.SINGLE_ALGORITHM,
            "load_balancing": OrchestratorMode.LOAD_BALANCING,
            "ab_testing": OrchestratorMode.A_B_TESTING,
            "ensemble": OrchestratorMode.ENSEMBLE,
            "adaptive": OrchestratorMode.ADAPTIVE,
        }

        strategy_mapping = {
            "priority_based": DecisionStrategy.PRIORITY_BASED,
            "performance_based": DecisionStrategy.PERFORMANCE_BASED,
            "round_robin": DecisionStrategy.ROUND_ROBIN,
            "weighted_random": DecisionStrategy.WEIGHTED_RANDOM,
            "confidence_based": DecisionStrategy.CONFIDENCE_BASED,
        }

        return OrchestratorConfig(
            mode=mode_mapping.get(
                orchestrator_config.get("mode", "single_algorithm"),
                OrchestratorMode.SINGLE_ALGORITHM,
            ),
            decision_strategy=strategy_mapping.get(
                orchestrator_config.get("decision_strategy", "priority_based"),
                DecisionStrategy.PRIORITY_BASED,
            ),
            default_algorithm=orchestrator_config.get("default_algorithm"),
            fallback_algorithm=orchestrator_config.get("fallback_algorithm"),
            timeout_seconds=orchestrator_config.get("timeout_seconds", 5.0),
            max_concurrent_requests=orchestrator_config.get(
                "max_concurrent_requests", 100
            ),
            enable_caching=orchestrator_config.get("enable_caching", True),
            cache_ttl_seconds=orchestrator_config.get("cache_ttl_seconds", 60),
            enable_monitoring=orchestrator_config.get("enable_monitoring", True),
            monitoring_window_minutes=orchestrator_config.get(
                "monitoring_window_minutes", 10
            ),
            ab_test_config=self.config.get("experiments", {}).get("ab_test_config"),
            ensemble_config=self.config.get("experiments", {}).get("ensemble_config"),
        )

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "handover_algorithms": {"traditional": {}, "reinforcement_learning": {}},
            "environment": {
                "gymnasium": {
                    "env_name": "LEOSatelliteHandoverEnv-v1",
                    "max_episode_steps": 1000,
                }
            },
            "orchestrator": {
                "mode": "single_algorithm",
                "decision_strategy": "priority_based",
                "timeout_seconds": 5.0,
                "max_concurrent_requests": 100,
                "enable_caching": True,
                "enable_monitoring": True,
            },
            "experiments": {"enable_ab_testing": False, "enable_ensemble": False},
            "monitoring": {
                "enable_metrics_collection": True,
                "metrics_retention_hours": 24,
            },
        }

    async def _generate_initialization_report(self) -> None:
        """生成初始化報告"""
        try:
            registered_algorithms = self.algorithm_registry.get_registered_algorithms()

            report = {
                "initialization_time": self.startup_time.isoformat(),
                "total_initialization_duration_seconds": (
                    datetime.now() - self.startup_time
                ).total_seconds(),
                "registered_algorithms": list(registered_algorithms.keys()),
                "orchestrator_mode": self.orchestrator.config.mode.value,
                "decision_strategy": self.orchestrator.config.decision_strategy.value,
                "analysis_engine_enabled": self.analysis_engine is not None,
                "training_pipeline_available": RLTrainingPipeline is not None,
                "components_status": {
                    "algorithm_registry": self.algorithm_registry._initialized,
                    "environment_manager": self.environment_manager._initialized,
                    "orchestrator": self.orchestrator._initialized,
                },
            }

            logger.info("📊 生態系統初始化報告:")
            logger.info(f"  - 已註冊算法: {len(registered_algorithms)} 個")
            logger.info(f"  - 協調器模式: {report['orchestrator_mode']}")
            logger.info(f"  - 決策策略: {report['decision_strategy']}")
            logger.info(
                f"  - 分析引擎: {'啟用' if report['analysis_engine_enabled'] else '未啟用'}"
            )
            logger.info(
                f"  - 初始化耗時: {report['total_initialization_duration_seconds']:.2f} 秒"
            )

        except Exception as e:
            logger.error(f"生成初始化報告失敗: {e}")

    # 主要 API 方法
    async def predict_handover(
        self, context: HandoverContext, algorithm_name: Optional[str] = None
    ) -> HandoverDecision:
        """執行換手預測

        Args:
            context: 換手上下文
            algorithm_name: 指定算法名稱（可選）

        Returns:
            HandoverDecision: 換手決策
        """
        if not self.is_initialized:
            await self.initialize()

        decision = await self.orchestrator.predict_handover(context, algorithm_name)

        # 記錄到分析引擎
        if self.analysis_engine:
            self.analysis_engine.record_decision_metrics(
                decision.algorithm_name, context, decision
            )

        return decision

    def get_registered_algorithms(self) -> List[str]:
        """獲取已註冊的算法列表"""
        if not self.is_initialized:
            return []

        return list(self.algorithm_registry.get_registered_algorithms().keys())

    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        return {
            "status": "running",
            "initialization_time": (
                self.startup_time.isoformat() if self.startup_time else None
            ),
            "uptime_seconds": (
                (datetime.now() - self.startup_time).total_seconds()
                if self.startup_time
                else 0
            ),
            "registered_algorithms": self.get_registered_algorithms(),
            "orchestrator_stats": self.orchestrator.get_orchestrator_stats(),
            "analysis_engine_available": self.analysis_engine is not None,
            "active_ab_tests": (
                self.analysis_engine.get_active_ab_tests()
                if self.analysis_engine
                else {}
            ),
        }

    async def start_ab_test(
        self, test_id: str, algorithms: List[str], traffic_split: Dict[str, float]
    ) -> bool:
        """啟動 A/B 測試"""
        if not self.analysis_engine:
            logger.error("分析引擎未啟用，無法進行 A/B 測試")
            return False

        return self.analysis_engine.start_ab_test(test_id, algorithms, traffic_split)

    async def stop_ab_test(self, test_id: str):
        """停止 A/B 測試"""
        if not self.analysis_engine:
            logger.error("分析引擎未啟用")
            return None

        return self.analysis_engine.stop_ab_test(test_id)

    def generate_performance_report(
        self,
        algorithms: Optional[List[str]] = None,
        time_window: Optional[timedelta] = None,
    ) -> Dict[str, Any]:
        """生成性能報告"""
        if not self.analysis_engine:
            return {"error": "Analysis engine not available"}

        return self.analysis_engine.generate_performance_report(algorithms, time_window)

    async def train_rl_algorithm(
        self, algorithm_name: str, episodes: int = 1000
    ) -> Dict[str, Any]:
        """訓練強化學習算法"""
        if not self.training_pipeline:
            self.training_pipeline = RLTrainingPipeline(self.config_path)

        return await self.training_pipeline.train_algorithm(algorithm_name, episodes)

    async def cleanup(self) -> None:
        """清理資源"""
        logger.info("開始清理算法生態系統...")

        if self.orchestrator:
            await self.orchestrator.cleanup()

        if self.algorithm_registry:
            await self.algorithm_registry.cleanup()

        if self.environment_manager:
            self.environment_manager.cleanup()

        if self.training_pipeline:
            self.training_pipeline.cleanup()

        self.is_initialized = False
        logger.info("算法生態系統清理完成")
