"""
🤖 SAC 換手智能體

基於軟演員評論家 (Soft Actor-Critic) 的衛星換手決策算法。
"""

import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .base_rl_algorithm import BaseRLHandoverAlgorithm
from ..interfaces import HandoverContext, HandoverDecision, AlgorithmInfo

logger = logging.getLogger(__name__)


class SACNetwork(nn.Module):
    """SAC 網路基類"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 256):
        """初始化網路
        
        Args:
            input_dim: 輸入維度
            hidden_dim: 隱藏層維度
        """
        super(SACNetwork, self).__init__()
        
        self.shared_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化網路權重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)


class SACCritic(SACNetwork):
    """SAC 評論家網路"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        """初始化評論家網路
        
        Args:
            state_dim: 狀態維度
            action_dim: 動作維度
            hidden_dim: 隱藏層維度
        """
        super(SACCritic, self).__init__(state_dim + action_dim, hidden_dim)
        
        self.q_layer = nn.Linear(hidden_dim, 1)
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """前向傳播
        
        Args:
            state: 狀態張量
            action: 動作張量
            
        Returns:
            torch.Tensor: Q 值
        """
        x = torch.cat([state, action], dim=-1)
        x = self.shared_layers(x)
        q_value = self.q_layer(x)
        return q_value


class SACActor(SACNetwork):
    """SAC 演員網路"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        """初始化演員網路
        
        Args:
            state_dim: 狀態維度
            action_dim: 動作維度
            hidden_dim: 隱藏層維度
        """
        super(SACActor, self).__init__(state_dim, hidden_dim)
        
        self.mean_layer = nn.Linear(hidden_dim, action_dim)
        self.log_std_layer = nn.Linear(hidden_dim, action_dim)
        
        self.min_log_std = -20
        self.max_log_std = 2
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向傳播
        
        Args:
            state: 狀態張量
            
        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (均值, 對數標準差)
        """
        x = self.shared_layers(state)
        mean = self.mean_layer(x)
        log_std = self.log_std_layer(x)
        log_std = torch.clamp(log_std, self.min_log_std, self.max_log_std)
        return mean, log_std
    
    def sample(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """採樣動作
        
        Args:
            state: 狀態張量
            
        Returns:
            Tuple[torch.Tensor, torch.Tensor]: (動作, 對數概率)
        """
        mean, log_std = self.forward(state)
        std = log_std.exp()
        
        # 重參數化技巧
        normal = torch.distributions.Normal(mean, std)
        x_t = normal.rsample()  # 用於反向傳播
        
        # 應用 tanh 激活並計算對數概率
        action = torch.tanh(x_t)
        log_prob = normal.log_prob(x_t)
        
        # 修正 tanh 變換的雅可比行列式
        log_prob -= torch.log(1 - action.pow(2) + 1e-6)
        log_prob = log_prob.sum(dim=-1, keepdim=True)
        
        return action, log_prob


class SACHandoverAgent(BaseRLHandoverAlgorithm):
    """SAC 換手智能體
    
    實現基於 SAC 的衛星換手決策算法，包括：
    - 最大熵強化學習
    - 雙 Q 網路
    - 自動溫度調節
    - 連續動作空間處理
    """
    
    def __init__(self, name: str = "sac_handover", config: Optional[Dict[str, Any]] = None):
        """初始化 SAC 智能體
        
        Args:
            name: 算法名稱
            config: 算法配置
        """
        super().__init__(name, config)
        
        # SAC 特定配置
        self.hidden_dim = self.training_config.get('hidden_dim', 256)
        self.learning_rate = self.training_config.get('learning_rate', 0.0003)
        self.alpha = self.training_config.get('alpha', 0.2)  # 溫度參數
        self.tau = self.training_config.get('tau', 0.005)  # 軟更新係數
        self.gamma = self.training_config.get('gamma', 0.99)
        self.batch_size = self.training_config.get('batch_size', 128)
        self.memory_size = self.training_config.get('memory_size', 100000)
        self.auto_alpha = self.training_config.get('auto_alpha', True)  # 自動調節溫度
        
        # 推理配置
        self.temperature = self.inference_config.get('temperature', 1.0)
        
        # 網路組件
        self.actor: Optional[SACActor] = None
        self.critic1: Optional[SACCritic] = None
        self.critic2: Optional[SACCritic] = None
        self.target_critic1: Optional[SACCritic] = None
        self.target_critic2: Optional[SACCritic] = None
        
        # 優化器
        self.actor_optimizer: Optional[optim.Adam] = None
        self.critic1_optimizer: Optional[optim.Adam] = None
        self.critic2_optimizer: Optional[optim.Adam] = None
        self.alpha_optimizer: Optional[optim.Adam] = None
        
        # 自動溫度調節
        if self.auto_alpha:
            self.target_entropy = -self.action_dim  # 目標熵
            self.log_alpha = torch.zeros(1, requires_grad=True, device=self.device)
        
        # 經驗回放
        self.memory = []
        self.memory_idx = 0
        
        # 訓練統計
        self.training_step = 0
        
        logger.info(f"SAC 智能體 '{name}' 初始化完成")
    
    async def _create_model(self) -> None:
        """創建 SAC 模型"""
        try:
            # 創建網路
            self.actor = SACActor(
                state_dim=self.observation_dim,
                action_dim=self.action_dim,
                hidden_dim=self.hidden_dim
            ).to(self.device)
            
            self.critic1 = SACCritic(
                state_dim=self.observation_dim,
                action_dim=self.action_dim,
                hidden_dim=self.hidden_dim
            ).to(self.device)
            
            self.critic2 = SACCritic(
                state_dim=self.observation_dim,
                action_dim=self.action_dim,
                hidden_dim=self.hidden_dim
            ).to(self.device)
            
            # 創建目標網路
            self.target_critic1 = SACCritic(
                state_dim=self.observation_dim,
                action_dim=self.action_dim,
                hidden_dim=self.hidden_dim
            ).to(self.device)
            
            self.target_critic2 = SACCritic(
                state_dim=self.observation_dim,
                action_dim=self.action_dim,
                hidden_dim=self.hidden_dim
            ).to(self.device)
            
            # 初始化目標網路
            self._soft_update(self.target_critic1, self.critic1, tau=1.0)
            self._soft_update(self.target_critic2, self.critic2, tau=1.0)
            
            # 設置優化器
            self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=self.learning_rate)
            self.critic1_optimizer = optim.Adam(self.critic1.parameters(), lr=self.learning_rate)
            self.critic2_optimizer = optim.Adam(self.critic2.parameters(), lr=self.learning_rate)
            
            if self.auto_alpha:
                self.alpha_optimizer = optim.Adam([self.log_alpha], lr=self.learning_rate)
            
            # 將主要模型設為 actor（用於推理）
            self.model = self.actor
            
            total_params = sum(p.numel() for network in [self.actor, self.critic1, self.critic2] for p in network.parameters())
            logger.info(f"SAC 模型創建完成，總參數量: {total_params}")
            
        except Exception as e:
            logger.error(f"SAC 模型創建失敗: {e}")
            raise
    
    async def _forward_pass(self, observation: torch.Tensor) -> torch.Tensor:
        """SAC 前向傳播
        
        Args:
            observation: 觀察張量
            
        Returns:
            torch.Tensor: 決策輸出
        """
        self.actor.eval()
        with torch.no_grad():
            if self.training:
                # 訓練時採樣動作
                action, _ = self.actor.sample(observation)
            else:
                # 推理時使用確定性動作
                mean, _ = self.actor.forward(observation)
                action = torch.tanh(mean)
            
            # 應用溫度縮放
            if self.temperature != 1.0:
                action = action / self.temperature
            
            # 轉換為決策格式
            decision_tensor = self._action_to_decision(action)
            
            return decision_tensor
    
    def _action_to_decision(self, action: torch.Tensor) -> torch.Tensor:
        """將連續動作轉換為決策格式
        
        Args:
            action: 動作張量 [batch_size, action_dim]
            
        Returns:
            torch.Tensor: 決策張量 [batch_size, decision_dim]
        """
        batch_size = action.size(0)
        decision_dim = 3 + 8  # 3 個決策類型 + 8 個候選衛星概率
        
        decision_tensor = torch.zeros(batch_size, decision_dim).to(self.device)
        
        # 將連續動作轉換為概率分佈
        action_probs = torch.softmax(action, dim=-1)
        
        # 前 3 個對應決策類型
        decision_tensor[:, :3] = action_probs[:, :3]
        
        # 後面的對應衛星選擇
        if action_probs.size(1) > 3:
            decision_tensor[:, 3:3+min(8, action_probs.size(1)-3)] = action_probs[:, 3:3+min(8, action_probs.size(1)-3)]
        
        return decision_tensor
    
    def _soft_update(self, target_network: nn.Module, source_network: nn.Module, tau: float) -> None:
        """軟更新目標網路
        
        Args:
            target_network: 目標網路
            source_network: 源網路
            tau: 更新係數
        """
        for target_param, source_param in zip(target_network.parameters(), source_network.parameters()):
            target_param.data.copy_(tau * source_param.data + (1.0 - tau) * target_param.data)
    
    def store_experience(self, state: torch.Tensor, action: torch.Tensor, reward: float,
                        next_state: torch.Tensor, done: bool) -> None:
        """存儲經驗到回放緩衝區
        
        Args:
            state: 當前狀態
            action: 採取的動作
            reward: 獲得的獎勵
            next_state: 下一個狀態
            done: 是否結束
        """
        experience = (state, action, reward, next_state, done)
        
        if len(self.memory) < self.memory_size:
            self.memory.append(experience)
        else:
            self.memory[self.memory_idx] = experience
            self.memory_idx = (self.memory_idx + 1) % self.memory_size
    
    async def train_step(self) -> Dict[str, float]:
        """執行 SAC 訓練步驟
        
        Returns:
            Dict[str, float]: 訓練指標
        """
        if len(self.memory) < self.batch_size:
            return {'actor_loss': 0.0, 'critic1_loss': 0.0, 'critic2_loss': 0.0, 'alpha_loss': 0.0}
        
        try:
            # 採樣批次經驗
            batch = self._sample_batch()
            states, actions, rewards, next_states, dones = zip(*batch)
            
            # 轉換為張量
            states = torch.stack(states).to(self.device)
            actions = torch.stack(actions).to(self.device)
            rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device).unsqueeze(-1)
            next_states = torch.stack(next_states).to(self.device)
            dones = torch.tensor(dones, dtype=torch.bool).to(self.device).unsqueeze(-1)
            
            # 更新評論家網路
            critic1_loss, critic2_loss = self._update_critics(states, actions, rewards, next_states, dones)
            
            # 更新演員網路
            actor_loss = self._update_actor(states)
            
            # 更新溫度參數
            alpha_loss = 0.0
            if self.auto_alpha:
                alpha_loss = self._update_alpha(states)
            
            # 軟更新目標網路
            self._soft_update(self.target_critic1, self.critic1, self.tau)
            self._soft_update(self.target_critic2, self.critic2, self.tau)
            
            self.training_step += 1
            self._rl_statistics['training_episodes'] = self.training_step
            
            return {
                'actor_loss': actor_loss,
                'critic1_loss': critic1_loss,
                'critic2_loss': critic2_loss,
                'alpha_loss': alpha_loss,
                'alpha': self.alpha if not self.auto_alpha else self.log_alpha.exp().item(),
                'training_step': self.training_step
            }
            
        except Exception as e:
            logger.error(f"SAC 訓練步驟失敗: {e}")
            return {'actor_loss': float('inf'), 'critic1_loss': float('inf'), 'critic2_loss': float('inf'), 'alpha_loss': float('inf')}
    
    def _update_critics(self, states: torch.Tensor, actions: torch.Tensor, rewards: torch.Tensor,
                       next_states: torch.Tensor, dones: torch.Tensor) -> Tuple[float, float]:
        """更新評論家網路"""
        with torch.no_grad():
            next_actions, next_log_probs = self.actor.sample(next_states)
            alpha = self.alpha if not self.auto_alpha else self.log_alpha.exp()
            
            target_q1 = self.target_critic1(next_states, next_actions)
            target_q2 = self.target_critic2(next_states, next_actions)
            target_q = torch.min(target_q1, target_q2) - alpha * next_log_probs
            target_q = rewards + self.gamma * target_q * (~dones)
        
        # 更新 Critic 1
        current_q1 = self.critic1(states, actions)
        critic1_loss = F.mse_loss(current_q1, target_q)
        
        self.critic1_optimizer.zero_grad()
        critic1_loss.backward()
        self.critic1_optimizer.step()
        
        # 更新 Critic 2
        current_q2 = self.critic2(states, actions)
        critic2_loss = F.mse_loss(current_q2, target_q)
        
        self.critic2_optimizer.zero_grad()
        critic2_loss.backward()
        self.critic2_optimizer.step()
        
        return critic1_loss.item(), critic2_loss.item()
    
    def _update_actor(self, states: torch.Tensor) -> float:
        """更新演員網路"""
        actions, log_probs = self.actor.sample(states)
        alpha = self.alpha if not self.auto_alpha else self.log_alpha.exp()
        
        q1 = self.critic1(states, actions)
        q2 = self.critic2(states, actions)
        min_q = torch.min(q1, q2)
        
        actor_loss = (alpha * log_probs - min_q).mean()
        
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()
        
        return actor_loss.item()
    
    def _update_alpha(self, states: torch.Tensor) -> float:
        """更新溫度參數"""
        with torch.no_grad():
            _, log_probs = self.actor.sample(states)
        
        alpha_loss = -(self.log_alpha * (log_probs + self.target_entropy)).mean()
        
        self.alpha_optimizer.zero_grad()
        alpha_loss.backward()
        self.alpha_optimizer.step()
        
        return alpha_loss.item()
    
    def _sample_batch(self) -> list:
        """從經驗回放中採樣批次"""
        indices = np.random.choice(len(self.memory), self.batch_size, replace=False)
        return [self.memory[idx] for idx in indices]
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取 SAC 算法信息"""
        base_info = super().get_algorithm_info()
        
        # 添加 SAC 特定信息
        base_info.description = "軟演員評論家換手智能體 - 基於最大熵的強化學習算法"
        base_info.parameters.update({
            'learning_rate': self.learning_rate,
            'alpha': self.alpha if not self.auto_alpha else self.log_alpha.exp().item(),
            'tau': self.tau,
            'gamma': self.gamma,
            'hidden_dim': self.hidden_dim,
            'auto_alpha': self.auto_alpha,
            'training_step': self.training_step
        })
        
        return base_info
    
    def get_training_info(self) -> Dict[str, Any]:
        """獲取訓練相關信息"""
        return {
            'algorithm_type': 'SAC',
            'training_step': self.training_step,
            'memory_size': len(self.memory),
            'alpha': self.alpha if not self.auto_alpha else self.log_alpha.exp().item(),
            'learning_rate': self.learning_rate,
            'model_parameters': sum(p.numel() for network in [self.actor, self.critic1, self.critic2] for p in network.parameters()) if self.actor else 0,
            'device': str(self.device),
            'is_training': self.training
        }