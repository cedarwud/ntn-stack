#!/usr/bin/env python3
"""
LEO 衛星切換環境測試腳本

測試環境功能：
1. 環境創建和初始化
2. 狀態空間和動作空間
3. 基本的 step 功能
4. 獎勵計算
5. 與真實服務的整合

執行方式：
python test_leo_handover_env.py
"""

import sys
import os
import asyncio
import numpy as np
from datetime import datetime
import json
import time

# 添加 netstack 路徑
sys.path.append('/home/sat/ntn-stack/netstack')

# 導入環境
from netstack_api.envs.handover_env import (
    LEOSatelliteHandoverEnv,
    HandoverScenario,
    UEState,
    SatelliteState
)

def test_environment_creation():
    """測試環境創建"""
    print("=== 測試環境創建 ===")
    
    # 測試單UE場景
    env = LEOSatelliteHandoverEnv(
        scenario=HandoverScenario.SINGLE_UE,
        max_ues=1,
        max_satellites=10,
        episode_length=100
    )
    
    print(f"✅ 單UE環境創建成功")
    print(f"   觀測空間: {env.observation_space}")
    print(f"   動作空間: {env.action_space}")
    
    # 測試多UE場景
    env_multi = LEOSatelliteHandoverEnv(
        scenario=HandoverScenario.MULTI_UE,
        max_ues=5,
        max_satellites=20,
        episode_length=200
    )
    
    print(f"✅ 多UE環境創建成功")
    print(f"   觀測空間: {env_multi.observation_space}")
    print(f"   動作空間: {env_multi.action_space}")
    
    return env, env_multi

def test_environment_reset(env):
    """測試環境重置"""
    print("\n=== 測試環境重置 ===")
    
    obs, info = env.reset()
    
    print(f"✅ 環境重置成功")
    print(f"   觀測維度: {obs.shape}")
    print(f"   觀測範圍: [{obs.min():.3f}, {obs.max():.3f}]")
    print(f"   資訊字典: {list(info.keys())}")
    print(f"   UE數量: {info.get('active_ue_count', 0)}")
    print(f"   衛星數量: {info.get('active_satellite_count', 0)}")
    
    return obs, info

def test_action_space(env):
    """測試動作空間"""
    print("\n=== 測試動作空間 ===")
    
    # 測試隨機動作
    action = env.action_space.sample()
    print(f"✅ 隨機動作生成成功")
    print(f"   動作: {action}")
    
    # 測試手動動作 (單UE場景)
    if env.scenario == HandoverScenario.SINGLE_UE:
        manual_action = {
            "handover_decision": 1,  # trigger_handover
            "target_satellite": 0,
            "timing": np.array([2.0]),
            "power_control": np.array([0.8]),
            "priority": np.array([0.9])
        }
        print(f"✅ 手動動作構造成功")
        print(f"   動作: {manual_action}")
        return manual_action
    
    return action

def test_environment_step(env, action):
    """測試環境步驟"""
    print("\n=== 測試環境步驟 ===")
    
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f"✅ 環境步驟執行成功")
    print(f"   獎勵: {reward:.3f}")
    print(f"   結束: {terminated}")
    print(f"   截斷: {truncated}")
    print(f"   切換結果: {info.get('handover_results', [])}")
    print(f"   成功率: {info.get('handover_success_rate', 0):.3f}")
    print(f"   平均延遲: {info.get('average_handover_latency', 0):.1f}ms")
    
    return obs, reward, info

def test_episode_run(env, max_steps=10):
    """測試完整回合"""
    print(f"\n=== 測試完整回合 ({max_steps} 步) ===")
    
    obs, info = env.reset()
    total_reward = 0
    handover_count = 0
    
    for step in range(max_steps):
        # 生成動作
        action = env.action_space.sample()
        
        # 執行步驟
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        # 統計切換
        handover_results = info.get('handover_results', [])
        handover_count += len([r for r in handover_results if r.get('success', False)])
        
        print(f"   步驟 {step+1}: 獎勵={reward:.2f}, 累積獎勵={total_reward:.2f}")
        
        if terminated or truncated:
            print(f"   回合結束於步驟 {step+1}")
            break
    
    print(f"✅ 回合完成")
    print(f"   總獎勵: {total_reward:.3f}")
    print(f"   成功切換: {handover_count}")
    print(f"   最終成功率: {info.get('handover_success_rate', 0):.3f}")
    print(f"   平均延遲: {info.get('average_handover_latency', 0):.1f}ms")

def test_reward_calculation(env):
    """測試獎勵計算"""
    print("\n=== 測試獎勵計算 ===")
    
    env.reset()
    
    # 測試不同動作的獎勵
    if env.scenario == HandoverScenario.SINGLE_UE:
        # 測試不切換
        no_handover_action = {
            "handover_decision": 0,  # no_handover
            "target_satellite": 0,
            "timing": np.array([0.0]),
            "power_control": np.array([1.0]),
            "priority": np.array([0.5])
        }
        
        _, reward_no, _, _, _ = env.step(no_handover_action)
        print(f"   不切換獎勵: {reward_no:.3f}")
        
        # 重置環境
        env.reset()
        
        # 測試切換
        handover_action = {
            "handover_decision": 1,  # trigger_handover
            "target_satellite": 0,
            "timing": np.array([2.0]),  # 適當時機
            "power_control": np.array([0.8]),
            "priority": np.array([0.9])
        }
        
        _, reward_handover, _, _, info = env.step(handover_action)
        print(f"   切換獎勵: {reward_handover:.3f}")
        print(f"   切換結果: {info.get('handover_results', [])}")

