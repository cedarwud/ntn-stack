#!/usr/bin/env python3
"""
Phase 4 分佈式訓練系統使用示例

展示如何使用分佈式訓練系統進行強化學習訓練：
- 創建訓練配置
- 啟動分佈式訓練
- 監控訓練進度
- 管理訓練會話

Usage:
    python phase4_example.py
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
    TrainingConfiguration,
    TrainingMode,
    TrainingPhase,
    TrainingMetrics
)


class Phase4Example:
    """Phase 4 分佈式訓練系統使用示例"""
    
    def __init__(self):
        self.examples = {}
        
    async def run_examples(self):
        """運行示例"""
        logger.info("🚀 開始 Phase 4 分佈式訓練系統使用示例...")
        
        try:
            # 示例 1: 單節點 DQN 訓練
            await self.example_single_node_dqn()
            
            # 示例 2: 多節點 PPO 訓練
            await self.example_multi_node_ppo()
            
            # 示例 3: 聯邦學習 SAC 訓練
            await self.example_federated_sac()
            
            # 示例 4: 分層訓練
            await self.example_hierarchical_training()
            
            # 示例 5: 訓練指標分析
            await self.example_metrics_analysis()
            
            # 生成示例報告
            self.generate_example_report()
            
        except Exception as e:
            logger.error(f"❌ 示例運行失敗: {e}")
            raise
    
    async def example_single_node_dqn(self):
        """示例 1: 單節點 DQN 訓練"""
        logger.info("🎯 示例 1: 單節點 DQN 訓練")
        
        try:
            # 創建 DQN 訓練配置
            config = TrainingConfiguration(
                algorithm="DQN",
                environment="CartPole-v1",
                hyperparameters={
                    "learning_rate": 0.001,
                    "batch_size": 32,
                    "buffer_size": 10000,
                    "epsilon": 0.1,
                    "epsilon_decay": 0.995,
                    "epsilon_min": 0.01,
                    "gamma": 0.99,
                    "target_update_frequency": 100
                },
                training_mode=TrainingMode.SINGLE_NODE,
                max_nodes=1,
                min_nodes=1,
                resource_requirements={
                    "cpu": 2,
                    "memory": 4,
                    "gpu": 0
                },
                training_steps=10000,
                evaluation_frequency=1000,
                checkpoint_frequency=5000,
                timeout=3600,
                enable_fault_recovery=True
            )
            
            # 顯示配置
            print(f"📋 DQN 訓練配置:")
            print(f"   算法: {config.algorithm}")
            print(f"   環境: {config.environment}")
            print(f"   訓練模式: {config.training_mode.value}")
            print(f"   訓練步數: {config.training_steps:,}")
            print(f"   學習率: {config.hyperparameters['learning_rate']}")
            print(f"   批次大小: {config.hyperparameters['batch_size']}")
            
            # 模擬訓練會話創建
            session_id = f"dqn_session_{int(time.time())}"
            print(f"🎯 模擬創建訓練會話: {session_id}")
            
            self.examples["single_node_dqn"] = {
                "config": config.to_dict(),
                "session_id": session_id,
                "description": "單節點 DQN 訓練示例",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 單節點 DQN 訓練示例完成")
            
        except Exception as e:
            logger.error(f"❌ 單節點 DQN 訓練示例失敗: {e}")
            raise
    
    async def example_multi_node_ppo(self):
        """示例 2: 多節點 PPO 訓練"""
        logger.info("🌐 示例 2: 多節點 PPO 訓練")
        
        try:
            # 創建 PPO 多節點訓練配置
            config = TrainingConfiguration(
                algorithm="PPO",
                environment="LunarLander-v2",
                hyperparameters={
                    "learning_rate": 0.0003,
                    "batch_size": 64,
                    "buffer_size": 2048,
                    "epsilon": 0.2,
                    "value_loss_coef": 0.5,
                    "entropy_coef": 0.01,
                    "gamma": 0.99,
                    "gae_lambda": 0.95,
                    "ppo_epochs": 10
                },
                training_mode=TrainingMode.MULTI_NODE,
                max_nodes=4,
                min_nodes=2,
                resource_requirements={
                    "cpu": 4,
                    "memory": 8,
                    "gpu": 1
                },
                training_steps=50000,
                evaluation_frequency=5000,
                checkpoint_frequency=10000,
                timeout=7200,
                enable_fault_recovery=True
            )
            
            # 顯示配置
            print(f"📋 PPO 多節點訓練配置:")
            print(f"   算法: {config.algorithm}")
            print(f"   環境: {config.environment}")
            print(f"   訓練模式: {config.training_mode.value}")
            print(f"   節點範圍: {config.min_nodes} - {config.max_nodes}")
            print(f"   訓練步數: {config.training_steps:,}")
            print(f"   PPO 輪數: {config.hyperparameters['ppo_epochs']}")
            
            # 模擬多節點任務分配
            session_id = f"ppo_session_{int(time.time())}"
            print(f"🎯 模擬多節點任務分配: {session_id}")
            
            # 模擬節點分配
            nodes = [f"node_{i}" for i in range(config.max_nodes)]
            print(f"📡 模擬節點分配: {nodes}")
            
            self.examples["multi_node_ppo"] = {
                "config": config.to_dict(),
                "session_id": session_id,
                "nodes": nodes,
                "description": "多節點 PPO 訓練示例",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 多節點 PPO 訓練示例完成")
            
        except Exception as e:
            logger.error(f"❌ 多節點 PPO 訓練示例失敗: {e}")
            raise
    
    async def example_federated_sac(self):
        """示例 3: 聯邦學習 SAC 訓練"""
        logger.info("🤝 示例 3: 聯邦學習 SAC 訓練")
        
        try:
            # 創建 SAC 聯邦學習配置
            config = TrainingConfiguration(
                algorithm="SAC",
                environment="Pendulum-v1",
                hyperparameters={
                    "learning_rate": 0.0003,
                    "batch_size": 256,
                    "buffer_size": 100000,
                    "tau": 0.005,
                    "alpha": 0.2,
                    "gamma": 0.99,
                    "target_update_interval": 1,
                    "gradient_steps": 1
                },
                training_mode=TrainingMode.FEDERATED,
                max_nodes=8,
                min_nodes=4,
                resource_requirements={
                    "cpu": 8,
                    "memory": 16,
                    "gpu": 2
                },
                training_steps=100000,
                evaluation_frequency=10000,
                checkpoint_frequency=20000,
                timeout=14400,
                enable_fault_recovery=True
            )
            
            # 顯示配置
            print(f"📋 SAC 聯邦學習配置:")
            print(f"   算法: {config.algorithm}")
            print(f"   環境: {config.environment}")
            print(f"   訓練模式: {config.training_mode.value}")
            print(f"   聯邦節點: {config.max_nodes}")
            print(f"   訓練步數: {config.training_steps:,}")
            print(f"   溫度參數: {config.hyperparameters['alpha']}")
            
            # 模擬聯邦學習架構
            session_id = f"sac_federated_{int(time.time())}"
            print(f"🎯 模擬聯邦學習架構: {session_id}")
            
            # 模擬參數服務器和客戶端
            server_node = "parameter_server"
            client_nodes = [f"client_{i}" for i in range(config.max_nodes - 1)]
            
            print(f"🖥️  參數服務器: {server_node}")
            print(f"📱 客戶端節點: {client_nodes}")
            
            self.examples["federated_sac"] = {
                "config": config.to_dict(),
                "session_id": session_id,
                "server_node": server_node,
                "client_nodes": client_nodes,
                "description": "聯邦學習 SAC 訓練示例",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 聯邦學習 SAC 訓練示例完成")
            
        except Exception as e:
            logger.error(f"❌ 聯邦學習 SAC 訓練示例失敗: {e}")
            raise
    
    async def example_hierarchical_training(self):
        """示例 4: 分層訓練"""
        logger.info("🏗️ 示例 4: 分層訓練")
        
        try:
            # 創建分層訓練配置
            config = TrainingConfiguration(
                algorithm="PPO",
                environment="MountainCar-v0",
                hyperparameters={
                    "learning_rate": 0.0003,
                    "batch_size": 128,
                    "buffer_size": 4096,
                    "epsilon": 0.2,
                    "gamma": 0.99,
                    "gae_lambda": 0.95,
                    "ppo_epochs": 8,
                    "clip_vloss": True
                },
                training_mode=TrainingMode.HIERARCHICAL,
                max_nodes=6,
                min_nodes=3,
                resource_requirements={
                    "cpu": 6,
                    "memory": 12,
                    "gpu": 1
                },
                training_steps=75000,
                evaluation_frequency=7500,
                checkpoint_frequency=15000,
                timeout=10800,
                enable_fault_recovery=True
            )
            
            # 顯示配置
            print(f"📋 分層訓練配置:")
            print(f"   算法: {config.algorithm}")
            print(f"   環境: {config.environment}")
            print(f"   訓練模式: {config.training_mode.value}")
            print(f"   層次節點: {config.max_nodes}")
            print(f"   訓練步數: {config.training_steps:,}")
            
            # 模擬分層架構
            session_id = f"hierarchical_{int(time.time())}"
            print(f"🎯 模擬分層架構: {session_id}")
            
            # 模擬主節點和工作節點
            master_node = "master_node"
            worker_nodes = [f"worker_{i}" for i in range(config.max_nodes - 1)]
            
            print(f"👑 主節點: {master_node}")
            print(f"👷 工作節點: {worker_nodes}")
            
            self.examples["hierarchical_training"] = {
                "config": config.to_dict(),
                "session_id": session_id,
                "master_node": master_node,
                "worker_nodes": worker_nodes,
                "description": "分層訓練示例",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 分層訓練示例完成")
            
        except Exception as e:
            logger.error(f"❌ 分層訓練示例失敗: {e}")
            raise
    
    async def example_metrics_analysis(self):
        """示例 5: 訓練指標分析"""
        logger.info("📊 示例 5: 訓練指標分析")
        
        try:
            # 模擬訓練指標
            session_id = "metrics_analysis_session"
            node_id = "analysis_node"
            
            # 創建一系列訓練指標
            metrics_series = []
            for step in range(0, 1000, 100):
                # 模擬訓練進度
                reward = 10 + step * 0.01 + (step % 300) * 0.05
                loss = 1.0 - step * 0.0008
                epsilon = max(0.01, 0.9 - step * 0.0009)
                
                metrics = TrainingMetrics(
                    session_id=session_id,
                    timestamp=datetime.now(),
                    node_id=node_id,
                    step=step,
                    episode_reward=reward,
                    episode_length=200 + step // 10,
                    loss=loss,
                    learning_rate=0.001,
                    epsilon=epsilon,
                    q_values=[reward * 0.8, reward * 0.9, reward * 1.0],
                    actor_loss=loss * 0.6,
                    critic_loss=loss * 0.4,
                    entropy=0.1 + step * 0.0001
                )
                
                metrics_series.append(metrics)
            
            # 分析指標
            print(f"📊 訓練指標分析:")
            print(f"   會話ID: {session_id}")
            print(f"   節點ID: {node_id}")
            print(f"   指標數量: {len(metrics_series)}")
            print(f"   步驟範圍: {metrics_series[0].step} - {metrics_series[-1].step}")
            print(f"   初始回報: {metrics_series[0].episode_reward:.2f}")
            print(f"   最終回報: {metrics_series[-1].episode_reward:.2f}")
            print(f"   回報改善: {metrics_series[-1].episode_reward - metrics_series[0].episode_reward:.2f}")
            
            # 計算統計信息
            rewards = [m.episode_reward for m in metrics_series]
            losses = [m.loss for m in metrics_series]
            
            stats = {
                "avg_reward": sum(rewards) / len(rewards),
                "max_reward": max(rewards),
                "min_reward": min(rewards),
                "avg_loss": sum(losses) / len(losses),
                "max_loss": max(losses),
                "min_loss": min(losses),
                "improvement_rate": (rewards[-1] - rewards[0]) / len(rewards)
            }
            
            print(f"📈 統計信息:")
            print(f"   平均回報: {stats['avg_reward']:.2f}")
            print(f"   最大回報: {stats['max_reward']:.2f}")
            print(f"   平均損失: {stats['avg_loss']:.4f}")
            print(f"   改善率: {stats['improvement_rate']:.4f}")
            
            self.examples["metrics_analysis"] = {
                "session_id": session_id,
                "node_id": node_id,
                "metrics_count": len(metrics_series),
                "statistics": stats,
                "sample_metrics": [m.to_dict() for m in metrics_series[:3]],
                "description": "訓練指標分析示例",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 訓練指標分析示例完成")
            
        except Exception as e:
            logger.error(f"❌ 訓練指標分析示例失敗: {e}")
            raise
    
    def generate_example_report(self):
        """生成示例報告"""
        logger.info("📊 生成示例報告...")
        
        # 生成報告
        report = {
            "example_summary": {
                "total_examples": len(self.examples),
                "example_date": datetime.now().isoformat(),
                "version": "Phase 4 v1.0.0"
            },
            "examples": self.examples,
            "system_info": {
                "python_version": "3.10+",
                "environment": "Phase 4 Development",
                "components_used": [
                    "TrainingConfiguration",
                    "TrainingMode",
                    "TrainingMetrics",
                    "DistributedTrainingManager"
                ]
            }
        }
        
        # 保存報告
        report_file = f"/tmp/phase4_examples_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 顯示摘要
        print("\n" + "="*60)
        print("🎯 Phase 4 分佈式訓練系統使用示例報告")
        print("="*60)
        print(f"示例總數: {len(self.examples)}")
        print(f"報告文件: {report_file}")
        print("="*60)
        
        # 詳細示例
        for example_name, example_data in self.examples.items():
            print(f"📋 {example_name}: {example_data['description']}")
        
        print("\n🎉 所有示例完成！Phase 4 分佈式訓練系統使用示例展示完成。")
        print("📖 查看報告文件獲取完整配置和使用詳情。")
        
        logger.info(f"📊 示例報告已保存至: {report_file}")


async def main():
    """主函數"""
    print("🚀 Phase 4 分佈式訓練系統使用示例")
    print("="*60)
    
    # 創建示例
    example = Phase4Example()
    
    try:
        # 運行示例
        await example.run_examples()
        
    except Exception as e:
        logger.error(f"❌ 示例運行失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 運行示例
    exit_code = asyncio.run(main())
    exit(exit_code)
