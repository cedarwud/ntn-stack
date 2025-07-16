#!/usr/bin/env python3
"""
Phase 4 分佈式訓練系統簡化測試

測試分佈式訓練系統的基本功能：
- 組件初始化測試
- 基本功能測試
- 系統狀態測試

Usage:
    python simple_test.py
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入分佈式訓練組件
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from netstack_api.services.rl_training.distributed import (
    DistributedTrainingManager,
    TrainingConfiguration,
    TrainingMode,
    NodeCoordinator,
    LoadBalancer,
    FaultRecovery
)


class SimpleTestSuite:
    """簡化測試套件"""
    
    def __init__(self):
        self.test_results = {}
        
    async def run_basic_tests(self):
        """運行基本測試"""
        logger.info("🚀 開始 Phase 4 分佈式訓練系統基本測試...")
        
        try:
            # 組件初始化測試
            await self.test_component_initialization()
            
            # 分佈式訓練管理器測試
            await self.test_distributed_training_manager()
            
            # 訓練配置測試
            await self.test_training_configuration()
            
            # 生成測試報告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ 測試失敗: {e}")
            raise
    
    async def test_component_initialization(self):
        """測試組件初始化"""
        logger.info("🔧 測試組件初始化...")
        
        try:
            # 測試節點協調器初始化
            coordinator = NodeCoordinator(coordinator_port=8081)
            assert coordinator is not None, "節點協調器初始化失敗"
            
            # 測試負載均衡器初始化
            balancer = LoadBalancer()
            assert balancer is not None, "負載均衡器初始化失敗"
            
            # 測試故障恢復機制初始化
            recovery = FaultRecovery()
            assert recovery is not None, "故障恢復機制初始化失敗"
            
            self.test_results["component_initialization"] = {
                "status": "PASS",
                "message": "組件初始化測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 組件初始化測試通過")
            
        except Exception as e:
            self.test_results["component_initialization"] = {
                "status": "FAIL",
                "message": f"組件初始化測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 組件初始化測試失敗: {e}")
            raise
    
    async def test_distributed_training_manager(self):
        """測試分佈式訓練管理器"""
        logger.info("🎯 測試分佈式訓練管理器...")
        
        try:
            # 創建分佈式訓練管理器
            manager = DistributedTrainingManager(
                coordinator_port=8082,
                enable_fault_recovery=True,
                monitoring_interval=5
            )
            
            # 測試系統狀態
            health = manager.get_system_health()
            assert health is not None, "無法獲取系統健康狀態"
            assert "status" in health, "系統健康狀態格式不正確"
            
            # 測試系統統計
            stats = manager.get_system_stats()
            assert stats is not None, "無法獲取系統統計"
            assert "total_sessions" in stats, "系統統計格式不正確"
            
            # 測試會話管理
            all_sessions = manager.get_all_sessions()
            assert isinstance(all_sessions, list), "會話列表格式不正確"
            
            active_sessions = manager.get_active_sessions()
            assert isinstance(active_sessions, list), "活動會話列表格式不正確"
            
            self.test_results["distributed_training_manager"] = {
                "status": "PASS",
                "message": "分佈式訓練管理器測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 分佈式訓練管理器測試通過")
            
        except Exception as e:
            self.test_results["distributed_training_manager"] = {
                "status": "FAIL",
                "message": f"分佈式訓練管理器測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 分佈式訓練管理器測試失敗: {e}")
            raise
    
    async def test_training_configuration(self):
        """測試訓練配置"""
        logger.info("📋 測試訓練配置...")
        
        try:
            # 測試 DQN 配置
            dqn_config = TrainingConfiguration(
                algorithm="DQN",
                environment="CartPole-v1",
                hyperparameters={
                    "learning_rate": 0.001,
                    "batch_size": 32,
                    "buffer_size": 10000,
                    "epsilon": 0.1
                },
                training_mode=TrainingMode.SINGLE_NODE,
                max_nodes=1,
                min_nodes=1,
                resource_requirements={"cpu": 2, "memory": 4},
                training_steps=1000,
                evaluation_frequency=100,
                checkpoint_frequency=500,
                timeout=3600
            )
            
            assert dqn_config.algorithm == "DQN", "DQN 配置算法不正確"
            assert dqn_config.training_mode == TrainingMode.SINGLE_NODE, "訓練模式不正確"
            
            # 測試配置轉換
            config_dict = dqn_config.to_dict()
            assert isinstance(config_dict, dict), "配置轉換格式不正確"
            assert "algorithm" in config_dict, "配置字典缺少算法"
            assert "training_mode" in config_dict, "配置字典缺少訓練模式"
            
            # 測試 PPO 配置
            ppo_config = TrainingConfiguration(
                algorithm="PPO",
                environment="CartPole-v1",
                hyperparameters={
                    "learning_rate": 0.0003,
                    "batch_size": 64,
                    "buffer_size": 20000,
                    "epsilon": 0.2
                },
                training_mode=TrainingMode.MULTI_NODE,
                max_nodes=3,
                min_nodes=2,
                resource_requirements={"cpu": 4, "memory": 8},
                training_steps=2000,
                evaluation_frequency=200,
                checkpoint_frequency=1000,
                timeout=7200
            )
            
            assert ppo_config.algorithm == "PPO", "PPO 配置算法不正確"
            assert ppo_config.training_mode == TrainingMode.MULTI_NODE, "多節點訓練模式不正確"
            
            # 測試聯邦學習配置
            federated_config = TrainingConfiguration(
                algorithm="SAC",
                environment="CartPole-v1",
                hyperparameters={
                    "learning_rate": 0.0003,
                    "batch_size": 128,
                    "buffer_size": 50000,
                },
                training_mode=TrainingMode.FEDERATED,
                max_nodes=5,
                min_nodes=3,
                resource_requirements={"cpu": 8, "memory": 16},
                training_steps=5000,
                evaluation_frequency=500,
                checkpoint_frequency=2500,
                timeout=14400
            )
            
            assert federated_config.training_mode == TrainingMode.FEDERATED, "聯邦學習模式不正確"
            
            self.test_results["training_configuration"] = {
                "status": "PASS",
                "message": "訓練配置測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 訓練配置測試通過")
            
        except Exception as e:
            self.test_results["training_configuration"] = {
                "status": "FAIL",
                "message": f"訓練配置測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 訓練配置測試失敗: {e}")
            raise
    
    def generate_test_report(self):
        """生成測試報告"""
        logger.info("📊 生成測試報告...")
        
        # 統計測試結果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # 生成報告
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{success_rate:.1f}%",
                "test_date": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "system_info": {
                "python_version": "3.10+",
                "test_environment": "Phase 4 Development",
                "components_tested": [
                    "NodeCoordinator",
                    "LoadBalancer", 
                    "FaultRecovery",
                    "DistributedTrainingManager",
                    "TrainingConfiguration"
                ]
            }
        }
        
        # 保存報告
        report_file = f"/tmp/phase4_simple_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 顯示摘要
        print("\n" + "="*60)
        print("🎯 Phase 4 分佈式訓練系統基本測試報告")
        print("="*60)
        print(f"測試總數: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"失敗測試: {failed_tests}")
        print(f"成功率: {success_rate:.1f}%")
        print(f"報告文件: {report_file}")
        print("="*60)
        
        # 詳細結果
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {result['message']}")
        
        if failed_tests == 0:
            print("\n🎉 所有測試通過！Phase 4 分佈式訓練系統基本功能正常。")
        else:
            print(f"\n⚠️  {failed_tests} 個測試失敗，請檢查日誌詳情。")
        
        logger.info(f"📊 測試報告已保存至: {report_file}")


async def main():
    """主函數"""
    print("🚀 Phase 4 分佈式訓練系統基本測試")
    print("="*60)
    
    # 創建測試套件
    test_suite = SimpleTestSuite()
    
    try:
        # 運行測試
        await test_suite.run_basic_tests()
        
    except Exception as e:
        logger.error(f"❌ 測試運行失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 運行測試
    exit_code = asyncio.run(main())
    exit(exit_code)
