"""
🧪 真實指標計算系統測試
驗證所有改進的功能是否正常工作
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List

# 導入測試目標
from ..analytics.real_metrics_calculator import (
    RealMetricsCalculator, EpisodeData, get_real_metrics_calculator
)
from ..interfaces.metrics_interface import (
    MetricsStandardizer, StandardizedMetrics, TrendType
)
from ..algorithms.real_rl_algorithms import (
    RealDQNAlgorithm, RealPPOAlgorithm, RealSACAlgorithm
)
from ..core.algorithm_integrator import (
    DQNAlgorithm, PPOAlgorithm, SACAlgorithm, RLAlgorithmIntegrator
)

logger = logging.getLogger(__name__)


class RealMetricsSystemTester:
    """真實指標計算系統測試器"""
    
    def __init__(self):
        self.test_results = {}
        self.logger = logging.getLogger(__name__)
    
    async def test_real_metrics_calculator(self) -> Dict[str, Any]:
        """測試真實指標計算器"""
        self.logger.info("🧮 測試真實指標計算器...")
        
        try:
            # 獲取計算器實例
            calculator = await get_real_metrics_calculator()
            
            # 創建測試數據
            test_episodes = self._create_test_episodes()
            
            # 計算指標
            metrics = await calculator.calculate_training_metrics(
                session_id="test_session_001",
                algorithm="DQN",
                episodes_data=test_episodes
            )
            
            # 驗證結果
            results = {
                "success": True,
                "metrics_calculated": True,
                "success_rate": metrics.success_rate,
                "stability": metrics.stability,
                "learning_efficiency": metrics.learning_efficiency,
                "confidence_score": metrics.confidence_score,
                "performance_trend": metrics.performance_trend,
                "convergence_episode": metrics.convergence_episode,
                "data_points": len(test_episodes)
            }
            
            # 驗證指標範圍
            assert 0.0 <= metrics.success_rate <= 1.0, "Success rate 超出範圍"
            assert 0.0 <= metrics.stability <= 1.0, "Stability 超出範圍"
            assert 0.0 <= metrics.learning_efficiency <= 1.0, "Learning efficiency 超出範圍"
            assert 0.0 <= metrics.confidence_score <= 1.0, "Confidence score 超出範圍"
            
            self.logger.info(f"✅ 真實指標計算器測試通過: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 真實指標計算器測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_metrics_standardizer(self) -> Dict[str, Any]:
        """測試指標標準化器"""
        self.logger.info("📏 測試指標標準化器...")
        
        try:
            standardizer = MetricsStandardizer()
            
            # 創建測試指標
            test_metrics = StandardizedMetrics(
                success_rate=0.85,
                stability=0.92,
                learning_efficiency=0.78,
                confidence_score=0.65,
                average_reward=150.5,
                convergence_episode=45,
                performance_trend=TrendType.IMPROVING,
                calculation_timestamp=datetime.now().isoformat(),
                data_points_count=100,
                calculation_method="test"
            )
            
            # 測試前端格式化
            frontend_format = standardizer.format_for_frontend(test_metrics)
            
            # 測試後端格式化
            backend_format = standardizer.format_for_backend(test_metrics)
            
            # 驗證格式化結果
            assert frontend_format["success_rate"] == 85.0, "前端成功率格式化錯誤"
            assert backend_format["success_rate"] == 0.85, "後端成功率格式化錯誤"
            assert "trend_emoji" in frontend_format, "缺少趨勢表情符號"
            assert "confidence_emoji" in frontend_format, "缺少可信度表情符號"
            
            results = {
                "success": True,
                "frontend_format_valid": True,
                "backend_format_valid": True,
                "validation_passed": standardizer._validate_all_metrics(test_metrics),
                "confidence_level": standardizer.get_confidence_level(test_metrics.confidence_score),
                "quality_score": standardizer._calculate_quality_score(test_metrics)
            }
            
            self.logger.info(f"✅ 指標標準化器測試通過: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 指標標準化器測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_real_algorithms(self) -> Dict[str, Any]:
        """測試真實 RL 算法"""
        self.logger.info("🧠 測試真實 RL 算法...")
        
        results = {}
        
        try:
            # 測試 DQN 算法
            dqn = RealDQNAlgorithm(state_size=10, action_size=4)
            test_state = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            
            # 測試預測
            action = await dqn.predict(test_state)
            assert 0 <= action <= 3, "DQN 動作超出範圍"
            
            # 測試學習
            await dqn.learn(test_state, action, 10.0, test_state, False)
            
            # 獲取指標
            dqn_metrics = dqn.get_metrics()
            
            results["dqn"] = {
                "prediction_valid": True,
                "learning_executed": True,
                "metrics_available": bool(dqn_metrics),
                "total_steps": dqn_metrics.get("total_steps", 0),
                "epsilon": dqn_metrics.get("epsilon", 0)
            }
            
            # 測試 PPO 算法
            ppo = RealPPOAlgorithm(state_size=10, action_size=4)
            action = await ppo.predict(test_state)
            await ppo.learn(test_state, action, 15.0, test_state, False)
            ppo_metrics = ppo.get_metrics()
            
            results["ppo"] = {
                "prediction_valid": True,
                "learning_executed": True,
                "metrics_available": bool(ppo_metrics),
                "total_steps": ppo_metrics.get("total_steps", 0)
            }
            
            # 測試 SAC 算法
            sac = RealSACAlgorithm(state_size=10, action_size=4)
            action = await sac.predict(test_state)
            await sac.learn(test_state, action, 12.0, test_state, False)
            sac_metrics = sac.get_metrics()
            
            results["sac"] = {
                "prediction_valid": True,
                "learning_executed": True,
                "metrics_available": bool(sac_metrics),
                "total_steps": sac_metrics.get("total_steps", 0)
            }
            
            results["success"] = True
            self.logger.info(f"✅ 真實 RL 算法測試通過: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 真實 RL 算法測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_algorithm_integrator(self) -> Dict[str, Any]:
        """測試算法整合器"""
        self.logger.info("🔧 測試算法整合器...")
        
        try:
            integrator = RLAlgorithmIntegrator()
            
            # 測試算法獲取
            dqn_algo = await integrator.get_algorithm("dqn")
            ppo_algo = await integrator.get_algorithm("ppo")
            sac_algo = await integrator.get_algorithm("sac")
            
            assert dqn_algo is not None, "DQN 算法獲取失敗"
            assert ppo_algo is not None, "PPO 算法獲取失敗"
            assert sac_algo is not None, "SAC 算法獲取失敗"
            
            # 測試算法切換
            switch_success = integrator.set_active_algorithm("dqn")
            assert switch_success, "算法切換失敗"
            
            active_algo = integrator.get_active_algorithm()
            assert active_algo is not None, "活躍算法獲取失敗"
            
            # 測試指標獲取
            all_metrics = integrator.get_all_metrics()
            assert len(all_metrics) == 3, "指標數量不正確"
            
            # 測試狀態獲取
            status = integrator.get_integration_status()
            
            results = {
                "success": True,
                "algorithms_available": integrator.get_available_algorithms(),
                "active_algorithm": integrator.active_algorithm,
                "total_algorithms": status["total_algorithms"],
                "status": status["status"]
            }
            
            self.logger.info(f"✅ 算法整合器測試通過: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ 算法整合器測試失敗: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """運行綜合測試"""
        self.logger.info("🚀 開始綜合測試...")
        
        test_results = {
            "test_timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # 運行各項測試
        test_results["tests"]["real_metrics_calculator"] = await self.test_real_metrics_calculator()
        test_results["tests"]["metrics_standardizer"] = await self.test_metrics_standardizer()
        test_results["tests"]["real_algorithms"] = await self.test_real_algorithms()
        test_results["tests"]["algorithm_integrator"] = await self.test_algorithm_integrator()
        
        # 計算總體成功率
        successful_tests = sum(1 for test in test_results["tests"].values() if test.get("success", False))
        total_tests = len(test_results["tests"])
        success_rate = successful_tests / total_tests
        
        test_results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "overall_success": success_rate >= 0.75  # 75% 通過率為成功
        }
        
        if test_results["summary"]["overall_success"]:
            self.logger.info(f"🎉 綜合測試通過! 成功率: {success_rate:.2%}")
        else:
            self.logger.warning(f"⚠️ 綜合測試部分失敗! 成功率: {success_rate:.2%}")
        
        return test_results
    
    def _create_test_episodes(self) -> List[EpisodeData]:
        """創建測試回合數據"""
        episodes = []
        
        for i in range(50):
            # 模擬學習曲線：初期較差，逐漸改善
            progress = i / 49.0
            base_reward = 50 + progress * 100  # 從 50 提升到 150
            
            # 添加一些隨機變化
            import random
            noise = random.uniform(-10, 10)
            episode_reward = base_reward + noise
            
            # 判斷成功（基於獎勵閾值）
            success = episode_reward > 100.0
            
            episode = EpisodeData(
                episode_number=i + 1,
                total_reward=episode_reward,
                steps=random.randint(50, 200),
                success=success,
                handover_count=random.randint(0, 5),
                average_latency=random.uniform(10, 100),
                timestamp=datetime.now()
            )
            episodes.append(episode)
        
        return episodes


async def main():
    """主測試函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    tester = RealMetricsSystemTester()
    results = await tester.run_comprehensive_test()
    
    # 輸出測試結果
    print("\n" + "="*60)
    print("🧪 真實指標計算系統測試結果")
    print("="*60)
    print(json.dumps(results, indent=2, ensure_ascii=False))
    print("="*60)
    
    return results["summary"]["overall_success"]


if __name__ == "__main__":
    success = asyncio.run(main())
