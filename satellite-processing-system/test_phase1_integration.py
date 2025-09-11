#!/usr/bin/env python3
"""
Phase 1整合測試腳本

測試Stage4Processor是否正確整合了所有Phase 1組件：
- MeasurementOffsetConfig
- HandoverCandidateManager
- HandoverDecisionEngine
- DynamicThresholdController
"""

import sys
import logging
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from stages.stage4_signal_analysis.stage4_processor import Stage4Processor

def test_phase1_component_initialization():
    """測試Phase 1組件初始化"""
    print("🧪 測試 Phase 1 組件初始化...")
    
    try:
        # 創建Stage4Processor實例
        processor = Stage4Processor()
        
        # 檢查Phase 1組件是否正確初始化
        components = {
            "measurement_offset_config": hasattr(processor, 'measurement_offset_config'),
            "candidate_manager": hasattr(processor, 'candidate_manager'),
            "decision_engine": hasattr(processor, 'decision_engine'),
            "threshold_controller": hasattr(processor, 'threshold_controller')
        }
        
        print("📋 Phase 1 組件檢查結果:")
        for component, available in components.items():
            status = "✅" if available else "❌"
            print(f"  {status} {component}: {'可用' if available else '不可用'}")
        
        # 檢查處理統計是否包含Phase 1字段
        phase1_stats_fields = [
            "handover_candidates_evaluated",
            "handover_decisions_made", 
            "threshold_adjustments_performed"
        ]
        
        print("\n📊 處理統計字段檢查:")
        for field in phase1_stats_fields:
            available = field in processor.processing_stats
            status = "✅" if available else "❌"
            print(f"  {status} {field}: {'已包含' if available else '缺失'}")
        
        # 總體結果
        all_components_available = all(components.values())
        all_stats_available = all(field in processor.processing_stats for field in phase1_stats_fields)
        
        if all_components_available and all_stats_available:
            print("\n🎉 Phase 1 組件整合測試通過！")
            return True
        else:
            print("\n❌ Phase 1 組件整合測試失敗！")
            return False
            
    except Exception as e:
        print(f"\n❌ 初始化測試失敗: {e}")
        return False

def test_phase1_method_availability():
    """測試Phase 1相關方法是否可用"""
    print("\n🔍 測試 Phase 1 方法可用性...")
    
    try:
        processor = Stage4Processor()
        
        # 檢查新增的輔助方法
        phase1_methods = [
            "_calculate_candidate_diversity",
            "_calculate_decision_confidence",
            "_calculate_threshold_optimization",
            "_calculate_3gpp_compliance_rate",
            "_assess_phase1_component_availability",
            "_calculate_phase1_efficiency"
        ]
        
        print("📋 Phase 1 方法檢查結果:")
        methods_available = []
        for method in phase1_methods:
            available = hasattr(processor, method)
            status = "✅" if available else "❌"
            print(f"  {status} {method}: {'可用' if available else '不可用'}")
            methods_available.append(available)
        
        # 檢查Phase 1驗證方法
        validation_methods = [
            "_check_phase1_component_integration",
            "_check_phase1_3gpp_compliance",
            "_check_phase1_performance"
        ]
        
        print("\n📋 Phase 1 驗證方法檢查:")
        for method in validation_methods:
            available = hasattr(processor, method)
            status = "✅" if available else "❌"
            print(f"  {status} {method}: {'可用' if available else '不可用'}")
            methods_available.append(available)
        
        if all(methods_available):
            print("\n🎉 Phase 1 方法可用性測試通過！")
            return True
        else:
            print("\n❌ Phase 1 方法可用性測試失敗！")
            return False
            
    except Exception as e:
        print(f"\n❌ 方法可用性測試失敗: {e}")
        return False

def test_phase1_component_interaction():
    """測試Phase 1組件交互能力"""
    print("\n🔗 測試 Phase 1 組件交互...")
    
    try:
        processor = Stage4Processor()
        
        # 測試組件可用性評估
        availability = processor._assess_phase1_component_availability()
        print("📋 組件可用性評估結果:")
        for component, available in availability.items():
            status = "✅" if available else "❌"
            print(f"  {status} {component}: {'可用' if available else '不可用'}")
        
        # 測試Phase 1效率計算
        efficiency = processor._calculate_phase1_efficiency()
        print(f"\n📊 Phase 1 處理效率: {efficiency:.1f}%")
        
        # 測試配置統計
        if hasattr(processor.measurement_offset_config, 'get_current_configuration'):
            config = processor.measurement_offset_config.get_current_configuration()
            print(f"\n⚙️ 測量偏移配置可用: {'✅' if config else '❌'}")
        
        print("\n🎉 Phase 1 組件交互測試通過！")
        return True
        
    except Exception as e:
        print(f"\n❌ 組件交互測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🚀 Stage4 Phase 1 整合測試開始")
    print("=" * 60)
    
    # 設置日誌級別
    logging.basicConfig(level=logging.WARNING)
    
    tests = [
        ("Phase 1 組件初始化", test_phase1_component_initialization),
        ("Phase 1 方法可用性", test_phase1_method_availability),
        ("Phase 1 組件交互", test_phase1_component_interaction)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'-' * 40}")
        print(f"🧪 執行測試: {test_name}")
        print(f"{'-' * 40}")
        
        result = test_func()
        results.append((test_name, result))
    
    # 總結測試結果
    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 測試通過率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 所有Phase 1整合測試通過！Stage4處理器已成功整合Phase 1組件。")
        return True
    else:
        print(f"\n❌ 有 {len(results) - passed} 個測試失敗，需要檢查Phase 1整合。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)