#!/usr/bin/env python3
"""
TLE數據路徑管理器整合測試 - Phase 3.5 Task 4c
測試TLE路徑管理器與處理器的整合功能
"""

import sys
import os
import logging
from pathlib import Path

# 設置路徑以便導入模組
sys.path.append('/home/sat/ntn-stack')
sys.path.append('/home/sat/ntn-stack/netstack/src')

def test_tle_path_manager():
    """測試TLE路徑管理器基本功能"""
    print("=== 測試 1: TLE路徑管理器基本功能 ===")
    
    try:
        from tle_data_path_manager import create_tle_path_manager
        
        # 創建管理器
        manager = create_tle_path_manager()
        print(f"✅ TLE路徑管理器創建成功")
        print(f"   檢測環境: {manager.environment.value}")
        print(f"   基礎路徑: {manager.config.base_path}")
        
        # 測試路徑獲取
        starlink_path = manager.get_constellation_path('starlink', 'tle')
        oneweb_path = manager.get_constellation_path('oneweb', 'tle')
        
        print(f"   Starlink TLE路徑: {starlink_path}")
        print(f"   OneWeb TLE路徑: {oneweb_path}")
        
        # 測試文件發現
        starlink_files = manager.discover_tle_files('starlink')
        oneweb_files = manager.discover_tle_files('oneweb')
        
        print(f"   發現Starlink文件: {len(starlink_files)}個")
        print(f"   發現OneWeb文件: {len(oneweb_files)}個")
        
        if starlink_files:
            latest_starlink = starlink_files[0]
            print(f"   最新Starlink: {latest_starlink.date} ({latest_starlink.file_size/1024/1024:.1f}MB)")
        
        if oneweb_files:
            latest_oneweb = oneweb_files[0]
            print(f"   最新OneWeb: {latest_oneweb.date} ({latest_oneweb.file_size/1024/1024:.1f}MB)")
        
        return True
        
    except Exception as e:
        print(f"❌ TLE路徑管理器測試失敗: {e}")
        return False

def test_tle_health_check():
    """測試TLE數據健康檢查"""
    print("\n=== 測試 2: TLE數據健康檢查 ===")
    
    try:
        from tle_data_path_manager import create_tle_path_manager
        
        manager = create_tle_path_manager()
        health = manager.health_check()
        
        print(f"整體健康狀態: {'✅ 正常' if health['overall_healthy'] else '❌ 有問題'}")
        print(f"基礎路徑存在: {'✅' if health['base_path_exists'] else '❌'}")
        print(f"備份路徑存在: {'✅' if health['backup_path_exists'] else '❌'}")
        print(f"總TLE文件數: {health['total_tle_files']}")
        
        print("\n星座詳細狀態:")
        for const_name, const_info in health['constellations'].items():
            status = "✅" if const_info['tle_dir_exists'] and const_info['valid_files'] > 0 else "❌"
            print(f"  {const_name}: {status}")
            print(f"    TLE目錄存在: {'✅' if const_info['tle_dir_exists'] else '❌'}")
            print(f"    有效文件數: {const_info['valid_files']}")
            print(f"    最新日期: {const_info['latest_date'] or '無'}")
            print(f"    最新文件大小: {const_info['latest_size_mb']}MB")
        
        if health['issues']:
            print(f"\n發現的問題 ({len(health['issues'])}個):")
            for issue in health['issues']:
                print(f"  - {issue}")
        else:
            print(f"\n✅ 無問題發現")
        
        if health['latest_files']:
            print(f"\n最新文件摘要:")
            for const, date in health['latest_files'].items():
                print(f"  {const}: {date}")
        
        return health['overall_healthy']
        
    except Exception as e:
        print(f"❌ 健康檢查測試失敗: {e}")
        return False

