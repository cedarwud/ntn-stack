#!/usr/bin/env python3
"""
Quick Phase 1 驗證腳本 - 檢查座標軌道 API 端點狀態
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(url, description):
    """測試單個端點"""
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start_time
        
        result = {
            "description": description,
            "url": url,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time_ms": round(response_time * 1000, 2),
        }
        
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    result["data_keys"] = list(data.keys())[:5]  # 只顯示前5個key
                elif isinstance(data, list):
                    result["data_length"] = len(data)
            except:
                result["response_type"] = "non-json"
        else:
            result["error"] = response.text[:200]
            
        return result
        
    except Exception as e:
        return {
            "description": description,
            "url": url,
            "status_code": 0,
            "success": False,
            "error": str(e)
        }

def main():
    print("🚀 Phase 1 座標軌道 API 快速驗證")
    print("=" * 60)
    
    # 測試端點列表
    endpoints = [
        ("http://localhost:8080/api/v1/satellites/locations", "支援位置列表"),
        ("http://localhost:8080/api/v1/satellites/precomputed/ntpu", "NTPU預計算數據"),
        ("http://localhost:8080/api/v1/satellites/optimal-window/ntpu", "NTPU最佳時間窗"),
        ("http://localhost:8080/api/v1/satellites/display-data/ntpu", "NTPU顯示數據"),
        ("http://localhost:8080/api/v1/satellites/health/precomputed", "預計算健康檢查"),
    ]
    
    # 測試基礎健康端點
    base_health_endpoints = [
        ("http://localhost:8080/health", "NetStack基礎健康"),
        ("http://localhost:8888/health", "SimWorld健康"),
    ]
    
    results = []
    
    print("\n📍 基礎健康檢查:")
    print("-" * 30)
    for url, desc in base_health_endpoints:
        result = test_endpoint(url, desc)
        results.append(result)
        
        status_emoji = "✅" if result["success"] else "❌"
        print(f"{status_emoji} {desc}: {result['status_code']} ({result.get('response_time_ms', 'N/A')}ms)")
    
    print("\n🛰️ Phase 1 座標軌道 API 測試:")
    print("-" * 30)
    for url, desc in endpoints:
        result = test_endpoint(url, desc)
        results.append(result)
        
        status_emoji = "✅" if result["success"] else "❌"
        print(f"{status_emoji} {desc}: {result['status_code']} ({result.get('response_time_ms', 'N/A')}ms)")
        
        if result["success"] and "data_keys" in result:
            print(f"   📊 數據結構: {result['data_keys']}")
        elif not result["success"] and "error" in result:
            print(f"   ❌ 錯誤: {result['error'][:100]}...")
    
    # 統計結果
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n📊 測試總結:")
    print(f"   總測試數: {total_tests}")
    print(f"   成功: {successful_tests}")
    print(f"   失敗: {total_tests - successful_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    
    # 生成簡化報告
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 1 - Sky Project Integration (Quick Check)",
        "summary": {
            "total_tests": total_tests,
            "passed": successful_tests,
            "failed": total_tests - successful_tests,
            "success_rate": success_rate
        },
        "test_results": results
    }
    
    with open("/home/sat/ntn-stack/quick_phase1_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細報告已保存到: quick_phase1_report.json")
    
    if success_rate >= 85:
        print(f"\n🎉 Phase 1 驗證通過！成功率: {success_rate:.1f}%")
        return 0
    else:
        print(f"\n⚠️ Phase 1 需要進一步修復，成功率: {success_rate:.1f}%")
        return 1

if __name__ == "__main__":
    exit(main())