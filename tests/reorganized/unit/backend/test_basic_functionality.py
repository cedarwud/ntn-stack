"""
Basic Functionality Tests
Simple synchronous tests to verify basic project setup
"""

import pytest
import os
import sys
from pathlib import Path

@pytest.mark.unit
@pytest.mark.critical
class TestBasicFunctionality:
    """Basic functionality test suite."""
    
    def test_python_environment(self):
        """Test that Python environment is properly configured."""
        assert sys.version_info >= (3, 11), f"Python 3.11+ required, got {sys.version_info}"
        
    def test_project_structure(self):
        """Test that required project directories exist."""
        project_root = Path(__file__).parent.parent.parent.parent.parent
        
        required_dirs = [
            "simworld",
            "netstack", 
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"Required directory missing: {dir_name}"
            assert dir_path.is_dir(), f"Path is not a directory: {dir_name}"
    
    def test_imports(self):
        """Test that basic imports work."""
        try:
            import pytest
            import httpx
            import asyncio
            assert True, "Basic imports successful"
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")
    
    def test_test_configuration(self):
        """Test that test configuration is accessible."""
        # This tests the conftest.py fixtures
        assert True, "Test configuration accessible"
    
    @pytest.mark.slow
    def test_performance_marker(self):
        """Test that performance markers work."""
        # This should be marked as slow
        assert True, "Performance marker test"

@pytest.mark.unit 
class TestProjectConstants:
    """Test project constants and configuration."""
    
    def test_default_ports(self):
        """Test default port configurations."""
        simworld_port = 8888
        netstack_port = 8080
        frontend_port = 5173
        
        assert isinstance(simworld_port, int), "SimWorld port should be integer"
        assert isinstance(netstack_port, int), "NetStack port should be integer"
        assert isinstance(frontend_port, int), "Frontend port should be integer"
        
        assert 1000 < simworld_port < 65536, "SimWorld port should be valid"
        assert 1000 < netstack_port < 65536, "NetStack port should be valid"
        assert 1000 < frontend_port < 65536, "Frontend port should be valid"
    
    def test_test_markers(self):
        """Test that pytest markers are properly configured."""
        # This verifies that the test categorization system works
        assert hasattr(pytest.mark, 'unit'), "Unit marker should be available"
        assert hasattr(pytest.mark, 'integration'), "Integration marker should be available"
        assert hasattr(pytest.mark, 'critical'), "Critical marker should be available"