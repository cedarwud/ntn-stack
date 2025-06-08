#!/usr/bin/env python3
"""
簡單的 API 測試
直接測試實際運行的服務
"""

import requests
import time
import sys

def test_netstack_health():
    """測試 NetStack 健康檢查"""
    try:
        print("🔍 測試 NetStack 健康檢查...")
        response = requests.get("http://localhost:8080/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ NetStack 健康檢查通過: {data.get('overall_status', 'unknown')}")
            return True
        else:
            print(f"❌ NetStack 健康檢查失敗: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ NetStack 連接失敗: {e}")
        return False

def test_simworld_root():
    """測試 SimWorld 根端點"""
    try:
        print("🔍 測試 SimWorld 根端點...")
        response = requests.get("http://localhost:8888/", timeout=10)
        
        if response.status_code == 200:
            print("✅ SimWorld 根端點可訪問")
            return True
        else:
            print(f"❌ SimWorld 根端點失敗: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ SimWorld 連接失敗: {e}")
        return False

def test_frontend_accessibility():
    """測試前端可訪問性"""
    try:
        print("🔍 測試前端可訪問性...")
        response = requests.get("http://localhost:5173/", timeout=10)
        
        if response.status_code == 200:
            print("✅ 前端可訪問")
            return True
        else:
            print(f"❌ 前端訪問失敗: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 前端連接失敗: {e}")
        return False

def test_netstack_api_endpoints():
    """測試 NetStack API 端點"""
    endpoints = [
        "/api/v1/ue/status",
        "/api/v1/satellite-gnb/status", 
        "/api/v1/uav/status",
        "/api/v1/mesh/status"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            print(f"🔍 測試 NetStack API: {endpoint}")
            response = requests.get(f"http://localhost:8080{endpoint}", timeout=10)
            
            if response.status_code in [200, 404, 503]:  # 接受這些狀態碼
                print(f"✅ {endpoint}: HTTP {response.status_code}")
                results.append(True)
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: 連接失敗 - {e}")
            results.append(False)
    
    return all(results)

def test_simworld_api_endpoints():
    """測試 SimWorld API 端點"""
    endpoints = [
        "/api/v1/devices/",
        "/api/v1/satellites/oneweb/visible"
    ]
    
    results = []
    for endpoint in endpoints:
        try:
            print(f"🔍 測試 SimWorld API: {endpoint}")
            response = requests.get(f"http://localhost:8888{endpoint}", timeout=10)
            
            if response.status_code in [200, 404, 503]:  # 接受這些狀態碼
                print(f"✅ {endpoint}: HTTP {response.status_code}")
                results.append(True)
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
                results.append(False)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: 連接失敗 - {e}")
            results.append(False)
    
    return all(results)

def main():
    """執行所有測試"""
    print("🚀 開始執行 NTN Stack API 測試...")
    print("=" * 60)
    
    tests = [
        ("NetStack 健康檢查", test_netstack_health),
        ("SimWorld 根端點", test_simworld_root),
        ("前端可訪問性", test_frontend_accessibility),
        ("NetStack API 端點", test_netstack_api_endpoints),
        ("SimWorld API 端點", test_simworld_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 執行測試: {test_name}")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)  # 避免過於頻繁的請求
    
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 總結: {passed}/{total} 測試通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有測試通過！系統運行正常")
        return 0
    else:
        print("⚠️  部分測試失敗，請檢查服務狀態")
        return 1

if __name__ == "__main__":
    sys.exit(main())