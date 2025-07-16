#!/usr/bin/env python3
"""
Phase 4 分佈式訓練系統最小化測試

只測試核心組件的基本功能，避免複雜的依賴問題
"""

import asyncio
import logging
import json
import time
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 導入組件
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from netstack_api.services.rl_training.distributed import (
    TrainingConfiguration,
    TrainingMode,
    TrainingPhase,
    TrainingMetrics
)


class MinimalTestSuite:
    """最小化測試套件"""
    
    def __init__(self):
        self.test_results = {}
        
    async def run_tests(self):
        """運行測試"""
        logger.info("🚀 開始 Phase 4 分佈式訓練系統最小化測試...")
        
        try:
            # 測試數據類
            await self.test_data_classes()
            
            # 測試枚舉
            await self.test_enums()
            
            # 生成測試報告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ 測試失敗: {e}")
            raise
    
    async def test_data_classes(self):
        """測試數據類"""
        logger.info("📋 測試數據類...")
        
        try:
            # 測試 TrainingConfiguration
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
            
            assert config.algorithm == "DQN", "算法設置不正確"
            assert config.training_mode == TrainingMode.SINGLE_NODE, "訓練模式不正確"
            assert config.max_nodes == 1, "最大節點數設置不正確"
            
            # 測試轉換為字典
            config_dict = config.to_dict()
            assert isinstance(config_dict, dict), "配置轉換失敗"
            assert "algorithm" in config_dict, "配置字典缺少算法"
            assert "training_mode" in config_dict, "配置字典缺少訓練模式"
            
            # 測試 TrainingMetrics
            metrics = TrainingMetrics(
                session_id="test_session",
                timestamp=datetime.now(),
                node_id="test_node",
                step=100,
                episode_reward=10.5,
                episode_length=200,
                loss=0.05,
                learning_rate=0.001,
                epsilon=0.1,
                q_values=[1.0, 2.0, 3.0]
            )
            
            assert metrics.session_id == "test_session", "會話ID不正確"
            assert metrics.step == 100, "步驟數不正確"
            assert metrics.episode_reward == 10.5, "回報不正確"
            
            # 測試轉換為字典
            metrics_dict = metrics.to_dict()
            assert isinstance(metrics_dict, dict), "指標轉換失敗"
            assert "session_id" in metrics_dict, "指標字典缺少會話ID"
            assert "step" in metrics_dict, "指標字典缺少步驟"
            
            self.test_results["data_classes"] = {
                "status": "PASS",
                "message": "數據類測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 數據類測試通過")
            
        except Exception as e:
            self.test_results["data_classes"] = {
                "status": "FAIL",
                "message": f"數據類測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 數據類測試失敗: {e}")
            raise
    
    async def test_enums(self):
        """測試枚舉"""
        logger.info("🔧 測試枚舉...")
        
        try:
            # 測試 TrainingMode
            assert TrainingMode.SINGLE_NODE.value == "single_node", "單節點模式值不正確"
            assert TrainingMode.MULTI_NODE.value == "multi_node", "多節點模式值不正確"
            assert TrainingMode.FEDERATED.value == "federated", "聯邦學習模式值不正確"
            assert TrainingMode.HIERARCHICAL.value == "hierarchical", "分層模式值不正確"
            
            # 測試 TrainingPhase
            assert TrainingPhase.INITIALIZING.value == "initializing", "初始化階段值不正確"
            assert TrainingPhase.PREPARING.value == "preparing", "準備階段值不正確"
            assert TrainingPhase.TRAINING.value == "training", "訓練階段值不正確"
            assert TrainingPhase.EVALUATING.value == "evaluating", "評估階段值不正確"
            assert TrainingPhase.COMPLETED.value == "completed", "完成階段值不正確"
            assert TrainingPhase.FAILED.value == "failed", "失敗階段值不正確"
            assert TrainingPhase.CANCELLED.value == "cancelled", "取消階段值不正確"
            
            # 測試枚舉列表
            all_modes = list(TrainingMode)
            assert len(all_modes) == 4, "訓練模式數量不正確"
            
            all_phases = list(TrainingPhase)
            assert len(all_phases) == 7, "訓練階段數量不正確"
            
            self.test_results["enums"] = {
                "status": "PASS",
                "message": "枚舉測試通過",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("✅ 枚舉測試通過")
            
        except Exception as e:
            self.test_results["enums"] = {
                "status": "FAIL",
                "message": f"枚舉測試失敗: {e}",
                "timestamp": datetime.now().isoformat()
            }
            logger.error(f"❌ 枚舉測試失敗: {e}")
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
                    "TrainingConfiguration",
                    "TrainingMetrics",
                    "TrainingMode",
                    "TrainingPhase"
                ]
            }
        }
        
        # 保存報告
        report_file = f"/tmp/phase4_minimal_test_report_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 顯示摘要
        print("\n" + "="*60)
        print("🎯 Phase 4 分佈式訓練系統最小化測試報告")
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
            print("\n🎉 所有測試通過！Phase 4 分佈式訓練系統核心組件正常。")
        else:
            print(f"\n⚠️  {failed_tests} 個測試失敗，請檢查日誌詳情。")
        
        logger.info(f"📊 測試報告已保存至: {report_file}")


async def main():
    """主函數"""
    print("🚀 Phase 4 分佈式訓練系統最小化測試")
    print("="*60)
    
    # 創建測試套件
    test_suite = MinimalTestSuite()
    
    try:
        # 運行測試
        await test_suite.run_tests()
        
    except Exception as e:
        logger.error(f"❌ 測試運行失敗: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # 運行測試
    exit_code = asyncio.run(main())
    exit(exit_code)
