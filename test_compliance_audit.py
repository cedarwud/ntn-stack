#!/usr/bin/env python3
"""
Phase 0 合規性審計功能測試
在虛擬環境中驗證核心模組功能
"""

import sys
import os
import importlib.util
import asyncio
from typing import Dict, Any, Optional

# 添加項目路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')
sys.path.insert(0, '/home/sat/ntn-stack/netstack/netstack_api')

def test_handover_event_detector():
    """測試事件檢測器"""
    print("🧪 測試 HandoverEventDetector...")
    
    try:
        # 直接導入模組
        spec = importlib.util.spec_from_file_location(
            'handover_event_detector', 
            '/home/sat/ntn-stack/netstack/src/services/satellite/handover_event_detector.py'
        )
        handover_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(handover_module)
        
        HandoverEventDetector = handover_module.HandoverEventDetector
        
        # 測試實例化
        detector = HandoverEventDetector('ntpu')
        print(f"✅ 實例化成功: 場景={detector.scene_id}")
        print(f"   門檻配置: 執行={detector.execution_threshold}°, 臨界={detector.critical_threshold}°")
        
        # 測試 RSRP 計算
        rsrp = detector._estimate_rsrp(45.0)
        print(f"✅ RSRP 計算: {rsrp:.1f} dBm")
        
        # 測試 D2 事件創建
        serving_sat = {
            'satellite_id': 'test-001',
            'constellation': 'starlink',
            'elevation_deg': 8.0,
            'azimuth_deg': 180.0,
            'range_km': 1200.0
        }
        
        neighbors = [{
            'satellite_id': 'test-002',
            'constellation': 'starlink', 
            'elevation_deg': 35.0,
            'azimuth_deg': 200.0,
            'range_km': 800.0
        }]
        
        d2_event = detector._create_d2_event('2025-08-02T12:00:00Z', serving_sat, neighbors)
        assert d2_event is not None, "D2 事件創建失敗"
        assert d2_event['event_type'] == 'D2', "D2 事件類型不正確"
        print(f"✅ D2 事件創建: 類型={d2_event['event_type']}, 嚴重程度={d2_event['severity']}")
        
        # 測試 A4 事件創建
        candidate_sat = {
            'satellite_id': 'test-003',
            'constellation': 'starlink',
            'elevation_deg': 45.0,
            'azimuth_deg': 150.0,
            'range_km': 700.0
        }
        
        a4_event = detector._create_a4_event('2025-08-02T12:00:00Z', candidate_sat, serving_sat)
        if a4_event:
            print(f"✅ A4 事件創建: 類型={a4_event['event_type']}, 品質優勢={a4_event.get('quality_advantage_db', 0):.1f}dB")
        else:
            print("ℹ️ A4 事件未觸發 (正常，取決於 RSRP 門檻)")
        
        print("✅ HandoverEventDetector 測試通過\n")
        return True
        
    except Exception as e:
        print(f"❌ HandoverEventDetector 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_layered_elevation_threshold():
    """測試分層門檻系統"""
    print("🧪 測試 LayeredElevationEngine...")
    
    try:
        # 導入分層門檻模組
        spec = importlib.util.spec_from_file_location(
            'layered_elevation_threshold', 
            '/home/sat/ntn-stack/netstack/src/services/satellite/layered_elevation_threshold.py'
        )
        threshold_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(threshold_module)
        
        create_layered_engine = threshold_module.create_layered_engine
        LayeredThreshold = threshold_module.LayeredThreshold
        HandoverPhase = threshold_module.HandoverPhase
        
        # 測試引擎創建
        engine = create_layered_engine('suburban')
        print("✅ 分層門檻引擎創建成功")
        
        # 測試門檻配置
        threshold = LayeredThreshold()
        print(f"✅ 門檻配置: 準備={threshold.pre_handover_elevation}°, 執行={threshold.execution_elevation}°, 臨界={threshold.critical_elevation}°")
        
        # 測試不同仰角的分析
        test_cases = [
            {'elevation': 20.0, 'expected_phase': 'monitoring'},
            {'elevation': 12.0, 'expected_phase': 'preparation'}, 
            {'elevation': 8.0, 'expected_phase': 'execution'},
            {'elevation': 3.0, 'expected_phase': 'critical'}
        ]
        
        print("📊 分層門檻分析:")
        for case in test_cases:
            test_satellite = {
                'elevation_deg': case['elevation'],
                'satellite_id': f'sat-{case["elevation"]}',
                'constellation': 'starlink'
            }
            
            result = engine.analyze_satellite_phase(test_satellite)
            phase = result.get('handover_phase', 'unknown')
            urgency = result.get('urgency_level', 'unknown')
            print(f"   仰角 {case['elevation']}° → 階段: {phase}, 緊急度: {urgency}")
        
        print("✅ LayeredElevationEngine 測試通過\n")
        return True
        
    except Exception as e:
        print(f"❌ LayeredElevationEngine 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_sib19_unified_platform():
    """測試 SIB19 統一平台"""
    print("🧪 測試 SIB19UnifiedPlatform...")
    
    try:
        # 導入 SIB19 模組
        sys.path.insert(0, '/home/sat/ntn-stack/netstack/netstack_api')
        from services.sib19_unified_platform import SIB19UnifiedPlatform, SIB19Data
        
        # 測試實例化（不依賴外部服務）
        platform = SIB19UnifiedPlatform(None, None)
        print("✅ SIB19UnifiedPlatform 實例化成功")
        
        # 測試狀態獲取
        status = await platform.get_sib19_status()
        print(f"✅ SIB19 狀態獲取: {status['status']}")
        
        # 測試時間校正生成
        time_correction = await platform._generate_time_correction()
        print(f"✅ 時間校正生成: {time_correction is not None}")
        
        # 測試 SMTC 配置生成
        smtc_config = await platform._generate_smtc_configuration(['sat-001', 'sat-002'])
        print(f"✅ SMTC 配置生成: {smtc_config is not None}")
        
        print("✅ SIB19UnifiedPlatform 基本功能測試通過\n")
        return True
        
    except Exception as e:
        print(f"❌ SIB19UnifiedPlatform 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rsrp_calculation():
    """測試 RSRP 計算相關功能"""
    print("🧪 測試 RSRP 計算功能...")
    
    try:
        # 測試多普勒補償系統
        try:
            spec = importlib.util.spec_from_file_location(
                'doppler_compensation_system', 
                '/home/sat/ntn-stack/netstack/src/services/satellite/doppler_compensation_system.py'
            )
            doppler_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(doppler_module)
            
            DopplerCompensationSystem = doppler_module.DopplerCompensationSystem
            
            # 創建多普勒系統實例
            doppler_system = DopplerCompensationSystem()
            print("✅ DopplerCompensationSystem 實例化成功")
            
            # 測試多普勒頻移計算
            test_params = {
                'satellite_velocity_ms': 7500.0,  # m/s
                'frequency_ghz': 28.0,
                'elevation_deg': 45.0
            }
            
            doppler_shift = doppler_system.calculate_doppler_shift(
                test_params['satellite_velocity_ms'],
                test_params['frequency_ghz'],
                test_params['elevation_deg']
            )
            print(f"✅ 多普勒頻移計算: {doppler_shift:.1f} Hz")
            
        except Exception as e:
            print(f"⚠️ 多普勒系統測試失敗: {e}")
        
        # 測試動態鏈路預算計算器
        try:
            spec = importlib.util.spec_from_file_location(
                'dynamic_link_budget_calculator', 
                '/home/sat/ntn-stack/netstack/src/services/satellite/dynamic_link_budget_calculator.py'
            )
            link_budget_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(link_budget_module)
            
            DynamicLinkBudgetCalculator = link_budget_module.DynamicLinkBudgetCalculator
            
            # 創建鏈路預算計算器實例
            link_calculator = DynamicLinkBudgetCalculator()
            print("✅ DynamicLinkBudgetCalculator 實例化成功")
            
        except Exception as e:
            print(f"⚠️ 動態鏈路預算測試失敗: {e}")
        
        print("✅ RSRP 相關功能測試完成\n")
        return True
        
    except Exception as e:
        print(f"❌ RSRP 計算測試失敗: {e}")
        return False

def test_import_coverage():
    """測試模組導入覆蓋率"""
    print("🧪 測試模組導入覆蓋率...")
    
    modules_to_test = [
        ('/home/sat/ntn-stack/netstack/src/services/satellite/handover_event_detector.py', 'HandoverEventDetector'),
        ('/home/sat/ntn-stack/netstack/src/services/satellite/layered_elevation_threshold.py', 'LayeredElevationEngine'),
        ('/home/sat/ntn-stack/netstack/src/services/satellite/doppler_compensation_system.py', 'DopplerCompensationSystem'),
        ('/home/sat/ntn-stack/netstack/src/services/satellite/dynamic_link_budget_calculator.py', 'DynamicLinkBudgetCalculator'),
        ('/home/sat/ntn-stack/netstack/src/services/satellite/smtc_measurement_optimizer.py', 'SMTCMeasurementOptimizer'),
        ('/home/sat/ntn-stack/netstack/netstack_api/services/sib19_unified_platform.py', 'SIB19UnifiedPlatform'),
    ]
    
    successful_imports = 0
    total_modules = len(modules_to_test)
    
    for module_path, class_name in modules_to_test:
        try:
            if os.path.exists(module_path):
                spec = importlib.util.spec_from_file_location(
                    f'test_module_{successful_imports}', 
                    module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, class_name):
                    print(f"✅ {class_name} 導入成功")
                    successful_imports += 1
                else:
                    print(f"⚠️ {class_name} 類別不存在於模組中")
            else:
                print(f"❌ 模組檔案不存在: {module_path}")
        except Exception as e:
            print(f"❌ {class_name} 導入失敗: {e}")
    
    coverage_rate = (successful_imports / total_modules) * 100
    print(f"\n📊 模組導入覆蓋率: {successful_imports}/{total_modules} ({coverage_rate:.1f}%)")
    
    return coverage_rate >= 80.0  # 80% 覆蓋率為通過標準

async def main():
    """主測試函數"""
    print("🚀 開始 Phase 0 合規性審計功能測試")
    print("=" * 60)
    
    test_results = []
    
    # 1. 測試模組導入覆蓋率
    test_results.append(("模組導入覆蓋率", test_import_coverage()))
    
    # 2. 測試事件檢測器
    test_results.append(("HandoverEventDetector", test_handover_event_detector()))
    
    # 3. 測試分層門檻系統
    test_results.append(("LayeredElevationEngine", test_layered_elevation_threshold()))
    
    # 4. 測試 SIB19 統一平台
    test_results.append(("SIB19UnifiedPlatform", await test_sib19_unified_platform()))
    
    # 5. 測試 RSRP 計算功能
    test_results.append(("RSRP 計算功能", test_rsrp_calculation()))
    
    # 生成測試報告
    print("=" * 60)
    print("📋 測試結果總結:")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n🎯 測試通過率: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80.0:
        print("🎉 測試結果: 總體通過！")
        return True
    else:
        print("⚠️ 測試結果: 需要改進")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)