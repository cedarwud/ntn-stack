"""
UAV 編隊管理 Gymnasium 環境

多智能體 UAV 編隊管理和協調環境
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Dict, Tuple, Any, Optional, List
from datetime import datetime

class UAVFormationEnv(gym.Env):
    """UAV 編隊管理環境"""
    
    metadata = {'render_modes': ['human', 'rgb_array']}
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        
        self.config = config or {}
        self.num_uavs = self.config.get('num_uavs', 4)
        self.formation_type = self.config.get('formation_type', 'diamond')
        
        # 狀態空間：每個 UAV 的位置、速度、電量、信號強度等
        # [x, y, z, vx, vy, vz, battery, signal_strength] * num_uavs + [formation_metrics]
        state_dim = self.num_uavs * 8 + 5  # 每UAV 8維 + 5維編隊指標
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(state_dim,),
            dtype=np.float32
        )
        
        # 行動空間：每個 UAV 的移動指令 [thrust, pitch, yaw, roll]
        action_dim = self.num_uavs * 4
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(action_dim,),
            dtype=np.float32
        )
        
        # 環境參數
        self.current_step = 0
        self.max_steps = self.config.get('max_steps', 2000)
        
        # UAV 初始參數
        self.uav_states = []
        self.formation_center = np.array([0.0, 0.0, 100.0])  # 編隊中心
        self.target_formation = self._get_target_formation()
        
        # 性能指標
        self.formation_quality_history = []
        self.communication_quality_history = []
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """重置環境"""
        super().reset(seed=seed)
        
        self.current_step = 0
        
        # 初始化 UAV 狀態
        self._initialize_uav_states()
        
        # 生成初始觀測
        initial_state = self._get_observation()
        
        info = {
            'episode': len(self.formation_quality_history),
            'num_uavs': self.num_uavs,
            'formation_type': self.formation_type,
            'timestamp': datetime.now().isoformat()
        }
        
        return initial_state, info
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """執行編隊行動"""
        self.current_step += 1
        
        # 解析每個 UAV 的行動
        uav_actions = self._parse_actions(action)
        
        # 更新每個 UAV 的狀態
        formation_result = self._update_uav_states(uav_actions)
        
        # 計算獎勵
        reward = self._calculate_formation_reward(formation_result)
        
        # 生成新的觀測
        next_state = self._get_observation()
        
        # 檢查終止條件
        terminated = self._is_mission_complete()
        truncated = self.current_step >= self.max_steps
        
        # 收集詳細資訊
        info = {
            'formation_quality': formation_result['formation_quality'],
            'communication_quality': formation_result['communication_quality'],
            'energy_efficiency': formation_result['energy_efficiency'],
            'collision_risk': formation_result['collision_risk'],
            'coverage_area': formation_result['coverage_area'],
            'individual_uav_states': [
                {
                    'id': i,
                    'position': self.uav_states[i]['position'].tolist(),
                    'velocity': self.uav_states[i]['velocity'].tolist(),
                    'battery': self.uav_states[i]['battery'],
                    'signal_strength': self.uav_states[i]['signal_strength']
                } for i in range(self.num_uavs)
            ],
            'step': self.current_step
        }
        
        return next_state, reward, terminated, truncated, info
    
    def _initialize_uav_states(self):
        """初始化 UAV 狀態"""
        self.uav_states = []
        
        for i in range(self.num_uavs):
            # 隨機但合理的初始位置（編隊中心附近）
            initial_pos = self.formation_center + np.random.uniform(-50, 50, 3)
            initial_pos[2] = max(50, initial_pos[2])  # 確保最低高度
            
            uav_state = {
                'id': i,
                'position': initial_pos,
                'velocity': np.random.uniform(-2, 2, 3),
                'battery': np.random.uniform(0.7, 1.0),  # 70-100% 電量
                'signal_strength': np.random.uniform(0.5, 1.0),
                'status': 'active'
            }
            
            self.uav_states.append(uav_state)
    
    def _get_target_formation(self) -> List[np.ndarray]:
        """獲取目標編隊形狀"""
        formations = {
            'diamond': [
                np.array([0, 0, 0]),      # 中心
                np.array([30, 0, 0]),     # 右
                np.array([-30, 0, 0]),    # 左  
                np.array([0, 30, 10])     # 後上
            ],
            'line': [
                np.array([i * 40, 0, 0]) for i in range(self.num_uavs)
            ],
            'square': [
                np.array([25, 25, 0]),
                np.array([-25, 25, 0]), 
                np.array([-25, -25, 0]),
                np.array([25, -25, 0])
            ]
        }
        
        formation = formations.get(self.formation_type, formations['diamond'])
        
        # 確保有足夠的位置
        while len(formation) < self.num_uavs:
            formation.append(np.random.uniform(-50, 50, 3))
        
        return formation[:self.num_uavs]
    
    def _parse_actions(self, action: np.ndarray) -> List[Dict]:
        """解析行動為每個 UAV 的控制指令"""
        uav_actions = []
        
        for i in range(self.num_uavs):
            start_idx = i * 4
            uav_action = {
                'thrust': action[start_idx],      # 推力 [-1, 1]
                'pitch': action[start_idx + 1],   # 俯仰 [-1, 1] 
                'yaw': action[start_idx + 2],     # 偏航 [-1, 1]
                'roll': action[start_idx + 3]     # 翻滾 [-1, 1]
            }
            uav_actions.append(uav_action)
        
        return uav_actions
    
    def _update_uav_states(self, uav_actions: List[Dict]) -> Dict[str, float]:
        """更新 UAV 狀態並計算編隊指標"""
        
        formation_quality = 0.0
        communication_quality = 0.0
        energy_efficiency = 0.0
        collision_risk = 0.0
        
        # 更新每個 UAV
        for i, (uav_state, action) in enumerate(zip(self.uav_states, uav_actions)):
            
            # 計算加速度（基於控制指令）
            acceleration = np.array([
                action['roll'] * 2.0,      # 側向加速度
                action['pitch'] * 2.0,     # 前後加速度
                action['thrust'] * 3.0     # 垂直加速度
            ])
            
            # 更新速度（考慮空氣阻力）
            uav_state['velocity'] = uav_state['velocity'] * 0.9 + acceleration * 0.1
            uav_state['velocity'] = np.clip(uav_state['velocity'], -10, 10)
            
            # 更新位置
            uav_state['position'] += uav_state['velocity']
            
            # 確保高度限制
            uav_state['position'][2] = max(30, uav_state['position'][2])
            
            # 消耗電量（基於行動強度）
            action_intensity = np.sum(np.abs([action['thrust'], action['pitch'], 
                                            action['yaw'], action['roll']]))
            energy_cost = 0.001 + action_intensity * 0.0005
            uav_state['battery'] -= energy_cost
            uav_state['battery'] = max(0, uav_state['battery'])
            
            # 更新信號強度（基於與其他 UAV 的距離）
            signal_strength = self._calculate_signal_strength(i)
            uav_state['signal_strength'] = signal_strength
        
        # 計算編隊品質指標
        formation_quality = self._calculate_formation_quality()
        communication_quality = self._calculate_communication_quality()
        energy_efficiency = self._calculate_energy_efficiency()
        collision_risk = self._calculate_collision_risk()
        coverage_area = self._calculate_coverage_area()
        
        return {
            'formation_quality': formation_quality,
            'communication_quality': communication_quality,
            'energy_efficiency': energy_efficiency,
            'collision_risk': collision_risk,
            'coverage_area': coverage_area
        }
    
    def _calculate_signal_strength(self, uav_id: int) -> float:
        """計算 UAV 與其他 UAV 的通信信號強度"""
        
        total_signal = 0.0
        count = 0
        
        current_pos = self.uav_states[uav_id]['position']
        
        for j, other_uav in enumerate(self.uav_states):
            if j != uav_id and other_uav['status'] == 'active':
                distance = np.linalg.norm(current_pos - other_uav['position'])
                # 信號強度與距離反相關
                signal = max(0, 1.0 - distance / 200.0)
                total_signal += signal
                count += 1
        
        return total_signal / max(1, count)
    
    def _calculate_formation_quality(self) -> float:
        """計算編隊品質"""
        
        if len(self.uav_states) != len(self.target_formation):
            return 0.0
        
        total_error = 0.0
        
        for i, (uav_state, target_pos) in enumerate(zip(self.uav_states, self.target_formation)):
            # 相對於編隊中心的實際位置
            actual_relative = uav_state['position'] - self.formation_center
            
            # 計算與目標位置的誤差
            error = np.linalg.norm(actual_relative - target_pos)
            total_error += error
        
        # 轉換為 0-1 的品質分數（誤差越小品質越高）
        max_error = 100.0  # 假設最大可接受誤差
        quality = max(0, 1.0 - total_error / (max_error * self.num_uavs))
        
        return quality
    
    def _calculate_communication_quality(self) -> float:
        """計算通信品質"""
        
        total_quality = 0.0
        count = 0
        
        for uav_state in self.uav_states:
            if uav_state['status'] == 'active':
                total_quality += uav_state['signal_strength']
                count += 1
        
        return total_quality / max(1, count)
    
    def _calculate_energy_efficiency(self) -> float:
        """計算能源效率"""
        
        total_battery = sum(uav['battery'] for uav in self.uav_states)
        return total_battery / self.num_uavs
    
    def _calculate_collision_risk(self) -> float:
        """計算碰撞風險"""
        
        min_safe_distance = 15.0  # 最小安全距離
        risk = 0.0
        
        for i in range(self.num_uavs):
            for j in range(i + 1, self.num_uavs):
                distance = np.linalg.norm(
                    self.uav_states[i]['position'] - self.uav_states[j]['position']
                )
                if distance < min_safe_distance:
                    risk += (min_safe_distance - distance) / min_safe_distance
        
        return min(1.0, risk)
    
    def _calculate_coverage_area(self) -> float:
        """計算覆蓋面積"""
        
        # 簡化計算：基於 UAV 位置的分散程度
        positions = np.array([uav['position'][:2] for uav in self.uav_states])  # 只考慮 x, y
        
        if len(positions) < 3:
            return 0.0
        
        # 計算凸包面積的近似值
        center = np.mean(positions, axis=0)
        max_distance = np.max([np.linalg.norm(pos - center) for pos in positions])
        
        # 正規化覆蓋面積
        return min(1.0, max_distance / 100.0)
    
    def _calculate_formation_reward(self, formation_result: Dict[str, float]) -> float:
        """計算編隊管理獎勵"""
        
        reward = 0.0
        
        # 編隊品質獎勵（主要目標）
        formation_quality = formation_result['formation_quality']
        reward += formation_quality * 20
        
        # 通信品質獎勵
        comm_quality = formation_result['communication_quality']
        reward += comm_quality * 10
        
        # 能源效率獎勵
        energy_efficiency = formation_result['energy_efficiency']
        reward += energy_efficiency * 8
        
        # 碰撞風險懲罰
        collision_risk = formation_result['collision_risk']
        reward -= collision_risk * 25
        
        # 覆蓋面積獎勵
        coverage = formation_result['coverage_area']
        reward += coverage * 5
        
        # 穩定性獎勵（速度不要太大）
        total_velocity = sum(np.linalg.norm(uav['velocity']) for uav in self.uav_states)
        avg_velocity = total_velocity / self.num_uavs
        if avg_velocity < 3.0:  # 鼓勵穩定飛行
            reward += 3
        elif avg_velocity > 8.0:  # 懲罰過快飛行
            reward -= 5
        
        # 完美編隊額外獎勵
        if (formation_quality > 0.9 and comm_quality > 0.8 and 
            collision_risk < 0.1 and energy_efficiency > 0.6):
            reward += 15
        
        return float(reward)
    
    def _get_observation(self) -> np.ndarray:
        """獲取當前觀測"""
        
        obs = []
        
        # 每個 UAV 的狀態
        for uav_state in self.uav_states:
            obs.extend(uav_state['position'])           # x, y, z
            obs.extend(uav_state['velocity'])           # vx, vy, vz
            obs.append(uav_state['battery'])            # battery
            obs.append(uav_state['signal_strength'])    # signal
        
        # 編隊整體指標
        obs.append(self._calculate_formation_quality())      # formation_quality
        obs.append(self._calculate_communication_quality())  # comm_quality
        obs.append(self._calculate_energy_efficiency())      # energy_efficiency
        obs.append(self._calculate_collision_risk())         # collision_risk
        obs.append(self._calculate_coverage_area())          # coverage
        
        return np.array(obs, dtype=np.float32)
    
    def _is_mission_complete(self) -> bool:
        """檢查任務是否完成"""
        
        # 檢查編隊品質
        formation_quality = self._calculate_formation_quality()
        comm_quality = self._calculate_communication_quality()
        energy_efficiency = self._calculate_energy_efficiency()
        collision_risk = self._calculate_collision_risk()
        
        # 任務成功條件
        if (formation_quality > 0.85 and 
            comm_quality > 0.8 and 
            collision_risk < 0.1 and
            energy_efficiency > 0.3):
            return True
        
        # 任務失敗條件
        active_uavs = sum(1 for uav in self.uav_states if uav['battery'] > 0.1)
        if active_uavs < 2:  # 太少 UAV 可用
            return True
        
        if collision_risk > 0.8:  # 碰撞風險過高
            return True
        
        return False
    
    def render(self, mode='human'):
        """渲染環境"""
        if mode == 'human':
            print(f"Step: {self.current_step}")
            print(f"Formation Quality: {self._calculate_formation_quality():.3f}")
            print(f"Communication Quality: {self._calculate_communication_quality():.3f}")
            print(f"Energy Efficiency: {self._calculate_energy_efficiency():.3f}")
            print(f"Collision Risk: {self._calculate_collision_risk():.3f}")
            print(f"Coverage Area: {self._calculate_coverage_area():.3f}")
            print("-" * 50)
    
    def close(self):
        """清理資源"""
        pass