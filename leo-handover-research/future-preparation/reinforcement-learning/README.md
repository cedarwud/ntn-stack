# 🤖 強化學習系統準備 (Phase 5+)

## 📋 總覽

基於完成的 Phase 0-4 基礎架構，準備實現深度強化學習 (RL) 驅動的智能換手決策系統。

### 🎯 RL 系統目標
- **智能決策**: 基於環境狀態的最優換手策略
- **多目標優化**: 平衡延遲、吞吐量、切換次數
- **自適應學習**: 持續優化決策品質
- **多代理協調**: 支援多用戶場景協調換手

---

## 📁 RL 系統架構

### **1. Deep Q-Network (DQN) 單用戶優化** 🧠
- **文檔**: [dqn-single-user.md](dqn-single-user.md)
- **應用**: 單用戶最優換手時機決策
- **狀態空間**: RSRP、距離、仰角、歷史切換
- **優先級**: Phase 5 首要實現

### **2. Multi-Agent RL 多用戶協調** 🤝
- **文檔**: [multi-agent-coordination.md](multi-agent-coordination.md)
- **應用**: 多用戶衝突避免與負載平衡
- **演算法**: MA-PPO、QMIX、MADDPG
- **優先級**: Phase 6 主要目標

### **3. Graph Neural Network 拓撲感知** 🌐
- **文檔**: [gnn-topology-aware.md](gnn-topology-aware.md)
- **應用**: 星座拓撲變化的感知決策
- **技術**: Graph Attention Network、GraphSAINT
- **優先級**: Phase 7 進階功能

### **4. 預測性切換 LSTM/GRU** 🔮
- **文檔**: [predictive-handover.md](predictive-handover.md)  
- **應用**: 軌跡預測與預先準備切換
- **技術**: LSTM、GRU、Transformer
- **優先級**: Phase 6 輔助功能

---

## 🏗️ RL 基礎架構設計

### **狀態空間定義**
```python
class HandoverStateSpace:
    """
    換手決策狀態空間
    基於 SIB19 增強的系統狀態
    """
    
    def __init__(self):
        self.state_dim = 32  # 狀態維度
        
    def get_state_vector(self, timestamp, satellite_data, ue_context):
        """
        獲取當前狀態向量
        """
        state = np.zeros(self.state_dim)
        
        # 1. 服務衛星狀態 (8維)
        serving_satellite = ue_context['serving_satellite']
        state[0] = serving_satellite['rsrp_dbm'] / 100.0  # 歸一化 RSRP
        state[1] = serving_satellite['elevation_deg'] / 90.0
        state[2] = serving_satellite['distance_km'] / 2000.0
        state[3] = serving_satellite['doppler_offset_hz'] / 100000.0
        state[4] = serving_satellite['link_quality_index']  # 0-1
        state[5] = serving_satellite['load_factor']  # 0-1
        state[6] = serving_satellite['reliability_score']  # 0-1
        state[7] = serving_satellite['remaining_visibility_sec'] / 3600.0
        
        # 2. 最佳候選衛星狀態 (8維)
        best_candidate = self._get_best_candidate(satellite_data)
        if best_candidate:
            state[8] = best_candidate['rsrp_dbm'] / 100.0
            state[9] = best_candidate['elevation_deg'] / 90.0
            state[10] = best_candidate['distance_km'] / 2000.0
            state[11] = best_candidate['doppler_offset_hz'] / 100000.0
            state[12] = best_candidate['link_quality_index']
            state[13] = best_candidate['load_factor']
            state[14] = best_candidate['reliability_score']
            state[15] = best_candidate['visibility_duration_sec'] / 3600.0
        
        # 3. 網路狀態 (8維)
        network_state = ue_context['network_state']
        state[16] = network_state['total_load'] / 100.0
        state[17] = network_state['handover_rate'] / 10.0  # 每分鐘切換次數
        state[18] = network_state['packet_loss_rate']
        state[19] = network_state['average_latency_ms'] / 1000.0
        state[20] = network_state['throughput_mbps'] / 1000.0
        state[21] = network_state['congestion_level']  # 0-1
        state[22] = network_state['interference_level']  # 0-1
        state[23] = network_state['weather_impact_factor']  # 0-2
        
        # 4. 歷史換手統計 (8維)
        handover_history = ue_context['handover_history']
        state[24] = handover_history['recent_handover_count'] / 10.0
        state[25] = handover_history['success_rate']
        state[26] = handover_history['average_handover_time_ms'] / 1000.0
        state[27] = handover_history['ping_pong_rate']
        state[28] = handover_history['last_handover_time_sec'] / 3600.0
        state[29] = handover_history['handover_urgency_score']  # 0-1
        state[30] = handover_history['user_mobility_pattern']  # 0-1
        state[31] = handover_history['service_continuity_score']  # 0-1
        
        return state
        
    def _get_best_candidate(self, satellite_data):
        """選擇最佳候選衛星"""
        candidates = [s for s in satellite_data if s['elevation_deg'] > 10]
        if not candidates:
            return None
        
        # 基於綜合分數排序
        scored_candidates = []
        for candidate in candidates:
            score = (
                candidate['rsrp_dbm'] / 100.0 * 0.4 +
                candidate['elevation_deg'] / 90.0 * 0.3 +
                (1 - candidate['load_factor']) * 0.2 +
                candidate['reliability_score'] * 0.1
            )
            scored_candidates.append((score, candidate))
        
        return max(scored_candidates, key=lambda x: x[0])[1]
```

