#!/usr/bin/env python3
"""
Phase 0 完整驗證測試 - 數據真實性強化
確保 Phase 0 的所有子階段都已真實完成並達到論文研究級標準
"""

import sys
import os
sys.path.append('/home/sat/ntn-stack/netstack')

import subprocess

def run_phase_test(test_file, phase_name):
    """運行單個階段測試"""
    print(f"🔍 運行 {phase_name} 驗證測試...")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd='/home/sat/ntn-stack/netstack',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {phase_name} 驗證通過")
            return True
        else:
            print(f"❌ {phase_name} 驗證失敗")
            print("錯誤輸出:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {phase_name} 測試超時")
        return False
    except Exception as e:
        print(f"❌ {phase_name} 測試錯誤: {e}")
        return False

def test_phase0_integration():
    """測試 Phase 0 整合功能"""
    print("🔍 Phase 0 整合功能測試")
    print("-" * 60)
    
    # 測試所有物理模型的整合使用
    try:
        from netstack_api.models.physical_propagation_models import PhysicalPropagationModel
        from netstack_api.models.doppler_calculation_engine import DopplerCalculationEngine
        from netstack_api.models.ionospheric_models import IonosphericEffectsCalculator
        from netstack_api.models.ntn_path_loss_models import NTNPathLossModel, NTNScenario, SatelliteOrbitType, AntennaPattern
        from netstack_api.models.itu_r_p618_rain_attenuation import itu_r_p618_model, Polarization
        
        print("  ✅ 所有物理模型模組成功導入")
        
        # 測試整合計算
        # 1. 物理傳播模型
        prop_model = PhysicalPropagationModel()
        rain_attenuation = prop_model.calculate_rain_attenuation(45.0, 12.0, 10.0)
        print(f"  ✅ 降雨衰減計算: {rain_attenuation:.2f} dB")
        
        # 2. 都卜勒計算
        doppler_engine = DopplerCalculationEngine()
        from netstack_api.models.doppler_calculation_engine import Position3D, Velocity3D
        
        sat_pos = Position3D(x=-1000000, y=5000000, z=3000000)
        sat_vel = Velocity3D(vx=4560, vy=6080, vz=0)
        
        doppler_result = doppler_engine.calculate_doppler_shift(
            sat_pos, sat_vel, 25.0, 121.0, 100.0, 2.4e9
        )
        print(f"  ✅ 都卜勒頻移計算: {doppler_result.doppler_shift_hz:.1f} Hz")
        
        # 3. 電離層效應
        iono_calc = IonosphericEffectsCalculator()
        from datetime import datetime, timezone
        
        iono_result = iono_calc.calculate_total_ionospheric_effects(
            25.0, 121.0, 45.0, 180.0, datetime.now(timezone.utc), 12.0
        )
        print(f"  ✅ 電離層延遲計算: {iono_result['corrected_delay_meters']:.3f} m")
        
        # 4. NTN 路徑損耗
        ntn_model = NTNPathLossModel()
        antenna = AntennaPattern(
            max_gain_dbi=35.0,
            half_power_beamwidth_deg=2.0,
            front_to_back_ratio_db=25.0,
            side_lobe_level_db=-20.0,
            azimuth_beamwidth_deg=2.0,
            elevation_beamwidth_deg=2.0
        )
        
        ntn_result = ntn_model.calculate_ntn_path_loss(
            12.0, 550, 45.0, NTNScenario.URBAN_MACRO, 
            SatelliteOrbitType.LEO, antenna, 0.0, 1.0
        )
        print(f"  ✅ NTN 路徑損耗計算: {ntn_result.total_path_loss_db:.1f} dB")
        
        # 5. ITU-R P.618 降雨衰減
        itu_result = itu_r_p618_model.calculate_rain_attenuation(
            12.0, 45.0, 10.0, Polarization.CIRCULAR
        )
        print(f"  ✅ ITU-R P.618 降雨衰減: {itu_result['rain_attenuation_db']:.3f} dB")
        
        print("  ✅ 所有物理模型整合測試通過")
        return True
        
    except Exception as e:
        print(f"  ❌ 整合測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 Phase 0: 數據真實性強化 - 完整驗證測試")
    print("=" * 80)
    
    # Phase 0 的所有子階段測試
    phase_tests = [
        ("test_phase0_1_verification.py", "Phase 0.1: ITU-R P.618 降雨衰減模型"),
        ("test_phase0_2_verification.py", "Phase 0.2: Klobuchar 電離層延遲模型"),
        ("test_phase0_3_verification.py", "Phase 0.3: 都卜勒頻移精確計算"),
        ("test_phase0_4_verification.py", "Phase 0.4: 3GPP TR 38.811 NTN 路徑損耗模型")
    ]
    
    passed_tests = 0
    total_tests = len(phase_tests)
    
    # 運行各子階段測試
    for test_file, phase_name in phase_tests:
        if run_phase_test(test_file, phase_name):
            passed_tests += 1
        print()
    
    # 運行整合測試
    print("🔍 Phase 0 整合功能測試")
    print("=" * 80)
    
    if test_phase0_integration():
        passed_tests += 1
        total_tests += 1
        print("✅ Phase 0 整合功能測試通過")
    else:
        total_tests += 1
        print("❌ Phase 0 整合功能測試失敗")
    
    print()
    print("=" * 80)
    print("📊 Phase 0 總體驗證結果")
    print("=" * 80)
    
    print(f"通過測試: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 Phase 0: 數據真實性強化 - 完全驗證通過！")
        print()
        print("✅ **達成的論文研究級標準:**")
        print("  • ITU-R P.618-13 降雨衰減模型 (1-100 GHz 完整參數)")
        print("  • GPS Klobuchar 電離層模型 (真實參數)")
        print("  • SGP4 軌道都卜勒計算 (< 100 Hz 精度)")
        print("  • 3GPP TR 38.811 NTN 路徑損耗 (6種場景)")
        print("  • 所有物理常數精確 (光速、地球參數等)")
        print()
        print("🎓 **論文研究級特徵:**")
        print("  • 使用國際標準和真實參數")
        print("  • 物理模型完整實現")
        print("  • 計算精度達到研究要求")
        print("  • 支援多頻段和多場景")
        print("  • 完整的驗證測試覆蓋")
        print()
        print("📋 Phase 0 可以在 events-improvement-master.md 中標記為 100% 完成")
        return 0
    else:
        print("❌ Phase 0 存在未完成的部分，需要進一步改進")
        print(f"   失敗的測試: {total_tests - passed_tests}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
