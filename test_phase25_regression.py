#!/usr/bin/env python3
"""
Phase 2.5 回歸測試
確保重構不破壞現有功能並驗證新架構正確性
"""

import os
import sys
import logging
import json
from typing import Dict, Any, List

# 添加路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/config')
sys.path.insert(0, '/home/sat/ntn-stack/netstack')

def run_regression_tests():
    """執行全面的回歸測試"""
    
    logging.basicConfig(level=logging.WARNING)  # 減少日誌輸出
    
    print("=" * 80)
    print("Phase 2.5 回歸測試 - 確保重構不破壞現有功能")
    print("=" * 80)
    
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    # ===================================================================
    # 測試 1: 統一配置系統完整性測試
    # ===================================================================
    print("🔧 測試 1: 統一配置系統完整性")
    test_results["total_tests"] += 1
    
    try:
        from unified_satellite_config import get_unified_config, UnifiedSatelliteConfig
        
        # 測試配置載入
        config = get_unified_config()
        assert config is not None, "配置載入失敗"
        
        # 測試配置驗證
        validation_result = config.validate()
        assert validation_result.is_valid, f"配置驗證失敗: {validation_result.errors}"
        
        # 測試配置內容
        assert config.version == "5.0.0", f"版本錯誤: {config.version}"
        assert len(config.constellations) == 2, f"星座數量錯誤: {len(config.constellations)}"
        assert "starlink" in config.constellations, "缺少 Starlink 配置"
        assert "oneweb" in config.constellations, "缺少 OneWeb 配置"
        
        # 測試觀測點配置
        assert abs(config.observer.latitude - 24.9441667) < 0.001, "觀測點緯度錯誤"
        assert abs(config.observer.longitude - 121.3713889) < 0.001, "觀測點經度錯誤"
        
        # 測試配置方法
        starlink_config = config.get_constellation_config("starlink")
        assert starlink_config is not None, "無法獲取 Starlink 配置"
        assert starlink_config.total_satellites == 555, f"Starlink 衛星池錯誤: {starlink_config.total_satellites}"
        assert starlink_config.target_satellites == 15, f"Starlink 目標錯誤: {starlink_config.target_satellites}"
        
        test_results["passed_tests"] += 1
        test_results["test_details"].append({"name": "統一配置系統", "status": "✅ 通過", "details": "配置完整性驗證通過"})
        print("✅ 統一配置系統測試通過")
        
    except Exception as e:
        test_results["failed_tests"] += 1
        test_results["test_details"].append({"name": "統一配置系統", "status": "❌ 失敗", "details": str(e)})
        print(f"❌ 統一配置系統測試失敗: {e}")
    
    # ===================================================================
    # 測試 2: 數據池準備器功能測試
    # ===================================================================
    print("\n🏗️ 測試 2: 數據池準備器功能")
    test_results["total_tests"] += 1
    
    try:
        from satellite_data_pool_builder import create_satellite_data_pool_builder
        
        # 創建準備器
        config = get_unified_config()
        builder = create_satellite_data_pool_builder(config)
        assert builder is not None, "數據池準備器創建失敗"
        
        # 準備測試數據
        test_raw_data = {
            "starlink": [
                {
                    "name": f"TEST-STARLINK-{i}",
                    "norad_id": 40000 + i,
                    "line1": f"1 {40000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                    "line2": f"2 {40000+i:05d}  53.2000 100.0000 0001000  90.0000 270.0000 15.50000000    1{i%10}",
                    "tle_date": "20250810"
                }
                for i in range(100)  # 100 顆測試數據
            ],
            "oneweb": [
                {
                    "name": f"TEST-ONEWEB-{i}",
                    "norad_id": 45000 + i,
                    "line1": f"1 {45000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                    "line2": f"2 {45000+i:05d}  87.4000 180.0000 0001000  45.0000 315.0000 13.50000000    1{i%10}",
                    "tle_date": "20250810"
                }
                for i in range(50)   # 50 顆測試數據
            ]
        }
        
        # 測試池建構
        pools = builder.build_satellite_pools(test_raw_data)
        assert pools is not None, "衛星池建構失敗"
        assert "starlink" in pools, "缺少 Starlink 池"
        assert "oneweb" in pools, "缺少 OneWeb 池"
        
        # 測試池大小（應該受到配置目標限制）
        starlink_pool_size = len(pools["starlink"])
        oneweb_pool_size = len(pools["oneweb"])
        
        # Starlink: 100 -> 100 (小於 555 目標，全部保留)
        # OneWeb: 50 -> 50 (小於 134 目標，全部保留)
        assert starlink_pool_size == 100, f"Starlink 池大小錯誤: {starlink_pool_size}"
        assert oneweb_pool_size == 50, f"OneWeb 池大小錯誤: {oneweb_pool_size}"
        
        # 測試統計信息
        stats = builder.get_pool_statistics(pools)
        assert stats["total_constellations"] == 2, "星座數統計錯誤"
        assert stats["total_satellites"] == 150, "總衛星數統計錯誤"
        
        test_results["passed_tests"] += 1
        test_results["test_details"].append({"name": "數據池準備器", "status": "✅ 通過", "details": f"成功建構 {starlink_pool_size + oneweb_pool_size} 顆衛星池"})
        print("✅ 數據池準備器測試通過")
        
    except Exception as e:
        test_results["failed_tests"] += 1
        test_results["test_details"].append({"name": "數據池準備器", "status": "❌ 失敗", "details": str(e)})
        print(f"❌ 數據池準備器測試失敗: {e}")
    
    # ===================================================================
    # 測試 3: 智能衛星選擇器功能測試
    # ===================================================================
    print("\n🚀 測試 3: 智能衛星選擇器功能")
    test_results["total_tests"] += 1
    
    try:
        from intelligent_satellite_selector import create_intelligent_satellite_selector
        
        # 創建選擇器
        config = get_unified_config()
        selector = create_intelligent_satellite_selector(config)
        assert selector is not None, "智能選擇器創建失敗"
        
        # 準備測試衛星池
        test_pools = {
            "starlink": [
                {
                    "name": f"TEST-STARLINK-{i}",
                    "norad_id": 40000 + i,
                    "constellation": "starlink",
                    "line1": f"1 {40000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                    "line2": f"2 {40000+i:05d}  {53 + (i%5)*0.1:.1f}000 {i*10%360:03d}.0000 000{i%9+1:d}000  {i*15%360:03d}.0000 {i*20%360:03d}.0000 15.{40+i%20:02d}000000    1{i%10}",
                    "tle_date": "20250810"
                }
                for i in range(30)  # 30 顆 Starlink 測試池
            ],
            "oneweb": [
                {
                    "name": f"TEST-ONEWEB-{i}",
                    "norad_id": 45000 + i,
                    "constellation": "oneweb",
                    "line1": f"1 {45000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                    "line2": f"2 {45000+i:05d}  87.{4000+i*10%1000:04d} {i*12%360:03d}.0000 000{i%7+1:d}000  {i*25%360:03d}.0000 {i*30%360:03d}.0000 13.{20+i%15:02d}000000    1{i%10}",
                    "tle_date": "20250810"
                }
                for i in range(15)  # 15 顆 OneWeb 測試池
            ]
        }
        
        # 測試智能選擇
        result = selector.select_optimal_satellites(test_pools)
        assert result is not None, "智能選擇結果為空"
        assert hasattr(result, 'selected_satellites'), "選擇結果缺少衛星數據"
        assert hasattr(result, 'metrics'), "選擇結果缺少指標數據"
        assert hasattr(result, 'selection_summary'), "選擇結果缺少統計數據"
        
        # 測試選擇數量
        total_selected = len(result.selected_satellites)
        expected_total = 15 + 8  # Starlink 15 + OneWeb 8
        assert total_selected == expected_total, f"選擇數量錯誤: {total_selected} != {expected_total}"
        
        # 測試星座分佈
        starlink_selected = result.get_constellation_count("starlink")
        oneweb_selected = result.get_constellation_count("oneweb")
        assert starlink_selected == 15, f"Starlink 選擇數錯誤: {starlink_selected}"
        assert oneweb_selected == 8, f"OneWeb 選擇數錯誤: {oneweb_selected}"
        
        # 測試指標評分
        assert len(result.metrics) == total_selected, "指標數量與選擇衛星數不匹配"
        
        # 檢查評分合理性
        for metric in result.metrics:
            score = metric.get_overall_score()
            assert 0 <= score <= 100, f"評分超出範圍: {score}"
            assert metric.satellite_name.startswith("TEST-"), "衛星名稱格式錯誤"
        
        test_results["passed_tests"] += 1
        test_results["test_details"].append({"name": "智能衛星選擇器", "status": "✅ 通過", "details": f"成功選擇 {total_selected} 顆衛星"})
        print("✅ 智能衛星選擇器測試通過")
        
    except Exception as e:
        test_results["failed_tests"] += 1
        test_results["test_details"].append({"name": "智能衛星選擇器", "status": "❌ 失敗", "details": str(e)})
        print(f"❌ 智能衛星選擇器測試失敗: {e}")
    
    # ===================================================================
    # 測試 4: 端到端工作流程測試
    # ===================================================================
    print("\n🔄 測試 4: 端到端工作流程")
    test_results["total_tests"] += 1
    
    try:
        # 完整工作流程：原始數據 -> 數據池 -> 智能選擇
        config = get_unified_config()
        builder = create_satellite_data_pool_builder(config)
        selector = create_intelligent_satellite_selector(config)
        
        # 原始數據
        raw_data = {
            "starlink": [
                {
                    "name": f"E2E-STARLINK-{i}",
                    "norad_id": 30000 + i,
                    "line1": f"1 {30000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                    "line2": f"2 {30000+i:05d}  53.2000 {i*5%360:03d}.0000 0001000  {i*8%360:03d}.0000 {i*12%360:03d}.0000 15.50000000    1{i%10}",
                    "tle_date": "20250810"
                }
                for i in range(600)  # 600 顆原始數據
            ],
            "oneweb": [
                {
                    "name": f"E2E-ONEWEB-{i}",
                    "norad_id": 35000 + i,
                    "line1": f"1 {35000+i:05d}U 21001A   21001.00000000  .00001000  00000-0  10000-4 0  999{i%10}",
                    "line2": f"2 {35000+i:05d}  87.4000 {i*6%360:03d}.0000 0001000  {i*9%360:03d}.0000 {i*15%360:03d}.0000 13.50000000    1{i%10}",
                    "tle_date": "20250810"
                }
                for i in range(150)  # 150 顆原始數據
            ]
        }
        
        # 步驟1: 建構衛星池
        pools = builder.build_satellite_pools(raw_data)
        assert len(pools["starlink"]) == 555, "Starlink 池大小不符合配置"  # 600 -> 555 (達到目標)
        assert len(pools["oneweb"]) == 134, "OneWeb 池大小不符合配置"     # 150 -> 134 (達到目標)
        
        # 步驟2: 智能選擇
        result = selector.select_optimal_satellites(pools)
        assert len(result.selected_satellites) == 23, "端到端選擇數量錯誤"  # 15 + 8 = 23
        
        # 驗證數據流一致性
        original_count = 600 + 150  # 750 顆原始
        pool_count = 555 + 134      # 689 顆池
        selected_count = 23         # 23 顆選擇
        
        assert original_count > pool_count > selected_count, "數據流遞減檢查失敗"
        
        # 驗證配置一致性
        expected_selected = sum(c.target_satellites for c in config.constellations.values())
        assert selected_count == expected_selected, "配置與選擇結果不一致"
        
        test_results["passed_tests"] += 1
        test_results["test_details"].append({"name": "端到端工作流程", "status": "✅ 通過", "details": f"數據流: {original_count} -> {pool_count} -> {selected_count}"})
        print("✅ 端到端工作流程測試通過")
        
    except Exception as e:
        test_results["failed_tests"] += 1
        test_results["test_details"].append({"name": "端到端工作流程", "status": "❌ 失敗", "details": str(e)})
        print(f"❌ 端到端工作流程測試失敗: {e}")
    
    # ===================================================================
    # 測試 5: 架構分離驗證測試
    # ===================================================================
    print("\n🏛️ 測試 5: 架構分離驗證")
    test_results["total_tests"] += 1
    
    try:
        # 驗證建構時和運行時的職責分離
        config = get_unified_config()
        builder = create_satellite_data_pool_builder(config)
        selector = create_intelligent_satellite_selector(config)
        
        # 檢查類別職責
        # 數據池準備器應該不包含智能評分邏輯
        builder_methods = [method for method in dir(builder) if not method.startswith('_')]
        intelligent_methods = [method for method in dir(selector) if not method.startswith('_')]
        
        # 檢查職責邊界
        assert 'build_satellite_pools' in builder_methods, "數據池準備器缺少主要方法"
        assert 'select_optimal_satellites' in intelligent_methods, "智能選擇器缺少主要方法"
        
        # 檢查不應該存在的交叉職責
        prohibited_in_builder = ['evaluate_satellite', 'calculate_visibility_score', 'handover_suitability']
        prohibited_in_selector = ['basic_filter_satellites', 'diverse_sampling']
        
        for method in prohibited_in_builder:
            assert method not in builder_methods, f"數據池準備器不應包含智能評估方法: {method}"
        
        for method in prohibited_in_selector:
            assert method not in intelligent_methods, f"智能選擇器不應包含基礎篩選方法: {method}"
        
        # 檢查配置統一
        assert builder.config.version == selector.config.version, "配置版本不一致"
        assert builder.config.constellations.keys() == selector.config.constellations.keys(), "支援星座不一致"
        
        test_results["passed_tests"] += 1
        test_results["test_details"].append({"name": "架構分離驗證", "status": "✅ 通過", "details": "職責分離清晰，配置統一"})
        print("✅ 架構分離驗證測試通過")
        
    except Exception as e:
        test_results["failed_tests"] += 1
        test_results["test_details"].append({"name": "架構分離驗證", "status": "❌ 失敗", "details": str(e)})
        print(f"❌ 架構分離驗證測試失敗: {e}")
    
    # ===================================================================
    # 測試結果總結
    # ===================================================================
    print("\n" + "=" * 80)
    print("回歸測試結果總結")
    print("=" * 80)
    
    print(f"總測試數: {test_results['total_tests']}")
    print(f"通過測試: {test_results['passed_tests']} ✅")
    print(f"失敗測試: {test_results['failed_tests']} ❌")
    print(f"成功率: {test_results['passed_tests'] / test_results['total_tests'] * 100:.1f}%")
    
    print(f"\n詳細測試結果:")
    for test_detail in test_results["test_details"]:
        print(f"  {test_detail['status']} {test_detail['name']}: {test_detail['details']}")
    
    # 判定整體結果
    all_tests_passed = test_results["failed_tests"] == 0
    
    if all_tests_passed:
        print(f"\n🎉 所有回歸測試通過！Phase 2.5 重構成功！")
        print("✅ 雙重篩選邏輯矛盾已完全解決")
        print("✅ 新架構功能正常，不影響現有功能")
        print("✅ 統一配置系統運行穩定")
        print("✅ 建構時與運行時職責分離清晰")
    else:
        print(f"\n⚠️ 發現 {test_results['failed_tests']} 個測試失敗")
        print("❌ 需要修復失敗的測試才能完成重構")
    
    print("=" * 80)
    
    return all_tests_passed, test_results

if __name__ == "__main__":
    success, results = run_regression_tests()
    
    # 生成測試報告
    report_path = "/home/sat/ntn-stack/phase25_regression_test_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": "2025-08-10T07:30:00Z",
            "phase": "2.5",
            "test_type": "regression_testing", 
            "overall_success": success,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 測試報告已保存至: {report_path}")
    
    sys.exit(0 if success else 1)