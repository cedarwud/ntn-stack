export interface RLEngineMetrics {
    engine_type: 'dqn' | 'ppo' | 'sac' | 'null' | 'DQN' | 'PPO' | 'SAC'
    algorithm: string
    environment: string
    model_status: 'training' | 'inference' | 'idle' | 'error'
    episodes_completed: number
    average_reward: number
    current_epsilon: number
    training_progress: number
    prediction_accuracy: number
    response_time_ms: number
    memory_usage: number
    gpu_utilization?: number
} 