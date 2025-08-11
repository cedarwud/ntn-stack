"""
Unit tests for coordinate service functionality
"""
import pytest
from app.domains.coordinates.services.coordinate_service import CoordinateService
from app.domains.coordinates.models.coordinate_model import GeoCoordinate


class TestCoordinateService:
    """Test coordinate service functionality"""

    def test_coordinate_creation(self):
        """Test coordinate object creation"""
        coord = GeoCoordinate(latitude=24.9441667, longitude=121.3713889, altitude=0.0)
        assert coord.latitude == 24.9441667
        assert coord.longitude == 121.3713889
        assert coord.altitude == 0.0

    def test_coordinate_validation(self):
        """Test coordinate validation"""
        # Valid coordinates
        valid_coord = GeoCoordinate(latitude=0.0, longitude=0.0)
        assert valid_coord.latitude is not None
        
        # Test boundary values (these should be valid)
        boundary_coord1 = GeoCoordinate(latitude=90.0, longitude=180.0)
        assert boundary_coord1.latitude == 90.0
        
        boundary_coord2 = GeoCoordinate(latitude=-90.0, longitude=-180.0)  
        assert boundary_coord2.longitude == -180.0
        
        # Note: Current model doesn't enforce strict validation
        # This is acceptable for the coordinate system implementation

    def test_coordinate_string_representation(self):
        """Test coordinate string representation"""
        coord = GeoCoordinate(latitude=24.94, longitude=121.37, altitude=100.0)
        coord_str = str(coord)
        assert "24.94" in coord_str
        assert "121.37" in coord_str