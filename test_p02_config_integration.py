#!/usr/bin/env python3
"""
P0.2 配置系統統一 - 測試腳本
驗證 LEO 配置系統是否正確整合
"""

import sys
import asyncio
import json
from pathlib import Path

# Add paths
sys.path.append('/home/sat/ntn-stack/netstack/config')
sys.path.append('/home/sat/ntn-stack/netstack/src/leo_core')

def test_leo_config_creation():
    """測試 LEO 配置系統創建"""
    print("🧪 測試 LEO 配置系統創建...")
    
    try:
        from leo_config import (
            create_default_config,
            create_netstack_compatible_config,
            create_unified_config_manager
        )
        
        # Test 1: Default config creation
        leo_config = create_default_config()
        print("✅ LEO restructure 預設配置創建成功")
        print(f"   - TLE Loader: {'tle_loader' in leo_config}")
        print(f"   - Satellite Filter: {'satellite_filter' in leo_config}")
        print(f"   - Event Processor: {'event_processor' in leo_config}")
        print(f"   - Optimizer: {'optimizer' in leo_config}")
        
        # Test 2: NetStack compatible config
        netstack_config = create_netstack_compatible_config()
        print("✅ NetStack 兼容配置創建成功")
        print(f"   - Observer: {'observer' in netstack_config}")
        print(f"   - Elevation Thresholds: {'elevation_thresholds' in netstack_config}")
        print(f"   - Signal Thresholds: {'signal_thresholds' in netstack_config}")
        
        # Test 3: Unified config manager
        manager = create_unified_config_manager(ultra_fast=True)
        manager_config = manager.get_leo_restructure_format()
        print("✅ 統一配置管理器創建成功")
        
        # Check ultra-fast mode settings
        sample_limits = manager_config['tle_loader'].get('sample_limits', {})
        if sample_limits and sample_limits.get('starlink') == 10:
            print("✅ Ultra-fast 模式配置正確")
        else:
            print("⚠️  Ultra-fast 模式配置可能有問題")
        
        return True
        
    except Exception as e:
        print(f"❌ LEO 配置系統測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_leo_restructure_compatibility():
    """測試與 LEO restructure 系統的兼容性"""
    print("\n🧪 測試與 LEO restructure 系統兼容性...")
    
    try:
        # Test compatibility with existing leo restructure config format
        from leo_config import create_default_config
        
        config = create_default_config()
        
        # Verify required sections exist
        required_sections = ['tle_loader', 'satellite_filter', 'event_processor', 'optimizer']
        for section in required_sections:
            if section not in config:
                print(f"❌ 缺少必要配置段落: {section}")
                return False
        
        # Verify TLE loader configuration
        tle_config = config['tle_loader']
        if 'data_sources' not in tle_config:
            print("❌ TLE loader 缺少 data_sources")
            return False
            
        if 'calculation_params' not in tle_config:
            print("❌ TLE loader 缺少 calculation_params")
            return False
        
        # Verify NTPU coordinates
        satellite_filter = config['satellite_filter']
        if 'ntpu_coordinates' not in satellite_filter:
            print("❌ Satellite filter 缺少 NTPU coordinates")
            return False
            
        ntpu_coords = satellite_filter['ntpu_coordinates']
        expected_lat, expected_lon = 24.9441667, 121.3713889
        
        if (abs(ntpu_coords['latitude'] - expected_lat) > 0.001 or 
            abs(ntpu_coords['longitude'] - expected_lon) > 0.001):
            print("❌ NTPU 座標不正確")
            return False
        
        print("✅ LEO restructure 兼容性測試通過")
        return True
        
    except Exception as e:
        print(f"❌ LEO restructure 兼容性測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_elevation_thresholds():
    """測試仰角門檻配置"""
    print("\n🧪 測試仰角門檻配置...")
    
    try:
        from leo_config import LEOConfigManager
        
        manager = LEOConfigManager()
        netstack_format = manager.get_legacy_netstack_format()
        
        # Check Starlink thresholds
        starlink_thresholds = netstack_format['elevation_thresholds']['starlink']
        expected_starlink = {
            'min_elevation': 10.0,
            'preparation_elevation': 15.0,
            'critical_elevation': 5.0
        }
        
        for key, expected_value in expected_starlink.items():
            if starlink_thresholds.get(key) != expected_value:
                print(f"❌ Starlink {key} 不正確: 期望 {expected_value}, 實際 {starlink_thresholds.get(key)}")
                return False
        
        # Check OneWeb thresholds  
        oneweb_thresholds = netstack_format['elevation_thresholds']['oneweb']
        expected_oneweb = {
            'min_elevation': 15.0,
            'preparation_elevation': 20.0,
            'critical_elevation': 10.0
        }
        
        for key, expected_value in expected_oneweb.items():
            if oneweb_thresholds.get(key) != expected_value:
                print(f"❌ OneWeb {key} 不正確: 期望 {expected_value}, 實際 {oneweb_thresholds.get(key)}")
                return False
        
        print("✅ 仰角門檻配置測試通過")
        print(f"   - Starlink 執行門檻: {starlink_thresholds['min_elevation']}°")
        print(f"   - OneWeb 執行門檻: {oneweb_thresholds['min_elevation']}°")
        return True
        
    except Exception as e:
        print(f"❌ 仰角門檻配置測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mode_switching():
    """測試運行模式切換"""
    print("\n🧪 測試運行模式切換...")
    
    try:
        from leo_config import create_unified_config_manager
        
        # Test ultra-fast mode
        ultra_fast_manager = create_unified_config_manager(ultra_fast=True)
        ultra_fast_config = ultra_fast_manager.get_leo_restructure_format()
        
        sample_limits = ultra_fast_config['tle_loader'].get('sample_limits', {})
        if sample_limits.get('starlink') != 10:
            print(f"❌ Ultra-fast 模式 Starlink 限制不正確: {sample_limits.get('starlink')}")
            return False
        
        # Test production mode
        production_manager = create_unified_config_manager(production=True)
        production_config = production_manager.get_leo_restructure_format()
        
        production_limits = production_config['tle_loader'].get('sample_limits')
        if production_limits is not None:
            print(f"❌ Production 模式不應該有樣本限制: {production_limits}")
            return False
        
        print("✅ 運行模式切換測試通過")
        print(f"   - Ultra-fast: Starlink 限制 {sample_limits.get('starlink')} 顆")
        print(f"   - Production: 無樣本限制")
        return True
        
    except Exception as e:
        print(f"❌ 運行模式切換測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 P0.2 配置系統統一 - 整合測試")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("LEO配置系統創建", test_leo_config_creation()))
    test_results.append(("LEO restructure兼容性", test_leo_restructure_compatibility()))
    test_results.append(("仰角門檻配置", test_elevation_thresholds()))
    test_results.append(("運行模式切換", test_mode_switching()))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 P0.2 測試結果總結:")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} {test_name}")
        if result:
            passed_tests += 1
    
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests) * 100
    
    print(f"\n📊 測試通過率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎉 P0.2 配置系統統一 - 全部測試通過！")
        print("✅ 準備進行 P0.3 輸出格式對接")
        return True
    else:
        print(f"\n⚠️  P0.2 配置系統統一 - 需要修復 {total_tests - passed_tests} 個問題")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)