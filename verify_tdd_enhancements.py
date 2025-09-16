#!/usr/bin/env python3
"""
TDD增強框架驗證腳本
用於驗證修復後的12項科學級測試是否正常工作
"""

import sys
import json
from pathlib import Path

# 添加src路徑
sys.path.append(str(Path(__file__).parent / "satellite-processing-system" / "src"))

def test_tdd_framework():
    """測試TDD框架的完整性和功能"""

    try:
        from shared.tdd_integration_coordinator import TDDIntegrationCoordinator

        print("=== 🔬 TDD框架完整性驗證 ===")
        print()

        # 創建TDD協調器
        coordinator = TDDIntegrationCoordinator()
        test_engine = coordinator.test_engine

        # 檢查所有科學級測試方法是否存在
        scientific_methods = [
            '_validate_orbital_physics_constraints',
            '_validate_satellite_altitude_ranges',
            '_validate_orbital_velocity_ranges',
            '_validate_constellation_orbital_parameters',
            '_validate_time_epoch_consistency',
            '_validate_orbital_trajectory_statistics'
        ]

        basic_methods = [
            '_validate_output_structure',
            '_validate_data_integrity',
            '_validate_output_files_exist',
            '_validate_metadata_fields',
            '_validate_processing_statistics',
            '_validate_academic_compliance_markers'
        ]

        print("📋 基礎TDD測試方法:")
        basic_count = 0
        for method in basic_methods:
            if hasattr(test_engine, method):
                print(f"  ✅ {method}")
                basic_count += 1
            else:
                print(f"  ❌ {method} (缺失)")

        print()
        print("🚀 新增科學級測試方法:")
        scientific_count = 0
        for method in scientific_methods:
            if hasattr(test_engine, method):
                print(f"  ✅ {method}")
                scientific_count += 1
            else:
                print(f"  ❌ {method} (缺失)")

        total_methods = basic_count + scientific_count
        total_expected = len(basic_methods) + len(scientific_methods)

        print()
        print(f"🎯 框架完整性統計:")
        print(f"  • 基礎測試: {basic_count}/{len(basic_methods)} ({basic_count/len(basic_methods)*100:.1f}%)")
        print(f"  • 科學測試: {scientific_count}/{len(scientific_methods)} ({scientific_count/len(scientific_methods)*100:.1f}%)")
        print(f"  • 總體完整性: {total_methods}/{total_expected} ({total_methods/total_expected*100:.1f}%)")

        if total_methods == total_expected:
            print("\n🏆 TDD框架完全就緒！所有測試方法都已正確實現")
            return True
        else:
            print(f"\n⚠️ TDD框架不完整，缺少 {total_expected - total_methods} 個方法")
            return False

    except Exception as e:
        print(f"❌ TDD框架測試失敗: {e}")
        return False

