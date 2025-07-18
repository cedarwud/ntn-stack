# 當前獎勵數據來源分析

## 概述

當前系統中的獎勵數據主要來自兩個來源：
1. **真實 NetStack API 響應**（當 API 可用時）
2. **模擬數據生成**（當 API 不可用時，作為後備方案）

## 數據來源詳細分析

### 1. 真實 API 數據來源

**位置：** `ExperimentControlSection.tsx` 第180-240行

**API 端點嘗試順序：**
```javascript
const endpoints = [
    `/api/v1/rl/training/status/${experimentConfig.algorithm}`,
    `/api/v1/rl/enhanced/status/${experimentConfig.algorithm}`,
    `/api/v1/rl/status`,
    `/api/v1/rl/phase-2-3/system/status`,
]
```

**數據提取邏輯：**
```javascript
current_reward: status.training_progress?.current_reward || 
                status.metrics?.current_reward || 
                status.reward || 
                0,
average_reward: status.training_progress?.average_reward || 
                status.metrics?.average_reward || 
                status.avg_reward || 
                0,
```

### 2. 模擬數據生成（當前主要使用）

**位置：** `ExperimentControlSection.tsx` 第275-310行

**獎勵計算公式：**

#### 當前獎勵 (current_reward)
```javascript
const progress = currentEpisode / experimentConfig.total_episodes
const baseReward = -50 + progress * 100  // 從-50逐漸提升到50
const rewardVariance = 20 * (1 - progress * 0.5)  // 方差隨時間減小

current_reward = baseReward + (Math.random() - 0.5) * rewardVariance
```

**計算邏輯說明：**
- **基礎獎勵：** 隨訓練進度線性增長，從-50提升到+50
- **隨機變化：** 添加隨機噪聲模擬真實訓練的波動
- **方差衰減：** 隨著訓練進行，獎勵變化幅度逐漸減小（更穩定）

#### 平均獎勵 (average_reward)
```javascript
average_reward = baseReward + (Math.random() - 0.5) * rewardVariance * 0.3
```

**計算邏輯說明：**
- 基於相同的基礎獎勵
- 變化幅度比當前獎勵小（30%），模擬平均值的穩定性

### 3. 獎勵數據的真實性評估

#### 優點：
1. **漸進式改善：** 獎勵隨訓練進度逐漸提升，符合強化學習的預期
2. **合理波動：** 包含隨機變化，模擬真實訓練的不確定性
3. **穩定性增加：** 後期變化幅度減小，符合收斂特性

#### 限制：
1. **純數學模擬：** 不反映真實的環境交互和學習效果
2. **缺乏算法特異性：** 不同算法（DQN、PPO、SAC）使用相同的獎勵模式
3. **無環境依賴：** 不考慮具體的LEO衛星切換場景特性

### 4. 改進建議

#### 短期改進：
1. **算法特異性獎勵：**
```javascript
const getAlgorithmSpecificReward = (algorithm, progress) => {
    switch(algorithm) {
        case 'dqn': return -60 + progress * 110  // DQN通常開始較差
        case 'ppo': return -40 + progress * 90   // PPO較穩定
        case 'sac': return -45 + progress * 95   // SAC中等表現
    }
}
```

2. **場景相關獎勵：**
```javascript
const getScenarioReward = (scenario, baseReward) => {
    const scenarioMultipliers = {
        'urban': 0.8,        // 城市環境較困難
        'maritime': 1.1,     // 海洋環境較簡單
        'high_speed': 0.7    // 高速移動最困難
    }
    return baseReward * (scenarioMultipliers[scenario] || 1.0)
}
```

#### 長期改進：
1. **真實 RL 後端整合：** 連接到實際的強化學習訓練系統
2. **歷史數據記錄：** 保存和分析真實的訓練歷史
3. **性能基準：** 建立不同場景下的性能基準線

## 當前狀態總結

**數據來源：** 主要是模擬數據（因為 NetStack RL API 端點返回 404）
**數據質量：** 數學上合理，但缺乏真實性
**適用性：** 適合演示和 UI 測試，不適合真實研究

**建議：** 優先修復 NetStack RL API 連接，或實現更精確的模擬邏輯。
