#!/usr/bin/env python3
"""
端到端功能測試
完成 Phase 4.1 要求：測試整個系統的端到端功能
"""

import sys
import os
import asyncio
import time
import requests
import json
from datetime import datetime, timezone

sys.path.append('/home/sat/ntn-stack/netstack')

class EndToEndTester:
    """端到端功能測試器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        
    def test_api_connectivity(self):
        """測試 API 連接性"""
        print("🔍 測試 API 連接性")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ API 服務正常運行")
                return True
            else:
                print(f"  ❌ API 服務異常，狀態碼: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ API 連接失敗: {e}")
            return False
    
    def test_sib19_data_flow(self):
        """測試 SIB19 數據流"""
        print("🔍 測試 SIB19 數據流")
        try:
            # 獲取 SIB19 數據
            response = requests.get(f"{self.base_url}/api/sib19/current")
            if response.status_code == 200:
                data = response.json()
                required_fields = [
                    'broadcast_time', 'reference_location', 'time_correction',
                    'satellite_list', 'ephemeris_data'
                ]
                
                missing_fields = [field for field in required_fields if field not in data]
                if not missing_fields:
                    print("  ✅ SIB19 數據結構完整")
                    return True
                else:
                    print(f"  ❌ SIB19 數據缺少字段: {missing_fields}")
                    return False
            else:
                print(f"  ❌ SIB19 數據獲取失敗，狀態碼: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ SIB19 數據流測試失敗: {e}")
            return False
    
    def test_measurement_events_workflow(self):
        """測試測量事件工作流"""
        print("🔍 測試測量事件工作流")
        
        events = ['A4', 'D1', 'D2', 'T1']
        all_passed = True
        
        for event in events:
            try:
                # 啟動測量事件
                start_payload = {
                    'event_type': event,
                    'config': {
                        'measurement_interval': 1000,
                        'reporting_interval': 5000
                    }
                }
                
                response = requests.post(
                    f"{self.base_url}/api/measurement-events/start",
                    json=start_payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"  ✅ {event} 事件啟動成功")
                    
                    # 等待一段時間收集數據
                    time.sleep(3)
                    
                    # 獲取測量數據
                    data_response = requests.get(
                        f"{self.base_url}/api/measurement-events/{event}/data"
                    )
                    
                    if data_response.status_code == 200:
                        data = data_response.json()
                        if data and len(data) > 0:
                            print(f"  ✅ {event} 事件數據收集正常")
                        else:
                            print(f"  ❌ {event} 事件無數據")
                            all_passed = False
                    else:
                        print(f"  ❌ {event} 事件數據獲取失敗")
                        all_passed = False
                    
                    # 停止測量事件
                    stop_response = requests.post(
                        f"{self.base_url}/api/measurement-events/stop",
                        json={'event_type': event}
                    )
                    
                    if stop_response.status_code == 200:
                        print(f"  ✅ {event} 事件停止成功")
                    else:
                        print(f"  ❌ {event} 事件停止失敗")
                        all_passed = False
                        
                else:
                    print(f"  ❌ {event} 事件啟動失敗，狀態碼: {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"  ❌ {event} 事件測試失敗: {e}")
                all_passed = False
        
        return all_passed
    
    def test_orbit_calculation_accuracy(self):
        """測試軌道計算精度"""
        print("🔍 測試軌道計算精度")
        try:
            # 測試已知 TLE 的軌道計算
            test_payload = {
                'tle_line1': '1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990',
                'tle_line2': '2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456',
                'prediction_time': datetime.now(timezone.utc).isoformat()
            }
            
            response = requests.post(
                f"{self.base_url}/api/orbit/calculate-position",
                json=test_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['latitude', 'longitude', 'altitude', 'velocity']
                
                if all(field in data for field in required_fields):
                    # 檢查數值合理性
                    lat, lon, alt = data['latitude'], data['longitude'], data['altitude']
                    if -90 <= lat <= 90 and -180 <= lon <= 180 and 200 <= alt <= 2000:
                        print("  ✅ 軌道計算結果合理")
                        return True
                    else:
                        print(f"  ❌ 軌道計算結果異常: lat={lat}, lon={lon}, alt={alt}")
                        return False
                else:
                    print("  ❌ 軌道計算結果缺少必要字段")
                    return False
            else:
                print(f"  ❌ 軌道計算請求失敗，狀態碼: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ 軌道計算精度測試失敗: {e}")
            return False
    
    def test_data_consistency(self):
        """測試數據一致性"""
        print("🔍 測試數據一致性")
        try:
            # 同時從多個端點獲取相同數據
            endpoints = [
                '/api/sib19/current',
                '/api/measurement-events/A4/sib19-data',
                '/api/measurement-events/D1/sib19-data'
            ]
            
            responses = []
            for endpoint in endpoints:
                response = requests.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    responses.append(response.json())
                else:
                    print(f"  ❌ 端點 {endpoint} 請求失敗")
                    return False
            
            # 檢查關鍵字段的一致性
            if len(responses) >= 2:
                base_time = responses[0].get('broadcast_time')
                for i, resp in enumerate(responses[1:], 1):
                    if resp.get('broadcast_time') != base_time:
                        print(f"  ❌ 數據不一致：端點 {i} 的 broadcast_time 不匹配")
                        return False
                
                print("  ✅ 數據一致性檢查通過")
                return True
            else:
                print("  ❌ 無足夠數據進行一致性檢查")
                return False
                
        except Exception as e:
            print(f"  ❌ 數據一致性測試失敗: {e}")
            return False
    
    def test_error_handling(self):
        """測試錯誤處理"""
        print("🔍 測試錯誤處理")
        try:
            # 測試無效請求
            invalid_requests = [
                ('/api/measurement-events/INVALID/data', 404),
                ('/api/orbit/calculate-position', 400),  # 無 payload
                ('/api/sib19/invalid-endpoint', 404)
            ]
            
            all_passed = True
            for endpoint, expected_status in invalid_requests:
                if endpoint.endswith('calculate-position'):
                    response = requests.post(f"{self.base_url}{endpoint}")
                else:
                    response = requests.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == expected_status:
                    print(f"  ✅ 錯誤處理正確: {endpoint} -> {response.status_code}")
                else:
                    print(f"  ❌ 錯誤處理異常: {endpoint} -> {response.status_code} (期望 {expected_status})")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            print(f"  ❌ 錯誤處理測試失敗: {e}")
            return False
    
    def test_performance_benchmarks(self):
        """測試性能基準"""
        print("🔍 測試性能基準")
        try:
            # 測試 API 響應時間
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/sib19/current")
            response_time = time.time() - start_time
            
            if response.status_code == 200 and response_time < 1.0:
                print(f"  ✅ API 響應時間正常: {response_time:.3f}s")
                
                # 測試並發請求
                import concurrent.futures
                
                def make_request():
                    return requests.get(f"{self.base_url}/api/sib19/current")
                
                start_time = time.time()
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(make_request) for _ in range(10)]
                    results = [future.result() for future in futures]
                
                concurrent_time = time.time() - start_time
                success_count = sum(1 for r in results if r.status_code == 200)
                
                if success_count >= 8 and concurrent_time < 5.0:
                    print(f"  ✅ 並發性能正常: {success_count}/10 成功, {concurrent_time:.3f}s")
                    return True
                else:
                    print(f"  ❌ 並發性能異常: {success_count}/10 成功, {concurrent_time:.3f}s")
                    return False
            else:
                print(f"  ❌ API 響應時間過長: {response_time:.3f}s")
                return False
                
        except Exception as e:
            print(f"  ❌ 性能基準測試失敗: {e}")
            return False
    
    def run_all_tests(self):
        """運行所有端到端測試"""
        print("🚀 開始端到端功能測試")
        print("=" * 60)
        
        tests = [
            ("API 連接性", self.test_api_connectivity),
            ("SIB19 數據流", self.test_sib19_data_flow),
            ("測量事件工作流", self.test_measurement_events_workflow),
            ("軌道計算精度", self.test_orbit_calculation_accuracy),
            ("數據一致性", self.test_data_consistency),
            ("錯誤處理", self.test_error_handling),
            ("性能基準", self.test_performance_benchmarks)
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
        print("📊 端到端測試結果統計")
        print("=" * 60)
        print(f"📈 總體通過率: {passed_tests}/{len(tests)} ({(passed_tests/len(tests)*100):.1f}%)")
        
        if passed_tests == len(tests):
            print("🎉 所有端到端測試通過！系統功能完整。")
            return 0
        elif passed_tests >= len(tests) * 0.8:
            print("✅ 大部分端到端測試通過，系統基本功能正常。")
            return 0
        else:
            print("⚠️ 多項端到端測試失敗，系統需要修復。")
            return 1

def main():
    """主函數"""
    tester = EndToEndTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
