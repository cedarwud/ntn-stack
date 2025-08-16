# 🚀 Phase 2 RL擴展系統 - 詳細實施計劃

**版本**: v2.0  
**更新日期**: 2025-08-15  
**狀態**: 規劃階段 (等待Phase 1完成)

---

## 📋 執行前提

### ✅ Phase 1完成確認清單
- [ ] **全量8736顆衛星軌道計算完成**
- [ ] **可見性合規達到>70%** (測試模式) 或 >90% (正式模式)
- [ ] **Phase 1最終報告生成** (`/tmp/phase1_outputs/phase1_final_report.json`)
- [ ] **候選衛星池最佳化完成** (205顆Starlink + 63顆OneWeb 或更佳結果)
- [ ] **A4/A5/D2事件檢測框架驗證**

### 📊 Phase 1輸出依賴
```bash
# 必要的Phase 1輸出文件
/tmp/phase1_outputs/
├── stage1_tle_loading_results.json      # TLE載入統計
├── stage2_filtering_results.json        # 候選衛星+軌道位置
├── stage3_event_analysis_results.json   # A4/A5/D2事件
├── stage4_optimization_results.json     # 最佳衛星池
└── phase1_final_report.json            # 完整報告
```

---

## 🗓️ 詳細時程規劃

### 📅 Week 1: 基礎設施建設 (5天)

#### Day 1: 環境設置和依賴安裝
```bash
# 任務清單
- [ ] 創建Phase 2目錄結構
- [ ] 安裝RL框架依賴 (PyTorch, Gymnasium, Stable-Baselines3)
- [ ] 設置實驗追蹤 (Weights & Biases)
- [ ] 建立Git分支和版本控制
```

**技術規格**:
```bash
# 依賴安裝
pip install torch gymnasium stable-baselines3[extra]
pip install wandb ray[rllib] mlflow
pip install pandas numpy scikit-learn plotly

# 目錄創建
cd /home/sat/ntn-stack/leo_restructure/phase2_rl_expansion
mkdir -p ml1_data_collector ml2_model_trainer ml3_inference_engine
mkdir -p performance_monitor integration experiments docs
```

#### Day 2: Phase 1數據適配器開發
```python
# 核心文件: ml1_data_collector/phase1_data_adapter.py
class Phase1DataAdapter:
    def __init__(self, phase1_output_dir="/tmp/phase1_outputs"):
        self.output_dir = Path(phase1_output_dir)
        self.satellite_pools = None
        self.orbital_positions = None
        self.handover_events = None
    
    def validate_phase1_completion(self) -> bool:
        """驗證Phase 1是否完成且數據完整"""
        required_files = [
            "stage4_optimization_results.json",
            "stage2_filtering_results.json", 
            "stage3_event_analysis_results.json",
            "phase1_final_report.json"
        ]
        
        for file in required_files:
            if not (self.output_dir / file).exists():
                raise FileNotFoundError(f"Phase 1輸出缺失: {file}")
        
        # 驗證可見性合規
        final_report = self.load_final_report()
        visibility_compliance = final_report['final_results']['optimal_satellite_pools']['visibility_compliance']
        
        if visibility_compliance < 0.7:  # 最低要求70%
            raise ValueError(f"可見性合規不足: {visibility_compliance:.1%} < 70%")
        
        return True
    
    def extract_rl_training_data(self) -> Dict:
        """提取RL訓練所需的所有數據"""
        return {
            'satellite_pools': self.load_optimal_pools(),
            'orbital_trajectories': self.extract_orbital_trajectories(),
            'handover_scenarios': self.extract_handover_scenarios(),
            'visibility_constraints': self.extract_constraints(),
            'performance_baselines': self.extract_baselines()
        }
```

