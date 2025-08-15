#!/usr/bin/env python3
"""
P0.3 Output Format Alignment - 測試腳本
驗證 LEO 到前端格式轉換是否正確
"""

import json
import sys
import os
from pathlib import Path

# Add paths
sys.path.append('/home/sat/ntn-stack/netstack/config')

def test_format_converter_creation():
    """測試格式轉換器創建"""
    print("🧪 測試格式轉換器創建...")
    
    try:
        from output_format_converter import create_leo_to_frontend_converter
        
        converter = create_leo_to_frontend_converter()
        if converter is None:
            print("❌ 轉換器創建失敗")
            return False
        
        print("✅ 格式轉換器創建成功")
        return True
        
    except Exception as e:
        print(f"❌ 格式轉換器創建失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_phase1_to_frontend_conversion():
    """測試 Phase 1 到前端格式轉換"""
    print("\n🧪 測試 Phase 1 到前端格式轉換...")
    
    try:
        from output_format_converter import create_leo_to_frontend_converter
        
        # Create sample LEO Phase 1 report
        sample_leo_report = {
            "phase1_completion_report": {
                "timestamp": "2025-08-15T14:19:15.801098+00:00",
                "pipeline_statistics": {
                    "start_time": "2025-08-15T14:19:15.413182+00:00",
                    "stages_completed": 4,
                    "total_stages": 4
                },
                "final_results": {
                    "optimal_satellite_pools": {
                        "starlink_count": 5,
                        "oneweb_count": 3,
                        "total_count": 8,
                        "visibility_compliance": 0.85,
                        "temporal_distribution": 0.75,
                        "signal_quality": 0.9
                    },
                    "handover_events": {
                        "total_events": 768,
                        "a4_events": 768,
                        "a5_events": 0,
                        "d2_events": 0
                    }
                }
            }
        }
        
        # Convert to frontend format
        converter = create_leo_to_frontend_converter()
        frontend_data = converter.convert_phase1_report_to_frontend(sample_leo_report)
        
        # Validate conversion
        if not frontend_data:
            print("❌ 轉換結果為空")
            return False
        
        # Check required structure
        if 'metadata' not in frontend_data or 'satellites' not in frontend_data:
            print("❌ 轉換結果缺少必要結構")
            return False
        
        metadata = frontend_data['metadata']
        satellites = frontend_data['satellites']
        
        print("✅ Phase 1 到前端格式轉換成功")
        print(f"   - 衛星數量: {len(satellites)}")
        print(f"   - 時間跨度: {metadata['time_span_minutes']} 分鐘")
        print(f"   - 數據點: {metadata['total_time_points']} 個")
        print(f"   - 參考位置: NTPU ({metadata['reference_location']['latitude']}, {metadata['reference_location']['longitude']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 到前端格式轉換失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_satellite_data_structure():
    """測試衛星數據結構"""
    print("\n🧪 測試衛星數據結構...")
    
    try:
        from output_format_converter import create_leo_to_frontend_converter
        
        sample_leo_report = {
            "phase1_completion_report": {
                "timestamp": "2025-08-15T14:19:15.801098+00:00",
                "final_results": {
                    "optimal_satellite_pools": {
                        "starlink_count": 2,
                        "oneweb_count": 1,
                        "total_count": 3
                    },
                    "handover_events": {
                        "total_events": 100
                    }
                }
            }
        }
        
        converter = create_leo_to_frontend_converter()
        frontend_data = converter.convert_phase1_report_to_frontend(sample_leo_report)
        
        satellites = frontend_data['satellites']
        
        # Test first satellite structure
        if not satellites:
            print("❌ 沒有衛星數據")
            return False
        
        first_sat = satellites[0]
        required_keys = ['norad_id', 'name', 'constellation', 'mrl_distances', 'orbital_positions']
        
        for key in required_keys:
            if key not in first_sat:
                print(f"❌ 衛星數據缺少 {key}")
                return False
        
        # Check mrl_distances structure
        mrl_distances = first_sat['mrl_distances']
        if not isinstance(mrl_distances, list) or len(mrl_distances) == 0:
            print("❌ mrl_distances 結構不正確")
            return False
        
        # Check orbital_positions structure
        orbital_positions = first_sat['orbital_positions']
        if not isinstance(orbital_positions, list) or len(orbital_positions) == 0:
            print("❌ orbital_positions 結構不正確")
            return False
        
        first_pos = orbital_positions[0]
        pos_required_keys = ['latitude', 'longitude', 'altitude']
        for key in pos_required_keys:
            if key not in first_pos:
                print(f"❌ 軌道位置缺少 {key}")
                return False
        
        print("✅ 衛星數據結構測試通過")
        print(f"   - 第一個衛星: {first_sat['name']} (NORAD: {first_sat['norad_id']})")
        print(f"   - 星座: {first_sat['constellation']}")
        print(f"   - MRL 距離點數: {len(mrl_distances)}")
        print(f"   - 軌道位置點數: {len(orbital_positions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 衛星數據結構測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_constellation_filtering():
    """測試星座過濾功能"""
    print("\n🧪 測試星座過濾功能...")
    
    try:
        from output_format_converter import create_leo_to_frontend_converter
        
        sample_leo_report = {
            "phase1_completion_report": {
                "timestamp": "2025-08-15T14:19:15.801098+00:00",
                "final_results": {
                    "optimal_satellite_pools": {
                        "starlink_count": 3,
                        "oneweb_count": 2,
                        "total_count": 5
                    },
                    "handover_events": {
                        "total_events": 200
                    }
                }
            }
        }
        
        converter = create_leo_to_frontend_converter()
        mixed_data = converter.convert_phase1_report_to_frontend(sample_leo_report)
        
        # Test Starlink filtering
        starlink_data = converter.convert_to_constellation_specific(mixed_data, 'starlink')
        starlink_satellites = [sat for sat in starlink_data['satellites'] if sat['constellation'] == 'starlink']
        
        if len(starlink_satellites) != 3:
            print(f"❌ Starlink 過濾不正確: 期望 3, 實際 {len(starlink_satellites)}")
            return False
        
        # Test OneWeb filtering
        oneweb_data = converter.convert_to_constellation_specific(mixed_data, 'oneweb')
        oneweb_satellites = [sat for sat in oneweb_data['satellites'] if sat['constellation'] == 'oneweb']
        
        if len(oneweb_satellites) != 2:
            print(f"❌ OneWeb 過濾不正確: 期望 2, 實際 {len(oneweb_satellites)}")
            return False
        
        print("✅ 星座過濾功能測試通過")
        print(f"   - Starlink 衛星: {len(starlink_satellites)} 顆")
        print(f"   - OneWeb 衛星: {len(oneweb_satellites)} 顆")
        
        return True
        
    except Exception as e:
        print(f"❌ 星座過濾功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_format_validation():
    """測試格式驗證功能"""
    print("\n🧪 測試格式驗證功能...")
    
    try:
        from output_format_converter import create_leo_to_frontend_converter
        
        converter = create_leo_to_frontend_converter()
        
        # Test valid format
        valid_format = {
            'metadata': {
                'computation_time': '2025-08-15T14:19:15.801098+00:00',
                'constellation': 'mixed',
                'time_span_minutes': 120,
                'reference_location': {
                    'latitude': 24.9441667,
                    'longitude': 121.3713889
                },
                'satellites_processed': 2
            },
            'satellites': [
                {
                    'norad_id': 44000,
                    'name': 'STARLINK-1000',
                    'constellation': 'starlink',
                    'mrl_distances': [1000.0, 1100.0, 1200.0]
                }
            ]
        }
        
        if not converter.validate_frontend_format(valid_format):
            print("❌ 有效格式驗證失敗")
            return False
        
        # Test invalid format (missing required key)
        invalid_format = {
            'metadata': {
                'computation_time': '2025-08-15T14:19:15.801098+00:00'
                # Missing other required keys
            },
            'satellites': []
        }
        
        if converter.validate_frontend_format(invalid_format):
            print("❌ 無效格式驗證應該失敗但通過了")
            return False
        
        print("✅ 格式驗證功能測試通過")
        print("   - 有效格式: 通過驗證")
        print("   - 無效格式: 正確拒絕")
        
        return True
        
    except Exception as e:
        print(f"❌ 格式驗證功能測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_phase1_conversion():
    """測試真實 Phase 1 數據轉換"""
    print("\n🧪 測試真實 Phase 1 數據轉換...")
    
    # Check if real phase1 data exists
    phase1_file = "/tmp/p01_v2_verification/phase1_final_report.json"
    
    if not os.path.exists(phase1_file):
        print("⚠️  真實 Phase 1 數據不存在，跳過此測試")
        return True
    
    try:
        from output_format_converter import convert_phase1_to_frontend_format
        
        # Convert real data
        output_file = "/tmp/test_frontend_output.json"
        success = convert_phase1_to_frontend_format(
            phase1_file,
            output_file
        )
        
        if not success:
            print("❌ 真實 Phase 1 數據轉換失敗")
            return False
        
        # Verify output file
        if not os.path.exists(output_file):
            print("❌ 輸出文件未生成")
            return False
        
        # Load and check output
        with open(output_file, 'r', encoding='utf-8') as f:
            frontend_data = json.load(f)
        
        if 'metadata' not in frontend_data or 'satellites' not in frontend_data:
            print("❌ 輸出文件格式不正確")
            return False
        
        print("✅ 真實 Phase 1 數據轉換成功")
        print(f"   - 輸出文件: {output_file}")
        print(f"   - 衛星數量: {len(frontend_data['satellites'])}")
        
        # Clean up
        os.remove(output_file)
        
        return True
        
    except Exception as e:
        print(f"❌ 真實 Phase 1 數據轉換失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("🚀 P0.3 輸出格式對接 - 整合測試")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("格式轉換器創建", test_format_converter_creation()))
    test_results.append(("Phase1到前端轉換", test_phase1_to_frontend_conversion()))
    test_results.append(("衛星數據結構", test_satellite_data_structure()))
    test_results.append(("星座過濾功能", test_constellation_filtering()))
    test_results.append(("格式驗證功能", test_format_validation()))
    test_results.append(("真實數據轉換", test_real_phase1_conversion()))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 P0.3 測試結果總結:")
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
        print("\n🎉 P0.3 輸出格式對接 - 全部測試通過！")
        print("✅ LEO Restructure 數據已可轉換為前端立體圖格式")
        print("✅ 準備進行 P0.4 系統替換與驗證")
        return True
    else:
        print(f"\n⚠️  P0.3 輸出格式對接 - 需要修復 {total_tests - passed_tests} 個問題")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)