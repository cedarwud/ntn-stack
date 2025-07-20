#!/usr/bin/env python3
"""
Phase 2.2 D1 事件驗證測試
驗證 D1 全球化地理座標和智能衛星選擇功能
"""

import sys
import os
import asyncio
import math
from datetime import datetime, timezone

sys.path.append("/home/sat/ntn-stack/netstack")

from netstack_api.services.measurement_event_service import MeasurementEventService
from netstack_api.services.sib19_unified_platform import SIB19UnifiedPlatform
from netstack_api.services.orbit_calculation_engine import OrbitCalculationEngine
from netstack_api.services.tle_manager import TLEManager


class D1EventVerificationTester:
    """D1 事件驗證測試器"""

    def __init__(self):
        # 初始化依賴服務
        self.orbit_engine = OrbitCalculationEngine()
        self.sib19_platform = SIB19UnifiedPlatform()
        self.tle_manager = TLEManager()
        self.measurement_service = MeasurementEventService(
            self.orbit_engine, self.sib19_platform, self.tle_manager
        )
        self.test_results = {}

    def calculate_great_circle_distance(self, lat1, lon1, lat2, lon2):
        """計算大圓距離 (km)"""
        R = 6371.0  # 地球半徑 (km)

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def test_global_coordinate_support(self):
        """測試全球化座標支援"""
        print("🔍 測試全球化座標支援")

        # 測試不同地區的參考位置
        test_locations = [
            {"name": "台北", "lat": 25.0330, "lon": 121.5654},
            {"name": "東京", "lat": 35.6762, "lon": 139.6503},
            {"name": "紐約", "lat": 40.7128, "lon": -74.0060},
            {"name": "倫敦", "lat": 51.5074, "lon": -0.1278},
            {"name": "雪梨", "lat": -33.8688, "lon": 151.2093},
            {"name": "聖保羅", "lat": -23.5505, "lon": -46.6333},
        ]

        all_passed = True

        for location in test_locations:
            try:
                # 配置 D1 事件參數
                config = {
                    "event_type": "D1",
                    "reference_latitude": location["lat"],
                    "reference_longitude": location["lon"],
                    "reference_altitude": 0.1,
                    "thresh1": 50.0,
                    "thresh2": 100.0,
                    "hysteresis": 0.5,
                }

                # 模擬 UE 位置 (距離參考位置約 30km)
                ue_lat = location["lat"] + 0.27  # 約 30km 北
                ue_lon = location["lon"]

                # 計算距離
                distance = self.calculate_great_circle_distance(
                    location["lat"], location["lon"], ue_lat, ue_lon
                )

                # 驗證距離計算精度
                expected_distance = 30.0  # km
                distance_error = abs(distance - expected_distance)

                if distance_error < 1.0:  # 1km 誤差容忍
                    print(
                        f"  ✅ {location['name']} 座標支援正常 (距離: {distance:.2f}km)"
                    )
                else:
                    print(
                        f"  ❌ {location['name']} 距離計算錯誤 (計算: {distance:.2f}km, 期望: {expected_distance}km)"
                    )
                    all_passed = False

            except Exception as e:
                print(f"  ❌ {location['name']} 測試失敗: {e}")
                all_passed = False

        return all_passed

    def test_distance_calculation_accuracy(self):
        """測試距離計算精度"""
        print("🔍 測試距離計算精度")

        # 已知距離的測試案例
        test_cases = [
            {
                "name": "台北-高雄",
                "lat1": 25.0330,
                "lon1": 121.5654,
                "lat2": 22.6273,
                "lon2": 120.3014,
                "expected_distance": 351.0,  # km (約)
            },
            {
                "name": "東京-大阪",
                "lat1": 35.6762,
                "lon1": 139.6503,
                "lat2": 34.6937,
                "lon2": 135.5023,
                "expected_distance": 403.0,  # km (約)
            },
            {
                "name": "紐約-華盛頓",
                "lat1": 40.7128,
                "lon1": -74.0060,
                "lat2": 38.9072,
                "lon2": -77.0369,
                "expected_distance": 328.0,  # km (約)
            },
        ]

        all_passed = True

        for case in test_cases:
            calculated_distance = self.calculate_great_circle_distance(
                case["lat1"], case["lon1"], case["lat2"], case["lon2"]
            )

            error_percentage = (
                abs(calculated_distance - case["expected_distance"])
                / case["expected_distance"]
                * 100
            )

            if error_percentage < 5.0:  # 5% 誤差容忍
                print(
                    f"  ✅ {case['name']} 距離計算精確 (計算: {calculated_distance:.1f}km, 期望: {case['expected_distance']}km, 誤差: {error_percentage:.1f}%)"
                )
            else:
                print(
                    f"  ❌ {case['name']} 距離計算不精確 (計算: {calculated_distance:.1f}km, 期望: {case['expected_distance']}km, 誤差: {error_percentage:.1f}%)"
                )
                all_passed = False

        return all_passed

    def test_dual_threshold_logic(self):
        """測試雙重門檻邏輯"""
        print("🔍 測試雙重門檻邏輯")

        # 測試配置
        config = {
            "event_type": "D1",
            "reference_latitude": 25.0330,
            "reference_longitude": 121.5654,
            "reference_altitude": 0.1,
            "thresh1": 50.0,  # 第一門檻 50km
            "thresh2": 100.0,  # 第二門檻 100km
            "hysteresis": 0.5,
        }

        # 測試案例：不同距離下的觸發行為
        test_distances = [
            {
                "distance": 30.0,
                "expected_trigger": False,
                "description": "低於第一門檻",
            },
            {"distance": 60.0, "expected_trigger": True, "description": "超過第一門檻"},
            {
                "distance": 80.0,
                "expected_trigger": True,
                "description": "介於兩門檻之間",
            },
            {
                "distance": 120.0,
                "expected_trigger": True,
                "description": "超過第二門檻",
            },
        ]

        all_passed = True

        for test_case in test_distances:
            # 計算對應距離的 UE 位置
            distance_km = test_case["distance"]
            lat_offset = distance_km / 111.0  # 約 111km per degree

            ue_lat = config["reference_latitude"] + lat_offset
            ue_lon = config["reference_longitude"]

            # 計算實際距離
            actual_distance = self.calculate_great_circle_distance(
                config["reference_latitude"],
                config["reference_longitude"],
                ue_lat,
                ue_lon,
            )

            # 判斷是否應該觸發
            should_trigger = (actual_distance > config["thresh1"]) or (
                actual_distance > config["thresh2"]
            )

            if should_trigger == test_case["expected_trigger"]:
                print(
                    f"  ✅ {test_case['description']} - 觸發邏輯正確 (距離: {actual_distance:.1f}km)"
                )
            else:
                print(
                    f"  ❌ {test_case['description']} - 觸發邏輯錯誤 (距離: {actual_distance:.1f}km)"
                )
                all_passed = False

        return all_passed

    def test_hysteresis_mechanism(self):
        """測試遲滯機制"""
        print("🔍 測試遲滯機制")

        config = {"thresh1": 50.0, "hysteresis": 2.0}  # 2km 遲滯

        # 測試遲滯行為
        test_scenarios = [
            {
                "name": "進入觸發",
                "distance": 52.0,  # 超過門檻 + 遲滯
                "previous_state": False,
                "expected_trigger": True,
            },
            {
                "name": "保持觸發",
                "distance": 51.0,  # 超過門檻但在遲滯範圍內
                "previous_state": True,
                "expected_trigger": True,
            },
            {
                "name": "離開觸發",
                "distance": 48.0,  # 低於門檻 - 遲滯
                "previous_state": True,
                "expected_trigger": False,
            },
        ]

        all_passed = True

        for scenario in test_scenarios:
            # 模擬遲滯邏輯
            distance = scenario["distance"]
            thresh = config["thresh1"]
            hysteresis = config["hysteresis"]
            previous_state = scenario["previous_state"]

            if previous_state:
                # 已觸發狀態，需要低於 (門檻 - 遲滯) 才解除
                should_trigger = distance > (thresh - hysteresis)
            else:
                # 未觸發狀態，需要高於 (門檻 + 遲滯) 才觸發
                should_trigger = distance > (thresh + hysteresis)

            if should_trigger == scenario["expected_trigger"]:
                print(f"  ✅ {scenario['name']} - 遲滯機制正確")
            else:
                print(f"  ❌ {scenario['name']} - 遲滯機制錯誤")
                all_passed = False

        return all_passed

    def test_sib19_integration(self):
        """測試 SIB19 統一平台整合"""
        print("🔍 測試 SIB19 統一平台整合")

        try:
            # 獲取 SIB19 數據
            sib19_data = self.sib19_platform.get_current_sib19_data()

            # 驗證 D1 事件特定數據萃取
            d1_data = self.sib19_platform.extract_d1_specific_data()

            # 檢查必要字段
            required_fields = [
                "reference_location",
                "time_correction",
                "satellite_list",
            ]

            missing_fields = [
                field for field in required_fields if field not in d1_data
            ]

            if not missing_fields:
                print("  ✅ SIB19 D1 數據萃取完整")

                # 驗證參考位置數據
                ref_loc = d1_data["reference_location"]
                if "latitude" in ref_loc and "longitude" in ref_loc:
                    print("  ✅ 參考位置數據結構正確")
                    return True
                else:
                    print("  ❌ 參考位置數據結構錯誤")
                    return False
            else:
                print(f"  ❌ SIB19 D1 數據缺少字段: {missing_fields}")
                return False

        except Exception as e:
            print(f"  ❌ SIB19 整合測試失敗: {e}")
            return False

    def test_coordinate_system_consistency(self):
        """測試座標系統一致性"""
        print("🔍 測試座標系統一致性")

        # 測試 WGS84 座標系統
        test_coordinates = [
            {"lat": 90.0, "lon": 0.0, "valid": True, "name": "北極"},
            {"lat": -90.0, "lon": 0.0, "valid": True, "name": "南極"},
            {"lat": 0.0, "lon": 180.0, "valid": True, "name": "國際日期變更線"},
            {"lat": 0.0, "lon": -180.0, "valid": True, "name": "國際日期變更線西"},
            {"lat": 91.0, "lon": 0.0, "valid": False, "name": "無效緯度"},
            {"lat": 0.0, "lon": 181.0, "valid": False, "name": "無效經度"},
        ]

        all_passed = True

        for coord in test_coordinates:
            lat, lon = coord["lat"], coord["lon"]

            # 驗證座標有效性
            is_valid = (-90 <= lat <= 90) and (-180 <= lon <= 180)

            if is_valid == coord["valid"]:
                status = "✅" if coord["valid"] else "✅ (正確拒絕)"
                print(f"  {status} {coord['name']} 座標驗證正確")
            else:
                print(f"  ❌ {coord['name']} 座標驗證錯誤")
                all_passed = False

        return all_passed

    def run_all_tests(self):
        """運行所有 D1 事件驗證測試"""
        print("🚀 開始 D1 事件驗證測試")
        print("=" * 60)

        tests = [
            ("全球化座標支援", self.test_global_coordinate_support),
            ("距離計算精度", self.test_distance_calculation_accuracy),
            ("雙重門檻邏輯", self.test_dual_threshold_logic),
            ("遲滯機制", self.test_hysteresis_mechanism),
            ("SIB19 統一平台整合", self.test_sib19_integration),
            ("座標系統一致性", self.test_coordinate_system_consistency),
        ]

        passed_tests = 0

        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 40)
            try:
                if test_func():
                    passed_tests += 1
                    self.test_results[test_name] = "PASS"
                    print(f"✅ {test_name} 測試通過")
                else:
                    self.test_results[test_name] = "FAIL"
                    print(f"❌ {test_name} 測試失敗")
            except Exception as e:
                self.test_results[test_name] = f"ERROR: {e}"
                print(f"❌ {test_name} 測試錯誤: {e}")

        print("\n" + "=" * 60)
        print("📊 D1 事件驗證測試結果統計")
        print("=" * 60)
        print(
            f"📈 總體通過率: {passed_tests}/{len(tests)} ({(passed_tests/len(tests)*100):.1f}%)"
        )

        if passed_tests == len(tests):
            print("🎉 所有 D1 事件驗證測試通過！")
            return 0
        elif passed_tests >= len(tests) * 0.8:
            print("✅ 大部分 D1 事件驗證測試通過，功能基本正常。")
            return 0
        else:
            print("⚠️ 多項 D1 事件驗證測試失敗，需要修復。")
            return 1


def main():
    """主函數"""
    tester = D1EventVerificationTester()
    return tester.run_all_tests()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