#### Day 3: LEO衛星RL環境設計
```python
# 核心文件: ml2_model_trainer/leo_environment.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class LEOSatelliteEnv(gym.Env):
    """基於Phase 1真實數據的LEO衛星換手環境"""
    
    def __init__(self, phase1_data: Dict):
        super().__init__()
        
        # 基於Phase 1數據初始化
        self.satellite_pools = phase1_data['satellite_pools']
        self.orbital_data = phase1_data['orbital_trajectories']
        self.constraints = phase1_data['visibility_constraints']
        
        # 狀態空間定義 (基於Phase 1實際數據維度)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, 
            shape=(self._get_state_dimension(),), 
            dtype=np.float32
        )
        
        # 動作空間定義 (基於候選衛星數量)
        max_candidates = max(len(self.satellite_pools['starlink']), 
                           len(self.satellite_pools['oneweb']))
        self.action_space = spaces.Discrete(max_candidates + 1)  # +1 for STAY
        
        # 初始化狀態
        self.reset()
    
    def _get_state_dimension(self) -> int:
        """計算狀態向量維度"""
        return (
            1 +          # 當前衛星RSRP
            1 +          # 當前衛星仰角  
            1 +          # 當前衛星距離
            10 +         # 最多10個候選衛星的RSRP
            10 +         # 最多10個候選衛星的仰角
            5 +          # 換手歷史特徵
            3 +          # 網路負載特徵
            2            # 時間特徵
        )  # 總計: 33維狀態空間
    
    def step(self, action):
        """執行動作並計算獎勵"""
        # 根據Phase 1約束驗證動作合法性
        if not self._is_action_valid(action):
            return self.state, -1.0, True, True, {"error": "違反Phase 1約束"}
        
        # 執行動作
        next_state = self._execute_action(action)
        reward = self._compute_reward(self.state, action, next_state)
        done = self._is_episode_done()
        
        self.state = next_state
        return self.state, reward, done, False, {}
    
    def _compute_reward(self, state, action, next_state) -> float:
        """基於Phase 1數據的獎勵函數"""
        reward = 0.0
        
        # 1. 信號品質改善 (基於Phase 1的RSRP計算)
        rsrp_improvement = next_state[0] - state[0]
        reward += 0.3 * np.tanh(rsrp_improvement / 10.0)  # 正規化
        
        # 2. 可見性合規 (基於Phase 1的仰角約束)
        elevation = next_state[1]
        if elevation >= 5.0:  # Starlink閾值
            reward += 0.25
        elif elevation >= 0.0:
            reward += 0.1 * (elevation / 5.0)  # 線性獎勵
        else:
            reward -= 0.5  # 重懲罰負仰角
        
        # 3. 換手成本
        if action > 0:  # 非STAY動作
            reward -= 0.1
        
        return reward
```

#### Day 4: 基礎獎勵函數實現
```python
# 核心文件: ml2_model_trainer/reward_function.py
class Phase1AwareRewardFunction:
    """基於Phase 1約束和目標的獎勵函數"""
    
    def __init__(self, phase1_constraints: Dict):
        self.constraints = phase1_constraints
        self.weights = {
            'signal_quality': 0.3,
            'visibility_compliance': 0.25, 
            'handover_cost': 0.1,
            'qos_satisfaction': 0.2,
            'constraint_violation': 0.15
        }
    
    def compute(self, state, action, next_state, context) -> float:
        """計算多目標獎勵"""
        components = {}
        
        # 1. 信號品質改善
        components['signal_quality'] = self._signal_quality_reward(state, next_state)
        
        # 2. Phase 1可見性合規
        components['visibility_compliance'] = self._visibility_reward(next_state, context)
        
        # 3. 換手成本
        components['handover_cost'] = self._handover_cost_penalty(action)
        
        # 4. QoS滿足度
        components['qos_satisfaction'] = self._qos_reward(next_state, context)
        
        # 5. Phase 1約束違反懲罰
        components['constraint_violation'] = self._constraint_penalty(next_state, context)
        
        # 加權總和
        total_reward = sum(
            self.weights[component] * value 
            for component, value in components.items()
        )
        
        return total_reward, components  # 返回總獎勵和組件分解
```

