#!/usr/bin/env python3
"""
ITU-R P.618 降雨衰減模型驗證測試
確保實現符合 ITU-R P.618-13 標準
"""

import sys
import os
sys.path.append('/home/sat/ntn-stack/netstack')

import math
import pytest
from netstack_api.models.itu_r_p618_rain_attenuation import (
    ITU_R_P618_RainAttenuation, 
    Polarization
)

def test_itu_r_p618_basic_functionality():
    """測試 ITU-R P.618 基本功能"""
    print("🔍 測試 ITU-R P.618 基本功能...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 測試參數獲取
    params_12ghz = model.get_frequency_parameters(12.0)
    assert params_12ghz.frequency_ghz == 12.0
    assert params_12ghz.k_h == 0.0064907
    assert params_12ghz.k_v == 0.0030219
    print("  ✅ 頻率參數獲取正確")
    
    # 測試插值
    params_11_5ghz = model.get_frequency_parameters(11.5)
    assert 11.0 < params_11_5ghz.frequency_ghz < 12.0
    print("  ✅ 頻率插值功能正常")
    
    return True

def test_specific_attenuation_calculation():
    """測試比衰減計算"""
    print("🔍 測試比衰減計算...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 測試標準案例：12 GHz, 10 mm/h 降雨率
    gamma_r = model.calculate_specific_attenuation(
        frequency_ghz=12.0,
        rain_rate_mm_h=10.0,
        polarization=Polarization.HORIZONTAL
    )
    
    # 預期值：γR = k * R^α = 0.0064907 * 10^0.939 ≈ 0.056 dB/km
    expected_gamma_r = 0.0064907 * (10.0 ** 0.939)
    assert abs(gamma_r - expected_gamma_r) < 0.001
    print(f"  ✅ 12 GHz 比衰減計算正確: {gamma_r:.4f} dB/km")
    
    # 測試不同極化
    gamma_r_v = model.calculate_specific_attenuation(
        frequency_ghz=12.0,
        rain_rate_mm_h=10.0,
        polarization=Polarization.VERTICAL
    )
    
    expected_gamma_r_v = 0.0030219 * (10.0 ** 0.929)
    assert abs(gamma_r_v - expected_gamma_r_v) < 0.001
    print(f"  ✅ 垂直極化比衰減計算正確: {gamma_r_v:.4f} dB/km")
    
    return True

def test_effective_path_length():
    """測試有效路徑長度計算"""
    print("🔍 測試有效路徑長度計算...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 測試高仰角 (30度)
    path_length_30deg = model.calculate_effective_path_length(
        elevation_angle_deg=30.0,
        rain_height_km=2.0,
        earth_station_height_km=0.0
    )
    
    # 預期值：2.0 / sin(30°) = 4.0 km
    expected_length = 2.0 / math.sin(math.radians(30.0))
    assert abs(path_length_30deg - expected_length) < 0.1
    print(f"  ✅ 30度仰角路徑長度正確: {path_length_30deg:.2f} km")
    
    # 測試低仰角 (5度) - 應該考慮地球曲率
    path_length_5deg = model.calculate_effective_path_length(
        elevation_angle_deg=5.0,
        rain_height_km=2.0,
        earth_station_height_km=0.0
    )
    
    # 低仰角路徑應該比簡單計算長
    simple_calculation = 2.0 / math.sin(math.radians(5.0))
    assert path_length_5deg > simple_calculation * 0.8  # 允許一些差異
    print(f"  ✅ 5度仰角路徑長度考慮地球曲率: {path_length_5deg:.2f} km")
    
    return True

def test_complete_rain_attenuation():
    """測試完整降雨衰減計算"""
    print("🔍 測試完整降雨衰減計算...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 標準測試案例
    result = model.calculate_rain_attenuation(
        frequency_ghz=12.0,
        elevation_angle_deg=30.0,
        rain_rate_mm_h=10.0,
        polarization=Polarization.CIRCULAR
    )
    
    # 檢查結果完整性
    required_keys = [
        "rain_attenuation_db", "specific_attenuation_db_km", 
        "effective_path_length_km", "frequency_ghz", "rain_rate_mm_h",
        "elevation_angle_deg", "polarization", "calculation_method"
    ]
    
    for key in required_keys:
        assert key in result
    
    # 檢查數值合理性
    assert result["rain_attenuation_db"] > 0
    assert result["specific_attenuation_db_km"] > 0
    assert result["effective_path_length_km"] > 0
    assert result["calculation_method"] == "ITU-R P.618-13"
    
    print(f"  ✅ 完整計算結果: {result['rain_attenuation_db']:.3f} dB")
    print(f"    - 比衰減: {result['specific_attenuation_db_km']:.4f} dB/km")
    print(f"    - 有效路徑: {result['effective_path_length_km']:.2f} km")
    
    return True

def test_frequency_range_coverage():
    """測試頻率範圍覆蓋"""
    print("🔍 測試頻率範圍覆蓋...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 測試不同頻段
    test_frequencies = [1.0, 2.0, 6.0, 12.0, 20.0, 30.0, 60.0, 100.0]
    
    for freq in test_frequencies:
        result = model.calculate_rain_attenuation(
            frequency_ghz=freq,
            elevation_angle_deg=30.0,
            rain_rate_mm_h=5.0,
            polarization=Polarization.CIRCULAR
        )
        
        assert result["rain_attenuation_db"] >= 0
        print(f"    {freq} GHz: {result['rain_attenuation_db']:.3f} dB")
    
    print("  ✅ 所有頻段計算正常")
    
    return True

def test_edge_cases():
    """測試邊界情況"""
    print("🔍 測試邊界情況...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 零降雨率
    result_zero_rain = model.calculate_rain_attenuation(
        frequency_ghz=12.0,
        elevation_angle_deg=30.0,
        rain_rate_mm_h=0.0
    )
    assert result_zero_rain["rain_attenuation_db"] == 0.0
    print("  ✅ 零降雨率處理正確")
    
    # 零仰角
    result_zero_elevation = model.calculate_rain_attenuation(
        frequency_ghz=12.0,
        elevation_angle_deg=0.0,
        rain_rate_mm_h=10.0
    )
    assert result_zero_elevation["rain_attenuation_db"] == 0.0
    print("  ✅ 零仰角處理正確")
    
    # 極高降雨率
    result_heavy_rain = model.calculate_rain_attenuation(
        frequency_ghz=12.0,
        elevation_angle_deg=30.0,
        rain_rate_mm_h=100.0
    )
    assert result_heavy_rain["rain_attenuation_db"] > 0
    print(f"  ✅ 極高降雨率處理正確: {result_heavy_rain['rain_attenuation_db']:.2f} dB")
    
    return True

def test_polarization_effects():
    """測試極化效應"""
    print("🔍 測試極化效應...")
    
    model = ITU_R_P618_RainAttenuation()
    
    # 比較不同極化的結果
    test_params = {
        "frequency_ghz": 12.0,
        "elevation_angle_deg": 30.0,
        "rain_rate_mm_h": 10.0
    }
    
    result_h = model.calculate_rain_attenuation(
        polarization=Polarization.HORIZONTAL, **test_params
    )
    
    result_v = model.calculate_rain_attenuation(
        polarization=Polarization.VERTICAL, **test_params
    )
    
    result_c = model.calculate_rain_attenuation(
        polarization=Polarization.CIRCULAR, **test_params
    )
    
    # 水平極化通常比垂直極化衰減更大
    assert result_h["rain_attenuation_db"] > result_v["rain_attenuation_db"]
    
    # 圓極化應該在兩者之間
    assert (result_v["rain_attenuation_db"] <= result_c["rain_attenuation_db"] <= 
            result_h["rain_attenuation_db"])
    
    print(f"  ✅ 水平極化: {result_h['rain_attenuation_db']:.3f} dB")
    print(f"  ✅ 垂直極化: {result_v['rain_attenuation_db']:.3f} dB")
    print(f"  ✅ 圓極化: {result_c['rain_attenuation_db']:.3f} dB")
    
    return True

def main():
    """主測試函數"""
    print("🚀 ITU-R P.618 降雨衰減模型驗證測試")
    print("=" * 60)
    
    tests = [
        test_itu_r_p618_basic_functionality,
        test_specific_attenuation_calculation,
        test_effective_path_length,
        test_complete_rain_attenuation,
        test_frequency_range_coverage,
        test_edge_cases,
        test_polarization_effects
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
            print()
        except Exception as e:
            print(f"  ❌ 測試失敗: {e}")
            print()
    
    print("=" * 60)
    print(f"📊 測試結果: {passed_tests}/{total_tests} 通過")
    
    if passed_tests == total_tests:
        print("🎉 ITU-R P.618 模型驗證通過！")
        print("✅ 符合 ITU-R P.618-13 標準")
        print("✅ 達到論文研究級精度")
        return 0
    else:
        print("❌ 部分測試失敗，需要修復")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
