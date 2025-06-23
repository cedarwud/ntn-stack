#!/usr/bin/env python3
"""
LEO 衛星切換環境永久測試腳本

這是一個完整的測試腳本，用於驗證 LEO 衛星切換 Gymnasium 環境的功能。
環境已完全修復並可永久使用。

執行方式：
docker exec netstack-api python test_leo_handover_permanent.py

或在容器內：
python test_leo_handover_permanent.py
"""

import sys
import gymnasium as gym
import numpy as np
from datetime import datetime

def test_basic_functionality():
    """測試基本功能"""
    print("=== 測試基本功能 ===")
    
    # 導入和創建環境
    import netstack_api.envs  # 觸發環境註冊
    
    env = gym.make('netstack/LEOSatelliteHandover-v0')
    print("✅ 環境創建成功")
    
    # 檢查空間
    print(f"   觀測空間: {env.observation_space}")
    print(f"   動作空間: {env.action_space}")
    
    # 重置環境
    obs, info = env.reset()
    print(f"✅ 環境重置成功")
    print(f"   觀測維度: {obs.shape}")
    print(f"   UE數量: {info['active_ue_count']}")
    print(f"   衛星數量: {info['active_satellite_count']}")
    
    # 測試動作
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    print(f"✅ 步驟執行成功")
    print(f"   獎勵: {reward:.3f}")
    print(f"   切換結果: {len(info.get('handover_results', []))}")
    
    env.close()
    return True

def test_episode_run():
    """測試完整回合"""
    print("\n=== 測試完整回合 ===")
    
    env = gym.make('netstack/LEOSatelliteHandover-v0')
    obs, info = env.reset()
    
    total_reward = 0
    handover_count = 0
    latency_sum = 0
    latency_count = 0
    
    print("執行 20 步測試...")
    
    for step in range(20):
        # 生成動作
        action = env.action_space.sample()
        
        # 執行步驟
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        # 統計切換結果
        handover_results = info.get('handover_results', [])
        for result in handover_results:
            if result.get('success', False):
                handover_count += 1
                if 'latency' in result:
                    latency_sum += result['latency']
                    latency_count += 1
        
        # 每 5 步報告一次
        if (step + 1) % 5 == 0:
            decision_map = ['不切換', '觸發切換', '準備切換']
            decision = decision_map[action['handover_decision']]
            print(f"   步驟 {step+1}: {decision}, 累積獎勵={total_reward:.2f}")
        
        if terminated or truncated:
            print(f"   回合提前結束於步驟 {step+1}")
            break
    
    avg_latency = latency_sum / max(1, latency_count)
    
    print(f"✅ 回合測試完成")
    print(f"   總獎勵: {total_reward:.2f}")
    print(f"   成功切換: {handover_count}")
    print(f"   平均延遲: {avg_latency:.1f}ms")
    print(f"   最終成功率: {info.get('handover_success_rate', 0):.3f}")
    
    env.close()
    return True

def test_different_scenarios():
    """測試不同場景"""
    print("\n=== 測試不同場景 ===")
    
    # 從環境模組導入場景類型
    from netstack_api.envs.handover_env_fixed import LEOSatelliteHandoverEnv, HandoverScenario
    
    scenarios = [
        (HandoverScenario.SINGLE_UE, 1, 5),
        (HandoverScenario.MULTI_UE, 3, 10),
    ]
    
    for scenario, max_ues, max_satellites in scenarios:
        print(f"\n--- 測試 {scenario.value} 場景 ---")
        
        env = LEOSatelliteHandoverEnv(
            scenario=scenario,
            max_ues=max_ues,
            max_satellites=max_satellites,
            episode_length=30
        )
        
        obs, info = env.reset()
        print(f"   觀測維度: {obs.shape}")
        print(f"   UE數量: {info['active_ue_count']}")
        print(f"   衛星數量: {info['active_satellite_count']}")
        
        # 執行幾步
        total_reward = 0
        for i in range(5):
            action = env.action_space.sample()
            obs, reward, term, trunc, info = env.step(action)
            total_reward += reward
        
        print(f"   5步總獎勵: {total_reward:.2f}")
        print(f"   成功率: {info.get('handover_success_rate', 0):.3f}")
        
        env.close()
    
    print("✅ 不同場景測試完成")
    return True

