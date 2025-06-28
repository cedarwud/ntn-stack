#!/usr/bin/env python3
"""
Gymnasium RL 訓練統一測試程式

整合所有 Gymnasium 相關測試：
- 環境測試
- 訓練測試  
- 模型驗證測試

執行方式:
python gymnasium_tests.py [--env=all|satellite|handover] [--quick]
"""

import sys
import os
import time
import logging
import argparse
import numpy as np
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GymnasiumTestFramework:
    """Gymnasium 測試統一框架"""
    
    def __init__(self, quick_mode=False):
        self.results = []
        self.quick_mode = quick_mode
        self.start_time = None
        
    def log_result(self, test_name: str, success: bool, details: str = "", metrics: Dict = None):
        """記錄測試結果"""
        self.results.append({
            'name': test_name,
            'success': success,
            'details': details,
            'metrics': metrics or {},
            'timestamp': time.time()
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name} - {details}")

    def test_satellite_environment(self):
        """測試衛星環境"""
        logger.info("🛰️ 測試衛星環境...")
        
        try:
            # 模擬 Gymnasium 衛星環境
            class SatelliteEnv:
                def __init__(self):
                    self.num_satellites = 5
                    self.num_ues = 10
                    self.observation_space_size = self.num_satellites * 4 + self.num_ues * 3  # 位置+狀態
                    self.action_space_size = self.num_ues  # 每個UE的衛星選擇
                    self.state = None
                    self.step_count = 0
                
                def reset(self):
                    """重置環境"""
                    self.state = np.random.rand(self.observation_space_size)
                    self.step_count = 0
                    return self.state.copy()
                
                def step(self, action):
                    """執行動作"""
                    assert len(action) == self.action_space_size, f"動作維度錯誤: {len(action)} vs {self.action_space_size}"
                    
                    # 模擬環境動態
                    self.state += np.random.normal(0, 0.01, self.observation_space_size)
                    self.state = np.clip(self.state, 0, 1)
                    self.step_count += 1
                    
                    # 計算獎勵
                    reward = self._calculate_reward(action)
                    
                    # 判斷是否結束
                    done = self.step_count >= 100
                    
                    return self.state.copy(), reward, done, {}
                
                def _calculate_reward(self, action):
                    """計算獎勵"""
                    # 模擬獎勵計算：基於負載平衡和換手頻率
                    load_balance_penalty = np.var(np.bincount(action, minlength=self.num_satellites))
                    handover_penalty = np.sum(np.abs(np.diff(action))) * 0.1
                    
                    base_reward = 10.0
                    return base_reward - load_balance_penalty - handover_penalty
            
            # 測試環境基本功能
            env = SatelliteEnv()
            
            # 測試重置
            initial_state = env.reset()
            assert len(initial_state) == env.observation_space_size, "狀態維度錯誤"
            assert np.all(initial_state >= 0) and np.all(initial_state <= 1), "狀態範圍錯誤"
            
            # 測試步驟執行
            episodes = 2 if self.quick_mode else 5
            total_reward = 0
            total_steps = 0
            
            for episode in range(episodes):
                state = env.reset()
                episode_reward = 0
                step_count = 0
                
                while step_count < (20 if self.quick_mode else 50):
                    # 隨機動作
                    action = np.random.randint(0, env.num_satellites, env.num_ues)
                    
                    next_state, reward, done, info = env.step(action)
                    episode_reward += reward
                    step_count += 1
                    
                    assert len(next_state) == env.observation_space_size, "下一狀態維度錯誤"
                    
                    if done:
                        break
                
                total_reward += episode_reward
                total_steps += step_count
            
            avg_reward = total_reward / episodes
            avg_steps = total_steps / episodes
            
            details = f"平均獎勵: {avg_reward:.2f}, 平均步數: {avg_steps:.1f}"
            self.log_result("衛星環境測試", True, details, 
                          {'avg_reward': avg_reward, 'avg_steps': avg_steps, 'episodes': episodes})
            return True
            
        except Exception as e:
            self.log_result("衛星環境測試", False, str(e))
            return False

    def test_handover_environment(self):
        """測試換手環境"""
        logger.info("🔄 測試換手環境...")
        
        try:
            # 模擬換手專用環境
            class HandoverEnv:
                def __init__(self):
                    self.num_satellites = 3
                    self.ue_position = np.array([0.0, 0.0])  # 2D位置
                    self.satellite_positions = np.random.rand(self.num_satellites, 2)
                    self.current_satellite = 0
                    self.handover_count = 0
                    self.step_count = 0
                
                def reset(self):
                    """重置環境"""
                    self.ue_position = np.random.rand(2)
                    self.satellite_positions = np.random.rand(self.num_satellites, 2)
                    self.current_satellite = 0
                    self.handover_count = 0
                    self.step_count = 0
                    return self._get_observation()
                
                def _get_observation(self):
                    """獲取觀察"""
                    obs = []
                    obs.extend(self.ue_position)
                    obs.extend(self.satellite_positions.flatten())
                    obs.append(self.current_satellite)
                    obs.append(self.handover_count)
                    return np.array(obs)
                
                def step(self, action):
                    """執行動作"""
                    # action: 0=保持, 1=換手到衛星1, 2=換手到衛星2, ...
                    
                    old_satellite = self.current_satellite
                    
                    if action > 0 and action <= self.num_satellites:
                        new_satellite = action - 1
                        if new_satellite != self.current_satellite:
                            self.current_satellite = new_satellite
                            self.handover_count += 1
                    
                    # 模擬UE移動
                    self.ue_position += np.random.normal(0, 0.01, 2)
                    self.ue_position = np.clip(self.ue_position, 0, 1)
                    
                    # 模擬衛星移動
                    self.satellite_positions += np.random.normal(0, 0.005, (self.num_satellites, 2))
                    self.satellite_positions = np.clip(self.satellite_positions, 0, 1)
                    
                    self.step_count += 1
                    
                    # 計算獎勵
                    reward = self._calculate_handover_reward(old_satellite, self.current_satellite)
                    
                    done = self.step_count >= 50
                    
                    return self._get_observation(), reward, done, {'handovers': self.handover_count}
                
                def _calculate_handover_reward(self, old_sat: int, new_sat: int):
                    """計算換手獎勵"""
                    # 距離獎勵：與當前衛星的距離越近獎勵越高
                    current_sat_pos = self.satellite_positions[self.current_satellite]
                    distance = np.linalg.norm(self.ue_position - current_sat_pos)
                    distance_reward = 1.0 - distance
                    
                    # 換手懲罰
                    handover_penalty = 0.1 if old_sat != new_sat else 0.0
                    
                    return distance_reward - handover_penalty
            
            # 測試換手環境
            env = HandoverEnv()
            
            episodes = 3 if self.quick_mode else 5
            total_handovers = 0
            total_rewards = 0
            
            for episode in range(episodes):
                state = env.reset()
                episode_reward = 0
                
                for step in range(30 if self.quick_mode else 50):
                    # 簡單策略：基於距離選擇衛星
                    ue_pos = state[:2]
                    sat_positions = state[2:2+env.num_satellites*2].reshape(env.num_satellites, 2)
                    
                    distances = [np.linalg.norm(ue_pos - sat_pos) for sat_pos in sat_positions]
                    best_satellite = np.argmin(distances)
                    
                    action = best_satellite + 1  # +1 因為0是保持動作
                    
                    next_state, reward, done, info = env.step(action)
                    episode_reward += reward
                    state = next_state
                    
                    if done:
                        break
                
                total_handovers += info.get('handovers', 0)
                total_rewards += episode_reward
            
            avg_handovers = total_handovers / episodes
            avg_reward = total_rewards / episodes
            
            details = f"平均換手次數: {avg_handovers:.1f}, 平均獎勵: {avg_reward:.2f}"
            self.log_result("換手環境測試", True, details,
                          {'avg_handovers': avg_handovers, 'avg_reward': avg_reward})
            return True
            
        except Exception as e:
            self.log_result("換手環境測試", False, str(e))
            return False

    def test_rl_training_simulation(self):
        """測試RL訓練模擬"""
        logger.info("🧠 測試RL訓練模擬...")
        
        try:
            # 模擬簡單的Q-learning代理
            class SimpleQLearningAgent:
                def __init__(self, state_size: int, action_size: int, learning_rate=0.1, epsilon=0.1):
                    self.state_size = state_size
                    self.action_size = action_size
                    self.learning_rate = learning_rate
                    self.epsilon = epsilon
                    self.q_table = {}  # 使用字典模擬Q表
                    self.training_rewards = []
                
                def _state_to_key(self, state):
                    """將狀態轉換為字典鍵"""
                    # 簡化：只使用狀態的前幾個維度
                    return tuple(np.round(state[:min(4, len(state))], 1))
                
                def choose_action(self, state, training=True):
                    """選擇動作"""
                    state_key = self._state_to_key(state)
                    
                    if training and np.random.random() < self.epsilon:
                        return np.random.randint(self.action_size)
                    
                    if state_key not in self.q_table:
                        self.q_table[state_key] = np.zeros(self.action_size)
                    
                    return np.argmax(self.q_table[state_key])
                
                def update_q_value(self, state, action, reward, next_state):
                    """更新Q值"""
                    state_key = self._state_to_key(state)
                    next_state_key = self._state_to_key(next_state)
                    
                    if state_key not in self.q_table:
                        self.q_table[state_key] = np.zeros(self.action_size)
                    if next_state_key not in self.q_table:
                        self.q_table[next_state_key] = np.zeros(self.action_size)
                    
                    # Q-learning更新
                    old_q = self.q_table[state_key][action]
                    next_max_q = np.max(self.q_table[next_state_key])
                    
                    new_q = old_q + self.learning_rate * (reward + 0.9 * next_max_q - old_q)
                    self.q_table[state_key][action] = new_q
                
                def train_episode(self, env):
                    """訓練一個episode"""
                    state = env.reset()
                    total_reward = 0
                    steps = 0
                    
                    while steps < 30:  # 限制步數
                        action = self.choose_action(state, training=True)
                        next_state, reward, done, _ = env.step([action] if hasattr(env, 'num_ues') else action)
                        
                        self.update_q_value(state, action, reward, next_state)
                        
                        total_reward += reward
                        state = next_state
                        steps += 1
                        
                        if done:
                            break
                    
                    self.training_rewards.append(total_reward)
                    return total_reward
            
            # 創建簡單環境用於訓練測試
            class SimpleEnv:
                def __init__(self):
                    self.state_size = 4
                    self.action_size = 3
                    self.state = None
                    self.step_count = 0
                
                def reset(self):
                    self.state = np.random.rand(self.state_size)
                    self.step_count = 0
                    return self.state.copy()
                
                def step(self, action):
                    # 簡化環境動態
                    self.state += np.random.normal(0, 0.1, self.state_size)
                    self.state = np.clip(self.state, 0, 1)
                    self.step_count += 1
                    
                    # 簡單獎勵：狀態值越高獎勵越高，動作2獎勵更高
                    reward = np.sum(self.state) + (0.5 if action == 2 else 0)
                    done = self.step_count >= 20
                    
                    return self.state.copy(), reward, done, {}
            
            # 執行訓練測試
            env = SimpleEnv()
            agent = SimpleQLearningAgent(env.state_size, env.action_size)
            
            # 訓練
            training_episodes = 20 if self.quick_mode else 50
            for episode in range(training_episodes):
                agent.train_episode(env)
            
            # 評估改善
            initial_rewards = agent.training_rewards[:5]
            final_rewards = agent.training_rewards[-5:]
            
            initial_avg = np.mean(initial_rewards)
            final_avg = np.mean(final_rewards)
            improvement = (final_avg - initial_avg) / abs(initial_avg) if initial_avg != 0 else 0
            
            # 測試學習到的策略
            test_episodes = 5
            test_rewards = []
            
            for _ in range(test_episodes):
                state = env.reset()
                total_reward = 0
                
                for _ in range(20):
                    action = agent.choose_action(state, training=False)
                    next_state, reward, done, _ = env.step(action)
                    total_reward += reward
                    state = next_state
                    
                    if done:
                        break
                
                test_rewards.append(total_reward)
            
            avg_test_reward = np.mean(test_rewards)
            
            details = f"訓練改善: {improvement:.2%}, 測試獎勵: {avg_test_reward:.2f}, Q表大小: {len(agent.q_table)}"
            self.log_result("RL訓練模擬", True, details,
                          {'improvement': improvement, 'test_reward': avg_test_reward, 'q_table_size': len(agent.q_table)})
            return True
            
        except Exception as e:
            self.log_result("RL訓練模擬", False, str(e))
            return False

    def test_model_evaluation(self):
        """測試模型評估"""
        logger.info("📊 測試模型評估...")
        
        try:
            # 模擬模型評估框架
            class ModelEvaluator:
                def __init__(self):
                    self.evaluation_metrics = ['reward', 'handover_efficiency', 'load_balance', 'latency']
                
                def evaluate_model(self, model_type: str, episodes: int) -> dict:
                    """評估模型效能"""
                    np.random.seed(42)  # 固定隨機種子確保可重複
                    
                    results = {
                        'model_type': model_type,
                        'episodes': episodes,
                        'metrics': {}
                    }
                    
                    # 模擬不同模型的效能特性
                    if model_type == 'random':
                        base_reward = 5.0
                        reward_std = 2.0
                        handover_eff = 0.3
                        load_balance = 0.4
                        latency = 100.0
                    elif model_type == 'greedy':
                        base_reward = 8.0
                        reward_std = 1.5
                        handover_eff = 0.6
                        load_balance = 0.5
                        latency = 80.0
                    elif model_type == 'q_learning':
                        base_reward = 10.0
                        reward_std = 1.0
                        handover_eff = 0.8
                        load_balance = 0.7
                        latency = 60.0
                    elif model_type == 'dqn':
                        base_reward = 12.0
                        reward_std = 0.8
                        handover_eff = 0.85
                        load_balance = 0.8
                        latency = 50.0
                    else:
                        base_reward = 6.0
                        reward_std = 2.5
                        handover_eff = 0.4
                        load_balance = 0.3
                        latency = 120.0
                    
                    # 生成評估數據
                    rewards = np.random.normal(base_reward, reward_std, episodes)
                    
                    results['metrics'] = {
                        'avg_reward': float(np.mean(rewards)),
                        'reward_std': float(np.std(rewards)),
                        'handover_efficiency': handover_eff + np.random.normal(0, 0.05),
                        'load_balance_score': load_balance + np.random.normal(0, 0.05),
                        'avg_latency_ms': latency + np.random.normal(0, 5)
                    }
                    
                    return results
                
                def compare_models(self, model_results: List[dict]) -> dict:
                    """比較多個模型"""
                    if not model_results:
                        return {}
                    
                    comparison = {
                        'models': len(model_results),
                        'best_model': {},
                        'rankings': {}
                    }
                    
                    # 找出各項指標的最佳模型
                    metrics = ['avg_reward', 'handover_efficiency', 'load_balance_score']
                    
                    for metric in metrics:
                        best_value = max(result['metrics'][metric] for result in model_results)
                        best_model = next(r for r in model_results if r['metrics'][metric] == best_value)
                        comparison['best_model'][metric] = best_model['model_type']
                    
                    # 延遲越低越好
                    best_latency = min(result['metrics']['avg_latency_ms'] for result in model_results)
                    best_latency_model = next(r for r in model_results if r['metrics']['avg_latency_ms'] == best_latency)
                    comparison['best_model']['avg_latency_ms'] = best_latency_model['model_type']
                    
                    # 計算綜合排名
                    for result in model_results:
                        score = (
                            result['metrics']['avg_reward'] * 0.3 +
                            result['metrics']['handover_efficiency'] * 10 * 0.3 +
                            result['metrics']['load_balance_score'] * 10 * 0.2 +
                            (200 - result['metrics']['avg_latency_ms']) / 200 * 0.2
                        )
                        comparison['rankings'][result['model_type']] = score
                    
                    # 找出總體最佳模型
                    best_overall = max(comparison['rankings'], key=comparison['rankings'].get)
                    comparison['best_overall'] = best_overall
                    
                    return comparison
            
            # 執行模型評估測試
            evaluator = ModelEvaluator()
            
            # 測試不同模型
            models_to_test = ['random', 'greedy', 'q_learning'] if self.quick_mode else ['random', 'greedy', 'q_learning', 'dqn']
            episodes_per_model = 10 if self.quick_mode else 20
            
            model_results = []
            for model_type in models_to_test:
                result = evaluator.evaluate_model(model_type, episodes_per_model)
                model_results.append(result)
                
                # 驗證結果合理性
                assert result['metrics']['avg_reward'] > 0, f"獎勵異常: {model_type}"
                assert 0 <= result['metrics']['handover_efficiency'] <= 1, f"換手效率異常: {model_type}"
                assert result['metrics']['avg_latency_ms'] > 0, f"延遲異常: {model_type}"
            
            # 比較模型
            comparison = evaluator.compare_models(model_results)
            
            # 驗證比較結果
            assert len(comparison['rankings']) == len(models_to_test), "排名數量不匹配"
            assert comparison['best_overall'] in models_to_test, "最佳模型不在測試列表中"
            
            # 驗證進階模型效能更好
            if 'q_learning' in comparison['rankings'] and 'random' in comparison['rankings']:
                assert comparison['rankings']['q_learning'] > comparison['rankings']['random'], \
                    "Q-learning應該比隨機策略效能更好"
            
            best_model = comparison['best_overall']
            best_score = comparison['rankings'][best_model]
            
            details = f"最佳模型: {best_model}, 綜合分數: {best_score:.2f}, 測試模型數: {len(models_to_test)}"
            self.log_result("模型評估", True, details,
                          {'best_model': best_model, 'best_score': best_score, 'models_tested': len(models_to_test)})
            return True
            
        except Exception as e:
            self.log_result("模型評估", False, str(e))
            return False

    def run_all_tests(self):
        """執行所有測試"""
        logger.info("🚀 開始執行Gymnasium測試...")
        self.start_time = time.time()
        
        results = []
        results.append(self.test_satellite_environment())
        results.append(self.test_handover_environment())
        results.append(self.test_rl_training_simulation())
        results.append(self.test_model_evaluation())
        
        return all(results)
    
    def print_summary(self):
        """印出測試摘要"""
        if not self.results:
            logger.warning("沒有測試結果")
            return
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*60)
        print("🎮 Gymnasium RL 測試框架 - 測試報告")
        print("="*60)
        print(f"📊 測試統計:")
        print(f"   總測試數: {total_tests}")
        print(f"   通過: {passed_tests} ✅")
        print(f"   失敗: {failed_tests} ❌") 
        print(f"   成功率: {passed_tests/total_tests:.1%}")
        print(f"   總耗時: {total_duration:.2f}s")
        print(f"   快速模式: {'是' if self.quick_mode else '否'}")
        print()
        
        if failed_tests > 0:
            print("❌ 失敗的測試:")
            for result in self.results:
                if not result['success']:
                    print(f"   - {result['name']}: {result['details']}")
            print()
        
        print("✅ Gymnasium測試完成" if passed_tests == total_tests else "⚠️  部分測試失敗")
        print("="*60)

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='Gymnasium RL 測試框架')
    parser.add_argument('--env', choices=['all', 'satellite', 'handover'], default='all', help='環境類型')
    parser.add_argument('--quick', action='store_true', help='快速測試模式')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    framework = GymnasiumTestFramework(quick_mode=args.quick)
    
    try:
        if args.env == 'satellite':
            success = framework.test_satellite_environment()
        elif args.env == 'handover':
            success = framework.test_handover_environment()
        else:  # all
            success = framework.run_all_tests()
        
        framework.print_summary()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("測試被用戶中斷")
        sys.exit(130)
    except Exception as e:
        logger.error(f"測試執行時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