#### Day 5: 數據驗證和初步測試
```python
# 核心文件: ml1_data_collector/data_validator.py
class Phase1DataValidator:
    """Phase 1數據品質驗證器"""
    
    def validate_complete_pipeline(self, phase1_data: Dict) -> ValidationReport:
        """完整數據管道驗證"""
        report = ValidationReport()
        
        # 1. 數據完整性檢查
        report.add_check("數據完整性", self._check_data_completeness(phase1_data))
        
        # 2. 數據一致性檢查
        report.add_check("數據一致性", self._check_data_consistency(phase1_data))
        
        # 3. 約束滿足檢查
        report.add_check("約束滿足", self._check_constraint_satisfaction(phase1_data))
        
        # 4. 訓練數據充足性檢查
        report.add_check("訓練數據充足性", self._check_training_data_sufficiency(phase1_data))
        
        return report
    
    def _check_constraint_satisfaction(self, data) -> bool:
        """檢查Phase 1約束是否滿足"""
        pools = data['satellite_pools']
        
        # 檢查衛星池大小
        starlink_count = len(pools.get('starlink_satellites', []))
        oneweb_count = len(pools.get('oneweb_satellites', []))
        
        # 檢查可見性合規
        visibility_compliance = pools.get('visibility_compliance', 0.0)
        
        return (
            starlink_count >= 50 and  # 最低候選數量
            oneweb_count >= 20 and
            visibility_compliance >= 0.7  # 最低合規要求
        )
```

---

### 📅 Week 2: 深度學習模型開發 (5天)

#### Day 6-7: DQN網路架構實現
```python
# 核心文件: ml2_model_trainer/dqn_trainer.py
import torch
import torch.nn as nn
import torch.nn.functional as F

class LEOSatelliteDQN(nn.Module):
    """專為LEO衛星換手設計的DQN網路"""
    
    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        
        # 狀態編碼器 (處理33維狀態向量)
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.LayerNorm(128),
            nn.Dropout(0.1),
            
            nn.Linear(128, 64),
            nn.ReLU(), 
            nn.LayerNorm(64)
        )
        
        # 衛星特徵編碼器 (處理候選衛星特徵)
        self.satellite_encoder = nn.Sequential(
            nn.Linear(20, 32),  # 10個候選的RSRP+仰角
            nn.ReLU(),
            nn.Linear(32, 16)
        )
        
        # 決策頭 (Q值預測)
        self.q_head = nn.Sequential(
            nn.Linear(64 + 16, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )
    
    def forward(self, state):
        # 分離不同類型的特徵
        general_features = state[:, :13]  # 前13維為一般特徵
        satellite_features = state[:, 13:33]  # 後20維為衛星特徵
        
        # 編碼特徵
        general_encoded = self.state_encoder(general_features)
        satellite_encoded = self.satellite_encoder(satellite_features)
        
        # 拼接特徵
        combined_features = torch.cat([general_encoded, satellite_encoded], dim=1)
        
        # 預測Q值
        q_values = self.q_head(combined_features)
        
        return q_values

class DQNTrainer:
    """DQN訓練器"""
    
    def __init__(self, env, config):
        self.env = env
        self.config = config
        
        # 網路初始化
        state_dim = env.observation_space.shape[0]
        action_dim = env.action_space.n
        
        self.q_network = LEOSatelliteDQN(state_dim, action_dim)
        self.target_network = LEOSatelliteDQN(state_dim, action_dim)
        self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=config.learning_rate)
        
        # 經驗回放
        self.replay_buffer = ReplayBuffer(config.buffer_size)
        
        # 訓練統計
        self.episode_rewards = []
        self.training_losses = []
    
    def train(self, num_episodes: int):
        """執行DQN訓練"""
        for episode in range(num_episodes):
            episode_reward = self._train_episode()
            self.episode_rewards.append(episode_reward)
            
            # 定期更新目標網路
            if episode % self.config.target_update_freq == 0:
                self._update_target_network()
            
            # 記錄和可視化
            if episode % 100 == 0:
                self._log_training_progress(episode)
    
    def _train_episode(self) -> float:
        """訓練單個episode"""
        state, _ = self.env.reset()
        episode_reward = 0.0
        done = False
        
        while not done:
            # 選擇動作 (ε-greedy)
            action = self._select_action(state)
            
            # 執行動作
            next_state, reward, done, truncated, info = self.env.step(action)
            done = done or truncated
            
            # 存儲經驗
            self.replay_buffer.push(state, action, reward, next_state, done)
            
            # 訓練網路
            if len(self.replay_buffer) > self.config.batch_size:
                loss = self._train_step()
                self.training_losses.append(loss)
            
            state = next_state
            episode_reward += reward
        
        return episode_reward
```