### **動作空間定義**
```python
class HandoverActionSpace:
    """
    換手決策動作空間
    """
    
    def __init__(self):
        self.action_dim = 4
        self.actions = {
            0: 'MAINTAIN',      # 維持當前連接
            1: 'HANDOVER',      # 執行換手
            2: 'PREPARE',       # 準備換手 (預配置)
            3: 'EMERGENCY'      # 緊急換手
        }
        
    def get_valid_actions(self, state_vector, satellite_data):
        """
        獲取當前狀態下的有效動作
        """
        valid_actions = [0]  # MAINTAIN 總是有效
        
        # 檢查是否有可用候選衛星
        candidates = [s for s in satellite_data if s['elevation_deg'] > 10]
        if candidates:
            valid_actions.extend([1, 2])  # HANDOVER, PREPARE
        
        # 檢查是否需要緊急換手
        serving_rsrp = state_vector[0] * 100.0
        if serving_rsrp < -115:  # 信號極弱
            valid_actions.append(3)  # EMERGENCY
        
        return valid_actions
```

### **獎勵函數設計**
```python
class HandoverRewardFunction:
    """
    換手決策獎勵函數
    多目標平衡：QoS + 效率 + 穩定性
    """
    
    def __init__(self):
        self.weights = {
            'qos': 0.4,         # 服務品質
            'efficiency': 0.3,   # 切換效率
            'stability': 0.3     # 連接穩定性
        }
        
    def calculate_reward(self, prev_state, action, new_state, handover_result):
        """
        計算獎勵值
        """
        # 1. QoS 獎勵
        qos_reward = self._calculate_qos_reward(prev_state, new_state)
        
        # 2. 效率獎勵
        efficiency_reward = self._calculate_efficiency_reward(
            action, handover_result)
        
        # 3. 穩定性獎勵
        stability_reward = self._calculate_stability_reward(
            prev_state, action, new_state)
        
        # 加權總獎勵
        total_reward = (
            self.weights['qos'] * qos_reward +
            self.weights['efficiency'] * efficiency_reward +
            self.weights['stability'] * stability_reward
        )
        
        return {
            'total_reward': total_reward,
            'qos_reward': qos_reward,
            'efficiency_reward': efficiency_reward,
            'stability_reward': stability_reward
        }
    
    def _calculate_qos_reward(self, prev_state, new_state):
        """
        QoS 改善獎勵
        """
        # RSRP 改善
        prev_rsrp = prev_state[0] * 100.0
        new_rsrp = new_state[0] * 100.0
        rsrp_improvement = (new_rsrp - prev_rsrp) / 10.0  # 歸一化到 ±10dB
        
        # 延遲改善
        prev_latency = prev_state[19] * 1000.0
        new_latency = new_state[19] * 1000.0
        latency_improvement = (prev_latency - new_latency) / 100.0  # 歸一化到 ±100ms
        
        # 吞吐量改善
        prev_throughput = prev_state[20] * 1000.0
        new_throughput = new_state[20] * 1000.0
        throughput_improvement = (new_throughput - prev_throughput) / 100.0
        
        qos_reward = (
            rsrp_improvement * 0.5 +
            latency_improvement * 0.3 +
            throughput_improvement * 0.2
        )
        
        return np.clip(qos_reward, -1.0, 1.0)
    
    def _calculate_efficiency_reward(self, action, handover_result):
        """
        切換效率獎勵
        """
        if action == 0:  # MAINTAIN
            return 0.1  # 小正獎勵：不必要的切換
        
        if action in [1, 3]:  # HANDOVER, EMERGENCY
            if handover_result and handover_result['success']:
                # 成功切換獎勵
                handover_time = handover_result.get('handover_time_ms', 500)
                time_efficiency = max(0, (1000 - handover_time) / 1000)
                return 0.5 + 0.5 * time_efficiency
            else:
                # 切換失敗懲罰
                return -0.8
        
        if action == 2:  # PREPARE
            # 準備動作小獎勵
            return 0.2
        
        return 0.0
    
    def _calculate_stability_reward(self, prev_state, action, new_state):
        """
        連接穩定性獎勵
        """
        # Ping-pong 懲罰
        handover_count = new_state[24] * 10.0
        if handover_count > 5:  # 5分鐘內超過5次切換
            ping_pong_penalty = -0.5 * (handover_count - 5) / 5
        else:
            ping_pong_penalty = 0.0
        
        # 服務連續性獎勵
        service_continuity = new_state[31]
        continuity_reward = (service_continuity - 0.5) * 0.4
        
        # 預測準確性獎勵 (如果是預先準備的切換)
        if action == 2 and prev_state[29] > 0.7:  # 高緊急度下準備
            prediction_reward = 0.3
        else:
            prediction_reward = 0.0
        
        stability_reward = ping_pong_penalty + continuity_reward + prediction_reward
        
        return np.clip(stability_reward, -1.0, 1.0)
```

