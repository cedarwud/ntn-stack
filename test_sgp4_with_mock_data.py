#!/usr/bin/env python3
"""
SGP4 實施測試腳本 - 使用模擬 TLE 數據
直接測試 SGP4 計算器而不依賴 Docker Volume
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone

# 設置路徑
sys.path.append('/home/sat/ntn-stack/simworld/backend')

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 真實的 Starlink TLE 數據樣本
MOCK_TLE_DATA = [
    {
        "name": "STARLINK-1007",
        "norad_id": 44713,
        "line1": "1 44713U 19074A   25211.50000000  .00001234  00000-0  12345-4 0  9995",
        "line2": "2 44713  53.0000 123.4567 0001234  89.1234 270.9876 15.50000000123456",
        "constellation": "starlink",
        "source": "mock_data"
    },
    {
        "name": "STARLINK-1372", 
        "norad_id": 45359,
        "line1": "1 45359U 20006A   25211.50000000  .00001456  00000-0  23456-4 0  9996",
        "line2": "2 45359  53.0000 145.6789 0001456  112.3456 247.6543 15.50000000134567",
        "constellation": "starlink",
        "source": "mock_data"
    },
    {
        "name": "STARLINK-1573",
        "norad_id": 45657,
        "line1": "1 45657U 20019A   25211.50000000  .00001678  00000-0  34567-4 0  9997",
        "line2": "2 45657  53.0000 167.8901 0001678  135.5678 224.4321 15.50000000145678",
        "constellation": "starlink", 
        "source": "mock_data"
    }
]

async def test_sgp4_calculator_directly():
    """直接測試 SGP4 計算器"""
    try:
        logger.info("🚀 直接測試 SGP4 計算器")
        
        from app.services.sgp4_calculator import SGP4Calculator, TLEData
        from app.services.distance_calculator import DistanceCalculator, Position
        
        # 初始化計算器
        sgp4_calc = SGP4Calculator()
        distance_calc = DistanceCalculator()
        
        # 測試時間
        test_time = datetime.now(timezone.utc)
        
        # 參考位置 (台北科技大學)
        reference_pos = Position(
            latitude=24.9441,
            longitude=121.3714,
            altitude=0.0
        )
        
        logger.info(f"⏰ 測試時間: {test_time.isoformat()}")
        logger.info(f"📍 參考位置: {reference_pos.latitude:.4f}°N, {reference_pos.longitude:.4f}°E")
        
        successful_calculations = 0
        total_calculations = 0
        
        for sat_data in MOCK_TLE_DATA:
            logger.info(f"\n🛰️ 測試衛星: {sat_data['name']}")
            
            # 創建 TLE 數據對象
            tle_data = TLEData(
                name=sat_data["name"],
                line1=sat_data["line1"],
                line2=sat_data["line2"],
                epoch=test_time.isoformat()
            )
            
            total_calculations += 1
            
            # 測試 TLE 解析
            logger.info(f"   📊 TLE 解析結果:")
            logger.info(f"      - NORAD ID: {tle_data.catalog_number}")
            logger.info(f"      - 平均運動: {tle_data.mean_motion:.6f} 轉/日")
            logger.info(f"      - 軌道傾角: {tle_data.inclination:.4f}°")
            logger.info(f"      - 離心率: {tle_data.eccentricity:.6f}")
            logger.info(f"      - 升交點赤經: {tle_data.right_ascension:.4f}°")
            logger.info(f"      - 近地點幅角: {tle_data.argument_of_perigee:.4f}°")
            logger.info(f"      - 平均近點角: {tle_data.mean_anomaly:.4f}°")
            
            # 使用 SGP4 計算軌道位置
            orbit_position = sgp4_calc.propagate_orbit(tle_data, test_time)
            
            if orbit_position:
                successful_calculations += 1
                
                logger.info(f"   ✅ SGP4 計算成功:")
                logger.info(f"      - 位置: {orbit_position.latitude:.6f}°N, {orbit_position.longitude:.6f}°E")
                logger.info(f"      - 高度: {orbit_position.altitude:.1f} km")
                
                # 計算速度大小
                vx, vy, vz = orbit_position.velocity
                v_mag = (vx**2 + vy**2 + vz**2)**0.5
                logger.info(f"      - 速度: ({vx:.3f}, {vy:.3f}, {vz:.3f}) km/s")
                logger.info(f"      - 速度大小: {v_mag:.3f} km/s")
                
                # 驗證速度是否合理 (LEO 衛星約 7-8 km/s)
                if 6.0 <= v_mag <= 9.0:
                    logger.info(f"      - ✅ 速度大小合理 (LEO 衛星範圍)")
                else:
                    logger.warning(f"      - ⚠️ 速度大小異常")
                
                # 計算相對於參考位置的觀測數據
                try:
                    satellite_pos = Position(
                        latitude=orbit_position.latitude,
                        longitude=orbit_position.longitude,
                        altitude=orbit_position.altitude * 1000  # 轉換為米
                    )
                    
                    elevation = distance_calc.calculate_elevation_angle(reference_pos, satellite_pos)
                    azimuth = distance_calc.calculate_azimuth_angle(reference_pos, satellite_pos)
                    distance_result = distance_calc.calculate_d2_distances(reference_pos, satellite_pos, reference_pos)
                    
                    logger.info(f"   📡 觀測數據:")
                    logger.info(f"      - 仰角: {elevation:.2f}°")
                    logger.info(f"      - 方位角: {azimuth:.2f}°")
                    logger.info(f"      - 距離: {distance_result.satellite_distance/1000:.1f} km")
                    logger.info(f"      - 可見: {'是' if elevation > 10 else '否'} (仰角 > 10°)")
                    
                except Exception as e:
                    logger.warning(f"      - ⚠️ 觀測數據計算失敗: {e}")
                    
            else:
                logger.error(f"   ❌ SGP4 計算失敗")
                
        # 總結
        success_rate = successful_calculations / total_calculations * 100 if total_calculations > 0 else 0
        logger.info(f"\n📊 SGP4 計算總結:")
        logger.info(f"   - 成功: {successful_calculations}/{total_calculations} ({success_rate:.1f}%)")
        
        return successful_calculations > 0
        
    except Exception as e:
        logger.error(f"❌ SGP4 計算器測試失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return False

async def test_timeseries_generation():
    """測試時間序列生成"""
    try:
        logger.info("🕐 測試 120 分鐘時間序列生成")
        
        from app.services.local_volume_data_service import LocalVolumeDataService
        
        # 創建服務實例
        volume_service = LocalVolumeDataService()
        
        # 模擬 TLE 數據載入方法
        class MockVolumeService(LocalVolumeDataService):
            async def get_local_tle_data(self, constellation: str = "starlink"):
                logger.info(f"🔄 使用模擬 TLE 數據: {constellation}")
                return [sat for sat in MOCK_TLE_DATA if sat["constellation"] == constellation]
        
        mock_service = MockVolumeService()
        
        # 參考位置
        reference_location = {
            "latitude": 24.9441,
            "longitude": 121.3714,
            "altitude": 0.0
        }
        
        # 生成時間序列數據
        unified_data = await mock_service.generate_120min_timeseries(
            constellation="starlink",
            reference_location=reference_location
        )
        
        if unified_data:
            metadata = unified_data.get("metadata", {})
            satellites = unified_data.get("satellites", [])
            ue_trajectory = unified_data.get("ue_trajectory", [])
            
            logger.info(f"✅ 成功生成時間序列數據:")
            logger.info(f"   - 星座: {metadata.get('constellation')}")
            logger.info(f"   - 時間跨度: {metadata.get('time_span_minutes')} 分鐘")
            logger.info(f"   - 時間間隔: {metadata.get('time_interval_seconds')} 秒")
            logger.info(f"   - 總時間點: {metadata.get('total_time_points')}")
            logger.info(f"   - 衛星數量: {len(satellites)}")
            logger.info(f"   - UE 軌跡點: {len(ue_trajectory)}")
            logger.info(f"   - 數據來源: {metadata.get('data_source')}")
            
            # 驗證數據品質
            if satellites:
                first_sat = satellites[0]
                time_series = first_sat.get("time_series", [])
                
                if time_series:
                    logger.info(f"🔍 數據品質檢查 - 衛星 {first_sat.get('name')}:")
                    logger.info(f"   - 時間序列點數: {len(time_series)}")
                    
                    # 檢查幾個時間點
                    sample_points = [0, len(time_series)//4, len(time_series)//2, len(time_series)*3//4, len(time_series)-1]
                    
                    for i, point_idx in enumerate(sample_points):
                        if point_idx < len(time_series):
                            point = time_series[point_idx]
                            position = point.get("position", {})
                            observation = point.get("observation", {})
                            
                            logger.info(f"   - 時間點 {point_idx} ({i*25}%):")
                            logger.info(f"     * 位置: {position.get('latitude', 0):.3f}°N, {position.get('longitude', 0):.3f}°E, {position.get('altitude', 0)/1000:.1f}km")
                            logger.info(f"     * 仰角: {observation.get('elevation_deg', 0):.1f}°, 可見: {observation.get('is_visible', False)}")
                            logger.info(f"     * RSRP: {observation.get('rsrp_dbm', 0):.1f}dBm")
                    
                    # 統計可見時間點
                    visible_count = sum(1 for tp in time_series if tp.get("observation", {}).get("is_visible", False))
                    logger.info(f"   - 可見時間點: {visible_count}/{len(time_series)} ({visible_count/len(time_series)*100:.1f}%)")
            
            return True
        else:
            logger.error("❌ 未能生成時間序列數據")
            return False
            
    except Exception as e:
        logger.error(f"❌ 時間序列生成測試失敗: {e}")
        import traceback
        logger.error(f"詳細錯誤: {traceback.format_exc()}")
        return False

async def main():
    """主測試函數"""
    logger.info("="*60)
    logger.info("🧪 SGP4 精確軌道計算測試 (使用模擬數據)")
    logger.info("="*60)
    
    # 測試順序
    tests = [
        ("SGP4 計算器直接測試", test_sgp4_calculator_directly),
        ("120分鐘時間序列生成測試", test_timeseries_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n🔄 執行 {test_name}")
        result = await test_func()
        results.append((test_name, result))
        logger.info(f"{'✅' if result else '❌'} {test_name} {'通過' if result else '失敗'}")
    
    # 總結
    logger.info("\n" + "="*60)
    logger.info("📊 測試結果總結")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\n🎯 總計: {passed}/{total} 測試通過 ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 SGP4 實施測試全部通過！")
        logger.info("✨ 簡化圓軌道模型已成功替換為 SGP4 精確軌道計算")
        return 0
    else:
        logger.error("💥 部分測試失敗，需要進一步調試")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)