#!/usr/bin/env python3
"""
簡化的 LEO 衛星環境測試

直接測試 LEOSatelliteEnvironment 類，不依賴複雜的 RL 系統
"""

import asyncio
import logging
import sys
import os
import numpy as np

# 簡化導入，避免複雜依賴
sys.path.append('/home/sat/ntn-stack/netstack')

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_direct_leo_environment():
    """直接測試 LEO 衛星環境"""
    print("🚀 直接測試 LEO 衛星環境...")
    
    try:
        # 直接導入 LEOSatelliteEnvironment
        from netstack_api.services.rl_training.environments.leo_satellite_environment import LEOSatelliteEnvironment
        
        # 測試配置
        config = {
            'simworld_url': 'http://localhost:8888',
            'max_satellites': 6,
            'scenario': 'urban',
            'min_elevation': 10.0,
            'fallback_enabled': True,
            'max_episode_steps': 10
        }
        
        print("📋 1. 創建環境...")
        env = LEOSatelliteEnvironment(config)
        print(f"✅ 環境創建成功")
        print(f"   - 動作空間: {env.action_space}")
        print(f"   - 觀測空間形狀: {env.observation_space.shape}")
        
        print("\n🔄 2. 重置環境...")
        observation, info = await env.reset()
        print(f"✅ 環境重置成功")
        print(f"   - 觀測形狀: {observation.shape}")
        print(f"   - 服務衛星ID: {info.get('serving_satellite_id')}")
        print(f"   - 可用衛星數: {info.get('available_satellites')}")
        
        print("\n👟 3. 執行測試步驟...")
        total_reward = 0
        for step in range(3):
            action = np.random.randint(0, env.max_satellites)
            obs, reward, terminated, truncated, info = await env.step(action)
            total_reward += reward
            
            print(f"   步驟 {step+1}: 動作={action}, 獎勵={reward:.3f}, "
                  f"服務衛星={info.get('serving_satellite_id')}")
            
            if terminated or truncated:
                break
        
        print(f"✅ 測試完成，總獎勵: {total_reward:.3f}")
        
        print("\n📊 4. 環境統計...")
        stats = env.get_stats()
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        print("\n🛡️ 5. 測試 Fallback 機制...")
        env_fallback = LEOSatelliteEnvironment({
            **config,
            'simworld_url': 'http://invalid-url:9999',
            'fallback_enabled': True
        })
        
        obs_fallback, info_fallback = await env_fallback.reset()
        print("✅ Fallback 機制正常")
        print(f"   - Fallback 衛星數: {info_fallback.get('available_satellites')}")
        
        env.close()
        env_fallback.close()
        
        print("\n🎉 LEO 衛星環境測試成功!")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simworld_api():
    """測試 SimWorld API 連接"""
    print("\n🌍 測試 SimWorld API 連接...")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            # 測試衛星 API
            url = "http://localhost:8888/api/v1/satellites/visible_satellites"
            params = {'count': 6, 'min_elevation_deg': 10.0}
            
            async with session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    satellites = data.get('satellites', [])
                    print(f"✅ SimWorld API 正常，返回 {len(satellites)} 顆衛星")
                    
                    # 顯示第一顆衛星的詳細資訊
                    if satellites:
                        sat = satellites[0]
                        print(f"   - 示例衛星: {sat['name']} (ID: {sat['id']})")
                        print(f"   - 位置: {sat['position']['latitude']:.2f}°, {sat['position']['longitude']:.2f}°")
                        print(f"   - 仰角: {sat['position']['elevation']:.2f}°")
                    
                    return True
                else:
                    print(f"❌ SimWorld API 響應錯誤: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"⚠️ SimWorld API 連接失敗: {e}")
        print("   將使用 fallback 機制")
        return False


async def main():
    """主測試函數"""
    print("=" * 60)
    print("🧪 LEO 衛星環境簡化測試 (Phase 2.1)")
    print("=" * 60)
    
    # 測試 SimWorld API
    api_ok = await test_simworld_api()
    
    # 測試 LEO 環境
    env_ok = await test_direct_leo_environment()
    
    print("\n" + "=" * 60)
    print("📋 測試總結:")
    if env_ok:
        print("🎉 LEO 衛星環境核心功能正常!")
        if api_ok:
            print("✅ SimWorld API 整合成功")
        else:
            print("⚠️ SimWorld API 不可用，但 fallback 機制正常")
        print("✅ Phase 2.1 衛星軌道動力學整合 - 基礎完成!")
        return 0
    else:
        print("❌ LEO 衛星環境測試失敗")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())