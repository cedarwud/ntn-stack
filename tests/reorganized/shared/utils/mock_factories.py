"""
Test Data Factories
Provides factory functions to generate consistent test data
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

class SatelliteDataFactory:
    """Factory for generating satellite test data."""
    
    @staticmethod
    def create_tle_data(
        name: str = None,
        norad_id: int = None,
        inclination: float = None,
        longitude: float = None
    ) -> Dict[str, Any]:
        """Create TLE (Two-Line Element) satellite data."""
        name = name or f"STARLINK-{random.randint(1000, 9999)}"
        norad_id = norad_id or random.randint(40000, 60000)
        inclination = inclination or round(random.uniform(53.0, 53.2), 4)
        longitude = longitude or round(random.uniform(0, 360), 4)
        
        # Generate realistic TLE lines
        line1 = f"1 {norad_id}U 19074A   23001.00000000  .00002182  00000-0  15933-3 0  9991"
        line2 = f"2 {norad_id}  {inclination:7.4f} {longitude:8.4f} 0001311  85.0000 275.0000 15.05000000000000"
        
        return {
            "name": name,
            "norad_id": norad_id,
            "line1": line1,
            "line2": line2,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "epoch": "2023-01-01T00:00:00Z",
            "mean_motion": 15.05,
            "eccentricity": 0.0001311,
            "inclination": inclination,
            "raan": longitude,
            "arg_perigee": 85.0,
            "mean_anomaly": 275.0
        }
    
    @staticmethod
    def create_satellite_position(
        satellite_id: str = None,
        latitude: float = None,
        longitude: float = None,
        altitude: float = None
    ) -> Dict[str, Any]:
        """Create satellite position data."""
        return {
            "satellite_id": satellite_id or f"sat-{uuid.uuid4().hex[:8]}",
            "position": {
                "latitude": latitude or round(random.uniform(-85, 85), 6),
                "longitude": longitude or round(random.uniform(-180, 180), 6),
                "altitude": altitude or round(random.uniform(540, 560), 2)  # LEO altitude
            },
            "velocity": {
                "x": round(random.uniform(-8000, 8000), 2),
                "y": round(random.uniform(-8000, 8000), 2),
                "z": round(random.uniform(-1000, 1000), 2)
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @staticmethod
    def create_constellation(count: int = 10) -> List[Dict[str, Any]]:
        """Create a constellation of satellites."""
        return [SatelliteDataFactory.create_tle_data() for _ in range(count)]

class UAVDataFactory:
    """Factory for generating UAV test data."""
    
    @staticmethod
    def create_uav_data(
        uav_id: str = None,
        latitude: float = None,
        longitude: float = None,
        altitude: float = None,
        status: str = "active"
    ) -> Dict[str, Any]:
        """Create UAV data."""
        return {
            "uav_id": uav_id or f"uav-{uuid.uuid4().hex[:8]}",
            "position": {
                "latitude": latitude or round(random.uniform(24.5, 25.5), 6),  # Taiwan area
                "longitude": longitude or round(random.uniform(121.0, 122.0), 6),
                "altitude": altitude or round(random.uniform(50, 200), 1)
            },
            "velocity": {
                "x": round(random.uniform(-50, 50), 2),
                "y": round(random.uniform(-50, 50), 2),
                "z": round(random.uniform(-10, 10), 2)
            },
            "orientation": {
                "yaw": round(random.uniform(0, 360), 2),
                "pitch": round(random.uniform(-30, 30), 2),
                "roll": round(random.uniform(-15, 15), 2)
            },
            "connected_satellite": f"STARLINK-{random.randint(1000, 9999)}",
            "signal_strength_dbm": round(random.uniform(-120, -60), 1),
            "battery_level": round(random.uniform(20, 100), 1),
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @staticmethod
    def create_uav_fleet(count: int = 5) -> List[Dict[str, Any]]:
        """Create a fleet of UAVs."""
        return [UAVDataFactory.create_uav_data() for _ in range(count)]

class HandoverDataFactory:
    """Factory for generating handover test data."""
    
    @staticmethod
    def create_handover_event(
        uav_id: str = None,
        source_satellite: str = None,
        target_satellite: str = None,
        success: bool = True,
        latency_ms: float = None
    ) -> Dict[str, Any]:
        """Create handover event data."""
        return {
            "event_id": f"handover-{uuid.uuid4().hex[:8]}",
            "uav_id": uav_id or f"uav-{uuid.uuid4().hex[:8]}",
            "source_satellite": source_satellite or f"STARLINK-{random.randint(1000, 9999)}",
            "target_satellite": target_satellite or f"STARLINK-{random.randint(1000, 9999)}",
            "trigger_reason": random.choice([
                "signal_degradation", "satellite_handoff", "load_balancing", 
                "interference_avoidance", "planned_maintenance"
            ]),
            "start_time": datetime.utcnow().isoformat() + "Z",
            "end_time": (datetime.utcnow() + timedelta(milliseconds=latency_ms or random.uniform(20, 100))).isoformat() + "Z",
            "latency_ms": latency_ms or round(random.uniform(20, 100), 2),
            "success": success,
            "error_message": None if success else "Connection timeout",
            "signal_strength_before": round(random.uniform(-120, -80), 1),
            "signal_strength_after": round(random.uniform(-90, -60), 1) if success else None,
            "algorithm_used": random.choice(["traditional", "ml_optimized", "rl_based", "ieee_infocom_2024"]),
            "metrics": {
                "packet_loss": round(random.uniform(0, 5), 2),
                "throughput_mbps": round(random.uniform(10, 100), 2),
                "jitter_ms": round(random.uniform(1, 10), 2)
            }
        }
    
    @staticmethod
    def create_handover_sequence(count: int = 10) -> List[Dict[str, Any]]:
        """Create a sequence of handover events."""
        events = []
        uav_id = f"uav-{uuid.uuid4().hex[:8]}"
        satellites = [f"STARLINK-{random.randint(1000, 9999)}" for _ in range(5)]
        
        for i in range(count):
            source = satellites[i % len(satellites)]
            target = satellites[(i + 1) % len(satellites)]
            
            event = HandoverDataFactory.create_handover_event(
                uav_id=uav_id,
                source_satellite=source,
                target_satellite=target,
                success=random.random() > 0.1  # 90% success rate
            )
            events.append(event)
        
        return events

class InterferenceDataFactory:
    """Factory for generating interference test data."""
    
    @staticmethod
    def create_sinr_data(
        grid_size: int = 100,
        frequency_mhz: float = 2400
    ) -> Dict[str, Any]:
        """Create SINR (Signal-to-Interference-plus-Noise Ratio) data."""
        grid_data = []
        for x in range(grid_size):
            row = []
            for y in range(grid_size):
                # Generate realistic SINR values (-20 to 30 dB)
                sinr_db = round(random.uniform(-20, 30), 2)
                row.append(sinr_db)
            grid_data.append(row)
        
        return {
            "grid_size": grid_size,
            "frequency_mhz": frequency_mhz,
            "sinr_grid": grid_data,
            "metadata": {
                "min_sinr": min(min(row) for row in grid_data),
                "max_sinr": max(max(row) for row in grid_data),
                "avg_sinr": sum(sum(row) for row in grid_data) / (grid_size * grid_size)
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    
    @staticmethod
    def create_interference_source(
        source_type: str = "unknown"
    ) -> Dict[str, Any]:
        """Create interference source data."""
        return {
            "source_id": f"interference-{uuid.uuid4().hex[:8]}",
            "type": source_type,
            "position": {
                "latitude": round(random.uniform(24.5, 25.5), 6),
                "longitude": round(random.uniform(121.0, 122.0), 6),
                "altitude": round(random.uniform(0, 50), 1)
            },
            "frequency_range": {
                "start_mhz": round(random.uniform(2400, 2450), 1),
                "end_mhz": round(random.uniform(2450, 2500), 1)
            },
            "power_dbm": round(random.uniform(-50, 10), 1),
            "detected_at": datetime.utcnow().isoformat() + "Z"
        }

class NetworkDataFactory:
    """Factory for generating network test data."""
    
    @staticmethod
    def create_5g_cell_data(
        cell_id: str = None,
        gnb_id: int = None
    ) -> Dict[str, Any]:
        """Create 5G cell data."""
        return {
            "cell_id": cell_id or f"cell-{uuid.uuid4().hex[:8]}",
            "gnb_id": gnb_id or random.randint(1, 1000),
            "plmn": "00101",  # Test PLMN
            "tac": random.randint(1, 65535),
            "frequency_band": random.choice([1, 3, 7, 28, 78]),
            "bandwidth_mhz": random.choice([5, 10, 15, 20]),
            "max_ue_count": random.randint(100, 1000),
            "current_ue_count": random.randint(0, 100),
            "status": random.choice(["active", "inactive", "maintenance"]),
            "coverage_area": {
                "center": {
                    "latitude": round(random.uniform(24.5, 25.5), 6),
                    "longitude": round(random.uniform(121.0, 122.0), 6)
                },
                "radius_km": round(random.uniform(1, 10), 2)
            }
        }

# Utility functions
def save_test_data_to_file(data: Any, filename: str):
    """Save test data to JSON file."""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_test_data_from_file(filename: str) -> Any:
    """Load test data from JSON file."""
    with open(filename, 'r') as f:
        return json.load(f)

# Pre-generated test data sets
def get_standard_test_dataset() -> Dict[str, Any]:
    """Get standard test dataset for common scenarios."""
    return {
        "satellites": SatelliteDataFactory.create_constellation(20),
        "uavs": UAVDataFactory.create_uav_fleet(5),
        "handover_events": HandoverDataFactory.create_handover_sequence(15),
        "interference_sources": [
            InterferenceDataFactory.create_interference_source("radar"),
            InterferenceDataFactory.create_interference_source("wifi"),
            InterferenceDataFactory.create_interference_source("lte")
        ],
        "5g_cells": [NetworkDataFactory.create_5g_cell_data() for _ in range(10)]
    }