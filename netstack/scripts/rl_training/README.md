# 🤖 RL 訓練腳本

本目錄包含 LEO 衛星切換 RL 算法的完整訓練腳本。

## 📁 檔案結構

```
rl_training/
├── README.md                # 本文件
├── verify_algorithms.py     # 快速驗證腳本
├── train_dqn.py            # DQN 訓練腳本
├── train_ppo.py            # PPO 訓練腳本
└── train_sac.py            # SAC 訓練腳本
```

## 🚀 使用方式

### 1. 快速驗證（推薦第一步）

```bash
# 在容器內執行驗證
docker exec netstack-api python /app/scripts/rl_training/verify_algorithms.py

# 預期輸出
🔍 開始 RL 算法整合驗證...
🧪 測試環境基本功能...
✅ 環境重置成功 - 觀測維度: 152
✅ 環境步驟成功 - 獎勵: 2.345
🤖 快速測試 DQN 算法...
✅ DQN 測試成功:
   訓練時間: 12.3s
   平均獎勵: 8.567
   成功率: 85.0%
   平均延遲: 28.5ms
...
🎉 所有算法驗證成功！可以開始完整訓練。
```

### 2. 完整訓練

#### DQN 訓練
```bash
# 基本 Q-Learning 算法，適合離散動作
docker exec netstack-api python /app/scripts/rl_training/train_dqn.py

# 預期訓練時間: 15-30 分鐘
# 預期結果: 平均獎勵 15+, 成功率 92%+, 延遲 < 30ms
```

#### PPO 訓練
```bash
# 策略梯度算法，更穩定的訓練
docker exec netstack-api python /app/scripts/rl_training/train_ppo.py

# 預期訓練時間: 20-40 分鐘
# 預期結果: 平均獎勵 18+, 成功率 95%+, 延遲 < 25ms
```

#### SAC 訓練
```bash
# 軟演員-評論家算法，最佳連續控制
docker exec netstack-api python /app/scripts/rl_training/train_sac.py

# 預期訓練時間: 30-60 分鐘
# 預期結果: 平均獎勵 20+, 成功率 97%+, 延遲 < 20ms
```

## 📊 算法特性對比

| 算法 | 適用場景 | 優勢 | 劣勢 | 訓練時間 |
|------|----------|------|------|----------|
| **DQN** | 簡單離散決策 | 穩定、易理解 | 離散動作限制 | 最短 |
| **PPO** | 複雜策略學習 | 穩定、樣本效率 | 需要調參 | 中等 |
| **SAC** | 精細連續控制 | 最優性能 | 複雜、需大量數據 | 最長 |

## 🎯 預期性能指標

### 成功標準
- **DQN**: 獎勵 > 15, 成功率 > 90%, 延遲 < 30ms
- **PPO**: 獎勵 > 18, 成功率 > 95%, 延遲 < 25ms  
- **SAC**: 獎勵 > 20, 成功率 > 97%, 延遲 < 20ms

### 與基準對比
- **IEEE INFOCOM 2024**: 延遲 25ms, 成功率 90%
- **預期改善**: 20-40% 延遲改善, 5-7% 成功率提升

## 📁 輸出檔案

### 訓練過程中生成
```
/app/
├── logs/                   # 訓練日誌
│   ├── dqn_training_*.log
│   ├── ppo_training_*.log
│   └── sac_training_*.log
├── models/                 # 訓練模型
│   ├── dqn_final.zip
│   ├── dqn_best/
│   ├── ppo_final.zip
│   ├── ppo_best/
│   ├── sac_final.zip
│   └── sac_best/
├── results/                # 結果數據
│   ├── dqn_results_*.json
│   ├── ppo_results_*.json
│   └── sac_results_*.json
└── reports/                # 驗證報告
    └── rl_verification_report_*.txt
```

### 可視化輸出
```
/app/results/
├── dqn_training_curves_*.png      # DQN 訓練曲線
├── ppo_training_analysis_*.png    # PPO 分析圖表
└── sac_control_analysis_*.png     # SAC 控制分析
```

## 🔧 配置調整

