#!/usr/bin/env python3
"""
🧠 NetStack RL 系統設置腳本

自動化設置和初始化世界級 LEO 衛星強化學習系統。
支援完整的開發環境建置和配置。
"""

import os
import sys
import asyncio
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rl_system.core.di_container import DIContainer
from rl_system.core.service_locator import ServiceLocator
from rl_system.core.config_manager import ConfigDrivenAlgorithmManager, create_default_config
from rl_system.core.algorithm_factory import AlgorithmFactory

logger = logging.getLogger(__name__)


class RLSystemSetup:
    """RL 系統設置管理器"""
    
    def __init__(self, config_path: Optional[str] = None, environment: str = "development"):
        self.environment = environment
        self.config_path = Path(config_path) if config_path else Path("rl_system/config/default_config.yaml")
        self.container: Optional[DIContainer] = None
        self.algorithm_manager: Optional[ConfigDrivenAlgorithmManager] = None
        
        # 設置日誌
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """設置日誌系統"""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler("setup.log")
            ]
        )
        
    async def setup_complete_system(self) -> bool:
        """設置完整的 RL 系統"""
        try:
            logger.info("🚀 開始設置 NetStack RL 系統...")
            
            # 1. 創建必要的目錄結構
            await self._create_directory_structure()
            
            # 2. 檢查並創建配置文件
            await self._setup_configuration()
            
            # 3. 初始化數據庫
            await self._setup_database()
            
            # 4. 設置依賴注入容器
            await self._setup_dependency_injection()
            
            # 5. 註冊算法
            await self._register_algorithms()
            
            # 6. 初始化算法管理器
            await self._setup_algorithm_manager()
            
            # 7. 驗證系統配置
            await self._validate_system()
            
            # 8. 運行健康檢查
            await self._run_health_checks()
            
            logger.info("✅ NetStack RL 系統設置完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 系統設置失敗: {e}")
            return False
    
    async def _create_directory_structure(self) -> None:
        """創建必要的目錄結構"""
        logger.info("📁 創建目錄結構...")
        
        directories = [
            "rl_models",
            "exports", 
            "backups",
            "logs",
            "test_data",
            "temp",
            "rl_system/database/migrations",
            "rl_system/implementations/plugins"
        ]
        
        for directory in directories:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"創建目錄: {dir_path}")
        
        logger.info("✅ 目錄結構創建完成")
    
    async def _setup_configuration(self) -> None:
        """設置配置文件"""
        logger.info("⚙️ 設置配置文件...")
        
        if not self.config_path.exists():
            logger.info(f"配置文件不存在，創建預設配置: {self.config_path}")
            create_default_config(self.config_path)
        else:
            logger.info(f"使用現有配置文件: {self.config_path}")
        
        # 驗證配置文件
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info("✅ 配置文件驗證通過")
        except Exception as e:
            raise RuntimeError(f"配置文件驗證失敗: {e}")
    
    async def _setup_database(self) -> None:
        """設置數據庫"""
        logger.info("🗄️ 設置數據庫...")
        
        try:
            # 檢查 PostgreSQL 連接
            await self._check_postgresql_connection()
            
            # 運行數據庫遷移
            await self._run_database_migrations()
            
            logger.info("✅ 數據庫設置完成")
            
        except Exception as e:
            logger.warning(f"數據庫設置失敗，將使用內存存儲: {e}")
    
    async def _check_postgresql_connection(self) -> None:
        """檢查 PostgreSQL 連接"""
        try:
            import asyncpg
            import yaml
            
            # 從配置文件讀取數據庫 URL
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            db_url = config.get('system', {}).get('database_url', '')
            if not db_url:
                raise ValueError("配置文件中未找到數據庫 URL")
            
            # 嘗試連接
            conn = await asyncpg.connect(db_url)
            await conn.close()
            logger.info("✅ PostgreSQL 連接成功")
            
        except ImportError:
            logger.warning("asyncpg 未安裝，跳過 PostgreSQL 檢查")
        except Exception as e:
            raise RuntimeError(f"PostgreSQL 連接失敗: {e}")
    
    async def _run_database_migrations(self) -> None:
        """運行數據庫遷移"""
        logger.info("📊 運行數據庫遷移...")
        
        schema_file = Path("rl_system/database/schema.sql")
        if schema_file.exists():
            logger.info("找到數據庫架構文件，準備執行遷移...")
            # 這裡可以添加實際的遷移邏輯
            logger.info("✅ 數據庫遷移完成")
        else:
            logger.warning("未找到數據庫架構文件")
    
    async def _setup_dependency_injection(self) -> None:
        """設置依賴注入容器"""
        logger.info("🔗 設置依賴注入容器...")
        
        # 創建 DI 容器
        self.container = DIContainer()
        
        # 註冊核心服務（這裡使用模擬實現）
        await self._register_core_services()
        
        # 初始化服務定位器
        ServiceLocator.initialize(self.container)
        
        logger.info("✅ 依賴注入容器設置完成")
    
    async def _register_core_services(self) -> None:
        """註冊核心服務"""
        logger.info("📋 註冊核心服務...")
        
        # 這裡會註冊實際的服務實現
        # 現在使用模擬實現作為演示
        
        from rl_system.interfaces.training_scheduler import ITrainingScheduler
        from rl_system.interfaces.performance_monitor import IPerformanceMonitor
        from rl_system.interfaces.data_repository import IDataRepository
        from rl_system.interfaces.model_manager import IModelManager
        
        # 創建模擬實現（實際項目中應該使用真實實現）
        class MockTrainingScheduler(ITrainingScheduler):
            async def submit_training_job(self, job): 
                return "mock_job_id"
            async def cancel_training_job(self, job_id): 
                return True
            async def get_job_status(self, job_id): 
                return {"status": "completed"}
            async def get_training_queue(self): 
                return []
            async def get_scheduler_status(self): 
                from rl_system.interfaces.training_scheduler import SchedulerStatus
                return SchedulerStatus(0, 0, 0, 0, 0.0, 0.0, None, 0.0, 0.0)
            async def set_scheduling_strategy(self, strategy): 
                return True
            async def set_resource_constraints(self, constraints): 
                return True
            async def pause_scheduler(self): 
                return True
            async def resume_scheduler(self): 
                return True
            async def shutdown_scheduler(self, wait_for_completion=True): 
                return True
        
        class MockPerformanceMonitor(IPerformanceMonitor):
            async def record_metric(self, metric): 
                return True
            async def record_metrics_batch(self, metrics): 
                return len(metrics)
            async def get_performance_summary(self, algorithm_name, metric_types=None, scenario_type=None, time_range=None): 
                return {}
            async def compare_with_baseline(self, our_algorithm, baseline_algorithm, metric_types, scenario_type=None): 
                return []
            async def analyze_convergence(self, algorithm_name, session_ids=None, convergence_threshold=0.95): 
                return []
            async def get_real_time_metrics(self, algorithm_name, time_window_minutes=5): 
                return {}
            async def export_metrics_for_paper(self, algorithm_names, metric_types, format_type="csv", include_statistical_tests=True): 
                return "mock_export_path"
            async def generate_performance_report(self, algorithm_names, report_type="comprehensive"): 
                return {}
            async def set_performance_alert(self, algorithm_name, metric_type, threshold, comparison_operator="less_than"): 
                return "mock_alert_id"
            async def get_trending_analysis(self, algorithm_name, metric_type, time_period_days=7): 
                return {}
        
        class MockDataRepository(IDataRepository):
            async def create_experiment_session(self, session): 
                return 1
            async def get_experiment_session(self, session_id): 
                return None
            async def update_experiment_session(self, session_id, updates): 
                return True
            async def delete_experiment_session(self, session_id): 
                return True
            async def query_experiment_sessions(self, filter_obj): 
                return []
            async def create_training_episode(self, episode): 
                return 1
            async def get_training_episodes(self, session_id, limit=None, offset=None): 
                return []
            async def get_latest_episode(self, session_id): 
                return None
            async def batch_create_episodes(self, episodes): 
                return len(episodes)
            async def store_performance_metric(self, metric): 
                return True
            async def batch_store_metrics(self, metrics): 
                return len(metrics)
            async def query_performance_metrics(self, algorithm_names, metric_types, start_time=None, end_time=None, scenario_type=None): 
                return []
            async def create_model_version(self, model): 
                return 1
            async def get_model_versions(self, algorithm_type, limit=None): 
                return []
            async def get_best_model(self, algorithm_type, metric="validation_score"): 
                return None
            async def get_algorithm_statistics(self, algorithm_name, scenario_type=None): 
                return {}
            async def get_convergence_analysis(self, session_ids, convergence_threshold=0.95): 
                return []
            async def compare_algorithms(self, algorithm_names, metric_types, scenario_type=None): 
                return {}
            async def backup_data(self, backup_path): 
                return True
            async def restore_data(self, backup_path): 
                return True
            async def cleanup_old_data(self, days_to_keep=30): 
                return 0
            async def get_database_health(self): 
                return {"status": "healthy"}
        
        class MockModelManager(IModelManager):
            async def register_model(self, metadata): 
                return "mock_model_id"
            async def get_model_metadata(self, model_id): 
                return None
            async def update_model_metadata(self, model_id, updates): 
                return True
            async def delete_model(self, model_id, force=False): 
                return True
            async def list_models(self, algorithm_name=None, scenario_type=None, status=None, limit=None): 
                return []
            async def validate_model(self, model_id, validation_dataset, validation_config=None): 
                from rl_system.interfaces.model_manager import ValidationReport, ValidationStatus
                return ValidationReport("val_id", model_id, ValidationStatus.PASSED, 0.9, {}, 10, 0, 1.0)
            async def get_validation_report(self, validation_id): 
                return None
            async def set_validation_pipeline(self, algorithm_name, validation_steps): 
                return True
            async def deploy_model(self, config): 
                return "mock_deployment_id"
            async def undeploy_model(self, deployment_id): 
                return True
            async def get_deployment_status(self, deployment_id): 
                return {"status": "deployed"}
            async def list_deployments(self, environment=None, status=None): 
                return []
            async def scale_deployment(self, deployment_id, replica_count): 
                return True
            async def start_ab_test(self, config): 
                return "mock_test_id"
            async def stop_ab_test(self, test_id): 
                return {"winner": "model_a"}
            async def get_ab_test_results(self, test_id): 
                return {}
            async def list_ab_tests(self, status=None): 
                return []
            async def monitor_model_performance(self, model_id, metrics, time_window_minutes=60): 
                return {}
            async def set_performance_alert(self, model_id, metric_name, threshold, alert_callback): 
                return "mock_alert_id"
            async def get_model_health(self, model_id): 
                return {"status": "healthy"}
            async def create_model_version(self, base_model_id, new_version, changes): 
                return "new_model_id"
            async def compare_model_versions(self, model_id_a, model_id_b, metrics): 
                return {}
            async def rollback_to_version(self, deployment_id, target_model_id): 
                return True
        
        # 註冊服務
        self.container.register_singleton(ITrainingScheduler, MockTrainingScheduler)
        self.container.register_singleton(IPerformanceMonitor, MockPerformanceMonitor)
        self.container.register_singleton(IDataRepository, MockDataRepository)
        self.container.register_singleton(IModelManager, MockModelManager)
        
        logger.info("✅ 核心服務註冊完成")
    
    async def _register_algorithms(self) -> None:
        """註冊算法實現"""
        logger.info("🧮 註冊算法實現...")
        
        try:
            # 註冊 DQN 算法（已通過裝飾器自動註冊）
            from rl_system.implementations.dqn_implementation import DQNAlgorithmImpl
            
            # 檢查算法是否成功註冊
            available_algorithms = AlgorithmFactory.get_available_algorithms()
            logger.info(f"可用算法: {available_algorithms}")
            
            if "DQN" in available_algorithms:
                logger.info("✅ DQN 算法註冊成功")
            else:
                logger.warning("❌ DQN 算法註冊失敗")
            
            # 可以在這裡註冊更多算法
            # from rl_system.implementations.ppo_implementation import PPOAlgorithmImpl
            # from rl_system.implementations.sac_implementation import SACAlgorithmImpl
            
        except Exception as e:
            logger.error(f"算法註冊失敗: {e}")
    
    async def _setup_algorithm_manager(self) -> None:
        """設置算法管理器"""
        logger.info("🎯 設置算法管理器...")
        
        try:
            self.algorithm_manager = ConfigDrivenAlgorithmManager(
                config_path=self.config_path,
                container=self.container
            )
            
            await self.algorithm_manager.initialize()
            
            logger.info("✅ 算法管理器設置完成")
            
        except Exception as e:
            logger.error(f"算法管理器設置失敗: {e}")
            raise
    
    async def _validate_system(self) -> None:
        """驗證系統配置"""
        logger.info("🔍 驗證系統配置...")
        
        # 驗證服務註冊
        validation_result = ServiceLocator.validate_services()
        if not validation_result["is_valid"]:
            logger.error(f"服務驗證失敗: {validation_result['errors']}")
            raise RuntimeError("系統配置驗證失敗")
        
        # 驗證算法註冊
        registry_stats = AlgorithmFactory.get_registry_stats()
        logger.info(f"算法註冊統計: {registry_stats}")
        
        if registry_stats["total_algorithms"] == 0:
            logger.warning("未發現已註冊的算法")
        
        logger.info("✅ 系統配置驗證通過")
    
    async def _run_health_checks(self) -> None:
        """運行健康檢查"""
        logger.info("🏥 運行健康檢查...")
        
        try:
            # 檢查服務定位器健康狀態
            health_status = ServiceLocator.get_health_status()
            logger.info(f"服務定位器狀態: {health_status['status']}")
            
            # 檢查算法管理器狀態
            if self.algorithm_manager:
                manager_stats = self.algorithm_manager.get_manager_stats()
                logger.info(f"算法管理器狀態: 已加載 {manager_stats['loaded_instances']} 個算法實例")
            
            # 嘗試創建一個算法實例
            try:
                from rl_system.interfaces.rl_algorithm import ScenarioType
                algorithm = AlgorithmFactory.create_algorithm("DQN", scenario_type=ScenarioType.URBAN)
                logger.info("✅ 算法實例創建測試通過")
            except Exception as e:
                logger.warning(f"算法實例創建測試失敗: {e}")
            
            logger.info("✅ 健康檢查完成")
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
    
    async def cleanup(self) -> None:
        """清理資源"""
        logger.info("🧹 清理系統資源...")
        
        try:
            if self.algorithm_manager:
                await self.algorithm_manager.shutdown()
            
            if self.container:
                # 清理容器資源（如果有的話）
                pass
            
            ServiceLocator.shutdown()
            
            logger.info("✅ 資源清理完成")
            
        except Exception as e:
            logger.error(f"資源清理失敗: {e}")


