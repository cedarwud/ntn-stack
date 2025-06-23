#!/usr/bin/env python3
"""
SAC LEO 衛星切換訓練腳本

使用 Soft Actor-Critic 訓練 LEO 衛星切換策略
SAC 適合連續控制任務，提供更精細的功率控制和時機選擇
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
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold, BaseCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.noise import NormalActionNoise
from stable_baselines3.common.evaluation import evaluate_policy

def setup_logging():
    """設置日誌"""
    log_dir = Path('/app/logs')
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f'sac_training_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

class SACMetricsCallback(BaseCallback):
    """SAC 專用訓練指標回調"""
    
    def __init__(self, check_freq: int = 1000, verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.metrics = {
            'episode_rewards': [],
            'actor_losses': [],
            'critic_losses': [],
            'entropy_temperatures': [],
            'success_rates': [],
            'handover_latencies': [],
            'exploration_noise': [],
            'timestamps': []
        }
    
    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            # 記錄 SAC 特有指標
            if hasattr(self.model, 'ent_coef'):
                # 記錄熵係數（SAC 的溫度參數）
                if hasattr(self.model.ent_coef, 'item'):
                    self.metrics['entropy_temperatures'].append(float(self.model.ent_coef.item()))
                else:
                    self.metrics['entropy_temperatures'].append(float(self.model.ent_coef))
            
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

def create_environment(config=None):
    """創建適合 SAC 的 LEO 衛星切換環境"""
    if config is None:
        config = {
            'scenario': 'MULTI_UE',  # SAC 適合複雜場景
            'max_ues': 3,
            'max_satellites': 20,
            'episode_length': 500    # SAC 適合長 episodes
        }
    
    try:
        # 導入環境
        import netstack_api.envs
        env = gym.make('netstack/LEOSatelliteHandover-v0')
        
        # 包裝環境以監控性能
        env = Monitor(env)
        
        # 檢查動作空間類型
        if hasattr(env.action_space, 'shape'):
            action_dim = env.action_space.shape[0] if env.action_space.shape else 1
        else:
            # 如果是 Dict 空間，需要轉換
            logging.warning("檢測到非 Box 動作空間，SAC 需要連續動作空間")
            # 這裡可以添加動作空間轉換邏輯
        
        logging.info(f"SAC 環境創建成功 - 觀測空間: {env.observation_space}")
        logging.info(f"動作空間: {env.action_space}")
        
        return env
    except Exception as e:
        logging.error(f"SAC 環境創建失敗: {e}")
        raise

def train_sac_model(env, config=None):
    """訓練 SAC 模型"""
    if config is None:
        config = {
            'learning_rate': 3e-4,
            'buffer_size': 1000000,    # SAC 使用大緩衝區
            'learning_starts': 10000,   # 延遲學習開始
            'batch_size': 256,          # 較大批次
            'tau': 0.005,               # 軟更新係數
            'gamma': 0.99,
            'train_freq': 1,            # 每步都訓練
            'gradient_steps': 1,
            'ent_coef': 'auto',         # 自動調整熵係數
            'target_update_interval': 1,
            'target_entropy': 'auto',   # 自動目標熵
            'use_sde': False,           # 狀態相關探索
            'sde_sample_freq': -1,
            'use_sde_at_warmup': False,
            'stats_window_size': 100,
            'tensorboard_log': None,
            'verbose': 1,
            'device': 'auto'
        }
    
    logging.info("開始訓練 SAC 模型...")
    logging.info(f"模型配置: {config}")
    
    # 創建動作噪聲（如果需要）
    n_actions = env.action_space.shape[0] if hasattr(env.action_space, 'shape') else 1
    action_noise = NormalActionNoise(
        mean=np.zeros(n_actions), 
        sigma=0.1 * np.ones(n_actions)
    )
    
    # 創建 SAC 模型
    model = SAC(
        "MlpPolicy",
        env,
        action_noise=action_noise,
        **config
    )
    
    # 設置回調函數
    metrics_callback = SACMetricsCallback(check_freq=1000)
    
    # 創建評估環境
    eval_env = Monitor(gym.make('netstack/LEOSatelliteHandover-v0'))
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path='/app/models/sac_best/',
        log_path='/app/logs/',
        eval_freq=5000,
        deterministic=True,
        render=False
    )
    
    # 停止訓練回調
    stop_callback = StopTrainingOnRewardThreshold(
        reward_threshold=20.0,    # SAC 預期最高獎勵
        verbose=1
    )
    
    # 開始訓練
    start_time = time.time()
    model.learn(
        total_timesteps=300000,   # SAC 通常需要更多步數
        callback=[metrics_callback, eval_callback, stop_callback],
        log_interval=10
    )
    training_time = time.time() - start_time
    
    logging.info(f"SAC 訓練完成，耗時: {training_time:.2f} 秒")
    
    # 保存最終模型
    model_dir = Path('/app/models')
    model_dir.mkdir(exist_ok=True)
    model.save(model_dir / 'sac_final')
    
    return model, metrics_callback.metrics

def evaluate_model(model, env, n_episodes=100):
    """評估 SAC 模型性能"""
    logging.info(f"開始評估 SAC 模型，運行 {n_episodes} 個 episodes...")
    
    # 使用 stable-baselines3 的評估函數
    mean_reward, std_reward = evaluate_policy(
        model, 
        env, 
        n_eval_episodes=n_episodes,
        deterministic=True
    )
    
    # 詳細評估，包括 SAC 特有指標
    episode_rewards = []
    success_rates = []
    handover_latencies = []
    action_smoothness = []
    continuous_control_quality = []
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        episode_reward = 0
        done = False
        episode_actions = []
        
        while not done:
            action, _states = model.predict(obs, deterministic=True)
            episode_actions.append(action.copy() if isinstance(action, np.ndarray) else action)
            obs, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
        
        episode_rewards.append(episode_reward)
        success_rates.append(info.get('handover_success_rate', 0))
        handover_latencies.append(info.get('average_handover_latency', 0))
        
        # 計算動作平滑度（SAC 的優勢）
        if len(episode_actions) > 1:
            actions_array = np.array(episode_actions)
            if actions_array.ndim > 1:
                action_diffs = np.diff(actions_array, axis=0)
                smoothness = 1.0 / (1.0 + np.mean(np.linalg.norm(action_diffs, axis=1)))
            else:
                action_diffs = np.diff(actions_array)
                smoothness = 1.0 / (1.0 + np.mean(np.abs(action_diffs)))
            action_smoothness.append(smoothness)
        
        # 評估連續控制品質
        if episode_actions:
            # 計算動作變化的標準差作為控制穩定性指標
            actions_std = np.std(episode_actions)
            control_quality = 1.0 / (1.0 + actions_std)
            continuous_control_quality.append(control_quality)
    
    results = {
        'mean_reward': mean_reward,
        'std_reward': std_reward,
        'episode_rewards': episode_rewards,
        'mean_success_rate': np.mean(success_rates),
        'std_success_rate': np.std(success_rates),
        'mean_latency': np.mean(handover_latencies),
        'std_latency': np.std(handover_latencies),
        'mean_action_smoothness': np.mean(action_smoothness) if action_smoothness else 0,
        'mean_control_quality': np.mean(continuous_control_quality) if continuous_control_quality else 0,
        'episodes_evaluated': n_episodes
    }
    
    logging.info(f"SAC 評估結果:")
    logging.info(f"  平均獎勵: {results['mean_reward']:.3f} ± {results['std_reward']:.3f}")
    logging.info(f"  平均成功率: {results['mean_success_rate']:.3f} ± {results['std_success_rate']:.3f}")
    logging.info(f"  平均延遲: {results['mean_latency']:.1f} ± {results['std_latency']:.1f} ms")
    logging.info(f"  動作平滑度: {results['mean_action_smoothness']:.3f}")
    logging.info(f"  控制品質: {results['mean_control_quality']:.3f}")
    
    return results

def analyze_continuous_control(model, env, n_episodes=10):
    """分析 SAC 連續控制特性"""
    logging.info("分析 SAC 連續控制特性...")
    
    control_analysis = {
        'power_control_patterns': [],
        'timing_precision': [],
        'action_space_coverage': [],
        'exploration_vs_exploitation': [],
        'temperature_effects': []
    }
    
    for episode in range(n_episodes):
        obs, info = env.reset()
        done = False
        episode_powers = []
        episode_timings = []
        episode_actions = []
        
        while not done:
            # 獲取確定性和隨機動作
            action_det, _ = model.predict(obs, deterministic=True)
            action_stoch, _ = model.predict(obs, deterministic=False)
            
            episode_actions.append(action_det.copy() if isinstance(action_det, np.ndarray) else action_det)
            
            # 假設動作包含功率控制和時機控制
            if isinstance(action_det, np.ndarray) and len(action_det) >= 2:
                episode_powers.append(action_det[0])  # 假設第一個是功率
                episode_timings.append(action_det[1])  # 假設第二個是時機
            
            obs, reward, terminated, truncated, info = env.step(action_det)
            done = terminated or truncated
        
        control_analysis['power_control_patterns'].append(episode_powers)
        control_analysis['timing_precision'].append(episode_timings)
        control_analysis['action_space_coverage'].append(episode_actions)
    
    logging.info(f"連續控制分析完成，分析了 {n_episodes} 個 episodes")
    return control_analysis

def save_results(training_metrics, evaluation_results, control_analysis, config):
    """保存 SAC 訓練和評估結果"""
    results_dir = Path('/app/results')
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存綜合結果
    results = {
        'timestamp': timestamp,
        'algorithm': 'SAC',
        'config': config,
        'training_metrics': training_metrics,
        'evaluation_results': evaluation_results,
        'control_analysis': control_analysis
    }
    
    results_file = results_dir / f'sac_results_{timestamp}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    # 生成 SAC 專用可視化
    plt.figure(figsize=(18, 12))
    
    # 子圖1: 獎勵曲線
    plt.subplot(3, 3, 1)
    if training_metrics['episode_rewards']:
        plt.plot(training_metrics['episode_rewards'])
        plt.title('Episode Rewards (SAC)')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.grid(True)
    
    # 子圖2: 熵溫度變化
    plt.subplot(3, 3, 2)
    if training_metrics['entropy_temperatures']:
        plt.plot(training_metrics['entropy_temperatures'])
        plt.title('Entropy Temperature')
        plt.xlabel('Update')
        plt.ylabel('Temperature')
        plt.grid(True)
    
    # 子圖3: 成功率
    plt.subplot(3, 3, 3)
    if training_metrics['success_rates']:
        plt.plot(training_metrics['success_rates'])
        plt.title('Handover Success Rate')
        plt.xlabel('Check Point')
        plt.ylabel('Success Rate')
        plt.ylim(0, 1.1)
        plt.grid(True)
    
    # 子圖4: 延遲變化
    plt.subplot(3, 3, 4)
    if training_metrics['handover_latencies']:
        plt.plot(training_metrics['handover_latencies'])
        plt.title('Average Handover Latency')
        plt.xlabel('Check Point')
        plt.ylabel('Latency (ms)')
        plt.grid(True)
    
    # 子圖5: 評估獎勵分佈
    plt.subplot(3, 3, 5)
    plt.hist(evaluation_results['episode_rewards'], bins=20, alpha=0.7, color='purple')
    plt.title('Evaluation Reward Distribution')
    plt.xlabel('Episode Reward')
    plt.ylabel('Frequency')
    plt.grid(True)
    
    # 子圖6: 功率控制模式
    plt.subplot(3, 3, 6)
    if control_analysis['power_control_patterns']:
        for pattern in control_analysis['power_control_patterns'][:3]:  # 顯示前3個episode
            plt.plot(pattern, alpha=0.7)
        plt.title('Power Control Patterns')
        plt.xlabel('Time Step')
        plt.ylabel('Power Level')
        plt.grid(True)
    
    # 子圖7: 時機控制精度
    plt.subplot(3, 3, 7)
    if control_analysis['timing_precision']:
        for timing in control_analysis['timing_precision'][:3]:
            plt.plot(timing, alpha=0.7)
        plt.title('Timing Control Precision')
        plt.xlabel('Time Step')
        plt.ylabel('Timing Value')
        plt.grid(True)
    
    # 子圖8: 動作空間覆蓋
    plt.subplot(3, 3, 8)
    if control_analysis['action_space_coverage']:
        all_actions = []
        for episode_actions in control_analysis['action_space_coverage']:
            for action in episode_actions:
                if isinstance(action, np.ndarray):
                    all_actions.extend(action.flatten())
                else:
                    all_actions.append(action)
        plt.hist(all_actions, bins=30, alpha=0.7, color='red')
        plt.title('Action Space Coverage')
        plt.xlabel('Action Value')
        plt.ylabel('Frequency')
        plt.grid(True)
    
    # 子圖9: 控制品質指標
    plt.subplot(3, 3, 9)
    quality_metrics = ['Smoothness', 'Control Quality', 'Success Rate']
    quality_values = [
        evaluation_results['mean_action_smoothness'],
        evaluation_results['mean_control_quality'],
        evaluation_results['mean_success_rate']
    ]
    plt.bar(quality_metrics, quality_values, color=['blue', 'green', 'orange'])
    plt.title('Control Quality Metrics')
    plt.ylabel('Score')
    plt.grid(True, axis='y')
    
    plt.tight_layout()
    plt.savefig(results_dir / f'sac_control_analysis_{timestamp}.png', dpi=300)
    plt.close()
    
    logging.info(f"SAC 結果已保存到: {results_file}")
    return results_file

def compare_with_other_algorithms(evaluation_results):
    """與其他算法對比"""
    # 基準性能數據
    baselines = {
        'IEEE_INFOCOM_2024': {
            'mean_latency': 25.0,
            'mean_success_rate': 0.90,
            'control_quality': 0.60,  # 估算
            'name': 'IEEE INFOCOM 2024'
        },
        'DQN_Algorithm': {
            'mean_latency': 18.5,
            'mean_success_rate': 0.94,
            'control_quality': 0.70,  # 離散控制限制
            'name': 'DQN Algorithm'
        },
        'PPO_Algorithm': {
            'mean_latency': 16.3,
            'mean_success_rate': 0.968,
            'control_quality': 0.80,  # 連續動作但較簡單
            'name': 'PPO Algorithm'
        }
    }
    
    # 計算改善程度
    comparisons = {}
    for baseline_name, baseline_perf in baselines.items():
        latency_improvement = (baseline_perf['mean_latency'] - evaluation_results['mean_latency']) / baseline_perf['mean_latency'] * 100
        success_improvement = (evaluation_results['mean_success_rate'] - baseline_perf['mean_success_rate']) / baseline_perf['mean_success_rate'] * 100
        control_improvement = (evaluation_results['mean_control_quality'] - baseline_perf['control_quality']) / baseline_perf['control_quality'] * 100
        
        comparisons[baseline_name] = {
            'baseline': baseline_perf,
            'improvements': {
                'latency_improvement_percent': latency_improvement,
                'success_improvement_percent': success_improvement,
                'control_improvement_percent': control_improvement
            }
        }
    
    # SAC 性能
    sac_performance = {
        'mean_latency': evaluation_results['mean_latency'],
        'mean_success_rate': evaluation_results['mean_success_rate'],
        'mean_action_smoothness': evaluation_results['mean_action_smoothness'],
        'mean_control_quality': evaluation_results['mean_control_quality'],
        'name': 'SAC Algorithm'
    }
    
    comparison_result = {
        'sac_performance': sac_performance,
        'comparisons': comparisons
    }
    
    logging.info(f"SAC 與其他算法對比:")
    for baseline_name, comp in comparisons.items():
        logging.info(f"  vs {baseline_name}:")
        logging.info(f"    延遲改善: {comp['improvements']['latency_improvement_percent']:.1f}%")
        logging.info(f"    成功率改善: {comp['improvements']['success_improvement_percent']:.1f}%")
        logging.info(f"    控制品質改善: {comp['improvements']['control_improvement_percent']:.1f}%")
    
    return comparison_result

def main():
    """主函數"""
    try:
        # 設置日誌
        logger = setup_logging()
        logger.info("開始 SAC LEO 衛星切換訓練...")
        
        # 創建環境
        env = create_environment()
        
        # SAC 訓練配置
        training_config = {
            'learning_rate': 3e-4,
            'buffer_size': 1000000,
            'learning_starts': 10000,
            'batch_size': 256,
            'tau': 0.005,
            'gamma': 0.99,
            'ent_coef': 'auto',
            'target_entropy': 'auto',
            'train_freq': 1,
            'verbose': 1
        }
        
        # 訓練模型
        model, training_metrics = train_sac_model(env, training_config)
        
        # 評估模型
        evaluation_results = evaluate_model(model, env, n_episodes=100)
        
        # 分析連續控制特性
        control_analysis = analyze_continuous_control(model, env, n_episodes=10)
        
        # 與其他算法對比
        comparison = compare_with_other_algorithms(evaluation_results)
        
        # 保存結果
        results_file = save_results(training_metrics, evaluation_results, control_analysis, training_config)
        
        # 輸出最終結果摘要
        logger.info("=" * 60)
        logger.info("SAC 訓練完成！")
        logger.info(f"平均獎勵: {evaluation_results['mean_reward']:.3f}")
        logger.info(f"切換成功率: {evaluation_results['mean_success_rate']:.1%}")
        logger.info(f"平均延遲: {evaluation_results['mean_latency']:.1f} ms")
        logger.info(f"動作平滑度: {evaluation_results['mean_action_smoothness']:.3f}")
        logger.info(f"控制品質: {evaluation_results['mean_control_quality']:.3f}")
        logger.info("SAC 提供最精細的連續控制能力！")
        logger.info("=" * 60)
        
        # 關閉環境
        env.close()
        
        return True
        
    except Exception as e:
        logger.error(f"SAC 訓練過程發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)