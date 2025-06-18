# 整合架構示例 - 可插拔設計

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import gymnasium as gym


class RLEngine(ABC):
    """RL 引擎抽象接口 - 可以輕易替換實現"""

    @abstractmethod
    async def get_action(self, state: Dict) -> Dict:
        pass

    @abstractmethod
    async def update(self, experience: Dict) -> None:
        pass


class GymnasiumEngine(RLEngine):
    """Gymnasium 實現"""

    def __init__(self, env_name: str):
        self.env = gym.make(env_name)
        self.agent = None  # 可插入不同算法

    async def get_action(self, state: Dict) -> Dict:
        return self.agent.get_action(state)

    async def update(self, experience: Dict) -> None:
        self.agent.update(experience)


class LegacyEngine(RLEngine):
    """原有實現"""

    def __init__(self, legacy_service):
        self.service = legacy_service

    async def get_action(self, state: Dict) -> Dict:
        return await self.service.legacy_method(state)

    async def update(self, experience: Dict) -> None:
        await self.service.legacy_update(experience)


class UnifiedAIService:
    """統一的 AI 服務 - 支持多種後端"""

    def __init__(self, engine: Optional[RLEngine] = None):
        self.engine = engine or self._get_default_engine()

    def _get_default_engine(self) -> RLEngine:
        """可以通過配置選擇引擎"""
        engine_type = os.getenv("RL_ENGINE", "legacy")

        if engine_type == "gymnasium":
            return GymnasiumEngine("netstack:interference-v0")
        else:
            return LegacyEngine(self._load_legacy_service())

    async def make_decision(self, network_state: Dict) -> Dict:
        """統一的決策接口"""
        return await self.engine.get_action(network_state)

    async def learn(self, experience: Dict) -> None:
        """統一的學習接口"""
        await self.engine.update(experience)

    def switch_engine(self, new_engine: RLEngine):
        """動態換手引擎 - 零停機時間"""
        self.engine = new_engine


# 使用示例
class AIRANAntiInterferenceService:
    def __init__(self, ai_engine: Optional[RLEngine] = None):
        self.ai_service = UnifiedAIService(ai_engine)

    async def detect_and_mitigate(self, interference_data: Dict):
        # 統一接口，後端可換手
        action = await self.ai_service.make_decision(interference_data)
        result = await self._execute_action(action)

        # 學習經驗
        experience = self._create_experience(interference_data, action, result)
        await self.ai_service.learn(experience)

        return result
