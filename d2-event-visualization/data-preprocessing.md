# Enhanced Data Preprocessing for D2 Events

## Overview

D2 events require calculating distances to satellite **moving reference locations** (nadir points), not just satellite positions. This document specifies the preprocessing enhancements needed.

## Current vs Required Data

### Current Data Structure
```json
{
  "positions": [{
    "elevation_deg": 83.7,
    "azimuth_deg": 152.6,
    "range_km": 565.9,
    "is_visible": true,
    "timestamp": "2025-07-31T12:00:00Z"
  }]
}
```

### Enhanced D2 Data Structure
```json
{
  "positions": [{
    "elevation_deg": 83.7,
    "azimuth_deg": 152.6,
    "range_km": 565.9,
    "is_visible": true,
    "timestamp": "2025-07-31T12:00:00Z",
    "satellite_position": {
      "lat": 24.95,
      "lon": 121.45,
      "alt_km": 550
    },
    "moving_reference_location": {
      "lat": 24.88,
      "lon": 121.39,
      "distance_to_ue_km": 12.5
    }
  }],
  "d2_events": [{
    "timestamp": "2025-07-31T12:05:30Z",
    "serving_satellite": "starlink-1234",
    "target_satellite": "starlink-5678",
    "ml1_km": 547.3,
    "ml2_km": 238.9,
    "event_type": "entering",
    "duration_seconds": 45
  }]
}
```

## Moving Reference Location Calculation

### Algorithm
```python
def calculate_moving_reference_location(satellite_ecef, timestamp):
    """
    Calculate satellite nadir point (ground projection)
    
    Args:
        satellite_ecef: (x, y, z) in ECEF coordinates
        timestamp: Current time
        
    Returns:
        (lat, lon) of nadir point
    """
    # 1. Normalize satellite position vector
    sat_norm = satellite_ecef / np.linalg.norm(satellite_ecef)
    
    # 2. Project onto Earth surface (WGS84 ellipsoid)
    earth_radius = 6371.0  # km
    nadir_ecef = sat_norm * earth_radius
    
    # 3. Convert ECEF to lat/lon
    lat, lon = ecef_to_latlon(nadir_ecef)
    
    return lat, lon
```

### Integration Points

1. **Modify `preprocess_120min_timeseries.py`**:
   ```python
   # Add to satellite position calculation
   for timestamp in time_points:
       position = sgp4_calculator.propagate_orbit(tle, timestamp)
       
       # NEW: Calculate moving reference location
       mrl = calculate_moving_reference_location(
           position['ecef'], 
           timestamp
       )
       
       # NEW: Calculate distance from UE to MRL
       mrl_distance = haversine_distance(
           ue_position, 
           mrl
       )
   ```

2. **Enhanced File Structure**:
   ```
   /app/data/
   ├── starlink_120min_d2_enhanced.json    # With MRL data
   ├── oneweb_120min_d2_enhanced.json      # With MRL data
   └── d2_events_detected.json             # Detected events
   ```

## D2 Event Detection Algorithm

### Core Logic
```python
def detect_d2_events(satellite_data, thresholds):
    """
    Detect D2 handover events based on dual distance thresholds
    
    D2 triggers when:
    - Ml1 (serving distance) > Thresh1 + Hys
    - Ml2 (target distance) < Thresh2 - Hys
    """
    events = []
    
    # Default thresholds (based on 3GPP recommendations)
    thresh1 = thresholds.get('thresh1', 500)  # km
    thresh2 = thresholds.get('thresh2', 300)  # km
    hys = thresholds.get('hysteresis', 20)    # km
    
    for i, timestamp in enumerate(timestamps):
        serving_ml = serving_satellite['mrl_distances'][i]
        
        # Check all potential targets
        for target_sat in candidate_satellites:
            target_ml = target_sat['mrl_distances'][i]
            
            # D2 entering condition
            if (serving_ml > thresh1 + hys and 
                target_ml < thresh2 - hys):
                
                # Check if new event or continuation
                if not in_event:
                    events.append({
                        'timestamp': timestamp,
                        'type': 'entering',
                        'serving': serving_satellite['id'],
                        'target': target_sat['id'],
                        'ml1': serving_ml,
                        'ml2': target_ml
                    })
                    in_event = True
            
            # D2 leaving condition
            elif in_event and (serving_ml < thresh1 - hys or 
                               target_ml > thresh2 + hys):
                events[-1]['end_timestamp'] = timestamp
                events[-1]['duration'] = calculate_duration()
                in_event = False
    
    return events
```

