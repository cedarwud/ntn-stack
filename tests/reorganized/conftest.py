"""
NTN Stack Test Suite - Global Test Configuration
Centralized pytest configuration for all test types
"""

import pytest
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Generator, AsyncGenerator

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "simworld" / "backend"))
sys.path.insert(0, str(project_root / "netstack"))

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable verbose logging during tests
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Test configuration fixture."""
    return {
        "api_base_url": os.getenv("TEST_API_BASE_URL", "http://localhost:8888"),
        "netstack_base_url": os.getenv("TEST_NETSTACK_BASE_URL", "http://localhost:8080"),
        "database_url": os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/test_db"),
        "redis_url": os.getenv("TEST_REDIS_URL", "redis://localhost:6379/0"),
        "timeout": int(os.getenv("TEST_TIMEOUT", "30")),
        "debug": os.getenv("TEST_DEBUG", "false").lower() == "true"
    }

@pytest.fixture
def mock_satellite_data():
    """Mock satellite TLE data for testing."""
    return {
        "satellites": [
            {
                "name": "STARLINK-1007",
                "line1": "1 44713U 19074A   23001.00000000  .00002182  00000-0  15933-3 0  9991",
                "line2": "2 44713  53.0539 339.0000 0001311  85.0000 275.0000 15.05000000000000",
                "timestamp": "2023-01-01T00:00:00Z"
            },
            {
                "name": "STARLINK-1008", 
                "line1": "1 44714U 19074B   23001.00000000  .00002182  00000-0  15933-3 0  9992",
                "line2": "2 44714  53.0539 339.0100 0001311  85.0100 275.0100 15.05000000000001",
                "timestamp": "2023-01-01T00:00:00Z"
            }
        ]
    }

@pytest.fixture
def mock_uav_data():
    """Mock UAV data for testing."""
    return {
        "uav_id": "test-uav-001",
        "position": {"latitude": 25.0330, "longitude": 121.5654, "altitude": 100.0},
        "velocity": {"x": 10.0, "y": 5.0, "z": 0.0},
        "connected_satellite": "STARLINK-1007",
        "signal_strength": -85.5,
        "status": "active"
    }

@pytest.fixture
def mock_handover_data():
    """Mock handover event data for testing."""
    return {
        "event_id": "handover-test-001", 
        "uav_id": "test-uav-001",
        "source_satellite": "STARLINK-1007",
        "target_satellite": "STARLINK-1008",
        "trigger_reason": "signal_degradation",
        "timestamp": "2023-01-01T12:00:00Z",
        "latency_ms": 45.2,
        "success": True
    }

# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "critical: Critical functionality tests")
    config.addinivalue_line("markers", "network: Tests requiring network access")
    config.addinivalue_line("markers", "database: Tests requiring database access")
    config.addinivalue_line("markers", "docker: Tests requiring Docker")

# Auto-apply markers based on test location
def pytest_collection_modifyitems(config, items):
    """Automatically apply markers based on test file location."""
    for item in items:
        # Get relative path from project root
        rel_path = os.path.relpath(item.fspath, str(project_root))
        
        # Apply markers based on path
        if "/unit/" in rel_path:
            item.add_marker(pytest.mark.unit)
        elif "/integration/" in rel_path:
            item.add_marker(pytest.mark.integration)
        elif "/e2e/" in rel_path:
            item.add_marker(pytest.mark.e2e)
        elif "/performance/" in rel_path:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
            
        # Apply component markers
        if "/backend/" in rel_path:
            item.add_marker(pytest.mark.backend)
        elif "/frontend/" in rel_path:
            item.add_marker(pytest.mark.frontend)
        elif "/netstack/" in rel_path:
            item.add_marker(pytest.mark.netstack)
            
        # Apply critical marker for essential tests
        if any(keyword in item.name.lower() for keyword in ["health", "connection", "handover", "api"]):
            item.add_marker(pytest.mark.critical)

# Cleanup after tests
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup fixture that runs after each test."""
    yield
    # Add any cleanup logic here
    pass