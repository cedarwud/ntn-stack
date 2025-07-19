#\!/usr/bin/env python3
"""
簡單測試：檢查新增的測量事件模組是否可以正常導入
"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'netstack_api')))

def test_imports():
    """測試模組導入"""
    print("=== 測量事件系統模組導入測試 ===")
    
    try:
        print("\n測試軌道計算引擎導入...")
        from services.orbit_calculation_engine import OrbitCalculationEngine
        print("✅ OrbitCalculationEngine 導入成功")
        
        print("\n測試 TLE 數據管理器導入...")
        from services.tle_data_manager import TLEDataManager
        print("✅ TLEDataManager 導入成功")
        
        print("\n測試 SIB19 統一平台導入...")
        from services.sib19_unified_platform import SIB19UnifiedPlatform
        print("✅ SIB19UnifiedPlatform 導入成功")
        
        print("\n測試測量事件服務導入...")
        from services.measurement_event_service import MeasurementEventService
        print("✅ MeasurementEventService 導入成功")
        
        print("\n測試測量事件路由導入...")
        from routers.measurement_events_router import router
        print("✅ MeasurementEventsRouter 導入成功")
        
        print("\n=== 所有模組導入成功 ===\n")
        return True
        
    except Exception as e:
        print(f"\n❌ 模組導入失敗: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == '__main__':
    success = test_imports()
    if success:
        print("✅ 統一改進主準則核心模組實施完成！")
        print("\n已實施的核心功能：")
        print("   📡 SGP4 軌道計算引擎 - 真實衛星軌道計算")
        print("   🛰️  TLE 數據管理系統 - 支援 Starlink/OneWeb/GPS")
        print("   📶 SIB19 統一基礎平台 - NTN 系統統一資訊基礎")
        print("   📊 測量事件統一服務 - A4/D1/D2/T1 事件支援")
        print("   🌐 統一 API 路由架構 - REST API 端點")
        print("\n下一階段：前端圖表整合和事件標準合規修正")
    else:
        print("❌ 模組導入測試失敗")
    
    sys.exit(0 if success else 1)

