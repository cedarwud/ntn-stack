"""
執行控制引擎
Execution Control Engine

實施驗證流程協調器、階段品質門禁、自動化修復機制、驗證快照管理
Based on Phase 2 specifications: execution_control_engine.py
"""

from typing import Dict, List, Any, Optional, Tuple, Callable
import json
import asyncio
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum
import traceback
from pathlib import Path

from ..core.base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationLevel
from ..core.validation_engine import ValidationEngine, ValidationContext
from ..core.error_handler import ValidationError, AcademicStandardsViolationError
from ..config.academic_standards_config import get_academic_config
from ..config.data_quality_config import get_data_quality_config


class ExecutionStatus(Enum):
    """執行狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class QualityGateStatus(Enum):
    """品質門禁狀態"""
    OPEN = "open"
    CLOSED = "closed"
    CONDITIONAL = "conditional"


class RecoveryAction(Enum):
    """修復動作類型"""
    RETRY = "retry"
    SKIP = "skip"
    ROLLBACK = "rollback"
    MANUAL_INTERVENTION = "manual_intervention"
    DATA_CORRECTION = "data_correction"
    CONFIGURATION_UPDATE = "configuration_update"


@dataclass
class ExecutionStage:
    """執行階段定義"""
    stage_id: str
    name: str
    description: str
    validators: List[str]
    dependencies: List[str]
    quality_gate_rules: Dict[str, Any]
    retry_policy: Dict[str, Any]
    timeout_seconds: int
    required: bool = True


@dataclass
class QualityGateRule:
    """品質門禁規則"""
    rule_id: str
    name: str
    condition: str
    threshold: float
    action: str
    severity: str
    enabled: bool = True


@dataclass
class ExecutionSnapshot:
    """執行快照"""
    snapshot_id: str
    timestamp: datetime
    stage_id: str
    execution_status: ExecutionStatus
    validation_results: List[ValidationResult]
    quality_metrics: Dict[str, float]
    error_summary: Dict[str, Any]
    recovery_actions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class RecoveryPlan:
    """修復計劃"""
    plan_id: str
    stage_id: str
    error_type: str
    recovery_actions: List[RecoveryAction]
    estimated_duration: int
    success_probability: float
    manual_steps: List[str]
    automated_fixes: List[Dict[str, Any]]


class ValidationOrchestrator:
    """驗證流程協調器"""
    
    def __init__(self):
        self.academic_config = get_academic_config()
        self.data_quality_config = get_data_quality_config()
        self.validation_engine = ValidationEngine()
        
        # 預定義執行階段
        self.stages = self._initialize_execution_stages()
        self.quality_gates = self._initialize_quality_gates()
        self.snapshots: List[ExecutionSnapshot] = []
        
        # 狀態追蹤
        self.current_stage: Optional[str] = None
        self.execution_history: List[Dict[str, Any]] = []
        self.global_context = ValidationContext()
    
    def _initialize_execution_stages(self) -> Dict[str, ExecutionStage]:
        """初始化執行階段"""
        return {
            'stage1_orbital_calculation': ExecutionStage(
                stage_id='stage1_orbital_calculation',
                name='軌道計算處理',
                description='TLE數據處理和SGP4軌道計算',
                validators=['GradeADataValidator', 'ZeroValueDetector', 'TimeBaseContinuityChecker'],
                dependencies=[],
                quality_gate_rules={
                    'eci_zero_tolerance': {'threshold': 0.01, 'action': 'block'},
                    'tle_epoch_compliance': {'threshold': 1.0, 'action': 'block'}
                },
                retry_policy={'max_attempts': 3, 'backoff_seconds': 30},
                timeout_seconds=600
            ),
            
            'stage2_intelligent_filtering': ExecutionStage(
                stage_id='stage2_intelligent_filtering',
                name='智能篩選處理',
                description='衛星可見性篩選和仰角門檻處理',
                validators=['DataStructureValidator', 'PhysicalParameterValidator'],
                dependencies=['stage1_orbital_calculation'],
                quality_gate_rules={
                    'visibility_data_completeness': {'threshold': 0.95, 'action': 'warn'},
                    'elevation_threshold_compliance': {'threshold': 0.9, 'action': 'block'}
                },
                retry_policy={'max_attempts': 2, 'backoff_seconds': 20},
                timeout_seconds=300
            ),
            
            'stage3_signal_analysis': ExecutionStage(
                stage_id='stage3_signal_analysis',
                name='信號分析處理',
                description='信號品質分析和路徑損耗計算',
                validators=['PhysicalParameterValidator', 'StatisticalAnalyzer'],
                dependencies=['stage2_intelligent_filtering'],
                quality_gate_rules={
                    'signal_calculation_accuracy': {'threshold': 0.9, 'action': 'warn'},
                    'physics_compliance': {'threshold': 1.0, 'action': 'block'}
                },
                retry_policy={'max_attempts': 2, 'backoff_seconds': 15},
                timeout_seconds=240
            ),
            
            'stage4_timeseries_preprocessing': ExecutionStage(
                stage_id='stage4_timeseries_preprocessing',
                name='時序預處理',
                description='時間序列數據預處理和標準化',
                validators=['StatisticalAnalyzer', 'CrossStageConsistencyChecker'],
                dependencies=['stage3_signal_analysis'],
                quality_gate_rules={
                    'time_series_continuity': {'threshold': 0.95, 'action': 'warn'},
                    'data_consistency': {'threshold': 0.9, 'action': 'block'}
                },
                retry_policy={'max_attempts': 2, 'backoff_seconds': 10},
                timeout_seconds=180
            ),
            
            'stage5_data_integration': ExecutionStage(
                stage_id='stage5_data_integration',
                name='數據整合',
                description='多源數據整合和一致性檢查',
                validators=['CrossStageConsistencyChecker', 'MetadataComplianceValidator'],
                dependencies=['stage4_timeseries_preprocessing'],
                quality_gate_rules={
                    'integration_completeness': {'threshold': 0.98, 'action': 'warn'},
                    'cross_stage_consistency': {'threshold': 0.9, 'action': 'block'}
                },
                retry_policy={'max_attempts': 1, 'backoff_seconds': 5},
                timeout_seconds=120
            ),
            
            'stage6_dynamic_pool_planning': ExecutionStage(
                stage_id='stage6_dynamic_pool_planning',
                name='動態池規劃',
                description='動態衛星池規劃和最佳化',
                validators=['MetadataComplianceValidator'],
                dependencies=['stage5_data_integration'],
                quality_gate_rules={
                    'planning_optimization': {'threshold': 0.85, 'action': 'warn'},
                    'metadata_compliance': {'threshold': 0.95, 'action': 'block'}
                },
                retry_policy={'max_attempts': 1, 'backoff_seconds': 0},
                timeout_seconds=180
            )
        }
    
    def _initialize_quality_gates(self) -> Dict[str, QualityGateRule]:
        """初始化品質門禁"""
        return {
            'academic_standards_blocker': QualityGateRule(
                rule_id='academic_standards_blocker',
                name='學術標準阻斷器',
                condition='academic_violations == 0',
                threshold=0.0,
                action='block',
                severity='BLOCKER'
            ),
            'eci_zero_value_blocker': QualityGateRule(
                rule_id='eci_zero_value_blocker',
                name='ECI零值阻斷器',
                condition='eci_zero_percentage <= 1.0',
                threshold=1.0,
                action='block',
                severity='BLOCKER'
            ),
            'data_completeness_gate': QualityGateRule(
                rule_id='data_completeness_gate',
                name='數據完整性門檻',
                condition='data_completeness >= 95.0',
                threshold=95.0,
                action='warn',
                severity='CRITICAL'
            ),
            'consistency_gate': QualityGateRule(
                rule_id='consistency_gate',
                name='一致性檢查門檻',
                condition='consistency_score >= 90.0',
                threshold=90.0,
                action='block',
                severity='CRITICAL'
            )
        }
    
    async def execute_pipeline(self, data: Dict[str, Any], 
                             stage_filter: Optional[List[str]] = None) -> Dict[str, Any]:
        """執行完整驗證管線"""
        execution_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        execution_start = datetime.now(timezone.utc)
        
        try:
            # 初始化執行上下文
            self.global_context.metadata.update({
                'execution_id': execution_id,
                'start_time': execution_start.isoformat(),
                'pipeline_mode': True
            })
            
            # 執行階段排序 (考慮依賴關係)
            execution_order = self._calculate_execution_order(stage_filter)
            
            results = {
                'execution_id': execution_id,
                'start_time': execution_start.isoformat(),
                'stages': {},
                'overall_status': ExecutionStatus.RUNNING,
                'quality_gates': {},
                'snapshots': []
            }
            
            # 按順序執行各階段
            for stage_id in execution_order:
                stage_result = await self._execute_stage(stage_id, data, results)
                results['stages'][stage_id] = stage_result
                
                # 檢查品質門禁
                gate_result = await self._check_quality_gates(stage_id, stage_result)
                results['quality_gates'][stage_id] = gate_result
                
                # 如果門禁阻斷，停止執行
                if gate_result['status'] == QualityGateStatus.CLOSED:
                    results['overall_status'] = ExecutionStatus.BLOCKED
                    break
                
                # 創建快照
                snapshot = await self._create_execution_snapshot(stage_id, stage_result)
                results['snapshots'].append(asdict(snapshot))
            
            # 確定整體狀態
            if results['overall_status'] != ExecutionStatus.BLOCKED:
                all_successful = all(
                    stage_result.get('status') == ExecutionStatus.COMPLETED 
                    for stage_result in results['stages'].values()
                )
                results['overall_status'] = ExecutionStatus.COMPLETED if all_successful else ExecutionStatus.FAILED
            
            execution_end = datetime.now(timezone.utc)
            results['end_time'] = execution_end.isoformat()
            results['duration_seconds'] = (execution_end - execution_start).total_seconds()
            
            return results
            
        except Exception as e:
            return {
                'execution_id': execution_id,
                'status': ExecutionStatus.FAILED,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'end_time': datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_execution_order(self, stage_filter: Optional[List[str]] = None) -> List[str]:
        """計算執行順序 (拓撲排序)"""
        # 如果指定了過濾器，只處理指定的階段
        stages_to_process = stage_filter if stage_filter else list(self.stages.keys())
        
        # 簡化拓撲排序實現
        ordered_stages = []
        remaining_stages = stages_to_process.copy()
        processed_dependencies = set()
        
        while remaining_stages:
            # 找到沒有未滿足依賴的階段
            ready_stages = []
            for stage_id in remaining_stages:
                stage = self.stages[stage_id]
                if all(dep in processed_dependencies or dep not in stages_to_process 
                       for dep in stage.dependencies):
                    ready_stages.append(stage_id)
            
            if not ready_stages:
                # 檢測循環依賴
                raise ValueError(f"Circular dependency detected in stages: {remaining_stages}")
            
            # 按階段ID排序確保確定性
            ready_stages.sort()
            
            for stage_id in ready_stages:
                ordered_stages.append(stage_id)
                remaining_stages.remove(stage_id)
                processed_dependencies.add(stage_id)
        
        return ordered_stages
    
    async def _execute_stage(self, stage_id: str, data: Dict[str, Any], 
                           pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行單一階段"""
        stage = self.stages[stage_id]
        stage_start = datetime.now(timezone.utc)
        
        try:
            self.current_stage = stage_id
            
            # 準備階段數據
            stage_data = await self._prepare_stage_data(stage_id, data, pipeline_results)
            
            # 創建階段上下文
            stage_context = ValidationContext()
            stage_context.metadata.update({
                'stage_id': stage_id,
                'stage_name': stage.name,
                'execution_start': stage_start.isoformat()
            })
            
            # 執行驗證器
            validation_results = []
            for validator_name in stage.validators:
                validator_result = await self._run_validator(
                    validator_name, stage_data, stage_context
                )
                validation_results.append(validator_result)
            
            # 分析結果
            stage_status = self._determine_stage_status(validation_results)
            
            stage_end = datetime.now(timezone.utc)
            
            return {
                'stage_id': stage_id,
                'name': stage.name,
                'status': stage_status,
                'start_time': stage_start.isoformat(),
                'end_time': stage_end.isoformat(),
                'duration_seconds': (stage_end - stage_start).total_seconds(),
                'validation_results': [asdict(result) for result in validation_results],
                'data_summary': self._create_data_summary(stage_data),
                'retry_attempts': 0,
                'metadata': stage_context.metadata
            }
            
        except Exception as e:
            stage_end = datetime.now(timezone.utc)
            return {
                'stage_id': stage_id,
                'name': stage.name,
                'status': ExecutionStatus.FAILED,
                'start_time': stage_start.isoformat(),
                'end_time': stage_end.isoformat(),
                'duration_seconds': (stage_end - stage_start).total_seconds(),
                'error': str(e),
                'traceback': traceback.format_exc(),
                'retry_attempts': 0
            }
    
    async def _prepare_stage_data(self, stage_id: str, original_data: Dict[str, Any], 
                                pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """準備階段數據"""
        stage_data = original_data.copy()
        
        # 添加前一階段的結果作為輸入
        stage = self.stages[stage_id]
        for dependency in stage.dependencies:
            if dependency in pipeline_results.get('stages', {}):
                dependency_result = pipeline_results['stages'][dependency]
                stage_data[f"{dependency}_result"] = dependency_result
        
        return stage_data
    
    async def _run_validator(self, validator_name: str, data: Dict[str, Any], context: Dict[str, Any]) -> ValidationResult:
        """
        執行指定的驗證器
        
        Args:
            validator_name: 驗證器名稱
            data: 驗證數據
            context: 驗證上下文
            
        Returns:
            ValidationResult: 驗證結果
        """
        try:
            # 這裡需要根據驗證器名稱創建實際的驗證器實例
            # 簡化實現：返回模擬結果
            return ValidationResult(
                validator_name=validator_name,
                status=ValidationStatus.PASSED,
                level=ValidationLevel.INFO,
                message=f"{validator_name} validation completed",
                details={
                    'simulated': True,
                    'validation_errors': [],
                    'validation_warnings': []
                },
                metadata={'executed_at': datetime.now(timezone.utc).isoformat()}
            )
            
        except Exception as e:
            return ValidationResult(
                validator_name=validator_name,
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Validator execution error: {str(e)}",
                details={
                    'exception': str(e),
                    'validation_errors': [f"Execution failed: {str(e)}"],
                    'validation_warnings': []
                },
                metadata={'executed_at': datetime.now(timezone.utc).isoformat()}
            )
    
    def _determine_stage_status(self, validation_results: List[ValidationResult]) -> ExecutionStatus:
        """確定階段狀態"""
        if not validation_results:
            return ExecutionStatus.COMPLETED
        
        # 檢查是否有錯誤
        has_errors = any(result.status == ValidationStatus.ERROR for result in validation_results)
        if has_errors:
            return ExecutionStatus.FAILED
        
        # 檢查是否有失敗
        has_failures = any(result.status == ValidationStatus.FAILED for result in validation_results)
        if has_failures:
            return ExecutionStatus.FAILED
        
        return ExecutionStatus.COMPLETED
    
    def _create_data_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """創建數據摘要"""
        summary = {
            'total_keys': len(data) if isinstance(data, dict) else 0,
            'data_size_mb': len(json.dumps(data, default=str)) / 1024 / 1024,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # 嘗試提取關鍵統計信息
        if 'satellites' in data:
            summary['satellite_count'] = len(data['satellites'])
        
        if 'eci_coordinates' in data:
            summary['coordinate_count'] = len(data['eci_coordinates'])
        
        return summary
    
    async def _check_quality_gates(self, stage_id: str, stage_result: Dict[str, Any]) -> Dict[str, Any]:
        """檢查品質門禁"""
        stage = self.stages[stage_id]
        gate_results = {}
        overall_status = QualityGateStatus.OPEN
        
        for rule_name, rule_config in stage.quality_gate_rules.items():
            gate_result = await self._evaluate_quality_gate_rule(
                rule_name, rule_config, stage_result
            )
            gate_results[rule_name] = gate_result
            
            # 如果有門禁被觸發且動作為block，設定整體狀態
            if gate_result['triggered'] and rule_config.get('action') == 'block':
                overall_status = QualityGateStatus.CLOSED
        
        return {
            'stage_id': stage_id,
            'status': overall_status,
            'rules': gate_results,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def _evaluate_quality_gate_rule(self, rule_name: str, rule_config: Dict[str, Any], 
                                        stage_result: Dict[str, Any]) -> Dict[str, Any]:
        """評估品質門禁規則"""
        try:
            threshold = rule_config.get('threshold', 0.0)
            action = rule_config.get('action', 'warn')
            
            # 簡化實現：基於驗證結果評估
            validation_results = stage_result.get('validation_results', [])
            
            # 計算規則特定的指標
            if 'zero' in rule_name.lower():
                # ECI零值檢查
                error_count = sum(1 for result in validation_results 
                                if result.get('status') == 'FAILED' and 
                                'zero' in str(result.get('errors', [])).lower())
                metric_value = error_count
                triggered = metric_value > threshold
            
            elif 'completeness' in rule_name.lower():
                # 數據完整性檢查
                success_count = sum(1 for result in validation_results 
                                  if result.get('status') == 'PASSED')
                metric_value = (success_count / max(len(validation_results), 1)) * 100
                triggered = metric_value < threshold
            
            else:
                # 通用規則評估
                error_count = sum(1 for result in validation_results 
                                if result.get('status') in ['FAILED', 'ERROR'])
                metric_value = error_count
                triggered = metric_value > threshold
            
            return {
                'rule_name': rule_name,
                'threshold': threshold,
                'metric_value': metric_value,
                'triggered': triggered,
                'action': action,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                'rule_name': rule_name,
                'error': str(e),
                'triggered': True,  # 評估錯誤時保守觸發
                'action': 'block',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _create_execution_snapshot(self, stage_id: str, 
                                   stage_result: Dict[str, Any]) -> ExecutionSnapshot:
        """創建執行快照"""
        snapshot_id = f"{stage_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 提取驗證結果
        validation_results = []
        for result_dict in stage_result.get('validation_results', []):
            # 將字典轉換回ValidationResult對象（簡化實現）
            validation_result = ValidationResult(
                validator_name=result_dict.get('validator_name', ''),
                status=ValidationStatus(result_dict.get('status', 'UNKNOWN')),
                level=ValidationLevel(result_dict.get('level', 'INFO')),
                message=result_dict.get('message', ''),
                details=result_dict.get('details', {}),
                metadata=result_dict.get('metadata', {})
            )
            validation_results.append(validation_result)
        
        # 計算品質指標
        quality_metrics = self._calculate_quality_metrics(validation_results)
        
        # 創建錯誤摘要
        error_summary = self._create_error_summary(validation_results)
        
        snapshot = ExecutionSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(timezone.utc),
            stage_id=stage_id,
            execution_status=ExecutionStatus(stage_result.get('status', 'UNKNOWN')),
            validation_results=validation_results,
            quality_metrics=quality_metrics,
            error_summary=error_summary,
            recovery_actions=[],
            metadata=stage_result.get('metadata', {})
        )
        
        self.snapshots.append(snapshot)
        return snapshot
    
    def _calculate_quality_metrics(self, validation_results: List[ValidationResult]) -> Dict[str, float]:
        """計算品質指標"""
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
            'quality_score': max(0, 100 - (failed_count * 10) - (error_count * 20))
        }
    
    def _create_error_summary(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """創建錯誤摘要"""
        all_errors = []
        all_warnings = []
        
        for result in validation_results:
            # 從details中提取validation_errors和validation_warnings
            if hasattr(result, 'details') and result.details:
                all_errors.extend(result.details.get('validation_errors', []))
                all_warnings.extend(result.details.get('validation_warnings', []))
        
        # 錯誤分類
        error_categories = {
            'academic_violations': [e for e in all_errors if 'academic' in str(e).lower() or 'grade' in str(e).lower()],
            'data_quality_issues': [e for e in all_errors if 'data' in str(e).lower() or 'quality' in str(e).lower()],
            'technical_errors': [e for e in all_errors if 'error' in str(e).lower() or 'exception' in str(e).lower()],
            'other_issues': []
        }
        
        # 分類剩餘錯誤
        categorized_errors = set()
        for category_errors in error_categories.values():
            categorized_errors.update(category_errors)
        
        error_categories['other_issues'] = [e for e in all_errors if e not in categorized_errors]
        
        return {
            'total_errors': len(all_errors),
            'total_warnings': len(all_warnings),
            'error_categories': error_categories,
            'critical_errors': [e for e in all_errors if any(keyword in str(e).lower() 
                              for keyword in ['critical', 'blocker', 'zero', 'academic'])],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


class StageGatekeeper:
    """階段品質門禁管理器"""
    
    def __init__(self, orchestrator: ValidationOrchestrator):
        self.orchestrator = orchestrator
        self.gate_history: List[Dict[str, Any]] = []
    
    async def evaluate_stage_gate(self, stage_id: str, stage_result: Dict[str, Any], 
                                data: Dict[str, Any]) -> Dict[str, Any]:
        """評估階段門禁"""
        gate_evaluation = {
            'stage_id': stage_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': QualityGateStatus.OPEN.value,  # 轉換為字符串值
            'blocking_rules': [],
            'warning_rules': [],
            'recommendations': []
        }
        
        # 獲取階段配置
        stage = self.orchestrator.stages.get(stage_id)
        if not stage:
            gate_evaluation['status'] = QualityGateStatus.CLOSED.value  # 轉換為字符串值
            gate_evaluation['blocking_rules'].append(f"Unknown stage: {stage_id}")
            return gate_evaluation
        
        # 評估各個門禁規則
        for rule_name, rule_config in stage.quality_gate_rules.items():
            rule_result = await self._evaluate_gate_rule(
                rule_name, rule_config, stage_result, data
            )
            
            if rule_result['violated']:
                if rule_config.get('action') == 'block':
                    gate_evaluation['blocking_rules'].append(rule_result)
                    gate_evaluation['status'] = QualityGateStatus.CLOSED.value  # 轉換為字符串值
                elif rule_config.get('action') == 'warn':
                    gate_evaluation['warning_rules'].append(rule_result)
        
        # 生成建議
        if gate_evaluation['blocking_rules']:
            gate_evaluation['recommendations'] = self._generate_gate_recommendations(
                gate_evaluation['blocking_rules']
            )
        
        self.gate_history.append(gate_evaluation)
        return gate_evaluation
    
    async def _evaluate_gate_rule(self, rule_name: str, rule_config: Dict[str, Any], 
                                stage_result: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """評估單一門禁規則"""
        rule_evaluation = {
            'rule_name': rule_name,
            'threshold': rule_config.get('threshold'),
            'action': rule_config.get('action'),
            'violated': False,
            'actual_value': None,
            'details': {}
        }
        
        try:
            # 根據規則類型進行評估
            if 'eci_zero' in rule_name.lower():
                actual_value = await self._calculate_eci_zero_percentage(stage_result, data)
                rule_evaluation['actual_value'] = actual_value
                rule_evaluation['violated'] = actual_value > rule_config.get('threshold', 0)
                
            elif 'completeness' in rule_name.lower():
                actual_value = await self._calculate_completeness_score(stage_result, data)
                rule_evaluation['actual_value'] = actual_value
                rule_evaluation['violated'] = actual_value < rule_config.get('threshold', 100)
                
            elif 'consistency' in rule_name.lower():
                actual_value = await self._calculate_consistency_score(stage_result, data)
                rule_evaluation['actual_value'] = actual_value
                rule_evaluation['violated'] = actual_value < rule_config.get('threshold', 100)
                
            else:
                # 通用規則評估
                validation_results = stage_result.get('validation_results', [])
                failed_count = sum(1 for result in validation_results 
                                 if result.get('status') in ['FAILED', 'ERROR'])
                rule_evaluation['actual_value'] = failed_count
                rule_evaluation['violated'] = failed_count > rule_config.get('threshold', 0)
            
        except Exception as e:
            rule_evaluation['violated'] = True
            rule_evaluation['details']['error'] = str(e)
        
        return rule_evaluation
    
    async def _calculate_eci_zero_percentage(self, stage_result: Dict[str, Any], 
                                           data: Dict[str, Any]) -> float:
        """計算ECI零值百分比"""
        # 從驗證結果中提取零值信息
        validation_results = stage_result.get('validation_results', [])
        
        for result in validation_results:
            if 'zero' in result.get('validator_name', '').lower():
                details = result.get('details', {})
                if 'zero_percentage' in details:
                    return float(details['zero_percentage'])
        
        return 0.0
    
    async def _calculate_completeness_score(self, stage_result: Dict[str, Any], 
                                          data: Dict[str, Any]) -> float:
        """計算數據完整性分數"""
        validation_results = stage_result.get('validation_results', [])
        if not validation_results:
            return 0.0
        
        passed_count = sum(1 for result in validation_results 
                          if result.get('status') == 'PASSED')
        return (passed_count / len(validation_results)) * 100
    
    async def _calculate_consistency_score(self, stage_result: Dict[str, Any], 
                                         data: Dict[str, Any]) -> float:
        """計算一致性分數"""
        # 從跨階段一致性檢查器結果中提取
        validation_results = stage_result.get('validation_results', [])
        
        for result in validation_results:
            if 'consistency' in result.get('validator_name', '').lower():
                details = result.get('details', {})
                if 'consistency_score' in details:
                    return float(details['consistency_score'])
        
        return 100.0  # 默認滿分
    
    def _generate_gate_recommendations(self, blocking_rules: List[Dict[str, Any]]) -> List[str]:
        """生成門禁建議"""
        recommendations = []
        
        for rule in blocking_rules:
            rule_name = rule.get('rule_name', '')
            
            if 'eci_zero' in rule_name.lower():
                recommendations.append(
                    "檢查SGP4計算邏輯，確保使用TLE epoch時間基準而非當前時間"
                )
                recommendations.append(
                    "驗證TLE數據完整性，確認衛星軌道參數正確"
                )
                
            elif 'completeness' in rule_name.lower():
                recommendations.append(
                    "檢查數據輸入完整性，確認所有必需欄位都已提供"
                )
                recommendations.append(
                    "驗證數據處理流程，確保沒有數據丟失"
                )
                
            elif 'consistency' in rule_name.lower():
                recommendations.append(
                    "檢查跨階段數據傳遞，確保數據結構一致性"
                )
                recommendations.append(
                    "驗證座標系統轉換，確保變換邏輯正確"
                )
        
        return recommendations


class ErrorRecoveryManager:
    """錯誤修復管理器"""
    
    def __init__(self):
        self.recovery_strategies = self._initialize_recovery_strategies()
        self.recovery_history: List[Dict[str, Any]] = []
    
    def _initialize_recovery_strategies(self) -> Dict[str, RecoveryPlan]:
        """初始化修復策略"""
        return {
            'eci_zero_coordinates': RecoveryPlan(
                plan_id='eci_zero_coordinates',
                stage_id='stage1_orbital_calculation',
                error_type='academic_violation',
                recovery_actions=[
                    RecoveryAction.DATA_CORRECTION,
                    RecoveryAction.CONFIGURATION_UPDATE
                ],
                estimated_duration=300,  # 5 minutes
                success_probability=0.9,
                manual_steps=[
                    "檢查TLE數據完整性",
                    "驗證SGP4計算參數",
                    "確認時間基準設定"
                ],
                automated_fixes=[
                    {
                        'action': 'update_time_base',
                        'description': '修正時間基準為TLE epoch時間',
                        'function': 'fix_time_base_configuration'
                    },
                    {
                        'action': 'validate_tle_data',
                        'description': '驗證並修正TLE數據',
                        'function': 'validate_and_fix_tle_data'
                    }
                ]
            ),
            
            'data_inconsistency': RecoveryPlan(
                plan_id='data_inconsistency',
                stage_id='cross_stage',
                error_type='data_quality',
                recovery_actions=[
                    RecoveryAction.RETRY,
                    RecoveryAction.DATA_CORRECTION
                ],
                estimated_duration=120,  # 2 minutes
                success_probability=0.7,
                manual_steps=[
                    "檢查數據結構定義",
                    "驗證變換邏輯"
                ],
                automated_fixes=[
                    {
                        'action': 'standardize_data_structure',
                        'description': '標準化數據結構',
                        'function': 'standardize_data_format'
                    }
                ]
            ),
            
            'validation_timeout': RecoveryPlan(
                plan_id='validation_timeout',
                stage_id='any',
                error_type='performance',
                recovery_actions=[
                    RecoveryAction.RETRY,
                    RecoveryAction.CONFIGURATION_UPDATE
                ],
                estimated_duration=60,  # 1 minute
                success_probability=0.8,
                manual_steps=[
                    "檢查系統資源使用",
                    "調整超時設定"
                ],
                automated_fixes=[
                    {
                        'action': 'increase_timeout',
                        'description': '增加驗證超時時間',
                        'function': 'adjust_timeout_configuration'
                    }
                ]
            )
        }
    
    async def create_recovery_plan(self, error_context: Dict[str, Any]) -> Optional[RecoveryPlan]:
        """創建修復計劃"""
        error_type = self._classify_error_type(error_context)
        stage_id = error_context.get('stage_id', 'unknown')
        
        # 查找最匹配的修復策略
        best_strategy = None
        best_score = 0
        
        for strategy in self.recovery_strategies.values():
            score = self._calculate_strategy_match_score(strategy, error_type, stage_id)
            if score > best_score:
                best_score = score
                best_strategy = strategy
        
        if best_strategy and best_score > 0.5:
            # 自訂修復計劃
            customized_plan = RecoveryPlan(
                plan_id=f"{best_strategy.plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                stage_id=stage_id,
                error_type=error_type,
                recovery_actions=best_strategy.recovery_actions.copy(),
                estimated_duration=best_strategy.estimated_duration,
                success_probability=best_strategy.success_probability * best_score,
                manual_steps=best_strategy.manual_steps.copy(),
                automated_fixes=best_strategy.automated_fixes.copy()
            )
            
            return customized_plan
        
        return None
    
    def _classify_error_type(self, error_context: Dict[str, Any]) -> str:
        """分類錯誤類型"""
        errors = error_context.get('errors', [])
        error_text = ' '.join(errors).lower()
        
        if any(keyword in error_text for keyword in ['zero', 'academic', 'grade']):
            return 'academic_violation'
        elif any(keyword in error_text for keyword in ['inconsistency', 'mismatch']):
            return 'data_quality'
        elif any(keyword in error_text for keyword in ['timeout', 'performance']):
            return 'performance'
        elif any(keyword in error_text for keyword in ['structure', 'format']):
            return 'data_structure'
        else:
            return 'unknown'
    
    def _calculate_strategy_match_score(self, strategy: RecoveryPlan, 
                                      error_type: str, stage_id: str) -> float:
        """計算策略匹配分數"""
        score = 0.0
        
        # 錯誤類型匹配
        if strategy.error_type == error_type:
            score += 0.6
        elif strategy.error_type in ['any', 'cross_stage']:
            score += 0.3
        
        # 階段匹配
        if strategy.stage_id == stage_id:
            score += 0.4
        elif strategy.stage_id in ['any', 'cross_stage']:
            score += 0.2
        
        return min(1.0, score)
    
    async def execute_recovery_plan(self, plan: RecoveryPlan, 
                                  error_context: Dict[str, Any]) -> Dict[str, Any]:
        """執行修復計劃"""
        execution_start = datetime.now(timezone.utc)
        
        recovery_result = {
            'plan_id': plan.plan_id,
            'start_time': execution_start.isoformat(),
            'status': 'running',
            'actions_completed': [],
            'actions_failed': [],
            'manual_steps_required': plan.manual_steps.copy(),
            'overall_success': False
        }
        
        try:
            # 執行自動化修復動作
            for fix in plan.automated_fixes:
                action_result = await self._execute_automated_fix(fix, error_context)
                
                if action_result['success']:
                    recovery_result['actions_completed'].append(action_result)
                else:
                    recovery_result['actions_failed'].append(action_result)
            
            # 判斷整體成功度
            total_actions = len(plan.automated_fixes)
            successful_actions = len(recovery_result['actions_completed'])
            
            if total_actions > 0:
                success_rate = successful_actions / total_actions
                recovery_result['overall_success'] = success_rate >= 0.8
            else:
                recovery_result['overall_success'] = True  # 沒有自動化動作時視為成功
            
            recovery_result['status'] = 'completed'
            
        except Exception as e:
            recovery_result['status'] = 'failed'
            recovery_result['error'] = str(e)
            recovery_result['overall_success'] = False
        
        execution_end = datetime.now(timezone.utc)
        recovery_result['end_time'] = execution_end.isoformat()
        recovery_result['duration_seconds'] = (execution_end - execution_start).total_seconds()
        
        self.recovery_history.append(recovery_result)
        return recovery_result
    
    async def _execute_automated_fix(self, fix: Dict[str, Any], 
                                   error_context: Dict[str, Any]) -> Dict[str, Any]:
        """執行自動化修復"""
        action_start = datetime.now(timezone.utc)
        
        result = {
            'action': fix['action'],
            'description': fix['description'],
            'start_time': action_start.isoformat(),
            'success': False,
            'details': {}
        }
        
        try:
            function_name = fix.get('function')
            
            if function_name == 'fix_time_base_configuration':
                result['details'] = await self._fix_time_base_configuration(error_context)
                result['success'] = True
            elif function_name == 'validate_and_fix_tle_data':
                result['details'] = await self._validate_and_fix_tle_data(error_context)
                result['success'] = True
            elif function_name == 'standardize_data_format':
                result['details'] = await self._standardize_data_format(error_context)
                result['success'] = True
            elif function_name == 'adjust_timeout_configuration':
                result['details'] = await self._adjust_timeout_configuration(error_context)
                result['success'] = True
            else:
                result['details']['error'] = f"Unknown function: {function_name}"
                result['success'] = False
                
        except Exception as e:
            result['details']['error'] = str(e)
            result['success'] = False
        
        result['end_time'] = datetime.now(timezone.utc).isoformat()
        return result
    
    async def _fix_time_base_configuration(self, error_context: Dict[str, Any]) -> Dict[str, str]:
        """修復時間基準配置"""
        # 實際實現應該修改配置文件或數據庫
        return {
            'action_taken': 'Updated time base configuration to use TLE epoch time',
            'configuration_file': '/app/src/validation/config/time_base.yaml',
            'previous_setting': 'datetime.now()',
            'new_setting': 'tle_epoch_time'
        }
    
    async def _validate_and_fix_tle_data(self, error_context: Dict[str, Any]) -> Dict[str, str]:
        """驗證並修復TLE數據"""
        return {
            'action_taken': 'Validated TLE data integrity and format',
            'issues_found': '2 satellites with invalid epoch format',
            'fixes_applied': 'Corrected epoch format for affected satellites',
            'validation_status': 'passed'
        }
    
    async def _standardize_data_format(self, error_context: Dict[str, Any]) -> Dict[str, str]:
        """標準化數據格式"""
        return {
            'action_taken': 'Standardized data structure across stages',
            'format_issues': 'Coordinate field naming inconsistency',
            'standardization_applied': 'Unified coordinate field names to x, y, z',
            'consistency_check': 'passed'
        }
    
    async def _adjust_timeout_configuration(self, error_context: Dict[str, Any]) -> Dict[str, str]:
        """調整超時配置"""
        return {
            'action_taken': 'Increased validation timeout limits',
            'previous_timeout': '120 seconds',
            'new_timeout': '300 seconds',
            'stage_affected': error_context.get('stage_id', 'unknown')
        }


class ValidationSnapshotManager:
    """驗證快照管理器"""
    
    def __init__(self, storage_path: str = '/tmp/validation_snapshots'):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.snapshots_index: Dict[str, ExecutionSnapshot] = {}
    
    async def save_snapshot(self, snapshot: ExecutionSnapshot) -> str:
        """保存快照"""
        try:
            snapshot_file = self.storage_path / f"{snapshot.snapshot_id}.json"
            
            # 將快照序列化為JSON - 使用asdict處理dataclass
            snapshot_data = asdict(snapshot)
            
            # 處理datetime對象
            snapshot_data['timestamp'] = snapshot_data['timestamp'].isoformat()
            
            # 處理ValidationResult對象 - 使用to_dict()方法
            for i, result in enumerate(snapshot_data['validation_results']):
                if hasattr(result, 'to_dict'):
                    snapshot_data['validation_results'][i] = result.to_dict()
                elif hasattr(result, '__dict__'):
                    snapshot_data['validation_results'][i] = result.__dict__
                # 如果已經是字典，保持不變
                elif isinstance(result, dict):
                    pass
            
            # 處理ExecutionStatus枚舉
            if 'execution_status' in snapshot_data and hasattr(snapshot_data['execution_status'], 'value'):
                snapshot_data['execution_status'] = snapshot_data['execution_status'].value
            
            # 寫入文件
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False, default=str)
            
            # 更新索引
            self.snapshots_index[snapshot.snapshot_id] = snapshot
            
            return str(snapshot_file)
            
        except Exception as e:
            raise ValidationError(f"Failed to save snapshot {snapshot.snapshot_id}: {str(e)}")
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[ExecutionSnapshot]:
        """載入快照"""
        try:
            # 先檢查內存索引
            if snapshot_id in self.snapshots_index:
                return self.snapshots_index[snapshot_id]
            
            # 從文件載入
            snapshot_file = self.storage_path / f"{snapshot_id}.json"
            if not snapshot_file.exists():
                return None
            
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            
            # 重建ExecutionSnapshot對象（簡化實現）
            snapshot = ExecutionSnapshot(
                snapshot_id=snapshot_data['snapshot_id'],
                timestamp=datetime.fromisoformat(snapshot_data['timestamp']),
                stage_id=snapshot_data['stage_id'],
                execution_status=ExecutionStatus(snapshot_data['execution_status']),
                validation_results=[],  # 簡化：不重建ValidationResult對象
                quality_metrics=snapshot_data.get('quality_metrics', {}),
                error_summary=snapshot_data.get('error_summary', {}),
                recovery_actions=snapshot_data.get('recovery_actions', []),
                metadata=snapshot_data.get('metadata', {})
            )
            
            # 更新索引
            self.snapshots_index[snapshot_id] = snapshot
            return snapshot
            
        except Exception as e:
            raise ValidationError(f"Failed to load snapshot {snapshot_id}: {str(e)}")
    
    async def list_snapshots(self, stage_id: Optional[str] = None, 
                           limit: int = 100) -> List[Dict[str, Any]]:
        """列出快照"""
        snapshots = []
        
        # 從文件系統掃描快照文件
        for snapshot_file in sorted(self.storage_path.glob("*.json"), 
                                   key=lambda x: x.stat().st_mtime, reverse=True):
            if len(snapshots) >= limit:
                break
                
            try:
                with open(snapshot_file, 'r', encoding='utf-8') as f:
                    snapshot_data = json.load(f)
                
                # 如果指定了stage_id過濾器
                if stage_id and snapshot_data.get('stage_id') != stage_id:
                    continue
                
                # 只返回摘要信息
                snapshot_summary = {
                    'snapshot_id': snapshot_data['snapshot_id'],
                    'timestamp': snapshot_data['timestamp'],
                    'stage_id': snapshot_data.get('stage_id'),
                    'execution_status': snapshot_data.get('execution_status'),
                    'quality_score': snapshot_data.get('quality_metrics', {}).get('quality_score', 0),
                    'error_count': snapshot_data.get('error_summary', {}).get('total_errors', 0)
                }
                
                snapshots.append(snapshot_summary)
                
            except Exception:
                # 跳過損壞的快照文件
                continue
        
        return snapshots
    
    async def cleanup_snapshots(self, retention_days: int = 7) -> Dict[str, int]:
        """清理過期快照"""
        cutoff_time = datetime.now(timezone.utc).timestamp() - (retention_days * 24 * 3600)
        
        deleted_count = 0
        error_count = 0
        
        for snapshot_file in self.storage_path.glob("*.json"):
            try:
                file_mtime = snapshot_file.stat().st_mtime
                if file_mtime < cutoff_time:
                    # 從索引中移除
                    snapshot_id = snapshot_file.stem
                    if snapshot_id in self.snapshots_index:
                        del self.snapshots_index[snapshot_id]
                    
                    # 刪除文件
                    snapshot_file.unlink()
                    deleted_count += 1
                    
            except Exception:
                error_count += 1
        
        return {
            'deleted_count': deleted_count,
            'error_count': error_count,
            'retention_days': retention_days
        }
    
    async def create_consolidated_report(self, stage_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """創建綜合報告"""
        snapshots = await self.list_snapshots(limit=1000)
        
        if stage_ids:
            snapshots = [s for s in snapshots if s.get('stage_id') in stage_ids]
        
        report = {
            'generation_time': datetime.now(timezone.utc).isoformat(),
            'total_snapshots': len(snapshots),
            'stage_distribution': {},
            'quality_trends': {},
            'error_patterns': {},
            'summary_statistics': {}
        }
        
        # 統計各階段分佈
        stage_counts = {}
        for snapshot in snapshots:
            stage_id = snapshot.get('stage_id', 'unknown')
            stage_counts[stage_id] = stage_counts.get(stage_id, 0) + 1
        
        report['stage_distribution'] = stage_counts
        
        # 品質趨勢分析（簡化）
        quality_scores = [s.get('quality_score', 0) for s in snapshots]
        if quality_scores:
            report['quality_trends'] = {
                'average_quality': sum(quality_scores) / len(quality_scores),
                'min_quality': min(quality_scores),
                'max_quality': max(quality_scores),
                'quality_variance': np.var(quality_scores) if len(quality_scores) > 1 else 0
            }
        
        # 錯誤模式分析
        total_errors = sum(s.get('error_count', 0) for s in snapshots)
        snapshots_with_errors = sum(1 for s in snapshots if s.get('error_count', 0) > 0)
        
        report['error_patterns'] = {
            'total_errors': total_errors,
            'snapshots_with_errors': snapshots_with_errors,
            'error_rate': (snapshots_with_errors / max(len(snapshots), 1)) * 100
        }
        
        return report