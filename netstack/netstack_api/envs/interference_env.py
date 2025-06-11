"""
干擾緩解 Gymnasium 環境

包裝現有的 AIRANAntiInterferenceService 為標準 RL 環境
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Any, Optional
import asyncio
from datetime import datetime

class InterferenceMitigationEnv(gym.Env):
    """干擾緩解環境"""
    
    metadata = {'render_modes': ['human', 'rgb_array']}
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        
        self.config = config or {}
        
        # 狀態空間：[SINR, 干擾功率, 位置座標, 頻率使用情況]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(20,),  # 20維狀態向量
            dtype=np.float32
        )
        
        # 行動空間：[功率控制, 頻率選擇, 波束方向, 展頻參數]
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(4,),  # 4維連續行動
            dtype=np.float32
        )
        
        # 環境狀態
        self.current_step = 0
        self.max_steps = self.config.get('max_steps', 1000)
        self.interference_level = 0.0
        self.target_sinr = self.config.get('target_sinr', 20.0)  # dB
        
        # 性能指標
        self.episode_rewards = []
        self.interference_history = []
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """重置環境"""
        super().reset(seed=seed)
        
        self.current_step = 0
        self.interference_level = np.random.uniform(0.1, 0.8)
        
        # 初始化網路狀態
        initial_state = self._generate_initial_state()
        
        info = {
            'episode': len(self.episode_rewards),
            'interference_level': self.interference_level,
            'timestamp': datetime.now().isoformat()
        }
        
        return initial_state, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """執行行動"""
        self.current_step += 1
        
        # 解析行動
        power_control = action[0]      # [-1, 1] -> [0.1, 1.0] 功率比例
        frequency_selection = action[1] # [-1, 1] -> 頻率選擇
        beam_direction = action[2]     # [-1, 1] -> 波束方向
        spread_factor = action[3]      # [-1, 1] -> 展頻參數
        
        # 執行干擾緩解行動
        mitigation_result = self._apply_mitigation_action(action)
        
        # 計算獎勵
        reward = self._calculate_reward(mitigation_result)
        
        # 更新狀態
        next_state = self._update_state(mitigation_result)
        
        # 檢查終止條件
        terminated = self._is_terminated()
        truncated = self.current_step >= self.max_steps
        
        # 收集資訊
        info = {
            'sinr_improvement': mitigation_result.get('sinr_improvement', 0),
            'interference_reduction': mitigation_result.get('interference_reduction', 0),
            'power_efficiency': mitigation_result.get('power_efficiency', 0),
            'step': self.current_step,
            'action_taken': {
                'power_control': power_control,
                'frequency_selection': frequency_selection,
                'beam_direction': beam_direction,
                'spread_factor': spread_factor
            }
        }
        
        return next_state, reward, terminated, truncated, info
    
    def _generate_initial_state(self) -> np.ndarray:
        """生成初始狀態"""
        state = np.zeros(20, dtype=np.float32)
        
        # SINR 相關 (0-4)
        state[0] = np.random.uniform(5, 15)    # 當前 SINR (dB)
        state[1] = np.random.uniform(0, 10)    # 干擾功率 (dBm)
        state[2] = np.random.uniform(0, 1)     # 信號品質指標
        state[3] = np.random.uniform(0, 1)     # 頻譜效率
        state[4] = np.random.uniform(0, 1)     # 連接穩定性
        
        # 位置資訊 (5-9)
        state[5:7] = np.random.uniform(-1, 1, 2)  # UE 相對位置
        state[7:9] = np.random.uniform(-1, 1, 2)  # 干擾源位置
        state[9] = np.random.uniform(0, 1)        # 距離歸一化
        
        # 頻率使用情況 (10-14)
        state[10:15] = np.random.uniform(0, 1, 5)  # 5個頻段使用率
        
        # 系統狀態 (15-19)
        state[15] = np.random.uniform(0, 1)    # 系統負載
        state[16] = np.random.uniform(0, 1)    # 電池電量
        state[17] = np.random.uniform(0, 1)    # 網路壅塞
        state[18] = np.random.uniform(0, 1)    # 移動速度
        state[19] = self.interference_level    # 當前干擾水平
        
        return state
    
    def _apply_mitigation_action(self, action: np.ndarray) -> Dict[str, float]:
        """模擬干擾緩解行動的效果"""
        
        power_control = (action[0] + 1) / 2 * 0.9 + 0.1  # [0.1, 1.0]
        frequency_selection = action[1]
        beam_direction = action[2] 
        spread_factor = (action[3] + 1) / 2  # [0, 1]
        
        # 模擬 SINR 改善
        sinr_improvement = 0
        
        # 功率控制效果
        if power_control > 0.7:
            sinr_improvement += 2.0  # 高功率提升信號
        elif power_control < 0.3:
            sinr_improvement -= 1.0  # 低功率節能但信號弱
        
        # 頻率選擇效果
        if abs(frequency_selection) < 0.3:  # 選擇干淨頻段
            sinr_improvement += 3.0
        
        # 波束成形效果  
        if abs(beam_direction) > 0.5:  # 積極波束調整
            sinr_improvement += 1.5
        
        # 展頻效果
        if spread_factor > 0.6:  # 高展頻比
            sinr_improvement += 1.0
        
        # 添加隨機性
        sinr_improvement += np.random.normal(0, 0.5)
        
        # 計算干擾減少
        interference_reduction = max(0, sinr_improvement * 0.1)
        
        # 計算功率效率
        power_efficiency = 1.0 - power_control + 0.1
        
        return {
            'sinr_improvement': sinr_improvement,
            'interference_reduction': interference_reduction, 
            'power_efficiency': power_efficiency
        }
    
    def _calculate_reward(self, mitigation_result: Dict[str, float]) -> float:
        """計算獎勵函數"""
        
        sinr_improvement = mitigation_result['sinr_improvement']
        interference_reduction = mitigation_result['interference_reduction']
        power_efficiency = mitigation_result['power_efficiency']
        
        # 主要獎勵：SINR 改善
        reward = sinr_improvement * 2.0
        
        # 干擾減少獎勵
        reward += interference_reduction * 10.0
        
        # 功率效率獎勵
        reward += power_efficiency * 1.0
        
        # 達到目標 SINR 的額外獎勵
        current_sinr = 10 + sinr_improvement  # 假設基準 SINR 10dB
        if current_sinr >= self.target_sinr:
            reward += 5.0
        
        # 懲罰過度功率使用
        if power_efficiency < 0.3:
            reward -= 2.0
        
        return float(reward)
    
    def _update_state(self, mitigation_result: Dict[str, float]) -> np.ndarray:
        """更新環境狀態"""
        
        # 獲取當前狀態
        state = self._generate_initial_state()
        
        # 應用緩解效果
        sinr_improvement = mitigation_result['sinr_improvement']
        interference_reduction = mitigation_result['interference_reduction']
        
        # 更新 SINR
        state[0] += sinr_improvement
        state[0] = np.clip(state[0], 0, 40)  # 限制在合理範圍
        
        # 更新干擾水平
        self.interference_level *= (1 - interference_reduction)
        self.interference_level = np.clip(self.interference_level, 0.01, 1.0)
        state[19] = self.interference_level
        
        # 添加時間演化
        state[15] += np.random.normal(0, 0.1)  # 系統負載變化
        state[16] -= 0.01  # 電池消耗
        
        return np.clip(state, -10, 10)  # 防止數值爆炸
    
    def _is_terminated(self) -> bool:
        """檢查是否終止"""
        
        # 如果達到目標性能
        if self.interference_level < 0.1:
            return True
            
        # 如果干擾過於嚴重
        if self.interference_level > 0.9:
            return True
            
        return False
    
    def render(self, mode='human'):
        """渲染環境（可選）"""
        if mode == 'human':
            print(f"Step: {self.current_step}")
            print(f"Interference Level: {self.interference_level:.3f}")
            print(f"Episode Rewards: {sum(self.episode_rewards[-10:]) if self.episode_rewards else 0:.2f}")
        
    def close(self):
        """清理資源"""
        pass