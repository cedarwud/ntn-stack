#!/usr/bin/env python3
"""
Phase 4 分佈式訓練系統測試

測試分佈式訓練系統的完整功能：
- 節點協調器測試
- 負載均衡測試  
- 故障恢復測試
- 分佈式訓練管理測試

Usage:
    python test_distributed_training.py
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


class DistributedTrainingTestSuite:
    """分佈式訓練測試套件"""
    
    def __init__(self):
        self.training_manager = None
        self.test_results = {}
        
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("🚀 開始 Phase 4 分佈式訓練系統測試...")
        
        try:
            # 基礎組件測試
            await self.test_node_coordinator()
            await self.test_load_balancer()
            await self.test_fault_recovery()
            
            # 集成測試
            await self.test_distributed_training_manager()
            await self.test_training_session_lifecycle()
            await self.test_multi_node_training()
            
            # 壓力測試
            await self.test_system_performance()
            
            # 生成測試報告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ 測試失敗: {e}")
            raise
        finally:
            if self.training_manager:
                await self.training_manager.stop()
    
    async def test_node_coordinator(self):
        """測試節點協調器"""
        logger.info("🔧 測試節點協調器...")
        
        try:
            # 創建節點協調器
            coordinator = NodeCoordinator(coordinator_port=8081)
            await coordinator.start()
            
            # 測試節點註冊
            node_info = {
                "node_id": "test_node_1",
                "node_type": "compute",
                "host": "localhost",
                "port": 8090,
                "resources": {
                    "cpu_cores": 4,
                    "memory_gb": 8,
                    "gpu_count": 1
                }
            }
            
            success = await coordinator.register_node("test_node_1", node_info)
            assert success, "節點註冊失敗"
            
            # 測試節點狀態
            nodes = await coordinator.get_all_nodes()
            assert len(nodes) == 1, "節點數量不正確"
            assert "test_node_1" in nodes, "節點不存在"
            
            # 測試心跳
            await coordinator.update_node_heartbeat("test_node_1")
            
            # 清理
            await coordinator.stop()
            
            self.test_results["node_coordinator"] = {
                "status": "PASS",
                "message": "節點協調器測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 節點協調器測試通過")
            
        except Exception as e:
            self.test_results["node_coordinator"] = {
                "status": "FAIL",
                "message": f"節點協調器測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 節點協調器測試失敗: {e}")
            raise
    
    async def test_load_balancer(self):
        """測試負載均衡器"""
        logger.info("⚖️ 測試負載均衡器...")
        
        try:
            # 創建負載均衡器
            balancer = LoadBalancer()
            await balancer.start()
            
            # 模擬節點
            from netstack_api.services.rl_training.distributed.node_coordinator import (
                NodeInfo, NodeStatus, NodeType
            )
            
            nodes = {
                "node_1": NodeInfo(
                    node_id="node_1",
                    node_type=NodeType.COMPUTE,
                    host="localhost",
                    port=8091,
                    status=NodeStatus.IDLE,
                    resources={"cpu_cores": 4, "memory_gb": 8},
                    current_load=0.3,
                    last_heartbeat=datetime.now()
                ),
                "node_2": NodeInfo(
                    node_id="node_2",
                    node_type=NodeType.COMPUTE,
                    host="localhost",
                    port=8092,
                    status=NodeStatus.IDLE,
                    resources={"cpu_cores": 8, "memory_gb": 16},
                    current_load=0.7,
                    last_heartbeat=datetime.now()
                )
            }
            
            # 更新節點信息
            await balancer.update_nodes(nodes)
            
            # 測試節點選擇
            selected_nodes = await balancer.select_nodes(list(nodes.keys()), 1)
            assert len(selected_nodes) == 1, "節點選擇數量不正確"
            assert selected_nodes[0] in nodes, "選擇的節點不存在"
            
            # 測試負載均衡策略
            from netstack_api.services.rl_training.distributed.load_balancer import (
                LoadBalancingStrategy
            )
            
            # 測試最小負載策略
            balancer.strategy = LoadBalancingStrategy.LEAST_LOADED
            selected = await balancer.select_nodes(list(nodes.keys()), 1)
            assert selected[0] == "node_1", "最小負載策略選擇錯誤"
            
            # 清理
            await balancer.stop()
            
            self.test_results["load_balancer"] = {
                "status": "PASS",
                "message": "負載均衡器測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 負載均衡器測試通過")
            
        except Exception as e:
            self.test_results["load_balancer"] = {
                "status": "FAIL",
                "message": f"負載均衡器測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 負載均衡器測試失敗: {e}")
            raise
    
    async def test_fault_recovery(self):
        """測試故障恢復機制"""
        logger.info("🔧 測試故障恢復機制...")
        
        try:
            # 創建故障恢復機制
            recovery = FaultRecovery()
            await recovery.start()
            
            # 模擬節點和任務
            from netstack_api.services.rl_training.distributed.node_coordinator import (
                NodeInfo, NodeStatus, NodeType, TrainingTask
            )
            
            nodes = {
                "node_1": NodeInfo(
                    node_id="node_1",
                    node_type=NodeType.COMPUTE,
                    host="localhost",
                    port=8091,
                    status=NodeStatus.IDLE,
                    resources={"cpu_cores": 4, "memory_gb": 8},
                    current_load=0.3,
                    last_heartbeat=datetime.now()
                )
            }
            
            tasks = {
                "task_1": TrainingTask(
                    task_id="task_1",
                    task_type="training",
                    algorithm="DQN",
                    environment="CartPole-v1",
                    hyperparameters={"learning_rate": 0.001},
                    resource_requirements={"cpu": 2, "memory": 4},
                    priority=1,
                    timeout=3600,
                    created_at=datetime.now(),
                    assigned_node="node_1"
                )
            }
            
            # 更新系統狀態
            await recovery.update_system_state(nodes, tasks)
            
            # 等待一段時間讓系統運行
            await asyncio.sleep(2)
            
            # 檢查故障統計
            stats = recovery.get_failure_stats()
            assert "total_failures" in stats, "故障統計不完整"
            
            # 清理
            await recovery.stop()
            
            self.test_results["fault_recovery"] = {
                "status": "PASS",
                "message": "故障恢復機制測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 故障恢復機制測試通過")
            
        except Exception as e:
            self.test_results["fault_recovery"] = {
                "status": "FAIL",
                "message": f"故障恢復機制測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 故障恢復機制測試失敗: {e}")
            raise
    
    async def test_distributed_training_manager(self):
        """測試分佈式訓練管理器"""
        logger.info("🎯 測試分佈式訓練管理器...")
        
        try:
            # 創建分佈式訓練管理器
            self.training_manager = DistributedTrainingManager(
                coordinator_port=8082,
                enable_fault_recovery=True,
                monitoring_interval=5
            )
            
            await self.training_manager.start()
            
            # 等待組件啟動
            await asyncio.sleep(2)
            
            # 測試系統狀態
            health = self.training_manager.get_system_health()
            assert health["status"] in ["healthy", "degraded"], "系統狀態異常"
            
            # 測試系統統計
            stats = self.training_manager.get_system_stats()
            assert "total_sessions" in stats, "系統統計不完整"
            assert "uptime_seconds" in stats, "系統運行時間統計缺失"
            
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
    
    async def test_training_session_lifecycle(self):
        """測試訓練會話生命週期"""
        logger.info("🔄 測試訓練會話生命週期...")
        
        try:
            # 創建訓練配置
            config = TrainingConfiguration(
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
            
            # 創建訓練會話
            session_id = await self.training_manager.create_training_session(config)
            assert session_id is not None, "訓練會話創建失敗"
            
            # 檢查會話狀態
            session_status = self.training_manager.get_session_status(session_id)
            assert session_status is not None, "無法獲取會話狀態"
            assert session_status["phase"] == "initializing", "會話狀態不正確"
            
            # 測試會話列表
            all_sessions = self.training_manager.get_all_sessions()
            assert len(all_sessions) == 1, "會話數量不正確"
            assert all_sessions[0]["session_id"] == session_id, "會話ID不匹配"
            
            self.test_results["training_session_lifecycle"] = {
                "status": "PASS",
                "message": "訓練會話生命週期測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 訓練會話生命週期測試通過")
            
        except Exception as e:
            self.test_results["training_session_lifecycle"] = {
                "status": "FAIL",
                "message": f"訓練會話生命週期測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 訓練會話生命週期測試失敗: {e}")
            raise
    
    async def test_multi_node_training(self):
        """測試多節點訓練"""
        logger.info("🌐 測試多節點訓練...")
        
        try:
            # 創建多節點訓練配置
            config = TrainingConfiguration(
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
            
            # 創建多節點訓練會話
            session_id = await self.training_manager.create_training_session(config)
            assert session_id is not None, "多節點訓練會話創建失敗"
            
            # 檢查會話配置
            session_status = self.training_manager.get_session_status(session_id)
            assert session_status["configuration"]["training_mode"] == "multi_node", "訓練模式不正確"
            
            self.test_results["multi_node_training"] = {
                "status": "PASS",
                "message": "多節點訓練測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 多節點訓練測試通過")
            
        except Exception as e:
            self.test_results["multi_node_training"] = {
                "status": "FAIL",
                "message": f"多節點訓練測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 多節點訓練測試失敗: {e}")
            raise
    
    async def test_system_performance(self):
        """測試系統性能"""
        logger.info("⚡ 測試系統性能...")
        
        try:
            start_time = time.time()
            
            # 創建多個並發會話
            session_ids = []
            for i in range(3):
                config = TrainingConfiguration(
                    algorithm="SAC",
                    environment="CartPole-v1",
                    hyperparameters={
                        "learning_rate": 0.0003,
                        "batch_size": 32,
                        "buffer_size": 10000,
                    },
                    training_mode=TrainingMode.SINGLE_NODE,
                    max_nodes=1,
                    min_nodes=1,
                    resource_requirements={"cpu": 1, "memory": 2},
                    training_steps=500,
                    evaluation_frequency=100,
                    checkpoint_frequency=250,
                    timeout=1800
                )
                
                session_id = await self.training_manager.create_training_session(config)
                session_ids.append(session_id)
            
            creation_time = time.time() - start_time
            
            # 檢查系統統計
            stats = self.training_manager.get_system_stats()
            assert stats["total_sessions"] == len(session_ids), "會話數量統計不正確"
            
            # 性能指標
            performance_metrics = {
                "session_creation_time": creation_time,
                "sessions_created": len(session_ids),
                "average_creation_time": creation_time / len(session_ids),
                "system_uptime": stats["uptime_seconds"]
            }
            
            self.test_results["system_performance"] = {
                "status": "PASS",
                "message": "系統性能測試通過",
                "metrics": performance_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ 系統性能測試通過 - 創建 {len(session_ids)} 個會話耗時 {creation_time:.2f} 秒")
            
        except Exception as e:
            self.test_results["system_performance"] = {
                "status": "FAIL",
                "message": f"系統性能測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 系統性能測試失敗: {e}")
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
                    "DistributedTrainingManager"
                ]
            }
        }
        
        # 保存報告
        report_file = f"/tmp/phase4_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 顯示摘要
        print("\n" + "="*60)
        print("🎯 Phase 4 分佈式訓練系統測試報告")
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
            print("\n🎉 所有測試通過！Phase 4 分佈式訓練系統運行正常。")
        else:
            print(f"\n⚠️  {failed_tests} 個測試失敗，請檢查日誌詳情。")
        
        logger.info(f"📊 測試報告已保存至: {report_file}")


async def main():
    """主函數"""
    print("🚀 Phase 4 分佈式訓練系統測試")
    print("="*60)
    
    # 創建測試套件
    test_suite = DistributedTrainingTestSuite()
    
    try:
        # 運行測試
        await test_suite.run_all_tests()
        
    except Exception as e:
        logger.error(f"❌ 測試運行失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 運行測試
    exit_code = asyncio.run(main())
    exit(exit_code)
