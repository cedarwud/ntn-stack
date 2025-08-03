"""
Pytest configuration file for Phase 2 automated testing framework
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add project paths
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'netstack_api'))

# Test data fixtures
@pytest.fixture
def sample_tle_data():
    """Sample TLE data for testing"""
    return {
        'starlink': [
            {
                'name': 'STARLINK-1007',
                'line1': '1 44713U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  9990',
                'line2': '2 44713  53.0000 123.4567 0001234  90.1234 269.8765 15.12345678123456'
            },
            {
                'name': 'STARLINK-1008',
                'line1': '1 44714U 19074A   25215.12345678  .00001234  00000-0  12345-4 0  9991',
                'line2': '2 44714  53.0001 123.4568 0001235  90.1235 269.8766 15.12345679123457'
            }
        ],
        'oneweb': [
            {
                'name': 'ONEWEB-0001',
                'line1': '1 43013U 19003A   25215.12345678  .00001234  00000-0  12345-4 0  9990',
                'line2': '2 43013  87.4000 45.6789 0001234  90.1234 269.8765 13.12345678123456'
            }
        ]
    }

@pytest.fixture
def sample_sib19_data():
    """Sample SIB19 data for testing"""
    return {
        'satelliteEphemeris': {
            'STARLINK-1007': {
                'norad_id': 44713,
                'latitude': 24.5,
                'longitude': 121.0,
                'altitude': 550.0,
                'inclination': 53.0,
                'raan': 123.45,
                'mean_motion': 15.12345678
            },
            'STARLINK-1008': {
                'norad_id': 44714,
                'latitude': 25.0,
                'longitude': 121.5,
                'altitude': 555.0,
                'inclination': 53.0,
                'raan': 124.50,
                'mean_motion': 15.11234567
            }
        },
        'epochTime': '2025-08-03T12:00:00Z',
        'ntn-NeighCellConfigList': [
            {'cellId': 1, 'pci': 100},
            {'cellId': 2, 'pci': 101}
        ],
        'distanceThresh': 1000.0
    }

@pytest.fixture
def mock_satellite_config():
    """Mock satellite configuration for testing"""
    config = Mock()
    config.MAX_CANDIDATE_SATELLITES = 8
    config.PREPROCESS_SATELLITES = {"starlink": 40, "oneweb": 30}
    config.BATCH_COMPUTE_MAX_SATELLITES = 50
    
    # Mock elevation thresholds
    thresholds = Mock()
    thresholds.trigger_threshold_deg = 15.0
    thresholds.execution_threshold_deg = 10.0
    thresholds.critical_threshold_deg = 5.0
    config.elevation_thresholds = thresholds
    
    # Mock intelligent selection
    selection = Mock()
    selection.enabled = True
    selection.geographic_filter_enabled = True
    selection.target_location = {"lat": 24.9441667, "lon": 121.3713889}
    config.intelligent_selection = selection
    
    return config

# Test environment setup
def pytest_configure(config):
    """Configure pytest environment"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )

# Test discovery
def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

# Mock external dependencies
@pytest.fixture(autouse=True)
def mock_external_dependencies():
    """Mock external dependencies that might not be available in test environment"""
    with patch('sys.path', sys.path + ['/app/netstack']):
        yield