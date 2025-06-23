#!/usr/bin/env python3
"""
PPO LEO 衛星切換訓練腳本

使用 Proximal Policy Optimization 訓練 LEO 衛星切換策略
相比 DQN，PPO 提供更穩定的訓練和更好的樣本效率
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
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold, BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_util import make_vec_env

def setup_logging():
    """設置日誌"""
    log_dir = Path('/app/logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f'ppo_training_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class PPOMetricsCallback(BaseCallback):
    """PPO 專用訓練指標回調"""
    
    def __init__(self, check_freq: int = 2048, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.metrics = {
            'episode_rewards': [],
            'policy_losses': [],
            'value_losses': [],
            'entropy_losses': [],
            'success_rates': [],
            'handover_latencies': [],
            'learning_rates': [],
            'timestamps': []
        }
    
    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # 記錄學習率
            if hasattr(self.model, 'lr_schedule'):
                current_lr = self.model.lr_schedule(self.model._current_progress_remaining)
                self.metrics['learning_rates'].append(current_lr)
            
            # 嘗試獲取環境信息
            try:
                if hasattr(self.training_env, 'envs') and len(self.training_env.envs) > 0:
                    env = self.training_env.envs[0]
                    if hasattr(env, 'get_wrapper_attr'):
                        info = env.get_wrapper_attr('get_episode_info')()
                        if info:
                            self.metrics['success_rates'].append(info.get('handover_success_rate', 0))
                            self.metrics['handover_latencies'].append(info.get('average_handover_latency', 0))
            except:
                pass
            
            self.metrics['timestamps'].append(datetime.now())
        
        return True

def create_environment(n_envs=1, config=None):
    """創建 LEO 衛星切換環境（支援向量化）"""
    if config is None:
        config = {
            'scenario': 'SINGLE_UE',
            'max_ues': 1,
            'max_satellites': 10,
            'episode_length': 200  # PPO 適合較長的 episodes
        }
    
    def make_env():
        import netstack_api.envs
        env = gym.make('netstack/LEOSatelliteHandover-v0')
        env = Monitor(env)
        return env
    
    if n_envs == 1:
        env = make_env()
        logging.info(f"單環境創建成功 - 觀測空間: {env.observation_space}")
    else:
        # 創建向量化環境提高樣本收集效率
        env = DummyVecEnv([make_env for _ in range(n_envs)])
        logging.info(f"向量化環境創建成功 - {n_envs} 個並行環境")
    
    logging.info(f"動作空間: {env.action_space if n_envs == 1 else env.envs[0].action_space}")
    return env

def train_ppo_model(env, config=None):
    """訓練 PPO 模型"""
    if config is None:
        config = {
            'learning_rate': 3e-4,
            'n_steps': 2048,          # 每次更新收集的步數
            'batch_size': 64,         # 小批次大小
            'n_epochs': 10,           # 每次更新的訓練輪數
            'gamma': 0.99,            # 折扣因子
            'gae_lambda': 0.95,       # GAE 參數
            'clip_range': 0.2,        # PPO 裁剪參數
            'clip_range_vf': None,    # 價值函數裁剪
            'ent_coef': 0.01,         # 熵正則化係數
            'vf_coef': 0.5,           # 價值函數損失係數
            'max_grad_norm': 0.5,     # 梯度裁剪
            'target_kl': 0.01,        # 目標 KL 散度
            'verbose': 1,
            'device': 'auto'
        }
    
    logging.info("開始訓練 PPO 模型...")
    logging.info(f"模型配置: {config}")
    
    # 創建 PPO 模型
    model = PPO(
        "MlpPolicy",
        env,
        **config
    )
    
    # 設置回調函數
    metrics_callback = PPOMetricsCallback(check_freq=config['n_steps'])
    
    # 創建評估環境
    eval_env = Monitor(gym.make('netstack/LEOSatelliteHandover-v0'))
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='/app/models/ppo_best/',
        log_path='/app/logs/',
        eval_freq=10000,          # PPO 評估頻率較低
        deterministic=True,
        render=False
    )
    
    # 停止訓練回調
    stop_callback = StopTrainingOnRewardThreshold(
        reward_threshold=18.0,    # PPO 預期更高的獎勵
        verbose=1
    )
    
    # 開始訓練
    start_time = time.time()
    model.learn(
        total_timesteps=200000,   # PPO 通常需要更多步數
        callback=[metrics_callback, eval_callback, stop_callback],
        log_interval=10
    )
    training_time = time.time() - start_time
    
    logging.info(f"PPO 訓練完成，耗時: {training_time:.2f} 秒")
    
    # 保存最終模型
    model_dir = Path('/app/models')
    model_dir.mkdir(exist_ok=True)
    model.save(model_dir / 'ppo_final')
    
    return model, metrics_callback.metrics

def evaluate_model(model, env, n_episodes=100):
    """評估 PPO 模型性能"""
    logging.info(f"開始評估 PPO 模型，運行 {n_episodes} 個 episodes...")
    
    # 確保使用單一環境進行評估
    if hasattr(env, 'envs'):
        eval_env = Monitor(gym.make('netstack/LEOSatelliteHandover-v0'))
    else:
        eval_env = env
    
    # 使用 stable-baselines3 的評估函數
    mean_reward, std_reward = evaluate_policy(
        model, 
        eval_env, 
        n_eval_episodes=n_episodes,
        deterministic=True
    )
    
    # 詳細評估
    episode_rewards = []
    success_rates = []
    handover_latencies = []
    action_entropies = []
    
    for episode in range(n_episodes):
        obs, info = eval_env.reset()
        episode_reward = 0
        done = False
        episode_actions = []
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            episode_actions.append(action)
            obs, reward, terminated, truncated, info = eval_env.step(action)
            episode_reward += reward
            done = terminated or truncated
        
        episode_rewards.append(episode_reward)
        success_rates.append(info.get('handover_success_rate', 0))
        handover_latencies.append(info.get('average_handover_latency', 0))
        
        # 計算動作熵（多樣性指標）
        if episode_actions:
            action_entropy = -np.mean([np.log(1e-8 + abs(a)) for a in episode_actions])
            action_entropies.append(action_entropy)
    
    results = {
        'mean_reward': mean_reward,
        'std_reward': std_reward,
        'episode_rewards': episode_rewards,
        'mean_success_rate': np.mean(success_rates),
        'std_success_rate': np.std(success_rates),
        'mean_latency': np.mean(handover_latencies),
        'std_latency': np.std(handover_latencies),
        'mean_action_entropy': np.mean(action_entropies) if action_entropies else 0,
        'episodes_evaluated': n_episodes
    }
    
    logging.info(f"PPO 評估結果:")
    logging.info(f"  平均獎勵: {results['mean_reward']:.3f} ± {results['std_reward']:.3f}")
    logging.info(f"  平均成功率: {results['mean_success_rate']:.3f} ± {results['std_success_rate']:.3f}")
    logging.info(f"  平均延遲: {results['mean_latency']:.1f} ± {results['std_latency']:.1f} ms")
    logging.info(f"  動作多樣性: {results['mean_action_entropy']:.3f}")
    
    return results

def analyze_policy_behavior(model, env, n_episodes=10):
    """分析 PPO 策略行為"""
    logging.info("分析 PPO 策略行為...")
    
    if hasattr(env, 'envs'):
        analysis_env = Monitor(gym.make('netstack/LEOSatelliteHandover-v0'))
    else:
        analysis_env = env
    
    policy_analysis = {
        'action_distributions': [],
        'state_value_estimates': [],
        'policy_confidence': [],
        'decision_patterns': []
    }
    
    for episode in range(n_episodes):
        obs, info = analysis_env.reset()
        done = False
        episode_values = []
        episode_actions = []
        
        while not done:
            # 獲取動作和狀態值
            action, _states = model.predict(obs, deterministic=False)
            
            # 如果可能，獲取狀態值估計
            try:
                if hasattr(model, 'predict_values'):
                    value = model.predict_values(obs)
                    episode_values.append(float(value))
            except:
                pass
            
            episode_actions.append(action)
            obs, reward, terminated, truncated, info = analysis_env.step(action)
            done = terminated or truncated
        
        policy_analysis['action_distributions'].append(episode_actions)
        policy_analysis['state_value_estimates'].append(episode_values)
    
    logging.info(f"策略分析完成，分析了 {n_episodes} 個 episodes")
    return policy_analysis

def save_results(training_metrics, evaluation_results, policy_analysis, config):
    """保存 PPO 訓練和評估結果"""
    results_dir = Path('/app/results')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存綜合結果
    results = {
        'timestamp': timestamp,
        'algorithm': 'PPO',
        'config': config,
        'training_metrics': training_metrics,
        'evaluation_results': evaluation_results,
        'policy_analysis': policy_analysis
    }
    
    results_file = results_dir / f'ppo_results_{timestamp}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 生成 PPO 專用可視化
    plt.figure(figsize=(15, 10))
    
    # 子圖1: 獎勵曲線
    plt.subplot(2, 3, 1)
    if training_metrics['episode_rewards']:
        plt.plot(training_metrics['episode_rewards'])
        plt.title('Episode Rewards (PPO)')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
    
    # 子圖2: 學習率變化
    plt.subplot(2, 3, 2)
    if training_metrics['learning_rates']:
        plt.plot(training_metrics['learning_rates'])
        plt.title('Learning Rate Schedule')
        plt.xlabel('Update')
        plt.ylabel('Learning Rate')
        plt.grid(True)
    
    # 子圖3: 成功率
    plt.subplot(2, 3, 3)
    if training_metrics['success_rates']:
        plt.plot(training_metrics['success_rates'])
        plt.title('Handover Success Rate')
        plt.xlabel('Check Point')
        plt.ylabel('Success Rate')
        plt.ylim(0, 1.1)
        plt.grid(True)
    
    # 子圖4: 延遲變化
    plt.subplot(2, 3, 4)
    if training_metrics['handover_latencies']:
        plt.plot(training_metrics['handover_latencies'])
        plt.title('Average Handover Latency')
        plt.xlabel('Check Point')
        plt.ylabel('Latency (ms)')
        plt.grid(True)
    
    # 子圖5: 評估獎勵分佈
    plt.subplot(2, 3, 5)
    plt.hist(evaluation_results['episode_rewards'], bins=20, alpha=0.7, color='green')
    plt.title('Evaluation Reward Distribution')
    plt.xlabel('Episode Reward')
    plt.ylabel('Frequency')
    plt.grid(True)
    
    # 子圖6: 動作分佈
    plt.subplot(2, 3, 6)
    if policy_analysis['action_distributions']:
        all_actions = [action for episode in policy_analysis['action_distributions'] for action in episode]
        plt.hist(all_actions, bins=20, alpha=0.7, color='orange')
        plt.title('Action Distribution')
        plt.xlabel('Action Value')
        plt.ylabel('Frequency')
        plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(results_dir / f'ppo_training_analysis_{timestamp}.png', dpi=300)
    plt.close()
    
    logging.info(f"PPO 結果已保存到: {results_file}")
    return results_file

def compare_with_dqn_and_baseline(evaluation_results):
    """與 DQN 和基準算法對比"""
    # 基準性能數據
    baselines = {
        'IEEE_INFOCOM_2024': {
            'mean_latency': 25.0,
            'mean_success_rate': 0.90,
            'name': 'IEEE INFOCOM 2024'
        },
        'DQN_Expected': {
            'mean_latency': 18.5,  # 基於 DQN 預期性能
            'mean_success_rate': 0.94,
            'name': 'DQN Algorithm'
        }
    }
    
    # 計算改善程度
    comparisons = {}
    for baseline_name, baseline_perf in baselines.items():
        latency_improvement = (baseline_perf['mean_latency'] - evaluation_results['mean_latency']) / baseline_perf['mean_latency'] * 100
        success_improvement = (evaluation_results['mean_success_rate'] - baseline_perf['mean_success_rate']) / baseline_perf['mean_success_rate'] * 100
        
        comparisons[baseline_name] = {
            'baseline': baseline_perf,
            'improvements': {
                'latency_improvement_percent': latency_improvement,
                'success_improvement_percent': success_improvement
            }
        }
    
    # PPO 性能
    ppo_performance = {
        'mean_latency': evaluation_results['mean_latency'],
        'mean_success_rate': evaluation_results['mean_success_rate'],
        'mean_action_entropy': evaluation_results['mean_action_entropy'],
        'name': 'PPO Algorithm'
    }
    
    comparison_result = {
        'ppo_performance': ppo_performance,
        'comparisons': comparisons
    }
    
    logging.info(f"PPO 與基準算法對比:")
    for baseline_name, comp in comparisons.items():
        logging.info(f"  vs {baseline_name}:")
        logging.info(f"    延遲改善: {comp['improvements']['latency_improvement_percent']:.1f}%")
        logging.info(f"    成功率改善: {comp['improvements']['success_improvement_percent']:.1f}%")
    
    return comparison_result

def main():
    """主函數"""
    try:
        # 設置日誌
        logger = setup_logging()
        logger.info("開始 PPO LEO 衛星切換訓練...")
        
        # 創建向量化環境（PPO 的優勢）
        n_envs = 4  # 使用 4 個並行環境
        env = create_environment(n_envs=n_envs)
        
        # PPO 訓練配置
        training_config = {
            'learning_rate': 3e-4,
            'n_steps': 2048,
            'batch_size': 64,
            'n_epochs': 10,
            'gamma': 0.99,
            'gae_lambda': 0.95,
            'clip_range': 0.2,
            'ent_coef': 0.01,
            'vf_coef': 0.5,
            'max_grad_norm': 0.5,
            'verbose': 1
        }
        
        # 訓練模型
        model, training_metrics = train_ppo_model(env, training_config)
        
        # 評估模型
        evaluation_results = evaluate_model(model, env, n_episodes=100)
        
        # 分析策略行為
        policy_analysis = analyze_policy_behavior(model, env, n_episodes=10)
        
        # 與其他算法對比
        comparison = compare_with_dqn_and_baseline(evaluation_results)
        
        # 保存結果
        results_file = save_results(training_metrics, evaluation_results, policy_analysis, training_config)
        
        # 輸出最終結果摘要
        logger.info("=" * 60)
        logger.info("PPO 訓練完成！")
        logger.info(f"平均獎勵: {evaluation_results['mean_reward']:.3f}")
        logger.info(f"切換成功率: {evaluation_results['mean_success_rate']:.1%}")
        logger.info(f"平均延遲: {evaluation_results['mean_latency']:.1f} ms")
        logger.info(f"動作多樣性: {evaluation_results['mean_action_entropy']:.3f}")
        for baseline_name, comp in comparison['comparisons'].items():
            logger.info(f"vs {baseline_name} 延遲改善: {comp['improvements']['latency_improvement_percent']:.1f}%")
        logger.info("=" * 60)
        
        # 關閉環境
        env.close()
        
        return True
        
    except Exception as e:
        logger.error(f"PPO 訓練過程發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)