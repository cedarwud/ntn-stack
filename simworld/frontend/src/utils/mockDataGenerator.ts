/**
 * 模擬數據生成器
 * 為各種組件提供初始化數據
 */

// RL 訓練指標初始化
export const createInitialTrainingMetrics = () => ({
    dqn: {
        episodes: 0,
        avgReward: 0,
        progress: 0,
        handoverDelay: 45,
        successRate: 82,
        signalDropTime: 18,
        energyEfficiency: 0.75,
    },
    ppo: {
        episodes: 0,
        avgReward: 0,
        progress: 0,
        handoverDelay: 42,
        successRate: 85,
        signalDropTime: 16,
        energyEfficiency: 0.78,
    },
    sac: {
        episodes: 0,
        avgReward: 0,
        progress: 0,
        handoverDelay: 38,
        successRate: 88,
        signalDropTime: 14,
        energyEfficiency: 0.82,
    },
})

// RL 獎勵趨勢數據初始化
export const createInitialRLData = () => ({
    labels: Array.from({ length: 20 }, (_, i) => `${i + 1}`),
    dqnData: [],
    ppoData: [],
    sacData: [],
})

// Policy Loss 數據初始化
export const createInitialPolicyLossData = () => ({
    labels: Array.from({ length: 20 }, (_, i) => `${i + 1}`),
    dqnData: [],
    ppoData: [],
    sacData: [],
})

// 圖表分析模擬數據生成
export const createMockData = () => {
    // 可以根據需要添加其他模擬數據
    return {
        chartData: {},
        performanceData: {},
        systemData: {},
    }
}