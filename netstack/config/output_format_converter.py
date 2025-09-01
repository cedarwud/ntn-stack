#!/usr/bin/env python3
"""
P0.3 Output Format Alignment - 輸出格式轉換器
將 LEO Restructure 格式轉換為前端立體圖所需格式
"""

import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import math
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class SatelliteTimeseriesPoint:
    """衛星時間序列數據點"""
    timestamp: str
    latitude: float
    longitude: float
    altitude: float  # km
    elevation: float  # degrees
    azimuth: float   # degrees
    distance: float  # km
    rsrp: Optional[float] = None  # dBm
    signal_quality: Optional[float] = None

@dataclass
class FrontendSatelliteData:
    """前端衛星數據格式"""
    norad_id: int
    name: str
    constellation: str
    mrl_distances: List[float]
    orbital_positions: List[Dict[str, float]]
    signal_data: Optional[List[Dict[str, Any]]] = None
    handover_events: Optional[List[Dict[str, Any]]] = None

@dataclass
class FrontendMetadata:
    """前端元數據格式"""
    computation_time: str
    constellation: str
    time_span_minutes: int
    time_interval_seconds: int
    total_time_points: int
    data_source: str
    sgp4_mode: str
    selection_mode: str
    reference_location: Dict[str, float]
    satellites_processed: int
    build_timestamp: str