#### Day 8-9: 經驗回放和訓練優化
```python
# 核心文件: ml2_model_trainer/replay_buffer.py
import random
from collections import deque, namedtuple
import numpy as np

Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])

class PrioritizedReplayBuffer:
    """優先經驗回放緩衝區"""
    
    def __init__(self, capacity: int, alpha: float = 0.6):
        self.capacity = capacity
        self.alpha = alpha  # 優先級指數
        self.beta = 0.4     # 重要性採樣指數
        self.beta_increment = 0.001
        
        self.buffer = []
        self.priorities = deque(maxlen=capacity)
        self.position = 0
    
    def push(self, state, action, reward, next_state, done):
        """添加新經驗"""
        experience = Experience(state, action, reward, next_state, done)
        
        # 新經驗獲得最大優先級
        max_priority = max(self.priorities) if self.priorities else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(max_priority)
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = max_priority
        
        self.position = (self.position + 1) % self.capacity
    
    def sample(self, batch_size: int):
        """基於優先級採樣"""
        if len(self.buffer) < batch_size:
            return None
        
        # 計算採樣概率
        priorities = np.array(self.priorities)
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        # 採樣索引
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
        
        # 計算重要性權重
        weights = (len(self.buffer) * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()
        
        # 提取批次數據
        batch = [self.buffer[idx] for idx in indices]
        
        # 更新β
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        return batch, indices, weights
    
    def update_priorities(self, indices, priorities):
        """更新優先級"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-6  # 避免零優先級
```

#### Day 10: 訓練監控和實驗追蹤
```python
# 核心文件: ml2_model_trainer/training_monitor.py
import wandb
import matplotlib.pyplot as plt
from typing import Dict, List

class TrainingMonitor:
    """訓練過程監控和可視化"""
    
    def __init__(self, project_name: str, config: Dict):
        # 初始化Weights & Biases
        wandb.init(project=project_name, config=config)
        
        self.metrics_history = {
            'episode_rewards': [],
            'training_losses': [],
            'q_values': [],
            'exploration_rate': [],
            'phase1_compliance_rate': []
        }
    
    def log_episode(self, episode: int, metrics: Dict):
        """記錄單個episode的指標"""
        # 更新歷史記錄
        for key, value in metrics.items():
            if key in self.metrics_history:
                self.metrics_history[key].append(value)
        
        # 記錄到wandb
        wandb.log({
            "episode": episode,
            **metrics
        })
        
        # 生成可視化圖表
        if episode % 500 == 0:
            self._generate_training_plots(episode)
    
    def log_phase1_compliance(self, episode: int, compliance_metrics: Dict):
        """記錄Phase 1約束合規性"""
        wandb.log({
            "episode": episode,
            "phase1/visibility_compliance": compliance_metrics.get('visibility_compliance', 0),
            "phase1/constraint_violations": compliance_metrics.get('violations', 0),
            "phase1/reward_from_constraints": compliance_metrics.get('constraint_reward', 0)
        })
    
    def _generate_training_plots(self, episode: int):
        """生成訓練過程可視化圖表"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Episode獎勵趨勢
        axes[0, 0].plot(self.metrics_history['episode_rewards'])
        axes[0, 0].set_title('Episode Rewards')
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Reward')
        
        # 2. 訓練損失
        if self.metrics_history['training_losses']:
            axes[0, 1].plot(self.metrics_history['training_losses'])
            axes[0, 1].set_title('Training Loss')
            axes[0, 1].set_xlabel('Training Step')
            axes[0, 1].set_ylabel('Loss')
        
        # 3. Q值統計
        if self.metrics_history['q_values']:
            axes[1, 0].plot(self.metrics_history['q_values'])
            axes[1, 0].set_title('Average Q-Values')
            axes[1, 0].set_xlabel('Episode')
            axes[1, 0].set_ylabel('Q-Value')
        
        # 4. Phase 1合規率
        if self.metrics_history['phase1_compliance_rate']:
            axes[1, 1].plot(self.metrics_history['phase1_compliance_rate'])
            axes[1, 1].set_title('Phase 1 Compliance Rate')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Compliance Rate')
        
        plt.tight_layout()
        
        # 保存並上傳到wandb
        plt.savefig(f'/tmp/training_plots_episode_{episode}.png')
        wandb.log({"training_plots": wandb.Image(f'/tmp/training_plots_episode_{episode}.png')})
        plt.close()
```

