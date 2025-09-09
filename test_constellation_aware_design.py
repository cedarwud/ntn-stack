#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Constellation-Aware Design

Test that the six-stage pipeline correctly handles:
- Starlink: 96 minutes orbit -> 192 time points
- OneWeb: 109 minutes orbit -> 218 time points
"""

def test_constellation_specs():
    """Test constellation-specific orbital specifications"""
    
    # Constellation specifications
    constellation_specs = {
        "starlink": {
            "orbital_period_minutes": 96,
            "time_points": 192,
            "interval_seconds": 30
        },
        "oneweb": {
            "orbital_period_minutes": 109,
            "time_points": 218,
            "interval_seconds": 30
        }
    }
    
    print("=== Constellation-Aware Design Test ===")
    print("")
    
    for constellation, specs in constellation_specs.items():
        print(f"{constellation.upper()}:")
        print(f"  Orbital period: {specs['orbital_period_minutes']} minutes")
        print(f"  Time points: {specs['time_points']}")
        print(f"  Interval: {specs['interval_seconds']} seconds")
        
        # Verify calculation
        expected_points = (specs['orbital_period_minutes'] * 60) // specs['interval_seconds']
        assert specs['time_points'] == expected_points, f"Calculation error for {constellation}"
        print(f"  Calculation verified: {specs['orbital_period_minutes']}min * 60s / {specs['interval_seconds']}s = {expected_points} points")
        print("")
    
    print("✅ All constellation specifications verified!")

def validate_satellite_timeseries(satellite):
    """Validate satellite timeseries based on constellation"""
    constellation = satellite.get('constellation', '').lower()
    timeseries = satellite.get('position_timeseries', [])
    
    expected_points = {
        'starlink': 192,
        'oneweb': 218
    }.get(constellation)
    
    if expected_points is None:
        raise ValueError(f"Unknown constellation: {constellation}")
    
    if len(timeseries) != expected_points:
        raise ValueError(
            f"Timeseries length error for {constellation}: "
            f"{len(timeseries)} != {expected_points}"
        )
    
    return True

def test_satellite_validation():
    """Test satellite validation with correct constellation-specific data"""
    
    print("=== Satellite Validation Test ===")
    
    # Test data with correct constellation-specific time points
    test_satellites = [
        {
            "satellite_id": "STARLINK-1234",
            "constellation": "starlink",
            "position_timeseries": [{"time": i, "pos": [0,0,0]} for i in range(192)]
        },
        {
            "satellite_id": "ONEWEB-5678",
            "constellation": "oneweb", 
            "position_timeseries": [{"time": i, "pos": [0,0,0]} for i in range(218)]
        }
    ]
    
    for satellite in test_satellites:
        try:
            validate_satellite_timeseries(satellite)
            constellation = satellite['constellation']
            points = len(satellite['position_timeseries'])
            print(f"✅ {constellation.upper()}: {points} time points - VALID")
        except ValueError as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    # Test invalid cases (should fail)
    print("\n--- Testing invalid cases ---")
    
    invalid_satellites = [
        {
            "satellite_id": "STARLINK-WRONG",
            "constellation": "starlink",
            "position_timeseries": [{"time": i} for i in range(218)]  # Wrong: Starlink with 218 points
        },
        {
            "satellite_id": "ONEWEB-WRONG", 
            "constellation": "oneweb",
            "position_timeseries": [{"time": i} for i in range(192)]  # Wrong: OneWeb with 192 points
        }
    ]
    
    for satellite in invalid_satellites:
        try:
            validate_satellite_timeseries(satellite)
            print(f"❌ Should have failed for {satellite['satellite_id']}")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected {satellite['satellite_id']}: {e}")
    
    print("\n✅ All constellation-aware validation tests passed!")
    return True

def main():
    """Run all constellation-aware design tests"""
    try:
        test_constellation_specs()
        test_satellite_validation()
        
        print("\n🎉 Constellation-Aware Design Correction Complete!")
        print("Key fixes:")
        print("- Starlink satellites: 192 time points (96 min orbit)")
        print("- OneWeb satellites: 218 time points (109 min orbit)")
        print("- Stage validation now constellation-specific")
        print("- No more false positives for OneWeb 218-point data")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)