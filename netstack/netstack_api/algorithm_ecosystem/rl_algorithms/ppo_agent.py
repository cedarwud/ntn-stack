"""
🤖 PPO 換手智能體

基於近端策略優化 (Proximal Policy Optimization) 的衛星換手決策算法。
"""

import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .base_rl_algorithm import BaseRLHandoverAlgorithm
from ..interfaces import HandoverContext, HandoverDecision, AlgorithmInfo

logger = logging.getLogger(__name__)


class PPONetwork(nn.Module):
    """PPO 演員-評論家網路架構"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 256, action_dim: int = 11):
        """初始化 PPO 網路
        
        Args:
            input_dim: 輸入維度
            hidden_dim: 隱藏層維度
            action_dim: 動作空間大小
        """
        super(PPONetwork, self).__init__()
        
        # 共享特徵提取器
        self.shared_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # 演員網路 (策略網路)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # 評論家網路 (價值網路)
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化網路權重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
                nn.init.constant_(module.bias, 0)
        
        # 策略網路最後一層使用較小的權重
        nn.init.orthogonal_(self.actor[-2].weight, gain=0.01)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向傳播
        
        Args:
            x: 輸入張量
            
        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (動作概率, 狀態價值)
        """
        shared_features = self.shared_layers(x)
        action_probs = self.actor(shared_features)
        state_values = self.critic(shared_features)
        return action_probs, state_values
    
    def get_action_and_value(self, x: torch.Tensor, action: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """獲取動作和價值（用於訓練）
        
        Args:
            x: 狀態張量
            action: 採取的動作 (可選，用於計算對數概率)
            
        Returns:
            Tuple: (採樣動作, 對數概率, 熵, 狀態價值)
        """
        action_probs, state_values = self.forward(x)
        
        # 創建動作分佈
        dist = torch.distributions.Categorical(action_probs)
        
        if action is None:
            action = dist.sample()
        
        log_probs = dist.log_prob(action)
        entropy = dist.entropy()
        
        return action, log_probs, entropy, state_values.squeeze(-1)


class PPOHandoverAgent(BaseRLHandoverAlgorithm):
    """PPO 換手智能體
    
    實現基於 PPO 的衛星換手決策算法，包括：
    - 演員-評論家架構
    - 剪切目標函數
    - 廣義優勢估計 (GAE)
    - 價值函數學習
    """
    
    def __init__(self, name: str = "ppo_handover", config: Optional[Dict[str, Any]] = None):
        """初始化 PPO 智能體
        
        Args:
            name: 算法名稱
            config: 算法配置
        """
        super().__init__(name, config)
        
        # PPO 特定配置
        self.hidden_dim = self.training_config.get('hidden_dim', 256)
        self.learning_rate = self.training_config.get('learning_rate', 0.0003)
        self.clip_epsilon = self.training_config.get('clip_epsilon', 0.2)
        self.value_coefficient = self.training_config.get('value_coefficient', 0.5)
        self.entropy_coefficient = self.training_config.get('entropy_coefficient', 0.01)
        self.batch_size = self.training_config.get('batch_size', 256)
        self.minibatch_size = self.training_config.get('minibatch_size', 64)
        self.epochs_per_update = self.training_config.get('epochs_per_update', 4)
        self.gamma = self.training_config.get('gamma', 0.99)
        self.gae_lambda = self.training_config.get('gae_lambda', 0.95)
        self.max_grad_norm = self.training_config.get('max_grad_norm', 0.5)
        
        # 推理配置
        self.temperature = self.inference_config.get('temperature', 1.0)
        
        # 優化器
        self.optimizer: Optional[optim.Adam] = None
        
        # 經驗緩衝區
        self.rollout_buffer = []
        self.episode_rewards = []
        
        # 訓練統計
        self.update_count = 0
        self.total_timesteps = 0
        
        logger.info(f"PPO 智能體 '{name}' 初始化完成")
    
    async def _create_model(self) -> None:
        """創建 PPO 模型"""
        try:
            self.model = PPONetwork(
                input_dim=self.observation_dim,
                hidden_dim=self.hidden_dim,
                action_dim=self.action_dim
            ).to(self.device)
            
            # 設置優化器
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate, eps=1e-5)
            
            logger.info(f"PPO 模型創建完成，參數量: {sum(p.numel() for p in self.model.parameters())}")
            
        except Exception as e:
            logger.error(f"PPO 模型創建失敗: {e}")
            raise
    
    async def _forward_pass(self, observation: torch.Tensor) -> torch.Tensor:
        """PPO 前向傳播
        
        Args:
            observation: 觀察張量
            
        Returns:
            torch.Tensor: 決策輸出
        """
        self.model.eval()
        with torch.no_grad():
            action_probs, _ = self.model(observation)
            
            # 應用溫度縮放
            if self.temperature != 1.0:
                action_probs = torch.pow(action_probs, 1.0 / self.temperature)
                action_probs = action_probs / action_probs.sum(dim=-1, keepdim=True)
            
            # 轉換為決策格式
            decision_tensor = self._action_probs_to_decision(action_probs)
            
            return decision_tensor
    
    def _action_probs_to_decision(self, action_probs: torch.Tensor) -> torch.Tensor:
        """將動作概率轉換為決策格式
        
        Args:
            action_probs: 動作概率張量 [batch_size, action_dim]
            
        Returns:
            torch.Tensor: 決策張量 [batch_size, decision_dim]
        """
        batch_size = action_probs.size(0)
        decision_dim = 3 + 8  # 3 個決策類型 + 8 個候選衛星概率
        
        decision_tensor = torch.zeros(batch_size, decision_dim).to(self.device)
        
        # 前 3 個動作對應決策類型
        decision_tensor[:, :3] = action_probs[:, :3]
        
        # 後面的動作對應衛星選擇概率
        if action_probs.size(1) > 3:
            decision_tensor[:, 3:3+min(8, action_probs.size(1)-3)] = action_probs[:, 3:3+min(8, action_probs.size(1)-3)]
        
        return decision_tensor
    
    def store_experience(self, state: torch.Tensor, action: int, reward: float, 
                        log_prob: float, value: float, done: bool) -> None:
        """存儲經驗到回放緩衝區
        
        Args:
            state: 當前狀態
            action: 採取的動作
            reward: 獲得的獎勵
            log_prob: 動作對數概率
            value: 狀態價值
            done: 是否結束
        """
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'log_prob': log_prob,
            'value': value,
            'done': done
        }
        
        self.rollout_buffer.append(experience)
        self.total_timesteps += 1
    
    def compute_gae(self, rewards: List[float], values: List[float], 
                   dones: List[bool], next_value: float = 0.0) -> Tuple[List[float], List[float]]:
        """計算廣義優勢估計 (GAE)
        
        Args:
            rewards: 獎勵列表
            values: 價值列表
            dones: 結束標誌列表
            next_value: 下一個狀態的價值
            
        Returns:
            Tuple[List[float], List[float]]: (優勢, 回報)
        """
        advantages = []
        returns = []
        
        gae = 0
        next_value = next_value
        
        for step in reversed(range(len(rewards))):
            if step == len(rewards) - 1:
                next_non_terminal = 1.0 - dones[step]
                next_values = next_value
            else:
                next_non_terminal = 1.0 - dones[step]
                next_values = values[step + 1]
            
            delta = rewards[step] + self.gamma * next_values * next_non_terminal - values[step]
            gae = delta + self.gamma * self.gae_lambda * next_non_terminal * gae
            
            advantages.insert(0, gae)
            returns.insert(0, gae + values[step])
        
        return advantages, returns
    
    async def train_step(self) -> Dict[str, float]:
        """執行 PPO 訓練更新
        
        Returns:
            Dict[str, float]: 訓練指標
        """
        if len(self.rollout_buffer) < self.batch_size:
            return {'policy_loss': 0.0, 'value_loss': 0.0, 'entropy_loss': 0.0}
        
        try:
            # 準備訓練數據
            states = torch.stack([exp['state'] for exp in self.rollout_buffer]).to(self.device)
            actions = torch.tensor([exp['action'] for exp in self.rollout_buffer], dtype=torch.long).to(self.device)
            old_log_probs = torch.tensor([exp['log_prob'] for exp in self.rollout_buffer], dtype=torch.float32).to(self.device)
            rewards = [exp['reward'] for exp in self.rollout_buffer]
            values = [exp['value'] for exp in self.rollout_buffer]
            dones = [exp['done'] for exp in self.rollout_buffer]
            
            # 計算優勢和回報
            advantages, returns = self.compute_gae(rewards, values, dones)
            advantages = torch.tensor(advantages, dtype=torch.float32).to(self.device)
            returns = torch.tensor(returns, dtype=torch.float32).to(self.device)
            
            # 正規化優勢
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
            
            # 多輪訓練
            total_policy_loss = 0.0
            total_value_loss = 0.0
            total_entropy_loss = 0.0
            
            for epoch in range(self.epochs_per_update):
                # 隨機排列數據
                indices = torch.randperm(len(self.rollout_buffer))
                
                for start in range(0, len(self.rollout_buffer), self.minibatch_size):
                    end = start + self.minibatch_size
                    minibatch_indices = indices[start:end]
                    
                    # 獲取小批次數據
                    mb_states = states[minibatch_indices]
                    mb_actions = actions[minibatch_indices]
                    mb_old_log_probs = old_log_probs[minibatch_indices]
                    mb_advantages = advantages[minibatch_indices]
                    mb_returns = returns[minibatch_indices]
                    
                    # 前向傳播
                    _, new_log_probs, entropy, new_values = self.model.get_action_and_value(mb_states, mb_actions)
                    
                    # 計算策略損失
                    ratio = torch.exp(new_log_probs - mb_old_log_probs)
                    surr1 = ratio * mb_advantages
                    surr2 = torch.clamp(ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon) * mb_advantages
                    policy_loss = -torch.min(surr1, surr2).mean()
                    
                    # 計算價值損失
                    value_loss = nn.MSELoss()(new_values, mb_returns)
                    
                    # 計算熵損失
                    entropy_loss = -entropy.mean()
                    
                    # 總損失
                    total_loss = policy_loss + self.value_coefficient * value_loss + self.entropy_coefficient * entropy_loss
                    
                    # 反向傳播
                    self.optimizer.zero_grad()
                    total_loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.max_grad_norm)
                    self.optimizer.step()
                    
                    total_policy_loss += policy_loss.item()
                    total_value_loss += value_loss.item()
                    total_entropy_loss += entropy_loss.item()
            
            # 清空緩衝區
            self.rollout_buffer.clear()
            self.update_count += 1
            
            # 更新統計信息
            self._rl_statistics['training_episodes'] = self.update_count
            
            num_updates = self.epochs_per_update * (len(states) // self.minibatch_size)
            
            return {
                'policy_loss': total_policy_loss / num_updates,
                'value_loss': total_value_loss / num_updates,
                'entropy_loss': total_entropy_loss / num_updates,
                'total_timesteps': self.total_timesteps,
                'update_count': self.update_count
            }
            
        except Exception as e:
            logger.error(f"PPO 訓練步驟失敗: {e}")
            return {'policy_loss': float('inf'), 'value_loss': float('inf'), 'entropy_loss': float('inf')}
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取 PPO 算法信息"""
        base_info = super().get_algorithm_info()
        
        # 添加 PPO 特定信息
        base_info.description = "近端策略優化換手智能體 - 基於策略梯度的強化學習算法"
        base_info.parameters.update({
            'learning_rate': self.learning_rate,
            'clip_epsilon': self.clip_epsilon,
            'value_coefficient': self.value_coefficient,
            'entropy_coefficient': self.entropy_coefficient,
            'hidden_dim': self.hidden_dim,
            'gamma': self.gamma,
            'gae_lambda': self.gae_lambda,
            'update_count': self.update_count,
            'total_timesteps': self.total_timesteps
        })
        
        return base_info
    
    def get_training_info(self) -> Dict[str, Any]:
        """獲取訓練相關信息
        
        Returns:
            Dict[str, Any]: 訓練信息
        """
        return {
            'algorithm_type': 'PPO',
            'update_count': self.update_count,
            'total_timesteps': self.total_timesteps,
            'buffer_size': len(self.rollout_buffer),
            'learning_rate': self.learning_rate,
            'clip_epsilon': self.clip_epsilon,
            'model_parameters': sum(p.numel() for p in self.model.parameters()) if self.model else 0,
            'device': str(self.device),
            'is_training': self.training
        }