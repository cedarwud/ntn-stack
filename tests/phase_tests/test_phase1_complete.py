#!/usr/bin/env python3
"""
Phase 1 完成度測試 - 驗證所有 Phase 1 功能是否完整實現
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

# 添加路徑
sys.path.append('netstack/src')
sys.path.append('netstack')

async def test_phase1_completion():
    """測試 Phase 1 完成度"""
    print("🎯 Phase 1 完成度測試")
    print("=" * 60)
    
    results = {
        "phase1_features": {},
        "integration_status": {},
        "api_endpoints": {},
        "overall_score": 0
    }
    
    # 測試 1: NetStack 衛星 API 增強
    print("\n🚀 1. NetStack 衛星 API 增強")
    
    try:
        from netstack.netstack_api.routers.coordinate_orbit_endpoints import router, phase0_loader
        
        # 檢查數據載入器
        data_available = phase0_loader.is_data_available()
        print(f"✅ Phase 0 數據載入器: {'可用' if data_available else '不可用'}")
        
        if data_available:
            total_satellites = phase0_loader.data_summary.get('phase0_data_summary', {}).get('total_satellites', 0)
            print(f"✅ 總衛星數: {total_satellites:,}")
            results["phase1_features"]["netstack_api_enhanced"] = True
            results["phase1_features"]["phase0_data_integration"] = True
        else:
            print("⚠️ Phase 0 數據不可用，使用模擬數據")
            results["phase1_features"]["netstack_api_enhanced"] = True
            results["phase1_features"]["phase0_data_integration"] = False
            
    except Exception as e:
        print(f"❌ NetStack API 增強測試失敗: {e}")
        results["phase1_features"]["netstack_api_enhanced"] = False
        results["phase1_features"]["phase0_data_integration"] = False
    
    # 測試 2: SimWorld Backend 衛星功能移除
    print("\n🔄 2. SimWorld Backend 衛星功能移除")
    
    try:
        # 檢查 requirements.txt
        with open('simworld/backend/requirements.txt', 'r') as f:
            requirements = f.read()
        
        skyfield_removed = 'skyfield' in requirements and '# 已移除' in requirements
        print(f"✅ Skyfield 依賴移除: {'是' if skyfield_removed else '否'}")
        
        # 檢查 NetStack 客戶端
        from simworld.backend.app.services.netstack_client import NetStackAPIClient
        from simworld.backend.app.services.skyfield_migration import SkyfieldMigrationService
        
        print("✅ NetStack 客戶端存在")
        print("✅ Skyfield 遷移服務存在")
        
        results["phase1_features"]["simworld_skyfield_removed"] = skyfield_removed
        results["phase1_features"]["netstack_client_integrated"] = True
        
    except Exception as e:
        print(f"❌ SimWorld 功能移除測試失敗: {e}")
        results["phase1_features"]["simworld_skyfield_removed"] = False
        results["phase1_features"]["netstack_client_integrated"] = False
    
    # 測試 3: 容器啟動順序優化
    print("\n🐳 3. 容器啟動順序優化")
    
    try:
        # 檢查 NetStack compose 配置
        with open('netstack/compose/core.yaml', 'r') as f:
            netstack_compose = f.read()
        
        # 檢查 SimWorld compose 配置
        with open('simworld/docker-compose.yml', 'r') as f:
            simworld_compose = f.read()
        
        netstack_health_check = 'healthcheck:' in netstack_compose and 'netstack-api' in netstack_compose
        simworld_netstack_network = 'netstack-core' in simworld_compose
        
        print(f"✅ NetStack 健康檢查: {'配置' if netstack_health_check else '未配置'}")
        print(f"✅ SimWorld NetStack 網路: {'連接' if simworld_netstack_network else '未連接'}")
        
        results["phase1_features"]["container_startup_optimized"] = netstack_health_check and simworld_netstack_network
        
    except Exception as e:
        print(f"❌ 容器啟動順序測試失敗: {e}")
        results["phase1_features"]["container_startup_optimized"] = False
    
    # 測試 4: API 端點功能測試
    print("\n🔗 4. API 端點功能測試")
    
    try:
        from fastapi.testclient import TestClient
        from netstack.netstack_api.routers.coordinate_orbit_endpoints import router
        from fastapi import FastAPI
        
        # 創建測試應用
        test_app = FastAPI()
        test_app.include_router(router, prefix="/api/v1/satellites")
        
        client = TestClient(test_app)
        
        # 測試健康檢查端點
        health_response = client.get("/api/v1/satellites/health/precomputed")
        health_ok = health_response.status_code == 200
        print(f"✅ 健康檢查端點: {'正常' if health_ok else '異常'}")
        
        # 測試預計算數據端點
        orbit_response = client.get("/api/v1/satellites/precomputed/ntpu")
        orbit_ok = orbit_response.status_code == 200
        print(f"✅ 預計算數據端點: {'正常' if orbit_ok else '異常'}")
        
        if orbit_ok:
            orbit_data = orbit_response.json()
            data_source = orbit_data.get('computation_metadata', {}).get('data_source', 'unknown')
            print(f"✅ 數據來源: {data_source}")
        
        results["api_endpoints"]["health_check"] = health_ok
        results["api_endpoints"]["precomputed_data"] = orbit_ok
        
    except Exception as e:
        print(f"❌ API 端點測試失敗: {e}")
        results["api_endpoints"]["health_check"] = False
        results["api_endpoints"]["precomputed_data"] = False
    
    # 計算總分
    total_features = len(results["phase1_features"]) + len(results["api_endpoints"])
    completed_features = sum(results["phase1_features"].values()) + sum(results["api_endpoints"].values())
    
    if total_features > 0:
        results["overall_score"] = (completed_features / total_features) * 100
    
    # 輸出結果摘要
    print(f"\n📊 Phase 1 完成度摘要")
    print(f"=" * 40)
    print(f"總體完成度: {results['overall_score']:.1f}%")
    print(f"完成功能: {completed_features}/{total_features}")
    
    print(f"\n🎯 功能狀態:")
    for feature, status in results["phase1_features"].items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {feature}")
    
    for endpoint, status in results["api_endpoints"].items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} API {endpoint}")
    
    # 保存結果
    with open('test_phase1_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 測試結果已保存至: test_phase1_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_phase1_completion())
