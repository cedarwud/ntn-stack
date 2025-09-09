"""
數據品質配置系統
Data Quality Configuration System

定義數據完整性、一致性、準確性檢查標準
Based on Phase 2 data quality engine specifications
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class QualityDimension(Enum):
    """數據品質維度"""
    COMPLETENESS = "completeness"      # 完整性
    CONSISTENCY = "consistency"        # 一致性  
    ACCURACY = "accuracy"             # 準確性
    VALIDITY = "validity"             # 有效性
    INTEGRITY = "integrity"           # 完整性
    TIMELINESS = "timeliness"         # 及時性


class QualityLevel(Enum):
    """品質等級"""
    EXCELLENT = "excellent"           # 優秀 (>95%)
    GOOD = "good"                    # 良好 (85-95%)
    ACCEPTABLE = "acceptable"        # 可接受 (70-85%)
    POOR = "poor"                    # 較差 (50-70%)
    CRITICAL = "critical"            # 嚴重 (<50%)


@dataclass
class QualityMetric:
    """品質指標定義"""
    metric_id: str
    name: str
    description: str
    dimension: QualityDimension
    threshold_excellent: float
    threshold_good: float
    threshold_acceptable: float
    unit: str
    enabled: bool = True


class DataQualityConfig:
    """數據品質配置管理器"""
    
    def __init__(self):
        self._initialize_structure_validation_rules()
        self._initialize_statistical_analysis_config()
        self._initialize_cross_stage_consistency_rules()
        self._initialize_metadata_compliance_rules()
        self._initialize_quality_metrics()
    
    def _initialize_structure_validation_rules(self):
        """數據結構驗證規則"""
        self.STRUCTURE_VALIDATION = {
            'tle_data_structure': {
                'required_fields': ['satellite_name', 'line1', 'line2', 'epoch'],
                'field_types': {
                    'satellite_name': str,
                    'line1': str,
                    'line2': str,
                    'epoch': str
                },
                'field_constraints': {
                    'line1_length': 69,
                    'line2_length': 69,
                    'satellite_name_max_length': 24
                },
                'validation_patterns': {
                    'line1_checksum': r'^1\s\d{5}[A-Z]\s',
                    'line2_checksum': r'^2\s\d{5}\s'
                }
            },
            'orbital_data_structure': {
                'required_fields': ['satellite_id', 'timestamp', 'eci_x', 'eci_y', 'eci_z'],
                'field_types': {
                    'satellite_id': (int, str),
                    'timestamp': str,
                    'eci_x': float,
                    'eci_y': float,
                    'eci_z': float
                },
                'field_constraints': {
                    'eci_coordinate_range': (-50000, 50000),  # km
                    'timestamp_format': '%Y-%m-%d %H:%M:%S'
                }
            },
            'visibility_data_structure': {
                'required_fields': ['satellite_id', 'timestamp', 'elevation', 'azimuth', 'distance'],
                'field_types': {
                    'satellite_id': (int, str),
                    'timestamp': str,
                    'elevation': float,
                    'azimuth': float,
                    'distance': float
                },
                'field_constraints': {
                    'elevation_range': (-90, 90),      # degrees
                    'azimuth_range': (0, 360),         # degrees
                    'distance_range': (160, 2000)      # km (LEO range)
                }
            }
        }
    
    def _initialize_statistical_analysis_config(self):
        """統計分析配置"""
        self.STATISTICAL_ANALYSIS = {
            'distribution_tests': {
                'normality_test': {
                    'method': 'shapiro_wilk',
                    'significance_level': 0.05,
                    'sample_size_threshold': 5000
                },
                'outlier_detection': {
                    'method': 'iqr',  # Interquartile Range
                    'iqr_multiplier': 1.5,
                    'z_score_threshold': 3.0
                }
            },
            'time_series_validation': {
                'temporal_consistency': {
                    'max_time_gap': 300,  # seconds
                    'min_data_points': 100,
                    'trend_analysis': True
                },
                'periodicity_check': {
                    'orbital_period_tolerance': 0.1,  # 10% tolerance
                    'expected_leo_period_range': (90, 120)  # minutes
                }
            },
            'correlation_analysis': {
                'cross_variable_correlation': {
                    'elevation_distance_correlation': True,
                    'expected_correlation_threshold': 0.7
                },
                'inter_satellite_correlation': {
                    'constellation_coherence': True,
                    'anomaly_detection_threshold': 0.3
                }
            }
        }
    
    def _initialize_cross_stage_consistency_rules(self):
        """跨階段一致性規則"""
        self.CROSS_STAGE_CONSISTENCY = {
            'stage_dependencies': {
                'stage1_to_stage2': {
                    'satellite_count_consistency': True,
                    'timestamp_alignment': True,
                    'coordinate_system_consistency': True
                },
                'stage2_to_stage3': {
                    'visibility_calculation_consistency': True,
                    'elevation_threshold_consistency': True,
                    'time_window_alignment': True
                },
                'stage3_to_stage4': {
                    'signal_strength_consistency': True,
                    'quality_metric_alignment': True,
                    'filtering_result_validation': True
                }
            },
            'data_flow_validation': {
                'input_output_mapping': {
                    'preserve_satellite_identifiers': True,
                    'maintain_temporal_ordering': True,
                    'validate_data_completeness': True
                },
                'transformation_integrity': {
                    'coordinate_transformation_validation': True,
                    'unit_conversion_verification': True,
                    'precision_loss_monitoring': True
                }
            }
        }
    
    def _initialize_metadata_compliance_rules(self):
        """元數據合規性規則"""
        self.METADATA_COMPLIANCE = {
            'mandatory_metadata': {
                'processing_timestamp': True,
                'data_source_identification': True,
                'processing_version': True,
                'validation_status': True
            },
            'traceability_requirements': {
                'input_data_lineage': True,
                'processing_parameters': True,
                'quality_assessment_results': True,
                'error_handling_logs': True
            },
            'academic_compliance': {
                'grade_level_classification': True,
                'data_source_attribution': True,
                'methodology_documentation': True,
                'reproducibility_information': True
            }
        }
    
    def _initialize_quality_metrics(self):
        """初始化品質指標"""
        self.quality_metrics = [
            # 數據完整性指標
            QualityMetric(
                metric_id="DATA_COMPLETENESS",
                name="數據完整性",
                description="檢查必需欄位的完整性百分比",
                dimension=QualityDimension.COMPLETENESS,
                threshold_excellent=99.0,
                threshold_good=95.0,
                threshold_acceptable=85.0,
                unit="percentage"
            ),
            
            # ECI座標準確性
            QualityMetric(
                metric_id="ECI_COORDINATE_ACCURACY",
                name="ECI座標準確性",
                description="ECI座標非零值百分比",
                dimension=QualityDimension.ACCURACY,
                threshold_excellent=100.0,
                threshold_good=99.0,
                threshold_acceptable=95.0,
                unit="percentage"
            ),
            
            # 時間序列一致性
            QualityMetric(
                metric_id="TEMPORAL_CONSISTENCY",
                name="時間序列一致性",
                description="時間戳順序和間隔的一致性",
                dimension=QualityDimension.CONSISTENCY,
                threshold_excellent=98.0,
                threshold_good=90.0,
                threshold_acceptable=80.0,
                unit="percentage"
            ),
            
            # 統計分佈正常性
            QualityMetric(
                metric_id="STATISTICAL_NORMALITY",
                name="統計分佈正常性",
                description="數據分佈符合預期統計特性的程度",
                dimension=QualityDimension.VALIDITY,
                threshold_excellent=95.0,
                threshold_good=85.0,
                threshold_acceptable=70.0,
                unit="percentage"
            ),
            
            # 跨階段一致性
            QualityMetric(
                metric_id="CROSS_STAGE_CONSISTENCY",
                name="跨階段一致性",
                description="數據在處理階段間的一致性保持度",
                dimension=QualityDimension.INTEGRITY,
                threshold_excellent=99.5,
                threshold_good=95.0,
                threshold_acceptable=85.0,
                unit="percentage"
            )
        ]
    
    def get_structure_validation_rules(self) -> Dict[str, Any]:
        """獲取結構驗證規則"""
        return self.STRUCTURE_VALIDATION
    
    def get_statistical_analysis_config(self) -> Dict[str, Any]:
        """獲取統計分析配置"""
        return self.STATISTICAL_ANALYSIS
    
    def get_cross_stage_consistency_rules(self) -> Dict[str, Any]:
        """獲取跨階段一致性規則"""
        return self.CROSS_STAGE_CONSISTENCY
    
    def get_metadata_compliance_rules(self) -> Dict[str, Any]:
        """獲取元數據合規性規則"""
        return self.METADATA_COMPLIANCE
    
    def get_quality_metrics(self, dimension: QualityDimension = None) -> List[QualityMetric]:
        """獲取品質指標"""
        if dimension:
            return [metric for metric in self.quality_metrics if metric.dimension == dimension]
        return self.quality_metrics
    
    def get_metric_by_id(self, metric_id: str) -> QualityMetric:
        """根據ID獲取特定指標"""
        for metric in self.quality_metrics:
            if metric.metric_id == metric_id:
                return metric
        raise KeyError(f"Metric not found: {metric_id}")
    
    def evaluate_quality_level(self, metric_id: str, value: float) -> QualityLevel:
        """評估品質等級"""
        metric = self.get_metric_by_id(metric_id)
        
        if value >= metric.threshold_excellent:
            return QualityLevel.EXCELLENT
        elif value >= metric.threshold_good:
            return QualityLevel.GOOD
        elif value >= metric.threshold_acceptable:
            return QualityLevel.ACCEPTABLE
        elif value >= 50.0:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def validate_data_structure(self, data: Dict, structure_type: str) -> Dict[str, Any]:
        """驗證數據結構"""
        if structure_type not in self.STRUCTURE_VALIDATION:
            raise ValueError(f"Unknown structure type: {structure_type}")
        
        rules = self.STRUCTURE_VALIDATION[structure_type]
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 檢查必需欄位
        for field in rules['required_fields']:
            if field not in data:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # 檢查欄位類型
        for field, expected_type in rules['field_types'].items():
            if field in data:
                if isinstance(expected_type, tuple):
                    if not isinstance(data[field], expected_type):
                        validation_result['warnings'].append(f"Field {field} type mismatch")
                else:
                    if not isinstance(data[field], expected_type):
                        validation_result['warnings'].append(f"Field {field} type mismatch")
        
        return validation_result


# 全域配置實例
data_quality_config = DataQualityConfig()


# 配置常數導出
STRUCTURE_VALIDATION_RULES = data_quality_config.get_structure_validation_rules()
STATISTICAL_ANALYSIS_CONFIG = data_quality_config.get_statistical_analysis_config()
CROSS_STAGE_CONSISTENCY_RULES = data_quality_config.get_cross_stage_consistency_rules()
METADATA_COMPLIANCE_RULES = data_quality_config.get_metadata_compliance_rules()
QUALITY_METRICS = data_quality_config.get_quality_metrics()


def get_data_quality_config() -> DataQualityConfig:
    """獲取數據品質配置實例"""
    return data_quality_config