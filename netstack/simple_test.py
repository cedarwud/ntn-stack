#!/usr/bin/env python3
"""
簡單的 Phase 0 測試 - 檢查模組是否可以正常導入和基本功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 確保正確的 Python 路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

print(f"當前目錄: {current_dir}")
print(f"Python 路徑: {sys.path}")

# 測試導入
try:
    print("1. 測試 skyfield 導入...")
    from skyfield.api import load, EarthSatellite
    print("✅ skyfield 導入成功")
    
    print("2. 測試 aiohttp 導入...")
    import aiohttp
    print("✅ aiohttp 導入成功")
    
    print("3. 測試 aiofiles 導入...")
    import aiofiles
    print("✅ aiofiles 導入成功")
    
    print("4. 測試 TLE 下載器導入...")
    from src.services.satellite.starlink_tle_downloader import StarlinkTLEDownloader
    print("✅ TLE 下載器導入成功")
    
    print("5. 測試預篩選器導入...")
    from src.services.satellite.satellite_prefilter import SatellitePrefilter, ObserverLocation
    print("✅ 預篩選器導入成功")
    
    print("6. 測試創建實例...")
    downloader = StarlinkTLEDownloader()
    prefilter = SatellitePrefilter()
    observer = ObserverLocation(24.9441667, 121.3713889)
    print("✅ 實例創建成功")
    
    print("\n🎉 所有模組測試通過！")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 簡單的功能測試
async def simple_functional_test():
    """簡單的功能測試"""
    print("\n=== 簡單功能測試 ===")
    
    try:
        # 測試 TLE 下載器
        print("測試 TLE 下載器...")
        downloader = StarlinkTLEDownloader(cache_dir="simple_test_cache")
        
        # 嘗試下載少量數據進行測試（使用小的超時時間）
        satellites = await downloader.get_starlink_tle_data()
        
        if satellites and len(satellites) > 0:
            print(f"✅ 成功獲取 {len(satellites)} 顆衛星數據")
            
            # 測試預篩選器
            print("測試預篩選器...")
            prefilter = SatellitePrefilter()
            observer = ObserverLocation(24.9441667, 121.3713889)
            
            # 只使用前10顆衛星測試
            test_satellites = satellites[:10]
            candidates, excluded = prefilter.pre_filter_satellites_by_orbit(observer, test_satellites)
            
            print(f"✅ 預篩選完成: {len(candidates)} 候選衛星, {len(excluded)} 排除衛星")
            
            print("\n🎉 簡單功能測試通過！")
            return True
        else:
            print("❌ 未獲取到衛星數據")
            return False
            
    except Exception as e:
        print(f"❌ 功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 運行功能測試
    success = asyncio.run(simple_functional_test())
    
    if success:
        print("\n✅ Phase 0 基本功能驗證通過！")
    else:
        print("\n❌ Phase 0 基本功能驗證失敗！")
        sys.exit(1)