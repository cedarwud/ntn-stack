"""
離散動作空間 LEO 衛星切換環境

專門為 DQN 算法設計的離散動作空間環境
"""

import gymnasium as gym
import numpy as np
from typing import Dict, Any, Tuple, Optional
from gymnasium.spaces import Discrete, Box
import logging

from .handover_env_fixed import LEOSatelliteHandoverEnv, HandoverScenario
from ..adapters.real_data_adapter import RealDataAdapter

logger = logging.getLogger(__name__)


class DiscreteLEOSatelliteHandoverEnv(gym.Env):
    """
    離散動作空間的 LEO 衛星切換環境

    將連續動作空間轉換為離散動作空間，適合 DQN 算法使用
    """

    def __init__(
        self,
        scenario: HandoverScenario = HandoverScenario.SINGLE_UE,
        max_ues: int = 5,
        max_satellites: int = 20,
        discrete_actions: int = 10,
        **kwargs,
    ):
        """
        初始化離散動作環境

        Args:
            scenario: 切換場景類型
            max_ues: 最大UE數量
            max_satellites: 最大衛星數量
            discrete_actions: 離散動作數量
        """
        super().__init__()

        # 初始化底層連續環境
        self.base_env = LEOSatelliteHandoverEnv(
            scenario=scenario, max_ues=max_ues, max_satellites=max_satellites, **kwargs
        )

        # 離散動作設定
        self.discrete_actions = discrete_actions

        # 定義離散動作空間
        self.action_space = Discrete(discrete_actions)

        # 觀測空間與底層環境相同
        self.observation_space = self.base_env.observation_space

        # 動作映射表
        self._create_action_mapping()

        # 環境狀態
        self.current_obs = None
        self.current_info = None

        logger.info(f"離散動作環境初始化完成: {discrete_actions} 個離散動作")

    def _create_action_mapping(self):
        """創建離散動作到連續動作的映射表"""
        self.action_mapping = {}

        # 基本動作類型
        action_types = [
            {"handover_decision": 0, "timing": 0.0, "target_satellite": 0},  # 維持連接
            {
                "handover_decision": 1,
                "timing": 1.0,
                "target_satellite": 0,
            },  # 立即切換到衛星0
            {
                "handover_decision": 1,
                "timing": 2.0,
                "target_satellite": 1,
            },  # 2秒後切換到衛星1
            {
                "handover_decision": 1,
                "timing": 3.0,
                "target_satellite": 2,
            },  # 3秒後切換到衛星2
            {
                "handover_decision": 1,
                "timing": 1.5,
                "target_satellite": 0,
            },  # 1.5秒後切換到衛星0
            {
                "handover_decision": 2,
                "timing": 2.0,
                "target_satellite": 1,
            },  # 2秒後準備切換到衛星1
            {
                "handover_decision": 1,
                "timing": 0.5,
                "target_satellite": 2,
            },  # 0.5秒後切換到衛星2
            {
                "handover_decision": 2,
                "timing": 1.0,
                "target_satellite": 0,
            },  # 1秒後準備切換到衛星0
            {
                "handover_decision": 1,
                "timing": 2.5,
                "target_satellite": 1,
            },  # 2.5秒後切換到衛星1
            {
                "handover_decision": 0,
                "timing": 0.0,
                "target_satellite": -1,
            },  # 維持當前連接
        ]

        # 確保動作數量匹配
        for i in range(self.discrete_actions):
            if i < len(action_types):
                self.action_mapping[i] = action_types[i]
            else:
                # 生成額外動作（變化目標衛星）
                satellite_id = i % 3  # 循環使用衛星0-2
                timing = 1.0 + (i % 3) * 0.5  # 時機從1.0到2.0
                self.action_mapping[i] = {
                    "handover_decision": 1,
                    "timing": timing,
                    "target_satellite": satellite_id,
                }

        logger.debug(f"創建了 {len(self.action_mapping)} 個離散動作映射")

    def _discrete_to_continuous(self, discrete_action: int) -> Dict[str, np.ndarray]:
        """將離散動作轉換為連續動作"""
        if discrete_action not in self.action_mapping:
            logger.warning(f"無效的離散動作: {discrete_action}, 使用維持動作")
            discrete_action = 0

        action_dict = self.action_mapping[discrete_action]

        # 轉換為底層環境期望的動作格式
        # 根據底層環境的 _parse_action 方法，單UE場景期望標量值，不是數組
        continuous_action = {
            "handover_decision": int(action_dict["handover_decision"]),  # 標量整數
            "timing": np.array([action_dict["timing"]], dtype=np.float32),
            "target_satellite": int(action_dict["target_satellite"]),  # 標量整數
            "power_control": np.array([1.0], dtype=np.float32),  # 默認功率控制
            "priority": np.array([0.5], dtype=np.float32),  # 默認優先級
        }

        return continuous_action

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """重置環境"""
        self.current_obs, self.current_info = self.base_env.reset(
            seed=seed, options=options
        )
        return self.current_obs, self.current_info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """執行動作"""
        # 轉換離散動作為連續動作
        continuous_action = self._discrete_to_continuous(action)

        # 執行底層環境
        obs, reward, terminated, truncated, info = self.base_env.step(continuous_action)

        # 更新當前狀態
        self.current_obs = obs
        self.current_info = info

        # 添加離散動作資訊
        info["discrete_action"] = action
        info["continuous_action"] = continuous_action

        return obs, reward, terminated, truncated, info

    def render(self, mode: str = "human"):
        """渲染環境"""
        return self.base_env.render(mode)

    def close(self):
        """關閉環境"""
        self.base_env.close()

    def get_action_info(self, action: int) -> Dict[str, Any]:
        """獲取動作詳細資訊"""
        if action in self.action_mapping:
            action_dict = self.action_mapping[action].copy()
            action_dict["discrete_action"] = action

            # 添加動作描述
            if action_dict["handover_decision"] == 0:
                action_dict["description"] = "維持當前連接"
            elif action_dict["handover_decision"] == 1:
                action_dict["description"] = (
                    f"在 {action_dict['timing']:.1f}秒後切換到衛星 {action_dict['target_satellite']}"
                )
            elif action_dict["handover_decision"] == 2:
                action_dict["description"] = (
                    f"在 {action_dict['timing']:.1f}秒後準備切換到衛星 {action_dict['target_satellite']}"
                )

            return action_dict
        else:
            return {"error": f"無效動作: {action}"}

    def get_all_actions_info(self) -> Dict[int, Dict[str, Any]]:
        """獲取所有動作的詳細資訊"""
        return {
            action: self.get_action_info(action)
            for action in range(self.discrete_actions)
        }


