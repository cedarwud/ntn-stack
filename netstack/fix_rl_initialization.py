#!/usr/bin/env python3
"""
RL 系統初始化修復腳本

解決 Phase 1.3b 完成後的 RL 系統初始化問題
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


async def fix_rl_initialization():
    """修復 RL 系統初始化問題"""
    logger.info("🔧 開始修復 RL 系統初始化問題...")

    try:
        # 步驟 1: 初始化 RLTrainingService
        logger.info("📝 步驟 1: 初始化 RLTrainingService")
        try:
            from netstack_api.services.rl_training.rl_training_service import (
                get_rl_training_service,
            )

            rl_service = get_rl_training_service()
            success = await rl_service.initialize()

            if success:
                logger.info("✅ RLTrainingService 初始化成功")
            else:
                logger.error("❌ RLTrainingService 初始化失敗")
                return False

        except Exception as e:
            logger.error(f"❌ RLTrainingService 導入/初始化失敗: {e}")

        # 步驟 2: 檢查算法生態系統管理器
        logger.info("📝 步驟 2: 檢查算法生態系統管理器")
        try:
            from netstack_api.algorithm_ecosystem.ecosystem_manager import (
                AlgorithmEcosystemManager,
            )

            ecosystem_manager = AlgorithmEcosystemManager()
            success = await ecosystem_manager.initialize()

            if success:
                logger.info("✅ AlgorithmEcosystemManager 初始化成功")

                # 檢查狀態
                status = ecosystem_manager.get_system_status()
                logger.info(f"🔍 系統狀態: {status}")

            else:
                logger.error("❌ AlgorithmEcosystemManager 初始化失敗")

        except Exception as e:
            logger.error(f"❌ AlgorithmEcosystemManager 導入/初始化失敗: {e}")

        # 步驟 3: 檢查配置文件
        logger.info("📝 步驟 3: 檢查配置文件")
        config_files = [
            "netstack_api/services/rl-training/config/rl_config.yaml",
            "netstack_api/services/rl-training/config/default_config.yaml",
        ]

        for config_file in config_files:
            config_path = project_root / config_file
            if config_path.exists():
                logger.info(f"✅ 配置文件存在: {config_file}")
            else:
                logger.warning(f"⚠️ 配置文件不存在: {config_file}")

        # 步驟 4: 測試 API 端點
        logger.info("📝 步驟 4: 測試關鍵組件")
        try:
            # 測試訓練引擎
            from netstack_api.rl.training_engine import (
                RLTrainingEngine,
                get_training_engine,
            )

            engine = await get_training_engine()
            algorithms = await engine.get_available_algorithms()
            logger.info(f"🔍 可用算法: {algorithms}")

        except Exception as e:
            logger.error(f"❌ 訓練引擎測試失敗: {e}")

        # 步驟 5: 手動註冊算法（如果需要）
        logger.info("📝 步驟 5: 手動註冊基本算法")
        try:
            from netstack_api.algorithm_ecosystem.registry import AlgorithmRegistry

            registry = AlgorithmRegistry()
            await registry.initialize()

            registered = registry.get_registered_algorithms()
            logger.info(f"🔍 已註冊算法: {list(registered.keys())}")

        except Exception as e:
            logger.error(f"❌ 算法註冊表測試失敗: {e}")

        logger.info("🎉 RL 系統初始化修復完成")
        return True

    except Exception as e:
        logger.error(f"💥 修復過程失敗: {e}")
        return False


async def main():
    """主函數"""
    logger.info("🚀 RL 系統初始化修復腳本啟動")

    success = await fix_rl_initialization()

    if success:
        logger.info("✅ 修復完成，請重新測試 RL 系統")

        # 測試 API 響應
        logger.info("📋 建議測試命令:")
        logger.info("curl -s http://localhost:8080/api/v1/rl/health | jq .")
        logger.info(
            "curl -s http://localhost:8080/api/v1/rl/training/start/dqn -X POST | jq ."
        )

    else:
        logger.error("❌ 修復失敗，需要進一步調查")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
