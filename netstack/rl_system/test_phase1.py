#!/usr/bin/env python3
"""
LEO衛星換手決策RL系統 - Phase 1 集成測試
驗證 PostgreSQL 真實數據庫功能
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Phase1TestSuite:
    """Phase 1 功能測試套件"""
    
    def __init__(self):
        self.test_results = []
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://rl_user:rl_password@localhost:5432/rl_research_db"
        )
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        """記錄測試結果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✅ {test_name}: {message}")
        else:
            logger.error(f"❌ {test_name}: {message}")
    
    async def test_database_initialization(self) -> bool:
        """測試數據庫初始化"""
        logger.info("🧪 測試 1: 數據庫初始化")
        
        try:
            from database.init_database import RLDatabaseInitializer, get_config_from_env
            
            config = get_config_from_env()
            initializer = RLDatabaseInitializer(config)
            
            # 測試數據庫連接
            success = await initializer.test_connection()
            
            if success:
                self.log_test_result("數據庫初始化", True, "PostgreSQL 連接成功")
                return True
            else:
                # 嘗試初始化
                success = await initializer.full_initialization()
                self.log_test_result("數據庫初始化", success, 
                                   "數據庫初始化完成" if success else "數據庫初始化失敗")
                return success
                
        except Exception as e:
            self.log_test_result("數據庫初始化", False, f"錯誤: {e}")
            return False
    
    async def test_postgresql_repository(self) -> bool:
        """測試 PostgreSQL 儲存庫"""
        logger.info("🧪 測試 2: PostgreSQL 儲存庫")
        
        try:
            from implementations.postgresql_repository import PostgreSQLRepository
            
            repository = PostgreSQLRepository(self.database_url)
            
            # 初始化儲存庫
            if not await repository.initialize():
                self.log_test_result("PostgreSQL 儲存庫", False, "儲存庫初始化失敗")
                return False
            
            # 測試健康檢查
            health = await repository.health_check()
            if health.get("status") == "healthy":
                self.log_test_result("PostgreSQL 儲存庫", True, f"健康檢查通過: {health}")
                await repository.close()
                return True
            else:
                self.log_test_result("PostgreSQL 儲存庫", False, f"健康檢查失敗: {health}")
                await repository.close()
                return False
                
        except Exception as e:
            self.log_test_result("PostgreSQL 儲存庫", False, f"錯誤: {e}")
            return False
    
    async def test_experiment_session_management(self) -> bool:
        """測試實驗會話管理"""
        logger.info("🧪 測試 3: 實驗會話管理")
        
        try:
            from implementations.postgresql_repository import PostgreSQLRepository
            
            repository = PostgreSQLRepository(self.database_url)
            await repository.initialize()
            
            # 創建測試實驗會話
            session_id = await repository.create_experiment_session(
                experiment_name="Phase1_Test_Session",
                algorithm_type="DQN",
                scenario_type="test",
                hyperparameters={"learning_rate": 0.001, "batch_size": 32},
                environment_config={"env_name": "CartPole-v1"},
                researcher_id="test_researcher",
                research_notes="Phase 1 測試會話"
            )
            
            if session_id:
                # 獲取會話信息
                session_info = await repository.get_experiment_session(session_id)
                if session_info:
                    self.log_test_result("實驗會話管理", True, f"成功創建會話 ID: {session_id}")
                    
                    # 測試會話更新
                    update_success = await repository.update_experiment_session(
                        session_id=session_id,
                        session_status="completed",
                        total_episodes=100
                    )
                    
                    if update_success:
                        self.log_test_result("實驗會話更新", True, "會話狀態更新成功")
                    else:
                        self.log_test_result("實驗會話更新", False, "會話狀態更新失敗")
                    
                    await repository.close()
                    return True
                else:
                    self.log_test_result("實驗會話管理", False, "無法獲取會話信息")
                    await repository.close()
                    return False
            else:
                self.log_test_result("實驗會話管理", False, "會話創建失敗")
                await repository.close()
                return False
                
        except Exception as e:
            self.log_test_result("實驗會話管理", False, f"錯誤: {e}")
            return False
    
    async def test_episode_recording(self) -> bool:
        """測試訓練回合記錄"""
        logger.info("🧪 測試 4: 訓練回合記錄")
        
        try:
            from implementations.postgresql_repository import PostgreSQLRepository
            
            repository = PostgreSQLRepository(self.database_url)
            await repository.initialize()
            
            # 創建測試會話
            session_id = await repository.create_experiment_session(
                experiment_name="Phase1_Episode_Test",
                algorithm_type="DQN",
                scenario_type="test"
            )
            
            # 記錄測試回合
            episode_success = await repository.record_episode(
                session_id=session_id,
                episode_number=1,
                total_reward=100.5,
                success_rate=0.95,
                handover_latency_ms=25.3,
                convergence_indicator=0.85,
                exploration_rate=0.1,
                episode_metadata={
                    "test_episode": True,
                    "phase": "phase1_test"
                }
            )
            
            if episode_success:
                # 獲取回合數據
                episodes = await repository.get_episodes_by_session(session_id, limit=10)
                if episodes and len(episodes) > 0:
                    self.log_test_result("訓練回合記錄", True, f"成功記錄 {len(episodes)} 個回合")
                    await repository.close()
                    return True
                else:
                    self.log_test_result("訓練回合記錄", False, "無法獲取回合數據")
                    await repository.close()
                    return False
            else:
                self.log_test_result("訓練回合記錄", False, "回合記錄失敗")
                await repository.close()
                return False
                
        except Exception as e:
            self.log_test_result("訓練回合記錄", False, f"錯誤: {e}")
            return False
    
    async def test_performance_metrics(self) -> bool:
        """測試性能指標記錄"""
        logger.info("🧪 測試 5: 性能指標記錄")
        
        try:
            from implementations.postgresql_repository import PostgreSQLRepository
            
            repository = PostgreSQLRepository(self.database_url)
            await repository.initialize()
            
            # 記錄性能指標
            metrics_success = await repository.record_performance_metrics(
                algorithm_type="DQN",
                success_rate=0.92,
                average_reward=85.3,
                response_time_ms=15.2,
                stability_score=0.88,
                training_progress_percent=75.0,
                resource_utilization={
                    "cpu_usage": 45.2,
                    "memory_usage": 2048,
                    "gpu_usage": 0.0
                }
            )
            
            if metrics_success:
                # 獲取性能時間序列
                timeseries = await repository.get_performance_timeseries(
                    algorithm_type="DQN",
                    limit=10
                )
                
                if timeseries:
                    self.log_test_result("性能指標記錄", True, f"成功記錄 {len(timeseries)} 個指標")
                    await repository.close()
                    return True
                else:
                    self.log_test_result("性能指標記錄", False, "無法獲取性能時間序列")
                    await repository.close()
                    return False
            else:
                self.log_test_result("性能指標記錄", False, "性能指標記錄失敗")
                await repository.close()
                return False
                
        except Exception as e:
            self.log_test_result("性能指標記錄", False, f"錯誤: {e}")
            return False
    
    async def test_mock_repository_replacement(self) -> bool:
        """測試 MockRepository 替換"""
        logger.info("🧪 測試 6: MockRepository 替換")
        
        try:
            from api.enhanced_training_routes import get_repository
            
            # 獲取儲存庫實例
            repository = await get_repository()
            
            # 檢查是否為真實的 PostgreSQL 儲存庫
            if hasattr(repository, 'pool') and hasattr(repository, 'database_url'):
                self.log_test_result("MockRepository 替換", True, "成功使用 PostgreSQL 儲存庫")
                return True
            else:
                # 檢查是否為 MockRepository
                if repository.__class__.__name__ == "MockRepository":
                    self.log_test_result("MockRepository 替換", False, "仍在使用 MockRepository")
                    return False
                else:
                    self.log_test_result("MockRepository 替換", True, f"使用儲存庫: {repository.__class__.__name__}")
                    return True
                    
        except Exception as e:
            self.log_test_result("MockRepository 替換", False, f"錯誤: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有測試"""
        logger.info("🚀 開始 Phase 1 集成測試")
        logger.info("=" * 60)
        
        tests = [
            ("數據庫初始化", self.test_database_initialization),
            ("PostgreSQL 儲存庫", self.test_postgresql_repository),
            ("實驗會話管理", self.test_experiment_session_management),
            ("訓練回合記錄", self.test_episode_recording),
            ("性能指標記錄", self.test_performance_metrics),
            ("MockRepository 替換", self.test_mock_repository_replacement)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                success = await test_func()
                if success:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"❌ {test_name} 測試執行失敗: {e}")
                failed += 1
        
        logger.info("=" * 60)
        logger.info(f"🎯 測試完成: {passed} 通過, {failed} 失敗")
        
        if failed == 0:
            logger.info("🎉 Phase 1 所有測試通過！")
            logger.info("✅ 系統已成功實現真實 PostgreSQL 數據庫儲存")
        else:
            logger.error(f"❌ {failed} 個測試失敗，需要修復")
        
        return {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(tests) * 100,
            "results": self.test_results
        }
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """生成測試報告"""
        report = f"""
# LEO衛星換手決策RL系統 - Phase 1 測試報告

## 測試摘要
- 總測試數: {results['total_tests']}
- 通過測試: {results['passed']}
- 失敗測試: {results['failed']}
- 成功率: {results['success_rate']:.1f}%

## 詳細結果
"""
        
        for result in results['results']:
            status = "✅" if result['success'] else "❌"
            report += f"- {status} {result['test_name']}: {result['message']}\n"
        
        return report

async def main():
    """主測試函數"""
    test_suite = Phase1TestSuite()
    
    # 運行所有測試
    results = await test_suite.run_all_tests()
    
    # 生成測試報告
    report = test_suite.generate_test_report(results)
    
    # 保存測試報告
    with open("phase1_test_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    logger.info("📋 測試報告已保存至 phase1_test_report.md")
    
    # 返回測試結果
    return results['failed'] == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        logger.info("🎉 Phase 1 測試完全成功！")
        exit(0)
    else:
        logger.error("❌ Phase 1 測試失敗")
        exit(1)