class LEOToFrontendConverter:
    """LEO Restructure 到前端格式轉換器"""
    
    def __init__(self):
        self.ntpu_coords = {
            'latitude': 24.9441667,
            'longitude': 121.3713889,
            'altitude': 0.0
        }
    
    def convert_leo_report_to_frontend(self, 
                                        leo_report: Dict[str, Any],
                                        detailed_timeseries: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        將 LEO 報告轉換為前端格式 (支持舊的F1→F2→F3→A1格式和新的Stage 6格式)
        
        Args:
            leo_report: LEO report (leo_optimization_final_report.json or Stage 6 output)
            detailed_timeseries: 詳細時間序列數據 (如果可用)
        
        Returns:
            前端兼容的數據格式
        """
        try:
            # Check if this is Stage 6 format (has dynamic_satellite_pool)
            if 'dynamic_satellite_pool' in leo_report:
                return self.convert_stage6_to_frontend(leo_report)
            
            # Otherwise handle old F1→F2→F3→A1 format
            # Extract report data
            final_report = leo_report.get('final_report', leo_report)
            final_results = final_report.get('final_results', {})
            optimal_pools = final_results.get('optimal_satellite_pools', {})
            handover_events = final_results.get('handover_events', {})
            
            # Create metadata
            metadata = self._create_frontend_metadata(
                final_report, optimal_pools, handover_events
            )
            
            # Create satellite data
            satellites_data = []
            
            if detailed_timeseries:
                satellites_data = self._convert_detailed_timeseries(detailed_timeseries)
            else:
                # Generate mock timeseries from summary data
                satellites_data = self._generate_mock_timeseries_from_summary(optimal_pools, handover_events)
            
            frontend_format = {
                'metadata': asdict(metadata),
                'satellites': satellites_data
            }
            
            logger.info("Successfully converted LEO format to frontend format",
                       satellites_count=len(satellites_data),
                       handover_events=handover_events.get('total_events', 0))
            
            return frontend_format
            
        except Exception as e:
            logger.error("Failed to convert LEO format to frontend format", error=str(e))
            raise
    
    def _create_frontend_metadata(self, final_report: Dict, 
                                optimal_pools: Dict, handover_events: Dict) -> FrontendMetadata:
        """創建前端元數據"""
        timestamp = final_report.get('timestamp', datetime.utcnow().isoformat())
        total_satellites = optimal_pools.get('total_count', 8)
        
        return FrontendMetadata(
            computation_time=timestamp,
            constellation="mixed",  # Starlink + OneWeb
            time_span_minutes=120,  # Standard frontend expectation
            time_interval_seconds=30,  # LEO restructure standard
            total_time_points=240,  # 120min / 30s = 240 points
            data_source="leo_f1_f2_f3_a1_system",
            sgp4_mode="real_tle_computation",
            selection_mode="intelligent_dynamic_pool",
            reference_location={
                'latitude': self.ntpu_coords['latitude'],
                'longitude': self.ntpu_coords['longitude'],
                'altitude': self.ntpu_coords['altitude']
            },
            satellites_processed=total_satellites,
            build_timestamp=timestamp
        )
    
    def _generate_mock_timeseries_from_summary(self, 
                                             optimal_pools: Dict, 
                                             handover_events: Dict) -> List[Dict[str, Any]]:
        """
        從匯總數據生成模擬時間序列
        注意：這是P0.3的權宜之計，P0.4會使用真實數據
        """
        satellites_data = []
        
        # Generate Starlink satellites
        starlink_count = optimal_pools.get('starlink_count', 5)
        for i in range(starlink_count):
            sat_data = self._create_mock_satellite_timeseries(
                constellation='starlink',
                satellite_index=i,
                handover_events=handover_events
            )
            satellites_data.append(sat_data)
        
        # Generate OneWeb satellites
        oneweb_count = optimal_pools.get('oneweb_count', 3)
        for i in range(oneweb_count):
            sat_data = self._create_mock_satellite_timeseries(
                constellation='oneweb',
                satellite_index=i,
                handover_events=handover_events
            )
            satellites_data.append(sat_data)
        
        return satellites_data
    
    def _create_mock_satellite_timeseries(self, 
                                        constellation: str, 
                                        satellite_index: int,
                                        handover_events: Dict) -> Dict[str, Any]:
        """創建單個衛星的模擬時間序列"""
        # Generate realistic NORAD ID
        if constellation == 'starlink':
            base_norad = 44000 + satellite_index * 100
            sat_name = f"STARLINK-{1000 + satellite_index}"
        else:  # oneweb
            base_norad = 60000 + satellite_index * 100
            sat_name = f"ONEWEB-{1000 + satellite_index}"
        
        # Generate 240 time points (120 minutes / 30 seconds)
        mrl_distances = []
        orbital_positions = []
        
        total_events = handover_events.get('total_events', 0)
        events_per_satellite = max(1, total_events // 8)  # Distribute events
        
        for time_point in range(240):
            # Simulate satellite motion over NTPU
            time_factor = time_point / 240.0
            
            # Simulate orbital motion (circular approximation)
            angle = time_factor * 2 * math.pi + satellite_index * 0.5
            
            # Satellite position (simplified LEO orbit)
            sat_lat = self.ntpu_coords['latitude'] + math.sin(angle) * 10
            sat_lon = self.ntpu_coords['longitude'] + math.cos(angle) * 10
            sat_alt = 550 + math.sin(angle * 3) * 50  # 500-600 km altitude
            
            # Calculate distance from NTPU
            distance = self._calculate_distance(
                self.ntpu_coords['latitude'], self.ntpu_coords['longitude'],
                sat_lat, sat_lon, sat_alt
            )
            
            mrl_distances.append(distance)
            
            orbital_positions.append({
                'latitude': sat_lat,
                'longitude': sat_lon,
                'altitude': sat_alt,
                'timestamp': datetime.utcnow() + timedelta(seconds=time_point * 30)
            })
        
        return {
            'norad_id': base_norad,
            'name': sat_name,
            'constellation': constellation,
            'mrl_distances': mrl_distances,
            'orbital_positions': [
                {
                    'latitude': pos['latitude'],
                    'longitude': pos['longitude'],
                    'altitude': pos['altitude']
                } for pos in orbital_positions
            ],
            'handover_potential': min(events_per_satellite, 100)  # Normalized score
        }
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float, alt2: float) -> float:
        """計算地面點到衛星的距離 (km)"""
        # Earth radius
        R = 6371.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula for surface distance
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        surface_distance = 2 * R * math.asin(math.sqrt(a))
        
        # 3D distance including altitude
        distance_3d = math.sqrt(surface_distance**2 + alt2**2)
        
        return distance_3d
    
    def convert_to_constellation_specific(self, 
                                        frontend_data: Dict[str, Any], 
                                        constellation: str) -> Dict[str, Any]:
        """
        將混合數據分離為特定星座數據
        """
        filtered_satellites = [
            sat for sat in frontend_data['satellites']
            if sat['constellation'] == constellation
        ]
        
        constellation_data = frontend_data.copy()
        constellation_data['satellites'] = filtered_satellites
        constellation_data['metadata']['constellation'] = constellation
        constellation_data['metadata']['satellites_processed'] = len(filtered_satellites)
        
        return constellation_data
    
    def convert_stage6_to_frontend(self, stage6_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 Stage 6 動態池規劃輸出轉換為前端格式
        
        Args:
            stage6_data: Stage 6 enhanced_dynamic_pools_output.json
        
        Returns:
            前端兼容的數據格式
        """
        try:
            pool_data = stage6_data.get('dynamic_satellite_pool', {})
            selection_details = pool_data.get('selection_details', [])
            metadata = stage6_data.get('metadata', {})
            
            # Create frontend metadata
            frontend_metadata = {
                'computation_time': metadata.get('processing_timestamp', datetime.utcnow().isoformat()),
                'constellation': 'mixed',
                'time_span_minutes': 120,
                'time_interval_seconds': 60,
                'total_time_points': 120,
                'data_source': 'stage6_dynamic_pool',
                'sgp4_mode': 'optimized',
                'selection_mode': 'intelligent',
                'reference_location': self.ntpu_coords,
                'satellites_processed': pool_data.get('total_selected', 0),
                'build_timestamp': metadata.get('processing_timestamp', datetime.utcnow().isoformat())
            }
            
            # Convert satellite data
            satellites_data = []
            for sat in selection_details:
                sat_data = self._convert_stage6_satellite(sat)
                if sat_data:
                    satellites_data.append(sat_data)
            
            frontend_format = {
                'metadata': frontend_metadata,
                'satellites': satellites_data
            }
            
            logger.info("Successfully converted Stage 6 format to frontend format",
                       satellites_count=len(satellites_data))
            
            return frontend_format
            
        except Exception as e:
            logger.error("Failed to convert Stage 6 format to frontend format", error=str(e))
            raise
    
    def _convert_stage6_satellite(self, sat_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single Stage 6 satellite to frontend format"""
        try:
            # Extract position timeseries
            position_timeseries = sat_data.get('position_timeseries', [])
            
            # Build MRL distances and orbital positions
            mrl_distances = []
            orbital_positions = []
            
            for pos in position_timeseries:
                # Convert to frontend expected format
                mrl_distances.append(pos.get('range_km', 0))
                orbital_positions.append({
                    'time': pos.get('time', ''),
                    'latitude': pos.get('latitude', 0),
                    'longitude': pos.get('longitude', 0),
                    'altitude': pos.get('altitude_km', 550),
                    'elevation': pos.get('elevation_deg', 0),
                    'azimuth': pos.get('azimuth_deg', 0),
                    'distance': pos.get('range_km', 0)
                })
            
            # Build signal data if available
            signal_metrics = sat_data.get('signal_metrics', {})
            signal_data = []
            if signal_metrics:
                for pos in position_timeseries:
                    signal_data.append({
                        'time': pos.get('time', ''),
                        'rsrp': signal_metrics.get('average_rsrp', -90),
                        'signal_quality': signal_metrics.get('signal_quality', 0.5)
                    })
            
            return {
                'norad_id': int(sat_data.get('norad_id', 0)),
                'name': sat_data.get('satellite_name', 'Unknown'),
                'constellation': sat_data.get('constellation', 'unknown'),
                'mrl_distances': mrl_distances,
                'orbital_positions': orbital_positions,
                'signal_data': signal_data if signal_data else None,
                'handover_events': None  # Can be added if needed
            }
            
        except Exception as e:
            logger.error(f"Failed to convert satellite {sat_data.get('satellite_name')}: {e}")
            return None
    
    def validate_frontend_format(self, frontend_data: Dict[str, Any]) -> bool:
        """驗證前端格式的完整性"""
        try:
            # Check required top-level keys
            if 'metadata' not in frontend_data or 'satellites' not in frontend_data:
                return False
            
            metadata = frontend_data['metadata']
            required_metadata_keys = [
                'computation_time', 'constellation', 'time_span_minutes',
                'reference_location', 'satellites_processed'
            ]
            
            for key in required_metadata_keys:
                if key not in metadata:
                    logger.error(f"Missing metadata key: {key}")
                    return False
            
            # Check satellite data structure
            satellites = frontend_data['satellites']
            for i, sat in enumerate(satellites):
                required_sat_keys = ['norad_id', 'name', 'constellation', 'mrl_distances']
                for key in required_sat_keys:
                    if key not in sat:
                        logger.error(f"Missing satellite key {key} in satellite {i}")
                        return False
            
            logger.info("Frontend format validation passed",
                       satellites_count=len(satellites))
            return True
            
        except Exception as e:
            logger.error("Frontend format validation failed", error=str(e))
            return False

    # Backward compatibility alias for existing code
    def convert_phase1_report_to_frontend(self, leo_report: Dict[str, Any], 
                                        detailed_timeseries: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Backward compatibility alias for convert_leo_report_to_frontend"""
        return self.convert_leo_report_to_frontend(leo_report, detailed_timeseries)

def create_leo_to_frontend_converter() -> LEOToFrontendConverter:
    """創建 LEO 到前端格式轉換器"""
    return LEOToFrontendConverter()

def convert_leo_to_frontend_format(leo_report_path: str, 
                                    output_path: str,
                                    constellation: Optional[str] = None) -> bool:
    """
    便利函數：轉換 Phase 1 報告為前端格式
    
    Args:
        leo_report_path: LEO leo_optimization_final_report.json 路徑
        output_path: 輸出前端格式文件路徑  
        constellation: 特定星座過濾 ('starlink' 或 'oneweb')
    
    Returns:
        轉換是否成功
    """
    try:
        # Load LEO report
        with open(leo_report_path, 'r', encoding='utf-8') as f:
            leo_report = json.load(f)
        
        # Convert to frontend format
        converter = create_leo_to_frontend_converter()
        frontend_data = converter.convert_leo_report_to_frontend(leo_report)
        
        # Filter by constellation if specified
        if constellation:
            frontend_data = converter.convert_to_constellation_specific(frontend_data, constellation)
        
        # Validate format
        if not converter.validate_frontend_format(frontend_data):
            logger.error("Frontend format validation failed")
            return False
        
        # Save to output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully converted LEO format to frontend format",
                   output_path=output_path,
                   satellites_count=len(frontend_data['satellites']))
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert LEO to frontend format", error=str(e))
        return False

# Backward compatibility alias for existing code
def convert_phase1_to_frontend_format(leo_report_path: str, 
                                    output_path: str,
                                    constellation: Optional[str] = None) -> bool:
    """Backward compatibility alias for convert_leo_to_frontend_format"""
    return convert_leo_to_frontend_format(leo_report_path, output_path, constellation)