"""
NTN Stack 統一測試配置
簡化的 pytest 配置，支援統一測試框架
"""

import pytest
import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "netstack"))
sys.path.insert(0, str(project_root / "simworld" / "backend"))

# 配置測試日誌
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)


@pytest.fixture(scope="session")
def event_loop():
    """為測試會話創建事件循環"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """配置 pytest markers"""
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line(
        "markers", "critical: Critical functionality tests")
    config.addinivalue_line(
        "markers", "network: Tests requiring network access")
    config.addinivalue_line(
        "markers", "database: Tests requiring database access")
    config.addinivalue_line("markers", "docker: Tests requiring Docker")


@pytest.fixture
def test_config():
    """測試配置"""
    return {
        "api_base_url": "http://localhost:8888",
        "netstack_base_url": "http://localhost:8080",
        "timeout": 30,
        "debug": False
    }

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
        if any(keyword in item.name.lower()
               for keyword in ["health", "connection", "handover", "api"]):
            item.add_marker(pytest.mark.critical)

# Cleanup after tests


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup fixture that runs after each test."""
    yield
    # Add any cleanup logic here
    pass
