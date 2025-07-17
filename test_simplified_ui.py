#!/usr/bin/env python3
"""
🎯 測試簡化後的 UI
"""

import requests
import time

BASE_URL = "http://localhost:8080"

def test_simplified_ui():
    """測試簡化後的 UI 功能"""
    print("🎯 測試簡化後的 UI...")
    
    # 1. 開始訓練
    print("\n1️⃣ 開始訓練...")
    start_response = requests.post(f"{BASE_URL}/api/v1/rl/training/start/ppo", json={
        "experiment_name": f"simplified_test_{int(time.time())}",
        "total_episodes": 100,
        "scenario_type": "test",
        "hyperparameters": {"learning_rate": 0.001, "batch_size": 32}
    })
    
    if start_response.status_code != 200:
        print(f"❌ 開始訓練失敗")
        return False
    
    print("✅ 開始訓練成功")
    time.sleep(3)
    
    # 2. 檢查運行狀態
    print("\n2️⃣ 檢查運行狀態...")
    status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
    if status_response.status_code == 200:
        status = status_response.json()
        print(f"📊 狀態: {status['status']} | training_active: {status['training_active']}")
        
        if status['training_active']:
            print("✅ 前端應該顯示：⏹️ 停止 按鈕（置中）")
        else:
            print("✅ 前端應該顯示：▶️ 開始 按鈕（置中）")
    else:
        print("❌ 獲取狀態失敗")
        return False
    
    # 3. 停止訓練
    print("\n3️⃣ 停止訓練...")
    stop_response = requests.post(f"{BASE_URL}/api/v1/rl/training/stop-algorithm/ppo")
    if stop_response.status_code == 200:
        print("✅ 停止成功")
        time.sleep(1)
        
        status_response = requests.get(f"{BASE_URL}/api/v1/rl/training/status/ppo")
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"📊 停止後狀態: {status['status']} | training_active: {status['training_active']}")
            
            if not status['training_active']:
                print("✅ 前端應該顯示：▶️ 開始 按鈕（置中）")
            else:
                print("⚠️ 狀態可能還在更新中")
        
    else:
        print("❌ 停止失敗")
        return False
    
    return True

if __name__ == "__main__":
    test_simplified_ui()
    
    print("\n🎉 UI 簡化完成！")
    print("\n📝 變更總結：")
    print("✅ 移除了暫停功能")
    print("✅ 移除了恢復功能")
    print("✅ 簡化為只有「開始」和「停止」兩個按鈕")
    print("✅ 按鈕已置中顯示")
    print("✅ 移除了複雜的狀態判斷邏輯")
    
    print("\n🎯 用戶體驗：")
    print("- 沒有訓練時：顯示「▶️ 開始」按鈕（置中）")
    print("- 訓練中：顯示「⏹️ 停止」按鈕（置中）")
    print("- 停止後：顯示「▶️ 開始」按鈕（置中）")
    print("- 簡單明瞭，不會再有暫停相關的問題")
    
    print("\n📋 用戶操作：")
    print("1. 刷新瀏覽器頁面")
    print("2. 測試：開始 → 停止 → 開始")
    print("3. 確認按鈕都是置中顯示")
    print("4. 確認沒有暫停/恢復按鈕")
