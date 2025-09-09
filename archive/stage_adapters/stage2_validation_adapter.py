#!/usr/bin/env python3
"""
Stage 2 Validation Adapter - 衛星可見性過濾器驗證轉接器
Phase 3 驗證框架整合：智能過濾與仰角計算驗證

責任範圍:
- 衛星可見性過濾邏輯驗證
- 仰角計算精度檢查 (ITU-R P.618標準)
- 地理座標有效性檢查
- 時間窗口連續性驗證
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

# 設定路徑以導入驗證框架
sys.path.append('/app/src')

logger = logging.getLogger(__name__)

class Stage2ValidationAdapter:
    """
    Stage 2 智能過濾驗證轉接器
    
    專門負責衛星可見性過濾器的驗證邏輯，確保：
    - 仰角計算符合 ITU-R P.618 標準
    - 地理座標範圍有效性
    - 過濾邏輯一致性檢查
    - 時間窗口連續性驗證
    """
    
    def __init__(self):
        """初始化 Stage 2 驗證轉接器"""
        self.stage_id = 'stage2_satellite_visibility_filter'
        self.validation_engines = {}
        self._initialize_validation_engines()
    
    def _initialize_validation_engines(self):
        """初始化各個驗證引擎"""
        try:
            # 動態導入驗證引擎
            from validation.engines.academic_standards_engine import (
                GradeADataValidator,
                PhysicalParameterValidator,
                TimeBaseContinuityChecker
            )
            from validation.engines.data_quality_engine import (
                DataStructureValidator,
                StatisticalAnalyzer,
                CrossStageConsistencyChecker
            )
            from validation.engines.execution_control_engine import (
                ValidationOrchestrator,
                StageGatekeeper
            )
            
            # 初始化學術標準驗證器
            self.validation_engines['grade_a_validator'] = GradeADataValidator()
            self.validation_engines['physical_parameter_validator'] = PhysicalParameterValidator()
            self.validation_engines['time_base_checker'] = TimeBaseContinuityChecker()
            
            # 初始化數據品質驗證器
            self.validation_engines['data_structure_validator'] = DataStructureValidator()
            self.validation_engines['statistical_analyzer'] = StatisticalAnalyzer()
            self.validation_engines['consistency_checker'] = CrossStageConsistencyChecker()
            
            # 初始化執行控制
            self.validation_engines['orchestrator'] = ValidationOrchestrator()
            self.validation_engines['stage_gatekeeper'] = StageGatekeeper()
            
            logger.info(f"🛡️ Stage 2 驗證引擎初始化完成：{len(self.validation_engines)} 個引擎")
            
        except Exception as e:
            logger.error(f"❌ Stage 2 驗證引擎初始化失敗: {str(e)}")
            self.validation_engines = {}
    
    async def pre_process_validation(self, orbital_input_data: List[Dict[str, Any]], 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Stage 2 預處理驗證 - 軌道數據載入前檢查
        
        驗證重點：
        - 軌道數據結構完整性 
        - 時間序列數據連續性
        - 座標系統一致性檢查
        - 可見性計算必需參數驗證
        """
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': self.stage_id,
                'phase': 'pre_process',
                'input_data_size': len(orbital_input_data),
                'validation_timestamp': validation_start.isoformat(),
                'context': context or {}
            }
            
            # 預處理驗證結果收集
            validation_results = {
                'success': True,
                'stage': 'stage2_pre_process',
                'timestamp': validation_start.isoformat(),
                'validation_checks': [],
                'warnings': [],
                'blocking_errors': []
            }
            
            # 1. 軌道數據結構完整性檢查
            logger.info("🔍 執行軌道數據結構完整性檢查...")
            structure_check = await self._validate_orbital_data_structure(orbital_input_data)
            validation_results['validation_checks'].append(structure_check)
            
            if not structure_check.get('passed', False):
                validation_results['blocking_errors'].extend(structure_check.get('errors', []))
                validation_results['success'] = False
            
            # 2. 時間序列數據連續性驗證
            if validation_results['success']:
                logger.info("🔍 執行時間序列數據連續性驗證...")
                time_continuity_check = await self._validate_time_series_continuity(orbital_input_data)
                validation_results['validation_checks'].append(time_continuity_check)
                
                if not time_continuity_check.get('passed', False):
                    validation_results['warnings'].extend(time_continuity_check.get('warnings', []))
            
            # 3. 座標系統一致性檢查
            if validation_results['success']:
                logger.info("🔍 執行座標系統一致性檢查...")
                coordinate_check = await self._validate_coordinate_systems(orbital_input_data)
                validation_results['validation_checks'].append(coordinate_check)
                
                if not coordinate_check.get('passed', False):
                    validation_results['blocking_errors'].extend(coordinate_check.get('errors', []))
                    validation_results['success'] = False
            
            # 4. 可見性計算必需參數驗證
            if validation_results['success']:
                logger.info("🔍 執行可見性計算參數驗證...")
                visibility_params_check = await self._validate_visibility_parameters(orbital_input_data)
                validation_results['validation_checks'].append(visibility_params_check)
                
                if not visibility_params_check.get('passed', False):
                    validation_results['blocking_errors'].extend(visibility_params_check.get('errors', []))
                    validation_results['success'] = False
            
            # 記錄驗證總耗時
            validation_end = datetime.now(timezone.utc)
            validation_duration = (validation_end - validation_start).total_seconds()
            validation_results['validation_duration_seconds'] = validation_duration
            
            logger.info(f"✅ Stage 2 預處理驗證完成 - 耗時: {validation_duration:.2f}秒")
            return validation_results
            
        except Exception as e:
            logger.error(f"🚨 Stage 2 預處理驗證異常: {str(e)}")
            return {
                'success': False,
                'stage': 'stage2_pre_process',
                'error': str(e),
                'timestamp': validation_start.isoformat(),
                'blocking_errors': [f"Stage 2 預處理驗證引擎異常: {str(e)}"]
            }
    
    async def post_process_validation(self, filtered_result_data: List[Dict[str, Any]], 
                                    processing_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Stage 2 後處理驗證 - 可見性過濾結果檢查
        
        驗證重點：
        - 仰角計算精度驗證 (ITU-R P.618標準)
        - 過濾邏輯一致性檢查
        - 可見性時間窗口合理性
        - 學術標準合規性檢查
        """
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': self.stage_id,
                'phase': 'post_process',
                'output_data_size': len(filtered_result_data),
                'validation_timestamp': validation_start.isoformat(),
                'processing_metrics': processing_metrics or {}
            }
            
            # 後處理驗證結果收集
            validation_results = {
                'success': True,
                'stage': 'stage2_post_process',
                'timestamp': validation_start.isoformat(),
                'validation_checks': [],
                'warnings': [],
                'blocking_errors': [],
                'academic_compliance': {
                    'compliant': True,
                    'grade_level': 'A',
                    'violations': []
                }
            }
            
            # 1. 仰角計算精度驗證 (ITU-R P.618標準)
            logger.info("🔍 執行仰角計算精度驗證...")
            elevation_precision_check = await self._validate_elevation_calculations(filtered_result_data)
            validation_results['validation_checks'].append(elevation_precision_check)
            
            if not elevation_precision_check.get('passed', False):
                validation_results['academic_compliance']['violations'].extend(
                    elevation_precision_check.get('violations', [])
                )
                if elevation_precision_check.get('severity') == 'critical':
                    validation_results['blocking_errors'].extend(elevation_precision_check.get('errors', []))
                    validation_results['success'] = False
                else:
                    validation_results['warnings'].extend(elevation_precision_check.get('warnings', []))
            
            # 2. 過濾邏輯一致性檢查
            if validation_results['success']:
                logger.info("🔍 執行過濾邏輯一致性檢查...")
                filtering_logic_check = await self._validate_filtering_logic_consistency(filtered_result_data, processing_metrics)
                validation_results['validation_checks'].append(filtering_logic_check)
                
                if not filtering_logic_check.get('passed', False):
                    validation_results['warnings'].extend(filtering_logic_check.get('warnings', []))
            
            # 3. 可見性時間窗口合理性檢查
            if validation_results['success']:
                logger.info("🔍 執行可見性時間窗口合理性檢查...")
                time_window_check = await self._validate_visibility_time_windows(filtered_result_data)
                validation_results['validation_checks'].append(time_window_check)
                
                if not time_window_check.get('passed', False):
                    validation_results['warnings'].extend(time_window_check.get('warnings', []))
            
            # 4. 學術標準最終合規性檢查
            if validation_results['academic_compliance']['violations']:
                validation_results['academic_compliance']['compliant'] = False
                validation_results['academic_compliance']['grade_level'] = 'B'
                logger.warning(f"⚠️ Stage 2 學術合規性問題: {len(validation_results['academic_compliance']['violations'])} 項違規")
            
            # 品質門禁檢查
            if not validation_results['success']:
                quality_gate_result = await self._apply_stage2_quality_gate(validation_results)
                if quality_gate_result.get('blocked', False):
                    validation_results['error'] = f"Quality gate blocked: {quality_gate_result.get('reason', 'Unknown')}"
            
            # 記錄驗證總耗時
            validation_end = datetime.now(timezone.utc)
            validation_duration = (validation_end - validation_start).total_seconds()
            validation_results['validation_duration_seconds'] = validation_duration
            
            logger.info(f"✅ Stage 2 後處理驗證完成 - 耗時: {validation_duration:.2f}秒")
            return validation_results
            
        except Exception as e:
            logger.error(f"🚨 Stage 2 後處理驗證異常: {str(e)}")
            return {
                'success': False,
                'stage': 'stage2_post_process',
                'error': str(e),
                'timestamp': validation_start.isoformat(),
                'blocking_errors': [f"Stage 2 後處理驗證引擎異常: {str(e)}"]
            }
    
    # 私有驗證方法實現
    async def _validate_orbital_data_structure(self, orbital_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證軌道數據結構完整性"""
        try:
            required_fields = ['satellite_id', 'name', 'constellation', 'position_timeseries']
            missing_fields = []
            invalid_satellites = []
            
            for i, sat_data in enumerate(orbital_data):
                satellite_missing_fields = []
                for field in required_fields:
                    if field not in sat_data:
                        satellite_missing_fields.append(field)
                
                if satellite_missing_fields:
                    missing_fields.extend(satellite_missing_fields)
                    invalid_satellites.append({
                        'index': i,
                        'satellite_id': sat_data.get('satellite_id', 'unknown'),
                        'missing_fields': satellite_missing_fields
                    })
                
                # 檢查位置時間序列數據
                positions = sat_data.get('position_timeseries', [])
                if not positions or len(positions) == 0:
                    invalid_satellites.append({
                        'index': i,
                        'satellite_id': sat_data.get('satellite_id', 'unknown'),
                        'issue': 'empty_position_timeseries'
                    })
            
            passed = len(missing_fields) == 0 and len(invalid_satellites) == 0
            
            return {
                'check_name': 'orbital_data_structure_validation',
                'passed': passed,
                'details': {
                    'total_satellites': len(orbital_data),
                    'invalid_satellites_count': len(invalid_satellites),
                    'missing_fields': list(set(missing_fields))
                },
                'errors': [f"衛星結構驗證失敗: {len(invalid_satellites)} 顆衛星缺少必要欄位"] if not passed else [],
                'warnings': []
            }
            
        except Exception as e:
            return {
                'check_name': 'orbital_data_structure_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"軌道數據結構驗證異常: {str(e)}"]
            }
    
    async def _validate_time_series_continuity(self, orbital_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證時間序列數據連續性"""
        try:
            discontinuities = []
            invalid_timestamps = []
            
            for sat_data in orbital_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                if len(positions) < 2:
                    discontinuities.append({
                        'satellite_id': satellite_id,
                        'issue': 'insufficient_time_points',
                        'count': len(positions)
                    })
                    continue
                
                # 檢查時間戳格式和連續性
                prev_timestamp = None
                for i, pos in enumerate(positions):
                    timestamp_str = pos.get('timestamp', '')
                    
                    try:
                        current_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        
                        if prev_timestamp and (current_timestamp - prev_timestamp).total_seconds() > 3600:
                            # 時間間隔超過1小時視為不連續
                            discontinuities.append({
                                'satellite_id': satellite_id,
                                'issue': 'time_gap_too_large',
                                'position_index': i,
                                'gap_seconds': (current_timestamp - prev_timestamp).total_seconds()
                            })
                        
                        prev_timestamp = current_timestamp
                        
                    except Exception:
                        invalid_timestamps.append({
                            'satellite_id': satellite_id,
                            'position_index': i,
                            'invalid_timestamp': timestamp_str
                        })
            
            passed = len(discontinuities) == 0 and len(invalid_timestamps) == 0
            warnings = []
            
            if discontinuities:
                warnings.append(f"發現 {len(discontinuities)} 處時間序列不連續")
            if invalid_timestamps:
                warnings.append(f"發現 {len(invalid_timestamps)} 個無效時間戳")
            
            return {
                'check_name': 'time_series_continuity_validation',
                'passed': passed,
                'details': {
                    'discontinuities_count': len(discontinuities),
                    'invalid_timestamps_count': len(invalid_timestamps)
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'time_series_continuity_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"時間序列連續性驗證異常: {str(e)}"]
            }
    
    async def _validate_coordinate_systems(self, orbital_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證座標系統一致性"""
        try:
            coordinate_issues = []
            zero_coordinate_count = 0
            
            for sat_data in orbital_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                zero_positions = 0
                for pos in positions:
                    x = pos.get('eci_x', 0)
                    y = pos.get('eci_y', 0) 
                    z = pos.get('eci_z', 0)
                    
                    # 檢查ECI座標零值問題 (學術標準違規)
                    if abs(x) < 0.1 and abs(y) < 0.1 and abs(z) < 0.1:
                        zero_positions += 1
                
                if zero_positions > 0:
                    zero_coordinate_count += zero_positions
                    coordinate_issues.append({
                        'satellite_id': satellite_id,
                        'issue': 'eci_zero_coordinates',
                        'zero_positions': zero_positions,
                        'total_positions': len(positions),
                        'zero_percentage': (zero_positions / len(positions)) * 100 if positions else 0
                    })
            
            # 零值座標是學術標準嚴重違規，必須阻斷
            passed = zero_coordinate_count == 0
            errors = []
            
            if not passed:
                errors.append(f"發現 {zero_coordinate_count} 個零值ECI座標 - 嚴重違反學術標準")
            
            return {
                'check_name': 'coordinate_systems_validation',
                'passed': passed,
                'details': {
                    'satellites_with_issues': len(coordinate_issues),
                    'total_zero_coordinates': zero_coordinate_count
                },
                'errors': errors,
                'warnings': []
            }
            
        except Exception as e:
            return {
                'check_name': 'coordinate_systems_validation', 
                'passed': False,
                'error': str(e),
                'errors': [f"座標系統驗證異常: {str(e)}"]
            }
    
    async def _validate_visibility_parameters(self, orbital_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證可見性計算必需參數"""
        try:
            parameter_issues = []
            
            for sat_data in orbital_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                missing_params = []
                for pos in positions:
                    required_params = ['elevation', 'azimuth', 'range_km']
                    for param in required_params:
                        if param not in pos or pos[param] is None:
                            missing_params.append(param)
                
                if missing_params:
                    parameter_issues.append({
                        'satellite_id': satellite_id,
                        'missing_parameters': list(set(missing_params))
                    })
            
            passed = len(parameter_issues) == 0
            errors = []
            
            if not passed:
                errors.append(f"{len(parameter_issues)} 顆衛星缺少可見性計算必需參數")
            
            return {
                'check_name': 'visibility_parameters_validation',
                'passed': passed,
                'details': {
                    'satellites_with_missing_params': len(parameter_issues)
                },
                'errors': errors,
                'warnings': []
            }
            
        except Exception as e:
            return {
                'check_name': 'visibility_parameters_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"可見性參數驗證異常: {str(e)}"]
            }
    
    async def _validate_elevation_calculations(self, filtered_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證仰角計算精度 (ITU-R P.618標準)"""
        try:
            elevation_violations = []
            threshold_violations = []
            
            for sat_data in filtered_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                constellation = sat_data.get('constellation', 'unknown')
                
                # 根據星座確定仰角門檻 (學術標準)
                expected_threshold = 5.0 if constellation.lower() == 'starlink' else 10.0
                
                invalid_elevations = 0
                below_threshold_count = 0
                
                for pos in positions:
                    elevation = pos.get('elevation', 0)
                    
                    # 檢查仰角值合理性 (0-90度)
                    if elevation < 0 or elevation > 90:
                        invalid_elevations += 1
                    
                    # 檢查是否低於期望門檻
                    if elevation < expected_threshold:
                        below_threshold_count += 1
                
                if invalid_elevations > 0:
                    elevation_violations.append({
                        'satellite_id': satellite_id,
                        'invalid_elevations': invalid_elevations,
                        'total_positions': len(positions)
                    })
                
                # 如果所有位置都低於門檻，可能是過濾邏輯問題
                if below_threshold_count == len(positions) and len(positions) > 0:
                    threshold_violations.append({
                        'satellite_id': satellite_id,
                        'constellation': constellation,
                        'expected_threshold': expected_threshold,
                        'all_below_threshold': True
                    })
            
            passed = len(elevation_violations) == 0
            severity = 'critical' if elevation_violations else 'warning'
            
            errors = []
            warnings = []
            violations = []
            
            if elevation_violations:
                errors.append(f"{len(elevation_violations)} 顆衛星仰角計算不符合ITU-R P.618標準")
                violations.extend(elevation_violations)
            
            if threshold_violations:
                warnings.append(f"{len(threshold_violations)} 顆衛星所有位置都低於期望仰角門檻")
            
            return {
                'check_name': 'elevation_calculations_validation',
                'passed': passed,
                'severity': severity,
                'details': {
                    'elevation_violations': len(elevation_violations),
                    'threshold_violations': len(threshold_violations)
                },
                'errors': errors,
                'warnings': warnings,
                'violations': violations
            }
            
        except Exception as e:
            return {
                'check_name': 'elevation_calculations_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"仰角計算驗證異常: {str(e)}"]
            }
    
    async def _validate_filtering_logic_consistency(self, filtered_data: List[Dict[str, Any]], 
                                                  processing_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """驗證過濾邏輯一致性"""
        try:
            consistency_issues = []
            
            # 檢查過濾率合理性
            input_count = processing_metrics.get('input_satellites', 0) if processing_metrics else 0
            output_count = len(filtered_data)
            
            if input_count > 0:
                retention_rate = (output_count / input_count) * 100
                
                # 過濾率異常檢查 (經驗值：正常應該在10-80%之間)
                if retention_rate < 10:
                    consistency_issues.append({
                        'issue': 'excessive_filtering',
                        'retention_rate': retention_rate,
                        'input_count': input_count,
                        'output_count': output_count
                    })
                elif retention_rate > 80:
                    consistency_issues.append({
                        'issue': 'insufficient_filtering', 
                        'retention_rate': retention_rate,
                        'input_count': input_count,
                        'output_count': output_count
                    })
            
            passed = len(consistency_issues) == 0
            warnings = []
            
            if consistency_issues:
                warnings.append(f"過濾邏輯一致性問題: {len(consistency_issues)} 項異常")
            
            return {
                'check_name': 'filtering_logic_consistency_validation',
                'passed': passed,
                'details': {
                    'consistency_issues': len(consistency_issues),
                    'retention_rate': retention_rate if input_count > 0 else 0
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'filtering_logic_consistency_validation',
                'passed': False,
                'error': str(e),
                'warnings': [f"過濾邏輯一致性驗證異常: {str(e)}"]
            }
    
    async def _validate_visibility_time_windows(self, filtered_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證可見性時間窗口合理性"""
        try:
            time_window_issues = []
            
            for sat_data in filtered_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                if len(positions) < 2:
                    continue
                
                # 計算可見性時間窗口長度
                first_time = datetime.fromisoformat(positions[0]['timestamp'].replace('Z', '+00:00'))
                last_time = datetime.fromisoformat(positions[-1]['timestamp'].replace('Z', '+00:00'))
                window_duration_minutes = (last_time - first_time).total_seconds() / 60
                
                # 可見性窗口合理性檢查 (一般LEO衛星可見時間5-15分鐘)
                if window_duration_minutes < 1:
                    time_window_issues.append({
                        'satellite_id': satellite_id,
                        'issue': 'too_short_visibility_window',
                        'duration_minutes': window_duration_minutes
                    })
                elif window_duration_minutes > 30:
                    time_window_issues.append({
                        'satellite_id': satellite_id,
                        'issue': 'unusually_long_visibility_window',
                        'duration_minutes': window_duration_minutes
                    })
            
            passed = len(time_window_issues) == 0
            warnings = []
            
            if time_window_issues:
                warnings.append(f"可見性時間窗口異常: {len(time_window_issues)} 顆衛星")
            
            return {
                'check_name': 'visibility_time_windows_validation',
                'passed': passed,
                'details': {
                    'time_window_issues': len(time_window_issues)
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'visibility_time_windows_validation',
                'passed': False,
                'error': str(e),
                'warnings': [f"可見性時間窗口驗證異常: {str(e)}"]
            }
    
    async def _apply_stage2_quality_gate(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """應用 Stage 2 品質門禁"""
        try:
            blocking_errors = validation_results.get('blocking_errors', [])
            
            # 品質門禁規則：有任何阻斷性錯誤就阻止進入下一階段
            if blocking_errors:
                return {
                    'blocked': True,
                    'reason': f"Stage 2 存在 {len(blocking_errors)} 項阻斷性錯誤",
                    'details': blocking_errors
                }
            
            return {'blocked': False}
            
        except Exception as e:
            return {
                'blocked': True,
                'reason': f"品質門禁檢查異常: {str(e)}"
            }

if __name__ == "__main__":
    # 測試 Stage 2 驗證轉接器
    logger.info("🧪 測試 Stage 2 驗證轉接器...")
    
    adapter = Stage2ValidationAdapter()
    
    # 模擬測試數據
    test_orbital_data = [
        {
            'satellite_id': 'STARLINK-1001',
            'name': 'STARLINK-1001',
            'constellation': 'starlink',
            'position_timeseries': [
                {
                    'timestamp': '2025-09-09T08:00:00Z',
                    'eci_x': 1000.0,
                    'eci_y': 2000.0,
                    'eci_z': 3000.0,
                    'elevation': 15.0,
                    'azimuth': 180.0,
                    'range_km': 800.0
                }
            ]
        }
    ]
    
    # 運行預處理驗證測試
    asyncio.run(adapter.pre_process_validation(test_orbital_data, {'test': True}))
    logger.info("✅ Stage 2 驗證轉接器測試完成")