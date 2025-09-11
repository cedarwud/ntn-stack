"""
Stage 1 驗證轉接器
Stage 1 Validation Adapter

將新驗證框架整合到 Stage1TLEProcessor 中
適配現有軌道計算處理器，實現零侵入式驗證整合
"""

from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime, timezone
# asdict removed - using ValidationResult.to_dict() instead

logger = logging.getLogger(__name__)

from validation.core.base_validator import ValidationResult, ValidationStatus, ValidationLevel
from validation.engines.academic_standards_engine import (
    GradeADataValidator,
    ZeroValueDetector, 
    TimeBaseContinuityChecker,
    PhysicalParameterValidator
)
from validation.engines.data_quality_engine import (
    DataStructureValidator,
    StatisticalAnalyzer
)
from validation.engines.execution_control_engine import (
    ValidationOrchestrator,
    StageGatekeeper,
    ValidationSnapshotManager
)
from validation.config.academic_standards_config import get_academic_config
from validation.config.data_quality_config import get_data_quality_config


class Stage1ValidationAdapter:
    """Stage 1 軌道計算驗證轉接器"""
    
    def __init__(self, output_dir: str = "/app/data"):
        # 驗證引擎初始化
        self.academic_config = get_academic_config()
        self.quality_config = get_data_quality_config()
        
        # Stage 1 專用驗證器
        self.grade_a_validator = GradeADataValidator(self.academic_config)
        self.zero_value_detector = ZeroValueDetector(self.academic_config)
        self.time_base_checker = TimeBaseContinuityChecker(self.academic_config)
        self.physics_validator = PhysicalParameterValidator(self.academic_config)
        self.structure_validator = DataStructureValidator(self.quality_config)
        self.statistical_analyzer = StatisticalAnalyzer(self.quality_config)
        
        # 執行控制組件
        self.orchestrator = ValidationOrchestrator()
        self.gatekeeper = StageGatekeeper(self.orchestrator)
        self.snapshot_manager = ValidationSnapshotManager("/app/data/validation_snapshots")
        
        # 驗證歷史記錄
        self.validation_history: List[Dict[str, Any]] = []
        self.current_validation_context = {}
    
    async def pre_process_validation(self, input_data: Dict, validation_context: Dict) -> Dict:
        """執行預處理驗證"""
        validation_start = datetime.now(timezone.utc)
        validation_results = []
        
        try:
            logger.info("🔍 執行階段一預處理驗證...")
            
            # TLE完整性檢查
            tle_result = await self._validate_tle_completeness(
                input_data.get('tle_data', []), 
                validation_context
            )
            validation_results.append(tle_result)
            
            # 時間基準預驗證
            time_result = await self._pre_validate_time_base(
                input_data.get('tle_data', []), 
                validation_context
            )
            validation_results.append(time_result)
            
            # 學術標準預檢查
            academic_result = await self._validate_academic_standards(
                input_data.get('tle_data', []), 
                validation_context
            )
            validation_results.append(academic_result)
            
            # 評估預處理驗證成功性
            pre_process_success = self._evaluate_pre_process_success(validation_results)
            
            validation_summary = {
                'phase': 'pre_process',
                'start_time': validation_start.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'success': pre_process_success,
                'validation_results': [result.to_dict() for result in validation_results],
                'context': validation_context,
                'recommendations': self._generate_pre_process_recommendations(validation_results)
            }
            
            logger.info(f"✅ 階段一預處理驗證完成: {'成功' if pre_process_success else '失敗'}")
            return validation_summary
            
        except Exception as e:
            logger.error(f"❌ 階段一預處理驗證失敗: {e}")
            error_result = ValidationResult(
                validator_name="Pre_Processing_Validator",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Pre-processing validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Pre-processing validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'pre_processing'}
            )
            
            validation_results.append(error_result)
            return {
                'phase': 'pre_process',
                'start_time': validation_start.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'success': False,
                'validation_results': [result.to_dict() for result in validation_results],
                'context': validation_context,
                'error': str(e)
            }
    
    async def post_process_validation(self, orbital_data: List[Dict[str, Any]], 
                                    processing_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """後處理驗證 - SGP4 軌道計算後檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 更新驗證上下文
            validation_context = self.current_validation_context.copy()
            validation_context.update({
                'phase': 'post_process',
                'output_data_size': len(orbital_data),
                'processing_metrics': processing_metrics,
                'validation_timestamp': validation_start.isoformat()
            })
            
            # 核心學術標準驗證 (Zero Tolerance)
            academic_result = await self._validate_academic_standards(orbital_data, validation_context)
            
            # ECI 座標零值檢測 (OneWeb 問題防護)
            zero_value_result = await self._detect_zero_coordinates(orbital_data, validation_context)
            
            # 軌道物理參數驗證
            physics_result = await self._validate_orbital_physics(orbital_data, validation_context)
            
            # 統計品質分析
            statistical_result = await self._analyze_orbital_statistics(orbital_data, validation_context)
            
            # 時間基準合規性檢查
            time_compliance_result = await self._validate_time_compliance(
                orbital_data, processing_metrics, validation_context
            )
            
            # 綜合所有驗證結果
            validation_results = [
                academic_result,
                zero_value_result, 
                physics_result,
                statistical_result,
                time_compliance_result
            ]
            
            # 品質門禁檢查
            gate_result = await self.gatekeeper.evaluate_stage_gate(
                'stage1_orbital_calculation', 
                {'validation_results': [result.to_dict() for result in validation_results]},
                orbital_data
            )
            
            # 確定後處理驗證狀態
            post_process_success = self._evaluate_post_process_success(validation_results, gate_result)
            
            # 創建執行快照
            snapshot = await self._create_stage1_snapshot(
                validation_results, processing_metrics, validation_context
            )
            
            validation_summary = {
                'phase': 'post_process',
                'start_time': validation_start.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'success': post_process_success,
                'validation_results': [result.to_dict() for result in validation_results],
                'quality_gate': gate_result,
                'snapshot': {'snapshot_id': snapshot.snapshot_id, 'timestamp': snapshot.timestamp.isoformat(), 'stage_id': snapshot.stage_id, 'execution_status': snapshot.execution_status.value} if snapshot else None,
                'context': validation_context,
                'academic_compliance': self._assess_academic_compliance(validation_results),
                'recommendations': self._generate_post_process_recommendations(validation_results)
            }
            
            # 記錄驗證歷史
            self.validation_history.append(validation_summary)
            
            # 如果品質門禁阻斷，拋出錯誤
            if gate_result.get('status') == 'CLOSED':
                blocking_reasons = [rule['rule_name'] for rule in gate_result.get('blocking_rules', [])]
                raise ValidationError(f"Quality gate blocked: {blocking_reasons}")
            
            return validation_summary
            
        except Exception as e:
            error_summary = {
                'phase': 'post_process',
                'start_time': validation_start.isoformat(),
                'end_time': datetime.now(timezone.utc).isoformat(),
                'success': False,
                'error': str(e),
                'context': validation_context
            }
            self.validation_history.append(error_summary)
            return error_summary
    
    async def _validate_tle_structure(self, tle_data: List[Dict], context: Dict) -> ValidationResult:
        """TLE 數據結構驗證"""
        try:
            # 準備結構驗證數據
            if not tle_data:
                return ValidationResult(
                    validator_name="TLE_Structure_Validator",
                    status=ValidationStatus.FAILED,
                    level=ValidationLevel.CRITICAL,
                    message="No TLE data provided",
                    details={
                        'data_count': 0,
                        'validation_errors': ["Empty TLE dataset"],
                        'validation_warnings': []
                    },
                    metadata={'validation_type': 'tle_structure'}
                )
            
            # 使用數據結構驗證器
            sample_tle = tle_data[0]  # 檢查第一個樣本
            context['data_type'] = 'tle_data_structure'
            
            return await self.structure_validator.validate(sample_tle, context)
            
        except Exception as e:
            return ValidationResult(
                validator_name="TLE_Structure_Validator",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"TLE structure validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Structure validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'tle_structure'}
            )
    
    async def _validate_tle_completeness(self, tle_data: List[Dict], context: Dict) -> ValidationResult:
        """TLE 數據完整性檢查"""
        try:
            missing_fields = []
            invalid_satellites = []
            
            required_fields = ['satellite_name', 'line1', 'line2']
            
            for i, tle in enumerate(tle_data[:100]):  # 檢查前100個
                for field in required_fields:
                    if field not in tle or not tle[field]:
                        missing_fields.append(f"Satellite {i}: missing {field}")
                
                # 檢查 TLE 行格式
                if len(tle.get('line1', '')) != 69:
                    invalid_satellites.append(f"Satellite {i}: invalid line1 length")
                if len(tle.get('line2', '')) != 69:
                    invalid_satellites.append(f"Satellite {i}: invalid line2 length")
            
            completeness_errors = missing_fields + invalid_satellites
            is_complete = len(completeness_errors) == 0
            
            return ValidationResult(
                validator_name="TLE_Completeness_Validator",
                status=ValidationStatus.PASSED if is_complete else ValidationStatus.FAILED,
                level=ValidationLevel.INFO if is_complete else ValidationLevel.CRITICAL,
                message=f"TLE completeness check {'passed' if is_complete else 'failed'}",
                details={
                    'total_satellites': len(tle_data),
                    'checked_satellites': min(100, len(tle_data)),
                    'completeness_issues': len(completeness_errors),
                    'validation_errors': completeness_errors,
                    'validation_warnings': []
                },
                metadata={'validation_type': 'tle_completeness'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name="TLE_Completeness_Validator",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"TLE completeness validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Completeness validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'tle_completeness'}
            )
    
    async def _pre_validate_time_base(self, tle_data: List[Dict], context: Dict) -> ValidationResult:
        """預檢查時間基準設定"""
        try:
            # 檢查 TLE epoch 時間
            epoch_issues = []
            current_time = datetime.now(timezone.utc)
            
            for i, tle in enumerate(tle_data[:50]):  # 檢查前50個
                try:
                    # 這裡應該解析 TLE epoch，簡化實現
                    epoch_year = int(tle.get('line1', '')[18:20])
                    epoch_day = float(tle.get('line1', '')[20:32])
                    
                    # 檢查 epoch 年份合理性
                    full_year = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
                    if not (2020 <= full_year <= current_time.year + 1):
                        epoch_issues.append(f"Satellite {i}: invalid epoch year {full_year}")
                    
                    # 檢查 epoch 天數合理性
                    if not (1 <= epoch_day <= 366):
                        epoch_issues.append(f"Satellite {i}: invalid epoch day {epoch_day}")
                        
                except Exception as e:
                    epoch_issues.append(f"Satellite {i}: epoch parsing error - {str(e)}")
            
            time_base_valid = len(epoch_issues) == 0
            
            return ValidationResult(
                validator_name="Time_Base_Pre_Validator",
                status=ValidationStatus.PASSED if time_base_valid else ValidationStatus.FAILED,
                level=ValidationLevel.INFO if time_base_valid else ValidationLevel.CRITICAL,
                message=f"Time base pre-validation {'passed' if time_base_valid else 'failed'}",
                details={
                    'checked_satellites': min(50, len(tle_data)),
                    'epoch_issues': len(epoch_issues),
                    'validation_errors': epoch_issues,
                    'validation_warnings': []
                },
                metadata={'validation_type': 'time_base_pre_check'}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name="Time_Base_Pre_Validator",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Time base pre-validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Time base pre-validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'time_base_pre_check'}
            )
    
    async def _validate_academic_standards(self, orbital_data: List[Dict], context: Dict) -> ValidationResult:
        """學術標準驗證 (Zero Tolerance)"""
        try:
            # 準備學術標準檢查數據
            academic_data = {
                'orbital_data': orbital_data,
                'metadata': context,
                'grade_level': 'A'  # Stage 1 要求 Grade A 標準
            }
            
            return await self.grade_a_validator.validate(academic_data, context)
            
        except Exception as e:
            return ValidationResult(
                validator_name="Academic_Standards_Validator",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Academic standards validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Academic validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'academic_standards'}
            )
    
    async def _detect_zero_coordinates(self, orbital_data: List[Dict], context: Dict) -> ValidationResult:
        """ECI 座標零值檢測 (OneWeb 問題專門防護)"""
        try:
            # 提取 ECI 座標數據
            eci_coordinates = []
            for data_point in orbital_data:
                if 'satellite_positions' in data_point:
                    for position in data_point['satellite_positions']:
                        if all(coord in position for coord in ['x', 'y', 'z']):
                            eci_coordinates.append({
                                'x': position['x'],
                                'y': position['y'],
                                'z': position['z'],
                                'satellite_id': position.get('satellite_id', 'unknown'),
                                'timestamp': position.get('timestamp', 'unknown')
                            })
            
            # 使用專門的零值檢測器
            zero_detection_data = {'eci_coordinates': eci_coordinates}
            return await self.zero_value_detector.validate(zero_detection_data, context)
            
        except Exception as e:
            return ValidationResult(
                validator_name="Zero_Value_Detector",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Zero value detection error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Zero value detection failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'zero_value_detection'}
            )
    
    async def _validate_orbital_physics(self, orbital_data: List[Dict], context: Dict) -> ValidationResult:
        """軌道物理參數驗證"""
        try:
            # 準備物理參數數據
            physics_data = {
                'orbital_data': orbital_data,
                'context': context
            }
            
            return await self.physics_validator.validate(physics_data, context)
            
        except Exception as e:
            return ValidationResult(
                validator_name="Physics_Parameter_Validator",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Physics validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Physics validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'orbital_physics'}
            )
    
    async def _analyze_orbital_statistics(self, orbital_data: List[Dict], context: Dict) -> ValidationResult:
        """軌道數據統計分析"""
        try:
            # 使用統計分析器
            return await self.statistical_analyzer.validate(orbital_data, context)
            
        except Exception as e:
            return ValidationResult(
                validator_name="Statistical_Analyzer",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Statistical analysis error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Statistical analysis failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'statistical_analysis'}
            )
    
    async def _validate_time_compliance(self, orbital_data: List[Dict], 
                                      processing_metrics: Dict, context: Dict) -> ValidationResult:
        """時間基準合規性檢查"""
        try:
            # 準備時間合規檢查數據
            time_data = {
                'orbital_data': orbital_data,
                'processing_metadata': processing_metrics,
                'context': context
            }
            
            return await self.time_base_checker.validate(time_data, context)
            
        except Exception as e:
            return ValidationResult(
                validator_name="Time_Base_Compliance_Checker",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Time compliance validation error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Time compliance validation failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'validation_type': 'time_compliance'}
            )
    
    def _evaluate_post_process_success(self, validation_results: List[ValidationResult], 
                                     gate_result: Dict[str, Any]) -> bool:
        """評估後處理驗證是否成功"""
        # 檢查是否有驗證失敗或錯誤
        has_failures = any(result.status in [ValidationStatus.FAILED, ValidationStatus.ERROR] 
                          for result in validation_results)
        
        # 檢查品質門禁是否阻斷
        gate_blocked = gate_result.get('status') == 'CLOSED'
        
        return not (has_failures or gate_blocked)
    
    async def _create_stage1_snapshot(self, validation_results: List[ValidationResult],
                                    processing_metrics: Dict, context: Dict) -> Optional[Any]:
        """創建 Stage 1 執行快照"""
        try:
            from validation.engines.execution_control_engine import ExecutionSnapshot, ExecutionStatus
            
            # 確定執行狀態
            has_errors = any(result.status == ValidationStatus.ERROR for result in validation_results)
            has_failures = any(result.status == ValidationStatus.FAILED for result in validation_results)
            
            if has_errors:
                execution_status = ExecutionStatus.FAILED
            elif has_failures:
                execution_status = ExecutionStatus.FAILED
            else:
                execution_status = ExecutionStatus.COMPLETED
            
            # 計算品質指標
            quality_metrics = self._calculate_stage1_quality_metrics(validation_results)
            
            # 創建錯誤摘要
            error_summary = self._create_stage1_error_summary(validation_results)
            
            snapshot = ExecutionSnapshot(
                snapshot_id=f"stage1_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(timezone.utc),
                stage_id='stage1_orbital_calculation',
                execution_status=execution_status,
                validation_results=validation_results,
                quality_metrics=quality_metrics,
                error_summary=error_summary,
                recovery_actions=[],
                metadata={
                    'processing_metrics': processing_metrics,
                    'validation_context': context,
                    'stage_specific_info': {
                        'tle_processing': True,
                        'sgp4_calculation': True,
                        'eci_coordinate_generation': True
                    }
                }
            )
            
            # 保存快照
            await self.snapshot_manager.save_snapshot(snapshot)
            return snapshot
            
        except Exception as e:
            # 如果快照創建失敗，記錄但不阻斷流程
            print(f"Warning: Failed to create Stage 1 snapshot: {str(e)}")
            return None
    
    def _calculate_stage1_quality_metrics(self, validation_results: List[ValidationResult]) -> Dict[str, float]:
        """計算 Stage 1 特定品質指標"""
        if not validation_results:
            return {}
        
        total_validations = len(validation_results)
        passed_count = sum(1 for result in validation_results if result.status == ValidationStatus.PASSED)
        failed_count = sum(1 for result in validation_results if result.status == ValidationStatus.FAILED)
        error_count = sum(1 for result in validation_results if result.status == ValidationStatus.ERROR)
        
        return {
            'success_rate': (passed_count / total_validations) * 100,
            'failure_rate': (failed_count / total_validations) * 100,
            'error_rate': (error_count / total_validations) * 100,
            'total_validations': total_validations,
            'stage1_quality_score': max(0, 100 - (failed_count * 20) - (error_count * 30)),
            'orbital_calculation_reliability': (passed_count / total_validations) * 100,
            'academic_compliance_rate': 100.0 if failed_count == 0 else 0.0
        }
    
    def _create_stage1_error_summary(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """創建 Stage 1 特定錯誤摘要"""
        all_errors = []
        all_warnings = []
        
        for result in validation_results:
            # ValidationResult將errors和warnings存儲在details中
            details = result.details or {}
            all_errors.extend(details.get('validation_errors', []))
            all_warnings.extend(details.get('validation_warnings', []))
        
        # Stage 1 特定錯誤分類
        error_categories = {
            'eci_zero_value_errors': [e for e in all_errors if 'zero' in e.lower() or 'eci' in e.lower()],
            'tle_format_errors': [e for e in all_errors if 'tle' in e.lower() or 'format' in e.lower()],
            'time_base_errors': [e for e in all_errors if 'time' in e.lower() or 'epoch' in e.lower()],
            'physics_violations': [e for e in all_errors if 'physics' in e.lower() or 'orbital' in e.lower()],
            'academic_violations': [e for e in all_errors if 'academic' in e.lower() or 'grade' in e.lower()],
            'other_errors': []
        }
        
        # 分類剩餘錯誤
        categorized_errors = set()
        for category_errors in error_categories.values():
            categorized_errors.update(category_errors)
        
        error_categories['other_errors'] = [e for e in all_errors if e not in categorized_errors]
        
        return {
            'total_errors': len(all_errors),
            'total_warnings': len(all_warnings),
            'error_categories': error_categories,
            'critical_errors': error_categories['eci_zero_value_errors'] + error_categories['academic_violations'],
            'stage1_specific_issues': {
                'oneWeb_protection_status': 'active' if error_categories['eci_zero_value_errors'] else 'passed',
                'tle_data_quality': 'degraded' if error_categories['tle_format_errors'] else 'good',
                'time_base_compliance': 'violated' if error_categories['time_base_errors'] else 'compliant'
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _assess_academic_compliance(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """評估學術合規性"""
        academic_errors = []
        for result in validation_results:
            if result.validator_name in ['Academic_Standards_Validator', 'Grade_A_Data_Validator']:
                details = result.details or {}
                academic_errors.extend(details.get('validation_errors', []))
        
        return {
            'grade_level': 'A',
            'compliant': len(academic_errors) == 0,
            'violations': academic_errors,
            'violation_count': len(academic_errors),
            'compliance_score': 100.0 if len(academic_errors) == 0 else 0.0,
            'assessment_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _generate_pre_process_recommendations(self, validation_results: List[ValidationResult]) -> List[str]:
        """生成預處理建議"""
        recommendations = []
        
        for result in validation_results:
            if result.status == ValidationStatus.FAILED:
                if 'structure' in result.validator_name.lower():
                    recommendations.append("檢查 TLE 數據格式，確保符合標準 69 字元格式")
                elif 'completeness' in result.validator_name.lower():
                    recommendations.append("驗證 TLE 數據完整性，確保所有必要欄位都存在")
                elif 'time' in result.validator_name.lower():
                    recommendations.append("檢查 TLE epoch 時間，確保在合理的時間範圍內")
        
        if not recommendations:
            recommendations.append("預處理驗證通過，可繼續進行軌道計算")
        
        return recommendations
    
    def _generate_post_process_recommendations(self, validation_results: List[ValidationResult]) -> List[str]:
        """生成後處理建議"""
        recommendations = []
        
        for result in validation_results:
            if result.status == ValidationStatus.FAILED:
                if 'zero' in result.validator_name.lower():
                    recommendations.append("發現 ECI 座標零值問題，建議檢查 SGP4 計算邏輯和 TLE 數據完整性")
                elif 'academic' in result.validator_name.lower():
                    recommendations.append("學術標準違規，必須修復後才能進入下一階段處理")
                elif 'physics' in result.validator_name.lower():
                    recommendations.append("軌道物理參數驗證失敗，檢查軌道高度、傾角、周期等參數")
                elif 'time' in result.validator_name.lower():
                    recommendations.append("時間基準違規，確保使用 TLE epoch 時間而非當前時間")
        
        if not recommendations:
            recommendations.append("後處理驗證通過，數據品質符合學術標準，可進入下一階段")
        
        return recommendations
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """獲取驗證摘要報告"""
        if not self.validation_history:
            return {'message': 'No validation history available'}
        
        latest_validation = self.validation_history[-1]
        
        return {
            'stage': 'stage1_orbital_calculation',
            'total_validations': len(self.validation_history),
            'latest_validation': latest_validation,
            'success_rate': sum(1 for v in self.validation_history if v.get('success', False)) / len(self.validation_history) * 100,
            'common_issues': self._identify_common_issues(),
            'academic_compliance_status': latest_validation.get('academic_compliance', {}),
            'summary_generated': datetime.now(timezone.utc).isoformat()
        }
    
    def _identify_common_issues(self) -> List[str]:
        """識別常見問題模式"""
        all_errors = []
        for validation in self.validation_history:
            for result in validation.get('validation_results', []):
                if isinstance(result, dict):
                    all_errors.extend(result.get('validation_errors', []))
        
        # 統計錯誤頻率
        error_counts = {}
        for error in all_errors:
            error_type = self._classify_error_type(error)
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # 返回最常見的問題
        common_issues = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return [issue[0] for issue in common_issues]
    
    def _classify_error_type(self, error: str) -> str:
        """分類錯誤類型"""
        error_lower = error.lower()
        if 'zero' in error_lower or 'eci' in error_lower:
            return 'ECI零值問題'
        elif 'tle' in error_lower:
            return 'TLE數據問題'
        elif 'time' in error_lower or 'epoch' in error_lower:
            return '時間基準問題'
        elif 'academic' in error_lower:
            return '學術標準違規'
        elif 'physics' in error_lower:
            return '物理參數問題'
        else:
            return '其他問題'


# 為了避免循環導入，在這裡定義一個簡化的驗證錯誤類
class ValidationError(Exception):
    """驗證錯誤異常"""
    pass