---

### 📅 Week 3-4: 高級演算法和多目標優化 (10天)

#### Day 11-15: PPO和SAC演算法實現
```python
# 核心文件: ml2_model_trainer/ppo_trainer.py
import torch
import torch.nn as nn
from torch.distributions import Categorical

class PPOAgent:
    """Proximal Policy Optimization智能體"""
    
    def __init__(self, state_dim, action_dim, config):
        self.config = config
        
        # Actor-Critic網路
        self.actor_critic = ActorCriticNetwork(state_dim, action_dim)
        self.optimizer = torch.optim.Adam(self.actor_critic.parameters(), lr=config.learning_rate)
        
        # PPO參數
        self.epsilon = config.ppo_epsilon
        self.value_loss_coef = config.value_loss_coef
        self.entropy_coef = config.entropy_coef
    
    def select_action(self, state):
        """選擇動作並返回動作、log概率、狀態值"""
        with torch.no_grad():
            logits, value = self.actor_critic(state)
            dist = Categorical(logits=logits)
            action = dist.sample()
            log_prob = dist.log_prob(action)
        
        return action.item(), log_prob.item(), value.item()
    
    def update(self, trajectories):
        """使用收集的軌跡更新策略"""
        states, actions, rewards, log_probs, values, dones = trajectories
        
        # 計算優勢和回報
        advantages, returns = self._compute_gae(rewards, values, dones)
        
        # 多次更新策略
        for _ in range(self.config.ppo_epochs):
            # 前向傳播
            logits, current_values = self.actor_critic(states)
            dist = Categorical(logits=logits)
            current_log_probs = dist.log_prob(actions)
            entropy = dist.entropy().mean()
            
            # 計算PPO損失
            ratio = torch.exp(current_log_probs - log_probs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.epsilon, 1 + self.epsilon) * advantages
            
            actor_loss = -torch.min(surr1, surr2).mean()
            critic_loss = nn.MSELoss()(current_values.squeeze(), returns)
            
            total_loss = (
                actor_loss + 
                self.value_loss_coef * critic_loss - 
                self.entropy_coef * entropy
            )
            
            # 反向傳播
            self.optimizer.zero_grad()
            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor_critic.parameters(), 0.5)
            self.optimizer.step()
        
        return {
            'actor_loss': actor_loss.item(),
            'critic_loss': critic_loss.item(),
            'entropy': entropy.item()
        }
```

