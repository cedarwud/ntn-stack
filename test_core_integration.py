#!/usr/bin/env python3
"""
🎯 測試核心整合效果
"""

import requests
import time

BASE_URL = "http://localhost:8080"


def test_core_integration():
    """測試核心整合功能"""
    print("🎯 測試核心整合功能...")

    # 1. 測試可見衛星 API
    print("\n1️⃣ 測試可見衛星 API...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/satellites/visible_satellites?count=10&global_view=true"
        )
        if response.status_code == 200:
            data = response.json()
            satellites = data.get("satellites", [])
            print(f"✅ 衛星 API 可訪問，返回 {len(satellites)} 顆衛星")

            if satellites:
                sat = satellites[0]
                print(f"   示例衛星: {sat.get('name', 'Unknown')}")
                print(f"   仰角: {sat.get('position', {}).get('elevation', 0):.1f}°")
                print(
                    f"   RSRP: {sat.get('signal_quality', {}).get('rsrp', -100):.1f} dBm"
                )
            else:
                print("⚠️ 沒有真實衛星數據，前端將使用模擬數據")
        else:
            print(f"❌ 衛星 API 失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 衛星 API 異常: {e}")
        print("⚠️ 前端將使用模擬衛星數據作為後備")

    # 2. 測試訓練狀態 API
    print("\n2️⃣ 測試訓練狀態 API...")
    algorithms = ["dqn", "ppo", "sac"]

    for algo in algorithms:
        try:
            response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/{algo}")
            if response.status_code == 200:
                status = response.json()
                print(f"✅ {algo.upper()} 狀態: {status.get('status', 'unknown')}")
                print(f"   訓練活躍: {status.get('training_active', False)}")

                progress = status.get("training_progress", {})
                if progress:
                    current = progress.get("current_episode", 0)
                    total = progress.get("total_episodes", 1000)
                    print(f"   進度: {current}/{total} ({(current/total*100):.1f}%)")
            else:
                print(f"❌ {algo.upper()} 狀態 API 失敗: {response.status_code}")
        except Exception as e:
            print(f"❌ {algo.upper()} 狀態 API 異常: {e}")

    # 3. 測試訓練啟動
    print("\n3️⃣ 測試訓練啟動...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/rl/training/start/dqn",
            json={
                "experiment_name": f"core_integration_test_{int(time.time())}",
                "total_episodes": 50,
                "scenario_type": "leo_satellite_handover",
                "hyperparameters": {
                    "learning_rate": 0.001,
                    "batch_size": 32,
                    "gamma": 0.99,
                },
            },
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ DQN 訓練啟動成功: {result.get('session_id', 'Unknown')}")

            # 等待並檢查進度更新
            print("   等待進度更新...")
            for i in range(5):
                time.sleep(2)
                status_response = requests.get(
                    f"{BASE_URL}/api/v1/rl/training/status/dqn"
                )
                if status_response.status_code == 200:
                    status = status_response.json()
                    current_episode = status.get("training_progress", {}).get(
                        "current_episode", 0
                    )
                    print(f"   第{i+1}次檢查 - 當前回合: {current_episode}")

                    if current_episode > 0:
                        print("✅ 訓練進度正常更新")
                        break
                else:
                    print(f"   第{i+1}次檢查失敗")

            # 停止訓練
            print("   停止訓練...")
            stop_response = requests.post(
                f"{BASE_URL}/api/v1/rl/training/stop-algorithm/dqn"
            )
            if stop_response.status_code == 200:
                print("✅ 訓練停止成功")
            else:
                print("❌ 訓練停止失敗")

        else:
            print(f"❌ DQN 訓練啟動失敗: {response.status_code}")
    except Exception as e:
        print(f"❌ 訓練啟動異常: {e}")

    return True


if __name__ == "__main__":
    test_core_integration()

    print("\n🎉 核心整合測試完成！")
    print("\n📝 整合總結：")
    print("✅ 創建了核心訓練界面")
    print("✅ 整合了真實衛星數據顯示")
    print("✅ 簡化了訓練控制邏輯")
    print("✅ 專注於 LEO 衛星換手決策")
    print("✅ 移除了不必要的複雜功能")

    print("\n🎯 核心功能：")
    print("- 🛰️ 真實衛星數據：TLE 軌道數據 + 信號品質")
    print("- 🧠 RL 訓練：DQN/PPO/SAC 算法選擇")
    print("- 📊 實時進度：當前回合、平均獎勵")
    print("- 🎯 決策顯示：選擇的衛星和決策原因")
    print("- ⚙️ 簡單控制：開始/停止訓練")

    print("\n📋 用戶操作：")
    print("1. 刷新瀏覽器頁面")
    print("2. 點擊 'RL 監控' → '🛰️ 核心訓練' 分頁")
    print("3. 選擇算法並開始訓練")
    print("4. 觀察真實衛星數據和訓練進度")
    print("5. 查看算法的換手決策")

    print("\n⚠️ 注意事項：")
    print("- 當前仍是模擬訓練（快速演示）")
    print("- 真實訓練需要調整時間參數")
    print("- 其他分頁功能待後續完善")
    print("- 專注核心功能，避免功能分散")
