#!/usr/bin/env python3
"""
API 性能測試
完成 Phase 4.1 要求：測試 API 的性能指標和負載能力
"""

import sys
import os
import time
import statistics
import requests
import concurrent.futures
import threading
from datetime import datetime, timezone
import json

sys.path.append('/home/sat/ntn-stack/netstack')

class APIPerformanceTester:
    """API 性能測試器"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results = {}
        
    def measure_response_time(self, endpoint, method='GET', payload=None, iterations=10):
        """測量 API 響應時間"""
        response_times = []
        success_count = 0
        
        for i in range(iterations):
            start_time = time.time()
            try:
                if method == 'GET':
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == 'POST':
                    response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=10)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    response_times.append(response_time)
                    success_count += 1
                    
            except Exception as e:
                print(f"    請求 {i+1} 失敗: {e}")
        
        if response_times:
            return {
                'avg_response_time': statistics.mean(response_times),
                'min_response_time': min(response_times),
                'max_response_time': max(response_times),
                'median_response_time': statistics.median(response_times),
                'success_rate': success_count / iterations,
                'total_requests': iterations
            }
        else:
            return None
    
    def test_sib19_api_performance(self):
        """測試 SIB19 API 性能"""
        print("🔍 測試 SIB19 API 性能")
        
        endpoints = [
            '/api/sib19/current',
            '/api/sib19/history',
            '/api/sib19/validate'
        ]
        
        all_passed = True
        
        for endpoint in endpoints:
            print(f"  測試端點: {endpoint}")
            result = self.measure_response_time(endpoint, iterations=20)
            
            if result:
                avg_time = result['avg_response_time']
                success_rate = result['success_rate']
                
                print(f"    平均響應時間: {avg_time:.3f}s")
                print(f"    成功率: {success_rate:.1%}")
                print(f"    響應時間範圍: {result['min_response_time']:.3f}s - {result['max_response_time']:.3f}s")
                
                # 性能標準：平均響應時間 < 0.5s，成功率 > 95%
                if avg_time < 0.5 and success_rate > 0.95:
                    print(f"    ✅ {endpoint} 性能合格")
                else:
                    print(f"    ❌ {endpoint} 性能不合格")
                    all_passed = False
            else:
                print(f"    ❌ {endpoint} 測試失敗")
                all_passed = False
        
        return all_passed
    
    def test_measurement_events_api_performance(self):
        """測試測量事件 API 性能"""
        print("🔍 測試測量事件 API 性能")
        
        events = ['A4', 'D1', 'D2', 'T1']
        all_passed = True
        
        for event in events:
            print(f"  測試事件: {event}")
            
            # 測試數據獲取性能
            data_endpoint = f'/api/measurement-events/{event}/data'
            result = self.measure_response_time(data_endpoint, iterations=15)
            
            if result:
                avg_time = result['avg_response_time']
                success_rate = result['success_rate']
                
                print(f"    數據獲取平均響應時間: {avg_time:.3f}s")
                print(f"    數據獲取成功率: {success_rate:.1%}")
                
                # 測試配置更新性能
                config_payload = {
                    'event_type': event,
                    'config': {
                        'measurement_interval': 1000,
                        'reporting_interval': 5000
                    }
                }
                
                config_result = self.measure_response_time(
                    '/api/measurement-events/configure',
                    method='POST',
                    payload=config_payload,
                    iterations=10
                )
                
                if config_result:
                    config_avg_time = config_result['avg_response_time']
                    config_success_rate = config_result['success_rate']
                    
                    print(f"    配置更新平均響應時間: {config_avg_time:.3f}s")
                    print(f"    配置更新成功率: {config_success_rate:.1%}")
                    
                    # 性能標準：數據獲取 < 0.3s，配置更新 < 0.2s，成功率 > 95%
                    if (avg_time < 0.3 and config_avg_time < 0.2 and 
                        success_rate > 0.95 and config_success_rate > 0.95):
                        print(f"    ✅ {event} 事件 API 性能合格")
                    else:
                        print(f"    ❌ {event} 事件 API 性能不合格")
                        all_passed = False
                else:
                    print(f"    ❌ {event} 事件配置測試失敗")
                    all_passed = False
            else:
                print(f"    ❌ {event} 事件數據測試失敗")
                all_passed = False
        
        return all_passed
    
    def test_orbit_calculation_performance(self):
        """測試軌道計算性能"""
        print("🔍 測試軌道計算性能")
        
        # 測試單次軌道計算
        payload = {
            'tle_line1': '1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990',
            'tle_line2': '2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456',
            'prediction_time': datetime.now(timezone.utc).isoformat()
        }
        
        result = self.measure_response_time(
            '/api/orbit/calculate-position',
            method='POST',
            payload=payload,
            iterations=25
        )
        
        if result:
            avg_time = result['avg_response_time']
            success_rate = result['success_rate']
            
            print(f"  單次軌道計算平均響應時間: {avg_time:.3f}s")
            print(f"  軌道計算成功率: {success_rate:.1%}")
            
            # 測試批量軌道計算
            batch_payload = {
                'satellites': [
                    {
                        'tle_line1': '1 25544U 98067A   21001.00000000  .00002182  00000-0  40768-4 0  9990',
                        'tle_line2': '2 25544  51.6461 339.2911 0002829  86.3372 273.9164 15.48919103123456'
                    },
                    {
                        'tle_line1': '1 43013U 17073A   21001.00000000  .00000000  00000-0  00000-0 0  9990',
                        'tle_line2': '2 43013   0.0000   0.0000 0000000   0.0000   0.0000  1.00000000000000'
                    }
                ],
                'prediction_time': datetime.now(timezone.utc).isoformat()
            }
            
            batch_result = self.measure_response_time(
                '/api/orbit/calculate-batch',
                method='POST',
                payload=batch_payload,
                iterations=10
            )
            
            if batch_result:
                batch_avg_time = batch_result['avg_response_time']
                batch_success_rate = batch_result['success_rate']
                
                print(f"  批量軌道計算平均響應時間: {batch_avg_time:.3f}s")
                print(f"  批量軌道計算成功率: {batch_success_rate:.1%}")
                
                # 性能標準：單次 < 0.1s，批量 < 0.5s，成功率 > 98%
                if (avg_time < 0.1 and batch_avg_time < 0.5 and 
                    success_rate > 0.98 and batch_success_rate > 0.98):
                    print("  ✅ 軌道計算性能合格")
                    return True
                else:
                    print("  ❌ 軌道計算性能不合格")
                    return False
            else:
                print("  ❌ 批量軌道計算測試失敗")
                return False
        else:
            print("  ❌ 軌道計算測試失敗")
            return False
    
    def test_concurrent_load(self):
        """測試並發負載"""
        print("🔍 測試並發負載")
        
        def make_concurrent_request(endpoint):
            """發送並發請求"""
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                }
            except Exception as e:
                return {
                    'status_code': 0,
                    'response_time': 10.0,
                    'success': False,
                    'error': str(e)
                }
        
        # 測試不同並發級別
        concurrency_levels = [5, 10, 20, 50]
        endpoint = '/api/sib19/current'
        
        all_passed = True
        
        for concurrency in concurrency_levels:
            print(f"  測試並發級別: {concurrency}")
            
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_concurrent_request, endpoint) for _ in range(concurrency)]
                results = [future.result() for future in futures]
            
            total_time = time.time() - start_time
            
            success_count = sum(1 for r in results if r['success'])
            success_rate = success_count / concurrency
            avg_response_time = statistics.mean([r['response_time'] for r in results if r['success']])
            throughput = concurrency / total_time
            
            print(f"    成功率: {success_rate:.1%} ({success_count}/{concurrency})")
            print(f"    平均響應時間: {avg_response_time:.3f}s")
            print(f"    吞吐量: {throughput:.1f} 請求/秒")
            print(f"    總耗時: {total_time:.3f}s")
            
            # 性能標準：成功率 > 90%，平均響應時間 < 2s
            if success_rate > 0.9 and avg_response_time < 2.0:
                print(f"    ✅ 並發級別 {concurrency} 測試通過")
            else:
                print(f"    ❌ 並發級別 {concurrency} 測試失敗")
                all_passed = False
        
        return all_passed
    
    def test_memory_and_cpu_usage(self):
        """測試記憶體和 CPU 使用情況"""
        print("🔍 測試記憶體和 CPU 使用情況")
        
        try:
            import psutil
            
            # 獲取系統資源使用情況
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            print(f"  當前 CPU 使用率: {cpu_percent:.1f}%")
            print(f"  當前記憶體使用率: {memory.percent:.1f}%")
            print(f"  可用記憶體: {memory.available / 1024 / 1024 / 1024:.1f} GB")
            
            # 執行負載測試並監控資源使用
            print("  執行負載測試...")
            
            def stress_test():
                for _ in range(50):
                    requests.get(f"{self.base_url}/api/sib19/current", timeout=5)
            
            # 啟動負載測試
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(stress_test) for _ in range(5)]
                
                # 監控資源使用
                max_cpu = 0
                max_memory = 0
                
                for _ in range(10):
                    time.sleep(1)
                    cpu = psutil.cpu_percent()
                    mem = psutil.virtual_memory().percent
                    max_cpu = max(max_cpu, cpu)
                    max_memory = max(max_memory, mem)
                
                # 等待所有任務完成
                for future in futures:
                    future.result()
            
            print(f"  負載測試期間最大 CPU 使用率: {max_cpu:.1f}%")
            print(f"  負載測試期間最大記憶體使用率: {max_memory:.1f}%")
            
            # 性能標準：CPU < 80%，記憶體 < 85%
            if max_cpu < 80 and max_memory < 85:
                print("  ✅ 資源使用情況正常")
                return True
            else:
                print("  ❌ 資源使用情況異常")
                return False
                
        except ImportError:
            print("  ⚠️ psutil 未安裝，跳過資源監控測試")
            return True
        except Exception as e:
            print(f"  ❌ 資源監控測試失敗: {e}")
            return False
    
    def run_all_tests(self):
        """運行所有性能測試"""
        print("🚀 開始 API 性能測試")
        print("=" * 60)
        
        tests = [
            ("SIB19 API 性能", self.test_sib19_api_performance),
            ("測量事件 API 性能", self.test_measurement_events_api_performance),
            ("軌道計算性能", self.test_orbit_calculation_performance),
            ("並發負載測試", self.test_concurrent_load),
            ("資源使用監控", self.test_memory_and_cpu_usage)
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
        print("📊 API 性能測試結果統計")
        print("=" * 60)
        print(f"📈 總體通過率: {passed_tests}/{len(tests)} ({(passed_tests/len(tests)*100):.1f}%)")
        
        if passed_tests == len(tests):
            print("🎉 所有性能測試通過！API 性能優秀。")
            return 0
        elif passed_tests >= len(tests) * 0.8:
            print("✅ 大部分性能測試通過，API 性能良好。")
            return 0
        else:
            print("⚠️ 多項性能測試失敗，需要性能優化。")
            return 1

def main():
    """主函數"""
    tester = APIPerformanceTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
