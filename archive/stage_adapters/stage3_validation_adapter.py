#!/usr/bin/env python3
"""
Stage 3 Validation Adapter - 信號分析處理器驗證轉接器
Phase 3 驗證框架整合：信號強度分析與路徑損耗計算驗證

責任範圍:
- Friis公式實施驗證 (物理公式正確性)
- 都卜勒頻移計算檢查 (相對速度精度) 
- 大氣衰減模型合規 (ITU-R P.618標準)
- RSRP/RSRQ數值合理性 (無固定假設值)
"""

import asyncio
import sys
import os
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

# 設定路徑以導入驗證框架
sys.path.append('/app/src')

logger = logging.getLogger(__name__)

class Stage3ValidationAdapter:
    """
    Stage 3 信號分析驗證轉接器
    
    專門負責信號分析處理器的驗證邏輯，確保：
    - Friis公式實施符合物理原理
    - 都卜勒頻移計算使用真實相對速度
    - 大氣衰減模型符合ITU-R P.618標準
    - RSRP/RSRQ值基於真實計算而非假設
    """
    
    def __init__(self):
        """初始化 Stage 3 驗證轉接器"""
        self.stage_id = 'stage3_signal_quality_analysis'
        self.validation_engines = {}
        self._initialize_validation_engines()
        
        # 物理常數 (ITU-R標準)
        self.SPEED_OF_LIGHT = 299792458.0  # m/s
        self.CARRIER_FREQUENCY_GHZ = {
            'starlink': 10.7,     # Ku-band downlink
            'oneweb': 19.7        # Ka-band downlink
        }
        
        # RSRP/RSRQ合理範圍 (3GPP標準)
        self.RSRP_RANGE = (-140.0, -44.0)  # dBm
        self.RSRQ_RANGE = (-20.0, -3.0)    # dB
        
        # 路徑損耗合理範圍 (LEO衛星)
        self.PATH_LOSS_RANGE = (150.0, 190.0)  # dB
    
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
            
            logger.info(f"🛡️ Stage 3 驗證引擎初始化完成：{len(self.validation_engines)} 個引擎")
            
        except Exception as e:
            logger.error(f"❌ Stage 3 驗證引擎初始化失敗: {str(e)}")
            self.validation_engines = {}
    
    async def pre_process_validation(self, filtering_input_data: List[Dict[str, Any]], 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Stage 3 預處理驗證 - 智能過濾數據載入前檢查
        
        驗證重點：
        - 可見性過濾數據結構完整性
        - 仰角、方位角、距離數據有效性
        - 時間序列數據連續性檢查
        - 信號計算必需參數驗證
        """
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': self.stage_id,
                'phase': 'pre_process',
                'input_data_size': len(filtering_input_data),
                'validation_timestamp': validation_start.isoformat(),
                'context': context or {}
            }
            
            # 預處理驗證結果收集
            validation_results = {
                'success': True,
                'stage': 'stage3_pre_process',
                'timestamp': validation_start.isoformat(),
                'validation_checks': [],
                'warnings': [],
                'blocking_errors': []
            }
            
            # 1. 可見性過濾數據結構完整性檢查
            logger.info("🔍 執行可見性過濾數據結構完整性檢查...")
            structure_check = await self._validate_filtering_data_structure(filtering_input_data)
            validation_results['validation_checks'].append(structure_check)
            
            if not structure_check.get('passed', False):
                validation_results['blocking_errors'].extend(structure_check.get('errors', []))
                validation_results['success'] = False
            
            # 2. 信號計算必需參數驗證
            if validation_results['success']:
                logger.info("🔍 執行信號計算必需參數驗證...")
                signal_params_check = await self._validate_signal_calculation_parameters(filtering_input_data)
                validation_results['validation_checks'].append(signal_params_check)
                
                if not signal_params_check.get('passed', False):
                    validation_results['blocking_errors'].extend(signal_params_check.get('errors', []))
                    validation_results['success'] = False
            
            # 3. 幾何數據有效性檢查
            if validation_results['success']:
                logger.info("🔍 執行幾何數據有效性檢查...")
                geometry_check = await self._validate_geometry_data(filtering_input_data)
                validation_results['validation_checks'].append(geometry_check)
                
                if not geometry_check.get('passed', False):
                    validation_results['warnings'].extend(geometry_check.get('warnings', []))
            
            # 4. 星座特定參數驗證
            if validation_results['success']:
                logger.info("🔍 執行星座特定參數驗證...")
                constellation_params_check = await self._validate_constellation_specific_params(filtering_input_data)
                validation_results['validation_checks'].append(constellation_params_check)
                
                if not constellation_params_check.get('passed', False):
                    validation_results['warnings'].extend(constellation_params_check.get('warnings', []))
            
            # 記錄驗證總耗時
            validation_end = datetime.now(timezone.utc)
            validation_duration = (validation_end - validation_start).total_seconds()
            validation_results['validation_duration_seconds'] = validation_duration
            
            logger.info(f"✅ Stage 3 預處理驗證完成 - 耗時: {validation_duration:.2f}秒")
            return validation_results
            
        except Exception as e:
            logger.error(f"🚨 Stage 3 預處理驗證異常: {str(e)}")
            return {
                'success': False,
                'stage': 'stage3_pre_process',
                'error': str(e),
                'timestamp': validation_start.isoformat(),
                'blocking_errors': [f"Stage 3 預處理驗證引擎異常: {str(e)}"]
            }
    
    async def post_process_validation(self, signal_analysis_result_data: Dict[str, Any], 
                                    processing_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Stage 3 後處理驗證 - 信號分析結果檢查
        
        驗證重點：
        - Friis公式實施驗證 (物理公式正確性)
        - 都卜勒頻移計算檢查 (相對速度精度)
        - RSRP/RSRQ數值合理性驗證
        - 路徑損耗計算合規性檢查
        """
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': self.stage_id,
                'phase': 'post_process',
                'output_data_type': type(signal_analysis_result_data).__name__,
                'validation_timestamp': validation_start.isoformat(),
                'processing_metrics': processing_metrics or {}
            }
            
            # 後處理驗證結果收集
            validation_results = {
                'success': True,
                'stage': 'stage3_post_process',
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
            
            # 提取衛星數據用於驗證
            satellites_data = self._extract_satellites_data(signal_analysis_result_data)
            
            # 1. Friis公式實施驗證
            logger.info("🔍 執行Friis公式實施驗證...")
            friis_validation_check = await self._validate_friis_formula_implementation(satellites_data)
            validation_results['validation_checks'].append(friis_validation_check)
            
            if not friis_validation_check.get('passed', False):
                validation_results['academic_compliance']['violations'].extend(
                    friis_validation_check.get('violations', [])
                )
                if friis_validation_check.get('severity') == 'critical':
                    validation_results['blocking_errors'].extend(friis_validation_check.get('errors', []))
                    validation_results['success'] = False
                else:
                    validation_results['warnings'].extend(friis_validation_check.get('warnings', []))
            
            # 2. 都卜勒頻移計算驗證
            if validation_results['success']:
                logger.info("🔍 執行都卜勒頻移計算驗證...")
                doppler_validation_check = await self._validate_doppler_shift_calculations(satellites_data)
                validation_results['validation_checks'].append(doppler_validation_check)
                
                if not doppler_validation_check.get('passed', False):
                    validation_results['warnings'].extend(doppler_validation_check.get('warnings', []))
            
            # 3. RSRP/RSRQ數值合理性驗證
            if validation_results['success']:
                logger.info("🔍 執行RSRP/RSRQ數值合理性驗證...")
                signal_values_check = await self._validate_signal_values_reasonableness(satellites_data)
                validation_results['validation_checks'].append(signal_values_check)
                
                if not signal_values_check.get('passed', False):
                    validation_results['academic_compliance']['violations'].extend(
                        signal_values_check.get('violations', [])
                    )
                    if signal_values_check.get('severity') == 'critical':
                        validation_results['blocking_errors'].extend(signal_values_check.get('errors', []))
                        validation_results['success'] = False
                    else:
                        validation_results['warnings'].extend(signal_values_check.get('warnings', []))
            
            # 4. 大氣衰減模型合規性檢查
            if validation_results['success']:
                logger.info("🔍 執行大氣衰減模型合規性檢查...")
                atmospheric_model_check = await self._validate_atmospheric_attenuation_model(satellites_data)
                validation_results['validation_checks'].append(atmospheric_model_check)
                
                if not atmospheric_model_check.get('passed', False):
                    validation_results['warnings'].extend(atmospheric_model_check.get('warnings', []))
            
            # 5. 學術標準最終合規性檢查
            if validation_results['academic_compliance']['violations']:
                validation_results['academic_compliance']['compliant'] = False
                validation_results['academic_compliance']['grade_level'] = 'B'
                logger.warning(f"⚠️ Stage 3 學術合規性問題: {len(validation_results['academic_compliance']['violations'])} 項違規")
            
            # 品質門禁檢查
            if not validation_results['success']:
                quality_gate_result = await self._apply_stage3_quality_gate(validation_results)
                if quality_gate_result.get('blocked', False):
                    validation_results['error'] = f"Quality gate blocked: {quality_gate_result.get('reason', 'Unknown')}"
            
            # 記錄驗證總耗時
            validation_end = datetime.now(timezone.utc)
            validation_duration = (validation_end - validation_start).total_seconds()
            validation_results['validation_duration_seconds'] = validation_duration
            
            logger.info(f"✅ Stage 3 後處理驗證完成 - 耗時: {validation_duration:.2f}秒")
            return validation_results
            
        except Exception as e:
            logger.error(f"🚨 Stage 3 後處理驗證異常: {str(e)}")
            return {
                'success': False,
                'stage': 'stage3_post_process',
                'error': str(e),
                'timestamp': validation_start.isoformat(),
                'blocking_errors': [f"Stage 3 後處理驗證引擎異常: {str(e)}"]
            }
    
    # 私有驗證方法實現
    async def _validate_filtering_data_structure(self, filtering_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證可見性過濾數據結構完整性"""
        try:
            required_fields = ['satellite_id', 'constellation', 'position_timeseries']
            missing_fields = []
            invalid_satellites = []
            
            for i, sat_data in enumerate(filtering_data):
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
                'check_name': 'filtering_data_structure_validation',
                'passed': passed,
                'details': {
                    'total_satellites': len(filtering_data),
                    'invalid_satellites_count': len(invalid_satellites),
                    'missing_fields': list(set(missing_fields))
                },
                'errors': [f"可見性過濾數據結構驗證失敗: {len(invalid_satellites)} 顆衛星缺少必要欄位"] if not passed else [],
                'warnings': []
            }
            
        except Exception as e:
            return {
                'check_name': 'filtering_data_structure_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"過濾數據結構驗證異常: {str(e)}"]
            }
    
    async def _validate_signal_calculation_parameters(self, filtering_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證信號計算必需參數"""
        try:
            parameter_issues = []
            
            for sat_data in filtering_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                missing_params = []
                for pos in positions:
                    # 檢查信號計算必需的幾何參數
                    required_geometry_params = ['elevation', 'azimuth', 'range_km']
                    for param in required_geometry_params:
                        if param not in pos or pos[param] is None:
                            missing_params.append(param)
                    
                    # 檢查ECI座標 (用於相對速度計算)
                    required_eci_params = ['eci_x', 'eci_y', 'eci_z']
                    for param in required_eci_params:
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
                errors.append(f"{len(parameter_issues)} 顆衛星缺少信號計算必需參數")
            
            return {
                'check_name': 'signal_calculation_parameters_validation',
                'passed': passed,
                'details': {
                    'satellites_with_missing_params': len(parameter_issues)
                },
                'errors': errors,
                'warnings': []
            }
            
        except Exception as e:
            return {
                'check_name': 'signal_calculation_parameters_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"信號計算參數驗證異常: {str(e)}"]
            }
    
    async def _validate_geometry_data(self, filtering_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證幾何數據有效性"""
        try:
            geometry_issues = []
            
            for sat_data in filtering_data:
                positions = sat_data.get('position_timeseries', [])
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                invalid_geometry_count = 0
                for pos in positions:
                    elevation = pos.get('elevation', -999)
                    azimuth = pos.get('azimuth', -999)
                    range_km = pos.get('range_km', -1)
                    
                    # 檢查仰角範圍 (0-90度)
                    if elevation < 0 or elevation > 90:
                        invalid_geometry_count += 1
                        continue
                    
                    # 檢查方位角範圍 (0-360度)
                    if azimuth < 0 or azimuth > 360:
                        invalid_geometry_count += 1
                        continue
                    
                    # 檢查距離合理性 (LEO衛星 400-2000km)
                    if range_km < 400 or range_km > 2000:
                        invalid_geometry_count += 1
                        continue
                
                if invalid_geometry_count > 0:
                    geometry_issues.append({
                        'satellite_id': satellite_id,
                        'invalid_positions': invalid_geometry_count,
                        'total_positions': len(positions),
                        'invalid_percentage': (invalid_geometry_count / len(positions)) * 100 if positions else 0
                    })
            
            passed = len(geometry_issues) == 0
            warnings = []
            
            if geometry_issues:
                warnings.append(f"幾何數據異常: {len(geometry_issues)} 顆衛星有無效的幾何參數")
            
            return {
                'check_name': 'geometry_data_validation',
                'passed': passed,
                'details': {
                    'satellites_with_geometry_issues': len(geometry_issues)
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'geometry_data_validation',
                'passed': False,
                'error': str(e),
                'warnings': [f"幾何數據驗證異常: {str(e)}"]
            }
    
    async def _validate_constellation_specific_params(self, filtering_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證星座特定參數"""
        try:
            constellation_issues = []
            constellation_counts = {}
            
            for sat_data in filtering_data:
                constellation = sat_data.get('constellation', 'unknown').lower()
                constellation_counts[constellation] = constellation_counts.get(constellation, 0) + 1
                
                # 檢查是否為已知星座
                if constellation not in self.CARRIER_FREQUENCY_GHZ:
                    constellation_issues.append({
                        'satellite_id': sat_data.get('satellite_id', 'unknown'),
                        'issue': 'unknown_constellation',
                        'constellation': constellation
                    })
            
            passed = len(constellation_issues) == 0
            warnings = []
            
            if constellation_issues:
                warnings.append(f"未知星座: {len(constellation_issues)} 顆衛星屬於未知星座")
            
            # 檢查星座分布合理性
            if len(constellation_counts) == 0:
                warnings.append("沒有有效的星座數據")
            
            return {
                'check_name': 'constellation_specific_params_validation',
                'passed': passed,
                'details': {
                    'constellation_distribution': constellation_counts,
                    'unknown_constellation_count': len(constellation_issues)
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'constellation_specific_params_validation',
                'passed': False,
                'error': str(e),
                'warnings': [f"星座特定參數驗證異常: {str(e)}"]
            }
    
    def _extract_satellites_data(self, signal_analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """從信號分析結果中提取衛星數據"""
        satellites_data = []
        
        # 嘗試從不同的結構中提取衛星數據
        if 'constellations' in signal_analysis_result:
            for constellation_name, constellation_data in signal_analysis_result['constellations'].items():
                satellites = constellation_data.get('satellites', [])
                for sat in satellites:
                    satellites_data.append(sat)
        
        elif 'satellites' in signal_analysis_result:
            satellites_data = signal_analysis_result['satellites']
        
        return satellites_data
    
    async def _validate_friis_formula_implementation(self, satellites_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證Friis公式實施 (物理公式正確性)"""
        try:
            friis_violations = []
            sample_size = min(50, len(satellites_data))  # 抽樣驗證
            
            for sat_data in satellites_data[:sample_size]:
                satellite_id = sat_data.get('satellite_id', 'unknown')
                constellation = sat_data.get('constellation', 'unknown').lower()
                
                # 獲取載波頻率
                if constellation in self.CARRIER_FREQUENCY_GHZ:
                    carrier_freq_ghz = self.CARRIER_FREQUENCY_GHZ[constellation]
                else:
                    continue  # 跳過未知星座
                
                positions = sat_data.get('position_timeseries', [])
                for pos in positions:
                    range_km = pos.get('range_km', 0)
                    path_loss_db = pos.get('path_loss_db')
                    
                    if range_km > 0 and path_loss_db is not None:
                        # 計算理論Friis自由空間路徑損耗
                        range_m = range_km * 1000
                        wavelength = self.SPEED_OF_LIGHT / (carrier_freq_ghz * 1e9)
                        theoretical_fspl = 20 * math.log10(4 * math.pi * range_m / wavelength)
                        
                        # 檢查計算值與理論值的偏差
                        deviation = abs(path_loss_db - theoretical_fspl)
                        
                        # 允許10dB偏差 (考慮大氣衰減等因素)
                        if deviation > 10.0:
                            friis_violations.append({
                                'satellite_id': satellite_id,
                                'constellation': constellation,
                                'calculated_loss': path_loss_db,
                                'theoretical_fspl': theoretical_fspl,
                                'deviation': deviation,
                                'range_km': range_km
                            })
                            break  # 每顆衛星只記錄一次違規
            
            passed = len(friis_violations) == 0
            severity = 'critical' if len(friis_violations) > sample_size * 0.5 else 'warning'
            
            errors = []
            warnings = []
            violations = []
            
            if friis_violations:
                if severity == 'critical':
                    errors.append(f"Friis公式實施嚴重偏離物理原理: {len(friis_violations)} 顆衛星計算異常")
                else:
                    warnings.append(f"Friis公式實施偏差: {len(friis_violations)} 顆衛星計算偏差較大")
                violations.extend(friis_violations)
            
            return {
                'check_name': 'friis_formula_implementation_validation',
                'passed': passed,
                'severity': severity,
                'details': {
                    'sample_size': sample_size,
                    'violations_count': len(friis_violations)
                },
                'errors': errors,
                'warnings': warnings,
                'violations': violations
            }
            
        except Exception as e:
            return {
                'check_name': 'friis_formula_implementation_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"Friis公式驗證異常: {str(e)}"]
            }
    
    async def _validate_doppler_shift_calculations(self, satellites_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證都卜勒頻移計算 (相對速度精度)"""
        try:
            doppler_issues = []
            sample_size = min(30, len(satellites_data))  # 抽樣驗證
            
            for sat_data in satellites_data[:sample_size]:
                satellite_id = sat_data.get('satellite_id', 'unknown')
                constellation = sat_data.get('constellation', 'unknown').lower()
                
                positions = sat_data.get('position_timeseries', [])
                if len(positions) < 2:
                    continue  # 需要至少2個位置點來計算相對速度
                
                # 檢查都卜勒頻移是否合理
                doppler_shifts = []
                for pos in positions:
                    doppler_hz = pos.get('doppler_shift_hz')
                    if doppler_hz is not None:
                        doppler_shifts.append(doppler_hz)
                
                if doppler_shifts:
                    # 檢查都卜勒頻移範圍合理性 (LEO衛星應在±50kHz範圍內)
                    max_doppler = max(abs(d) for d in doppler_shifts)
                    if max_doppler > 50000:  # 50kHz
                        doppler_issues.append({
                            'satellite_id': satellite_id,
                            'max_doppler_hz': max_doppler,
                            'issue': 'excessive_doppler_shift'
                        })
                    
                    # 檢查都卜勒頻移變化是否連續
                    if len(doppler_shifts) > 1:
                        max_change = max(abs(doppler_shifts[i+1] - doppler_shifts[i]) 
                                       for i in range(len(doppler_shifts)-1))
                        if max_change > 10000:  # 10kHz 跳躍
                            doppler_issues.append({
                                'satellite_id': satellite_id,
                                'max_change_hz': max_change,
                                'issue': 'discontinuous_doppler_shift'
                            })
            
            passed = len(doppler_issues) == 0
            warnings = []
            
            if doppler_issues:
                warnings.append(f"都卜勒頻移計算異常: {len(doppler_issues)} 顆衛星")
            
            return {
                'check_name': 'doppler_shift_calculations_validation',
                'passed': passed,
                'details': {
                    'sample_size': sample_size,
                    'doppler_issues_count': len(doppler_issues)
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'doppler_shift_calculations_validation',
                'passed': False,
                'error': str(e),
                'warnings': [f"都卜勒頻移計算驗證異常: {str(e)}"]
            }
    
    async def _validate_signal_values_reasonableness(self, satellites_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證RSRP/RSRQ數值合理性 (無固定假設值)"""
        try:
            signal_violations = []
            fixed_value_count = 0
            sample_size = min(100, len(satellites_data))  # 抽樣驗證
            
            for sat_data in satellites_data[:sample_size]:
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                positions = sat_data.get('position_timeseries', [])
                rsrp_values = []
                rsrq_values = []
                
                for pos in positions:
                    rsrp = pos.get('rsrp_dbm')
                    rsrq = pos.get('rsrq_db')
                    
                    if rsrp is not None:
                        rsrp_values.append(rsrp)
                    if rsrq is not None:
                        rsrq_values.append(rsrq)
                
                # 檢查RSRP值
                if rsrp_values:
                    # 檢查範圍合理性
                    invalid_rsrp = [r for r in rsrp_values if r < self.RSRP_RANGE[0] or r > self.RSRP_RANGE[1]]
                    if invalid_rsrp:
                        signal_violations.append({
                            'satellite_id': satellite_id,
                            'issue': 'rsrp_out_of_range',
                            'invalid_count': len(invalid_rsrp),
                            'range_expected': self.RSRP_RANGE
                        })
                    
                    # 檢查是否為固定值 (學術造假檢測)
                    unique_rsrp = set(rsrp_values)
                    if len(unique_rsrp) == 1 and len(rsrp_values) > 5:
                        fixed_value_count += 1
                        signal_violations.append({
                            'satellite_id': satellite_id,
                            'issue': 'fixed_rsrp_value',
                            'fixed_value': list(unique_rsrp)[0],
                            'sample_count': len(rsrp_values)
                        })
                
                # 檢查RSRQ值
                if rsrq_values:
                    # 檢查範圍合理性
                    invalid_rsrq = [r for r in rsrq_values if r < self.RSRQ_RANGE[0] or r > self.RSRQ_RANGE[1]]
                    if invalid_rsrq:
                        signal_violations.append({
                            'satellite_id': satellite_id,
                            'issue': 'rsrq_out_of_range',
                            'invalid_count': len(invalid_rsrq),
                            'range_expected': self.RSRQ_RANGE
                        })
                    
                    # 檢查是否為固定值
                    unique_rsrq = set(rsrq_values)
                    if len(unique_rsrq) == 1 and len(rsrq_values) > 5:
                        fixed_value_count += 1
                        signal_violations.append({
                            'satellite_id': satellite_id,
                            'issue': 'fixed_rsrq_value',
                            'fixed_value': list(unique_rsrq)[0],
                            'sample_count': len(rsrq_values)
                        })
            
            passed = len(signal_violations) == 0
            severity = 'critical' if fixed_value_count > sample_size * 0.3 else 'warning'
            
            errors = []
            warnings = []
            violations = []
            
            if signal_violations:
                if severity == 'critical':
                    errors.append(f"RSRP/RSRQ數值嚴重違反學術標準: {fixed_value_count} 顆衛星使用固定假設值")
                else:
                    warnings.append(f"RSRP/RSRQ數值異常: {len(signal_violations)} 項問題")
                violations.extend(signal_violations)
            
            return {
                'check_name': 'signal_values_reasonableness_validation',
                'passed': passed,
                'severity': severity,
                'details': {
                    'sample_size': sample_size,
                    'signal_violations_count': len(signal_violations),
                    'fixed_value_count': fixed_value_count
                },
                'errors': errors,
                'warnings': warnings,
                'violations': violations
            }
            
        except Exception as e:
            return {
                'check_name': 'signal_values_reasonableness_validation',
                'passed': False,
                'error': str(e),
                'errors': [f"RSRP/RSRQ數值驗證異常: {str(e)}"]
            }
    
    async def _validate_atmospheric_attenuation_model(self, satellites_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """驗證大氣衰減模型合規 (ITU-R P.618標準)"""
        try:
            atmospheric_issues = []
            sample_size = min(50, len(satellites_data))
            
            for sat_data in satellites_data[:sample_size]:
                satellite_id = sat_data.get('satellite_id', 'unknown')
                
                positions = sat_data.get('position_timeseries', [])
                for pos in positions:
                    elevation = pos.get('elevation', 0)
                    atmospheric_loss_db = pos.get('atmospheric_loss_db')
                    
                    if elevation > 0 and atmospheric_loss_db is not None:
                        # 基於ITU-R P.618的大氣衰減合理性檢查
                        # 低仰角時衰減應該較大
                        expected_max_loss = 5.0  # dB for clear sky
                        if elevation < 10:  # 低仰角
                            expected_max_loss = 10.0  # dB
                        
                        if atmospheric_loss_db > expected_max_loss:
                            atmospheric_issues.append({
                                'satellite_id': satellite_id,
                                'elevation': elevation,
                                'atmospheric_loss': atmospheric_loss_db,
                                'expected_max': expected_max_loss,
                                'issue': 'excessive_atmospheric_loss'
                            })
            
            passed = len(atmospheric_issues) == 0
            warnings = []
            
            if atmospheric_issues:
                warnings.append(f"大氣衰減模型異常: {len(atmospheric_issues)} 個位置點")
            
            return {
                'check_name': 'atmospheric_attenuation_model_validation',
                'passed': passed,
                'details': {
                    'sample_size': sample_size,
                    'atmospheric_issues_count': len(atmospheric_issues)
                },
                'errors': [],
                'warnings': warnings
            }
            
        except Exception as e:
            return {
                'check_name': 'atmospheric_attenuation_model_validation',
                'passed': False,
                'error': str(e),
                'warnings': [f"大氣衰減模型驗證異常: {str(e)}"]
            }
    
    async def _apply_stage3_quality_gate(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """應用 Stage 3 品質門禁"""
        try:
            blocking_errors = validation_results.get('blocking_errors', [])
            
            # 品質門禁規則：有任何阻斷性錯誤就阻止進入下一階段
            if blocking_errors:
                return {
                    'blocked': True,
                    'reason': f"Stage 3 存在 {len(blocking_errors)} 項阻斷性錯誤",
                    'details': blocking_errors
                }
            
            return {'blocked': False}
            
        except Exception as e:
            return {
                'blocked': True,
                'reason': f"品質門禁檢查異常: {str(e)}"
            }

if __name__ == "__main__":
    # 測試 Stage 3 驗證轉接器
    logger.info("🧪 測試 Stage 3 驗證轉接器...")
    
    adapter = Stage3ValidationAdapter()
    
    # 模擬測試數據
    test_filtering_data = [
        {
            'satellite_id': 'STARLINK-1001',
            'constellation': 'starlink',
            'position_timeseries': [
                {
                    'elevation': 25.0,
                    'azimuth': 180.0,
                    'range_km': 800.0,
                    'eci_x': 1000.0,
                    'eci_y': 2000.0,
                    'eci_z': 3000.0
                }
            ]
        }
    ]
    
    # 運行預處理驗證測試
    asyncio.run(adapter.pre_process_validation(test_filtering_data, {'test': True}))
    logger.info("✅ Stage 3 驗證轉接器測試完成")