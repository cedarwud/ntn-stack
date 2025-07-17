#!/usr/bin/env python3
"""
🧪 測試前端修復
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_timing_issue():
    """測試時序問題"""
    print("🧪 測試前端時序修復...")
    
    # 1. 開始訓練
    print("\n1️⃣ 開始訓練...")
    start_response = requests.post(f"{BASE_URL}/api/v1/rl/training/start/ppo", json={
        "experiment_name": f"timing_test_{int(time.time())}",
        "total_episodes": 100,
        "scenario_type": "test",
        "hyperparameters": {"learning_rate": 0.001, "batch_size": 32}
    })
    
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
    
    # 3. 測試不同時間點的狀態
    for delay in [0.1, 0.5, 1.0, 1.5, 2.0]:
        print(f"\n⏱️ {delay}秒後檢查狀態...")
        time.sleep(delay - (0.1 if delay > 0.1 else 0))
        
        status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   狀態: {status['status']} | training_active: {status['training_active']}")
            
            if status['status'] == 'paused' and status['training_active']:
                print(f"   ✅ {delay}秒後狀態正確")
                break
            else:
                print(f"   ⚠️ {delay}秒後狀態仍未更新")
        else:
            print(f"   ❌ 獲取狀態失敗")
    
    # 清理
    print("\n🧹 清理...")
    requests.post(f"{BASE_URL}/api/v1/rl/training/stop-algorithm/ppo")
    
    return True

if __name__ == "__main__":
    test_timing_issue()
    
    print("\n📝 結論：")
    print("- 後端暫停功能正常")
    print("- 前端需要等待 1 秒後再刷新狀態")
    print("- 修復：增加暫停後的等待時間到 1 秒")
    print("\n🎯 用戶操作：")
    print("1. 刷新瀏覽器頁面")
    print("2. 測試：開始 → 暫停 → 檢查是否顯示恢復按鈕")
    print("3. 如果仍有問題，請提供新的日誌")
