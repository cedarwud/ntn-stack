#!/usr/bin/env python3
"""
測試整合修正 - 驗證 Dockerfile 整合、API 修正和側邊欄整合
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

async def test_integration_fixes():
    """測試整合修正"""
    print("🔧 整合修正驗證測試")
    print("=" * 50)
    
    results = {
        "dockerfile_integration": {},
        "api_fixes": {},
        "sidebar_integration": {},
        "overall_status": "unknown"
    }
    
    # 測試 1: Dockerfile 整合
    print("\n🐳 1. Dockerfile 整合驗證")
    
    try:
        # 檢查原始 Dockerfile 是否包含 Phase 0 功能
        dockerfile_path = Path("netstack/docker/Dockerfile")
        if dockerfile_path.exists():
            with open(dockerfile_path, 'r', encoding='utf-8') as f:
                dockerfile_content = f.read()
            
            phase0_features = {
                "precomputed_data_enabled": "PRECOMPUTED_DATA_ENABLED=true" in dockerfile_content,
                "orbit_cache_preload": "ORBIT_CACHE_PRELOAD=true" in dockerfile_content,
                "build_with_phase0_data": "build_with_phase0_data.py" in dockerfile_content,
                "phase0_build_execution": "python build_with_phase0_data.py" in dockerfile_content,
                "enhanced_health_check": "health/precomputed" in dockerfile_content
            }
            
            for feature, found in phase0_features.items():
                status = "✅" if found else "❌"
                print(f"  {status} {feature}")
                results["dockerfile_integration"][feature] = found
            
            # 檢查 Dockerfile.phase0 是否已刪除
            dockerfile_phase0_path = Path("netstack/docker/Dockerfile.phase0")
            dockerfile_phase0_deleted = not dockerfile_phase0_path.exists()
            print(f"  {'✅' if dockerfile_phase0_deleted else '❌'} Dockerfile.phase0 已刪除")
            results["dockerfile_integration"]["dockerfile_phase0_deleted"] = dockerfile_phase0_deleted
            
        else:
            print("❌ Dockerfile 不存在")
            results["dockerfile_integration"]["dockerfile_exists"] = False
            
    except Exception as e:
        print(f"❌ Dockerfile 整合測試失敗: {e}")
        results["dockerfile_integration"]["error"] = str(e)
    
    # 測試 2: API 修正驗證
    print("\n🔗 2. API 修正驗證")
    
    try:
        # 檢查 simworld-api.ts 中的端點修正
        simworld_api_path = Path("simworld/frontend/src/services/simworld-api.ts")
        if simworld_api_path.exists():
            with open(simworld_api_path, 'r', encoding='utf-8') as f:
                api_content = f.read()
            
            api_fixes = {
                "netstack_precomputed_endpoint": "/api/v1/satellites/precomputed/ntpu" in api_content,
                "removed_old_endpoint": "/api/v1/satellites/visible_satellites" not in api_content or api_content.count("/api/v1/satellites/visible_satellites") == 0,
                "correct_error_endpoint": "/api/v1/satellites/precomputed/ntpu" in api_content and "endpoint:" in api_content
            }
            
            for fix, applied in api_fixes.items():
                status = "✅" if applied else "❌"
                print(f"  {status} {fix}")
                results["api_fixes"][fix] = applied
                
        else:
            print("❌ simworld-api.ts 不存在")
            results["api_fixes"]["file_exists"] = False
            
    except Exception as e:
        print(f"❌ API 修正測試失敗: {e}")
        results["api_fixes"]["error"] = str(e)
    
    # 測試 3: 側邊欄整合驗證
    print("\n📋 3. 側邊欄整合驗證")
    
    try:
        # 檢查 Sidebar.tsx 中的 Phase 2 組件整合
        sidebar_path = Path("simworld/frontend/src/components/layout/Sidebar.tsx")
        if sidebar_path.exists():
            with open(sidebar_path, 'r', encoding='utf-8') as f:
                sidebar_content = f.read()
            
            sidebar_integration = {
                "timeline_controller_import": "import TimelineController from '../common/TimelineController'" in sidebar_content,
                "location_selector_import": "import LocationSelector from '../common/LocationSelector'" in sidebar_content,
                "phase2_props_added": "currentLocation?" in sidebar_content and "timelineIsPlaying?" in sidebar_content,
                "satellite_control_section": "📍 觀測點控制" in sidebar_content and "⏰ 時間軸控制" in sidebar_content,
                "components_in_satellite_tab": "activeCategory === 'satellite'" in sidebar_content and "LocationSelector" in sidebar_content
            }
            
            for integration, found in sidebar_integration.items():
                status = "✅" if found else "❌"
                print(f"  {status} {integration}")
                results["sidebar_integration"][integration] = found
                
        else:
            print("❌ Sidebar.tsx 不存在")
            results["sidebar_integration"]["file_exists"] = False
        
        # 檢查 StereogramView.tsx 中的組件移除
        stereogram_path = Path("simworld/frontend/src/components/scenes/StereogramView.tsx")
        if stereogram_path.exists():
            with open(stereogram_path, 'r', encoding='utf-8') as f:
                stereogram_content = f.read()
            
            stereogram_cleanup = {
                "timeline_controller_removed": "TimelineController" not in stereogram_content or stereogram_content.count("TimelineController") <= 1,
                "location_selector_removed": "LocationSelector" not in stereogram_content or stereogram_content.count("LocationSelector") <= 1,
                "ui_controls_removed": "Phase 2 UI 控制組件已移至側邊欄" in stereogram_content
            }
            
            for cleanup, done in stereogram_cleanup.items():
                status = "✅" if done else "❌"
                print(f"  {status} {cleanup}")
                results["sidebar_integration"][cleanup] = done
                
        else:
            print("❌ StereogramView.tsx 不存在")
            results["sidebar_integration"]["stereogram_exists"] = False
            
    except Exception as e:
        print(f"❌ 側邊欄整合測試失敗: {e}")
        results["sidebar_integration"]["error"] = str(e)
    
    # 測試 4: 狀態管理驗證
    print("\n🔄 4. 狀態管理驗證")
    
    try:
        # 檢查 AppStateContext.tsx 中的 Phase 2 狀態
        app_state_path = Path("simworld/frontend/src/contexts/AppStateContext.tsx")
        if app_state_path.exists():
            with open(app_state_path, 'r', encoding='utf-8') as f:
                app_state_content = f.read()
            
            state_management = {
                "satellite_state_extended": "currentLocation:" in app_state_content and "timelineIsPlaying:" in app_state_content,
                "update_functions_added": "setCurrentLocation" in app_state_content and "setTimelineIsPlaying" in app_state_content,
                "context_interface_updated": "setCurrentLocation:" in app_state_content and "setTimelineSpeed:" in app_state_content,
                "initial_state_configured": "name: 'NTPU'" in app_state_content and "lat: 24.94417" in app_state_content
            }
            
            for state, configured in state_management.items():
                status = "✅" if configured else "❌"
                print(f"  {status} {state}")
                results["sidebar_integration"][state] = configured
                
        else:
            print("❌ AppStateContext.tsx 不存在")
            results["sidebar_integration"]["app_state_exists"] = False
            
    except Exception as e:
        print(f"❌ 狀態管理測試失敗: {e}")
        results["sidebar_integration"]["state_error"] = str(e)
    
    # 計算總體狀態
    all_results = {}
    for category in results.values():
        if isinstance(category, dict):
            all_results.update(category)
    
    total_checks = len([v for v in all_results.values() if isinstance(v, bool)])
    passed_checks = len([v for v in all_results.values() if v is True])
    
    if total_checks > 0:
        success_rate = (passed_checks / total_checks) * 100
        if success_rate >= 90:
            results["overall_status"] = "success"
        elif success_rate >= 70:
            results["overall_status"] = "partial"
        else:
            results["overall_status"] = "failed"
    
    # 輸出結果摘要
    print(f"\n📊 整合修正結果摘要")
    print(f"=" * 30)
    print(f"總體狀態: {results['overall_status']}")
    print(f"通過檢查: {passed_checks}/{total_checks}")
    print(f"成功率: {success_rate:.1f}%")
    
    status_icon = {
        "success": "✅",
        "partial": "⚠️", 
        "failed": "❌",
        "unknown": "❓"
    }.get(results["overall_status"], "❓")
    
    print(f"\n{status_icon} 整合修正狀態: {results['overall_status']}")
    
    if results["overall_status"] == "success":
        print("\n🎉 所有修正已成功完成！")
        print("✅ Dockerfile.phase0 已整合到主 Dockerfile")
        print("✅ API 端點已修正為 NetStack 預計算端點")
        print("✅ 衛星控制組件已整合到側邊欄")
        print("✅ 狀態管理已更新支援 Phase 2 功能")
    elif results["overall_status"] == "partial":
        print("\n⚠️ 部分修正完成，需要檢查失敗項目")
    else:
        print("\n❌ 修正未完成，需要進一步調試")
    
    # 保存結果
    with open('test_integration_fixes_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            **results,
            "test_timestamp": datetime.now().isoformat(),
            "success_rate": success_rate,
            "passed_checks": passed_checks,
            "total_checks": total_checks
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 測試結果已保存至: test_integration_fixes_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_integration_fixes())
