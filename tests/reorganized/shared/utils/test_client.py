"""
Test HTTP Client Utilities
Provides standardized HTTP clients for testing different services
"""

import httpx
import asyncio
from typing import Dict, Any, Optional, Union
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class BaseTestAPIClient:
    """Standardized API test client with common functionality."""
    
    def __init__(self, base_url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.default_headers = headers or {}
        
    @asynccontextmanager
    async def client(self):
        """Async context manager for HTTP client."""
        async with httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self.default_headers
        ) as client:
            yield client
    
    async def get(self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None) -> httpx.Response:
        """Make GET request."""
        async with self.client() as client:
            response = await client.get(endpoint, params=params, headers=headers)
            logger.debug(f"GET {endpoint} -> {response.status_code}")
            return response
    
    async def post(self, endpoint: str, json_data: Optional[Dict] = None, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> httpx.Response:
        """Make POST request."""
        async with self.client() as client:
            response = await client.post(endpoint, json=json_data, data=data, headers=headers)
            logger.debug(f"POST {endpoint} -> {response.status_code}")
            return response
    
    async def put(self, endpoint: str, json_data: Optional[Dict] = None, data: Optional[Dict] = None, headers: Optional[Dict] = None) -> httpx.Response:
        """Make PUT request."""
        async with self.client() as client:
            response = await client.put(endpoint, json=json_data, data=data, headers=headers)
            logger.debug(f"PUT {endpoint} -> {response.status_code}")
            return response
    
    async def delete(self, endpoint: str, headers: Optional[Dict] = None) -> httpx.Response:
        """Make DELETE request."""
        async with self.client() as client:
            response = await client.delete(endpoint, headers=headers)
            logger.debug(f"DELETE {endpoint} -> {response.status_code}")
            return response
    
    async def health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            response = await self.get("/health")
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    async def wait_for_ready(self, max_attempts: int = 30, delay: float = 1.0) -> bool:
        """Wait for service to be ready."""
        for attempt in range(max_attempts):
            if await self.health_check():
                logger.info(f"Service ready after {attempt + 1} attempts")
                return True
            logger.debug(f"Attempt {attempt + 1}: Service not ready, waiting {delay}s...")
            await asyncio.sleep(delay)
        
        logger.error(f"Service not ready after {max_attempts} attempts")
        return False

class SimWorldAPIClient(BaseTestAPIClient):
    """SimWorld Backend API test client."""
    
    def __init__(self, base_url: str = "http://localhost:8888", **kwargs):
        super().__init__(base_url, **kwargs)
    
    async def get_satellites(self) -> httpx.Response:
        """Get satellite data."""
        return await self.get("/api/v1/satellite/")
    
    async def get_uav_positions(self) -> httpx.Response:
        """Get UAV positions."""
        return await self.get("/api/v1/tracking/uav/positions")
    
    async def trigger_handover(self, uav_id: str, target_satellite: str) -> httpx.Response:
        """Trigger handover for UAV."""
        return await self.post("/api/v1/handover/trigger", json_data={
            "uav_id": uav_id,
            "target_satellite": target_satellite
        })
    
    async def get_interference_data(self) -> httpx.Response:
        """Get interference analysis data."""
        return await self.get("/api/v1/interference/analysis")

class NetStackAPIClient(BaseTestAPIClient):
    """NetStack API test client."""
    
    def __init__(self, base_url: str = "http://localhost:8080", **kwargs):
        super().__init__(base_url, **kwargs)
    
    async def get_rl_status(self) -> httpx.Response:
        """Get RL engine status."""
        return await self.get("/api/v1/rl/status")
    
    async def get_ai_decision_status(self) -> httpx.Response:
        """Get AI decision engine status."""
        return await self.get("/api/v1/ai-decision/status")
    
    async def switch_to_gymnasium(self) -> httpx.Response:
        """Switch to Gymnasium RL engine."""
        return await self.post("/api/v1/ai-decision/switch-to-gymnasium")
    
    async def get_satellite_gnb_mapping(self) -> httpx.Response:
        """Get satellite-gNB mapping."""
        return await self.get("/api/v1/satellite-gnb/mapping")

def create_test_clients(config: Dict[str, Any]) -> Dict[str, BaseTestAPIClient]:
    """Create standardized test clients from configuration."""
    clients = {}
    
    # SimWorld API client
    clients['simworld'] = SimWorldAPIClient(
        base_url=config.get('api_base_url', 'http://localhost:8888'),
        timeout=config.get('timeout', 30)
    )
    
    # NetStack API client
    clients['netstack'] = NetStackAPIClient(
        base_url=config.get('netstack_base_url', 'http://localhost:8080'),
        timeout=config.get('timeout', 30)
    )
    
    return clients

async def wait_for_services(clients: Dict[str, BaseTestAPIClient], timeout: int = 120) -> Dict[str, bool]:
    """Wait for all services to be ready."""
    results = {}
    
    for name, client in clients.items():
        logger.info(f"Waiting for {name} service...")
        results[name] = await client.wait_for_ready(max_attempts=timeout)
        
        if results[name]:
            logger.info(f"✅ {name} service is ready")
        else:
            logger.error(f"❌ {name} service failed to start")
    
    return results

# Utility functions for common test scenarios
async def assert_healthy_services(clients: Dict[str, BaseTestAPIClient]):
    """Assert that all services are healthy."""
    for name, client in clients.items():
        is_healthy = await client.health_check()
        assert is_healthy, f"{name} service is not healthy"

async def assert_api_response_structure(response: httpx.Response, expected_fields: list):
    """Assert API response has expected structure."""
    assert response.status_code == 200, f"API call failed: {response.status_code}"
    
    try:
        data = response.json()
    except Exception as e:
        assert False, f"Response is not valid JSON: {e}"
    
    for field in expected_fields:
        assert field in data, f"Expected field '{field}' not found in response"