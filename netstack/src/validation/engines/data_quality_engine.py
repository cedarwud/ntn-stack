"""
數據品質檢查引擎
Data Quality Validation Engine

實現數據結構檢查、統計分析、跨階段一致性檢查、元數據合規性驗證
Based on Phase 2 specifications: data_quality_engine.py
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import json
import re
from datetime import datetime, timezone
import numpy as np
import scipy.stats as stats
from dataclasses import dataclass
from collections import defaultdict

from ..core.base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationLevel
from ..config.data_quality_config import (
    DataQualityConfig, QualityDimension, QualityLevel,
    get_data_quality_config
)


@dataclass
class StructureValidationResult:
    """結構驗證結果"""
    is_valid: bool
    missing_fields: List[str]
    type_mismatches: List[Dict[str, Any]]
    constraint_violations: List[Dict[str, Any]]
    format_errors: List[str]
    validation_summary: str


@dataclass
class StatisticalAnalysisResult:
    """統計分析結果"""
    total_samples: int
    normality_test_passed: bool
    outliers_detected: List[Dict[str, Any]]
    distribution_parameters: Dict[str, float]
    quality_score: float
    anomalies: List[str]


@dataclass
class ConsistencyCheckResult:
    """一致性檢查結果"""
    consistency_score: float
    inconsistencies: List[Dict[str, Any]]
    data_flow_integrity: bool
    transformation_errors: List[str]
    dependency_violations: List[str]


class DataStructureValidator(BaseValidator):
    """數據結構檢查器"""
    
    def __init__(self, config: DataQualityConfig = None):
        self.config = config or get_data_quality_config()
        self.structure_rules = self.config.get_structure_validation_rules()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """執行數據結構驗證"""
        try:
            validation_errors = []
            validation_warnings = []
            structure_results = {}
            
            # 根據數據類型選擇驗證規則
            data_type = context.get('data_type') if context else self._infer_data_type(data)
            
            if data_type in self.structure_rules:
                structure_result = self._validate_structure(data, data_type)
                structure_results[data_type] = structure_result
                
                if not structure_result.is_valid:
                    validation_errors.extend(structure_result.format_errors)
                    validation_errors.extend([f"Missing field: {field}" for field in structure_result.missing_fields])
                    validation_errors.extend([f"Type mismatch: {mismatch}" for mismatch in structure_result.type_mismatches])
                    validation_errors.extend([f"Constraint violation: {violation}" for violation in structure_result.constraint_violations])
            
            # 通用結構檢查
            general_result = self._validate_general_structure(data)
            validation_warnings.extend(general_result.get('warnings', []))
            validation_errors.extend(general_result.get('errors', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.CRITICAL if validation_errors else ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Data structure validation {'failed' if validation_errors else 'passed'}",
                details={
                    'structure_results': structure_results,
                    'data_type': data_type,
                    'general_validation': general_result,
                    'validation_errors': validation_errors,
                    'validation_warnings': validation_warnings
                },
                metadata={'validation_type': 'data_structure'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Data structure validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Validation error: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'data_structure'}
            )
    
    def _infer_data_type(self, data: Dict[str, Any]) -> str:
        """推斷數據類型"""
        # TLE數據檢查
        if any(key in data for key in ['line1', 'line2', 'satellite_name', 'epoch']):
            return 'tle_data_structure'
        
        # 軌道數據檢查
        if any(key in data for key in ['eci_x', 'eci_y', 'eci_z', 'satellite_id']):
            return 'orbital_data_structure'
        
        # 可見性數據檢查
        if any(key in data for key in ['elevation', 'azimuth', 'distance']):
            return 'visibility_data_structure'
        
        return 'unknown'
    
    def _validate_structure(self, data: Dict[str, Any], structure_type: str) -> StructureValidationResult:
        """驗證特定結構類型"""
        rules = self.structure_rules[structure_type]
        
        missing_fields = []
        type_mismatches = []
        constraint_violations = []
        format_errors = []
        
        # 檢查必需欄位
        required_fields = rules.get('required_fields', [])
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        # 檢查欄位類型
        field_types = rules.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data:
                actual_value = data[field]
                if isinstance(expected_type, tuple):
                    if not isinstance(actual_value, expected_type):
                        type_mismatches.append({
                            'field': field,
                            'expected': str(expected_type),
                            'actual': str(type(actual_value))
                        })
                else:
                    if not isinstance(actual_value, expected_type):
                        type_mismatches.append({
                            'field': field,
                            'expected': expected_type.__name__,
                            'actual': type(actual_value).__name__
                        })
        
        # 檢查欄位約束
        field_constraints = rules.get('field_constraints', {})
        for constraint_name, constraint_value in field_constraints.items():
            constraint_result = self._check_field_constraint(data, constraint_name, constraint_value)
            if constraint_result:
                constraint_violations.append(constraint_result)
        
        # 檢查驗證模式
        validation_patterns = rules.get('validation_patterns', {})
        for pattern_name, pattern in validation_patterns.items():
            pattern_result = self._check_validation_pattern(data, pattern_name, pattern)
            if pattern_result:
                format_errors.append(pattern_result)
        
        is_valid = not (missing_fields or type_mismatches or constraint_violations or format_errors)
        
        return StructureValidationResult(
            is_valid=is_valid,
            missing_fields=missing_fields,
            type_mismatches=type_mismatches,
            constraint_violations=constraint_violations,
            format_errors=format_errors,
            validation_summary=f"Structure validation {'passed' if is_valid else 'failed'} for {structure_type}"
        )
    
    def _validate_general_structure(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """通用結構檢查"""
        errors = []
        warnings = []
        
        # 檢查數據完整性
        if not data:
            errors.append("Empty data structure")
            return {'errors': errors, 'warnings': warnings}
        
        # 檢查數據深度
        max_depth = self._calculate_data_depth(data)
        if max_depth > 10:
            warnings.append(f"Data structure is deeply nested: {max_depth} levels")
        
        # 檢查數據大小
        if isinstance(data, dict):
            if len(data) > 1000:
                warnings.append(f"Large data structure: {len(data)} keys")
        
        # 檢查循環引用 (簡化實現)
        try:
            json.dumps(data)
        except (TypeError, ValueError) as e:
            errors.append(f"Data structure serialization error: {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_field_constraint(self, data: Dict, constraint_name: str, constraint_value: Any) -> Optional[Dict[str, Any]]:
        """檢查欄位約束"""
        if 'length' in constraint_name:
            field_name = constraint_name.replace('_length', '')
            if field_name in data:
                actual_length = len(str(data[field_name]))
                if actual_length != constraint_value:
                    return {
                        'constraint': constraint_name,
                        'field': field_name,
                        'expected': constraint_value,
                        'actual': actual_length
                    }
        
        elif 'range' in constraint_name:
            field_name = constraint_name.replace('_range', '')
            if field_name in data:
                value = data[field_name]
                if isinstance(constraint_value, tuple) and len(constraint_value) == 2:
                    min_val, max_val = constraint_value
                    if not (min_val <= value <= max_val):
                        return {
                            'constraint': constraint_name,
                            'field': field_name,
                            'expected_range': constraint_value,
                            'actual': value
                        }
        
        elif 'max_length' in constraint_name:
            field_name = constraint_name.replace('_max_length', '')
            if field_name in data:
                actual_length = len(str(data[field_name]))
                if actual_length > constraint_value:
                    return {
                        'constraint': constraint_name,
                        'field': field_name,
                        'max_length': constraint_value,
                        'actual': actual_length
                    }
        
        return None
    
    def _check_validation_pattern(self, data: Dict, pattern_name: str, pattern: str) -> Optional[str]:
        """檢查驗證模式"""
        if 'checksum' in pattern_name:
            field_name = pattern_name.replace('_checksum', '')
            if field_name in data:
                field_value = str(data[field_name])
                if not re.match(pattern, field_value):
                    return f"Pattern validation failed for {field_name}: does not match {pattern}"
        
        return None
    
    def _calculate_data_depth(self, data: Any, current_depth: int = 0) -> int:
        """計算數據結構深度"""
        if current_depth > 20:  # 防止無限遞歸
            return current_depth
        
        if isinstance(data, dict):
            if not data:
                return current_depth
            return max(self._calculate_data_depth(value, current_depth + 1) for value in data.values())
        elif isinstance(data, list):
            if not data:
                return current_depth
            return max(self._calculate_data_depth(item, current_depth + 1) for item in data)
        else:
            return current_depth


class StatisticalAnalyzer(BaseValidator):
    """統計分析模組"""
    
    def __init__(self, config: DataQualityConfig = None):
        self.config = config or get_data_quality_config()
        self.statistical_rules = self.config.get_statistical_analysis_config()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """執行統計分析驗證"""
        try:
            validation_errors = []
            validation_warnings = []
            analysis_results = {}
            
            # 數值欄位統計分析
            numerical_result = self._analyze_numerical_fields(data)
            analysis_results['numerical_analysis'] = numerical_result
            validation_warnings.extend(numerical_result.anomalies)
            
            # 時間序列驗證
            if self._has_time_series_data(data):
                time_series_result = self._validate_time_series(data)
                analysis_results['time_series_analysis'] = time_series_result
                validation_errors.extend(time_series_result.get('errors', []))
                validation_warnings.extend(time_series_result.get('warnings', []))
            
            # 相關性分析
            correlation_result = self._analyze_correlations(data)
            analysis_results['correlation_analysis'] = correlation_result
            validation_warnings.extend(correlation_result.get('warnings', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.CRITICAL if validation_errors else ValidationLevel.INFO
            
            analysis_results.update({
                'validation_errors': validation_errors,
                'validation_warnings': validation_warnings
            })
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Statistical analysis {'failed' if validation_errors else 'passed'}",
                details=analysis_results,
                metadata={'validation_type': 'statistical_analysis'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Statistical analysis error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Analysis error: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'statistical_analysis'}
            )
    
    def _analyze_numerical_fields(self, data: Dict[str, Any]) -> StatisticalAnalysisResult:
        """分析數值欄位"""
        numerical_fields = self._extract_numerical_fields(data)
        
        if not numerical_fields:
            return StatisticalAnalysisResult(
                total_samples=0,
                normality_test_passed=False,
                outliers_detected=[],
                distribution_parameters={},
                quality_score=0.0,
                anomalies=["No numerical fields found for analysis"]
            )
        
        total_samples = sum(len(values) for values in numerical_fields.values())
        outliers_detected = []
        distribution_parameters = {}
        anomalies = []
        normality_tests_passed = 0
        total_normality_tests = 0
        
        for field_name, values in numerical_fields.items():
            if len(values) < 3:
                anomalies.append(f"Insufficient data for statistical analysis in field '{field_name}'")
                continue
            
            # 正態性檢驗
            normality_result = self._test_normality(values, field_name)
            if normality_result['is_normal']:
                normality_tests_passed += 1
            total_normality_tests += 1
            
            # 異常值檢測
            field_outliers = self._detect_outliers(values, field_name)
            outliers_detected.extend(field_outliers)
            
            # 分佈參數計算
            distribution_parameters[field_name] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'median': float(np.median(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'skewness': float(stats.skew(values)),
                'kurtosis': float(stats.kurtosis(values))
            }
            
            # 異常檢測
            field_anomalies = self._detect_statistical_anomalies(values, field_name)
            anomalies.extend(field_anomalies)
        
        # 計算品質分數
        quality_score = self._calculate_statistical_quality_score(
            outliers_detected, distribution_parameters, anomalies, total_samples
        )
        
        normality_test_passed = (normality_tests_passed / max(total_normality_tests, 1)) > 0.5
        
        return StatisticalAnalysisResult(
            total_samples=total_samples,
            normality_test_passed=normality_test_passed,
            outliers_detected=outliers_detected,
            distribution_parameters=distribution_parameters,
            quality_score=quality_score,
            anomalies=anomalies
        )
    
    def _extract_numerical_fields(self, data: Dict[str, Any]) -> Dict[str, List[float]]:
        """提取數值欄位"""
        numerical_fields = defaultdict(list)
        
        def extract_from_item(item: Any, prefix: str = ''):
            if isinstance(item, dict):
                for key, value in item.items():
                    field_name = f"{prefix}.{key}" if prefix else key
                    extract_from_item(value, field_name)
            elif isinstance(item, list):
                for i, sub_item in enumerate(item):
                    extract_from_item(sub_item, prefix)
            elif isinstance(item, (int, float)) and not isinstance(item, bool):
                if prefix:
                    numerical_fields[prefix].append(float(item))
        
        extract_from_item(data)
        return dict(numerical_fields)
    
    def _test_normality(self, values: List[float], field_name: str) -> Dict[str, Any]:
        """正態性檢驗"""
        try:
            # Shapiro-Wilk 檢驗 (小樣本)
            if len(values) <= 5000:
                statistic, p_value = stats.shapiro(values)
                test_name = 'shapiro_wilk'
            else:
                # Kolmogorov-Smirnov 檢驗 (大樣本)
                statistic, p_value = stats.kstest(values, 'norm')
                test_name = 'kolmogorov_smirnov'
            
            significance_level = self.statistical_rules['distribution_tests']['normality_test']['significance_level']
            is_normal = p_value > significance_level
            
            return {
                'test_name': test_name,
                'statistic': float(statistic),
                'p_value': float(p_value),
                'is_normal': is_normal,
                'significance_level': significance_level
            }
            
        except Exception as e:
            return {
                'test_name': 'error',
                'error': str(e),
                'is_normal': False
            }
    
    def _detect_outliers(self, values: List[float], field_name: str) -> List[Dict[str, Any]]:
        """異常值檢測"""
        outliers = []
        
        try:
            # IQR 方法
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            
            iqr_multiplier = self.statistical_rules['distribution_tests']['outlier_detection']['iqr_multiplier']
            lower_bound = q1 - iqr_multiplier * iqr
            upper_bound = q3 + iqr_multiplier * iqr
            
            for i, value in enumerate(values):
                if value < lower_bound or value > upper_bound:
                    outliers.append({
                        'field': field_name,
                        'index': i,
                        'value': float(value),
                        'method': 'iqr',
                        'bounds': (float(lower_bound), float(upper_bound))
                    })
            
            # Z-score 方法 (補充)
            z_threshold = self.statistical_rules['distribution_tests']['outlier_detection']['z_score_threshold']
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val > 0:
                z_scores = np.abs((np.array(values) - mean_val) / std_val)
                z_outlier_indices = np.where(z_scores > z_threshold)[0]
                
                for idx in z_outlier_indices:
                    # 避免重複添加
                    existing = any(o['index'] == idx and o['field'] == field_name for o in outliers)
                    if not existing:
                        outliers.append({
                            'field': field_name,
                            'index': int(idx),
                            'value': float(values[idx]),
                            'method': 'z_score',
                            'z_score': float(z_scores[idx])
                        })
            
        except Exception as e:
            # 如果統計計算失敗，返回空列表但記錄錯誤
            pass
        
        return outliers
    
    def _detect_statistical_anomalies(self, values: List[float], field_name: str) -> List[str]:
        """檢測統計異常"""
        anomalies = []
        
        try:
            # 檢測全零值
            if all(v == 0 for v in values):
                anomalies.append(f"All values are zero in field '{field_name}'")
            
            # 檢測常數值
            elif len(set(values)) == 1:
                anomalies.append(f"All values are constant in field '{field_name}': {values[0]}")
            
            # 檢測極端偏斜
            skewness = stats.skew(values)
            if abs(skewness) > 3:
                anomalies.append(f"Extreme skewness in field '{field_name}': {skewness:.2f}")
            
            # 檢測極端峰度
            kurtosis = stats.kurtosis(values)
            if abs(kurtosis) > 10:
                anomalies.append(f"Extreme kurtosis in field '{field_name}': {kurtosis:.2f}")
            
        except Exception as e:
            anomalies.append(f"Statistical anomaly detection error in field '{field_name}': {str(e)}")
        
        return anomalies
    
    def _calculate_statistical_quality_score(self, outliers: List, distribution_params: Dict, 
                                           anomalies: List, total_samples: int) -> float:
        """計算統計品質分數"""
        if total_samples == 0:
            return 0.0
        
        # 基礎分數
        base_score = 100.0
        
        # 異常值影響 (每個異常值扣1分，上限20分)
        outlier_penalty = min(len(outliers), 20)
        base_score -= outlier_penalty
        
        # 異常情況影響 (每個異常扣5分，上限30分)
        anomaly_penalty = min(len(anomalies) * 5, 30)
        base_score -= anomaly_penalty
        
        # 數據完整性加分 (樣本數足夠)
        if total_samples >= 100:
            base_score += 10
        elif total_samples >= 30:
            base_score += 5
        
        return max(0.0, min(100.0, base_score))
    
    def _has_time_series_data(self, data: Dict[str, Any]) -> bool:
        """檢查是否包含時間序列數據"""
        time_indicators = ['timestamp', 'time', 'datetime', 'epoch']
        return any(indicator in str(data).lower() for indicator in time_indicators)
    
    def _validate_time_series(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """時間序列驗證"""
        errors = []
        warnings = []
        
        # 提取時間序列數據
        time_series_data = self._extract_time_series(data)
        
        if not time_series_data:
            warnings.append("No time series data found for validation")
            return {'errors': errors, 'warnings': warnings}
        
        # 時間間隔一致性檢查
        for series_name, timestamps in time_series_data.items():
            if len(timestamps) < 2:
                warnings.append(f"Insufficient time series data in '{series_name}'")
                continue
            
            # 檢查時間排序
            sorted_timestamps = sorted(timestamps)
            if timestamps != sorted_timestamps:
                errors.append(f"Time series not chronologically ordered in '{series_name}'")
            
            # 檢查時間間隔
            try:
                intervals = []
                for i in range(1, len(timestamps)):
                    if isinstance(timestamps[i], str) and isinstance(timestamps[i-1], str):
                        dt1 = datetime.fromisoformat(timestamps[i-1].replace('Z', '+00:00'))
                        dt2 = datetime.fromisoformat(timestamps[i].replace('Z', '+00:00'))
                        intervals.append((dt2 - dt1).total_seconds())
                
                if intervals:
                    avg_interval = np.mean(intervals)
                    interval_std = np.std(intervals)
                    
                    # 檢查間隔變異性
                    if len(intervals) > 1 and avg_interval > 0:
                        cv = interval_std / avg_interval  # 變異係數
                        if cv > 0.1:  # 10% 變異容差
                            warnings.append(f"High time interval variability in '{series_name}': {cv:.2%}")
                        
                        # 檢查最大時間間隙
                        max_gap = self.statistical_rules['time_series_validation']['temporal_consistency']['max_time_gap']
                        if max(intervals) > max_gap:
                            warnings.append(f"Large time gap detected in '{series_name}': {max(intervals):.1f}s")
            
            except Exception as e:
                errors.append(f"Time series validation error in '{series_name}': {str(e)}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _extract_time_series(self, data: Dict[str, Any]) -> Dict[str, List]:
        """提取時間序列數據"""
        time_series = {}
        
        def extract_timestamps(obj: Any, path: str = ''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    if key.lower() in ['timestamp', 'time', 'datetime', 'epoch']:
                        if isinstance(value, list):
                            time_series[current_path] = value
                        else:
                            time_series[current_path] = [value]
                    else:
                        extract_timestamps(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_timestamps(item, path)
        
        extract_timestamps(data)
        return time_series
    
    def _analyze_correlations(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """相關性分析"""
        warnings = []
        
        # 提取數值欄位進行相關性分析
        numerical_fields = self._extract_numerical_fields(data)
        
        if len(numerical_fields) < 2:
            warnings.append("Insufficient numerical fields for correlation analysis")
            return {'warnings': warnings}
        
        # 計算欄位間相關性
        try:
            field_names = list(numerical_fields.keys())
            correlation_matrix = []
            
            for i, field1 in enumerate(field_names):
                for j, field2 in enumerate(field_names):
                    if i < j:  # 避免重複計算
                        values1 = numerical_fields[field1]
                        values2 = numerical_fields[field2]
                        
                        # 確保數據長度一致
                        min_length = min(len(values1), len(values2))
                        if min_length < 3:
                            continue
                        
                        correlation = np.corrcoef(values1[:min_length], values2[:min_length])[0, 1]
                        
                        # 檢查異常相關性
                        if abs(correlation) > 0.95 and field1 != field2:
                            warnings.append(f"Extremely high correlation between '{field1}' and '{field2}': {correlation:.3f}")
                        elif abs(correlation) < 0.1 and self._should_be_correlated(field1, field2):
                            warnings.append(f"Unexpectedly low correlation between '{field1}' and '{field2}': {correlation:.3f}")
        
        except Exception as e:
            warnings.append(f"Correlation analysis error: {str(e)}")
        
        return {'warnings': warnings}
    
    def _should_be_correlated(self, field1: str, field2: str) -> bool:
        """判斷兩個欄位是否應該有相關性"""
        # 定義應該相關的欄位對
        correlated_pairs = [
            ('elevation', 'distance'),
            ('elevation', 'signal_strength'),
            ('distance', 'path_loss'),
            ('frequency', 'wavelength')
        ]
        
        field1_lower = field1.lower()
        field2_lower = field2.lower()
        
        for pair in correlated_pairs:
            if (pair[0] in field1_lower and pair[1] in field2_lower) or \
               (pair[1] in field1_lower and pair[0] in field2_lower):
                return True
        
        return False


class CrossStageConsistencyChecker(BaseValidator):
    """跨階段一致性檢查器"""
    
    def __init__(self, config: DataQualityConfig = None):
        self.config = config or get_data_quality_config()
        self.consistency_rules = self.config.get_cross_stage_consistency_rules()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """執行跨階段一致性檢查"""
        try:
            validation_errors = []
            validation_warnings = []
            
            # 階段依賴檢查
            dependency_result = self._check_stage_dependencies(data)
            consistency_result = ConsistencyCheckResult(
                consistency_score=dependency_result.get('score', 0.0),
                inconsistencies=dependency_result.get('inconsistencies', []),
                data_flow_integrity=dependency_result.get('integrity', False),
                transformation_errors=dependency_result.get('errors', []),
                dependency_violations=dependency_result.get('violations', [])
            )
            
            validation_errors.extend(consistency_result.transformation_errors)
            validation_errors.extend(consistency_result.dependency_violations)
            
            # 數據流驗證
            data_flow_result = self._validate_data_flow(data)
            validation_errors.extend(data_flow_result.get('errors', []))
            validation_warnings.extend(data_flow_result.get('warnings', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.CRITICAL if validation_errors else ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Cross-stage consistency validation {'failed' if validation_errors else 'passed'}",
                details={
                    'consistency_result': consistency_result,
                    'data_flow_result': data_flow_result,
                    'validation_errors': validation_errors,
                    'validation_warnings': validation_warnings
                },
                metadata={'validation_type': 'cross_stage_consistency'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Cross-stage consistency error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Consistency check error: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'cross_stage_consistency'}
            )
    
    def _check_stage_dependencies(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查階段依賴關係"""
        errors = []
        violations = []
        inconsistencies = []
        score = 100.0
        
        # 檢查衛星數量一致性
        satellite_counts = self._extract_satellite_counts(data)
        if len(set(satellite_counts.values())) > 1:
            inconsistencies.append({
                'type': 'satellite_count_mismatch',
                'details': satellite_counts
            })
            violations.append(f"Satellite count inconsistency across stages: {satellite_counts}")
            score -= 20
        
        # 檢查時間戳對齊
        timestamp_alignment = self._check_timestamp_alignment(data)
        if not timestamp_alignment['is_aligned']:
            inconsistencies.append({
                'type': 'timestamp_misalignment',
                'details': timestamp_alignment['misalignments']
            })
            violations.append("Timestamp misalignment detected across stages")
            score -= 15
        
        # 檢查座標系統一致性
        coordinate_consistency = self._check_coordinate_system_consistency(data)
        if not coordinate_consistency['is_consistent']:
            inconsistencies.append({
                'type': 'coordinate_system_inconsistency',
                'details': coordinate_consistency['issues']
            })
            errors.append("Coordinate system inconsistency detected")
            score -= 25
        
        return {
            'score': max(0.0, score),
            'inconsistencies': inconsistencies,
            'integrity': len(errors) == 0,
            'errors': errors,
            'violations': violations
        }
    
    def _extract_satellite_counts(self, data: Dict[str, Any]) -> Dict[str, int]:
        """提取各階段衛星數量"""
        counts = {}
        
        # 嘗試從不同數據結構中提取衛星數量
        if 'stage1_data' in data:
            stage1_data = data['stage1_data']
            if isinstance(stage1_data, list):
                counts['stage1'] = len(stage1_data)
            elif isinstance(stage1_data, dict) and 'satellites' in stage1_data:
                counts['stage1'] = len(stage1_data['satellites'])
        
        if 'stage2_data' in data:
            stage2_data = data['stage2_data']
            if isinstance(stage2_data, list):
                counts['stage2'] = len(stage2_data)
            elif isinstance(stage2_data, dict) and 'satellites' in stage2_data:
                counts['stage2'] = len(stage2_data['satellites'])
        
        # 通用方法：查找包含satellite_id的項目
        satellite_ids = set()
        
        def extract_satellite_ids(obj: Any):
            if isinstance(obj, dict):
                if 'satellite_id' in obj:
                    satellite_ids.add(obj['satellite_id'])
                for value in obj.values():
                    extract_satellite_ids(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_satellite_ids(item)
        
        extract_satellite_ids(data)
        if satellite_ids:
            counts['total_unique_satellites'] = len(satellite_ids)
        
        return counts
    
    def _check_timestamp_alignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查時間戳對齊"""
        timestamps_by_stage = {}
        misalignments = []
        
        # 提取各階段時間戳
        def extract_timestamps_by_stage(obj: Any, stage_prefix: str = ''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if 'stage' in key.lower():
                        new_prefix = key
                    else:
                        new_prefix = stage_prefix
                    
                    if key.lower() in ['timestamp', 'time', 'datetime']:
                        if new_prefix not in timestamps_by_stage:
                            timestamps_by_stage[new_prefix] = []
                        if isinstance(value, list):
                            timestamps_by_stage[new_prefix].extend(value)
                        else:
                            timestamps_by_stage[new_prefix].append(value)
                    else:
                        extract_timestamps_by_stage(value, new_prefix)
            elif isinstance(obj, list):
                for item in obj:
                    extract_timestamps_by_stage(item, stage_prefix)
        
        extract_timestamps_by_stage(data)
        
        # 檢查時間戳對齊
        stage_keys = list(timestamps_by_stage.keys())
        for i, stage1 in enumerate(stage_keys):
            for stage2 in stage_keys[i+1:]:
                timestamps1 = set(timestamps_by_stage[stage1])
                timestamps2 = set(timestamps_by_stage[stage2])
                
                # 檢查重疊度
                overlap = timestamps1.intersection(timestamps2)
                union = timestamps1.union(timestamps2)
                
                if len(union) > 0:
                    overlap_ratio = len(overlap) / len(union)
                    if overlap_ratio < 0.8:  # 80% 對齊閾值
                        misalignments.append({
                            'stage1': stage1,
                            'stage2': stage2,
                            'overlap_ratio': overlap_ratio
                        })
        
        return {
            'is_aligned': len(misalignments) == 0,
            'misalignments': misalignments
        }
    
    def _check_coordinate_system_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查座標系統一致性"""
        issues = []
        coordinate_systems = set()
        
        # 檢測使用的座標系統
        def detect_coordinate_systems(obj: Any, path: str = ''):
            if isinstance(obj, dict):
                # ECI 座標系統檢測
                if all(coord in obj for coord in ['x', 'y', 'z']):
                    coordinate_systems.add('eci')
                
                # 經緯度座標系統檢測
                if all(coord in obj for coord in ['latitude', 'longitude']):
                    coordinate_systems.add('geodetic')
                elif all(coord in obj for coord in ['lat', 'lon']):
                    coordinate_systems.add('geodetic')
                
                # 方位角-仰角系統檢測
                if all(coord in obj for coord in ['azimuth', 'elevation']):
                    coordinate_systems.add('topocentric')
                
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    detect_coordinate_systems(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    detect_coordinate_systems(item, path)
        
        detect_coordinate_systems(data)
        
        # 檢查座標變換一致性
        if 'eci' in coordinate_systems and 'geodetic' in coordinate_systems:
            # 驗證 ECI 到經緯度的轉換是否合理
            eci_coords = self._extract_coordinates(data, 'eci')
            geodetic_coords = self._extract_coordinates(data, 'geodetic')
            
            if eci_coords and geodetic_coords:
                consistency_check = self._validate_coordinate_transformation(eci_coords, geodetic_coords)
                if not consistency_check['is_consistent']:
                    issues.extend(consistency_check['issues'])
        
        return {
            'is_consistent': len(issues) == 0,
            'coordinate_systems': list(coordinate_systems),
            'issues': issues
        }
    
    def _extract_coordinates(self, data: Dict[str, Any], coord_type: str) -> List[Dict[str, float]]:
        """提取指定類型的座標"""
        coordinates = []
        
        def extract_coords(obj: Any):
            if isinstance(obj, dict):
                if coord_type == 'eci' and all(coord in obj for coord in ['x', 'y', 'z']):
                    coordinates.append({
                        'x': obj['x'],
                        'y': obj['y'], 
                        'z': obj['z']
                    })
                elif coord_type == 'geodetic':
                    if all(coord in obj for coord in ['latitude', 'longitude']):
                        coordinates.append({
                            'lat': obj['latitude'],
                            'lon': obj['longitude']
                        })
                    elif all(coord in obj for coord in ['lat', 'lon']):
                        coordinates.append({
                            'lat': obj['lat'],
                            'lon': obj['lon']
                        })
                
                for value in obj.values():
                    extract_coords(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_coords(item)
        
        extract_coords(data)
        return coordinates
    
    def _validate_coordinate_transformation(self, eci_coords: List[Dict], geodetic_coords: List[Dict]) -> Dict[str, Any]:
        """驗證座標變換一致性"""
        issues = []
        
        # 檢查座標數量是否一致
        if len(eci_coords) != len(geodetic_coords):
            issues.append(f"Coordinate count mismatch: ECI={len(eci_coords)}, Geodetic={len(geodetic_coords)}")
        
        # 檢查座標範圍合理性
        for i, eci_coord in enumerate(eci_coords[:min(len(eci_coords), len(geodetic_coords))]):
            if i < len(geodetic_coords):
                geodetic_coord = geodetic_coords[i]
                
                # ECI座標範圍檢查 (LEO範圍)
                eci_magnitude = np.sqrt(eci_coord['x']**2 + eci_coord['y']**2 + eci_coord['z']**2)
                if not (6600 <= eci_magnitude <= 8400):  # 地球半徑 + LEO高度範圍
                    issues.append(f"ECI coordinate magnitude out of LEO range at index {i}: {eci_magnitude:.1f} km")
                
                # 經緯度範圍檢查
                lat = geodetic_coord['lat']
                lon = geodetic_coord['lon']
                if not (-90 <= lat <= 90):
                    issues.append(f"Invalid latitude at index {i}: {lat}")
                if not (-180 <= lon <= 180):
                    issues.append(f"Invalid longitude at index {i}: {lon}")
        
        return {
            'is_consistent': len(issues) == 0,
            'issues': issues
        }
    
    def _validate_data_flow(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """驗證數據流完整性"""
        errors = []
        warnings = []
        
        # 檢查輸入輸出映射
        input_output_mapping = self._check_input_output_mapping(data)
        errors.extend(input_output_mapping.get('errors', []))
        warnings.extend(input_output_mapping.get('warnings', []))
        
        # 檢查變換完整性
        transformation_integrity = self._check_transformation_integrity(data)
        errors.extend(transformation_integrity.get('errors', []))
        warnings.extend(transformation_integrity.get('warnings', []))
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_input_output_mapping(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """檢查輸入輸出映射"""
        errors = []
        warnings = []
        
        # 檢查衛星識別符保持
        if self.consistency_rules['stage_dependencies']['stage1_to_stage2']['satellite_count_consistency']:
            satellite_ids_preservation = self._check_satellite_id_preservation(data)
            if not satellite_ids_preservation['preserved']:
                errors.append("Satellite identifiers not preserved across stages")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_satellite_id_preservation(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """檢查衛星ID保持"""
        # 簡化實現：檢查不同階段是否有相同的衛星ID集合
        stage_satellite_ids = {}
        
        def extract_stage_satellite_ids(obj: Any, current_stage: str = ''):
            if isinstance(obj, dict):
                if 'satellite_id' in obj:
                    if current_stage not in stage_satellite_ids:
                        stage_satellite_ids[current_stage] = set()
                    stage_satellite_ids[current_stage].add(obj['satellite_id'])
                
                for key, value in obj.items():
                    if 'stage' in key.lower():
                        new_stage = key
                    else:
                        new_stage = current_stage
                    extract_stage_satellite_ids(value, new_stage)
            elif isinstance(obj, list):
                for item in obj:
                    extract_stage_satellite_ids(item, current_stage)
        
        extract_stage_satellite_ids(data)
        
        # 檢查ID集合是否一致
        if len(stage_satellite_ids) > 1:
            id_sets = list(stage_satellite_ids.values())
            all_same = all(id_set == id_sets[0] for id_set in id_sets)
            return {'preserved': all_same}
        
        return {'preserved': True}
    
    def _check_transformation_integrity(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """檢查變換完整性"""
        errors = []
        warnings = []
        
        # 檢查座標變換完整性
        if 'coordinate_transformations' in data:
            coord_transforms = data['coordinate_transformations']
            for transform in coord_transforms:
                if 'precision_loss' in transform:
                    precision_loss = transform['precision_loss']
                    if precision_loss > 0.01:  # 1% 精度損失閾值
                        warnings.append(f"High precision loss in coordinate transformation: {precision_loss:.2%}")
        
        return {'errors': errors, 'warnings': warnings}


class MetadataComplianceValidator(BaseValidator):
    """元數據合規性驗證器"""
    
    def __init__(self, config: DataQualityConfig = None):
        self.config = config or get_data_quality_config()
        self.metadata_rules = self.config.get_metadata_compliance_rules()
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> ValidationResult:
        """執行元數據合規性驗證"""
        try:
            validation_errors = []
            validation_warnings = []
            
            # 必需元數據檢查
            mandatory_result = self._check_mandatory_metadata(data)
            validation_errors.extend(mandatory_result.get('errors', []))
            validation_warnings.extend(mandatory_result.get('warnings', []))
            
            # 可追溯性檢查
            traceability_result = self._check_traceability_requirements(data)
            validation_errors.extend(traceability_result.get('errors', []))
            validation_warnings.extend(traceability_result.get('warnings', []))
            
            # 學術合規性檢查
            academic_result = self._check_academic_compliance(data)
            validation_errors.extend(academic_result.get('errors', []))
            validation_warnings.extend(academic_result.get('warnings', []))
            
            status = ValidationStatus.FAILED if validation_errors else ValidationStatus.PASSED
            level = ValidationLevel.CRITICAL if validation_errors else ValidationLevel.INFO
            
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=status,
                level=level,
                message=f"Metadata compliance validation {'failed' if validation_errors else 'passed'}",
                details={
                    'mandatory_metadata': mandatory_result,
                    'traceability': traceability_result,
                    'academic_compliance': academic_result,
                    'validation_errors': validation_errors,
                    'validation_warnings': validation_warnings
                },
                metadata={'validation_type': 'metadata_compliance'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=self.__class__.__name__,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Metadata compliance error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Compliance check error: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'metadata_compliance'}
            )
    
    def _check_mandatory_metadata(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """檢查必需元數據"""
        errors = []
        warnings = []
        
        mandatory_fields = [
            'processing_timestamp',
            'data_source_identification', 
            'processing_version',
            'validation_status'
        ]
        
        metadata = data.get('metadata', {})
        
        for field in mandatory_fields:
            if self.metadata_rules['mandatory_metadata'].get(field, False):
                if field not in metadata:
                    errors.append(f"Missing mandatory metadata field: {field}")
                elif not metadata[field]:
                    warnings.append(f"Empty mandatory metadata field: {field}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_traceability_requirements(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """檢查可追溯性要求"""
        errors = []
        warnings = []
        
        traceability_fields = [
            'input_data_lineage',
            'processing_parameters',
            'quality_assessment_results', 
            'error_handling_logs'
        ]
        
        metadata = data.get('metadata', {})
        
        for field in traceability_fields:
            if self.metadata_rules['traceability_requirements'].get(field, False):
                if field not in metadata:
                    errors.append(f"Missing traceability metadata: {field}")
        
        return {'errors': errors, 'warnings': warnings}
    
    def _check_academic_compliance(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """檢查學術合規性"""
        errors = []
        warnings = []
        
        academic_fields = [
            'grade_level_classification',
            'data_source_attribution',
            'methodology_documentation',
            'reproducibility_information'
        ]
        
        metadata = data.get('metadata', {})
        
        for field in academic_fields:
            if self.metadata_rules['academic_compliance'].get(field, False):
                if field not in metadata:
                    errors.append(f"Missing academic compliance metadata: {field}")
        
        # 檢查Grade分級標記
        if 'grade_level_classification' in metadata:
            grade_level = metadata['grade_level_classification']
            if grade_level not in ['A', 'B', 'C']:
                errors.append(f"Invalid grade level classification: {grade_level}")
        
        return {'errors': errors, 'warnings': warnings}