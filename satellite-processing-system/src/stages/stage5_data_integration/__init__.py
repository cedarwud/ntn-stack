"""
Stage 5: Data Integration Layer (v2.0 Modular Architecture)

Based on stage5-data-integration.md specifications.

📊 v2.0 Modular Architecture Components:

1. TimeseriesConverter - Time series data conversion with interpolation and compression
   * convert_to_timeseries(satellite_pool) → time series dataset
   * generate_time_windows(timeseries, window_duration) → windowed data
   * interpolate_missing_data(timeseries) → interpolated values
   * compress_timeseries(timeseries) → compressed binary data

2. AnimationBuilder - Satellite trajectory animation data generation
   * build_satellite_animation(timeseries) → complete animation data
   * generate_trajectory_keyframes(satellite_timeseries) → keyframes and interpolation
   * create_coverage_animation(satellite_pool) → coverage area animation
   * optimize_animation_performance(animation) → optimized animation data

3. LayerDataGenerator - Hierarchical data structures and indexing
   * generate_hierarchical_data(timeseries) → hierarchical dataset
   * create_spatial_layers(satellite_data) → spatial layering
   * create_temporal_layers(timeseries) → temporal layering
   * build_multi_scale_index(hierarchical_data) → multi-scale index

4. FormatConverterHub - Multi-format output conversion management
   * convert_to_json(data, schema_version) → JSON format
   * convert_to_geojson(spatial_data) → GeoJSON format
   * convert_to_csv(tabular_data) → CSV format
   * package_for_api(data, api_version) → API-ready package

5. DataIntegrationProcessor - Main coordinator for data processing flow
   * Manages the complete data integration pipeline
   * Coordinates quality checks and performance optimization
   * Handles output management and optimization

🎯 Key Features:
- Multi-format data output (JSON, GeoJSON, CSV, XML, API packages)
- Time series processing with interpolation and compression
- Animation data generation for visualization
- Hierarchical data structures for efficient querying
- Performance optimization with >70% compression ratio

⚡ Performance Targets:
- Processing Time: 50-60 seconds for 150-250 satellites
- Memory Usage: <1GB
- Output Formats: 4+ simultaneous formats
- Compression Ratio: >70%
"""

# Import main processor
from .data_integration_processor import DataIntegrationProcessor

# Import v2.0 modular components
from .timeseries_converter import TimeseriesConverter, create_timeseries_converter
from .animation_builder import AnimationBuilder, create_animation_builder
from .layered_data_generator import LayeredDataGenerator
from .format_converter_hub import FormatConverterHub, create_format_converter_hub

# Backward compatibility aliases
Stage5Processor = DataIntegrationProcessor

__all__ = [
    # Main processor
    'DataIntegrationProcessor',
    'Stage5Processor',

    # v2.0 Modular components
    'TimeseriesConverter',
    'AnimationBuilder',
    'LayeredDataGenerator',
    'FormatConverterHub',

    # Factory functions
    'create_timeseries_converter',
    'create_animation_builder',
    'create_format_converter_hub'
]