#### Day 16-20: 多目標優化和超參數調優
```python
# 核心文件: ml2_model_trainer/multi_objective_optimizer.py
import optuna
from typing import Dict, List, Callable

class MultiObjectiveRLOptimizer:
    """多目標RL優化器"""
    
    def __init__(self, objectives: List[str], constraints: Dict):
        self.objectives = objectives  # ['reward', 'phase1_compliance', 'stability']
        self.constraints = constraints
        self.study = optuna.create_study(
            directions=['maximize'] * len(objectives),
            study_name='leo_satellite_rl_optimization'
        )
    
    def objective_function(self, trial):
        """多目標優化目標函數"""
        # 採樣超參數
        config = self._sample_hyperparameters(trial)
        
        # 訓練模型
        results = self._train_with_config(config)
        
        # 計算多個目標
        objectives = []
        
        # 目標1: 平均獎勵
        objectives.append(results['avg_reward'])
        
        # 目標2: Phase 1約束合規率
        objectives.append(results['phase1_compliance_rate'])
        
        # 目標3: 訓練穩定性 (負的標準差)
        objectives.append(-results['reward_std'])
        
        return objectives
    
    def _sample_hyperparameters(self, trial) -> Dict:
        """採樣超參數空間"""
        return {
            'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
            'batch_size': trial.suggest_categorical('batch_size', [32, 64, 128, 256]),
            'hidden_size': trial.suggest_categorical('hidden_size', [64, 128, 256, 512]),
            'epsilon_decay': trial.suggest_float('epsilon_decay', 0.9, 0.999),
            'reward_weights': {
                'signal_quality': trial.suggest_float('w_signal', 0.1, 0.5),
                'visibility_compliance': trial.suggest_float('w_visibility', 0.2, 0.4),
                'handover_cost': trial.suggest_float('w_cost', 0.05, 0.15),
                'qos_satisfaction': trial.suggest_float('w_qos', 0.1, 0.3)
            }
        }
    
    def optimize(self, n_trials: int = 100):
        """執行多目標優化"""
        self.study.optimize(self.objective_function, n_trials=n_trials)
        
        # 分析Pareto前沿
        pareto_trials = self._extract_pareto_front()
        
        return pareto_trials
    
    def _extract_pareto_front(self) -> List[Dict]:
        """提取Pareto最優解"""
        # 獲取所有試驗結果
        trials = self.study.trials
        
        # 提取目標值
        objectives_matrix = []
        for trial in trials:
            if trial.state == optuna.trial.TrialState.COMPLETE:
                objectives_matrix.append(trial.values)
        
        objectives_matrix = np.array(objectives_matrix)
        
        # 計算Pareto前沿
        pareto_indices = self._compute_pareto_front(objectives_matrix)
        
        pareto_trials = [trials[i] for i in pareto_indices]
        
        return pareto_trials
```

---

### 📅 Week 5-6: 整合測試和性能評估 (10天)

#### Day 21-25: A/B測試框架開發
```python
# 核心文件: performance_monitor/ab_testing.py
class ABTestFramework:
    """A/B測試框架 - RL vs 傳統演算法"""
    
    def __init__(self, phase1_data: Dict):
        self.phase1_data = phase1_data
        self.baseline_algorithm = TraditionalHandoverAlgorithm(phase1_data)
        self.rl_algorithm = None  # 將載入訓練好的RL模型
        
        self.test_scenarios = self._generate_test_scenarios()
        self.results = {'rl': [], 'baseline': []}
    
    def run_ab_test(self, rl_model_path: str, num_episodes: int = 1000):
        """執行A/B測試"""
        # 載入RL模型
        self.rl_algorithm = self._load_rl_model(rl_model_path)
        
        print(f"🧪 開始A/B測試 - {num_episodes} episodes")
        
        for episode in range(num_episodes):
            scenario = random.choice(self.test_scenarios)
            
            # 測試基準演算法
            baseline_result = self._test_algorithm(self.baseline_algorithm, scenario)
            self.results['baseline'].append(baseline_result)
            
            # 測試RL演算法
            rl_result = self._test_algorithm(self.rl_algorithm, scenario)
            self.results['rl'].append(rl_result)
            
            if episode % 100 == 0:
                self._log_intermediate_results(episode)
        
        # 生成最終報告
        return self._generate_ab_report()
    
    def _generate_ab_report(self) -> Dict:
        """生成A/B測試報告"""
        report = {
            'summary': {},
            'detailed_metrics': {},
            'statistical_significance': {},
            'phase1_compliance': {}
        }
        
        # 計算統計指標
        for algorithm in ['rl', 'baseline']:
            results = self.results[algorithm]
            
            report['summary'][algorithm] = {
                'avg_reward': np.mean([r['total_reward'] for r in results]),
                'avg_handover_delay': np.mean([r['handover_delay'] for r in results]),
                'success_rate': np.mean([r['success'] for r in results]),
                'phase1_compliance_rate': np.mean([r['phase1_compliant'] for r in results])
            }
        
        # 統計顯著性測試
        rl_rewards = [r['total_reward'] for r in self.results['rl']]
        baseline_rewards = [r['total_reward'] for r in self.results['baseline']]
        
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(rl_rewards, baseline_rewards)
        
        report['statistical_significance'] = {
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }
        
        return report
```

