#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 TDD核心測試執行器 - 完整TDD架構測試套件
📍 用於執行所有核心業務邏輯的TDD測試 (Phase 1-3)

🎯 測試範圍 (66個核心測試):
Phase 1: SGP4軌道引擎
- 🛰️ SGP4軌道引擎測試 (11個測試)
Phase 2: 信號處理與可見性  
- 📡 信號品質計算測試 (8個測試)  
- 👁️ 衛星可見性過濾測試 (8個測試)
Phase 3: Stage4-6核心算法
- ⏰ Stage4時間序列預處理測試 (8個測試)
- 🔧 Stage5數據整合引擎測試 (14個測試)
- 🤖 Stage6動態池規劃測試 (17個測試)

注意: 端到端整合測試和3GPP標準合規測試位於 tests/integration/ 目錄

使用方法:
python scripts/run_tdd_core_tests.py [--component=sgp4|signal|visibility|stage4|stage5|stage6|all]
"""

import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, timezone

class TDDTestRunner:
    """TDD測試運行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_components = {
            # Phase 1: SGP4 軌道引擎
            "sgp4": "tests/unit/algorithms/test_sgp4_orbital_engine.py",
            # Phase 2: 信號品質和可見性過濾
            "signal": "tests/unit/algorithms/test_signal_quality_calculator.py", 
            "visibility": "tests/unit/algorithms/test_satellite_visibility_filter.py",
            # Phase 3: Stage4-6 核心算法
            "stage4": "tests/unit/algorithms/test_timeseries_preprocessing.py",
            "stage5": "tests/unit/algorithms/test_data_integration_engine.py",
            "stage6": "tests/unit/algorithms/test_dynamic_pool_planning.py"
        }
        
    def run_component_tests(self, component_name, verbose=True):
        """運行指定組件的測試"""
        if component_name not in self.test_components:
            print(f"❌ 未知組件: {component_name}")
            print(f"✅ 可用組件: {', '.join(self.test_components.keys())}")
            return False
            
        test_file = self.test_components[component_name]
        print(f"\n🧪 執行{component_name.upper()}組件測試...")
        print(f"📂 測試文件: {test_file}")
        print("-" * 60)
        
        start_time = time.time()
        
        cmd = [
            "python", "-m", "pytest", 
            test_file,
            "-v" if verbose else "-q",
            "--tb=short",
            f"--junit-xml=tests/reports/{component_name}_test_results.xml"
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            end_time = time.time()
            duration = end_time - start_time
            
            print(result.stdout)
            if result.stderr:
                print("⚠️ 警告信息:")
                print(result.stderr)
                
            success = result.returncode == 0
            if success:
                print(f"✅ {component_name.upper()}測試通過! 耗時: {duration:.2f}秒")
            else:
                print(f"❌ {component_name.upper()}測試失敗! 耗時: {duration:.2f}秒")
                
            return success, duration
            
        except Exception as e:
            print(f"❌ 執行測試時發生錯誤: {e}")
            return False, 0
    
    def run_all_tests(self, verbose=True):
        """運行所有核心組件測試"""
        print("🚀 開始執行TDD核心測試套件...")
        print(f"📅 開始時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 60)
        
        total_start = time.time()
        results = {}
        
        for component in self.test_components:
            success, duration = self.run_component_tests(component, verbose)
            results[component] = {"success": success, "duration": duration}
        
        total_end = time.time()
        total_duration = total_end - total_start
        
        # 生成測試總結
        self.print_summary(results, total_duration)
        
        # 檢查整體成功率
        all_passed = all(result["success"] for result in results.values())
        return all_passed
    
    def print_summary(self, results, total_duration):
        """打印測試總結"""
        print("\n" + "=" * 60)
        print("📊 TDD核心測試套件執行總結")
        print("=" * 60)
        
        total_tests = sum(self.get_test_count(component) for component in self.test_components)
        passed_components = sum(1 for result in results.values() if result["success"])
        total_components = len(results)
        
        print(f"🧪 總測試數量: {total_tests}個測試 (Phase 1-3)")
        print(f"📦 測試組件: {passed_components}/{total_components}個通過")
        print(f"⏱️ 總執行時間: {total_duration:.2f}秒")
        print()
        
        # 各組件詳細結果
        print("📋 各組件測試結果:")
        for component, result in results.items():
            status = "✅ 通過" if result["success"] else "❌ 失敗" 
            test_count = self.get_test_count(component)
            print(f"  {component.upper():>12}: {status} ({test_count}個測試, {result['duration']:.2f}秒)")
        
        print()
        if all(result["success"] for result in results.values()):
            print("🎉 所有TDD核心測試通過！系統具備生產級穩定性！")
        else:
            print("⚠️ 部分測試失敗，請檢查具體錯誤信息")
        
        print(f"📅 完成時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    def get_test_count(self, component):
        """獲取各組件的測試數量（硬編碼，基於當前測試文件）"""
        test_counts = {
            # Phase 1
            "sgp4": 11,         # SGP4軌道引擎測試數量
            # Phase 2  
            "signal": 8,        # 信號品質計算測試數量  
            "visibility": 8,    # 衛星可見性過濾測試數量
            # Phase 3
            "stage4": 8,        # 時間序列預處理測試數量
            "stage5": 14,       # 數據整合引擎測試數量
            "stage6": 17        # 動態池規劃測試數量
        }
        return test_counts.get(component, 0)
    
    def run_quick_smoke_test(self):
        """運行快速冒煙測試 - 僅關鍵測試"""
        print("💨 執行快速冒煙測試...")
        
        smoke_tests = [
            # Phase 1: SGP4核心測試
            "tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_tle_epoch_time_usage_mandatory",
            # Phase 2: 信號品質核心測試
            "tests/unit/algorithms/test_signal_quality_calculator.py::TestSignalQualityCalculator::test_rsrp_calculation_friis_formula_compliance", 
            "tests/unit/algorithms/test_satellite_visibility_filter.py::TestSatelliteVisibilityFilter::test_elevation_threshold_filtering",
            # Phase 3: Stage4-6核心測試
            "tests/unit/algorithms/test_timeseries_preprocessing.py::TestTimeseriesPreprocessing::test_eci_to_wgs84_coordinate_conversion",
            "tests/unit/algorithms/test_data_integration_engine.py::TestStage5DataIntegrationEngine::test_enhanced_timeseries_processing",
            "tests/unit/algorithms/test_dynamic_pool_planning.py::TestStage6DynamicPoolPlanning::test_complete_dynamic_pool_processing"
        ]
        
        start_time = time.time()
        all_passed = True
        
        for test in smoke_tests:
            print(f"🧪 {test.split('::')[-1]}...")
            cmd = ["python", "-m", "pytest", test, "-q"]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ 通過")
            else:
                print("  ❌ 失敗")
                all_passed = False
        
        duration = time.time() - start_time
        print(f"\n💨 冒煙測試完成: {'✅ 通過' if all_passed else '❌ 失敗'} ({len(smoke_tests)}個核心測試, {duration:.2f}秒)")
        return all_passed

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description="TDD核心測試套件運行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
測試組件:
Phase 1:
  sgp4        SGP4軌道引擎測試 (11個測試)
Phase 2:
  signal      信號品質計算測試 (8個測試)  
  visibility  衛星可見性過濾測試 (8個測試)
Phase 3:
  stage4      時間序列預處理測試 (8個測試)
  stage5      數據整合引擎測試 (14個測試)
  stage6      動態池規劃測試 (17個測試)
  all         運行所有測試 (66個測試)

使用示例:
  python scripts/run_tdd_core_tests.py --component all
  python scripts/run_tdd_core_tests.py --component stage6
  python scripts/run_tdd_core_tests.py --smoke
        """
    )
    
    parser.add_argument(
        "--component", "-c",
        choices=["sgp4", "signal", "visibility", "stage4", "stage5", "stage6", "all"], 
        default="all",
        help="要運行的測試組件 (默認: all)"
    )
    
    parser.add_argument(
        "--smoke", "-s",
        action="store_true",
        help="運行快速冒煙測試"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true", 
        help="靜默模式（減少輸出）"
    )
    
    args = parser.parse_args()
    
    runner = TDDTestRunner()
    
    if args.smoke:
        success = runner.run_quick_smoke_test()
    elif args.component == "all":
        success = runner.run_all_tests(verbose=not args.quiet)
    else:
        success, _ = runner.run_component_tests(args.component, verbose=not args.quiet)
    
    # 返回適當的退出碼
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()