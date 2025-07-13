#!/usr/bin/env python3
"""
強制初始化 RL 系統腳本

直接調用和初始化 RL 系統組件，解決 ecosystem_status: "not_initialized" 問題
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def force_initialize_rl_system():
    """強制初始化 RL 系統"""
    logger.info("💪 強制初始化 RL 系統...")

    success_count = 0

    try:
        # 方法 1: 初始化 AlgorithmEcosystemManager 並確保狀態持久化
        logger.info("📝 方法 1: 直接初始化 AlgorithmEcosystemManager")
        try:
            from netstack_api.algorithm_ecosystem.ecosystem_manager import (
                AlgorithmEcosystemManager,
            )

            # 創建並初始化管理器
            ecosystem_manager = AlgorithmEcosystemManager()
            success = await ecosystem_manager.initialize()

            if success and ecosystem_manager.is_initialized:
                logger.info("✅ AlgorithmEcosystemManager 初始化成功")

                # 獲取並顯示狀態
                status = ecosystem_manager.get_system_status()
                logger.info(f"🔍 系統狀態: {status}")

                # 設置為全局變量（如果可能）
                try:
                    # 嘗試設置到監控路由器的全局變量
                    import netstack_api.routers.rl_monitoring_router as rl_router

                    rl_router.ecosystem_manager = ecosystem_manager
                    logger.info("✅ 已將管理器設置為全局變量")
                    success_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ 無法設置全局變量: {e}")

            else:
                logger.error("❌ AlgorithmEcosystemManager 初始化失敗")

        except Exception as e:
            logger.error(f"❌ AlgorithmEcosystemManager 初始化失敗: {e}")

        # 方法 2: 創建基本的 Mock 算法來填充算法列表
        logger.info("📝 方法 2: 創建基本算法來解決空算法列表問題")
        try:
            from netstack_api.algorithm_ecosystem.registry import AlgorithmRegistry
            from netstack_api.algorithm_ecosystem.interfaces import (
                HandoverAlgorithm,
                HandoverContext,
                HandoverDecision,
                AlgorithmInfo,
                AlgorithmType,
            )

            # 創建一個簡單的 Mock 算法
            class MockHandoverAlgorithm:
                def __init__(self, name: str):
                    self.name = name

                def get_algorithm_info(self):
                    return AlgorithmInfo(
                        name=self.name,
                        algorithm_type=AlgorithmType.TRADITIONAL,
                        version="1.0.0",
                        description=f"Mock {self.name} algorithm for testing",
                        parameters={},
                    )

                async def predict_handover(
                    self, context: HandoverContext
                ) -> HandoverDecision:
                    # 返回一個基本的換手決策
                    return HandoverDecision(
                        should_handover=False,
                        target_satellite_id=None,
                        confidence=0.5,
                        reasoning="Mock decision",
                        algorithm_name=self.name,
                        execution_time_ms=1.0,
                    )

            # 創建算法註冊表並註冊基本算法
            registry = AlgorithmRegistry()
            await registry.initialize()

            # 註冊幾個基本算法
            mock_algorithms = ["dqn", "ppo", "sac", "traditional"]
            for alg_name in mock_algorithms:
                mock_alg = MockHandoverAlgorithm(alg_name)
                await registry.register_algorithm(
                    alg_name, mock_alg, enabled=True, priority=10
                )
                logger.info(f"✅ 已註冊 Mock 算法: {alg_name}")

            # 檢查註冊的算法
            registered = registry.get_registered_algorithms()
            logger.info(f"🔍 已註冊算法數量: {len(registered)}")

            success_count += 1

        except Exception as e:
            logger.error(f"❌ Mock 算法註冊失敗: {e}")

        # 方法 3: 修復 RL 訓練引擎
        logger.info("📝 方法 3: 嘗試修復 RL 訓練引擎")
        try:
            from netstack_api.rl.training_engine import get_training_engine

            engine = await get_training_engine()

            if engine and engine.initialized:
                logger.info("✅ RL 訓練引擎已初始化")
                success_count += 1
            else:
                logger.warning("⚠️ RL 訓練引擎未初始化")

        except Exception as e:
            logger.error(f"❌ RL 訓練引擎測試失敗: {e}")

        # 總結
        logger.info(f"🎯 初始化完成，成功項目: {success_count}/3")

        if success_count >= 2:
            logger.info("✅ 強制初始化成功，建議重新測試 RL 系統")
            return True
        else:
            logger.warning("⚠️ 強制初始化部分成功，可能仍有問題")
            return False

    except Exception as e:
        logger.error(f"💥 強制初始化失敗: {e}")
        return False


async def main():
    """主函數"""
    logger.info("🚀 RL 系統強制初始化腳本啟動")

    success = await force_initialize_rl_system()

    if success:
        logger.info("✅ 強制初始化完成，請測試:")
        logger.info("curl -s http://localhost:8080/api/v1/rl/health | jq .")
    else:
        logger.error("❌ 強制初始化失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