#### Day 26-30: 性能監控儀表板開發
```python
# 核心文件: performance_monitor/dashboard_generator.py
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st

class RLPerformanceDashboard:
    """RL系統性能監控儀表板"""
    
    def __init__(self):
        self.data_loader = None
        self.metrics_cache = {}
    
    def create_dashboard(self):
        """創建Streamlit儀表板"""
        st.set_page_config(
            page_title="LEO衛星RL系統監控", 
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("🛰️ LEO衛星RL換手決策系統監控")
        st.markdown("基於Phase 1真實衛星池的RL性能監控")
        
        # 側邊欄控制
        self._create_sidebar()
        
        # 主要內容區域
        col1, col2 = st.columns(2)
        
        with col1:
            self._create_realtime_metrics()
            self._create_phase1_compliance_chart()
        
        with col2:
            self._create_ab_test_comparison()
            self._create_handover_performance_chart()
        
        # 底部詳細分析
        st.markdown("## 詳細性能分析")
        self._create_detailed_analysis()
    
    def _create_realtime_metrics(self):
        """創建實時指標卡片"""
        st.markdown("### 🔥 實時性能指標")
        
        # 載入最新指標
        metrics = self._load_latest_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="RL平均獎勵",
                value=f"{metrics.get('rl_avg_reward', 0):.2f}",
                delta=f"{metrics.get('rl_reward_delta', 0):.2f}"
            )
        
        with col2:
            st.metric(
                label="換手成功率",
                value=f"{metrics.get('handover_success_rate', 0):.1%}",
                delta=f"{metrics.get('success_rate_delta', 0):.1%}"
            )
        
        with col3:
            st.metric(
                label="Phase 1合規率", 
                value=f"{metrics.get('phase1_compliance', 0):.1%}",
                delta=f"{metrics.get('compliance_delta', 0):.1%}"
            )
        
        with col4:
            st.metric(
                label="平均延遲",
                value=f"{metrics.get('avg_latency', 0):.0f}ms",
                delta=f"{metrics.get('latency_delta', 0):.0f}ms"
            )
    
    def _create_ab_test_comparison(self):
        """創建A/B測試比較圖表"""
        st.markdown("### 📊 A/B測試比較 (RL vs 傳統)")
        
        # 載入A/B測試數據
        ab_data = self._load_ab_test_data()
        
        # 創建比較圖表
        fig = go.Figure()
        
        algorithms = ['RL演算法', '傳統演算法']
        metrics = ['平均獎勵', '成功率', '延遲(ms)', 'Phase1合規率']
        
        rl_values = [
            ab_data.get('rl_avg_reward', 0),
            ab_data.get('rl_success_rate', 0) * 100,
            ab_data.get('rl_avg_latency', 0),
            ab_data.get('rl_phase1_compliance', 0) * 100
        ]
        
        baseline_values = [
            ab_data.get('baseline_avg_reward', 0),
            ab_data.get('baseline_success_rate', 0) * 100,
            ab_data.get('baseline_avg_latency', 0),
            ab_data.get('baseline_phase1_compliance', 0) * 100
        ]
        
        fig.add_trace(go.Bar(
            name='RL演算法',
            x=metrics,
            y=rl_values,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='傳統演算法',
            x=metrics,
            y=baseline_values,
            marker_color='lightcoral'
        ))
        
        fig.update_layout(
            title='性能指標比較',
            xaxis_title='指標',
            yaxis_title='數值',
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
```

