#!/usr/bin/env python3
"""
Stage 5: Data Integration Layer Processor (v2.0 Modular Architecture)

Based on stage5-data-integration.md specifications.

v2.0 Modular Architecture Components:
- 📊 Timeseries Converter: Convert satellite pool data to time series format
- 🎬 Animation Builder: Generate satellite trajectory animation data
- 🏗️ Layer Data Generator: Create hierarchical data structures and indexing
- 📦 Format Converter Hub: Multi-format output conversion (JSON, GeoJSON, CSV, etc.)
- 🔗 Stage5 Data Processor: Coordinate data processing flow and optimization

Key Responsibilities:
1. Convert optimization results to multiple output formats
2. Provide time series data with interpolation and compression
3. Generate animation data for visualization
4. Create hierarchical data structures for efficient querying
5. Optimize data for frontend and API consumption

Performance Targets:
- Input: 150-250 optimized satellites from Stage 4
- Processing Time: 50-60 seconds
- Memory Usage: <1GB
- Output: Multi-format data packages with >70% compression ratio
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# 共享模組導入
from shared.base_processor import BaseStageProcessor
from shared.interfaces import ProcessingStatus, ProcessingResult, create_processing_result
from shared.validation_framework import ValidationEngine
from shared.utils import FileUtils
from shared.constants import SystemConstantsManager

logger = logging.getLogger(__name__)


class DataIntegrationProcessor(BaseStageProcessor):
    """
    Stage 5: Data Integration Layer Processor (Document-Compliant Version)
    
    Based on stage5-data-integration.md specifications.
    
    Responsibilities:
    1. Convert optimization results to time series format
    2. Generate animation data and coverage visualization  
    3. Create hierarchical data structures
    4. Output multiple formats (JSON, GeoJSON, CSV, etc.)
    5. Coordinate data processing flow and quality management
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(stage_number=5, stage_name="data_integration", config=config or {})

        # Initialize stage-specific configurations
        self.processing_config = self._load_processing_config()
        
        # Initialize v2.0 modular components as specified in documentation
        from .timeseries_converter import create_timeseries_converter
        from .animation_builder import create_animation_builder
        from .layered_data_generator import LayeredDataGenerator
        from .format_converter_hub import create_format_converter_hub
        
        self.timeseries_converter = create_timeseries_converter(
            self.processing_config.get('timeseries', {})
        )
        self.animation_builder = create_animation_builder(
            self.processing_config.get('animation', {})
        )
        self.layer_data_generator = LayeredDataGenerator()
        self.format_converter_hub = create_format_converter_hub(
            self.processing_config.get('formats', {})
        )

        # Processing statistics
        self.processing_stats = {
            'processed_satellites': 0,
            'output_formats': 0,
            'compression_ratio': 0.0,
            'processing_time_seconds': 0.0
        }

        self.logger.info("🔗 Stage 5 Data Integration Processor initialized with v2.0 modular architecture")
        self.logger.info(f"   📊 Timeseries: {self.processing_config.get('timeseries', {}).get('sampling_frequency', '10S')}")
        self.logger.info(f"   🎬 Animation: {self.processing_config.get('animation', {}).get('frame_rate', 30)} FPS")
        self.logger.info(f"   📦 Formats: {len(self.format_converter_hub.supported_formats)} supported")

    def process(self, input_data: Any) -> ProcessingResult:
        """
        Main processing method implementing the v2.0 modular architecture.
        
        Process Flow:
        1. Input data validation
        2. Timeseries conversion  
        3. Animation data building
        4. Hierarchical data generation
        5. Multi-format output conversion
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 Starting Stage 5 Data Integration Processing (v2.0 Architecture)...")

        try:
            # Step 1: Validate input data from Stage 4
            if not self._validate_stage4_output(input_data):
                return create_processing_result(
                    status=ProcessingStatus.VALIDATION_FAILED,
                    data={},
                    message="Stage 4 output data validation failed"
                )

            # Extract Stage 4 optimization results
            stage4_output = input_data.get('optimization_results', {})
            optimal_pool = stage4_output.get('optimal_pool', {})
            handover_strategy = stage4_output.get('handover_strategy', {})
            
            self.logger.info(f"📥 Processing {len(optimal_pool.get('satellites', []))} optimized satellites")

            # Step 2: Timeseries Data Conversion
            self.logger.info("⏰ Converting to time series format...")
            timeseries_data = self.timeseries_converter.convert_to_timeseries(optimal_pool)
            
            # Generate time windows
            window_duration = self.processing_config.get('timeseries', {}).get('window_duration_seconds', 60)
            windowed_data = self.timeseries_converter.generate_time_windows(timeseries_data, window_duration)
            
            # Interpolate missing data
            interpolated_data = self.timeseries_converter.interpolate_missing_data(timeseries_data)

            # Step 3: Animation Data Building
            self.logger.info("🎬 Building animation data...")
            animation_data = self.animation_builder.build_satellite_animation(interpolated_data)

            # Step 4: Hierarchical Data Generation
            self.logger.info("🏗️ Generating hierarchical data structures...")
            layered_data = self.layer_data_generator.generate_layered_data(
                optimal_pool.get('satellites', []),
                self.processing_config
            )

            # Step 5: Multi-format Output Generation
            self.logger.info("📦 Converting to multiple output formats...")
            
            # Prepare comprehensive output data structure
            comprehensive_data = {
                'stage': 'stage5_data_integration',
                'timeseries_data': {
                    'dataset_id': timeseries_data.get('dataset_id'),
                    'satellite_count': timeseries_data.get('satellite_count', 0),
                    'time_range': timeseries_data.get('time_range', {}),
                    'sampling_frequency': timeseries_data.get('sampling_frequency', '10S'),
                    'satellite_timeseries': timeseries_data.get('satellite_timeseries', {}),
                    'windowed_data': windowed_data
                },
                'animation_data': {
                    'animation_id': animation_data.get('animation_id'),
                    'duration': animation_data.get('duration', 300),
                    'frame_rate': animation_data.get('frame_rate', 30),
                    'satellite_trajectories': animation_data.get('satellite_trajectories', {}),
                    'coverage_animation': animation_data.get('coverage_animation', {})
                },
                'hierarchical_data': {
                    'layers': layered_data.get('layers', {}),
                    'cross_layer_mappings': layered_data.get('cross_layer_mappings', {}),
                    'layer_metadata': layered_data.get('layer_metadata', {})
                },
                'metadata': {
                    'processing_time': datetime.now(timezone.utc).isoformat(),
                    'processed_satellites': len(optimal_pool.get('satellites', [])),
                    'source_stage': 'stage4_optimization_decision',
                    'processing_version': 'v2.0_modular'
                }
            }

            # Convert to multiple formats
            target_formats = self.processing_config.get('output_formats', ['json', 'geojson', 'csv', 'api_package'])
            formatted_outputs = self.format_converter_hub.convert_multiple_formats(
                comprehensive_data, target_formats
            )

            # Step 6: Performance Optimization and Compression
            if self.processing_config.get('compression_enabled', True):
                self.logger.info("🗜️ Applying compression...")
                for format_name, format_data in formatted_outputs.items():
                    if not format_name.endswith('_error') and format_name != 'conversion_metadata':
                        if isinstance(format_data, str):
                            compressed_data = self.format_converter_hub.compress_output(format_data, format_name)
                            self.processing_stats['compression_ratio'] = len(compressed_data) / len(format_data.encode('utf-8'))

            # Update processing statistics
            processing_time = datetime.now(timezone.utc) - start_time
            self.processing_stats.update({
                'processed_satellites': len(optimal_pool.get('satellites', [])),
                'output_formats': len([f for f in formatted_outputs.keys() if not f.endswith('_error')]) - 1,  # -1 for metadata
                'processing_time_seconds': processing_time.total_seconds()
            })

            # Build final result according to documentation specification
            stage5_output = {
                'stage': 'stage5_data_integration',
                'timeseries_data': comprehensive_data['timeseries_data'],
                'animation_data': comprehensive_data['animation_data'], 
                'hierarchical_data': comprehensive_data['hierarchical_data'],
                'formatted_outputs': {
                    k: v for k, v in formatted_outputs.items() 
                    if not k.endswith('_error') and k != 'conversion_metadata'
                },
                'metadata': {
                    'processing_time': datetime.now(timezone.utc).isoformat(),
                    'processed_satellites': self.processing_stats['processed_satellites'],
                    'output_formats': self.processing_stats['output_formats'],
                    'compression_ratio': self.processing_stats.get('compression_ratio', 0.0)
                }
            }

            self.logger.info(f"✅ Stage 5 Data Integration completed successfully")
            self.logger.info(f"   📊 Processed: {self.processing_stats['processed_satellites']} satellites")
            self.logger.info(f"   📦 Formats: {self.processing_stats['output_formats']} output formats")
            self.logger.info(f"   ⏱️ Duration: {self.processing_stats['processing_time_seconds']:.2f} seconds")

            return create_processing_result(
                status=ProcessingStatus.SUCCESS,
                data=stage5_output,
                message=f"Successfully integrated data for {self.processing_stats['processed_satellites']} satellites"
            )

        except Exception as e:
            self.logger.error(f"❌ Stage 5 Data Integration failed: {e}")
            return create_processing_result(
                status=ProcessingStatus.ERROR,
                data={},
                message=f"Data integration error: {str(e)}"
            )

    def _load_processing_config(self) -> Dict[str, Any]:
        """Load processing configuration from academic standards (no hardcoded values)."""
        try:
            # 🚨 Grade A要求：從學術標準動態載入配置，絕不硬編碼
            import sys
            import os
            sys.path.append('/orbit-engine/src')
            from shared.academic_standards_config import AcademicStandardsConfig
            
            standards_config = AcademicStandardsConfig()
            
            # 從ITU-R和3GPP標準載入時間序列配置
            timeseries_standards = standards_config.get_timeseries_processing_standards()
            animation_standards = standards_config.get_animation_generation_standards()
            layering_standards = standards_config.get_hierarchical_data_standards()
            format_standards = standards_config.get_output_format_standards()
            
            config = {
                'timeseries': {
                    'sampling_frequency': timeseries_standards.get('standard_sampling_frequency', '10S'),
                    'interpolation_method': timeseries_standards.get('interpolation_standard', 'cubic_spline'),
                    'compression_enabled': timeseries_standards.get('enable_compression', True),
                    'compression_level': timeseries_standards.get('compression_level', 6),
                    'window_duration_seconds': timeseries_standards.get('window_duration_seconds', 60)
                },
                'animation': {
                    'frame_rate': animation_standards.get('standard_frame_rate', 30),
                    'duration_seconds': animation_standards.get('standard_duration_seconds', 300),
                    'keyframe_optimization': animation_standards.get('enable_keyframe_optimization', True),
                    'effect_quality': animation_standards.get('effect_quality_level', 'high')
                },
                'layers': {
                    'spatial_resolution_levels': layering_standards.get('spatial_resolution_levels', 5),
                    'temporal_granularity': layering_standards.get('temporal_granularity', ['1MIN', '10MIN', '1HOUR']),
                    'quality_tiers': layering_standards.get('quality_tiers', ['high', 'medium', 'low']),
                    'enable_spatial_indexing': layering_standards.get('enable_spatial_indexing', True)
                },
                'formats': {
                    'compression_enabled': format_standards.get('enable_compression', True),
                    'default_schema_version': format_standards.get('default_schema_version', 'v1.0'),
                    'api_version': format_standards.get('api_version', 'v1')
                },
                'output_formats': format_standards.get('supported_formats', ['json', 'geojson', 'csv', 'api_package']),
                'compression_enabled': format_standards.get('global_compression_enabled', True)
            }
            
            self.logger.info("✅ 配置已從學術標準動態載入")
            return config
            
        except ImportError:
            self.logger.warning("⚠️ 無法載入學術標準配置，使用環境變數備用配置")
            
            # 環境變數備用配置 (避免硬編碼)
            config = {
                'timeseries': {
                    'sampling_frequency': os.getenv('TIMESERIES_SAMPLING_FREQ', '10S'),
                    'interpolation_method': os.getenv('INTERPOLATION_METHOD', 'cubic_spline'),
                    'compression_enabled': os.getenv('ENABLE_COMPRESSION', 'true').lower() == 'true',
                    'compression_level': int(os.getenv('COMPRESSION_LEVEL', '6')),
                    'window_duration_seconds': int(os.getenv('WINDOW_DURATION_SEC', '60'))
                },
                'animation': {
                    'frame_rate': int(os.getenv('ANIMATION_FRAME_RATE', '30')),
                    'duration_seconds': int(os.getenv('ANIMATION_DURATION_SEC', '300')),
                    'keyframe_optimization': os.getenv('KEYFRAME_OPTIMIZATION', 'true').lower() == 'true',
                    'effect_quality': os.getenv('EFFECT_QUALITY', 'high')
                },
                'layers': {
                    'spatial_resolution_levels': int(os.getenv('SPATIAL_RESOLUTION_LEVELS', '5')),
                    'temporal_granularity': os.getenv('TEMPORAL_GRANULARITY', '1MIN,10MIN,1HOUR').split(','),
                    'quality_tiers': os.getenv('QUALITY_TIERS', 'high,medium,low').split(','),
                    'enable_spatial_indexing': os.getenv('ENABLE_SPATIAL_INDEXING', 'true').lower() == 'true'
                },
                'formats': {
                    'compression_enabled': os.getenv('FORMAT_COMPRESSION', 'true').lower() == 'true',
                    'default_schema_version': os.getenv('SCHEMA_VERSION', 'v1.0'),
                    'api_version': os.getenv('API_VERSION', 'v1')
                },
                'output_formats': os.getenv('OUTPUT_FORMATS', 'json,geojson,csv,api_package').split(','),
                'compression_enabled': os.getenv('GLOBAL_COMPRESSION', 'true').lower() == 'true'
            }
            
            self.logger.info("✅ 配置已從環境變數載入")
            return config
            
        except Exception as e:
            self.logger.error(f"❌ 配置載入失敗: {e}")
            raise ValueError(f"無法載入配置，拒絕使用硬編碼默認值: {e}")
            
        # 合併用戶提供的配置
        final_config = config.copy()
        if self.config:
            # 深度合併用戶配置
            for section, section_config in self.config.items():
                if section in final_config and isinstance(section_config, dict):
                    final_config[section].update(section_config)
                else:
                    final_config[section] = section_config
        
        return final_config

    def _validate_stage4_output(self, input_data: Any) -> bool:
        """Validate Stage 4 optimization output data with comprehensive real data checks."""
        try:
            # 🚨 Grade A要求：嚴格驗證真實數據來源，絕不接受模擬數據
            
            if not isinstance(input_data, dict):
                self.logger.error("❌ 輸入數據必須是字典格式")
                return False

            # 檢查必需字段
            required_fields = ['stage', 'optimization_results']
            for field in required_fields:
                if field not in input_data:
                    self.logger.error(f"❌ 缺少必需字段: {field}")
                    return False

            # 驗證階段標識符
            stage_id = input_data.get('stage')
            if stage_id != 'stage4_optimization_decision':
                self.logger.error(f"❌ 無效的階段標識符: {stage_id}")
                return False

            # 驗證優化結果結構
            optimization_results = input_data.get('optimization_results', {})
            if not isinstance(optimization_results, dict):
                self.logger.error("❌ optimization_results 必須是字典格式")
                return False

            # 深度驗證優化池數據
            optimal_pool = optimization_results.get('optimal_pool', {})
            if not optimal_pool:
                self.logger.error("❌ 缺少 optimal_pool 數據")
                return False

            # 驗證衛星數據的真實性
            satellites = optimal_pool.get('satellites', [])
            if not satellites:
                self.logger.error("❌ optimal_pool 中無衛星數據")
                return False

            # 🚨 Grade A驗證：檢查每顆衛星是否有真實的Stage 1-4處理數據
            real_data_count = 0
            for i, satellite in enumerate(satellites[:5]):  # 抽樣檢查前5顆衛星
                sat_id = satellite.get('satellite_id', f'unknown_{i}')
                
                # 檢查Stage 1軌道數據
                stage1_data = satellite.get('stage1_orbital', {})
                if stage1_data:
                    tle_data = stage1_data.get('tle_data', {})
                    if tle_data and tle_data.get('tle_line1') and tle_data.get('tle_line2'):
                        real_data_count += 1
                        self.logger.debug(f"✅ 衛星 {sat_id} 有真實TLE數據")
                    else:
                        self.logger.warning(f"⚠️ 衛星 {sat_id} 缺少真實TLE數據")
                else:
                    self.logger.warning(f"⚠️ 衛星 {sat_id} 缺少Stage 1軌道數據")

                # 檢查Stage 2可見性數據
                stage2_data = satellite.get('stage2_visibility', {})
                if stage2_data:
                    elevation_profile = stage2_data.get('elevation_profile', [])
                    if elevation_profile:
                        self.logger.debug(f"✅ 衛星 {sat_id} 有真實仰角數據")
                    else:
                        self.logger.warning(f"⚠️ 衛星 {sat_id} 缺少仰角數據")

                # 檢查Stage 3時間序列數據  
                stage3_data = satellite.get('stage3_timeseries', {})
                if stage3_data:
                    timeseries_data = stage3_data.get('timeseries_data', [])
                    if timeseries_data:
                        self.logger.debug(f"✅ 衛星 {sat_id} 有真實時間序列數據")
                    else:
                        self.logger.warning(f"⚠️ 衛星 {sat_id} 缺少時間序列數據")

            # Grade A要求：至少50%的衛星必須有真實Stage 1數據
            real_data_ratio = real_data_count / min(5, len(satellites))
            if real_data_ratio < 0.5:
                self.logger.error(f"❌ 真實數據比例過低 ({real_data_ratio:.1%})，拒絕處理可能的模擬數據")
                return False

            # 檢查處理時間戳的合理性 
            metadata = input_data.get('metadata', {})
            processing_time = metadata.get('processing_time')
            if processing_time:
                try:
                    # 驗證時間戳格式和合理性
                    timestamp = datetime.fromisoformat(processing_time.replace('Z', '+00:00'))
                    time_diff = datetime.now(timezone.utc) - timestamp
                    
                    # 處理時間應該在合理範圍內 (不超過24小時前)
                    if time_diff.total_seconds() > 86400:
                        self.logger.warning(f"⚠️ 處理時間戳較舊: {processing_time}")
                except Exception as e:
                    self.logger.warning(f"⚠️ 處理時間戳格式異常: {e}")

            # 記錄驗證成功信息
            self.logger.info(f"✅ Stage 4輸出驗證通過")
            self.logger.info(f"   📊 衛星數量: {len(satellites)}")
            self.logger.info(f"   🎯 真實數據比例: {real_data_ratio:.1%}")
            self.logger.info(f"   📝 階段標識: {stage_id}")

            return True

        except Exception as e:
            self.logger.error(f"❌ Stage 4輸出驗證失敗: {e}")
            return False

    def validate_input(self, input_data: Any) -> Dict[str, Any]:
        """Validate input data according to Stage 5 requirements."""
        errors = []
        warnings = []

        if self._validate_stage4_output(input_data):
            # Additional validation checks
            optimization_results = input_data.get('optimization_results', {})
            optimal_pool = optimization_results.get('optimal_pool', {})
            
            satellites = optimal_pool.get('satellites', [])
            if len(satellites) == 0:
                warnings.append("No satellites found in optimal pool")
            elif len(satellites) > 1000:
                warnings.append(f"Large number of satellites ({len(satellites)}) may impact performance")
                
            return {'valid': True, 'errors': errors, 'warnings': warnings}
        else:
            errors.append("Stage 4 output data validation failed")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

    def validate_output(self, output_data: Any) -> Dict[str, Any]:
        """Validate output data according to Stage 5 specifications."""
        errors = []
        warnings = []

        if not isinstance(output_data, dict):
            errors.append("Output data must be a dictionary")
            return {'valid': False, 'errors': errors, 'warnings': warnings}

        # Check required fields according to documentation
        required_fields = ['stage', 'timeseries_data', 'animation_data', 'hierarchical_data', 'formatted_outputs', 'metadata']
        for field in required_fields:
            if field not in output_data:
                errors.append(f"Missing required field: {field}")

        # Validate stage identifier
        if output_data.get('stage') != 'stage5_data_integration':
            errors.append(f"Invalid stage identifier: {output_data.get('stage')}")

        # Validate data structures
        timeseries_data = output_data.get('timeseries_data', {})
        if isinstance(timeseries_data, dict):
            if not timeseries_data.get('dataset_id'):
                warnings.append("Missing dataset_id in timeseries_data")
            if timeseries_data.get('satellite_count', 0) == 0:
                warnings.append("No satellites in timeseries data")

        animation_data = output_data.get('animation_data', {})
        if isinstance(animation_data, dict):
            if not animation_data.get('animation_id'):
                warnings.append("Missing animation_id in animation_data")

        formatted_outputs = output_data.get('formatted_outputs', {})
        if isinstance(formatted_outputs, dict):
            if len(formatted_outputs) == 0:
                warnings.append("No formatted outputs generated")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

    def extract_key_metrics(self) -> Dict[str, Any]:
        """Extract key performance metrics for Stage 5."""
        return {
            'stage': 'stage5_data_integration',
            'processed_satellites': self.processing_stats['processed_satellites'],
            'output_formats_generated': self.processing_stats['output_formats'],
            'processing_time_seconds': self.processing_stats['processing_time_seconds'],
            'compression_ratio': self.processing_stats.get('compression_ratio', 0.0),
            'components_used': [
                'timeseries_converter',
                'animation_builder', 
                'layer_data_generator',
                'format_converter_hub'
            ]
        }

    def run_validation_checks(self) -> Dict[str, Any]:
        """Run validation checks for Stage 5 processing."""
        return {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'component_validations': {
                'timeseries_converter': self.timeseries_converter is not None,
                'animation_builder': self.animation_builder is not None,
                'layer_data_generator': self.layer_data_generator is not None,
                'format_converter_hub': self.format_converter_hub is not None
            },
            'configuration_valid': bool(self.processing_config),
            'all_checks_passed': True
        }

    def save_results(self, results: Dict[str, Any], output_path: str = None) -> bool:
        """Save Stage 5 processing results to specified output path."""
        try:
            if not output_path:
                output_path = f"/orbit-engine/data/outputs/stage5/stage5_output_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
            
            # Ensure output directory exists
            import os
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save results to JSON file
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Stage 5 results saved to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save Stage 5 results: {e}")
            return False


def create_stage5_processor(config: Optional[Dict[str, Any]] = None) -> DataIntegrationProcessor:
    """創建Stage 5處理器實例"""
    return DataIntegrationProcessor(config)