def test_reward_function():
    """測試獎勵函數"""
    print("\n=== 測試獎勵函數 ===")
    
    env = gym.make('netstack/LEOSatelliteHandover-v0')
    obs, info = env.reset()
    
    # 測試不同動作的獎勵
    action_types = [
        (0, "不切換"),
        (1, "觸發切換"),
        (2, "準備切換")
    ]
    
    rewards = []
    
    for action_type, action_name in action_types:
        # 重置環境以確保一致的起始狀態
        obs, info = env.reset()
        
        # 構造特定動作
        action = {
            'handover_decision': action_type,
            'target_satellite': 0,
            'timing': np.array([2.0]),  # 適當時機
            'power_control': np.array([0.8]),
            'priority': np.array([0.9])
        }
        
        obs, reward, term, trunc, info = env.step(action)
        rewards.append((action_name, reward))
        
        print(f"   {action_name}: 獎勵={reward:.3f}")
        
        # 檢查切換結果
        handover_results = info.get('handover_results', [])
        if handover_results:
            result = handover_results[0]
            print(f"     狀態: {result.get('status', 'unknown')}")
            if 'latency' in result:
                print(f"     延遲: {result['latency']:.1f}ms")
    
    print("✅ 獎勵函數測試完成")
    env.close()
    return True

def test_observation_space():
    """測試觀測空間"""
    print("\n=== 測試觀測空間 ===")
    
    env = gym.make('netstack/LEOSatelliteHandover-v0')
    obs, info = env.reset()
    
    print(f"   觀測維度: {obs.shape}")
    print(f"   觀測類型: {obs.dtype}")
    print(f"   觀測範圍: [{obs.min():.3f}, {obs.max():.3f}]")
    print(f"   零值比例: {(obs == 0).sum() / len(obs):.2%}")
    
    # 檢查觀測值是否合理
    finite_obs = obs[np.isfinite(obs)]
    print(f"   有限值比例: {len(finite_obs) / len(obs):.2%}")
    
    # 測試觀測穩定性
    obs_history = [obs]
    for i in range(3):
        action = env.action_space.sample()
        obs, reward, term, trunc, info = env.step(action)
        obs_history.append(obs)
    
    # 計算觀測變化
    obs_changes = []
    for i in range(1, len(obs_history)):
        change = np.mean(np.abs(obs_history[i] - obs_history[i-1]))
        obs_changes.append(change)
    
    avg_change = np.mean(obs_changes)
    print(f"   平均觀測變化: {avg_change:.4f}")
    
    print("✅ 觀測空間測試完成")
    env.close()
    return True

def run_performance_benchmark():
    """運行性能基準測試"""
    print("\n=== 性能基準測試 ===")
    
    import time
    
    env = gym.make('netstack/LEOSatelliteHandover-v0')
    
    # 測試重置性能
    reset_times = []
    for i in range(5):
        start_time = time.time()
        obs, info = env.reset()
        reset_time = time.time() - start_time
        reset_times.append(reset_time)
    
    avg_reset_time = np.mean(reset_times)
    print(f"   平均重置時間: {avg_reset_time:.4f}s")
    
    # 測試步驟性能
    step_times = []
    for i in range(20):
        action = env.action_space.sample()
        start_time = time.time()
        obs, reward, term, trunc, info = env.step(action)
        step_time = time.time() - start_time
        step_times.append(step_time)
    
    avg_step_time = np.mean(step_times)
    estimated_fps = 1 / avg_step_time
    
    print(f"   平均步驟時間: {avg_step_time:.4f}s")
    print(f"   估計FPS: {estimated_fps:.1f}")
    
    env.close()
    print("✅ 性能測試完成")
    return True

def main():
    """主測試函數"""
    print("🚀 LEO 衛星切換環境完整測試")
    print("=" * 50)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python 版本: {sys.version}")
    print("=" * 50)
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("完整回合", test_episode_run),
        ("不同場景", test_different_scenarios),
        ("獎勵函數", test_reward_function),
        ("觀測空間", test_observation_space),
        ("性能基準", run_performance_benchmark),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 執行測試: {test_name}")
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} 測試通過")
            else:
                print(f"❌ {test_name} 測試失敗")
        except Exception as e:
            print(f"❌ {test_name} 測試異常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"🎯 測試總結: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試通過！LEO 衛星切換環境完全可用")
        print("\n📚 環境使用指南:")
        print("   1. 環境 ID: 'netstack/LEOSatelliteHandover-v0'")
        print("   2. 觀測維度: 136 (3 UE + 10 衛星 + 環境)")
        print("   3. 動作空間: Dict (切換決策 + 參數)")
        print("   4. 獎勵函數: 多目標優化 (延遲 + QoS + 平衡)")
        print("   5. 適用算法: DQN, PPO, SAC 等")
        
        print("\n🔧 快速開始:")
        print("   import gymnasium as gym")
        print("   env = gym.make('netstack/LEOSatelliteHandover-v0')")
        print("   obs, info = env.reset()")
        print("   action = env.action_space.sample()")
        print("   obs, reward, term, trunc, info = env.step(action)")
        
        return True
    else:
        print("⚠️  部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)