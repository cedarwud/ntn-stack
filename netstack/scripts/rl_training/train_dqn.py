#!/usr/bin/env python3
"""
DQN LEO 衛星切換訓練腳本

使用 Deep Q-Network 訓練 LEO 衛星切換策略，整合現有的論文算法作為基準對比
"""

import sys
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# 確保能找到 netstack_api
sys.path.append('/app')

import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold, BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.evaluation import evaluate_policy

def setup_logging():
    """設置日誌"""
    log_dir = Path('/app/logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f'dqn_training_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class TrainingMetricsCallback(BaseCallback):
    """自定義回調函數，記錄訓練指標"""
    
    def __init__(self, check_freq: int = 1000, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.metrics = {
            'episode_rewards': [],
            'episode_lengths': [],
            'success_rates': [],
            'handover_latencies': [],
            'timestamps': []
        }
    
    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # 收集環境信息
            if hasattr(self.training_env.envs[0], 'get_wrapper_attr'):
                info = self.training_env.envs[0].get_wrapper_attr('get_episode_info')()
                if info:
                    self.metrics['success_rates'].append(info.get('handover_success_rate', 0))
                    self.metrics['handover_latencies'].append(info.get('average_handover_latency', 0))
                    self.metrics['timestamps'].append(datetime.now())
        
        return True

def create_environment(config=None):
    """創建 LEO 衛星切換環境"""
    if config is None:
        config = {
            'scenario': 'SINGLE_UE',
            'max_ues': 1,
            'max_satellites': 10,
            'episode_length': 100
        }
    
    try:
        # 導入環境
        import netstack_api.envs
        env = gym.make('netstack/LEOSatelliteHandover-v0')
        
        # 包裝環境以監控性能
        env = Monitor(env)
        
        logging.info(f"環境創建成功 - 觀測空間: {env.observation_space}")
        logging.info(f"動作空間: {env.action_space}")
        
        return env
    except Exception as e:
        logging.error(f"環境創建失敗: {e}")
        raise

def train_dqn_model(env, config=None):
    """訓練 DQN 模型"""
    if config is None:
        config = {
            'learning_rate': 1e-4,
            'buffer_size': 100000,
            'learning_starts': 1000,
            'batch_size': 32,
            'tau': 1.0,
            'gamma': 0.99,
            'train_freq': 4,
            'gradient_steps': 1,
            'target_update_interval': 1000,
            'exploration_fraction': 0.3,
            'exploration_initial_eps': 1.0,
            'exploration_final_eps': 0.05,
            'max_grad_norm': 10,
            'verbose': 1,
            'device': 'auto'
        }
    
    logging.info("開始訓練 DQN 模型...")
    logging.info(f"模型配置: {config}")
    
    # 創建 DQN 模型
    model = DQN(
        "MlpPolicy",
        env,
        **config
    )
    
    # 設置回調函數
    metrics_callback = TrainingMetricsCallback(check_freq=1000)
    
    # 創建評估環境
    eval_env = Monitor(gym.make('netstack/LEOSatelliteHandover-v0'))
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='/app/models/dqn_best/',
        log_path='/app/logs/',
        eval_freq=5000,
        deterministic=True,
        render=False
    )
    
    # 停止訓練回調（當達到目標獎勵時）
    stop_callback = StopTrainingOnRewardThreshold(
        reward_threshold=15.0,  # 目標獎勵閾值
        verbose=1
    )
    
    # 開始訓練
    start_time = time.time()
    model.learn(
        total_timesteps=100000,
        callback=[metrics_callback, eval_callback, stop_callback],
        log_interval=10
    )
    training_time = time.time() - start_time
    
    logging.info(f"訓練完成，耗時: {training_time:.2f} 秒")
    
    # 保存最終模型
    model_dir = Path('/app/models')
    model_dir.mkdir(exist_ok=True)
    model.save(model_dir / 'dqn_final')
    
    return model, metrics_callback.metrics

def evaluate_model(model, env, n_episodes=100):
    """評估模型性能"""
    logging.info(f"開始評估模型，運行 {n_episodes} 個 episodes...")
    
    # 使用 stable-baselines3 的評估函數
    mean_reward, std_reward = evaluate_policy(
        model, 
        env, 
        n_eval_episodes=n_episodes,
        deterministic=True
    )
    
    # 詳細評估
    episode_rewards = []
    success_rates = []
    handover_latencies = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
        
        episode_rewards.append(episode_reward)
        success_rates.append(info.get('handover_success_rate', 0))
        handover_latencies.append(info.get('average_handover_latency', 0))
    
    results = {
        'mean_reward': mean_reward,
        'std_reward': std_reward,
        'episode_rewards': episode_rewards,
        'mean_success_rate': np.mean(success_rates),
        'std_success_rate': np.std(success_rates),
        'mean_latency': np.mean(handover_latencies),
        'std_latency': np.std(handover_latencies),
        'episodes_evaluated': n_episodes
    }
    
    logging.info(f"評估結果:")
    logging.info(f"  平均獎勵: {results['mean_reward']:.3f} ± {results['std_reward']:.3f}")
    logging.info(f"  平均成功率: {results['mean_success_rate']:.3f} ± {results['std_success_rate']:.3f}")
    logging.info(f"  平均延遲: {results['mean_latency']:.1f} ± {results['std_latency']:.1f} ms")
    
    return results

def save_results(training_metrics, evaluation_results, config):
    """保存訓練和評估結果"""
    results_dir = Path('/app/results')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存綜合結果
    results = {
        'timestamp': timestamp,
        'algorithm': 'DQN',
        'config': config,
        'training_metrics': training_metrics,
        'evaluation_results': evaluation_results
    }
    
    results_file = results_dir / f'dqn_results_{timestamp}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 生成訓練曲線圖
    if training_metrics['episode_rewards']:
        plt.figure(figsize=(12, 8))
        
        # 子圖1: 獎勵曲線
        plt.subplot(2, 2, 1)
        plt.plot(training_metrics['episode_rewards'])
        plt.title('Episode Rewards')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
        
        # 子圖2: 成功率
        if training_metrics['success_rates']:
            plt.subplot(2, 2, 2)
            plt.plot(training_metrics['success_rates'])
            plt.title('Handover Success Rate')
            plt.xlabel('Check Point')
            plt.ylabel('Success Rate')
            plt.ylim(0, 1.1)
            plt.grid(True)
        
        # 子圖3: 延遲
        if training_metrics['handover_latencies']:
            plt.subplot(2, 2, 3)
            plt.plot(training_metrics['handover_latencies'])
            plt.title('Average Handover Latency')
            plt.xlabel('Check Point')
            plt.ylabel('Latency (ms)')
            plt.grid(True)
        
        # 子圖4: 評估結果分佈
        plt.subplot(2, 2, 4)
        plt.hist(evaluation_results['episode_rewards'], bins=20, alpha=0.7)
        plt.title('Evaluation Reward Distribution')
        plt.xlabel('Episode Reward')
        plt.ylabel('Frequency')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(results_dir / f'dqn_training_curves_{timestamp}.png', dpi=300)
        plt.close()
    
    logging.info(f"結果已保存到: {results_file}")
    return results_file

def compare_with_baseline(evaluation_results):
    """與基準算法對比"""
    # 基準性能 (從現有論文算法或簡單策略)
    baseline_performance = {
        'mean_latency': 25.0,  # ms (IEEE INFOCOM 2024 論文基準)
        'mean_success_rate': 0.90,  # 90% 成功率
        'name': 'IEEE INFOCOM 2024 Baseline'
    }
    
    # 計算改善程度
    latency_improvement = (baseline_performance['mean_latency'] - evaluation_results['mean_latency']) / baseline_performance['mean_latency'] * 100
    success_improvement = (evaluation_results['mean_success_rate'] - baseline_performance['mean_success_rate']) / baseline_performance['mean_success_rate'] * 100
    
    comparison = {
        'baseline': baseline_performance,
        'dqn_performance': {
            'mean_latency': evaluation_results['mean_latency'],
            'mean_success_rate': evaluation_results['mean_success_rate'],
            'name': 'DQN Algorithm'
        },
        'improvements': {
            'latency_improvement_percent': latency_improvement,
            'success_improvement_percent': success_improvement
        }
    }
    
    logging.info(f"與基準算法對比:")
    logging.info(f"  延遲改善: {latency_improvement:.1f}%")
    logging.info(f"  成功率改善: {success_improvement:.1f}%")
    
    return comparison

def main():
    """主函數"""
    try:
        # 設置日誌
        logger = setup_logging()
        logger.info("開始 DQN LEO 衛星切換訓練...")
        
        # 創建環境
        env = create_environment()
        
        # 訓練配置
        training_config = {
            'learning_rate': 1e-4,
            'buffer_size': 100000,
            'learning_starts': 1000,
            'batch_size': 32,
            'target_update_interval': 1000,
            'exploration_fraction': 0.3,
            'exploration_final_eps': 0.05,
            'verbose': 1
        }
        
        # 訓練模型
        model, training_metrics = train_dqn_model(env, training_config)
        
        # 評估模型
        evaluation_results = evaluate_model(model, env, n_episodes=100)
        
        # 與基準算法對比
        comparison = compare_with_baseline(evaluation_results)
        
        # 保存結果
        results_file = save_results(training_metrics, evaluation_results, training_config)
        
        # 輸出最終結果摘要
        logger.info("=" * 60)
        logger.info("DQN 訓練完成！")
        logger.info(f"平均獎勵: {evaluation_results['mean_reward']:.3f}")
        logger.info(f"切換成功率: {evaluation_results['mean_success_rate']:.1%}")
        logger.info(f"平均延遲: {evaluation_results['mean_latency']:.1f} ms")
        logger.info(f"與基準算法延遲改善: {comparison['improvements']['latency_improvement_percent']:.1f}%")
        logger.info("=" * 60)
        
        # 關閉環境
        env.close()
        
        return True
        
    except Exception as e:
        logger.error(f"訓練過程發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)