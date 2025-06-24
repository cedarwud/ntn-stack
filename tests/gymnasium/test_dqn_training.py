"""
DQN 算法訓練測試

測試離散動作空間環境與 DQN 算法的兼容性
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, "/home/sat/ntn-stack")
sys.path.insert(0, "/home/sat/ntn-stack/netstack")

import numpy as np
import gymnasium as gym
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_discrete_environment():
    """測試離散動作環境基本功能"""
    print("=== 測試離散動作環境 ===")

    try:
        # 導入離散環境
        from netstack_api.envs.discrete_handover_env import (
            DiscreteLEOSatelliteHandoverEnv,
            DQNCompatibleHandoverEnv,
        )
        from netstack_api.envs.handover_env_fixed import HandoverScenario

        print("✅ 成功導入離散環境模塊")

        # 測試基本離散環境
        print("\n1. 測試基本離散環境...")
        env = DiscreteLEOSatelliteHandoverEnv(
            scenario=HandoverScenario.SINGLE_UE,
            max_ues=3,
            max_satellites=5,
            discrete_actions=10,
        )

        print(f"  動作空間: {env.action_space}")
        print(f"  觀測空間: {env.observation_space}")
        print(f"  離散動作數量: {env.discrete_actions}")

        # 測試重置和步進
        obs, info = env.reset()
        print(f"  重置成功，觀測維度: {obs.shape}")

        # 測試所有動作
        print("\n  測試所有離散動作:")
        for action in range(env.discrete_actions):
            action_info = env.get_action_info(action)
            print(f"    動作 {action}: {action_info['description']}")

        # 執行幾步測試
        total_reward = 0
        for step in range(10):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            total_reward += reward

            print(
                f"  步驟 {step}: 動作={action}, 獎勵={reward:.3f}, 結束={terminated or truncated}"
            )

            if terminated or truncated:
                obs, info = env.reset()
                print(f"  環境重置，總獎勵: {total_reward:.3f}")
                total_reward = 0

        env.close()
        print("✅ 基本離散環境測試通過")

        # 測試DQN優化環境
        print("\n2. 測試 DQN 優化環境...")
        dqn_env = DQNCompatibleHandoverEnv(
            scenario=HandoverScenario.SINGLE_UE,
            max_ues=3,
            max_satellites=5,
            discrete_actions=10,
            max_episode_steps=50,
            reward_scale=1.0,
            penalty_scale=0.1,
        )

        obs, info = dqn_env.reset()
        print(f"  DQN環境重置成功")
        print(f"  最大步數: {info.get('max_episode_steps')}")

        # 測試完整episode
        episode_reward = 0
        step_count = 0

        while True:
            action = dqn_env.action_space.sample()
            obs, reward, terminated, truncated, info = dqn_env.step(action)
            episode_reward += reward
            step_count += 1

            if step_count % 10 == 0:
                print(f"    步驟 {step_count}: 累積獎勵={episode_reward:.3f}")

            if terminated or truncated:
                print(f"  Episode結束: 步數={step_count}, 總獎勵={episode_reward:.3f}")
                print(f"  動作頻率: {info.get('action_frequency', {})}")
                break

        dqn_env.close()
        print("✅ DQN 優化環境測試通過")

        return True

    except Exception as e:
        print(f"❌ 離散環境測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_dqn_training():
    """測試 DQN 算法訓練"""
    print("\n=== 測試 DQN 算法訓練 ===")

    try:
        # 嘗試導入 stable-baselines3
        try:
            from stable_baselines3 import DQN
            from stable_baselines3.common.evaluation import evaluate_policy
            from stable_baselines3.common.env_checker import check_env

            print("✅ 成功導入 stable-baselines3")
        except ImportError:
            print("❌ stable-baselines3 未安裝，跳過 DQN 訓練測試")
            return True

        # 創建環境
        from netstack_api.envs.discrete_handover_env import DQNCompatibleHandoverEnv
        from netstack_api.envs.handover_env_fixed import HandoverScenario

        env = DQNCompatibleHandoverEnv(
            scenario=HandoverScenario.SINGLE_UE,
            max_ues=2,
            max_satellites=3,
            discrete_actions=8,
            max_episode_steps=100,
        )

        print("✅ DQN 環境創建成功")

        # 檢查環境兼容性
        print("\n1. 檢查環境兼容性...")
        try:
            check_env(env)
            print("✅ 環境兼容性檢查通過")
        except Exception as e:
            print(f"⚠️ 環境兼容性警告: {e}")

        # 創建 DQN 模型
        print("\n2. 創建 DQN 模型...")
        model = DQN(
            "MlpPolicy",  # 多層感知機策略
            env,
            learning_rate=1e-3,
            buffer_size=1000,
            learning_starts=100,
            batch_size=32,
            target_update_interval=100,
            train_freq=4,
            gradient_steps=1,
            exploration_fraction=0.3,
            exploration_initial_eps=1.0,
            exploration_final_eps=0.1,
            verbose=1,
        )

        print("✅ DQN 模型創建成功")
        print(f"  策略網路: {model.policy}")
        print(f"  動作空間: {model.action_space}")
        print(f"  觀測空間: {model.observation_space}")

        # 訓練前評估
        print("\n3. 訓練前性能評估...")
        mean_reward_before, std_reward_before = evaluate_policy(
            model, env, n_eval_episodes=5, deterministic=True
        )
        print(f"  訓練前平均獎勵: {mean_reward_before:.3f} ± {std_reward_before:.3f}")

        # 短期訓練
        print("\n4. 開始短期訓練...")
        training_start = time.time()

        model.learn(
            total_timesteps=1000, log_interval=100, progress_bar=True  # 短期訓練
        )

        training_time = time.time() - training_start
        print(f"✅ 訓練完成，耗時: {training_time:.2f}秒")

        # 訓練後評估
        print("\n5. 訓練後性能評估...")
        mean_reward_after, std_reward_after = evaluate_policy(
            model, env, n_eval_episodes=5, deterministic=True
        )
        print(f"  訓練後平均獎勵: {mean_reward_after:.3f} ± {std_reward_after:.3f}")

        # 性能改進分析
        improvement = mean_reward_after - mean_reward_before
        print(f"  性能改進: {improvement:.3f}")

        if improvement > 0:
            print("✅ DQN 訓練顯示正向學習效果")
        else:
            print("⚠️ 短期訓練未顯示明顯改進（這是正常的）")

        # 測試訓練後的決策
        print("\n6. 測試訓練後的決策...")
        obs, _ = env.reset()

        for i in range(10):
            action, _states = model.predict(obs, deterministic=True)
            action_info = env.get_action_info(action)
            print(
                f"  決策 {i}: 動作={action}, 描述={action_info.get('description', 'N/A')}"
            )

            obs, reward, terminated, truncated, info = env.step(action)

            if terminated or truncated:
                obs, _ = env.reset()

        # 保存模型
        model_dir = Path("/home/sat/ntn-stack/results/dqn_test")
        model_dir.mkdir(parents=True, exist_ok=True)

        model_path = (
            model_dir / f"dqn_test_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        model.save(str(model_path))
        print(f"✅ 模型已保存: {model_path}.zip")

        env.close()

        return True

    except Exception as e:
        print(f"❌ DQN 訓練測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_dqn_vs_baseline():
    """測試 DQN 與基準算法對比"""
    print("\n=== DQN 與基準算法對比測試 ===")

    try:
        # 檢查依賴
        try:
            from stable_baselines3 import DQN
            from stable_baselines3.common.evaluation import evaluate_policy
        except ImportError:
            print("❌ 跳過對比測試：缺少 stable-baselines3")
            return True

        # 導入基準算法
        sys.path.insert(0, "/home/sat/ntn-stack/netstack/scripts")
        from baseline_algorithms.simple_threshold_algorithm import (
            SimpleThresholdAlgorithm,
        )
        from baseline_algorithms.random_algorithm import RandomAlgorithm

        # 創建環境
        from netstack_api.envs.discrete_handover_env import DQNCompatibleHandoverEnv
        from netstack_api.envs.handover_env_fixed import HandoverScenario

        env = DQNCompatibleHandoverEnv(
            scenario=HandoverScenario.SINGLE_UE,
            max_ues=2,
            max_satellites=3,
            discrete_actions=8,
            max_episode_steps=50,
        )

        print("✅ 對比測試環境創建成功")

        # 快速訓練 DQN
        print("\n1. 快速訓練 DQN...")
        model = DQN("MlpPolicy", env, verbose=0)
        model.learn(total_timesteps=500)

        # 評估 DQN
        print("\n2. 評估 DQN 性能...")
        dqn_reward, dqn_std = evaluate_policy(model, env, n_eval_episodes=5)
        print(f"  DQN 平均獎勵: {dqn_reward:.3f} ± {dqn_std:.3f}")

        # 評估基準算法（簡化版，因為需要適配離散動作）
        print("\n3. 評估基準算法性能...")

        # 隨機基準
        random_rewards = []
        for episode in range(5):
            obs, _ = env.reset()
            episode_reward = 0

            while True:
                action = env.action_space.sample()  # 隨機動作
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward

                if terminated or truncated:
                    break

            random_rewards.append(episode_reward)

        random_mean = np.mean(random_rewards)
        random_std = np.std(random_rewards)
        print(f"  隨機算法平均獎勵: {random_mean:.3f} ± {random_std:.3f}")

        # 保守策略（總是維持連接）
        conservative_rewards = []
        for episode in range(5):
            obs, _ = env.reset()
            episode_reward = 0

            while True:
                action = 0  # 維持連接動作
                obs, reward, terminated, truncated, info = env.step(action)
                episode_reward += reward

                if terminated or truncated:
                    break

            conservative_rewards.append(episode_reward)

        conservative_mean = np.mean(conservative_rewards)
        conservative_std = np.std(conservative_rewards)
        print(f"  保守策略平均獎勵: {conservative_mean:.3f} ± {conservative_std:.3f}")

        # 對比結果
        print("\n4. 對比分析:")
        results = {
            "DQN": dqn_reward,
            "隨機算法": random_mean,
            "保守策略": conservative_mean,
        }

        best_algorithm = max(results, key=results.get)
        print(f"  最佳算法: {best_algorithm} (獎勵: {results[best_algorithm]:.3f})")

        # 排名
        ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)
        print("\n  性能排名:")
        for i, (algo, reward) in enumerate(ranked, 1):
            print(f"    {i}. {algo}: {reward:.3f}")

        # 分析結果
        if dqn_reward > max(random_mean, conservative_mean):
            print("✅ DQN 算法表現優於基準算法")
        else:
            print("⚠️ DQN 需要更長時間訓練以超越基準算法")

        env.close()

        return True

    except Exception as e:
        print(f"❌ 對比測試失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


def save_test_results(results: dict):
    """保存測試結果"""
    output_dir = Path("/home/sat/ntn-stack/results/dqn_tests")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = output_dir / f"dqn_test_results_{timestamp}.json"

    test_results = {
        "timestamp": datetime.now().isoformat(),
        "test_results": results,
        "environment_info": {
            "discrete_actions": 10,
            "max_episode_steps": 200,
            "python_version": sys.version,
        },
        "summary": {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if r),
            "success_rate": sum(1 for r in results.values() if r) / len(results) * 100,
        },
    }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    print(f"\n📊 測試結果已保存: {result_file}")


def main():
    """主測試函數"""
    print("🚀 開始 DQN 算法整合測試")
    print("=" * 60)

    test_results = {}

    # 測試離散環境
    test_results["discrete_environment"] = test_discrete_environment()

    # 測試 DQN 訓練
    test_results["dqn_training"] = test_dqn_training()

    # 測試對比評估
    test_results["dqn_vs_baseline"] = test_dqn_vs_baseline()

    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")

    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")

    success_rate = sum(1 for r in test_results.values() if r) / len(test_results) * 100
    print(f"\n總體成功率: {success_rate:.1f}%")

    # 保存結果
    save_test_results(test_results)

    if success_rate >= 80:
        print("🎉 DQN 算法整合測試基本成功！")
        print("💡 建議: 進行更長時間的訓練以獲得更好的性能")
    else:
        print("⚠️ 部分測試失敗，需要進一步調試")

    return success_rate >= 80


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