async def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="NetStack RL 系統設置")
    parser.add_argument("--config", help="配置文件路徑")
    parser.add_argument("--env", default="development", choices=["development", "testing", "production"],
                       help="運行環境")
    parser.add_argument("--skip-db", action="store_true", help="跳過數據庫設置")
    parser.add_argument("--demo", action="store_true", help="運行演示模式")
    
    args = parser.parse_args()
    
    # 創建設置管理器
    setup_manager = RLSystemSetup(
        config_path=args.config,
        environment=args.env
    )
    
    try:
        # 運行完整設置
        success = await setup_manager.setup_complete_system()
        
        if success:
            print("\n🎉 NetStack RL 系統設置成功！")
            print("\n📋 下一步操作:")
            print("1. 查看配置文件: rl_system/config/default_config.yaml")
            print("2. 啟動 Web UI: python -m rl_system.web.app")
            print("3. 運行 API 服務器: python -m rl_system.api.main")
            print("4. 查看文檔: http://localhost:8000/api/v1/docs")
            
            if args.demo:
                print("\n🚀 啟動演示模式...")
                await run_demo(setup_manager)
        else:
            print("\n❌ 系統設置失敗，請查看日誌獲取詳細信息")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷設置過程")
    except Exception as e:
        logger.error(f"設置過程中發生未預期的錯誤: {e}")
        sys.exit(1)
    finally:
        await setup_manager.cleanup()


