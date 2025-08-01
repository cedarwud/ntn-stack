#!/usr/bin/env python3
"""
Enhanced D2 Event Preprocessing Script
Adds Moving Reference Location (MRL) calculations and D2 event detection
to existing satellite time series data
"""

import os
import json
import math
import numpy as np
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class D2PreprocessingEnhancer:
    """Enhances satellite data with MRL calculations for D2 event detection"""
    
    def __init__(self):
        """Initialize the D2 preprocessor"""
        # Detect runtime environment
        if os.path.exists("/app"):
            self.app_root = Path("/app")
        else:
            self.app_root = Path(__file__).parent.parent.parent
        
        self.data_path = self.app_root / "data"
        
        # Earth parameters (WGS84)
        self.earth_radius_equatorial = 6378.137  # km
        self.earth_radius_polar = 6356.752      # km
        self.earth_flattening = 1 / 298.257223563
        
        # Default D2 thresholds
        self.default_thresholds = {
            "thresh1": 500.0,  # km - serving satellite distance threshold
            "thresh2": 300.0,  # km - target satellite distance threshold  
            "hysteresis": 20.0  # km
        }
        
        # Reference location (Taipei Tech University)
        self.ue_location = {
            "lat": 24.9441,
            "lon": 121.3714,
            "alt": 0.0  # km
        }
        
    def enhance_constellation_data(self, constellation: str) -> Optional[str]:
        """
        Enhance existing preprocessed data with MRL calculations
        
        Args:
            constellation: Name of constellation (starlink, oneweb)
            
        Returns:
            Path to enhanced output file or None if failed
        """
        try:
            # Load existing preprocessed data
            input_file = self.data_path / f"{constellation}_120min_timeseries.json"
            if not input_file.exists():
                logger.error(f"❌ Input file not found: {input_file}")
                return None
                
            logger.info(f"📂 Loading existing data from: {input_file}")
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Enhance satellite data with MRL
            logger.info(f"🛰️ Enhancing {len(data.get('satellites', []))} satellites with MRL data")
            enhanced_satellites = self._enhance_satellites_with_mrl(data.get('satellites', []))
            
            # Detect D2 events
            logger.info("🔍 Detecting D2 events...")
            d2_events = self._detect_d2_events(enhanced_satellites, data.get('timestamps', []))
            
            # Create enhanced data structure
            enhanced_data = {
                "metadata": {
                    **data.get('metadata', {}),
                    "d2_enhancement": {
                        "enhanced_at": datetime.now(timezone.utc).isoformat(),
                        "mrl_method": "nadir_projection",
                        "thresholds": self.default_thresholds,
                        "ue_location": self.ue_location
                    }
                },
                "satellites": enhanced_satellites,
                "timestamps": data.get('timestamps', []),
                "ue_trajectory": data.get('ue_trajectory', []),
                "d2_events": d2_events
            }
            
            # Save enhanced data
            output_file = self.data_path / f"{constellation}_120min_d2_enhanced.json"
            logger.info(f"💾 Saving enhanced data to: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2)
            
            # Log statistics
            logger.info(f"✅ Enhancement complete:")
            logger.info(f"   - Satellites processed: {len(enhanced_satellites)}")
            logger.info(f"   - D2 events detected: {len(d2_events)}")
            logger.info(f"   - Output file: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ Enhancement failed: {e}", exc_info=True)
            return None
    
    def _enhance_satellites_with_mrl(self, satellites: List[Dict]) -> List[Dict]:
        """Add MRL calculations to each satellite's position data"""
        enhanced_satellites = []
        
        for sat in satellites:
            try:
                enhanced_sat = sat.copy()
                enhanced_sat['moving_reference_locations'] = []
                enhanced_sat['mrl_distances'] = []
                enhanced_sat['positions'] = []  # Create positions array for compatibility
                
                time_series = sat.get('time_series', [])
                
                for i, ts_point in enumerate(time_series):
                    # Extract position data
                    pos_data = ts_point.get('position', {})
                    
                    # Create position entry for compatibility
                    position = {
                        'elevation_deg': ts_point.get('elevation', 0),
                        'azimuth_deg': ts_point.get('azimuth', 0),
                        'range_km': ts_point.get('range', 0),
                        'is_visible': ts_point.get('is_visible', False),
                        'timestamp': ts_point.get('timestamp')
                    }
                    enhanced_sat['positions'].append(position)
                    
                    # Calculate satellite position in ECEF
                    sat_ecef = self._calculate_satellite_ecef(position)
                    
                    # Calculate MRL (nadir point)
                    mrl_lat, mrl_lon = self._calculate_nadir_point(sat_ecef)
                    
                    # Calculate distance from UE to MRL
                    mrl_distance = self._haversine_distance(
                        self.ue_location['lat'], self.ue_location['lon'],
                        mrl_lat, mrl_lon
                    )
                    
                    # Add to enhanced data
                    enhanced_sat['moving_reference_locations'].append({
                        'lat': mrl_lat,
                        'lon': mrl_lon,
                        'ecef': sat_ecef
                    })
                    enhanced_sat['mrl_distances'].append(mrl_distance)
                
                enhanced_satellites.append(enhanced_sat)
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to enhance satellite {sat.get('name', 'unknown')}: {e}")
                enhanced_satellites.append(sat)  # Keep original if enhancement fails
        
        return enhanced_satellites
    
    def _calculate_satellite_ecef(self, position: Dict) -> Dict[str, float]:
        """
        Calculate satellite ECEF coordinates from position data
        
        Args:
            position: Position dict with elevation_deg, azimuth_deg, range_km
            
        Returns:
            ECEF coordinates dict with x, y, z in km
        """
        # Convert spherical to ECEF relative to UE location
        el_rad = math.radians(position.get('elevation_deg', 0))
        az_rad = math.radians(position.get('azimuth_deg', 0))
        range_km = position.get('range_km', 0)
        
        # Calculate satellite position relative to UE in ENU coordinates
        east = range_km * math.cos(el_rad) * math.sin(az_rad)
        north = range_km * math.cos(el_rad) * math.cos(az_rad)
        up = range_km * math.sin(el_rad)
        
        # Convert UE location to ECEF
        ue_ecef = self._geodetic_to_ecef(
            self.ue_location['lat'], 
            self.ue_location['lon'], 
            self.ue_location['alt']
        )
        
        # Transform ENU to ECEF
        lat_rad = math.radians(self.ue_location['lat'])
        lon_rad = math.radians(self.ue_location['lon'])
        
        # Rotation matrix from ENU to ECEF
        sat_ecef_x = (ue_ecef['x'] - east * math.sin(lon_rad) - 
                      north * math.sin(lat_rad) * math.cos(lon_rad) + 
                      up * math.cos(lat_rad) * math.cos(lon_rad))
        
        sat_ecef_y = (ue_ecef['y'] + east * math.cos(lon_rad) - 
                      north * math.sin(lat_rad) * math.sin(lon_rad) + 
                      up * math.cos(lat_rad) * math.sin(lon_rad))
        
        sat_ecef_z = (ue_ecef['z'] + north * math.cos(lat_rad) + 
                      up * math.sin(lat_rad))
        
        return {'x': sat_ecef_x, 'y': sat_ecef_y, 'z': sat_ecef_z}
    
    def _geodetic_to_ecef(self, lat: float, lon: float, alt: float) -> Dict[str, float]:
        """Convert geodetic coordinates to ECEF"""
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        # Calculate radius of curvature
        N = self.earth_radius_equatorial / math.sqrt(
            1 - (2 * self.earth_flattening - self.earth_flattening**2) * 
            math.sin(lat_rad)**2
        )
        
        # ECEF coordinates
        x = (N + alt) * math.cos(lat_rad) * math.cos(lon_rad)
        y = (N + alt) * math.cos(lat_rad) * math.sin(lon_rad)
        z = ((1 - self.earth_flattening)**2 * N + alt) * math.sin(lat_rad)
        
        return {'x': x, 'y': y, 'z': z}
    
    def _calculate_nadir_point(self, sat_ecef: Dict[str, float]) -> Tuple[float, float]:
        """
        Calculate satellite nadir point (ground projection)
        
        Args:
            sat_ecef: Satellite ECEF coordinates
            
        Returns:
            Tuple of (latitude, longitude) in degrees
        """
        # Normalize satellite position vector
        r = math.sqrt(sat_ecef['x']**2 + sat_ecef['y']**2 + sat_ecef['z']**2)
        
        # Project onto Earth surface (simplified sphere for nadir)
        nadir_x = sat_ecef['x'] / r * self.earth_radius_equatorial
        nadir_y = sat_ecef['y'] / r * self.earth_radius_equatorial  
        nadir_z = sat_ecef['z'] / r * self.earth_radius_equatorial
        
        # Convert ECEF to geodetic
        lon = math.degrees(math.atan2(nadir_y, nadir_x))
        
        # Simplified latitude calculation
        p = math.sqrt(nadir_x**2 + nadir_y**2)
        lat = math.degrees(math.atan2(nadir_z, p))
        
        return lat, lon
    
    def _haversine_distance(self, lat1: float, lon1: float, 
                           lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance between two points on Earth
        
        Returns:
            Distance in kilometers
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2)**2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Use mean Earth radius
        mean_radius = (self.earth_radius_equatorial + self.earth_radius_polar) / 2
        distance = mean_radius * c
        
        return distance
    
    def _detect_d2_events(self, satellites: List[Dict], 
                         timestamps: List[str]) -> List[Dict]:
        """
        Placeholder for D2 event detection - removed deterministic logic
        
        Note: Deterministic handover prediction removed as it's not realistic
        for LEO satellite networks. Real handover decisions should be probabilistic
        and consider multiple factors (signal quality, load, environment, etc.)
        """
        # Return empty list - no predetermined handover events
        logger.info("📊 D2 event detection disabled - using MRL distance visualization only")
        return []


async def main():
    """Main function to run D2 enhancement"""
    logger.info("🚀 Starting D2 Event Enhancement Process")
    
    enhancer = D2PreprocessingEnhancer()
    
    # Process each constellation
    constellations = ['starlink', 'oneweb']
    results = []
    
    for constellation in constellations:
        logger.info(f"\n{'='*60}")
        logger.info(f"📡 Processing constellation: {constellation}")
        logger.info(f"{'='*60}")
        
        result = enhancer.enhance_constellation_data(constellation)
        
        if result:
            results.append({
                'constellation': constellation,
                'status': 'success',
                'output_file': result
            })
        else:
            results.append({
                'constellation': constellation,
                'status': 'failed',
                'output_file': None
            })
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 Enhancement Summary:")
    logger.info(f"{'='*60}")
    
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        logger.info(f"{status_emoji} {result['constellation']}: {result['status']}")
        if result['output_file']:
            logger.info(f"   📄 Output: {result['output_file']}")
    
    # Create status file
    status_file = enhancer.data_path / ".d2_enhancement_status"
    with open(status_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'results': results
        }, f, indent=2)
    
    logger.info(f"\n✅ D2 Enhancement Complete!")
    logger.info(f"📄 Status file: {status_file}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())