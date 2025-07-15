"""
NetStack RL 客戶端

實現 SimWorld 干擾服務與 NetStack RL 訓練系統的 API 橋接，
提供統一的 RL 算法調用介面。

Phase 1: API 橋接整合的核心組件
"""

import logging
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class NetStackRLClient:
    """NetStack RL 系統客戶端"""

    def __init__(self, netstack_base_url: str = "http://localhost:8000"):
        """
        初始化 NetStack RL 客戶端

        Args:
            netstack_base_url: NetStack API 基礎 URL
        """
        self.base_url = netstack_base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logger

        # 算法映射
        self.algorithm_mapping = {"dqn": "DQN", "ppo": "PPO", "sac": "SAC"}

        # 連接狀態
        self.is_connected = False
        self.last_health_check = None

        self.logger.info(f"NetStack RL 客戶端初始化，目標: {self.base_url}")

    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.disconnect()

    async def connect(self) -> bool:
        """
        連接到 NetStack RL 系統

        Returns:
            bool: 連接是否成功
        """
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # 健康檢查
            health_ok = await self.health_check()
            if health_ok:
                self.is_connected = True
                self.logger.info("成功連接到 NetStack RL 系統")
                return True
            else:
                self.logger.warning("NetStack RL 系統健康檢查失敗")
                return False

        except Exception as e:
            self.logger.error(f"連接 NetStack RL 系統失敗: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """斷開連接"""
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        self.logger.info("已斷開 NetStack RL 系統連接")

    async def health_check(self) -> bool:
        """
        健康檢查

        Returns:
            bool: 系統是否健康
        """
        try:
            if not self.session:
                return False

            assert self.session is not None  # 類型檢查器提示
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    self.last_health_check = datetime.now()
                    return True
                return False

        except Exception as e:
            self.logger.error(f"健康檢查失敗: {e}")
            return False

    async def get_available_algorithms(self) -> List[str]:
        """
        獲取可用的 RL 算法列表

        Returns:
            List[str]: 可用算法列表
        """
        try:
            if not self.is_connected:
                await self.connect()

            assert self.session is not None
            async with self.session.get(
                f"{self.base_url}/api/rl-training/algorithms"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("algorithms", ["dqn", "ppo", "sac"])
                else:
                    self.logger.warning(f"獲取算法列表失敗: {response.status}")
                    return ["dqn"]  # 降級到基礎算法

        except Exception as e:
            self.logger.error(f"獲取算法列表失敗: {e}")
            return ["dqn"]  # 降級到基礎算法

    async def start_training_session(
        self, algorithm: str, config: Dict[str, Any], session_name: Optional[str] = None
    ) -> Optional[str]:
        """
        啟動訓練會話

        Args:
            algorithm: 算法名稱 (dqn/ppo/sac)
            config: 訓練配置
            session_name: 會話名稱

        Returns:
            Optional[str]: 會話 ID，失敗時返回 None
        """
        try:
            if not self.is_connected:
                await self.connect()

            payload = {
                "algorithm": self.algorithm_mapping.get(algorithm, algorithm),
                "config": config,
                "session_name": session_name
                or f"simworld_interference_{algorithm}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "source": "simworld_interference",
            }

            assert self.session is not None
            async with self.session.post(
                f"{self.base_url}/api/rl-training/sessions/start", json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    session_id = data.get("session_id")
                    self.logger.info(f"成功啟動訓練會話: {session_id}")
                    return session_id
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"啟動訓練會話失敗: {response.status} - {error_text}"
                    )
                    return None

        except Exception as e:
            self.logger.error(f"啟動訓練會話失敗: {e}")
            return None

    async def get_training_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取訓練狀態

        Args:
            session_id: 會話 ID

        Returns:
            Optional[Dict[str, Any]]: 訓練狀態，失敗時返回 None
        """
        try:
            if not self.is_connected:
                await self.connect()

            assert self.session is not None
            async with self.session.get(
                f"{self.base_url}/api/rl-training/sessions/{session_id}/status"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"獲取訓練狀態失敗: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"獲取訓練狀態失敗: {e}")
            return None

    async def make_decision(
        self, algorithm: str, state: np.ndarray, session_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        使用訓練好的模型進行決策

        Args:
            algorithm: 算法名稱
            state: 環境狀態
            session_id: 可選的會話 ID

        Returns:
            Optional[Dict[str, Any]]: 決策結果
        """
        try:
            if not self.is_connected:
                await self.connect()

            # 將 numpy 數組轉換為列表
            state_list = state.tolist() if isinstance(state, np.ndarray) else state

            payload = {
                "algorithm": self.algorithm_mapping.get(algorithm, algorithm),
                "state": state_list,
                "session_id": session_id,
            }

            assert self.session is not None
            async with self.session.post(
                f"{self.base_url}/api/rl-training/predict", json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    self.logger.error(f"決策請求失敗: {response.status} - {error_text}")
                    return None

        except Exception as e:
            self.logger.error(f"決策請求失敗: {e}")
            return None

    async def store_experience(
        self,
        session_id: str,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ) -> bool:
        """
        存儲經驗到 NetStack RL 系統

        Args:
            session_id: 會話 ID
            state: 當前狀態
            action: 執行的動作
            reward: 獲得的獎勵
            next_state: 下一個狀態
            done: 是否結束

        Returns:
            bool: 存儲是否成功
        """
        try:
            if not self.is_connected:
                await self.connect()

            payload = {
                "session_id": session_id,
                "experience": {
                    "state": state.tolist() if isinstance(state, np.ndarray) else state,
                    "action": action,
                    "reward": reward,
                    "next_state": (
                        next_state.tolist()
                        if isinstance(next_state, np.ndarray)
                        else next_state
                    ),
                    "done": done,
                    "timestamp": datetime.now().isoformat(),
                },
            }

            assert self.session is not None
            async with self.session.post(
                f"{self.base_url}/api/rl-training/experience", json=payload
            ) as response:
                if response.status == 200:
                    return True
                else:
                    self.logger.warning(f"存儲經驗失敗: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"存儲經驗失敗: {e}")
            return False

    async def pause_training(self, session_id: str) -> bool:
        """
        暫停訓練

        Args:
            session_id: 會話 ID

        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.is_connected:
                await self.connect()

            assert self.session is not None
            async with self.session.post(
                f"{self.base_url}/api/rl-training/sessions/{session_id}/pause"
            ) as response:
                if response.status == 200:
                    self.logger.info(f"成功暫停訓練會話: {session_id}")
                    return True
                else:
                    self.logger.warning(f"暫停訓練失敗: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"暫停訓練失敗: {e}")
            return False

    async def resume_training(self, session_id: str) -> bool:
        """
        恢復訓練

        Args:
            session_id: 會話 ID

        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.is_connected:
                await self.connect()

            assert self.session is not None
            async with self.session.post(
                f"{self.base_url}/api/rl-training/sessions/{session_id}/resume"
            ) as response:
                if response.status == 200:
                    self.logger.info(f"成功恢復訓練會話: {session_id}")
                    return True
                else:
                    self.logger.warning(f"恢復訓練失敗: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"恢復訓練失敗: {e}")
            return False

    async def stop_training(self, session_id: str) -> bool:
        """
        停止訓練

        Args:
            session_id: 會話 ID

        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.is_connected:
                await self.connect()

            assert self.session is not None
            async with self.session.post(
                f"{self.base_url}/api/rl-training/sessions/{session_id}/stop"
            ) as response:
                if response.status == 200:
                    self.logger.info(f"成功停止訓練會話: {session_id}")
                    return True
                else:
                    self.logger.warning(f"停止訓練失敗: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"停止訓練失敗: {e}")
            return False

    async def get_training_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取訓練指標

        Args:
            session_id: 會話 ID

        Returns:
            Optional[Dict[str, Any]]: 訓練指標
        """
        try:
            if not self.is_connected:
                await self.connect()

            assert self.session is not None
            async with self.session.get(
                f"{self.base_url}/api/rl-training/sessions/{session_id}/metrics"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"獲取訓練指標失敗: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"獲取訓練指標失敗: {e}")
            return None


# 全局客戶端實例（單例模式）
_netstack_rl_client: Optional[NetStackRLClient] = None


async def get_netstack_rl_client() -> NetStackRLClient:
    """
    獲取 NetStack RL 客戶端實例（單例）

    Returns:
        NetStackRLClient: 客戶端實例
    """
    global _netstack_rl_client

    if _netstack_rl_client is None:
        _netstack_rl_client = NetStackRLClient()
        await _netstack_rl_client.connect()

    return _netstack_rl_client


async def cleanup_netstack_rl_client():
    """清理客戶端資源"""
    global _netstack_rl_client

    if _netstack_rl_client:
        await _netstack_rl_client.disconnect()
        _netstack_rl_client = None
