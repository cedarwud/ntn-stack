#!/usr/bin/env python3
"""
🔧 簡化後端測試 - 只測試 API
"""

import requests
import time
import json

BASE_URL = "http://localhost:8080"

def test_backend_only():
    """只測試後端 API，不涉及前端"""
    print("🔧 純後端 API 測試...")
    
    # 1. 開始訓練
    print("\n1️⃣ 開始訓練...")
    start_response = requests.post(f"{BASE_URL}/api/v1/rl/training/start/ppo", json={
        "experiment_name": f"backend_test_{int(time.time())}",
        "total_episodes": 100,
        "scenario_type": "test",
        "hyperparameters": {"learning_rate": 0.001, "batch_size": 32}
    })
    
    if start_response.status_code != 200:
        print(f"❌ 開始訓練失敗: {start_response.status_code}")
        return False
    
    print(f"✅ 開始訓練成功: {start_response.json()['session_id']}")
    
    # 等待訓練開始
    time.sleep(3)
    
    # 2. 檢查運行狀態
    print("\n2️⃣ 檢查運行狀態...")
    status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
    if status_response.status_code != 200:
        print(f"❌ 獲取狀態失敗: {status_response.status_code}")
        return False
    
    status = status_response.json()
    print(f"📊 運行狀態: {status['status']} | training_active: {status['training_active']}")
    
    if status['status'] != 'running':
        print(f"❌ 運行狀態錯誤: {status['status']}")
        return False
    
    # 3. 暫停訓練
    print("\n3️⃣ 暫停訓練...")
    pause_response = requests.post(f"{BASE_URL}/api/v1/rl/training/pause/ppo")
    if pause_response.status_code != 200:
        print(f"❌ 暫停失敗: {pause_response.status_code}")
        return False
    
    print(f"✅ 暫停成功: {pause_response.json()['message']}")
    
    # 4. 立即檢查暫停狀態（關鍵測試）
    print("\n4️⃣ 立即檢查暫停狀態...")
    time.sleep(0.5)  # 短暫等待
    
    status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
    if status_response.status_code != 200:
        print(f"❌ 獲取暫停狀態失敗: {status_response.status_code}")
        return False
    
    status = status_response.json()
    print(f"📊 暫停狀態: {status['status']} | training_active: {status['training_active']} | is_training: {status['is_training']}")
    
    # 關鍵檢查
    if status['status'] != 'paused':
        print(f"❌ 後端暫停狀態錯誤！期望 'paused'，實際 '{status['status']}'")
        print("🔍 這是後端問題！")
        return False
    
    if not status['training_active']:
        print(f"❌ 後端 training_active 錯誤！期望 true，實際 {status['training_active']}")
        print("🔍 這是後端問題！")
        return False
    
    print("✅ 後端暫停狀態完全正確！")
    
    # 5. 測試恢復
    print("\n5️⃣ 測試恢復...")
    resume_response = requests.post(f"{BASE_URL}/api/v1/rl/training/resume/ppo")
    if resume_response.status_code != 200:
        print(f"❌ 恢復失敗: {resume_response.status_code}")
        return False
    
    print(f"✅ 恢復成功: {resume_response.json()['message']}")
    
    time.sleep(1)
    status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
    status = status_response.json()
    print(f"📊 恢復狀態: {status['status']} | training_active: {status['training_active']}")
    
    if status['status'] != 'running':
        print(f"❌ 恢復狀態錯誤: {status['status']}")
        return False
    
    # 6. 清理：停止訓練
    print("\n6️⃣ 清理：停止訓練...")
    stop_response = requests.post(f"{BASE_URL}/api/v1/rl/training/stop-algorithm/ppo")
    if stop_response.status_code == 200:
        print("✅ 清理成功")
    
    return True

if __name__ == "__main__":
    print("🚀 開始簡化後端測試...")
    
    success = test_backend_only()
    
    if success:
        print("\n🎉 後端測試通過！問題在前端。")
    else:
        print("\n❌ 後端測試失敗！問題在後端。")
    
    print("\n📝 下一步：")
    if success:
        print("- 問題在前端狀態管理")
        print("- 需要檢查前端數據獲取邏輯")
    else:
        print("- 問題在後端 API")
        print("- 需要檢查後端暫停實現")
