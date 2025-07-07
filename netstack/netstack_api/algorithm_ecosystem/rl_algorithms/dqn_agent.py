"""
🤖 DQN 換手智能體

基於深度 Q 網路 (Deep Q-Network) 的衛星換手決策算法。
"""

import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from .base_rl_algorithm import BaseRLHandoverAlgorithm
from ..interfaces import HandoverContext, HandoverDecision, AlgorithmInfo

logger = logging.getLogger(__name__)


class DQNNetwork(nn.Module):
    """DQN 神經網路架構"""
    
    def __init__(self, input_dim: int, hidden_dim: int = 256, output_dim: int = 11):
        """初始化 DQN 網路
        
        Args:
            input_dim: 輸入維度
            hidden_dim: 隱藏層維度
            output_dim: 輸出維度 (動作空間大小)
        """
        super(DQNNetwork, self).__init__()
        
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )
        
        # 決策頭：輸出動作 Q 值
        self.decision_head = nn.Sequential(
            nn.Linear(hidden_dim // 2, output_dim),
            nn.Softmax(dim=-1)  # 用於概率輸出
        )
        
        # 初始化權重
        self._initialize_weights()
    
    def _initialize_weights(self):
        """初始化網路權重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向傳播
        
        Args:
            x: 輸入張量
            
        Returns:
            torch.Tensor: Q 值輸出
        """
        features = self.feature_extractor(x)
        q_values = self.decision_head(features)
        return q_values


class DQNHandoverAgent(BaseRLHandoverAlgorithm):
    """DQN 換手智能體
    
    實現基於 DQN 的衛星換手決策算法，包括：
    - 經驗回放機制
    - 目標網路更新
    - ε-貪婪探索策略
    - 優先經驗回放 (可選)
    """
    
    def __init__(self, name: str = "dqn_handover", config: Optional[Dict[str, Any]] = None):
        """初始化 DQN 智能體
        
        Args:
            name: 算法名稱
            config: 算法配置
        """
        super().__init__(name, config)
        
        # DQN 特定配置
        self.hidden_dim = self.training_config.get('hidden_dim', 256)
        self.learning_rate = self.training_config.get('learning_rate', 0.0001)
        self.epsilon = self.training_config.get('epsilon_start', 1.0)
        self.epsilon_min = self.training_config.get('epsilon_min', 0.01)
        self.epsilon_decay = self.training_config.get('epsilon_decay', 0.995)
        self.target_update_frequency = self.training_config.get('target_update_frequency', 1000)
        self.batch_size = self.training_config.get('batch_size', 64)
        self.memory_size = self.training_config.get('memory_size', 100000)
        
        # 推理配置
        self.temperature = self.inference_config.get('temperature', 0.1)
        self.use_exploration = self.inference_config.get('use_exploration', False)
        
        # 網路和優化器
        self.target_network: Optional[DQNNetwork] = None
        self.optimizer: Optional[optim.Adam] = None
        self.loss_fn = nn.MSELoss()
        
        # 經驗回放
        self.memory = []
        self.memory_idx = 0
        
        # 訓練統計
        self.training_step = 0
        self.target_update_count = 0
        
        logger.info(f"DQN 智能體 '{name}' 初始化完成")
    
    async def _create_model(self) -> None:
        """創建 DQN 模型"""
        try:
            self.model = DQNNetwork(
                input_dim=self.observation_dim,
                hidden_dim=self.hidden_dim,
                output_dim=self.action_dim
            ).to(self.device)
            
            # 創建目標網路
            self.target_network = DQNNetwork(
                input_dim=self.observation_dim,
                hidden_dim=self.hidden_dim,
                output_dim=self.action_dim
            ).to(self.device)
            
            # 初始化目標網路
            self._update_target_network()
            
            # 設置優化器
            self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
            
            logger.info(f"DQN 模型創建完成，參數量: {sum(p.numel() for p in self.model.parameters())}")
            
        except Exception as e:
            logger.error(f"DQN 模型創建失敗: {e}")
            raise
    
    async def _forward_pass(self, observation: torch.Tensor) -> torch.Tensor:
        """DQN 前向傳播
        
        Args:
            observation: 觀察張量
            
        Returns:
            torch.Tensor: 決策輸出
        """
        self.model.eval()
        with torch.no_grad():
            q_values = self.model(observation)
            
            if self.use_exploration and self.training:
                # 訓練時使用 ε-貪婪策略
                if np.random.random() < self.epsilon:
                    # 隨機動作
                    action_probs = torch.ones_like(q_values) / q_values.size(-1)
                else:
                    # 貪婪動作
                    action_probs = q_values
            else:
                # 推理時使用溫度軟最大化
                action_probs = torch.softmax(q_values / self.temperature, dim=-1)
            
            # 轉換為決策格式：[no_handover, immediate_handover, prepare_handover, satellite_probs...]
            decision_tensor = self._q_values_to_decision(action_probs)
            
            return decision_tensor
    
    def _q_values_to_decision(self, q_values: torch.Tensor) -> torch.Tensor:
        """將 Q 值轉換為決策格式
        
        Args:
            q_values: Q 值張量 [batch_size, action_dim]
            
        Returns:
            torch.Tensor: 決策張量 [batch_size, decision_dim]
        """
        batch_size = q_values.size(0)
        decision_dim = 3 + 8  # 3 個決策類型 + 8 個候選衛星概率
        
        decision_tensor = torch.zeros(batch_size, decision_dim).to(self.device)
        
        # 前 3 個動作對應決策類型
        decision_tensor[:, :3] = q_values[:, :3]
        
        # 後面的動作對應衛星選擇概率
        if q_values.size(1) > 3:
            # 歸一化衛星選擇概率
            satellite_probs = torch.softmax(q_values[:, 3:], dim=-1)
            decision_tensor[:, 3:3+satellite_probs.size(1)] = satellite_probs
        
        return decision_tensor
    
    def _update_target_network(self) -> None:
        """更新目標網路"""
        if self.target_network is not None:
            self.target_network.load_state_dict(self.model.state_dict())
            self.target_update_count += 1
            logger.debug(f"目標網路更新 #{self.target_update_count}")
    
    def store_experience(self, state: torch.Tensor, action: int, reward: float, 
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
        """執行一步訓練
        
        Returns:
            Dict[str, float]: 訓練指標
        """
        if len(self.memory) < self.batch_size:
            return {'loss': 0.0, 'q_mean': 0.0}
        
        try:
            # 採樣批次經驗
            batch = self._sample_batch()
            states, actions, rewards, next_states, dones = zip(*batch)
            
            # 轉換為張量
            states = torch.stack(states).to(self.device)
            actions = torch.tensor(actions, dtype=torch.long).to(self.device)
            rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
            next_states = torch.stack(next_states).to(self.device)
            dones = torch.tensor(dones, dtype=torch.bool).to(self.device)
            
            # 計算當前 Q 值
            current_q_values = self.model(states).gather(1, actions.unsqueeze(1))
            
            # 計算目標 Q 值
            with torch.no_grad():
                next_q_values = self.target_network(next_states).max(1)[0]
                target_q_values = rewards + (0.99 * next_q_values * ~dones)
            
            # 計算損失
            loss = self.loss_fn(current_q_values.squeeze(), target_q_values)
            
            # 反向傳播
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            
            # 更新統計
            self.training_step += 1
            
            # 更新目標網路
            if self.training_step % self.target_update_frequency == 0:
                self._update_target_network()
            
            # 衰減探索率
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            
            # 更新統計信息
            self._rl_statistics['training_episodes'] = self.training_step
            
            return {
                'loss': loss.item(),
                'q_mean': current_q_values.mean().item(),
                'epsilon': self.epsilon,
                'target_updates': self.target_update_count
            }
            
        except Exception as e:
            logger.error(f"DQN 訓練步驟失敗: {e}")
            return {'loss': float('inf'), 'q_mean': 0.0}
    
    def _sample_batch(self) -> list:
        """從經驗回放中採樣批次
        
        Returns:
            list: 採樣的經驗批次
        """
        indices = np.random.choice(len(self.memory), self.batch_size, replace=False)
        return [self.memory[idx] for idx in indices]
    
    def get_algorithm_info(self) -> AlgorithmInfo:
        """獲取 DQN 算法信息"""
        base_info = super().get_algorithm_info()
        
        # 添加 DQN 特定信息
        base_info.description = "深度 Q 網路換手智能體 - 基於價值函數的強化學習算法"
        base_info.parameters.update({
            'learning_rate': self.learning_rate,
            'epsilon': self.epsilon,
            'hidden_dim': self.hidden_dim,
            'memory_size': self.memory_size,
            'target_update_frequency': self.target_update_frequency,
            'training_step': self.training_step
        })
        
        return base_info
    
    def get_training_info(self) -> Dict[str, Any]:
        """獲取訓練相關信息
        
        Returns:
            Dict[str, Any]: 訓練信息
        """
        return {
            'algorithm_type': 'DQN',
            'training_step': self.training_step,
            'epsilon': self.epsilon,
            'memory_size': len(self.memory),
            'target_update_count': self.target_update_count,
            'learning_rate': self.learning_rate,
            'model_parameters': sum(p.numel() for p in self.model.parameters()) if self.model else 0,
            'device': str(self.device),
            'is_training': self.training
        }