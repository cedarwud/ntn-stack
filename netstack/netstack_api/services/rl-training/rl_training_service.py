"""
RL Training Service

統一的RL訓練服務，整合所有RL功能到NetStack中
"""

from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from .core.system_initializer import RLSystemInitializer
from .core.service_locator import ServiceLocator
from .core.config_manager import ConfigDrivenAlgorithmManager
from .api.training_routes import router as training_router
from ...rl.training_engine import RLTrainingEngine

logger = logging.getLogger(__name__)


class RLTrainingService:
    """
    統一的RL訓練服務

    提供所有RL訓練功能的統一接口，整合到NetStack中
    """

    def __init__(self):
        self.system_initializer = None
        self.service_locator = None
        self.config_manager = None
        self.training_engine = None
        self.is_initialized = False

    async def initialize(self) -> bool:
        """
        初始化RL訓練服務

        Returns:
            bool: 初始化是否成功
        """
        try:
            # 初始化配置管理器
            self.config_manager = ConfigDrivenAlgorithmManager(
                config_path="config/algorithms.yml"
            )

            # 初始化系統
            self.system_initializer = RLSystemInitializer()
            await self.system_initializer.initialize()

            # 初始化服務定位器
            self.service_locator = ServiceLocator()

            # 初始化訓練引擎
            self.training_engine = RLTrainingEngine.get_instance()

            self.is_initialized = True
            logger.info("RL訓練服務初始化成功")
            return True

        except Exception as e:
            logger.error(f"RL訓練服務初始化失敗: {e}")
            return False

    async def start_training(
        self, algorithm: str, environment: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        開始訓練

        Args:
            algorithm: 算法名稱
            environment: 環境名稱
            config: 訓練配置

        Returns:
            Dict: 訓練結果
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            # 使用統一的訓練引擎
            result = await self.training_engine.start_training(
                algorithm=algorithm, environment=environment, config=config
            )

            logger.info(f"訓練開始成功: {algorithm}")
            return result

        except Exception as e:
            logger.error(f"訓練開始失敗: {e}")
            raise

    async def stop_training(self, session_id: str) -> Dict[str, Any]:
        """
        停止訓練

        Args:
            session_id: 訓練會話ID

        Returns:
            Dict: 停止結果
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            result = await self.training_engine.stop_training(session_id)
            logger.info(f"訓練停止成功: {session_id}")
            return result

        except Exception as e:
            logger.error(f"訓練停止失敗: {e}")
            raise

    async def get_training_status(self, session_id: str) -> Dict[str, Any]:
        """
        獲取訓練狀態

        Args:
            session_id: 訓練會話ID

        Returns:
            Dict: 訓練狀態
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            status = await self.training_engine.get_training_status(session_id)
            return status

        except Exception as e:
            logger.error(f"獲取訓練狀態失敗: {e}")
            raise

    async def get_training_sessions(self) -> Dict[str, Any]:
        """
        獲取所有訓練會話

        Returns:
            Dict: 訓練會話列表
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            sessions = await self.training_engine.get_training_sessions()
            return sessions

        except Exception as e:
            logger.error(f"獲取訓練會話失敗: {e}")
            raise

    async def get_available_algorithms(self) -> Dict[str, Any]:
        """
        獲取可用算法列表

        Returns:
            Dict: 可用算法列表
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            algorithms = await self.training_engine.get_available_algorithms()
            return algorithms

        except Exception as e:
            logger.error(f"獲取可用算法失敗: {e}")
            raise

    async def get_available_environments(self) -> Dict[str, Any]:
        """
        獲取可用環境列表

        Returns:
            Dict: 可用環境列表
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            environments = await self.training_engine.get_available_environments()
            return environments

        except Exception as e:
            logger.error(f"獲取可用環境失敗: {e}")
            raise

    async def cleanup(self):
        """
        清理資源
        """
        try:
            if self.system_initializer:
                await self.system_initializer.cleanup()
            logger.info("RL訓練服務資源清理完成")

        except Exception as e:
            logger.error(f"RL訓練服務資源清理失敗: {e}")


# 全局服務實例
_rl_training_service = None


def get_rl_training_service() -> RLTrainingService:
    """
    獲取RL訓練服務實例

    Returns:
        RLTrainingService: 服務實例
    """
    global _rl_training_service
    if _rl_training_service is None:
        _rl_training_service = RLTrainingService()
    return _rl_training_service
