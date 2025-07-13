#!/usr/bin/env python3
"""
🧪 Phase 1.2 完整功能測試
測試新的資料庫倉庫工廠、配置管理和系統初始化
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from rl_system.core.system_initializer import RLSystemInitializer, initialize_rl_system
from rl_system.core.repository_factory import RepositoryFactory, RepositoryType
from rl_system.core.service_locator import ServiceLocator
from rl_system.interfaces.data_repository import (
    ExperimentSession, TrainingEpisode, ModelVersion, 
    PerformanceMetric, MetricType, ScenarioType
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase12Tester:
    """Phase 1.2 完整測試器"""
    
    def __init__(self):
        self.initializer: RLSystemInitializer = None
        self.test_results: Dict[str, Any] = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有測試"""
        logger.info("🚀 開始 Phase 1.2 完整功能測試")
        
        try:
            # 測試系統初始化
            await self._test_system_initialization()
            
            # 測試倉庫工廠
            await self._test_repository_factory()
            
            # 測試服務定位器
            await self._test_service_locator()
            
            # 測試數據操作
            await self._test_data_operations()
            
            # 測試配置管理
            await self._test_config_management()
            
            # 生成測試報告
            await self._generate_test_report()
            
        except Exception as e:
            logger.error(f"測試執行失敗: {e}")
            self._record_test("overall_execution", False, f"Exception: {e}")
        
        finally:
            # 清理資源
            await self._cleanup()
        
        return self.test_results
    
    async def _test_system_initialization(self) -> None:
        """測試系統初始化"""
        logger.info("🔧 測試系統初始化...")
        
        try:
            # 測試初始化器創建
            self.initializer = RLSystemInitializer()
            self._record_test("initializer_creation", True, "成功創建初始化器")
            
            # 測試系統初始化
            init_result = await self.initializer.initialize()
            
            if init_result["status"] == "success":
                self._record_test("system_initialization", True, "系統初始化成功")
                logger.info(f"初始化結果: {init_result}")
            else:
                self._record_test("system_initialization", False, f"初始化失敗: {init_result}")
            
            # 測試系統資訊獲取
            system_info = self.initializer.get_system_info()
            self._record_test("system_info", True, f"獲取系統資訊: {len(system_info)} 項")
            
        except Exception as e:
            self._record_test("system_initialization", False, f"Exception: {e}")
    
    async def _test_repository_factory(self) -> None:
        """測試倉庫工廠"""
        logger.info("🏭 測試倉庫工廠...")
        
        try:
            # 測試 Mock 倉庫創建
            mock_repo = await RepositoryFactory.create_repository(
                repository_type=RepositoryType.MOCK,
                use_singleton=False
            )
            self._record_test("mock_repository_creation", True, "成功創建 Mock 倉庫")
            
            # 測試倉庫健康檢查
            health = await mock_repo.get_database_health()
            if health["status"] == "healthy":
                self._record_test("repository_health_check", True, "倉庫健康檢查通過")
            else:
                self._record_test("repository_health_check", False, f"健康檢查失敗: {health}")
            
            # 測試預設倉庫獲取
            default_repo = await RepositoryFactory.get_default_repository()
            self._record_test("default_repository", True, "成功獲取預設倉庫")
            
            # 測試工廠資訊
            factory_info = RepositoryFactory.get_instance_info()
            self._record_test("factory_info", True, f"工廠資訊: {factory_info['total_instances']} 個實例")
            
        except Exception as e:
            self._record_test("repository_factory", False, f"Exception: {e}")
    
    async def _test_service_locator(self) -> None:
        """測試服務定位器"""
        logger.info("📍 測試服務定位器...")
        
        try:
            # 測試服務定位器獲取
            service_locator = self.initializer.get_service_locator()
            self._record_test("service_locator_access", True, "成功獲取服務定位器")
            
            # 測試數據倉庫解析
            repository = ServiceLocator.get_data_repository()
            self._record_test("repository_resolution", True, f"成功解析倉庫: {type(repository).__name__}")
            
            # 測試健康狀態檢查
            health_status = ServiceLocator.get_health_status()
            self._record_test("service_locator_health", True, f"健康狀態: {health_status['status']}")
            
            # 測試服務驗證
            validation_result = ServiceLocator.validate_services()
            if validation_result["is_valid"]:
                self._record_test("service_validation", True, "服務配置驗證通過")
            else:
                self._record_test("service_validation", False, f"驗證失敗: {validation_result['errors']}")
            
        except Exception as e:
            self._record_test("service_locator", False, f"Exception: {e}")
    
    async def _test_data_operations(self) -> None:
        """測試數據操作"""
        logger.info("💾 測試數據操作...")
        
        try:
            repository = ServiceLocator.get_data_repository()
            
            # 測試實驗會話創建
            session = ExperimentSession(
                experiment_name="Phase12_Test",
                algorithm_type="DQN",
                scenario_type=ScenarioType.URBAN,
                researcher_id="test_user",
                hyperparameters={"learning_rate": 0.001},
                environment_config={"satellites": 100}
            )
            
            session_id = await repository.create_experiment_session(session)
            if session_id > 0:
                self._record_test("experiment_session_creation", True, f"創建會話 ID: {session_id}")
            else:
                self._record_test("experiment_session_creation", False, "會話創建失敗")
            
            # 測試訓練回合創建
            episode = TrainingEpisode(
                session_id=session_id,
                episode_number=1,
                total_reward=100.5,
                success_rate=0.95,
                handover_latency_ms=25.0,
                decision_confidence=0.88,
                candidate_satellites=["sat1", "sat2"],
                decision_reasoning={"factors": ["signal_strength", "latency"]},
                algorithm_type="DQN",
                scenario_type="urban",
                training_time_ms=500,
                convergence_indicator=0.85
            )
            
            episode_id = await repository.create_training_episode(episode)
            if episode_id > 0:
                self._record_test("training_episode_creation", True, f"創建回合 ID: {episode_id}")
            else:
                self._record_test("training_episode_creation", False, "回合創建失敗")
            
            # 測試性能指標存儲
            metric = PerformanceMetric(
                session_id=session_id,
                timestamp=datetime.now(),
                algorithm_type="DQN",
                metric_type=MetricType.REWARD,
                metric_value=100.5,
                episode_number=1,
                scenario_type="urban",
                additional_data={"test": True}
            )
            
            metric_stored = await repository.store_performance_metric(metric)
            self._record_test("performance_metric_storage", metric_stored, "性能指標存儲")
            
            # 測試模型版本創建
            model = ModelVersion(
                algorithm_type="DQN",
                version_number="1.0.0",
                model_path="/models/dqn_v1.pth",
                model_size_bytes=1024000,
                training_episodes=1000,
                validation_score=0.92,
                hyperparameters={"learning_rate": 0.001},
                training_duration_seconds=3600,
                created_by="test_user",
                notes="Phase 1.2 test model"
            )
            
            model_id = await repository.create_model_version(model)
            if model_id > 0:
                self._record_test("model_version_creation", True, f"創建模型 ID: {model_id}")
            else:
                self._record_test("model_version_creation", False, "模型創建失敗")
            
            # 測試統計分析
            stats = await repository.get_algorithm_statistics("DQN", ScenarioType.URBAN)
            self._record_test("algorithm_statistics", True, f"統計數據: {len(stats)} 項指標")
            
        except Exception as e:
            self._record_test("data_operations", False, f"Exception: {e}")
    
    async def _test_config_management(self) -> None:
        """測試配置管理"""
        logger.info("⚙️ 測試配置管理...")
        
        try:
            config_manager = self.initializer.get_config_manager()
            
            # 測試可用算法獲取
            available_algorithms = config_manager.get_available_algorithms()
            self._record_test("available_algorithms", True, f"可用算法: {available_algorithms}")
            
            # 測試算法配置獲取
            if available_algorithms:
                algo_name = available_algorithms[0]
                algo_config = config_manager.get_algorithm_config(algo_name)
                if algo_config:
                    self._record_test("algorithm_config", True, f"獲取 {algo_name} 配置")
                else:
                    self._record_test("algorithm_config", False, f"無法獲取 {algo_name} 配置")
            
            # 測試系統配置
            system_config = config_manager.get_system_config()
            if system_config:
                self._record_test("system_config", True, f"系統配置環境: {system_config.environment}")
            else:
                self._record_test("system_config", False, "無法獲取系統配置")
            
            # 測試管理器統計
            manager_stats = config_manager.get_manager_stats()
            self._record_test("config_manager_stats", True, f"管理器統計: {manager_stats}")
            
        except Exception as e:
            self._record_test("config_management", False, f"Exception: {e}")
    
    async def _generate_test_report(self) -> None:
        """生成測試報告"""
        logger.info("📊 生成測試報告...")
        
        try:
            total = self.test_results["total_tests"]
            passed = self.test_results["passed_tests"]
            failed = self.test_results["failed_tests"]
            success_rate = (passed / total * 100) if total > 0 else 0
            
            print("\n" + "="*60)
            print("🧪 Phase 1.2 完整功能測試報告")
            print("="*60)
            print(f"總測試數量: {total}")
            print(f"通過測試: {passed}")
            print(f"失敗測試: {failed}")
            print(f"成功率: {success_rate:.1f}%")
            print("-"*60)
            
            for test_detail in self.test_results["test_details"]:
                status_icon = "✅" if test_detail["passed"] else "❌"
                print(f"{status_icon} {test_detail['test_name']}: {test_detail['message']}")
            
            print("="*60)
            
            if success_rate >= 80:
                print("🎉 Phase 1.2 測試整體通過！")
            else:
                print("⚠️ Phase 1.2 測試需要改進")
            
        except Exception as e:
            logger.error(f"生成測試報告失敗: {e}")
    
    async def _cleanup(self) -> None:
        """清理測試資源"""
        logger.info("🧹 清理測試資源...")
        
        try:
            if self.initializer:
                await self.initializer.shutdown()
            
            # 清理倉庫實例
            await RepositoryFactory.shutdown_all()
            
            logger.info("資源清理完成")
            
        except Exception as e:
            logger.error(f"資源清理失敗: {e}")
    
    def _record_test(self, test_name: str, passed: bool, message: str = "") -> None:
        """記錄測試結果"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed_tests"] += 1
        else:
            self.test_results["failed_tests"] += 1
        
        self.test_results["test_details"].append({
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")


async def main():
    """主測試函數"""
    print("🧠 LEO衛星換手決策RL系統 - Phase 1.2 完整功能測試")
    print("測試範圍: 倉庫工廠、配置管理、服務定位器、數據操作")
    print("-"*60)
    
    # 設置測試環境
    os.environ["MOCK_DATA_ENABLED"] = "true"  # 使用 Mock 數據庫進行測試
    os.environ["ENVIRONMENT"] = "test"
    
    tester = Phase12Tester()
    results = await tester.run_all_tests()
    
    # 返回適當的退出碼
    if results["failed_tests"] == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())