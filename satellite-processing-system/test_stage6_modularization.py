#!/usr/bin/env python3
"""
Stage 6 模組化驗證測試腳本

驗證重構後的Stage 6模組能否正常工作:
1. 共享核心模組導入測試
2. 專業化模組初始化測試
3. 主處理器協調功能測試
4. 整合工作流程驗證

執行方式:
    cd /home/sat/ntn-stack/satellite-processing-system
    python test_stage6_modularization.py
"""

import sys
import os
from pathlib import Path

# 添加 src 目錄到 Python 路徑
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_tle_checksum(tle_line):
    """計算TLE行的校驗和"""
    if len(tle_line) != 69:
        return None

    checksum = 0
    for char in tle_line[:-1]:  # 排除最後一位校驗和
        if char.isdigit():
            checksum += int(char)
        elif char == '-':
            checksum += 1

    return checksum % 10

def fix_tle_checksum(tle_line):
    """修復TLE行的校驗和"""
    if len(tle_line) != 69:
        return tle_line

    correct_checksum = calculate_tle_checksum(tle_line)
    return tle_line[:-1] + str(correct_checksum)

def test_shared_core_modules():
    """測試共享核心模組導入"""
    logger.info("🔍 測試 1: 共享核心模組導入測試")

    try:
        from shared.core_modules import (
            OrbitalCalculationsCore,
            VisibilityCalculationsCore,
            SignalCalculationsCore
        )

        # 測試實例化
        observer_coords = (25.0, 121.0, 100.0)
        orbital_calc = OrbitalCalculationsCore(observer_coords)
        visibility_calc = VisibilityCalculationsCore(observer_coords)
        signal_calc = SignalCalculationsCore()

        logger.info("✅ 共享核心模組導入和實例化成功")
        return True

    except Exception as e:
        logger.error(f"❌ 共享核心模組測試失敗: {str(e)}")
        return False

def test_specialized_modules():
    """測試專業化模組導入和初始化"""
    logger.info("🔍 測試 2: 專業化模組導入測試")

    try:
        from stages.stage6_dynamic_pool_planning.dynamic_pool_strategy_engine import DynamicPoolStrategyEngine
        from stages.stage6_dynamic_pool_planning.coverage_optimization_engine import CoverageOptimizationEngine
        from stages.stage6_dynamic_pool_planning.backup_satellite_manager import BackupSatelliteManager
        from stages.stage6_dynamic_pool_planning.pool_planning_utilities import PoolPlanningUtilities

        # 測試配置
        test_config = {
            'observer': {
                'latitude': 25.0,
                'longitude': 121.0,
                'elevation_m': 100.0
            }
        }

        # 測試實例化
        strategy_engine = DynamicPoolStrategyEngine(test_config)
        optimization_engine = CoverageOptimizationEngine(test_config)
        backup_manager = BackupSatelliteManager(test_config)
        utilities = PoolPlanningUtilities(test_config)

        logger.info("✅ 專業化模組導入和實例化成功")
        logger.info(f"   - 策略引擎: {type(strategy_engine).__name__}")
        logger.info(f"   - 優化引擎: {type(optimization_engine).__name__}")
        logger.info(f"   - 備份管理器: {type(backup_manager).__name__}")
        logger.info(f"   - 工具模組: {type(utilities).__name__}")

        return True

    except Exception as e:
        logger.error(f"❌ 專業化模組測試失敗: {str(e)}")
        return False

def test_main_processor():
    """測試主處理器初始化"""
    logger.info("🔍 測試 3: 主處理器初始化測試")

    try:
        from stages.stage6_dynamic_pool_planning.temporal_spatial_analysis_engine import TemporalSpatialAnalysisEngine

        # 測試配置
        test_config = {
            'observer_lat': 24.9441667,
            'observer_lon': 121.3713889,
            'observer_elevation_m': 100.0
        }

        # 創建主處理器實例
        engine = TemporalSpatialAnalysisEngine(test_config)

        logger.info("✅ 主處理器初始化成功")
        logger.info(f"   - 觀測點: ({engine.observer_lat:.4f}°N, {engine.observer_lon:.4f}°E)")
        logger.info(f"   - 模組數量: 4個專業化模組 + 3個共享核心模組")

        return engine

    except Exception as e:
        logger.error(f"❌ 主處理器測試失敗: {str(e)}")
        return None

def test_data_validation():
    """測試數據驗證功能"""
    logger.info("🔍 測試 4: 數據驗證功能測試")

    try:
        from stages.stage6_dynamic_pool_planning.pool_planning_utilities import PoolPlanningUtilities

        utilities = PoolPlanningUtilities()

        # 創建測試衛星數據 (使用正確的TLE校驗和)
        test_satellites = [
            {
                'satellite_id': 'TEST-001',
                'constellation': 'test',
                'tle_line1': '1 12345U 24001A   25261.50000000  .00000000  00000-0  00000-0 0  9993',
                'tle_line2': '2 12345  53.0000 120.0000 0000000  90.0000 270.0000 15.50000000000007',
                'elevation_deg': 45.0,
                'azimuth_deg': 180.0,
                'distance_km': 800.0
            }
        ]

        # 執行驗證
        validation_result = utilities.validate_satellite_data(test_satellites)

        logger.info("✅ 數據驗證功能測試完成")
        logger.info(f"   - 驗證結果: {'成功' if validation_result.is_valid else '失敗'}")
        logger.info(f"   - 錯誤數量: {len(validation_result.errors)}")
        logger.info(f"   - 警告數量: {len(validation_result.warnings)}")

        return validation_result.is_valid

    except Exception as e:
        logger.error(f"❌ 數據驗證測試失敗: {str(e)}")
        return False