---

## 🎯 成功標準和驗收條件

### 📊 量化指標要求

| 階段 | 指標 | 基準值 | RL目標 | 驗收標準 |
|------|------|--------|--------|----------|
| **Week 1-2** | 環境搭建 | N/A | 100% | 所有環境組件正常運行 |
| **Week 3-4** | DQN收斂 | 隨機策略 | >基準30% | 訓練1000 episodes後收斂 |
| **Week 5-6** | 多演算法對比 | DQN基準 | PPO/SAC >DQN 10% | 統計顯著性p<0.05 |
| **Week 7-8** | A/B測試 | 傳統演算法 | >傳統20% | 各項指標均有提升 |

### 🏆 最終驗收標準

1. **技術指標**
   - RL演算法平均獎勵 > 傳統演算法20%
   - 換手成功率 >95%
   - 平均延遲 <500ms
   - Phase 1約束合規率 >99%

2. **系統整合**
   - 與Phase 1數據無縫整合
   - API響應時間 <100ms
   - 系統穩定運行24小時無故障

3. **研究價值**
   - 完整的實驗報告和論文草稿
   - 可重現的實驗結果
   - 開源代碼和文檔

---

## 🚨 風險評估和應對策略

### ⚠️ 高風險項目

1. **Phase 1數據不足**
   - **風險**: 可見性合規<70%，缺乏足夠訓練數據
   - **應對**: 開發數據增強技術，合成訓練場景

2. **RL訓練不收斂**
   - **風險**: 複雜環境導致訓練不穩定
   - **應對**: 課程學習，漸進式複雜度提升

3. **實時性能不達標**
   - **風險**: 推理延遲過高，無法滿足實時要求
   - **應對**: 模型壓縮、硬體加速

### 🛡️ 緩解措施

```python
# 數據增強策略
class DataAugmentation:
    def augment_phase1_data(self, original_data):
        """基於Phase 1數據生成更多訓練場景"""
        augmented_scenarios = []
        
        # 1. 時間窗口擴展
        augmented_scenarios.extend(self._temporal_augmentation(original_data))
        
        # 2. 噪聲注入
        augmented_scenarios.extend(self._noise_injection(original_data))
        
        # 3. 極端場景合成
        augmented_scenarios.extend(self._extreme_scenario_synthesis(original_data))
        
        return augmented_scenarios

# 課程學習策略  
class CurriculumLearning:
    def __init__(self):
        self.stages = [
            {'name': 'basic', 'max_satellites': 5, 'duration': 1000},
            {'name': 'intermediate', 'max_satellites': 10, 'duration': 2000}, 
            {'name': 'advanced', 'max_satellites': 20, 'duration': 3000},
            {'name': 'full', 'max_satellites': None, 'duration': 5000}
        ]
    
    def get_current_stage(self, episode):
        """根據episode數決定當前訓練階段"""
        cumulative_duration = 0
        for stage in self.stages:
            cumulative_duration += stage['duration']
            if episode < cumulative_duration:
                return stage
        return self.stages[-1]  # 最終階段
```

---

## 📈 預期成果

### 🎓 學術成果
1. **頂級會議論文** (IEEE ICC/GLOBECOM, ACM MobiCom)
2. **期刊論文** (IEEE TWC, IEEE JSAC)
3. **開源項目** (GitHub, 完整文檔)

### 🏭 實用價值
1. **可部署的RL換手系統**
2. **性能基準測試套件**
3. **多星座適應框架**

### 💡 技術創新
1. **約束感知RL演算法**
2. **多目標衛星換手優化**
3. **Phase 1-2無縫整合架構**

---

**Phase 2實施計劃將確保LEO衛星RL系統的成功開發和部署，實現學術價值和實用價值的雙重突破！** 🚀

---

*計劃制定: 2025-08-15*  
*下次更新: Phase 1完成後*