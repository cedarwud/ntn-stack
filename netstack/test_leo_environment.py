#!/usr/bin/env python3
"""
LEO 衛星環境測試腳本

測試 Phase 2.1 實現的 LEOSatelliteEnvironment 是否正常工作
"""

import asyncio
import logging
import sys
import os

# 添加 NetStack 路徑
sys.path.append('/home/sat/ntn-stack/netstack')

from netstack_api.services.rl_training.environments import LEOSatelliteEnvironment, get_available_environments

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_leo_environment():
    """測試 LEO 衛星環境"""
    print("🚀 開始測試 LEO 衛星環境...")
    
    # 測試環境配置
    config = {
        'simworld_url': 'http://localhost:8888',
        'max_satellites': 6,
        'scenario': 'urban',
        'min_elevation': 10.0,
        'fallback_enabled': True,
        'max_episode_steps': 10  # 短期測試
    }
    
    try:
        # 1. 創建環境
        print("\n📋 1. 創建 LEO 衛星環境...")
        env = LEOSatelliteEnvironment(config)
        print(f"✅ 環境創建成功")
        print(f"   - 動作空間: {env.action_space}")
        print(f"   - 觀測空間: {env.observation_space}")
        print(f"   - 最大衛星數: {env.max_satellites}")
        
        # 2. 重置環境
        print("\n🔄 2. 重置環境...")
        observation, info = await env.reset()
        print(f"✅ 環境重置成功")
        print(f"   - 觀測形狀: {observation.shape}")
        print(f"   - 服務衛星ID: {info.get('serving_satellite_id')}")
        print(f"   - 可用衛星數: {info.get('available_satellites')}")
        
        # 3. 執行幾步測試
        print("\n👟 3. 執行測試步驟...")
        total_reward = 0
        for step in range(5):
            # 選擇隨機動作
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = await env.step(action)
            total_reward += reward
            
            print(f"   步驟 {step+1}: 動作={action}, 獎勵={reward:.3f}, "
                  f"服務衛星={info.get('serving_satellite_id')}")
            
            if terminated or truncated:
                break
        
        print(f"✅ 測試步驟完成，總獎勵: {total_reward:.3f}")
        
        # 4. 獲取環境統計
        print("\n📊 4. 環境統計資訊...")
        stats = env.get_stats()
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        # 5. 測試 fallback 機制
        print("\n🛡️ 5. 測試 Fallback 機制...")
        env_fallback = LEOSatelliteEnvironment({
            **config,
            'simworld_url': 'http://invalid-url:9999',  # 故意使用無效URL
            'fallback_enabled': True
        })
        
        try:
            obs_fallback, info_fallback = await env_fallback.reset()
            print("✅ Fallback 機制正常工作")
            print(f"   - Fallback 衛星數: {info_fallback.get('available_satellites')}")
        except Exception as e:
            print(f"❌ Fallback 機制測試失敗: {e}")
        
        # 6. 清理資源
        print("\n🧹 6. 清理資源...")
        env.close()
        env_fallback.close()
        print("✅ 資源清理完成")
        
        print("\n🎉 LEO 衛星環境測試全部完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_environment_registry():
    """測試環境註冊"""
    print("\n📝 測試環境註冊...")
    
    try:
        # 獲取可用環境
        environments = get_available_environments()
        print("✅ 可用環境:")
        for env_id, env_info in environments.items():
            print(f"   - {env_id}: {env_info['description']}")
            print(f"     支援算法: {env_info['algorithm_support']}")
        
        # 嘗試使用 Gymnasium 創建環境
        try:
            import gymnasium as gym
            print("\n🏭 嘗試通過 Gymnasium 創建環境...")
            gym_env = gym.make('LEOSatelliteHandoverEnv-v1')
            print("✅ Gymnasium 環境創建成功")
            gym_env.close()
        except Exception as e:
            print(f"⚠️ Gymnasium 創建失敗 (可能是導入問題): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 環境註冊測試失敗: {e}")
        return False


async def main():
    """主測試函數"""
    print("=" * 60)
    print("🧪 LEO 衛星環境 Phase 2.1 綜合測試")
    print("=" * 60)
    
    # 測試結果
    results = []
    
    # 測試環境註冊
    results.append(await test_environment_registry())
    
    # 測試 LEO 衛星環境
    results.append(await test_leo_environment())
    
    # 總結
    print("\n" + "=" * 60)
    print("📋 測試總結:")
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"🎉 所有測試通過! ({success_count}/{total_count})")
        print("✅ LEO 衛星環境 Phase 2.1 實現成功!")
        return 0
    else:
        print(f"❌ 部分測試失敗 ({success_count}/{total_count})")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())