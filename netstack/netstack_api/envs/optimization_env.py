"""
網路優化 Gymnasium 環境

包裝現有的 AutomatedOptimizationService 為標準 RL 環境
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Any, Optional
from datetime import datetime

class NetworkOptimizationEnv(gym.Env):
    """網路優化環境"""
    
    metadata = {'render_modes': ['human', 'rgb_array']}
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        
        self.config = config or {}
        
        # 狀態空間：[吞吐量, 延遲, 丟包率, 資源使用率, 用戶數量等]
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0, 
            shape=(15,),  # 15維正規化狀態
            dtype=np.float32
        )
        
        # 行動空間：[頻寬分配, QoS 參數, 負載均衡, 快取策略]
        self.action_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(6,),  # 6維優化參數
            dtype=np.float32
        )
        
        # 環境參數
        self.current_step = 0
        self.max_steps = self.config.get('max_steps', 500)
        self.target_metrics = {
            'throughput': 0.8,  # 目標吞吐量
            'latency': 0.2,     # 目標延遲（越低越好）
            'packet_loss': 0.1, # 目標丟包率（越低越好）
        }
        
        # 性能歷史
        self.performance_history = []
        self.optimization_history = []
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """重置環境"""
        super().reset(seed=seed)
        
        self.current_step = 0
        
        # 初始化網路狀態（隨機但合理的初始條件）
        initial_state = self._generate_initial_network_state()
        
        info = {
            'episode': len(self.performance_history),
            'timestamp': datetime.now().isoformat(),
            'initial_performance': self._calculate_performance_score(initial_state)
        }
        
        return initial_state, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """執行優化行動"""
        self.current_step += 1
        
        # 應用優化行動
        optimization_result = self._apply_optimization(action)
        
        # 更新網路狀態
        next_state = self._update_network_state(optimization_result)
        
        # 計算獎勵
        reward = self._calculate_optimization_reward(optimization_result, next_state)
        
        # 檢查終止條件
        terminated = self._is_optimization_complete(next_state)
        truncated = self.current_step >= self.max_steps
        
        # 收集詳細資訊
        info = {
            'throughput': next_state[0],
            'latency': next_state[1], 
            'packet_loss': next_state[2],
            'resource_utilization': next_state[3],
            'performance_score': self._calculate_performance_score(next_state),
            'optimization_actions': {
                'bandwidth_allocation': action[0],
                'qos_priority': action[1],
                'load_balancing': action[2],
                'cache_policy': action[3],
                'routing_optimization': action[4],
                'congestion_control': action[5]
            },
            'step': self.current_step
        }
        
        return next_state, reward, terminated, truncated, info
    
    def _generate_initial_network_state(self) -> np.ndarray:
        """生成初始網路狀態"""
        state = np.zeros(15, dtype=np.float32)
        
        # 核心性能指標 (0-4)
        state[0] = np.random.uniform(0.3, 0.7)    # 吞吐量
        state[1] = np.random.uniform(0.3, 0.8)    # 延遲（正規化，越低越好）
        state[2] = np.random.uniform(0.1, 0.5)    # 丟包率（正規化，越低越好）
        state[3] = np.random.uniform(0.4, 0.9)    # 資源使用率
        state[4] = np.random.uniform(0.2, 0.8)    # 網路壅塞程度
        
        # 用戶與流量 (5-9)
        state[5] = np.random.uniform(0.3, 0.9)    # 活躍用戶數量（正規化）
        state[6] = np.random.uniform(0.2, 0.8)    # 平均數據流量
        state[7] = np.random.uniform(0.1, 0.7)    # 高優先級流量比例
        state[8] = np.random.uniform(0.0, 0.5)    # 緊急流量比例
        state[9] = np.random.uniform(0.3, 0.8)    # 流量分布均勻度
        
        # 系統資源 (10-14)
        state[10] = np.random.uniform(0.4, 0.9)   # CPU 使用率
        state[11] = np.random.uniform(0.3, 0.8)   # 記憶體使用率
        state[12] = np.random.uniform(0.2, 0.7)   # 頻寬使用率
        state[13] = np.random.uniform(0.1, 0.6)   # 儲存使用率
        state[14] = np.random.uniform(0.5, 1.0)   # 系統健康度
        
        return state
    
    def _apply_optimization(self, action: np.ndarray) -> Dict[str, float]:
        """應用優化策略"""
        
        bandwidth_allocation = action[0]    # 頻寬分配策略
        qos_priority = action[1]           # QoS 優先級設定
        load_balancing = action[2]         # 負載均衡強度
        cache_policy = action[3]           # 快取策略
        routing_optimization = action[4]    # 路由優化
        congestion_control = action[5]     # 壅塞控制
        
        # 計算各項優化效果
        optimization_effects = {}
        
        # 頻寬分配效果
        if bandwidth_allocation > 0.7:
            optimization_effects['throughput_improvement'] = 0.1
            optimization_effects['latency_reduction'] = 0.05
        elif bandwidth_allocation < 0.3:
            optimization_effects['throughput_improvement'] = -0.05
            optimization_effects['resource_efficiency'] = 0.1
        else:
            optimization_effects['throughput_improvement'] = bandwidth_allocation * 0.05
        
        # QoS 優化效果
        if qos_priority > 0.6:
            optimization_effects['latency_reduction'] = qos_priority * 0.08
            optimization_effects['packet_loss_reduction'] = qos_priority * 0.06
        
        # 負載均衡效果
        if load_balancing > 0.5:
            optimization_effects['resource_balance'] = load_balancing * 0.1
            optimization_effects['system_stability'] = load_balancing * 0.05
        
        # 快取策略效果
        if cache_policy > 0.4:
            optimization_effects['response_time_improvement'] = cache_policy * 0.07
            optimization_effects['bandwidth_saving'] = cache_policy * 0.05
        
        # 路由優化效果
        if routing_optimization > 0.6:
            optimization_effects['latency_reduction'] = (optimization_effects.get('latency_reduction', 0) + 
                                                       routing_optimization * 0.06)
        
        # 壅塞控制效果
        if congestion_control > 0.5:
            optimization_effects['packet_loss_reduction'] = (optimization_effects.get('packet_loss_reduction', 0) + 
                                                           congestion_control * 0.08)
        
        # 添加隨機性和相互影響
        for key in optimization_effects:
            optimization_effects[key] += np.random.normal(0, 0.01)
        
        return optimization_effects
    
    def _update_network_state(self, optimization_effects: Dict[str, float]) -> np.ndarray:
        """根據優化效果更新網路狀態"""
        
        # 重新生成基礎狀態（模擬網路動態變化）
        state = self._generate_initial_network_state()
        
        # 應用優化效果
        
        # 吞吐量改善
        if 'throughput_improvement' in optimization_effects:
            state[0] += optimization_effects['throughput_improvement']
            state[0] = np.clip(state[0], 0, 1)
        
        # 延遲減少
        if 'latency_reduction' in optimization_effects:
            state[1] -= optimization_effects['latency_reduction']
            state[1] = np.clip(state[1], 0, 1)
        
        # 丟包率減少
        if 'packet_loss_reduction' in optimization_effects:
            state[2] -= optimization_effects['packet_loss_reduction']
            state[2] = np.clip(state[2], 0, 1)
        
        # 資源效率改善
        if 'resource_efficiency' in optimization_effects:
            state[3] *= (1 - optimization_effects['resource_efficiency'])
            state[3] = np.clip(state[3], 0, 1)
        
        # 系統穩定性改善
        if 'system_stability' in optimization_effects:
            state[14] += optimization_effects['system_stability']
            state[14] = np.clip(state[14], 0, 1)
        
        # 模擬時間演化和隨機擾動
        state += np.random.normal(0, 0.01, 15)
        state = np.clip(state, 0, 1)
        
        return state
    
    def _calculate_optimization_reward(self, optimization_effects: Dict[str, float], state: np.ndarray) -> float:
        """計算優化獎勵"""
        
        reward = 0.0
        
        # 性能改善獎勵
        throughput = state[0]
        latency = state[1]  # 越低越好
        packet_loss = state[2]  # 越低越好
        
        # 吞吐量獎勵（越高越好）
        reward += (throughput - 0.5) * 10
        
        # 延遲懲罰（越低越好）
        reward -= latency * 8
        
        # 丟包率懲罰（越低越好）
        reward -= packet_loss * 12
        
        # 資源效率獎勵
        resource_utilization = state[3]
        if 0.6 <= resource_utilization <= 0.8:  # 最佳資源使用區間
            reward += 3
        elif resource_utilization > 0.9:  # 過度使用懲罰
            reward -= 5
        
        # 系統穩定性獎勵
        system_health = state[14]
        reward += system_health * 5
        
        # 達到目標的額外獎勵
        if (throughput >= self.target_metrics['throughput'] and
            latency <= self.target_metrics['latency'] and
            packet_loss <= self.target_metrics['packet_loss']):
            reward += 15  # 大幅獎勵
        
        # 優化效果獎勵
        for effect_name, effect_value in optimization_effects.items():
            if 'improvement' in effect_name or 'reduction' in effect_name:
                reward += effect_value * 20
        
        return float(reward)
    
    def _calculate_performance_score(self, state: np.ndarray) -> float:
        """計算整體性能分數"""
        
        throughput = state[0]
        latency = 1 - state[1]  # 轉換為正向指標
        reliability = 1 - state[2]  # 轉換為正向指標
        efficiency = 1 - state[3] if state[3] > 0.8 else state[3]  # 平衡使用率
        
        # 加權平均
        score = (throughput * 0.3 + 
                latency * 0.25 + 
                reliability * 0.25 + 
                efficiency * 0.2)
        
        return float(score)
    
    def _is_optimization_complete(self, state: np.ndarray) -> bool:
        """檢查優化是否完成"""
        
        performance_score = self._calculate_performance_score(state)
        
        # 如果達到高性能標準
        if performance_score >= 0.85:
            return True
        
        # 如果系統穩定且滿足基本要求
        if (state[0] >= self.target_metrics['throughput'] and
            state[1] <= self.target_metrics['latency'] and 
            state[2] <= self.target_metrics['packet_loss'] and
            state[14] >= 0.8):  # 系統健康度
            return True
        
        return False
    
    def render(self, mode='human'):
        """渲染環境狀態"""
        if mode == 'human':
            if hasattr(self, '_last_state'):
                state = self._last_state
                print(f"Step: {self.current_step}")
                print(f"Throughput: {state[0]:.3f}")
                print(f"Latency: {state[1]:.3f}")
                print(f"Packet Loss: {state[2]:.3f}")
                print(f"Performance Score: {self._calculate_performance_score(state):.3f}")
                print("-" * 40)
    
    def close(self):
        """清理資源"""
        pass