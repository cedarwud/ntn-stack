#!/usr/bin/env python3
"""
Generate D2 Event Demo Data with Realistic MRL Distance Variations
This creates demonstration data that simulates satellite MRL distance changes for D2 event visualization
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

def generate_mrl_distances_with_events(time_points: int = 720, constellation: str = "starlink"):
    """
    Generate realistic MRL distances that include D2 events
    
    Uses sinusoidal patterns to simulate satellite orbital motion relative to UE
    """
    # Time array (10 second intervals)
    t = np.linspace(0, 120 * 60, time_points)  # 120 minutes in seconds
    
    # Base parameters for satellite motion
    if constellation == "starlink":
        # Starlink LEO parameters
        orbital_period = 95 * 60  # ~95 minutes
        min_distance = 180  # km (when overhead)
        max_distance = 800  # km (at horizon)
    else:
        # OneWeb parameters
        orbital_period = 109 * 60  # ~109 minutes  
        min_distance = 250  # km
        max_distance = 1000  # km
    
    # Generate distances for multiple satellites
    satellites = []
    
    # Serving satellite (starts close, moves away)
    serving_distances = []
    for i, time_sec in enumerate(t):
        # Simulate satellite moving from overhead to horizon
        phase = (time_sec / orbital_period) * 2 * np.pi
        # Start at minimum distance, increase over time
        distance = min_distance + (max_distance - min_distance) * (1 + np.sin(phase - np.pi/2)) / 2
        # Add some noise
        distance += np.random.normal(0, 5)
        serving_distances.append(max(min_distance, distance))
    
    # Target satellite (starts far, gets closer)
    target_distances = []
    for i, time_sec in enumerate(t):
        # Simulate satellite moving from horizon to overhead
        phase = (time_sec / orbital_period) * 2 * np.pi + np.pi
        # Start at maximum distance, decrease over time
        distance = min_distance + (max_distance - min_distance) * (1 + np.sin(phase - np.pi/2)) / 2
        # Add some noise
        distance += np.random.normal(0, 5)
        target_distances.append(max(min_distance, distance))
    
    # Create crossing point for D2 event around middle of timeline
    # Adjust distances to ensure they cross thresholds
    crossover_index = time_points // 2
    
    # Smooth transition around crossover
    for i in range(crossover_index - 50, crossover_index + 50):
        if 0 <= i < time_points:
            # Serving satellite moves beyond thresh1
            if serving_distances[i] < 500:
                serving_distances[i] = 450 + (i - crossover_index + 50) * 1.5
            
            # Target satellite comes within thresh2  
            if target_distances[i] > 300:
                target_distances[i] = 350 - (i - crossover_index + 50) * 1.5
    
    return serving_distances, target_distances

def main():
    """Generate enhanced D2 demo data for both constellations"""
    
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    # Base timestamp
    base_time = datetime.utcnow().replace(second=0, microsecond=0)
    
    for constellation in ["starlink", "oneweb"]:
        print(f"🛰️ Generating D2 demo data for {constellation}")
        
        # Generate MRL distances with D2 events
        serving_distances, target_distances = generate_mrl_distances_with_events(
            constellation=constellation
        )
        
        # Load existing data structure as template
        existing_file = output_dir / f"{constellation}_120min_d2_enhanced.json"
        if existing_file.exists():
            with open(existing_file, 'r') as f:
                data = json.load(f)
        else:
            # Create minimal structure
            data = {
                "metadata": {
                    "constellation": constellation,
                    "time_span_minutes": 120,
                    "d2_enhancement": {
                        "thresholds": {
                            "thresh1": 500.0,
                            "thresh2": 300.0,
                            "hysteresis": 20.0
                        }
                    }
                },
                "satellites": [],
                "timestamps": [],
                "d2_events": []
            }
        
        # Update satellite MRL distances
        if len(data["satellites"]) >= 2:
            # Update first two satellites as serving/target
            data["satellites"][0]["mrl_distances"] = serving_distances
            data["satellites"][0]["name"] = f"{constellation.upper()}-SERVING"
            
            data["satellites"][1]["mrl_distances"] = target_distances  
            data["satellites"][1]["name"] = f"{constellation.upper()}-TARGET"
            
            # Ensure time_series exists with proper timestamps
            for sat_idx in range(2):
                if "time_series" not in data["satellites"][sat_idx]:
                    data["satellites"][sat_idx]["time_series"] = []
                
                # Update or create time series entries
                time_series = []
                for i in range(720):
                    timestamp = base_time + timedelta(seconds=i*10)
                    entry = {
                        "timestamp": timestamp.isoformat() + "Z",
                        "time_offset_seconds": i * 10,
                        "position": {"ecef": {"x": 0, "y": 0, "z": 0}},
                        "observation": {},
                        "handover_metrics": {},
                        "measurement_events": {}
                    }
                    time_series.append(entry)
                
                data["satellites"][sat_idx]["time_series"] = time_series
        
        # Detect D2 events
        thresh1 = data["metadata"]["d2_enhancement"]["thresholds"]["thresh1"]
        thresh2 = data["metadata"]["d2_enhancement"]["thresholds"]["thresh2"]
        hysteresis = data["metadata"]["d2_enhancement"]["thresholds"]["hysteresis"]
        
        d2_events = []
        in_d2_event = False
        d2_start_idx = None
        
        for i in range(len(serving_distances)):
            ml1 = serving_distances[i]
            ml2 = target_distances[i]
            
            # Check D2 conditions
            condition1 = ml1 > (thresh1 + hysteresis)  # Serving satellite too far
            condition2 = ml2 < (thresh2 - hysteresis)  # Target satellite close enough
            
            if condition1 and condition2 and not in_d2_event:
                # D2 event starts
                in_d2_event = True
                d2_start_idx = i
            elif in_d2_event and (not condition1 or not condition2):
                # D2 event ends
                in_d2_event = False
                if d2_start_idx is not None:
                    timestamp_start = base_time + timedelta(seconds=d2_start_idx*10)
                    timestamp_end = base_time + timedelta(seconds=i*10)
                    
                    d2_event = {
                        "id": f"d2_event_{len(d2_events)+1}",
                        "timestamp_start": timestamp_start.isoformat() + "Z",
                        "timestamp_end": timestamp_end.isoformat() + "Z",
                        "serving_satellite": {
                            "name": f"{constellation.upper()}-SERVING",
                            "id": "serving"
                        },
                        "target_satellite": {
                            "name": f"{constellation.upper()}-TARGET",
                            "id": "target"
                        },
                        "ml1_start": serving_distances[d2_start_idx],
                        "ml1_end": ml1,
                        "ml2_start": target_distances[d2_start_idx],
                        "ml2_end": ml2,
                        "duration_seconds": (i - d2_start_idx) * 10
                    }
                    d2_events.append(d2_event)
        
        data["d2_events"] = d2_events
        
        # Save demo data
        demo_file = output_dir / f"{constellation}_120min_d2_demo.json"
        with open(demo_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Generated demo data with {len(d2_events)} D2 events: {demo_file}")
        
        # Also save as enhanced file for immediate use
        enhanced_file = output_dir / f"{constellation}_120min_d2_enhanced.json"
        with open(enhanced_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Updated enhanced file: {enhanced_file}")

if __name__ == "__main__":
    main()