---

## 🔧 RL 訓練環境

### **仿真環境設計**
```python
class LEOHandoverEnvironment(gym.Env):
    """
    LEO 衛星換手 RL 訓練環境
    """
    
    def __init__(self, scenario_config):
        super().__init__()
        
        # 狀態和動作空間
        self.state_space = HandoverStateSpace()
        self.action_space = HandoverActionSpace()
        self.reward_function = HandoverRewardFunction()
        
        # 仿真組件
        self.orbit_simulator = OrbitSimulator(scenario_config)
        self.network_simulator = NetworkSimulator(scenario_config)
        self.user_mobility = UserMobilityModel(scenario_config)
        
        # Gym 介面
        self.observation_space = gym.spaces.Box(
            low=-1, high=1, shape=(32,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(4)
        
    def reset(self):
        """重置環境"""
        # 重置仿真器
        self.orbit_simulator.reset()
        self.network_simulator.reset()
        self.user_mobility.reset()
        
        # 初始狀態
        satellite_data = self.orbit_simulator.get_current_satellites()
        ue_context = self.network_simulator.get_ue_context()
        
        state = self.state_space.get_state_vector(
            time.time(), satellite_data, ue_context)
        
        return state
    
    def step(self, action):
        """執行動作並返回結果"""
        # 記錄前狀態
        prev_state = self._get_current_state()
        
        # 執行動作
        handover_result = self._execute_action(action)
        
        # 推進仿真
        self.orbit_simulator.step()
        self.network_simulator.step()
        self.user_mobility.step()
        
        # 獲取新狀態
        new_state = self._get_current_state()
        
        # 計算獎勵
        reward_info = self.reward_function.calculate_reward(
            prev_state, action, new_state, handover_result)
        
        # 檢查結束條件
        done = self._check_done()
        
        # 構建資訊
        info = {
            'handover_result': handover_result,
            'reward_breakdown': reward_info,
            'network_stats': self.network_simulator.get_stats()
        }
        
        return new_state, reward_info['total_reward'], done, info
```

---

## 📊 RL 演算法選擇

### **算法優先級排序**

| 演算法 | 應用場景 | 優先級 | 開發階段 |
|--------|----------|--------|----------|
| **DQN** | 單用戶離散動作 | ⭐⭐⭐⭐⭐ | Phase 5 |
| **PPO** | 單用戶連續控制 | ⭐⭐⭐⭐ | Phase 5 |
| **DDPG** | 連續動作空間 | ⭐⭐⭐ | Phase 6 |
| **MA-PPO** | 多用戶協調 | ⭐⭐⭐⭐ | Phase 6 |
| **QMIX** | 價值分解協調 | ⭐⭐⭐ | Phase 6 |
| **Graph RL** | 拓撲感知 | ⭐⭐⭐⭐ | Phase 7 |

---

## 📅 開發時程規劃

### **Phase 5 (3個月): DQN 基礎實現**
- Month 1: 仿真環境構建
- Month 2: DQN 演算法實現與訓練
- Month 3: 性能評估與優化

### **Phase 6 (4個月): 多代理協調**
- Month 1-2: Multi-Agent 環境設計
- Month 3: MA-PPO/QMIX 實現
- Month 4: 多用戶場景驗證

### **Phase 7 (3個月): 進階功能**
- Month 1: Graph Neural Network 整合
- Month 2: 預測性切換實現
- Month 3: 系統整合與最佳化

---

## 🎯 成功標準

### **Phase 5 目標**
- [ ] DQN 收斂：訓練 10M 步後穩定
- [ ] 切換成功率 >98%
- [ ] Ping-pong 率 <1%
- [ ] 平均 QoS 提升 >20%

### **Phase 6 目標**
- [ ] 多用戶衝突率 <5%
- [ ] 系統總吞吐量提升 >30%
- [ ] 負載平衡效果明顯
- [ ] 實時決策延遲 <50ms

### **Phase 7 目標**
- [ ] 拓撲變化適應性 >95%
- [ ] 預測準確率 >90%
- [ ] 整體系統穩定性達到商用級
- [ ] 學術論文發表就緒

---

*Reinforcement Learning System Preparation - Generated: 2025-08-01*