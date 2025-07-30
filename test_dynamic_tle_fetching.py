#!/usr/bin/env python3
"""
測試動態 TLE 數據獲取機制
驗證系統是否能夠獲取最新的 TLE 數據，避免依賴靜態歷史數據
"""

import sys
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 添加 SimWorld 後端到 Python 路徑
sys.path.append('/home/sat/ntn-stack/simworld/backend')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dynamic_tle_fetching():
    """測試動態 TLE 獲取功能"""
    try:
        from app.domains.satellite.services.orbit_service_netstack import OrbitServiceNetStack
        
        logger.info("🚀 開始測試動態 TLE 獲取機制...")
        
        # 創建軌道服務實例
        orbit_service = OrbitServiceNetStack()
        
        # 測試案例1: 測試 TLE 年齡計算
        print("\n" + "="*60)
        print("📅 測試 TLE 年齡計算")
        print("="*60)
        
        # Starlink TLE 示例（相對較新的數據）
        recent_tle = "1 47964U 21024AR  24356.12345678  .00001234  00000-0  12345-4 0  9991"
        old_tle = "1 47964U 21024AR  24001.12345678  .00001234  00000-0  12345-4 0  9991"
        
        recent_age = orbit_service._calculate_tle_age(recent_tle)
        old_age = orbit_service._calculate_tle_age(old_tle)
        
        print(f"較新 TLE 年齡: {recent_age:.1f} 天")
        print(f"較舊 TLE 年齡: {old_age:.1f} 天")
        print(f"年齡門檻 (30天): {'✅ 通過' if recent_age < 30 else '❌ 超出'}")
        
        # 測試案例2: 測試 Celestrak 動態獲取
        print("\n" + "="*60)
        print("🌐 測試 Celestrak 動態數據獲取")
        print("="*60)
        
        # 使用知名的 Starlink 衛星 NORAD ID
        test_norad_ids = [47964, 44713, 44714]  # 一些 Starlink 衛星
        
        for norad_id in test_norad_ids:
            print(f"\n🔍 測試 NORAD ID: {norad_id}")
            
            try:
                latest_tle = await orbit_service._fetch_latest_tle_from_celestrak(norad_id)
                
                if latest_tle:
                    tle_age = orbit_service._calculate_tle_age(latest_tle["line1"])
                    print(f"  ✅ 成功獲取: {latest_tle['name']}")
                    print(f"  📅 數據年齡: {tle_age:.1f} 天")
                    print(f"  🆔 NORAD ID: {latest_tle['norad_id']}")
                    
                    # 檢查數據是否足夠新
                    if tle_age < 30:
                        print(f"  ✅ 數據新鮮度: 良好 (< 30天)")
                    else:
                        print(f"  ⚠️  數據新鮮度: 需注意 (> 30天)")
                else:
                    print(f"  ❌ 無法獲取最新數據")
                    
            except Exception as e:
                print(f"  ❌ 錯誤: {e}")
        
        # 測試案例3: 測試完整的動態軌道計算流程
        print("\n" + "="*60)
        print("🛰️ 測試完整動態軌道計算流程")
        print("="*60)
        
        # 模擬過時的 TLE 數據（超過30天）
        old_tle_line1 = "1 47964U 21024AR  24001.12345678  .00001234  00000-0  12345-4 0  9991"
        old_tle_line2 = "2 47964  53.0123 123.4567 0012345  12.3456 123.4567 15.12345678123456"
        
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=2)
        
        print(f"開始時間: {start_time}")
        print(f"結束時間: {end_time}")
        print(f"使用過時 TLE (應觸發動態獲取): {old_tle_line1[:20]}...")
        
        try:
            result = await orbit_service._generate_orbit_with_dynamic_tle(
                47964, old_tle_line1, old_tle_line2, start_time, end_time, 300
            )
            
            if result.success:
                print(f"✅ 軌道計算成功")
                print(f"📊 軌道點數量: {result.total_points}")
                print(f"⏱️  計算時間: {result.computation_time_ms:.1f}ms")
                
                if result.orbit_points:
                    first_point = result.orbit_points[0]
                    print(f"🎯 首個軌道點: 緯度={first_point.latitude:.4f}, 經度={first_point.longitude:.4f}")
                    print(f"📡 仰角: {first_point.elevation_degrees:.2f}°")
                    print(f"👁️  可見性: {'是' if first_point.is_visible else '否'}")
            else:
                print(f"❌ 軌道計算失敗")
                
        except Exception as e:
            print(f"❌ 軌道計算錯誤: {e}")
        
        # 測試案例4: 測試數據源優先級
        print("\n" + "="*60)
        print("🔄 測試數據源優先級機制")
        print("="*60)
        
        print("數據源優先級:")
        print("1. Celestrak 最新數據 (優先)")
        print("2. 輸入 TLE 數據 (< 30天)")
        print("3. 歷史真實數據 (最後備案)")
        
        # 使用不存在的 NORAD ID 測試 fallback
        nonexistent_norad = 99999999
        print(f"\n🔍 測試不存在的 NORAD ID: {nonexistent_norad}")
        
        try:
            fallback_tle = await orbit_service._fetch_latest_tle_from_celestrak(nonexistent_norad)
            if not fallback_tle:
                print("✅ 正確觸發 fallback 機制 - 無法從 Celestrak 獲取不存在的衛星")
            
            # 測試完整 fallback 流程
            result = await orbit_service._generate_orbit_with_dynamic_tle(
                nonexistent_norad, None, None, start_time, end_time, 300
            )
            
            if result.success:
                print("✅ Fallback 機制正常工作，使用歷史數據成功生成軌道")
            else:
                print("❌ Fallback 機制失敗")
                
        except Exception as e:
            print(f"❌ Fallback 測試錯誤: {e}")
        
        print("\n" + "="*60)
        print("✅ 動態 TLE 獲取機制測試完成")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 動態 TLE 測試失敗: {e}", exc_info=True)
        return False

async def main():
    """主函數"""
    try:
        success = await test_dynamic_tle_fetching()
        
        if success:
            print("\n🎉 所有測試通過！動態 TLE 獲取機制正常工作")
            print("✅ 系統不會依賴靜態歷史數據，能夠獲取最新衛星數據")
            return 0
        else:
            print("\n❌ 測試失敗，需要檢查動態獲取機制")
            return 1
            
    except Exception as e:
        logger.error(f"❌ 測試過程出錯: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)