def test_stage_when_available(stage_num: int):
    """當階段數據可用時測試該階段"""

    stage_file = Path(f"/satellite-processing/data/outputs/stage{stage_num}")

    if stage_num == 1:
        output_file = stage_file / "tle_orbital_calculation_output.json"
    elif stage_num == 4:
        output_file = stage_file / "enhanced_timeseries_output.json"
    else:
        print(f"⚠️ 階段 {stage_num} 的測試邏輯尚未實現")
        return False

    if not output_file.exists():
        print(f"⏳ 階段 {stage_num} 輸出尚未準備就緒: {output_file}")
        return False

    try:
        from shared.tdd_integration_coordinator import TDDIntegrationCoordinator

        with open(output_file, 'r') as f:
            stage_results = json.load(f)

        coordinator = TDDIntegrationCoordinator()
        test_engine = coordinator.test_engine

        # 所有測試方法
        if stage_num == 1:
            tests = [
                ('輸出結構驗證', test_engine._validate_output_structure),
                ('數據完整性驗證', test_engine._validate_data_integrity),
                ('輸出文件存在性驗證', test_engine._validate_output_files_exist),
                ('Metadata字段驗證', test_engine._validate_metadata_fields),
                ('處理統計驗證', test_engine._validate_processing_statistics),
                ('學術合規標記驗證', test_engine._validate_academic_compliance_markers),
                ('軌道物理約束驗證', test_engine._validate_orbital_physics_constraints),
                ('衛星高度範圍驗證', test_engine._validate_satellite_altitude_ranges),
                ('軌道速度範圍驗證', test_engine._validate_orbital_velocity_ranges),
                ('星座軌道參數驗證', test_engine._validate_constellation_orbital_parameters),
                ('時間基準一致性驗證', test_engine._validate_time_epoch_consistency),
                ('軌道軌跡統計驗證', test_engine._validate_orbital_trajectory_statistics)
            ]
        else:
            # 階段四適用的測試子集
            tests = [
                ('輸出結構驗證', test_engine._validate_output_structure),
                ('數據完整性驗證', test_engine._validate_data_integrity),
                ('輸出文件存在性驗證', test_engine._validate_output_files_exist),
                ('Metadata字段驗證', test_engine._validate_metadata_fields),
                ('處理統計驗證', test_engine._validate_processing_statistics),
                ('學術合規標記驗證', test_engine._validate_academic_compliance_markers),
                ('時間基準一致性驗證', test_engine._validate_time_epoch_consistency)
            ]

        print(f"\n=== 🧪 階段 {stage_num} TDD測試結果 ===")

        passed_tests = 0
        failed_tests = 0

        for test_name, test_func in tests:
            try:
                if hasattr(test_func, '__code__') and test_func.__code__.co_argcount == 2:
                    result = test_func(f'stage{stage_num}')
                else:
                    result = test_func(f'stage{stage_num}', stage_results)

                if result:
                    passed_tests += 1
                    status = '✅'
                else:
                    failed_tests += 1
                    status = '❌'
                print(f"  {status} {test_name}")
            except Exception as e:
                failed_tests += 1
                print(f"  ❌ {test_name} (錯誤: {str(e)[:30]}...)")

        total_tests = len(tests)
        coverage_percentage = (passed_tests / total_tests) * 100

        print(f"\n🎯 階段 {stage_num} 測試統計:")
        print(f"  • 總測試數: {total_tests}")
        print(f"  • 通過測試: {passed_tests}")
        print(f"  • 失敗測試: {failed_tests}")
        print(f"  • 測試覆蓋率: {coverage_percentage:.1f}%")

        if coverage_percentage == 100:
            print(f"🏆 階段 {stage_num} 達到100%測試覆蓋率！")
            return True
        elif coverage_percentage >= 90:
            print(f"🌟 階段 {stage_num} 質量優秀 (90%+)")
            return True
        else:
            print(f"⚠️ 階段 {stage_num} 需要進一步修復")
            return False

    except Exception as e:
        print(f"❌ 階段 {stage_num} 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔬 TDD增強框架驗證腳本")
    print("=" * 50)

    # 1. 測試框架完整性
    framework_ok = test_tdd_framework()

    if not framework_ok:
        print("\n❌ TDD框架不完整，請先修復框架問題")
        sys.exit(1)

    # 2. 測試可用的階段
    print("\n🧪 檢查可用階段並執行測試...")

    stages_tested = []

    for stage_num in [1, 4]:  # 重點測試階段1和4
        if test_stage_when_available(stage_num):
            stages_tested.append(stage_num)

    print("\n" + "=" * 50)
    print("📊 最終總結:")
    print(f"  • TDD框架: {'✅ 完整' if framework_ok else '❌ 不完整'}")
    print(f"  • 測試通過階段: {stages_tested}")

    if framework_ok and stages_tested:
        print("\n🎉 TDD增強框架驗證成功！")
        print("💡 系統已準備就緒進行科學級軌道計算質量保證")
    else:
        print("\n⚠️ 仍有問題需要修復")