def test_data_integration():
    """測試數據整合"""
    print("\n=== 測試數據整合 ===")
    
    # 測試環境的數據獲取
    env = LEOSatelliteHandoverEnv(
        scenario=HandoverScenario.SINGLE_UE,
        max_ues=3,
        max_satellites=15,
        netstack_api_url="http://netstack-api:8080",
        simworld_api_url="http://simworld_backend:8888"
    )
    
    print("✅ 環境創建成功，配置API連接")
    
    # 重置環境會嘗試獲取真實數據
    obs, info = env.reset()
    
    print(f"   UE數量: {info.get('active_ue_count', 0)}")
    print(f"   衛星數量: {info.get('active_satellite_count', 0)}")
    
    # 檢查是否有真實數據
    if hasattr(env, 'ue_states') and env.ue_states:
        ue_id = list(env.ue_states.keys())[0]
        ue_state = env.ue_states[ue_id]
        print(f"   樣本UE狀態: {ue_id}")
        print(f"     位置: ({ue_state.latitude:.3f}, {ue_state.longitude:.3f})")
        print(f"     信號強度: {ue_state.signal_strength:.1f} dBm")
        print(f"     SINR: {ue_state.sinr:.1f} dB")
    
    if hasattr(env, 'satellite_states') and env.satellite_states:
        sat_id = list(env.satellite_states.keys())[0]
        sat_state = env.satellite_states[sat_id]
        print(f"   樣本衛星狀態: {sat_id}")
        print(f"     位置: ({sat_state.latitude:.3f}, {sat_state.longitude:.3f})")
        print(f"     負載: {sat_state.load_factor:.3f}")
        print(f"     可用性: {sat_state.is_available}")

def test_gymnasium_integration():
    """測試 Gymnasium 整合"""
    print("\n=== 測試 Gymnasium 整合 ===")
    
    try:
        import gymnasium as gym
        # 測試環境註冊
        env = gym.make('netstack/LEOSatelliteHandover-v0')
        print("✅ Gymnasium 整合成功")
        
        # 測試基本功能
        obs, info = env.reset()
        print(f"   觀測空間: {env.observation_space}")
        print(f"   動作空間: {env.action_space}")
        
        # 測試一步
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"   步驟執行成功，獎勵: {reward:.3f}")
        
        env.close()
        
    except Exception as e:
        print(f"❌ Gymnasium 整合失敗: {e}")

def run_performance_test():
    """運行性能測試"""
    print("\n=== 性能測試 ===")
    
    env = LEOSatelliteHandoverEnv(
        scenario=HandoverScenario.SINGLE_UE,
        max_ues=5,
        max_satellites=30,
        episode_length=100
    )
    
    # 測試重置性能
    start_time = time.time()
    obs, info = env.reset()
    reset_time = time.time() - start_time
    print(f"   重置時間: {reset_time:.3f}s")
    
    # 測試步驟性能
    step_times = []
    for i in range(10):
        action = env.action_space.sample()
        start_time = time.time()
        obs, reward, terminated, truncated, info = env.step(action)
        step_time = time.time() - start_time
        step_times.append(step_time)
    
    avg_step_time = np.mean(step_times)
    print(f"   平均步驟時間: {avg_step_time:.4f}s")
    print(f"   估計FPS: {1/avg_step_time:.1f}")

def main():
    """主測試函數"""
    print("🚀 開始 LEO 衛星切換環境測試")
    print("=" * 50)
    
    try:
        # 1. 環境創建測試
        env, env_multi = test_environment_creation()
        
        # 2. 環境重置測試
        obs, info = test_environment_reset(env)
        
        # 3. 動作空間測試
        action = test_action_space(env)
        
        # 4. 環境步驟測試
        obs, reward, info = test_environment_step(env, action)
        
        # 5. 完整回合測試
        test_episode_run(env, max_steps=5)
        
        # 6. 獎勵計算測試
        test_reward_calculation(env)
        
        # 7. 數據整合測試
        test_data_integration()
        
        # 8. Gymnasium 整合測試
        test_gymnasium_integration()
        
        # 9. 性能測試
        run_performance_test()
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("✅ 所有測試完成！LEO 衛星切換環境已準備就緒")
    print("\n🎯 環境功能總結:")
    print("   • 支援單UE和多UE場景")
    print("   • 完整的狀態空間和動作空間")
    print("   • 多目標獎勵函數")
    print("   • 真實數據整合能力")
    print("   • Gymnasium 標準介面")
    print("   • 性能優化")
    
    print("\n🔧 使用方式:")
    print("   import gymnasium as gym")
    print("   env = gym.make('netstack/LEOSatelliteHandover-v0')")
    print("   obs, info = env.reset()")
    print("   action = env.action_space.sample()")
    print("   obs, reward, terminated, truncated, info = env.step(action)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)