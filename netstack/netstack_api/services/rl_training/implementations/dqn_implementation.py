"""
🧠 DQN 算法實現

將現有的 DQN 算法適配到新的接口架構中，
提供完整的 IRLAlgorithm 接口實現。
"""

import logging
import asyncio
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

from ..interfaces.rl_algorithm import (
    IRLAlgorithm, ScenarioType, TrainingConfig, TrainingResult,
    PredictionContext, HandoverDecision, ITrainingObserver
)
from ..core.algorithm_factory import algorithm_plugin

# 嘗試導入現有的 DQN 實現
try:
    from ....algorithm_ecosystem.rl_algorithms.dqn_agent import DQNHandoverAgent, DQNNetwork
    EXISTING_DQN_AVAILABLE = True
except ImportError:
    EXISTING_DQN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("無法導入現有的 DQN 實現，將使用模擬實現")

logger = logging.getLogger(__name__)


class DQNNetworkWrapper(nn.Module):
    """DQN 網路包裝器"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_layers: List[int] = None):
        super().__init__()
        
        if hidden_layers is None:
            hidden_layers = [64, 64]
        
        layers = []
        prev_dim = state_dim
        
        for hidden_dim in hidden_layers:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU()
            ])
            prev_dim = hidden_dim
        
        layers.append(nn.Linear(prev_dim, action_dim))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


@algorithm_plugin(
    name="DQN",
    version="2.0.0",
    supported_scenarios=[ScenarioType.URBAN, ScenarioType.SUBURBAN, ScenarioType.LOW_LATENCY],
    description="Deep Q-Network 算法實現，適配新架構",
    author="NetStack Team"
)
class DQNAlgorithmImpl(IRLAlgorithm):
    """DQN 算法實現
    
    基於深度 Q 網路的強化學習算法，
    專門針對 LEO 衛星換手決策優化。
    """
    
    def __init__(self, config: Dict[str, Any], scenario_type: ScenarioType):
        self.config = config
        self.scenario_type = scenario_type
        self._name = "DQN"
        self._version = "2.0.0"
        
        # 算法參數
        self.learning_rate = config.get('learning_rate', 0.001)
        self.batch_size = config.get('batch_size', 32)
        self.gamma = config.get('gamma', 0.99)
        self.epsilon = config.get('epsilon', 1.0)
        self.epsilon_min = config.get('epsilon_min', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.target_update_freq = config.get('target_update_freq', 100)
        self.memory_size = config.get('memory_size', 10000)
        
        # 網路參數
        self.state_dim = config.get('state_dim', 10)  # 根據衛星狀態定義
        self.action_dim = config.get('action_dim', 5)  # 候選衛星數量
        self.hidden_layers = config.get('hidden_layers', [64, 64])
        
        # 初始化網路
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_network = DQNNetworkWrapper(self.state_dim, self.action_dim, self.hidden_layers).to(self.device)
        self.target_network = DQNNetworkWrapper(self.state_dim, self.action_dim, self.hidden_layers).to(self.device)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)
        
        # 經驗回放池
        self.memory = []
        self.memory_pointer = 0
        
        # 訓練狀態
        self._is_trained = False
        self._training_metrics = {}
        self._observers: List[ITrainingObserver] = []
        
        # 根據場景調整參數
        self._adjust_scenario_parameters()
        
        logger.info(f"DQN 算法初始化完成 (場景: {scenario_type.value})")
    
    def _adjust_scenario_parameters(self) -> None:\n        \"\"\"根據場景調整算法參數\"\"\"\n        if self.scenario_type == ScenarioType.LOW_LATENCY:\n            # 低延遲場景需要更快的決策\n            self.epsilon_decay = 0.99\n            self.target_update_freq = 50\n            logger.debug(\"調整參數以適應低延遲場景\")\n        elif self.scenario_type == ScenarioType.URBAN:\n            # 城市場景網路變化較快\n            self.learning_rate *= 1.2\n            logger.debug(\"調整參數以適應城市場景\")\n        elif self.scenario_type == ScenarioType.SUBURBAN:\n            # 郊區場景相對穩定\n            self.epsilon_decay = 0.998\n            logger.debug(\"調整參數以適應郊區場景\")\n    \n    def get_name(self) -> str:\n        \"\"\"獲取算法名稱\"\"\"\n        return self._name\n    \n    def get_version(self) -> str:\n        \"\"\"獲取算法版本\"\"\"\n        return self._version\n    \n    def get_supported_scenarios(self) -> List[ScenarioType]:\n        \"\"\"獲取支持的場景類型\"\"\"\n        return [ScenarioType.URBAN, ScenarioType.SUBURBAN, ScenarioType.LOW_LATENCY]\n    \n    async def train(self, config: TrainingConfig) -> TrainingResult:\n        \"\"\"執行訓練\"\"\"\n        start_time = datetime.now()\n        \n        try:\n            logger.info(f\"開始 DQN 訓練 (回合數: {config.episodes})\")\n            \n            total_reward = 0\n            episode_rewards = []\n            convergence_episode = None\n            convergence_threshold = 0.8  # 80% 成功率視為收斂\n            \n            for episode in range(config.episodes):\n                # 通知觀察者回合開始\n                for observer in self._observers:\n                    await observer.on_episode_start(episode, self._name)\n                \n                episode_reward = await self._train_episode(config)\n                episode_rewards.append(episode_reward)\n                total_reward += episode_reward\n                \n                # 計算移動平均成功率\n                if len(episode_rewards) >= 100:\n                    recent_success_rate = np.mean([r > 0 for r in episode_rewards[-100:]])\n                    if recent_success_rate >= convergence_threshold and convergence_episode is None:\n                        convergence_episode = episode\n                        logger.info(f\"算法在第 {episode} 回合收斂\")\n                \n                # 更新目標網路\n                if episode % self.target_update_freq == 0:\n                    self.target_network.load_state_dict(self.q_network.state_dict())\n                \n                # 衰減探索率\n                self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)\n                \n                # 通知觀察者回合結束\n                episode_metrics = {\n                    \"reward\": episode_reward,\n                    \"epsilon\": self.epsilon,\n                    \"success_rate\": recent_success_rate if len(episode_rewards) >= 100 else 0.0\n                }\n                \n                for observer in self._observers:\n                    await observer.on_episode_end(episode, episode_reward, episode_metrics)\n                \n                # 每100回合記錄進度\n                if (episode + 1) % 100 == 0:\n                    avg_reward = np.mean(episode_rewards[-100:])\n                    logger.info(f\"回合 {episode + 1}: 平均獎勵 = {avg_reward:.3f}, Epsilon = {self.epsilon:.3f}\")\n            \n            # 訓練完成\n            end_time = datetime.now()\n            duration = (end_time - start_time).total_seconds()\n            \n            self._is_trained = True\n            final_score = np.mean(episode_rewards[-100:]) if len(episode_rewards) >= 100 else np.mean(episode_rewards)\n            \n            # 更新訓練指標\n            self._training_metrics = {\n                \"total_episodes\": config.episodes,\n                \"final_score\": final_score,\n                \"convergence_episode\": convergence_episode,\n                \"final_epsilon\": self.epsilon,\n                \"training_duration\": duration\n            }\n            \n            result = TrainingResult(\n                success=True,\n                final_score=final_score,\n                episodes_completed=config.episodes,\n                convergence_episode=convergence_episode,\n                metrics=self._training_metrics,\n                model_path=None,  # 將在保存模型時設置\n                training_duration_seconds=duration,\n                memory_usage_mb=self._get_memory_usage_mb()\n            )\n            \n            # 通知觀察者訓練完成\n            for observer in self._observers:\n                await observer.on_training_complete(result)\n            \n            logger.info(f\"DQN 訓練完成: 最終分數 = {final_score:.3f}\")\n            return result\n            \n        except Exception as e:\n            logger.error(f\"DQN 訓練失敗: {e}\")\n            return TrainingResult(\n                success=False,\n                final_score=0.0,\n                episodes_completed=0,\n                convergence_episode=None,\n                metrics={\"error\": str(e)},\n                model_path=None,\n                training_duration_seconds=(datetime.now() - start_time).total_seconds(),\n                memory_usage_mb=self._get_memory_usage_mb()\n            )\n    \n    async def _train_episode(self, config: TrainingConfig) -> float:\n        \"\"\"訓練單個回合\"\"\"\n        # 模擬環境交互\n        total_reward = 0\n        \n        for step in range(config.max_steps_per_episode):\n            # 模擬狀態觀察\n            state = self._generate_mock_state()\n            \n            # 選擇動作\n            action = self._select_action(state)\n            \n            # 執行動作並獲得反饋\n            next_state, reward, done = self._simulate_environment_step(state, action)\n            \n            # 存儲經驗\n            self._store_experience(state, action, reward, next_state, done)\n            \n            # 更新網路\n            if len(self.memory) >= self.batch_size:\n                self._update_network()\n            \n            total_reward += reward\n            \n            if done:\n                break\n        \n        return total_reward\n    \n    def _generate_mock_state(self) -> np.ndarray:\n        \"\"\"生成模擬狀態\"\"\"\n        # 模擬衛星網路狀態：位置、信號強度、負載等\n        return np.random.randn(self.state_dim)\n    \n    def _select_action(self, state: np.ndarray) -> int:\n        \"\"\"選擇動作（epsilon-greedy策略）\"\"\"\n        if np.random.random() < self.epsilon:\n            return np.random.randint(self.action_dim)\n        \n        with torch.no_grad():\n            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)\n            q_values = self.q_network(state_tensor)\n            return q_values.argmax().item()\n    \n    def _simulate_environment_step(self, state: np.ndarray, action: int) -> tuple:\n        \"\"\"模擬環境步驟\"\"\"\n        # 模擬換手決策的結果\n        next_state = self._generate_mock_state()\n        \n        # 根據場景生成不同的獎勵\n        if self.scenario_type == ScenarioType.LOW_LATENCY:\n            # 低延遲場景重視快速決策\n            reward = np.random.normal(1.0, 0.5)\n        elif self.scenario_type == ScenarioType.URBAN:\n            # 城市場景重視穩定性\n            reward = np.random.normal(0.8, 0.3)\n        else:\n            # 郊區場景\n            reward = np.random.normal(0.9, 0.2)\n        \n        done = np.random.random() < 0.1  # 10% 機率結束\n        \n        return next_state, reward, done\n    \n    def _store_experience(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):\n        \"\"\"存儲經驗到回放池\"\"\"\n        experience = (state, action, reward, next_state, done)\n        \n        if len(self.memory) < self.memory_size:\n            self.memory.append(experience)\n        else:\n            self.memory[self.memory_pointer] = experience\n            self.memory_pointer = (self.memory_pointer + 1) % self.memory_size\n    \n    def _update_network(self):\n        \"\"\"更新 Q 網路\"\"\"\n        batch = np.random.choice(len(self.memory), self.batch_size, replace=False)\n        batch_experiences = [self.memory[i] for i in batch]\n        \n        states = torch.FloatTensor([exp[0] for exp in batch_experiences]).to(self.device)\n        actions = torch.LongTensor([exp[1] for exp in batch_experiences]).to(self.device)\n        rewards = torch.FloatTensor([exp[2] for exp in batch_experiences]).to(self.device)\n        next_states = torch.FloatTensor([exp[3] for exp in batch_experiences]).to(self.device)\n        dones = torch.BoolTensor([exp[4] for exp in batch_experiences]).to(self.device)\n        \n        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))\n        next_q_values = self.target_network(next_states).max(1)[0].detach()\n        target_q_values = rewards + (self.gamma * next_q_values * ~dones)\n        \n        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)\n        \n        self.optimizer.zero_grad()\n        loss.backward()\n        self.optimizer.step()\n    \n    async def predict(self, context: PredictionContext) -> HandoverDecision:\n        \"\"\"執行換手決策預測\"\"\"\n        try:\n            # 將上下文轉換為狀態向量\n            state = self._context_to_state(context)\n            \n            # 使用網路進行預測\n            with torch.no_grad():\n                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)\n                q_values = self.q_network(state_tensor)\n                action = q_values.argmax().item()\n            \n            # 將動作映射到候選衛星\n            target_satellite_id = context.candidate_satellites[action % len(context.candidate_satellites)]\n            confidence_score = float(torch.softmax(q_values, dim=1).max())\n            \n            # 根據場景估算性能指標\n            estimated_latency = self._estimate_latency(context, target_satellite_id)\n            predicted_throughput = self._estimate_throughput(context, target_satellite_id)\n            \n            decision = HandoverDecision(\n                target_satellite_id=target_satellite_id,\n                confidence_score=confidence_score,\n                estimated_latency_ms=estimated_latency,\n                predicted_throughput_mbps=predicted_throughput,\n                decision_reasoning={\n                    \"algorithm\": self._name,\n                    \"q_values\": q_values.cpu().numpy().tolist(),\n                    \"selected_action\": action,\n                    \"scenario\": self.scenario_type.value\n                },\n                execution_priority=1\n            )\n            \n            logger.debug(f\"DQN 預測完成: 目標衛星 {target_satellite_id}, 信心度 {confidence_score:.3f}\")\n            return decision\n            \n        except Exception as e:\n            logger.error(f\"DQN 預測失敗: {e}\")\n            # 返回預設決策\n            return HandoverDecision(\n                target_satellite_id=context.candidate_satellites[0],\n                confidence_score=0.1,\n                estimated_latency_ms=100.0,\n                predicted_throughput_mbps=10.0,\n                decision_reasoning={\"error\": str(e)},\n                execution_priority=5\n            )\n    \n    def _context_to_state(self, context: PredictionContext) -> np.ndarray:\n        \"\"\"將預測上下文轉換為狀態向量\"\"\"\n        # 簡化的狀態表示\n        state = np.zeros(self.state_dim)\n        \n        # UE 位置 (2D)\n        state[0] = context.ue_position.get('lat', 0.0)\n        state[1] = context.ue_position.get('lon', 0.0)\n        \n        # 當前服務衛星資訊\n        state[2] = context.current_serving_satellite\n        \n        # 候選衛星數量\n        state[3] = len(context.candidate_satellites)\n        \n        # 網路條件指標\n        network_conditions = context.network_conditions\n        state[4] = network_conditions.get('signal_strength', 0.0)\n        state[5] = network_conditions.get('latency', 0.0)\n        state[6] = network_conditions.get('throughput', 0.0)\n        state[7] = network_conditions.get('packet_loss', 0.0)\n        \n        # 時間特徵（小時）\n        state[8] = context.timestamp.hour / 24.0\n        \n        # 場景特徵\n        scenario_encoding = {\n            ScenarioType.URBAN: 0.0,\n            ScenarioType.SUBURBAN: 0.5,\n            ScenarioType.LOW_LATENCY: 1.0\n        }\n        state[9] = scenario_encoding.get(self.scenario_type, 0.0)\n        \n        return state\n    \n    def _estimate_latency(self, context: PredictionContext, satellite_id: int) -> float:\n        \"\"\"估算換手延遲\"\"\"\n        base_latency = 50.0  # 基礎延遲 (ms)\n        \n        if self.scenario_type == ScenarioType.LOW_LATENCY:\n            return base_latency * 0.8\n        elif self.scenario_type == ScenarioType.URBAN:\n            return base_latency * 1.2\n        else:\n            return base_latency\n    \n    def _estimate_throughput(self, context: PredictionContext, satellite_id: int) -> float:\n        \"\"\"估算吞吐量\"\"\"\n        base_throughput = 100.0  # 基礎吞吐量 (Mbps)\n        \n        if self.scenario_type == ScenarioType.URBAN:\n            return base_throughput * 1.5  # 城市場景帶寬較高\n        elif self.scenario_type == ScenarioType.LOW_LATENCY:\n            return base_throughput * 0.8  # 低延遲場景可能犧牲帶寬\n        else:\n            return base_throughput\n    \n    def load_model(self, model_path: str) -> bool:\n        \"\"\"加載模型\"\"\"\n        try:\n            model_path = Path(model_path)\n            if not model_path.exists():\n                logger.error(f\"模型文件不存在: {model_path}\")\n                return False\n            \n            checkpoint = torch.load(model_path, map_location=self.device)\n            self.q_network.load_state_dict(checkpoint['q_network'])\n            self.target_network.load_state_dict(checkpoint['target_network'])\n            self.optimizer.load_state_dict(checkpoint['optimizer'])\n            self.epsilon = checkpoint.get('epsilon', self.epsilon_min)\n            \n            self._is_trained = True\n            logger.info(f\"成功加載 DQN 模型: {model_path}\")\n            return True\n            \n        except Exception as e:\n            logger.error(f\"加載模型失敗: {e}\")\n            return False\n    \n    def save_model(self, model_path: str) -> bool:\n        \"\"\"保存模型\"\"\"\n        try:\n            model_path = Path(model_path)\n            model_path.parent.mkdir(parents=True, exist_ok=True)\n            \n            checkpoint = {\n                'q_network': self.q_network.state_dict(),\n                'target_network': self.target_network.state_dict(),\n                'optimizer': self.optimizer.state_dict(),\n                'epsilon': self.epsilon,\n                'config': self.config,\n                'scenario_type': self.scenario_type.value,\n                'training_metrics': self._training_metrics\n            }\n            \n            torch.save(checkpoint, model_path)\n            logger.info(f\"成功保存 DQN 模型: {model_path}\")\n            return True\n            \n        except Exception as e:\n            logger.error(f\"保存模型失敗: {e}\")\n            return False\n    \n    def get_hyperparameters(self) -> Dict[str, Any]:\n        \"\"\"獲取當前超參數\"\"\"\n        return {\n            'learning_rate': self.learning_rate,\n            'batch_size': self.batch_size,\n            'gamma': self.gamma,\n            'epsilon': self.epsilon,\n            'epsilon_min': self.epsilon_min,\n            'epsilon_decay': self.epsilon_decay,\n            'target_update_freq': self.target_update_freq,\n            'memory_size': self.memory_size,\n            'hidden_layers': self.hidden_layers\n        }\n    \n    def set_hyperparameters(self, params: Dict[str, Any]) -> bool:\n        \"\"\"設定超參數\"\"\"\n        try:\n            for key, value in params.items():\n                if hasattr(self, key):\n                    setattr(self, key, value)\n                    logger.debug(f\"更新超參數: {key} = {value}\")\n            return True\n        except Exception as e:\n            logger.error(f\"設定超參數失敗: {e}\")\n            return False\n    \n    def get_training_metrics(self) -> Dict[str, Any]:\n        \"\"\"獲取訓練指標\"\"\"\n        return self._training_metrics.copy()\n    \n    def is_trained(self) -> bool:\n        \"\"\"檢查模型是否已訓練\"\"\"\n        return self._is_trained\n    \n    def get_memory_usage(self) -> Dict[str, float]:\n        \"\"\"獲取記憶體使用量\"\"\"\n        return {\n            'total_mb': self._get_memory_usage_mb(),\n            'network_params': sum(p.numel() for p in self.q_network.parameters()) * 4 / 1024 / 1024,  # 假設 float32\n            'experience_replay_mb': len(self.memory) * self.state_dim * 4 / 1024 / 1024\n        }\n    \n    def _get_memory_usage_mb(self) -> float:\n        \"\"\"獲取總記憶體使用量 (MB)\"\"\"\n        import psutil\n        import os\n        process = psutil.Process(os.getpid())\n        return process.memory_info().rss / 1024 / 1024\n    \n    def validate_scenario(self, scenario: ScenarioType) -> bool:\n        \"\"\"驗證場景是否支援\"\"\"\n        return scenario in self.get_supported_scenarios()\n    \n    def add_training_observer(self, observer: ITrainingObserver) -> None:\n        \"\"\"添加訓練觀察者\"\"\"\n        self._observers.append(observer)\n    \n    def remove_training_observer(self, observer: ITrainingObserver) -> None:\n        \"\"\"移除訓練觀察者\"\"\"\n        if observer in self._observers:\n            self._observers.remove(observer)"