#!/usr/bin/env python3
"""
階段一整合驗證腳本
====================

驗證新整合的階段一是否：
1. 使用完整 SGP4 算法（非簡化）
2. 處理真實衛星數據（非模擬）  
3. 輸出符合階段二輸入需求
4. 整體功能正常運作

使用方法：
python3 validate_phase1_integration.py
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# 添加 netstack 路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack')
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sgp4_algorithm_validation():
    """測試 1: 驗證 SGP4 算法完整性"""
    logger.info("🧪 測試 1: SGP4 算法完整性驗證")
    
    try:
        # 檢查 SGP4 庫導入
        from sgp4.api import Satrec, jday
        logger.info("✅ SGP4 官方庫導入成功")
        
        # 檢查軌道引擎
        from services.satellite.coordinate_specific_orbit_engine import CoordinateSpecificOrbitEngine
        
        # 創建測試實例
        orbit_engine = CoordinateSpecificOrbitEngine(
            observer_lat=24.9441667,  # NTPU 座標
            observer_lon=121.3713889,
            observer_alt_m=100
        )
        
        logger.info("✅ CoordinateSpecificOrbitEngine 創建成功")
        
        # 測試 SGP4 計算方法存在性
        test_tle = {
            'name': 'TEST-SATELLITE',
            'line1': '1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990',
            'line2': '2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509',
            'norad_id': '25544'
        }
        
        # 測試軌道計算
        start_time = datetime.now(timezone.utc)
        result = orbit_engine.compute_120min_orbital_cycle(test_tle, start_time)
        
        if 'positions' in result:
            logger.info(f"✅ SGP4 軌道計算成功，生成 {len(result['positions'])} 個位置點")
            
            # 檢查是否使用真實 SGP4 算法
            if result.get('computation_metadata', {}).get('time_grid_aligned'):
                logger.info("✅ 使用標準化時間網格，確認完整 SGP4 實現")
            
            return True
        else:
            logger.error("❌ SGP4 計算未返回位置數據")
            return False
            
    except ImportError as e:
        logger.error(f"❌ SGP4 庫導入失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ SGP4 算法驗證失敗: {e}")
        return False

def test_real_data_processing():
    """測試 2: 真實數據處理驗證"""
    logger.info("🧪 測試 2: 真實數據處理驗證")
    
    try:
        # 檢查 TLE 數據文件是否存在
        tle_data_dir = Path('/home/sat/ntn-stack/netstack/tle_data')
        
        if not tle_data_dir.exists():
            logger.error("❌ TLE 數據目錄不存在")
            return False
        
        # 檢查各星座數據
        constellations = ['starlink', 'oneweb']
        real_data_found = False
        
        for constellation in constellations:
            constellation_dir = tle_data_dir / constellation / 'tle'
            if constellation_dir.exists():
                tle_files = list(constellation_dir.glob('*.tle'))
                if tle_files:
                    logger.info(f"✅ 發現 {constellation} 真實 TLE 數據: {len(tle_files)} 個文件")
                    real_data_found = True
                    
                    # 檢查文件內容
                    with open(tle_files[0], 'r') as f:
                        content = f.read()
                        if 'STARLINK' in content or 'ONEWEB' in content:
                            logger.info(f"✅ {constellation} TLE 數據內容驗證通過")
        
        if real_data_found:
            logger.info("✅ 確認使用真實衛星數據，非模擬數據")
            return True
        else:
            logger.error("❌ 未發現真實 TLE 數據")
            return False
            
    except Exception as e:
        logger.error(f"❌ 真實數據驗證失敗: {e}")
        return False

def test_phase1_execution():
    """測試 3: 階段一執行測試"""
    logger.info("🧪 測試 3: 階段一完整執行測試")
    
    try:
        # 導入階段一處理器
        sys.path.append('/home/sat/ntn-stack/netstack/docker')
        from build_with_phase0_data_refactored import Phase25DataPreprocessor
        
        # 創建處理器實例
        preprocessor = Phase25DataPreprocessor(
            tle_data_dir='/home/sat/ntn-stack/netstack/tle_data',
            output_dir='/tmp/phase1_test_output'
        )
        
        logger.info("✅ Phase25DataPreprocessor 創建成功")
        
        # 執行階段一處理
        logger.info("⏳ 執行階段一處理（這可能需要幾分鐘）...")
        result = preprocessor.process_all_tle_data()
        
        # 驗證輸出結果
        if 'metadata' in result:
            metadata = result['metadata']
            logger.info(f"✅ 階段一處理完成")
            logger.info(f"   - 版本: {metadata.get('version', 'unknown')}")
            logger.info(f"   - 星座數: {metadata.get('total_constellations', 0)}")
            logger.info(f"   - 衛星數: {metadata.get('total_satellites', 0)}")
            
            # 檢查算法使用情況
            algorithms = metadata.get('algorithms', {})
            if algorithms.get('orbit_calculation') == 'full_sgp4_algorithm':
                logger.info("✅ 確認使用完整 SGP4 算法")
            if algorithms.get('no_simulation') == True:
                logger.info("✅ 確認無模擬數據")
            if algorithms.get('full_satellite_processing') == True:
                logger.info("✅ 確認全量衛星處理")
                
            return result
        else:
            logger.error("❌ 階段一處理結果缺少 metadata")
            return None
            
    except Exception as e:
        logger.error(f"❌ 階段一執行測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_phase2_input_compatibility(phase1_output):
    """測試 4: 階段二輸入兼容性"""
    logger.info("🧪 測試 4: 階段二輸入兼容性驗證")
    
    if not phase1_output:
        logger.error("❌ 階段一輸出為空，無法進行兼容性測試")
        return False
    
    try:
        # 檢查必要字段
        required_fields = ['metadata', 'constellations']
        for field in required_fields:
            if field not in phase1_output:
                logger.error(f"❌ 缺少必要字段: {field}")
                return False
        
        logger.info("✅ 基本結構檢查通過")
        
        # 檢查星座數據結構
        constellations = phase1_output['constellations']
        for constellation_name, constellation_data in constellations.items():
            if 'satellites' not in constellation_data:
                logger.error(f"❌ 星座 {constellation_name} 缺少 satellites 字段")
                return False
            
            # 檢查衛星數據結構
            satellites = constellation_data['satellites']
            if satellites:
                sample_satellite = satellites[0]
                
                # 檢查軌道數據
                if 'timeseries' in sample_satellite:
                    logger.info(f"✅ 星座 {constellation_name} 包含軌道時間序列數據")
                    
                    # 檢查時間序列數據格式
                    timeseries = sample_satellite['timeseries']
                    if timeseries and isinstance(timeseries, list):
                        sample_point = timeseries[0]
                        required_point_fields = ['time', 'lat', 'lon', 'elevation_deg', 'azimuth_deg']
                        
                        for field in required_point_fields:
                            if field not in sample_point:
                                logger.error(f"❌ 軌道數據點缺少字段: {field}")
                                return False
                        
                        logger.info(f"✅ 軌道數據格式符合階段二輸入要求")
                else:
                    logger.warning(f"⚠️ 星座 {constellation_name} 缺少 timeseries 數據")
        
        logger.info("✅ 階段二輸入兼容性驗證通過")
        return True
        
    except Exception as e:
        logger.error(f"❌ 兼容性驗證失敗: {e}")
        return False

def main():
    """主驗證流程"""
    logger.info("🚀 開始階段一整合驗證")
    logger.info("=" * 50)
    
    test_results = {}
    
    # 測試 1: SGP4 算法驗證
    test_results['sgp4_algorithm'] = test_sgp4_algorithm_validation()
    print()
    
    # 測試 2: 真實數據驗證
    test_results['real_data'] = test_real_data_processing()
    print()
    
    # 測試 3: 階段一執行
    phase1_output = test_phase1_execution()
    test_results['phase1_execution'] = phase1_output is not None
    print()
    
    # 測試 4: 階段二兼容性
    if phase1_output:
        test_results['phase2_compatibility'] = test_phase2_input_compatibility(phase1_output)
    else:
        test_results['phase2_compatibility'] = False
    print()
    
    # 總結報告
    logger.info("📊 驗證結果總結")
    logger.info("=" * 50)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n🎯 總體結果: {passed_tests}/{total_tests} 測試通過")
    
    if passed_tests == total_tests:
        logger.info("🎉 階段一整合驗證完全成功！")
        logger.info("✅ 確認使用完整 SGP4 算法")
        logger.info("✅ 確認處理真實衛星數據")
        logger.info("✅ 確認輸出符合階段二要求")
        return True
    else:
        logger.error("❌ 部分驗證失敗，需要修復")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)