### DQN 參數調整
```python
# train_dqn.py 中修改配置
training_config = {
    'learning_rate': 1e-4,      # 學習率
    'buffer_size': 100000,      # 經驗池大小
    'exploration_fraction': 0.3, # 探索比例
    'target_update_interval': 1000  # 目標網路更新間隔
}
```

### PPO 參數調整
```python
# train_ppo.py 中修改配置
training_config = {
    'learning_rate': 3e-4,      # 學習率
    'n_steps': 2048,            # 收集步數
    'batch_size': 64,           # 批次大小
    'n_epochs': 10              # 訓練輪數
}
```

### SAC 參數調整
```python
# train_sac.py 中修改配置
training_config = {
    'learning_rate': 3e-4,      # 學習率
    'buffer_size': 1000000,     # 經驗池大小
    'batch_size': 256,          # 批次大小
    'ent_coef': 'auto'          # 熵係數（自動調整）
}
```

## 🐛 故障排除

### 常見問題

#### 1. 環境創建失敗
```bash
# 檢查環境註冊
docker exec netstack-api python -c "
import netstack_api.envs
import gymnasium as gym
print([env for env in gym.envs.registry.env_specs.keys() if 'netstack' in env])
"
```

#### 2. 訓練過程中記憶體不足
```python
# 減少批次大小或經驗池大小
'batch_size': 32,        # 從 64 改為 32
'buffer_size': 50000,    # 從 100000 改為 50000
```

#### 3. 訓練不收斂
```python
# 調整學習率
'learning_rate': 1e-5,   # 降低學習率
'exploration_fraction': 0.5,  # 增加探索
```

#### 4. SAC 動作空間問題
```python
# 檢查動作空間類型
env = gym.make('netstack/LEOSatelliteHandover-v0')
print(f"動作空間類型: {type(env.action_space)}")
print(f"動作空間: {env.action_space}")
```

### 日誌檢查
```bash
# 查看最新訓練日誌
docker exec netstack-api tail -f /app/logs/dqn_training_*.log

# 查看錯誤日誌
docker exec netstack-api grep ERROR /app/logs/*.log
```

## 📈 性能優化建議

### 1. 硬體資源
- **CPU**: 推薦 4+ 核心
- **記憶體**: 推薦 8GB+ RAM
- **GPU**: 可選，但會顯著加速 SAC 訓練

### 2. 訓練參數
- **並行環境**: PPO 使用 4 個並行環境
- **經驗池**: SAC 使用大型經驗池 (1M steps)
- **評估頻率**: 根據訓練時間調整評估間隔

### 3. 環境配置
- **Episode 長度**: DQN(100) < PPO(200) < SAC(500)
- **場景複雜度**: 從簡單開始，逐步增加

## 🎓 後續研究方向

### 1. 多目標優化
```python
# 修改獎勵函數支援多目標
def multi_objective_reward(latency, qos, energy):
    return weighted_sum([latency_reward, qos_reward, energy_reward])
```

### 2. 聯邦學習
```python
# 分散式訓練架構
class FederatedRLTrainer:
    def aggregate_models(self, local_models):
        # 模型聚合邏輯
        pass
```

### 3. 遷移學習
```python
# 從簡單場景遷移到複雜場景
pretrained_model = DQN.load("/app/models/dqn_simple_scenario")
model = DQN("MlpPolicy", complex_env, 
           policy_kwargs={"net_arch": pretrained_model.policy.mlp_extractor.policy_net})
```

## 📚 參考資源

- [Stable-Baselines3 文檔](https://stable-baselines3.readthedocs.io/)
- [Gymnasium 文檔](https://gymnasium.farama.org/)
- [LEO 切換環境文檔](/gymnasium.md)
- [專案實施計劃](/gym_todo.md)

## 📝 更新歷史

| 日期 | 版本 | 更新內容 |
|------|------|----------|
| 2025-06-23 | v1.0 | 初版：DQN, PPO, SAC 完整訓練腳本 |

---

**最後更新**: 2025年6月23日  
**維護者**: Claude Code Assistant