### Satellite Pairing Strategy

1. **Primary Serving Satellite**: Currently visible with highest elevation
2. **Candidate Targets**: 
   - Same constellation preferred
   - Upcoming visible satellites
   - Elevation > 10° within next 5 minutes

## Performance Optimizations

### 1. Batch Processing
```python
# Process all 70 satellites in parallel
with multiprocessing.Pool() as pool:
    results = pool.map(
        calculate_satellite_mrl,
        satellite_list
    )
```

### 2. Caching Strategy
- Cache MRL calculations (stable for TLE epoch)
- Pre-calculate D2 events for common thresholds
- Store results in optimized binary format

### 3. Memory Efficiency
- Use numpy arrays for time series data
- Compress historical data older than 1 hour
- Stream processing for real-time updates

## Implementation Script

Create `enhance_d2_preprocessing.py`:

```python
import json
import numpy as np
from datetime import datetime, timedelta
from sgp4.api import Satrec, WGS72
from skyfield.api import load, EarthSatellite
from skyfield.positionlib import ICRF

class D2PreprocessingEnhancer:
    def __init__(self, base_data_path):
        self.base_data_path = base_data_path
        self.earth_radius = 6371.0  # km
        
    def enhance_satellite_data(self, constellation):
        """Add MRL calculations to existing preprocessed data"""
        
        # Load existing data
        with open(f'{constellation}_120min_timeseries.json') as f:
            data = json.load(f)
            
        # Enhance each satellite
        for sat_data in data['satellites']:
            sat_data['moving_reference_locations'] = []
            sat_data['mrl_distances'] = []
            
            for pos in sat_data['positions']:
                # Calculate MRL for this position
                mrl = self.calculate_mrl(
                    pos['satellite_ecef']
                )
                
                # Calculate distance from UE to MRL
                distance = self.haversine_distance(
                    data['ue_location'],
                    mrl
                )
                
                sat_data['moving_reference_locations'].append(mrl)
                sat_data['mrl_distances'].append(distance)
        
        # Detect D2 events
        data['d2_events'] = self.detect_d2_events(data)
        
        # Save enhanced data
        output_path = f'{constellation}_120min_d2_enhanced.json'
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        return output_path

# Usage
enhancer = D2PreprocessingEnhancer('/app/data')
enhancer.enhance_satellite_data('starlink')
enhancer.enhance_satellite_data('oneweb')
```

## Validation Requirements

1. **MRL Accuracy**: Verify nadir points are on Earth surface
2. **Distance Consistency**: Ml <= satellite range
3. **Event Detection**: Test with known handover scenarios
4. **Performance**: < 5 seconds for 120-minute preprocessing

## Integration Checklist

- [ ] Modify SGP4Calculator to export ECEF coordinates
- [ ] Add MRL calculation to preprocessing pipeline
- [ ] Implement D2 event detection algorithm
- [ ] Create enhanced data schema
- [ ] Update API endpoints to serve D2 data
- [ ] Add validation tests
- [ ] Performance benchmarking

## Next Steps

1. Implement `enhance_d2_preprocessing.py`
2. Test with sample satellite data
3. Validate MRL calculations against reference
4. Optimize for 70-satellite processing
5. Document API changes in [api-endpoints.md](./api-endpoints.md)