"""
Phase 2 性能回歸測試 - 自動化性能基準測試

測試 Phase 1 和 Phase 2 實施後的系統性能：
- API 響應時間回歸測試
- 內存使用量回歸測試
- 並發處理能力回歸測試
- 數據庫查詢性能回歸測試
- 系統資源使用回歸測試
"""

import pytest
import sys
import os
import time
import requests
import psutil
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Tuple
import json

# 添加項目路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


@dataclass
class PerformanceBenchmark:
    """性能基準數據結構"""
    test_name: str
    response_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    throughput_rps: float
    timestamp: str


# Global benchmarks storage
performance_benchmarks = []

# Performance baselines
PERFORMANCE_BASELINES = {
    'api_health_check': {
        'max_response_time_ms': 100,
        'max_memory_usage_mb': 50,
        'max_cpu_usage_percent': 10,
        'min_success_rate': 0.99
    },
    'concurrent_requests': {
        'max_response_time_ms': 500,
        'max_memory_usage_mb': 100,
        'max_cpu_usage_percent': 30,
        'min_success_rate': 0.95,
        'min_throughput_rps': 20
    }
}


def measure_system_resources() -> Tuple[float, float]:
    """測量系統資源使用情況"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=0.1)
    return memory_mb, cpu_percent


def record_benchmark(benchmark: PerformanceBenchmark):
    """記錄性能基準"""
    performance_benchmarks.append(benchmark)


def validate_performance(test_name: str, metrics: Dict) -> bool:
    """驗證性能是否符合基準"""
    if test_name not in PERFORMANCE_BASELINES:
        return True
    
    baseline = PERFORMANCE_BASELINES[test_name]
    
    # 檢查響應時間
    if 'response_time_ms' in metrics and 'max_response_time_ms' in baseline:
        if metrics['response_time_ms'] > baseline['max_response_time_ms']:
            print(f"❌ {test_name} 響應時間回歸: {metrics['response_time_ms']:.1f}ms > {baseline['max_response_time_ms']}ms")
            return False
    
    # 檢查成功率
    if 'success_rate' in metrics and 'min_success_rate' in baseline:
        if metrics['success_rate'] < baseline['min_success_rate']:
            print(f"❌ {test_name} 成功率回歸: {metrics['success_rate']:.2f} < {baseline['min_success_rate']}")
            return False
    
    return True


class TestAPIPerformanceRegression:
    """API 性能回歸測試"""
    
    def setup_method(self):
        """測試方法設置"""
        self.api_base_url = "http://localhost:8080"
        self.simworld_url = "http://localhost:8888"
        self.session = requests.Session()
    
    def test_health_check_response_time_regression(self):
        """測試健康檢查響應時間回歸"""
        response_times = []
        success_count = 0
        
        # 執行多次測試獲得穩定數據
        for _ in range(10):
            start_time = time.time()
            memory_before, cpu_before = measure_system_resources()
            
            try:
                response = self.session.get(f"{self.api_base_url}/health", timeout=2)
                end_time = time.time()
                
                if response.status_code == 200:
                    success_count += 1
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)
                    
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(0.1)  # 避免過於頻繁的請求
        
        if not response_times:
            pytest.skip("API 健康檢查不可用")
        
        memory_after, cpu_after = measure_system_resources()
        
        # 計算性能指標
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        success_rate = success_count / 10
        memory_usage = abs(memory_after - memory_before)
        cpu_usage = max(cpu_after, cpu_before)
        
        metrics = {
            'response_time_ms': avg_response_time,
            'memory_usage_mb': memory_usage,
            'cpu_usage_percent': cpu_usage,
            'success_rate': success_rate
        }
        
        # 記錄基準
        benchmark = PerformanceBenchmark(
            test_name="api_health_check",
            response_time_ms=avg_response_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            success_rate=success_rate,
            throughput_rps=success_count / 1.0,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        record_benchmark(benchmark)
        
        # 驗證性能基準
        performance_ok = validate_performance("api_health_check", metrics)
        
        print(f"✅ API 健康檢查性能: 平均 {avg_response_time:.1f}ms, 最大 {max_response_time:.1f}ms, 成功率 {success_rate:.1%}")
        
        assert success_rate >= 0.9, f"健康檢查成功率 {success_rate:.1%} 過低"
        assert avg_response_time < 200, f"平均響應時間 {avg_response_time:.1f}ms 過長"
    
    def test_concurrent_requests_performance_regression(self):
        """測試並發請求性能回歸"""
        def make_request():
            try:
                start_time = time.time()
                response = self.session.get(f"{self.api_base_url}/health", timeout=5)
                end_time = time.time()
                
                return {
                    'success': response.status_code == 200,
                    'response_time': (end_time - start_time) * 1000,
                    'status_code': response.status_code
                }
            except:
                return {'success': False, 'response_time': 5000, 'status_code': 0}
        
        # 並發測試配置
        concurrent_users = 10
        requests_per_user = 5
        
        memory_before, cpu_before = measure_system_resources()
        start_time = time.time()
        
        # 執行並發請求
        results = []
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            for _ in range(concurrent_users * requests_per_user):
                futures.append(executor.submit(make_request))
            
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        memory_after, cpu_after = measure_system_resources()
        
        # 分析結果
        successful_requests = [r for r in results if r['success']]
        response_times = [r['response_time'] for r in successful_requests]
        
        if not response_times:
            pytest.skip("並發請求測試無有效響應")
        
        total_time = end_time - start_time
        success_rate = len(successful_requests) / len(results)
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        throughput = len(successful_requests) / total_time
        memory_usage = abs(memory_after - memory_before)
        cpu_usage = max(cpu_after - cpu_before, 0)
        
        metrics = {
            'response_time_ms': avg_response_time,
            'memory_usage_mb': memory_usage,
            'cpu_usage_percent': cpu_usage,
            'success_rate': success_rate,
            'throughput_rps': throughput
        }
        
        # 記錄基準
        benchmark = PerformanceBenchmark(
            test_name="concurrent_requests",
            response_time_ms=avg_response_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            success_rate=success_rate,
            throughput_rps=throughput,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        record_benchmark(benchmark)
        
        print(f"✅ 並發請求性能: {concurrent_users}用戶x{requests_per_user}請求")
        print(f"   平均響應時間: {avg_response_time:.1f}ms")
        print(f"   最大響應時間: {max_response_time:.1f}ms") 
        print(f"   成功率: {success_rate:.1%}")
        print(f"   吞吐量: {throughput:.1f} RPS")
        
        assert success_rate >= 0.8, f"並發請求成功率 {success_rate:.1%} 過低"
        assert avg_response_time < 1000, f"並發平均響應時間 {avg_response_time:.1f}ms 過長"


class TestSystemResourceRegression:
    """系統資源使用回歸測試"""
    
    def test_memory_usage_regression(self):
        """測試內存使用回歸"""
        # 獲取系統進程信息
        netstack_processes = []
        simworld_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
            try:
                proc_info = proc.info
                if 'python' in proc_info['name'].lower() or 'uvicorn' in proc_info['name'].lower():
                    # 通過端口連接判斷是哪個服務
                    try:
                        connections = proc.connections()
                        for conn in connections:
                            if conn.laddr.port == 8080:
                                netstack_processes.append(proc_info)
                            elif conn.laddr.port == 8888:
                                simworld_processes.append(proc_info)
                    except:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 計算內存使用
        total_memory_mb = 0
        process_count = 0
        
        for proc_list, service_name in [(netstack_processes, "NetStack"), (simworld_processes, "SimWorld")]:
            service_memory = 0
            for proc in proc_list:
                if proc['memory_info']:
                    memory_mb = proc['memory_info'].rss / 1024 / 1024
                    service_memory += memory_mb
                    process_count += 1
            
            if service_memory > 0:
                print(f"📊 {service_name} 內存使用: {service_memory:.1f}MB")
                total_memory_mb += service_memory
        
        print(f"📊 總內存使用: {total_memory_mb:.1f}MB ({process_count} 個進程)")
        
        # 記錄基準
        benchmark = PerformanceBenchmark(
            test_name="memory_usage",
            response_time_ms=0,
            memory_usage_mb=total_memory_mb,
            cpu_usage_percent=0,
            success_rate=1.0,
            throughput_rps=0,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        record_benchmark(benchmark)
        
        assert total_memory_mb < 1000, f"系統內存使用 {total_memory_mb:.1f}MB 過高"
    
    def test_response_time_stability_regression(self):
        """測試響應時間穩定性回歸"""
        response_times = []
        
        # 長時間穩定性測試
        for i in range(30):  # 30次請求，測試穩定性
            try:
                start_time = time.time()
                response = requests.get("http://localhost:8080/health", timeout=3)
                end_time = time.time()
                
                if response.status_code == 200:
                    response_time_ms = (end_time - start_time) * 1000
                    response_times.append(response_time_ms)
                
            except requests.exceptions.RequestException:
                response_times.append(3000)  # 超時記為 3000ms
            
            time.sleep(0.2)  # 每200ms一次請求
        
        if not response_times:
            pytest.skip("響應時間穩定性測試無有效數據")
        
        # 計算穩定性指標
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0
        min_time = min(response_times)
        max_time = max(response_times)
        
        # 計算變異係數 (標準差/平均值)
        coefficient_of_variation = (std_dev / avg_time) if avg_time > 0 else 0
        
        print(f"📊 響應時間穩定性分析:")
        print(f"   平均: {avg_time:.1f}ms")
        print(f"   中位數: {median_time:.1f}ms")
        print(f"   標準差: {std_dev:.1f}ms")
        print(f"   範圍: {min_time:.1f}ms - {max_time:.1f}ms")
        print(f"   變異係數: {coefficient_of_variation:.3f}")
        
        # 記錄基準
        benchmark = PerformanceBenchmark(
            test_name="response_time_stability",
            response_time_ms=avg_time,
            memory_usage_mb=0,
            cpu_usage_percent=0,
            success_rate=len([t for t in response_times if t < 1000]) / len(response_times),
            throughput_rps=len(response_times) / 6.0,  # 30次請求在6秒內
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        record_benchmark(benchmark)
        
        # 穩定性驗證
        assert avg_time < 200, f"平均響應時間 {avg_time:.1f}ms 過長"
        assert max_time < 1000, f"最大響應時間 {max_time:.1f}ms 過長"
        assert coefficient_of_variation < 0.5, f"響應時間變異過大 {coefficient_of_variation:.3f}"


class TestPerformanceReporting:
    """性能測試報告"""
    
    def test_generate_performance_report(self):
        """生成性能測試報告"""
        # 生成報告
        report = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_tests': len(performance_benchmarks),
            'benchmarks': [
                {
                    'test_name': b.test_name,
                    'response_time_ms': b.response_time_ms,
                    'memory_usage_mb': b.memory_usage_mb,
                    'cpu_usage_percent': b.cpu_usage_percent,
                    'success_rate': b.success_rate,
                    'throughput_rps': b.throughput_rps,
                    'timestamp': b.timestamp
                } for b in performance_benchmarks
            ]
        }
        
        # 保存報告到文件
        report_file = "/home/sat/ntn-stack/netstack/tests/performance/performance_report.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 性能測試報告已生成: {report_file}")
        print(f"📊 總計 {len(performance_benchmarks)} 項性能基準測試")
        
        # 報告摘要
        if performance_benchmarks:
            response_times = [b.response_time_ms for b in performance_benchmarks if b.response_time_ms > 0]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                print(f"📊 平均響應時間: {avg_response_time:.1f}ms")
            
            avg_success_rate = statistics.mean([b.success_rate for b in performance_benchmarks])
            print(f"📊 平均成功率: {avg_success_rate:.1%}")
        
        assert len(performance_benchmarks) > 0, "應該生成至少一項性能基準"


if __name__ == "__main__":
    # 運行性能回歸測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])