class DQNCompatibleHandoverEnv(DiscreteLEOSatelliteHandoverEnv):
    """
    專門為 DQN 算法優化的環境包裝器

    包含額外的 DQN 特定優化
    """

    def __init__(self, *args, **kwargs):
        """初始化 DQN 兼容環境"""
        # 提取 DQN 特定參數，避免傳遞給父類
        self.max_episode_steps = kwargs.pop("max_episode_steps", 200)
        self.reward_scale = kwargs.pop("reward_scale", 1.0)
        self.penalty_scale = kwargs.pop("penalty_scale", 0.1)

        # 初始化父類
        super().__init__(*args, **kwargs)

        # DQN 特定狀態
        self.episode_step_count = 0
        self.last_action = 0
        self.action_history = []

        logger.info("DQN 兼容環境初始化完成")

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """重置環境（DQN優化版）"""
        obs, info = super().reset(seed=seed, options=options)

        # 重置 DQN 特定狀態
        self.episode_step_count = 0
        self.last_action = 0
        self.action_history = []

        # 添加 DQN 特定資訊
        info["episode_step"] = self.episode_step_count
        info["max_episode_steps"] = self.max_episode_steps

        return obs, info

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """執行動作（DQN優化版）"""
        obs, reward, terminated, truncated, info = super().step(action)

        # 更新步數
        self.episode_step_count += 1

        # DQN 獎勵調整
        reward = self._adjust_reward_for_dqn(reward, action, info)

        # 檢查最大步數
        if self.episode_step_count >= self.max_episode_steps:
            truncated = True

        # 更新動作歷史
        self.last_action = action
        self.action_history.append(action)

        # 添加 DQN 特定資訊
        info["episode_step"] = self.episode_step_count
        info["last_action"] = self.last_action
        info["action_frequency"] = self._get_action_frequency()

        return obs, reward, terminated, truncated, info

    def _adjust_reward_for_dqn(
        self, reward: float, action: int, info: Dict[str, Any]
    ) -> float:
        """為 DQN 調整獎勵函數"""
        adjusted_reward = reward * self.reward_scale

        # 懲罰過於頻繁的切換
        if len(self.action_history) > 1:
            action_info = self.get_action_info(action)
            if action_info.get("handover_decision", 0) == 1:  # 切換動作
                # 檢查最近的動作
                recent_handovers = sum(
                    1
                    for a in self.action_history[-5:]
                    if self.get_action_info(a).get("handover_decision", 0) == 1
                )
                if recent_handovers > 2:
                    adjusted_reward -= self.penalty_scale * recent_handovers

        # 鼓勵良好的時機選擇
        if "handover_success" in info and info["handover_success"]:
            adjusted_reward += 0.1

        return adjusted_reward

    def _get_action_frequency(self) -> Dict[int, int]:
        """獲取動作頻率統計"""
        frequency = {}
        for action in self.action_history:
            frequency[action] = frequency.get(action, 0) + 1
        return frequency


# 環境註冊
def register_discrete_environments():
    """註冊離散動作環境"""
    try:
        from gymnasium.envs.registration import register

        # 註冊基本離散環境
        register(
            id="DiscreteLEOHandover-v1",
            entry_point="netstack_api.envs.discrete_handover_env:DiscreteLEOSatelliteHandoverEnv",
            max_episode_steps=200,
            kwargs={
                "scenario": HandoverScenario.SINGLE_UE,
                "max_ues": 5,
                "max_satellites": 10,
                "discrete_actions": 10,
            },
        )

        # 註冊 DQN 優化環境
        register(
            id="DQNLEOHandover-v1",
            entry_point="netstack_api.envs.discrete_handover_env:DQNCompatibleHandoverEnv",
            max_episode_steps=200,
            kwargs={
                "scenario": HandoverScenario.SINGLE_UE,
                "max_ues": 5,
                "max_satellites": 10,
                "discrete_actions": 10,
                "reward_scale": 1.0,
                "penalty_scale": 0.1,
            },
        )

        logger.info("離散動作環境註冊完成")

    except Exception as e:
        logger.warning(f"環境註冊失敗: {e}")


# 自動註冊環境
if __name__ != "__main__":
    register_discrete_environments()
