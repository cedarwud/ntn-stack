"""
Integration tests for API health endpoints
"""
import pytest
import requests
from fastapi.testclient import TestClient


class TestHealthAPI:
    """Test health API endpoints"""

    @pytest.fixture
    def base_url(self):
        """Base URL for API tests"""
        return "http://localhost:8000"

    def test_health_endpoint_response(self, base_url):
        """Test health endpoint returns correct structure"""
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "services" in data
        assert "timestamp" in data

    def test_root_endpoint_response(self, base_url):
        """Test root endpoint returns API information"""
        response = requests.get(base_url)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

    def test_api_documentation_accessible(self, base_url):
        """Test API documentation is accessible"""
        response = requests.get(f"{base_url}/docs")
        assert response.status_code == 200