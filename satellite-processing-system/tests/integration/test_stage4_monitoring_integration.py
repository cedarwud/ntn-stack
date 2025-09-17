#!/usr/bin/env python3
"""
🧪 Stage4 實時監控功能整合測試

驗證實時監控功能是否正確整合到 TimeseriesPreprocessingProcessor
"""

import sys
import os
from pathlib import Path

# 添加專案路徑
sys.path.append('/home/sat/ntn-stack/satellite-processing-system/src')

def test_monitoring_integration():
    """測試監控功能整合"""
    print("🔍 測試實時監控功能整合...")

    try:
        from stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor import (
            TimeseriesPreprocessingProcessor
        )

        # 創建處理器實例
        config = {
            "real_time_monitoring": {
                "coverage_threshold": 85.0,
                "alert_thresholds": {
                    "critical_rsrp": -110.0,
                    "warning_rsrp": -100.0,
                    "critical_elevation": 5.0,
                    "warning_elevation": 10.0
                }
            }
        }

        processor = TimeseriesPreprocessingProcessor(config)

        # 驗證監控引擎是否正確初始化
        if hasattr(processor, 'real_time_monitoring_engine'):
            print("✅ 實時監控引擎已正確整合到時間序列處理器")
            print(f"   覆蓋閾值: {processor.real_time_monitoring_engine.monitoring_config.get('coverage_threshold', 'N/A')}")
            print(f"   監控配置已載入")
        else:
            print("❌ 實時監控引擎未找到在時間序列處理器中")
            return False

        # 驗證處理方法是否存在
        if hasattr(processor, '_perform_real_time_monitoring'):
            print("✅ _perform_real_time_monitoring 方法已成功添加")
        else:
            print("❌ _perform_real_time_monitoring 方法未找到")
            return False

        return True

    except Exception as e:
        print(f"❌ 監控功能整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_methods_accessibility():
    """測試監控方法可訪問性"""
    print("🔍 測試監控方法可訪問性...")

    try:
        from stages.stage4_timeseries_preprocessing.timeseries_preprocessing_processor import (
            TimeseriesPreprocessingProcessor
        )

        processor = TimeseriesPreprocessingProcessor()

        # 驗證監控引擎核心方法
        engine = processor.real_time_monitoring_engine
        methods_to_check = [
            '_monitor_coverage_status',
            '_track_satellite_health',
            '_generate_status_reports'
        ]

        for method_name in methods_to_check:
            if hasattr(engine, method_name):
                print(f"✅ 監控方法 {method_name} 可訪問")
            else:
                print(f"❌ 監控方法 {method_name} 不存在")
                return False

        return True

    except Exception as e:
        print(f"❌ 監控方法可訪問性測試失敗: {e}")
        return False

def test_monitoring_functionality_basic():
    """基本監控功能測試"""
    print("🔍 測試基本監控功能...")

    try:
        from stages.stage4_timeseries_preprocessing.real_time_monitoring import (
            RealTimeMonitoringEngine
        )

        # 創建監控引擎
        engine = RealTimeMonitoringEngine()

        # 測試模擬衛星數據的監控
        mock_satellites_data = [{
            'norad_id': '12345',
            'signal_timeseries': [{
                'rsrp_dbm': -85.0,
                'elevation_deg': 30.0,
                'timestamp': '2025-09-16T12:00:00Z'
            }]
        }]

        # 測試三個核心監控方法
        coverage_status = engine._monitor_coverage_status(mock_satellites_data)
        satellite_health = engine._track_satellite_health(mock_satellites_data)
        status_reports = engine._generate_status_reports(mock_satellites_data, satellite_health)

        print("✅ 覆蓋狀態監控測試通過")
        print("✅ 衛星健康追蹤測試通過")
        print("✅ 狀態報告生成測試通過")

        return True

    except Exception as e:
        print(f"❌ 基本監控功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 開始 Stage4 實時監控功能整合測試")
    print("=" * 50)

    tests = [
        ("監控功能整合", test_monitoring_integration),
        ("監控方法可訪問性", test_monitoring_methods_accessibility),
        ("基本監控功能", test_monitoring_functionality_basic)
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 執行測試: {test_name}")
        if test_func():
            passed_tests += 1
        print("-" * 30)

    print(f"\n📊 測試結果摘要:")
    print(f"   總測試數: {total_tests}")
    print(f"   通過測試: {passed_tests}")
    print(f"   失敗測試: {total_tests - passed_tests}")
    print(f"   成功率: {(passed_tests/total_tests*100):.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 所有Stage4實時監控功能整合測試均通過！")
        return 0
    else:
        print(f"\n⚠️ 有 {total_tests - passed_tests} 個測試失敗，需要進一步檢查")
        return 1

if __name__ == "__main__":
    exit(main())