def test_processor_integration():
    """測試與orbital_calculation_processor的整合"""
    print("\n=== 測試 3: 處理器整合 ===")
    
    try:
        # 導入處理器
        from stages.orbital_calculation_processor import Stage1TLEProcessor
        
        # 創建處理器實例（會自動初始化TLE路徑管理器）
        processor = Stage1TLEProcessor()
        
        print(f"✅ Stage1 TLE處理器創建成功")
        print(f"   TLE路徑標準化: {'✅' if processor.tle_path_standardized else '❌'}")
        print(f"   TLE數據目錄: {processor.tle_data_dir}")
        
        if hasattr(processor, 'tle_path_manager') and processor.tle_path_manager:
            print(f"   路徑管理器環境: {processor.tle_path_manager.environment.value}")
            
            # 測試獲取TLE文件路徑
            starlink_tle = processor.get_tle_file_for_constellation('starlink')
            oneweb_tle = processor.get_tle_file_for_constellation('oneweb')
            
            if starlink_tle:
                print(f"   Starlink TLE文件: {starlink_tle.name}")
            else:
                print(f"   Starlink TLE文件: ❌ 未找到")
                
            if oneweb_tle:
                print(f"   OneWeb TLE文件: {oneweb_tle.name}")
            else:
                print(f"   OneWeb TLE文件: ❌ 未找到")
        
        return True
        
    except Exception as e:
        print(f"❌ 處理器整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment_detection():
    """測試環境自動檢測"""
    print("\n=== 測試 4: 環境自動檢測 ===")
    
    try:
        from tle_data_path_manager import create_tle_path_manager
        
        manager = create_tle_path_manager()
        env = manager.environment
        
        print(f"檢測到的環境: {env.value}")
        
        # 檢測邏輯驗證
        if os.path.exists("/.dockerenv"):
            expected = "container"
        elif os.environ.get("DOCKER_CONTAINER", "").lower() == "true":
            expected = "container"
        elif os.path.exists("/home/sat/ntn-stack"):
            expected = "host"
        else:
            expected = "development"
        
        print(f"預期環境: {expected}")
        
        if env.value == expected:
            print("✅ 環境檢測正確")
            return True
        else:
            print("⚠️ 環境檢測與預期不符")
            return False
            
    except Exception as e:
        print(f"❌ 環境檢測測試失敗: {e}")
        return False

def test_migration_planning():
    """測試路徑遷移計劃"""
    print("\n=== 測試 5: 路徑遷移計劃 ===")
    
    try:
        from tle_data_path_manager import create_tle_path_manager, TLEDataEnvironment
        
        manager = create_tle_path_manager()
        
        # 創建到不同環境的遷移計劃
        for target_env in TLEDataEnvironment:
            if target_env != manager.environment:
                plan = manager.create_path_migration_plan(target_env)
                print(f"\n遷移計劃: {manager.environment.value} -> {target_env.value}")
                print(f"  預估數據大小: {plan['estimated_size_mb']:.1f}MB")
                print(f"  遷移項目數: {len(plan['migrations'])}")
                
                for migration in plan['migrations']:
                    print(f"    {migration['constellation']}: {migration['file_count']}文件 "
                          f"({migration['size_mb']:.1f}MB)")
                break  # 只測試一個遷移計劃
        
        return True
        
    except Exception as e:
        print(f"❌ 遷移計劃測試失敗: {e}")
        return False

def main():
    """執行所有測試"""
    print("🧪 TLE數據路徑管理器整合測試開始\n")
    
    # 設置日誌
    logging.basicConfig(
        level=logging.WARNING,  # 只顯示警告和錯誤，避免測試輸出混亂
        format='%(levelname)s: %(message)s'
    )
    
    # 執行測試
    tests = [
        ("TLE路徑管理器基本功能", test_tle_path_manager),
        ("TLE數據健康檢查", test_tle_health_check),
        ("處理器整合", test_processor_integration),
        ("環境自動檢測", test_environment_detection),
        ("路徑遷移計劃", test_migration_planning)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 執行失敗: {e}")
            results.append((test_name, False))
    
    # 顯示測試總結
    print(f"\n{'='*50}")
    print(f"🧪 測試總結")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試都通過了！TLE數據路徑管理器整合成功")
        return 0
    else:
        print("⚠️ 部分測試失敗，請檢查上面的錯誤信息")
        return 1

if __name__ == "__main__":
    exit(main())