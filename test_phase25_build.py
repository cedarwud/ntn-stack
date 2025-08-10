#!/usr/bin/env python3
"""
Phase 2.5 重構版建構腳本測試版本
使用本地路徑進行測試
"""

import os
import sys
import tempfile

# 添加路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/config')
sys.path.insert(0, '/home/sat/ntn-stack/netstack')
sys.path.insert(0, '/home/sat/ntn-stack/netstack/docker')

# 導入重構版預處理器
from build_with_phase0_data_refactored import Phase25DataPreprocessor

def test_phase25_preprocessor():
    print("=" * 60)
    print("Phase 2.5 重構版建構腳本測試")
    print("=" * 60)
    
    # 使用臨時目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        tle_data_dir = os.path.join(temp_dir, "tle_data")
        output_dir = os.path.join(temp_dir, "data")
        
        # 創建測試目錄結構
        os.makedirs(tle_data_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"TLE 數據目錄: {tle_data_dir}")
        print(f"輸出目錄: {output_dir}")
        
        try:
            # 創建重構版預處理器
            preprocessor = Phase25DataPreprocessor(
                tle_data_dir=tle_data_dir,
                output_dir=output_dir
            )
            
            print("✅ 預處理器創建成功")
            print(f"  配置版本: {preprocessor.config.version}")
            print(f"  觀測座標: ({preprocessor.observer_lat:.5f}°, {preprocessor.observer_lon:.5f}°)")
            print(f"  SGP4 啟用: {preprocessor.enable_sgp4}")
            print(f"  支援星座: {', '.join(preprocessor.supported_constellations)}")
            
            # 測試數據掃描 (空目錄)
            scan_result = preprocessor.scan_tle_data()
            print(f"\n掃描測試結果:")
            print(f"  總星座數: {scan_result['total_constellations']}")
            print(f"  總文件數: {scan_result['total_files']}")
            
            # 測試數據池準備器
            try:
                from config.satellite_data_pool_builder import create_satellite_data_pool_builder
                builder = create_satellite_data_pool_builder(preprocessor.config)
                print("✅ 數據池準備器集成成功")
            except ImportError as e:
                print(f"⚠️ 數據池準備器導入失敗: {e}")
            
            # 測試智能選擇器
            try:
                from config.intelligent_satellite_selector import create_intelligent_satellite_selector
                selector = create_intelligent_satellite_selector(preprocessor.config)
                print("✅ 智能選擇器集成成功")
            except ImportError as e:
                print(f"⚠️ 智能選擇器導入失敗: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            return False

if __name__ == "__main__":
    success = test_phase25_preprocessor()
    print(f"\n{'=' * 60}")
    print(f"測試結果: {'成功' if success else '失敗'}")
    print("=" * 60)