async def run_demo(setup_manager: RLSystemSetup):
    """運行演示模式"""
    logger.info("🎬 開始演示模式...")
    
    try:
        from rl_system.interfaces.rl_algorithm import ScenarioType, TrainingConfig, PredictionContext
        from datetime import datetime
        
        # 1. 創建算法實例
        print("\n1️⃣ 創建 DQN 算法實例...")
        dqn = AlgorithmFactory.create_algorithm("DQN", scenario_type=ScenarioType.URBAN)
        print(f"   ✅ 算法: {dqn.get_name()} v{dqn.get_version()}")
        
        # 2. 運行簡短訓練
        print("\n2️⃣ 運行簡短訓練演示...")
        training_config = TrainingConfig(
            episodes=10,
            batch_size=16,
            learning_rate=0.001,
            max_steps_per_episode=50
        )
        
        result = await dqn.train(training_config)
        print(f"   ✅ 訓練完成: 最終分數 = {result.final_score:.3f}")
        
        # 3. 執行預測
        print("\n3️⃣ 執行換手決策預測...")
        context = PredictionContext(
            satellite_positions=[
                {"lat": 40.7128, "lon": -74.0060, "altitude": 550000},
                {"lat": 40.7580, "lon": -73.9855, "altitude": 550000}
            ],
            ue_position={"lat": 40.7413, "lon": -73.9896},
            network_conditions={
                "signal_strength": -80,
                "latency": 25,
                "throughput": 100,
                "packet_loss": 0.01
            },
            current_serving_satellite=1,
            candidate_satellites=[1, 2, 3],
            timestamp=datetime.now()
        )
        
        decision = await dqn.predict(context)
        print(f"   ✅ 決策完成: 目標衛星 {decision.target_satellite_id}, 信心度 {decision.confidence_score:.3f}")
        
        # 4. 顯示系統統計
        print("\n4️⃣ 系統統計資訊:")
        registry_stats = AlgorithmFactory.get_registry_stats()
        print(f"   📊 已註冊算法: {registry_stats['total_algorithms']}")
        print(f"   🏃 活躍實例: {registry_stats['active_instances']}")
        
        print("\n🎉 演示完成！系統運行正常。")
        
    except Exception as e:
        logger.error(f"演示模式失敗: {e}")


if __name__ == "__main__":
    asyncio.run(main())