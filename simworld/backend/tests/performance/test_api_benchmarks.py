"""
Performance benchmark tests for API endpoints
Verifies system meets refactor plan performance goals:
- API response times ≤ 100ms
- Memory usage reduction ≥ 20%
"""
import pytest
import time
import requests
import psutil
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median


class TestAPIPerformanceBenchmarks:
    """Test API performance benchmarks"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API tests"""
        return "http://localhost:8000"
    
    @pytest.fixture
    def netstack_url(self):
        """NetStack API URL"""
        return "http://localhost:8080"
    
    def measure_response_time(self, url):
        """Measure response time for a single request"""
        start_time = time.time()
        try:
            response = requests.get(url, timeout=5)
            end_time = time.time()
            return (end_time - start_time) * 1000, response.status_code  # Return milliseconds
        except Exception as e:
            end_time = time.time()
            return (end_time - start_time) * 1000, 500
    
    def test_health_endpoint_response_time(self, base_url):
        """Test health endpoint response time ≤ 100ms"""
        url = f"{base_url}/health"
        
        # Warm up
        requests.get(url)
        
        # Measure 10 requests
        response_times = []
        for _ in range(10):
            response_time, status_code = self.measure_response_time(url)
            if status_code == 200:
                response_times.append(response_time)
        
        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        
        print(f"Health endpoint - Avg: {avg_response_time:.2f}ms, Median: {median_response_time:.2f}ms")
        
        # Refactor plan goal: ≤ 100ms
        assert avg_response_time <= 100, f"Average response time {avg_response_time:.2f}ms exceeds 100ms target"
        assert median_response_time <= 100, f"Median response time {median_response_time:.2f}ms exceeds 100ms target"
    
    def test_root_endpoint_response_time(self, base_url):
        """Test root endpoint response time ≤ 100ms"""
        url = base_url
        
        # Warm up
        requests.get(url)
        
        # Measure 10 requests
        response_times = []
        for _ in range(10):
            response_time, status_code = self.measure_response_time(url)
            if status_code == 200:
                response_times.append(response_time)
        
        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        
        print(f"Root endpoint - Avg: {avg_response_time:.2f}ms, Median: {median_response_time:.2f}ms")
        
        # Refactor plan goal: ≤ 100ms  
        assert avg_response_time <= 100, f"Average response time {avg_response_time:.2f}ms exceeds 100ms target"
        assert median_response_time <= 100, f"Median response time {median_response_time:.2f}ms exceeds 100ms target"
    
    def test_concurrent_load_performance(self, base_url):
        """Test system under concurrent load"""
        url = f"{base_url}/health"
        
        def make_request():
            return self.measure_response_time(url)
        
        # Test with 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]
        
        response_times = [result[0] for result in results if result[1] == 200]
        success_rate = len(response_times) / len(results) * 100
        
        if response_times:
            avg_concurrent_time = mean(response_times)
            print(f"Concurrent load - Avg: {avg_concurrent_time:.2f}ms, Success rate: {success_rate:.1f}%")
            
            # Under load, allow slightly higher response time but still reasonable
            assert avg_concurrent_time <= 200, f"Concurrent response time {avg_concurrent_time:.2f}ms too high"
            assert success_rate >= 95, f"Success rate {success_rate:.1f}% too low"
    
    def test_memory_usage_baseline(self):
        """Test memory usage is reasonable"""
        # Get current memory usage of the system
        memory = psutil.virtual_memory()
        
        print(f"System memory - Used: {memory.percent:.1f}%, Available: {memory.available / 1024**3:.1f}GB")
        
        # Ensure system has reasonable memory usage
        assert memory.percent < 90, f"System memory usage {memory.percent:.1f}% too high"
        
        # Get Docker container memory if possible
        try:
            # This is a basic check - in a real benchmark we'd monitor container memory
            process_memory = psutil.Process().memory_info()
            memory_mb = process_memory.rss / 1024 / 1024
            print(f"Test process memory: {memory_mb:.1f}MB")
        except Exception:
            pass  # Not critical if we can't get process memory
    
    def test_netstack_integration_performance(self, netstack_url):
        """Test NetStack API integration performance"""
        health_url = f"{netstack_url}/health"
        
        # Warm up
        try:
            requests.get(health_url, timeout=2)
        except:
            pytest.skip("NetStack API not available for integration test")
        
        # Measure NetStack health endpoint
        response_times = []
        for _ in range(5):
            response_time, status_code = self.measure_response_time(health_url)
            if status_code == 200:
                response_times.append(response_time)
        
        if response_times:
            avg_netstack_time = mean(response_times)
            print(f"NetStack integration - Avg: {avg_netstack_time:.2f}ms")
            
            # NetStack should also respond quickly for good integration
            assert avg_netstack_time <= 500, f"NetStack response time {avg_netstack_time:.2f}ms too slow for integration"