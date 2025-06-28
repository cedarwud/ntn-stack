#!/usr/bin/env python3
"""
測試 SystemMonitoringService 的基本功能
"""

import asyncio
import sys
import os

# 添加項目根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domains.handover.services.monitoring.system_monitoring_service import SystemMonitoringService


class MockOrbitService:
    """模擬的 OrbitService 用於測試"""
    
    def __init__(self):
        self._satellite_repository = MockSatelliteRepository()


class MockSatelliteRepository:
    """模擬的衛星儲存庫"""
    
    async def get_satellites(self):
        """返回模擬的衛星數據"""
        return [{"id": i, "name": f"sat_{i}"} for i in range(2000)]  # 模擬2000顆衛星


async def test_system_monitoring_service():
    """測試系統監控服務的各項功能"""
    
    # 創建模擬的軌道服務
    mock_orbit_service = MockOrbitService()
    
    # 創建系統監控服務實例
    monitoring_service = SystemMonitoringService(mock_orbit_service)
    
    print("🚀 開始測試 SystemMonitoringService")
    print("=" * 60)
    
    # 測試 1: 系統資源分配分析
    print("📊 測試 1: 系統資源分配分析")
    try:
        result = await monitoring_service.calculate_system_resource_allocation(
            measurement_duration_minutes=30
        )
        print(f"✅ 系統資源分配分析成功，包含 {len(result['components_data'])} 個組件")
        print(f"   系統負載等級: {result['resource_summary']['system_load_level']}")
    except Exception as e:
        print(f"❌ 系統資源分配分析失敗: {e}")
    
    # 測試 2: 時間同步精度分析
    print("\n⏱️ 測試 2: 時間同步精度分析")
    try:
        result = await monitoring_service.calculate_time_sync_precision(
            measurement_duration_seconds=300
        )
        print(f"✅ 時間同步精度分析成功，整體精度: {result['overall_precision_ns']} ns")
        print(f"   同步狀態: {result['sync_status']}")
    except Exception as e:
        print(f"❌ 時間同步精度分析失敗: {e}")
    
    # 測試 3: 性能雷達分析
    print("\n🎯 測試 3: 性能雷達分析")
    try:
        result = await monitoring_service.calculate_performance_radar()
        print(f"✅ 性能雷達分析成功，總體評分: {result['overall_score']}")
        print(f"   性能等級: {result['performance_level']}")
    except Exception as e:
        print(f"❌ 性能雷達分析失敗: {e}")
    
    # 測試 4: 異常處理統計
    print("\n⚠️ 測試 4: 異常處理統計")
    try:
        result = await monitoring_service.calculate_exception_handling_statistics(
            analysis_duration_hours=24
        )
        print(f"✅ 異常處理統計成功，總異常數: {result['total_exceptions']}")
        print(f"   系統穩定性評分: {result['system_stability_score']}")
    except Exception as e:
        print(f"❌ 異常處理統計失敗: {e}")
    
    # 測試 5: QoE 時間序列分析
    print("\n📈 測試 5: QoE 時間序列分析")
    try:
        result = await monitoring_service.calculate_qoe_timeseries(
            measurement_duration_seconds=60,
            sample_interval_seconds=1
        )
        print(f"✅ QoE 時間序列分析成功，整體評分: {result['overall_qoe_score']}")
        print(f"   用戶體驗等級: {result['user_experience_level']}")
    except Exception as e:
        print(f"❌ QoE 時間序列分析失敗: {e}")
    
    # 測試 6: 全球覆蓋率統計
    print("\n🌍 測試 6: 全球覆蓋率統計")
    try:
        result = await monitoring_service.calculate_global_coverage()
        print(f"✅ 全球覆蓋率統計成功，最優星座: {result['optimal_constellation']}")
        print(f"   星座數量: {len(result['constellations_data'])}")
    except Exception as e:
        print(f"❌ 全球覆蓋率統計失敗: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 所有測試完成！")


if __name__ == "__main__":
    asyncio.run(test_system_monitoring_service())