def test_integration_workflow():
    """測試整合工作流程"""
    logger.info("🔍 測試 5: 整合工作流程測試")

    try:
        from stages.stage6_dynamic_pool_planning.temporal_spatial_analysis_engine import TemporalSpatialAnalysisEngine

        # 創建引擎實例
        engine = TemporalSpatialAnalysisEngine()

        # 創建測試候選衛星數據 (動態修復TLE校驗和)
        test_candidates = []
        for i in range(20):  # 20顆測試衛星
            # 生成原始TLE行
            tle_line1_raw = f'1 {12345+i:05d}U 24001A   25261.50000000  .00000000  00000-0  00000-0 0  999{i%10}'
            tle_line2_raw = f'2 {12345+i:05d}  53.0000 {120.0+i*10:.4f} 0000000  90.0000 270.0000 15.50000000000009'

            # 修復校驗和
            tle_line1_fixed = fix_tle_checksum(tle_line1_raw)
            tle_line2_fixed = fix_tle_checksum(tle_line2_raw)

            test_candidates.append({
                'satellite_id': f'TEST-{i:03d}',
                'constellation': 'starlink' if i % 2 == 0 else 'oneweb',
                'tle_line1': tle_line1_fixed,
                'tle_line2': tle_line2_fixed,
                'elevation_deg': 10.0 + (i % 80),
                'azimuth_deg': i * 36 % 360,
                'distance_km': 600.0 + (i % 400),
                'rsrp_dbm': -85.0 - (i % 20)
            })

        logger.info(f"   - 準備測試: {len(test_candidates)} 顆候選衛星")

        # 執行完整分析流程
        results = engine.execute_advanced_temporal_spatial_analysis(test_candidates)

        # 驗證結果結構
        required_keys = [
            'analysis_type', 'timestamp', 'input_satellites', 'valid_satellites',
            'selected_satellites', 'backup_satellites', 'performance_metrics'
        ]

        missing_keys = [key for key in required_keys if key not in results]

        if missing_keys:
            logger.warning(f"⚠️  結果缺少必要欄位: {missing_keys}")

        logger.info("✅ 整合工作流程測試完成")
        logger.info(f"   - 分析類型: {results.get('analysis_type', 'N/A')}")
        logger.info(f"   - 輸入衛星: {results.get('input_satellites', 0)} 顆")
        logger.info(f"   - 有效衛星: {results.get('valid_satellites', 0)} 顆")
        logger.info(f"   - 選中衛星: {len(results.get('selected_satellites', []))} 顆")
        logger.info(f"   - 備份衛星: {len(results.get('backup_satellites', []))} 顆")

        if 'performance_metrics' in results:
            perf = results['performance_metrics']
            logger.info(f"   - 處理時間: {perf.get('processing_time_ms', 0):.2f} ms")
            logger.info(f"   - 覆蓋率: {perf.get('coverage_percentage', 0):.1f}%")
            logger.info(f"   - 質量分數: {perf.get('quality_score', 0):.1f}/100")

        return len(missing_keys) == 0

    except Exception as e:
        logger.error(f"❌ 整合工作流程測試失敗: {str(e)}")
        return False

def main():
    """主測試函數"""
    logger.info("🚀 開始 Stage 6 模組化驗證測試")
    logger.info("=" * 60)

    test_results = []

    # 執行所有測試
    test_results.append(("共享核心模組", test_shared_core_modules()))
    test_results.append(("專業化模組", test_specialized_modules()))

    # 主處理器測試 (返回實例或None)
    main_processor = test_main_processor()
    test_results.append(("主處理器初始化", main_processor is not None))

    test_results.append(("數據驗證功能", test_data_validation()))
    test_results.append(("整合工作流程", test_integration_workflow()))

    # 輸出測試總結
    logger.info("=" * 60)
    logger.info("📊 測試結果總結:")

    passed_tests = 0
    total_tests = len(test_results)

    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed_tests += 1

    logger.info("-" * 40)
    logger.info(f"總體結果: {passed_tests}/{total_tests} 測試通過 ({passed_tests/total_tests*100:.1f}%)")

    if passed_tests == total_tests:
        logger.info("🎉 Stage 6 模組化驗證: 全部測試通過!")
        logger.info("✅ 模組化重構成功，可以進入下一階段開發")
        return 0
    else:
        logger.error("❌ Stage 6 模組化驗證: 存在失敗測試")
        logger.error("🔧 請檢查並修復失敗的模組")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)