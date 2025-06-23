# 🏋️ NTN Stack Gymnasium 環境使用指南

本文檔提供 NTN Stack 專案中所有 Gymnasium 強化學習環境的完整使用指南。

## 📚 目錄

1. [環境總覽](#環境總覽)
2. [LEO 衛星切換環境](#leo-衛星切換環境)
3. [其他 RL 環境](#其他-rl-環境)
4. [前端監控組件](#前端監控組件)
5. [開發指南](#開發指南)
6. [故障排除](#故障排除)

---

## 🌟 環境總覽

NTN Stack 提供以下 Gymnasium 環境：

| 環境 ID | 描述 | 狀態 | 適用算法 |
|---------|------|------|----------|
| `netstack/LEOSatelliteHandover-v0` | LEO 衛星切換優化 | ✅ **可用** | DQN, PPO, SAC |
| `netstack/InterferenceMitigation-v0` | 干擾緩解 | ✅ 可用 | DQN |
| `netstack/NetworkOptimization-v0` | 網路優化 | ✅ 可用 | PPO, SAC |
| `netstack/UAVFormation-v0` | UAV 編隊管理 | ✅ 可用 | Multi-Agent RL |

---

## 🛰️ LEO 衛星切換環境

### 概述

LEO 衛星切換環境是專門設計用於優化 LEO 衛星網路中的切換決策，支持與任何論文基準算法對比。

**核心特性**：
- 🎯 多目標優化 (延遲 + QoS + 負載平衡)
- 🔄 支援單UE和多UE場景
- 📊 完整的性能指標追蹤
- 🚀 高性能 (20,000+ FPS)

### 快速開始

```python
import gymnasium as gym

# 創建環境
env = gym.make('netstack/LEOSatelliteHandover-v0')

# 基本使用流程
obs, info = env.reset()
print(f"UE數量: {info['active_ue_count']}")
print(f"衛星數量: {info['active_satellite_count']}")

# 執行動作
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)

print(f"獎勵: {reward:.3f}")
print(f"切換成功率: {info['handover_success_rate']:.3f}")
print(f"平均延遲: {info['average_handover_latency']:.1f}ms")

env.close()
```

### 環境配置

#### 基本配置

```python
from netstack_api.envs.handover_env_fixed import LEOSatelliteHandoverEnv, HandoverScenario

# 單UE場景 (適合初學者)
env = LEOSatelliteHandoverEnv(
    scenario=HandoverScenario.SINGLE_UE,
    max_ues=1,
    max_satellites=10,
    episode_length=100
)

# 多UE場景 (適合進階研究)
env = LEOSatelliteHandoverEnv(
    scenario=HandoverScenario.MULTI_UE,
    max_ues=5,
    max_satellites=20,
    episode_length=200
)
```

#### 進階配置

```python
# 大規模場景
env = LEOSatelliteHandoverEnv(
    scenario=HandoverScenario.LOAD_BALANCE,
    max_ues=10,
    max_satellites=50,
    episode_length=1000,
    config={
        "learning_rate": 3e-4,
        "exploration_fraction": 0.3,
        "target_update_interval": 1000
    }
)
```

### 狀態空間說明

**觀測維度**: 可變 (依據 UE 和衛星數量)

**狀態組成**:
- **UE狀態** (每個UE 13維):
  - 位置座標 (緯度, 經度, 高度)
  - 移動速度 (vx, vy, vz)
  - 信號品質 (信號強度, SINR, 吞吐量, 延遲)
  - 服務狀態 (封包遺失率, 電池電量, 連接狀態)

- **衛星狀態** (每顆衛星 9維):
  - 位置座標 (緯度, 經度, 高度)
  - 相對角度 (仰角, 方位角)
  - 服務狀況 (距離, 負載, 頻寬, 可用性)

- **環境狀態** (7維):
  - 時間進度, 天氣狀況, 干擾水平
  - 網路壅塞, 系統統計

### 動作空間說明

#### 單UE場景 (Dict 格式)

```python
action_space = {
    'handover_decision': Discrete(3),    # 0: 不切換, 1: 觸發切換, 2: 準備切換
    'target_satellite': Discrete(50),    # 目標衛星 ID
    'timing': Box(0.0, 10.0, (1,)),     # 切換時機 (秒)
    'power_control': Box(0.0, 1.0, (1,)), # 功率控制因子
    'priority': Box(0.0, 1.0, (1,))     # 切換優先級
}
```

#### 多UE場景 (Box 格式)

```python
# 每個UE 6個動作參數
action_space = Box(0.0, 1.0, shape=(max_ues * 6,))
```

### 獎勵函數設計

**多目標獎勵函數**：

```python
total_reward = (
    latency_reward +      # 切換延遲獎勵 (越低越好)
    sinr_reward +         # 信號品質獎勵
    throughput_reward +   # 吞吐量獎勵  
    timing_reward +       # 時機選擇獎勵
    balance_reward -      # 負載平衡獎勵
    failure_penalty -     # 切換失敗懲罰
    congestion_penalty    # 過度切換懲罰
)
```

**具體計算**：
- **延遲獎勵**: `max(0, 100 - latency) / 100 * 10`
- **SINR獎勵**: `max(0, sinr) / 40 * 5`
- **時機獎勵**: `max(0, 5 - abs(timing - 2.0)) / 5 * 2`
- **失敗懲罰**: `-10` (每次失敗)

### 性能指標

環境提供詳細的性能指標：

```python
info = {
    'handover_success_rate': 0.95,      # 切換成功率
    'average_handover_latency': 25.3,   # 平均延遲 (ms)
    'total_handovers': 10,              # 總切換次數
    'service_interruptions': 1,         # 服務中斷次數
    'average_sinr': 20.5,               # 平均 SINR (dB)
    'network_congestion': 0.3           # 網路壅塞度
}
```

### RL 算法整合

#### DQN 範例

```python
from stable_baselines3 import DQN
from netstack_api.rl.engine import GymnasiumEngine

# 使用 RL Engine 框架
rl_engine = GymnasiumEngine(
    env_name="netstack/LEOSatelliteHandover-v0",
    algorithm="DQN",
    config={
        "learning_rate": 1e-4,
        "buffer_size": 100000,
        "exploration_fraction": 0.3
    }
)

# 訓練
await rl_engine.train(episodes=1000)

# 獲取動作
state = {"sinr": 15.0, "signal_strength": -80}
action = await rl_engine.get_action(state)
```

#### PPO 範例

```python
from stable_baselines3 import PPO

env = gym.make('netstack/LEOSatelliteHandover-v0')

model = PPO(
    "MlpPolicy", 
    env,
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    verbose=1
)

# 訓練
model.learn(total_timesteps=100000)

# 測試
obs, info = env.reset()
for _ in range(100):
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

### 論文對比研究

環境設計支援與任何論文算法對比：

```python
# 與 IEEE INFOCOM 2024 論文對比
baseline_latency = 25.0  # 論文報告的延遲

# 評估 RL 算法
rl_latency = info['average_handover_latency']
improvement = (baseline_latency - rl_latency) / baseline_latency * 100

print(f"RL 算法改善: {improvement:.1f}%")
```

### 測試與驗證

運行完整測試：

```bash
# 在容器內執行
docker exec netstack-api python /app/test_leo_handover_permanent.py

# 或移到專案測試目錄
python tests/gymnasium/test_leo_handover_permanent.py
```

**測試涵蓋**：
- ✅ 基本功能測試
- ✅ 完整回合測試  
- ✅ 不同場景測試
- ✅ 獎勵函數測試
- ✅ 觀測空間測試
- ✅ 性能基準測試

---

## 🔧 其他 RL 環境

### 干擾緩解環境

```python
env = gym.make('netstack/InterferenceMitigation-v0')
# 用於 AI-RAN 抗干擾研究
```

### 網路優化環境

```python
env = gym.make('netstack/NetworkOptimization-v0')
# 用於網路參數優化
```

### UAV 編隊環境

```python
env = gym.make('netstack/UAVFormation-v0')
# 用於無人機群組協調
```

---

## 📊 前端監控組件

### 已實現的前端組件

#### 🎯 高優先級組件

1. **GymnasiumRLMonitor** - 核心監控儀表板
   - 引擎狀態實時監控 (Gymnasium vs Legacy)
   - 訓練進度和性能指標
   - 一鍵引擎切換控制
   - 服務健康狀態總覽

2. **RLDecisionComparison** - 性能對比分析
   - A/B 測試自動化
   - 不同場景下的性能對比
   - 詳細指標分析 (響應時間、成功率、SINR改善)

3. **RLEnvironmentVisualization** - 環境狀態可視化
   - 狀態空間熱力圖顯示
   - 動作空間實時可視化
   - 特徵解釋和說明

#### 🎨 中優先級組件

4. **訓練曲線可視化**
   - 獎勵函數趨勢圖
   - 損失函數變化
   - 探索率 (epsilon) 衰減曲線

5. **決策路徑追蹤**
   - 決策樹可視化
   - 置信度熱力圖
   - 不確定性分析

### 前端整合建議

**整合方式**：
1. 在主導航中添加「RL 監控」選項
2. 在現有 Dashboard 中嵌入核心指標
3. 作為獨立分析頁面提供詳細功能

---

## 👨‍💻 開發指南

### 新增環境

1. **創建環境檔案**：
   ```python
   # /netstack/netstack_api/envs/my_new_env.py
   class MyNewEnv(gym.Env):
       def __init__(self):
           # 環境初始化
           pass
       
       def reset(self):
           # 重置邏輯
           pass
       
       def step(self, action):
           # 步驟邏輯
           pass
   ```

2. **註冊環境**：
   ```python
   # /netstack/netstack_api/envs/__init__.py
   register(
       id='netstack/MyNewEnv-v0',
       entry_point='netstack_api.envs.my_new_env:MyNewEnv',
       max_episode_steps=1000,
   )
   ```

3. **建立測試**：
   ```python
   # /tests/gymnasium/test_my_new_env.py
   def test_my_new_env():
       env = gym.make('netstack/MyNewEnv-v0')
       # 測試邏輯
   ```

### 環境設計最佳實踐

1. **狀態正規化**: 確保所有觀測值在合理範圍內
2. **獎勵設計**: 平衡多個目標，避免獎勵稀疏
3. **動作空間**: 設計符合實際應用的動作約束
4. **性能優化**: 避免不必要的計算，確保高 FPS
5. **錯誤處理**: 提供優雅的錯誤處理和回退機制

---

## 🔍 故障排除

### 常見問題

**Q: 環境創建失敗**
```bash
# 檢查環境註冊
docker exec netstack-api python -c "
import netstack_api.envs
import gymnasium as gym
print([env_id for env_id in gym.envs.registry.env_specs.keys() if 'netstack' in env_id])
"
```

**Q: 觀測空間維度錯誤**
```python
# 檢查觀測空間配置
env = gym.make('netstack/LEOSatelliteHandover-v0')
print(f"觀測空間: {env.observation_space}")
print(f"動作空間: {env.action_space}")
```

**Q: 獎勵異常**
```python
# 檢查獎勵計算
obs, info = env.reset()
action = env.action_space.sample()
obs, reward, term, trunc, info = env.step(action)
print(f"獎勵: {reward}, 切換結果: {info.get('handover_results', [])}")
```

### 效能調優

1. **減少 UE/衛星數量** (開發階段)
2. **降低 episode 長度**
3. **使用向量化環境**
4. **啟用 GPU 加速** (如果可用)

### 日誌除錯

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 環境會輸出詳細日誌
env = gym.make('netstack/LEOSatelliteHandover-v0')
```

---

## 📈 性能基準

### LEO Handover 環境基準

- **重置時間**: ~0.0001s
- **步驟時間**: ~0.00005s  
- **估計 FPS**: 20,000+
- **記憶體使用**: ~50MB (單環境)

### 建議硬體需求

- **CPU**: 4+ 核心
- **記憶體**: 8GB+ RAM
- **GPU**: 可選 (用於大規模訓練)

---

## 📝 更新歷史

| 日期 | 版本 | 更新內容 |
|------|------|----------|
| 2025-06-23 | v1.0 | 初版：LEO 衛星切換環境完整實現 |
| 2025-06-23 | v1.1 | 修復數據類型錯誤，添加完整測試 |

---

## 🤝 貢獻指南

1. **提交新環境**: 遵循現有架構模式
2. **改進現有環境**: 確保向後相容性
3. **更新文檔**: 同步更新此檔案
4. **測試覆蓋**: 為新功能添加測試

---

## 📞 聯絡與支援

如有問題或建議，請：
1. 檢查此文檔的故障排除章節
2. 運行測試腳本驗證環境狀態
3. 查看容器日誌獲取詳細資訊

**最後更新**: 2025年6月23日  
**文檔版本**: v1.1