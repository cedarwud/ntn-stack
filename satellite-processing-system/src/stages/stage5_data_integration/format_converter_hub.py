"""
Stage 5 Format Converter Hub Module

Unified format conversion management supporting multiple output formats.
Based on stage5-data-integration.md specifications.
"""

import logging
import json
import csv
import xml.etree.ElementTree as ET
import gzip
import zipfile
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import io

logger = logging.getLogger(__name__)

class FormatConverterHub:
    """
    Unified format conversion management for satellite data.

    Responsibilities:
    - Unified format conversion management
    - Support multiple output formats
    - Provide version control
    - Optimize conversion performance
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Format Converter Hub.

        Args:
            config: Configuration dictionary with format settings
        """
        self.config = config or {}
        self.supported_formats = ['json', 'geojson', 'csv', 'xml', 'api_package']
        self.default_schema_version = self.config.get('default_schema_version', 'v1.0')
        self.compression_enabled = self.config.get('compression_enabled', True)
        self.api_version = self.config.get('api_version', 'v1')

        # Format-specific configurations
        self.format_configs = {
            'json': {
                'indent': self.config.get('json_indent', 2),
                'ensure_ascii': False,
                'sort_keys': True
            },
            'csv': {
                'delimiter': self.config.get('csv_delimiter', ','),
                'quoting': csv.QUOTE_MINIMAL,
                'lineterminator': '\n'
            },
            'xml': {
                'encoding': 'utf-8',
                'xml_declaration': True,
                'pretty_print': True
            }
        }

        logger.info(f"FormatConverterHub initialized with formats: {self.supported_formats}")

    def convert_to_json(self, data: Dict[str, Any], schema_version: Optional[str] = None) -> str:
        """
        Convert data to JSON format with schema versioning.

        Args:
            data: Data to convert
            schema_version: JSON schema version to use

        Returns:
            JSON string representation
        """
        try:
            schema_version = schema_version or self.default_schema_version
            logger.info(f"Converting data to JSON (schema: {schema_version})")

            # Add schema metadata
            json_data = {
                'schema': {
                    'version': schema_version,
                    'format': 'json',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                'data': data
            }

            # Apply format configuration
            json_config = self.format_configs['json']
            json_string = json.dumps(json_data, **json_config, default=self._json_serializer)

            logger.info(f"Successfully converted to JSON ({len(json_string)} chars)")
            return json_string

        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            raise

    def convert_to_geojson(self, spatial_data: Dict[str, Any]) -> str:
        """
        Convert spatial data to GeoJSON format.

        Args:
            spatial_data: Spatial data with coordinates and features

        Returns:
            GeoJSON string representation
        """
        try:
            logger.info("Converting spatial data to GeoJSON")

            # Extract satellite positions and create features
            features = []

            # Handle satellite trajectory data
            if 'satellite_trajectories' in spatial_data:
                for sat_id, trajectory in spatial_data['satellite_trajectories'].items():
                    features.extend(self._create_trajectory_features(sat_id, trajectory))

            # Handle coverage data
            if 'coverage_animation' in spatial_data:
                coverage_features = self._create_coverage_features(spatial_data['coverage_animation'])
                features.extend(coverage_features)

            # Handle position timeseries
            if 'timeseries_data' in spatial_data:
                timeseries_features = self._create_timeseries_features(spatial_data['timeseries_data'])
                features.extend(timeseries_features)

            # Build GeoJSON structure
            geojson = {
                'type': 'FeatureCollection',
                'metadata': {
                    'generation_timestamp': datetime.now(timezone.utc).isoformat(),
                    'total_features': len(features),
                    'data_source': 'stage5_data_integration',
                    'coordinate_system': 'WGS84'
                },
                'features': features
            }

            geojson_string = json.dumps(geojson, **self.format_configs['json'], default=self._json_serializer)

            logger.info(f"Successfully converted to GeoJSON ({len(features)} features)")
            return geojson_string

        except Exception as e:
            logger.error(f"Error converting to GeoJSON: {e}")
            raise

    def convert_to_csv(self, tabular_data: Dict[str, Any]) -> str:
        """
        Convert tabular data to CSV format.

        Args:
            tabular_data: Data in tabular format

        Returns:
            CSV string representation
        """
        try:
            logger.info("Converting tabular data to CSV")

            # Flatten data structure for CSV format
            flattened_data = self._flatten_for_csv(tabular_data)

            # Generate CSV manually without pandas
            csv_config = self.format_configs['csv']
            csv_buffer = io.StringIO()

            if flattened_data:
                # Write header
                fieldnames = list(flattened_data[0].keys())
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, **csv_config)
                writer.writeheader()

                # Write data rows
                for row in flattened_data:
                    writer.writerow(row)

            csv_string = csv_buffer.getvalue()

            logger.info(f"Successfully converted to CSV ({len(flattened_data)} rows, {len(flattened_data[0].keys()) if flattened_data else 0} columns)")
            return csv_string

        except Exception as e:
            logger.error(f"Error converting to CSV: {e}")
            raise

    def convert_to_xml(self, data: Dict[str, Any]) -> str:
        """
        Convert data to XML format.

        Args:
            data: Data to convert

        Returns:
            XML string representation
        """
        try:
            logger.info("Converting data to XML")

            # Create root element
            root = ET.Element('satellite_data')
            root.set('timestamp', datetime.now(timezone.utc).isoformat())
            root.set('version', self.default_schema_version)

            # Convert dictionary to XML elements
            self._dict_to_xml(data, root)

            # Generate XML string
            xml_config = self.format_configs['xml']
            xml_string = ET.tostring(root, encoding='unicode')

            # Add XML declaration
            if xml_config.get('xml_declaration', True):
                xml_string = f'<?xml version="1.0" encoding="{xml_config["encoding"]}"?>\n{xml_string}'

            logger.info(f"Successfully converted to XML ({len(xml_string)} chars)")
            return xml_string

        except Exception as e:
            logger.error(f"Error converting to XML: {e}")
            raise

    def package_for_api(self, data: Dict[str, Any], api_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Package data for API consumption with versioning and optimization.

        Args:
            data: Data to package
            api_version: API version to use

        Returns:
            API-ready data package
        """
        try:
            api_version = api_version or self.api_version
            logger.info(f"Packaging data for API (version: {api_version})")

            # Create API package structure
            api_package = {
                'api': {
                    'version': api_version,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'format': 'api_package',
                    'compression': self.compression_enabled
                },
                'metadata': self._extract_api_metadata(data),
                'endpoints': self._create_api_endpoints(data, api_version),
                'data': self._optimize_for_api(data),
                'pagination': self._create_pagination_info(data),
                'links': self._create_api_links(data, api_version)
            }

            logger.info(f"Successfully packaged data for API (version: {api_version})")
            return api_package

        except Exception as e:
            logger.error(f"Error packaging for API: {e}")
            raise

    def convert_multiple_formats(self, data: Dict[str, Any], formats: List[str]) -> Dict[str, Any]:
        """
        Convert data to multiple formats in one operation.

        Args:
            data: Data to convert
            formats: List of target formats

        Returns:
            Dictionary with converted data in each format
        """
        try:
            logger.info(f"Converting data to multiple formats: {formats}")

            results = {}
            conversion_stats = {
                'successful_conversions': 0,
                'failed_conversions': 0,
                'total_formats': len(formats)
            }

            for format_name in formats:
                try:
                    if format_name == 'json':
                        results[format_name] = self.convert_to_json(data)
                    elif format_name == 'geojson':
                        results[format_name] = self.convert_to_geojson(data)
                    elif format_name == 'csv':
                        results[format_name] = self.convert_to_csv(data)
                    elif format_name == 'xml':
                        results[format_name] = self.convert_to_xml(data)
                    elif format_name == 'api_package':
                        results[format_name] = self.package_for_api(data)
                    else:
                        logger.warning(f"Unsupported format: {format_name}")
                        continue

                    conversion_stats['successful_conversions'] += 1

                except Exception as e:
                    logger.error(f"Failed to convert to {format_name}: {e}")
                    conversion_stats['failed_conversions'] += 1
                    results[f"{format_name}_error"] = str(e)

            # Add conversion metadata
            results['conversion_metadata'] = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'statistics': conversion_stats,
                'formats_requested': formats
            }

            logger.info(f"Multi-format conversion completed: "
                       f"{conversion_stats['successful_conversions']}/{conversion_stats['total_formats']} successful")

            return results

        except Exception as e:
            logger.error(f"Error in multi-format conversion: {e}")
            raise

    def compress_output(self, data: Union[str, bytes], format_name: str) -> bytes:
        """
        Compress output data for efficient storage/transmission.

        Args:
            data: Data to compress
            format_name: Format name for compression settings

        Returns:
            Compressed binary data
        """
        try:
            logger.info(f"Compressing {format_name} output")

            # Convert to bytes if necessary
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            else:
                data_bytes = data

            # Apply compression
            compressed_data = gzip.compress(data_bytes, compresslevel=6)

            original_size = len(data_bytes)
            compressed_size = len(compressed_data)
            compression_ratio = compressed_size / original_size

            logger.info(f"Compression completed: {original_size} -> {compressed_size} bytes "
                       f"(ratio: {compression_ratio:.3f})")

            return compressed_data

        except Exception as e:
            logger.error(f"Error compressing output: {e}")
            raise

    def create_format_bundle(self, data: Dict[str, Any], bundle_formats: List[str]) -> bytes:
        """
        Create a compressed bundle containing multiple formats.

        Args:
            data: Data to convert and bundle
            bundle_formats: List of formats to include in bundle

        Returns:
            Compressed ZIP bundle
        """
        try:
            logger.info(f"Creating format bundle with formats: {bundle_formats}")

            # Convert to all requested formats
            format_outputs = self.convert_multiple_formats(data, bundle_formats)

            # Create ZIP bundle
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:

                # Add each format to the bundle
                for format_name, format_data in format_outputs.items():
                    if not format_name.endswith('_error') and format_name != 'conversion_metadata':

                        # Determine file extension
                        if format_name == 'json':
                            filename = 'satellite_data.json'
                        elif format_name == 'geojson':
                            filename = 'satellite_data.geojson'
                        elif format_name == 'csv':
                            filename = 'satellite_data.csv'
                        elif format_name == 'xml':
                            filename = 'satellite_data.xml'
                        elif format_name == 'api_package':
                            filename = 'api_package.json'
                            format_data = json.dumps(format_data, **self.format_configs['json'], default=self._json_serializer)
                        else:
                            filename = f'{format_name}_data.txt'

                        # Add to ZIP
                        zipf.writestr(filename, format_data)

                # Add metadata file
                metadata = {
                    'bundle_info': {
                        'creation_timestamp': datetime.now(timezone.utc).isoformat(),
                        'formats_included': bundle_formats,
                        'total_files': len(bundle_formats),
                        'creator': 'FormatConverterHub'
                    },
                    'conversion_stats': format_outputs.get('conversion_metadata', {})
                }
                zipf.writestr('bundle_metadata.json', json.dumps(metadata, indent=2))

            bundle_data = zip_buffer.getvalue()

            logger.info(f"Created format bundle ({len(bundle_data)} bytes)")
            return bundle_data

        except Exception as e:
            logger.error(f"Error creating format bundle: {e}")
            raise

    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)

    def _create_trajectory_features(self, sat_id: str, trajectory: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create GeoJSON features from satellite trajectory data."""
        features = []

        keyframes = trajectory.get('keyframes', [])
        for i, keyframe in enumerate(keyframes):
            position = keyframe.get('position', {})

            if 'longitude' in position and 'latitude' in position:
                feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [position['longitude'], position['latitude'], position.get('altitude', 0)]
                    },
                    'properties': {
                        'satellite_id': sat_id,
                        'frame_index': keyframe.get('frame_index', i),
                        'timestamp': keyframe.get('timestamp', 0),
                        'elevation': keyframe.get('elevation', 0),
                        'is_visible': keyframe.get('is_visible', False),
                        'feature_type': 'satellite_position'
                    }
                }
                features.append(feature)

        # Create trajectory line if we have multiple points
        if len(keyframes) > 1:
            coordinates = []
            for kf in keyframes:
                pos = kf.get('position', {})
                if 'longitude' in pos and 'latitude' in pos:
                    coordinates.append([pos['longitude'], pos['latitude'], pos.get('altitude', 0)])

            if coordinates:
                trajectory_feature = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': coordinates
                    },
                    'properties': {
                        'satellite_id': sat_id,
                        'feature_type': 'satellite_trajectory',
                        'total_points': len(coordinates)
                    }
                }
                features.append(trajectory_feature)

        return features

    def _create_coverage_features(self, coverage_animation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create GeoJSON features from coverage animation data."""
        features = []

        frames = coverage_animation.get('frames', [])
        for frame in frames[:10]:  # Limit to first 10 frames for performance
            footprints = frame.get('satellite_footprints', [])

            for footprint in footprints:
                # Create circular footprint feature
                center_lat = footprint.get('center_latitude', 0)
                center_lon = footprint.get('center_longitude', 0)
                radius_km = footprint.get('radius_km', 0)

                if radius_km > 0:
                    # Approximate circle with polygon (simplified)
                    coordinates = self._create_circle_coordinates(center_lat, center_lon, radius_km)

                    feature = {
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Polygon',
                            'coordinates': [coordinates]
                        },
                        'properties': {
                            'satellite_id': footprint.get('satellite_id'),
                            'frame_index': frame.get('frame_index'),
                            'coverage_radius_km': radius_km,
                            'feature_type': 'satellite_footprint'
                        }
                    }
                    features.append(feature)

        return features

    def _create_timeseries_features(self, timeseries_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create GeoJSON features from real timeseries data (no performance limits that compromise data integrity)."""
        try:
            # 🚨 Grade A要求：使用完整的真實時間序列數據，絕不因性能而截斷數據
            
            features = []
            satellite_timeseries = timeseries_data.get('satellite_timeseries', {})
            
            if not satellite_timeseries:
                self.logger.warning("無時間序列數據可轉換")
                return features
            
            for sat_id, sat_data in satellite_timeseries.items():
                try:
                    # 從真實的Stage 1-4處理結果獲取位置數據
                    positions = sat_data.get('positions', [])
                    elevations = sat_data.get('elevation_angles', [])
                    visibilities = sat_data.get('visibility_status', [])
                    rsrp_values = sat_data.get('rsrp_values', [])
                    snr_values = sat_data.get('snr_values', [])
                    
                    if not positions:
                        self.logger.warning(f"衛星 {sat_id} 無位置數據")
                        continue
                    
                    # 🚨 處理完整數據集，不因性能而限制 (Grade A要求)
                    for i, position in enumerate(positions):
                        if not isinstance(position, dict):
                            continue
                            
                        longitude = position.get('longitude', None)
                        latitude = position.get('latitude', None)
                        
                        if longitude is None or latitude is None:
                            continue
                        
                        # 構建完整的特徵屬性 (真實數據)
                        properties = {
                            'satellite_id': sat_id,
                            'time_index': i,
                            'feature_type': 'timeseries_position',
                            'data_source': 'stage1_to_4_real_processing'
                        }
                        
                        # 添加真實的信號品質數據
                        if i < len(elevations):
                            properties['elevation_deg'] = elevations[i]
                        if i < len(visibilities):
                            properties['is_visible'] = visibilities[i]
                        if i < len(rsrp_values):
                            properties['rsrp_dbm'] = rsrp_values[i]
                        if i < len(snr_values):
                            properties['snr_db'] = snr_values[i]
                        
                        # 添加軌道數據 (如果可用)
                        if 'x' in position and 'y' in position and 'z' in position:
                            properties['cartesian_coordinates'] = {
                                'x_km': position['x'],
                                'y_km': position['y'], 
                                'z_km': position['z']
                            }
                        
                        feature = {
                            'type': 'Feature',
                            'geometry': {
                                'type': 'Point',
                                'coordinates': [
                                    longitude,
                                    latitude,
                                    position.get('altitude', 0)
                                ]
                            },
                            'properties': properties
                        }
                        features.append(feature)
                        
                except Exception as e:
                    self.logger.error(f"處理衛星 {sat_id} 時間序列數據失敗: {e}")
                    continue
            
            self.logger.info(f"成功從真實時間序列數據創建 {len(features)} 個GeoJSON特徵")
            return features
            
        except Exception as e:
            self.logger.error(f"時間序列特徵創建失敗: {e}")
            # Grade A要求：失敗時拋出異常，絕不返回空數據
            raise ValueError(f"無法從真實時間序列數據創建特徵: {e}")

    def _create_circle_coordinates(self, center_lat: float, center_lon: float, radius_km: float, points: int = 16) -> List[List[float]]:
        """Create approximate circle coordinates for satellite footprint."""
        import math

        coordinates = []
        earth_radius = 6371.0  # km

        for i in range(points + 1):  # +1 to close the polygon
            angle = 2 * math.pi * i / points

            # Approximate offset in degrees
            lat_offset = (radius_km / earth_radius) * (180 / math.pi) * math.cos(angle)
            lon_offset = (radius_km / earth_radius) * (180 / math.pi) * math.sin(angle) / math.cos(math.radians(center_lat))

            lat = center_lat + lat_offset
            lon = center_lon + lon_offset

            coordinates.append([lon, lat])

        return coordinates

    def _flatten_for_csv(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flatten nested data structure for CSV format."""
        flattened_rows = []

        # Handle different data types
        if 'satellite_timeseries' in data:
            # Flatten timeseries data
            satellite_timeseries = data['satellite_timeseries']
            for sat_id, sat_data in satellite_timeseries.items():
                positions = sat_data.get('positions', [])
                elevations = sat_data.get('elevation_angles', [])
                visibilities = sat_data.get('visibility_status', [])

                for i in range(len(positions)):
                    row = {
                        'satellite_id': sat_id,
                        'time_index': i,
                        'latitude': positions[i].get('latitude', 0) if i < len(positions) else 0,
                        'longitude': positions[i].get('longitude', 0) if i < len(positions) else 0,
                        'altitude': positions[i].get('altitude', 0) if i < len(positions) else 0,
                        'elevation_angle': elevations[i] if i < len(elevations) else 0,
                        'is_visible': visibilities[i] if i < len(visibilities) else False
                    }
                    flattened_rows.append(row)

        elif 'layers' in data:
            # Flatten layered data
            for layer_name, layer_data in data['layers'].items():
                satellites = layer_data.get('satellites', [])
                for satellite in satellites:
                    row = {
                        'layer': layer_name,
                        'satellite_id': satellite.get('satellite_id'),
                        'constellation': satellite.get('constellation'),
                        'analysis_status': satellite.get('analysis_status'),
                        'quality_score': satellite.get('quality_metrics', {}).get('overall_score', 0)
                    }
                    flattened_rows.append(row)

        else:
            # Generic flattening
            flattened_rows = [{'key': k, 'value': str(v)} for k, v in data.items()]

        return flattened_rows

    def _dict_to_xml(self, data: Dict[str, Any], parent: ET.Element):
        """Convert dictionary to XML elements recursively."""
        for key, value in data.items():
            # Clean key for XML element name
            clean_key = str(key).replace(' ', '_').replace('-', '_')

            if isinstance(value, dict):
                child = ET.SubElement(parent, clean_key)
                self._dict_to_xml(value, child)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        child = ET.SubElement(parent, f"{clean_key}_item")
                        child.set('index', str(i))
                        self._dict_to_xml(item, child)
                    else:
                        child = ET.SubElement(parent, f"{clean_key}_item")
                        child.set('index', str(i))
                        child.text = str(item)
            else:
                child = ET.SubElement(parent, clean_key)
                child.text = str(value)

    def _extract_api_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata for API package."""
        return {
            'data_type': 'satellite_processing_stage5',
            'record_count': self._count_records(data),
            'data_keys': list(data.keys()),
            'generation_timestamp': datetime.now(timezone.utc).isoformat()
        }

    def _count_records(self, data: Dict[str, Any]) -> int:
        """Count total records in data structure."""
        count = 0

        if 'satellite_timeseries' in data:
            count += len(data['satellite_timeseries'])
        elif 'layers' in data:
            for layer in data['layers'].values():
                count += len(layer.get('satellites', []))
        else:
            count = len(data)

        return count

    def _create_api_endpoints(self, data: Dict[str, Any], api_version: str) -> Dict[str, str]:
        """Create API endpoint information."""
        base_url = f"/api/{api_version}/satellite-data"

        endpoints = {
            'base': base_url,
            'timeseries': f"{base_url}/timeseries",
            'animation': f"{base_url}/animation",
            'layers': f"{base_url}/layers",
            'metadata': f"{base_url}/metadata"
        }

        return endpoints

    def _optimize_for_api(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data structure for API consumption."""
        # Remove large binary data, limit array sizes, etc.
        optimized = data.copy()

        # Limit timeseries data for API performance
        if 'satellite_timeseries' in optimized:
            for sat_id, sat_data in optimized['satellite_timeseries'].items():
                for key, values in sat_data.items():
                    if isinstance(values, list) and len(values) > 1000:
                        # Sample every nth element to reduce size
                        step = len(values) // 1000
                        optimized['satellite_timeseries'][sat_id][key] = values[::step]

        return optimized

    def _create_pagination_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create pagination information for API."""
        total_records = self._count_records(data)
        page_size = 100
        total_pages = (total_records + page_size - 1) // page_size

        return {
            'page_size': page_size,
            'total_records': total_records,
            'total_pages': total_pages,
            'current_page': 1
        }

    def _create_api_links(self, data: Dict[str, Any], api_version: str) -> Dict[str, str]:
        """Create API links for navigation."""
        base_url = f"/api/{api_version}/satellite-data"

        return {
            'self': base_url,
            'related': {
                'raw_data': f"{base_url}/raw",
                'processed_data': f"{base_url}/processed",
                'download': f"{base_url}/download"
            }
        }


def create_format_converter_hub(config: Optional[Dict[str, Any]] = None) -> FormatConverterHub:
    """
    Factory function to create FormatConverterHub instance.

    Args:
        config: Configuration dictionary

    Returns:
        Configured FormatConverterHub instance
    """
    return FormatConverterHub(config)