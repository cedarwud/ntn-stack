#!/usr/bin/env python3
"""
🔧 最終修復測試
"""

import requests
import time

BASE_URL = "http://localhost:8080"


def test_final_fix():
    """測試最終修復"""
    print("🔧 測試最終修復...")

    # 1. 開始訓練
    print("\n1️⃣ 開始訓練...")
    start_response = requests.post(
        f"{BASE_URL}/api/v1/rl/training/start/ppo",
        json={
            "experiment_name": f"final_test_{int(time.time())}",
            "total_episodes": 100,
            "scenario_type": "test",
            "hyperparameters": {"learning_rate": 0.001, "batch_size": 32},
        },
    )

    if start_response.status_code != 200:
        print(f"❌ 開始訓練失敗")
        return False

    print("✅ 開始訓練成功")
    time.sleep(3)

    # 2. 暫停訓練
    print("\n2️⃣ 暫停訓練...")
    pause_response = requests.post(f"{BASE_URL}/api/v1/rl/training/pause/ppo")
    if pause_response.status_code != 200:
        print(f"❌ 暫停失敗")
        return False

    print("✅ 暫停成功")
    time.sleep(1)

    # 3. 檢查暫停狀態
    print("\n3️⃣ 檢查暫停狀態...")
    status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
    if status_response.status_code == 200:
        status = status_response.json()
        print(
            f"📊 狀態: {status['status']} | training_active: {status['training_active']} | is_training: {status['is_training']}"
        )

        if (
            status["status"] == "paused"
            and status["training_active"]
            and not status["is_training"]
        ):
            print("✅ 後端暫停狀態正確")
        else:
            print("❌ 後端暫停狀態錯誤")
            return False
    else:
        print("❌ 獲取狀態失敗")
        return False

    # 4. 檢查訓練會話 API
    print("\n4️⃣ 檢查訓練會話 API...")
    sessions_response = requests.get(f"{BASE_URL}/api/v1/rl/training/sessions")
    if sessions_response.status_code == 200:
        sessions = sessions_response.json()
        active_sessions = (
            sessions
            if isinstance(sessions, list)
            else sessions.get("active_sessions", [])
        )
        print(f"📊 活躍會話數: {len(active_sessions)}")

        ppo_session = None
        for session in active_sessions:
            if session.get("algorithm") == "ppo":
                ppo_session = session
                break

        if ppo_session:
            print(f"📊 PPO 會話狀態: {ppo_session.get('status')}")
            if ppo_session.get("status") == "paused":
                print("✅ 會話 API 中 PPO 狀態正確（paused）")
                print("🎯 前端應該能正確識別暫停狀態")
            else:
                print(f"❌ 會話 API 中 PPO 狀態錯誤: {ppo_session.get('status')}")
        else:
            print("❌ 會話 API 中找不到 PPO 會話")
    else:
        print("❌ 獲取會話失敗")

    # 5. 測試恢復
    print("\n5️⃣ 測試恢復...")
    resume_response = requests.post(f"{BASE_URL}/api/v1/rl/training/resume/ppo")
    if resume_response.status_code == 200:
        print("✅ 恢復成功")
        time.sleep(1)

        status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
        if status_response.status_code == 200:
            status = status_response.json()
            print(
                f"📊 恢復後狀態: {status['status']} | training_active: {status['training_active']}"
            )
            if status["status"] == "running" and status["training_active"]:
                print("✅ 恢復狀態正確")
            else:
                print("❌ 恢復狀態錯誤")

    else:
        print("❌ 恢復失敗")

    # 清理
    print("\n🧹 清理...")
    requests.post(f"{BASE_URL}/api/v1/rl/training/stop-algorithm/ppo")

    return True


if __name__ == "__main__":
    test_final_fix()

    print("\n🎯 修復說明：")
    print("修復了前端狀態管理中的關鍵 bug：")
    print("- 原來只查找 status === 'running' 的會話")
    print("- 現在查找 status === 'running' 或 'paused' 的會話")
    print("- 這樣暫停狀態的會話也會被正確識別")

    print("\n📝 用戶操作：")
    print("1. 刷新瀏覽器頁面")
    print("2. 測試：開始 → 暫停 → 應該顯示「恢復」按鈕")
    print("3. 如果仍有問題，可能需要清除瀏覽器緩存")
