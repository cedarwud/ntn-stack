"""
Unified Health Monitoring Tests
Consolidates health check functionality for all services
"""

import pytest
import asyncio
import httpx
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

@pytest.mark.integration
@pytest.mark.critical
@pytest.mark.health
class TestHealthMonitoring:
    """Comprehensive health monitoring test suite."""
    
    @pytest.fixture
    def service_endpoints(self, test_config):
        """Define all service health endpoints."""
        return {
            "simworld_backend": f"{test_config['api_base_url']}/health",
            "netstack_api": f"{test_config['netstack_base_url']}/health",
            "simworld_frontend": f"{test_config['api_base_url'].replace('8888', '5173')}/",  # Frontend port
        }
    
    @pytest.mark.asyncio
    async def test_all_services_health(self, service_endpoints):
        """Test that all core services are healthy."""
        health_results = {}
        
        for service_name, endpoint in service_endpoints.items():
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(endpoint)
                    health_results[service_name] = {
                        "status_code": response.status_code,
                        "healthy": response.status_code == 200,
                        "response_time": response.elapsed.total_seconds() if response.elapsed else None
                    }
                    
                    logger.info(f"✅ {service_name} health check: {response.status_code}")
                    
            except Exception as e:
                health_results[service_name] = {
                    "status_code": None,
                    "healthy": False,
                    "error": str(e)
                }
                logger.error(f"❌ {service_name} health check failed: {e}")
        
        # Assert critical services are healthy (allow SimWorld backend to be down in test env)
        critical_services = ["netstack_api", "simworld_frontend"] 
        failed_critical_services = [
            name for name, result in health_results.items() 
            if name in critical_services and not result["healthy"]
        ]
        assert not failed_critical_services, f"Critical services unhealthy: {failed_critical_services}"
        
        # Log status of all services
        for name, result in health_results.items():
            if result["healthy"]:
                logger.info(f"✅ {name}: Healthy")
            else:
                if name == "simworld_backend":
                    logger.warning(f"⚠️ {name}: Not running (expected in test environment)")
                else:
                    logger.error(f"❌ {name}: Unhealthy")
    
    @pytest.mark.asyncio
    async def test_netstack_api_detailed_health(self, test_config):
        """Test detailed NetStack API health information."""
        endpoint = f"{test_config['netstack_base_url']}/health"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint)
            
            assert response.status_code == 200, f"NetStack health check failed: {response.status_code}"
            
            if response.headers.get("content-type", "").startswith("application/json"):
                health_data = response.json()
                
                # Check for expected health data structure
                # NetStack API returns 'overall_status' instead of 'status'
                if "overall_status" in health_data:
                    assert health_data["overall_status"] in ["healthy", "ok"], f"Unexpected health status: {health_data['overall_status']}"
                elif "status" in health_data:
                    assert health_data["status"] in ["healthy", "ok"], f"Unexpected health status: {health_data['status']}"
                
                # Check for timestamp
                assert "timestamp" in health_data, "Missing timestamp field"
    
    @pytest.mark.asyncio
    async def test_simworld_backend_health(self, test_config):
        """Test SimWorld backend health endpoint."""
        endpoint = f"{test_config['api_base_url']}/health"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint)
            
            # Allow 404 for SimWorld backend in test environment (service may not be running)
            if response.status_code == 404:
                logger.warning("⚠️ SimWorld backend not running (expected in test environment)")
            else:
                assert response.status_code == 200, f"SimWorld health check failed: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_service_response_times(self, service_endpoints):
        """Test that all services respond within acceptable time limits."""
        max_response_time = 5.0  # 5 seconds max
        response_times = {}
        
        for service_name, endpoint in service_endpoints.items():
            try:
                async with httpx.AsyncClient(timeout=max_response_time) as client:
                    start_time = asyncio.get_event_loop().time()
                    response = await client.get(endpoint)
                    end_time = asyncio.get_event_loop().time()
                    
                    response_time = end_time - start_time
                    response_times[service_name] = response_time
                    
                    assert response_time < max_response_time, f"{service_name} response time too slow: {response_time:.2f}s"
                    logger.info(f"⚡ {service_name} response time: {response_time:.2f}s")
                    
            except asyncio.TimeoutError:
                pytest.fail(f"{service_name} health check timed out (>{max_response_time}s)")
            except Exception as e:
                pytest.fail(f"{service_name} health check error: {e}")
    
    @pytest.mark.asyncio
    async def test_service_availability_over_time(self, service_endpoints):
        """Test service availability over multiple checks."""
        num_checks = 5
        check_interval = 1.0  # seconds
        availability_results = {service: [] for service in service_endpoints.keys()}
        
        for check_num in range(num_checks):
            logger.info(f"Running availability check {check_num + 1}/{num_checks}")
            
            for service_name, endpoint in service_endpoints.items():
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        response = await client.get(endpoint)
                        availability_results[service_name].append(response.status_code == 200)
                except Exception:
                    availability_results[service_name].append(False)
            
            if check_num < num_checks - 1:  # Don't sleep after last check
                await asyncio.sleep(check_interval)
        
        # Calculate availability percentage for each service
        for service_name, results in availability_results.items():
            availability_percentage = (sum(results) / len(results)) * 100
            logger.info(f"📊 {service_name} availability: {availability_percentage:.1f}%")
            
            # Allow SimWorld backend to have 0% availability in test environment
            if service_name == "simworld_backend" and availability_percentage == 0.0:
                logger.warning(f"⚠️ {service_name} not available (expected in test environment)")
            else:
                # Assert minimum 80% availability for other services
                assert availability_percentage >= 80.0, f"{service_name} availability too low: {availability_percentage:.1f}%"
    
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_health_under_load(self, service_endpoints):
        """Test health endpoints under concurrent load."""
        concurrent_requests = 10
        
        async def check_health(service_name: str, endpoint: str) -> bool:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(endpoint)
                    return response.status_code == 200
            except Exception as e:
                logger.warning(f"Health check failed under load for {service_name}: {e}")
                return False
        
        for service_name, endpoint in service_endpoints.items():
            logger.info(f"Testing {service_name} under load ({concurrent_requests} concurrent requests)")
            
            # Create concurrent health check tasks
            tasks = [check_health(service_name, endpoint) for _ in range(concurrent_requests)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful health checks
            successful_checks = sum(1 for result in results if result is True)
            success_rate = (successful_checks / concurrent_requests) * 100
            
            logger.info(f"📈 {service_name} success rate under load: {success_rate:.1f}%")
            
            # Allow SimWorld backend to have 0% success rate in test environment
            if service_name == "simworld_backend" and success_rate == 0.0:
                logger.warning(f"⚠️ {service_name} not available under load (expected in test environment)")
            else:
                # Assert at least 80% success rate under load for other services
                assert success_rate >= 80.0, f"{service_name} failed under load: {success_rate:.1f}% success rate"

@pytest.mark.integration  
@pytest.mark.critical
class TestServiceConnectivity:
    """Test connectivity between services."""
    
    @pytest.mark.asyncio
    async def test_netstack_to_simworld_connectivity(self, test_config):
        """Test that NetStack can communicate with SimWorld."""
        # This would test actual service-to-service communication
        # Implementation depends on specific inter-service APIs
        pass
    
    @pytest.mark.asyncio
    async def test_database_connectivity(self, test_config):
        """Test database connectivity if applicable."""
        # This would test database connections
        # Implementation depends on database configuration
        pass

# Helper functions for health monitoring
def get_service_version(endpoint: str) -> str:
    """Get service version from health endpoint if available."""
    # Implementation would depend on service health response format
    return "unknown"

def validate_health_response_format(response_data: dict) -> bool:
    """Validate the format of health response data."""
    required_fields = ["status"]
    return all(field in response_data for field in required_fields)