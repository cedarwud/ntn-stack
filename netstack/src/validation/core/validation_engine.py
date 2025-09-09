"""
驗證引擎核心類別
協調和執行所有驗證器，提供統一的驗證服務
"""

from typing import Dict, List, Any, Optional, Type
from datetime import datetime
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_validator import BaseValidator, ValidationResult, ValidationStatus, ValidationLevel
from .error_handler import ValidationError, ErrorHandler


logger = logging.getLogger(__name__)


class ValidationContext:
    """驗證上下文，提供驗證過程中的共享信息"""
    
    def __init__(self, 
                 stage: str = "",
                 data_type: str = "",
                 metadata: Dict[str, Any] = None):
        """
        初始化驗證上下文
        
        Args:
            stage: 處理階段（如 stage1, stage2, etc.）
            data_type: 數據類型（如 tle_data, orbital_data, etc.）
            metadata: 上下文元數據
        """
        self.stage = stage
        self.data_type = data_type
        self.metadata = metadata or {}
        self.start_time = datetime.utcnow()
        self.validators_run = []
        self.thread_local = threading.local()
        
    def add_validator(self, validator_name: str):
        """添加已運行的驗證器"""
        self.validators_run.append({
            "name": validator_name,
            "timestamp": datetime.utcnow()
        })
        
    def get_duration(self) -> float:
        """獲取驗證持續時間（秒）"""
        return (datetime.utcnow() - self.start_time).total_seconds()
        
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "stage": self.stage,
            "data_type": self.data_type,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat(),
            "duration_seconds": self.get_duration(),
            "validators_run": self.validators_run
        }


class ValidationEngine:
    """
    驗證引擎主類
    負責管理所有驗證器，協調驗證流程，聚合驗證結果
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化驗證引擎
        
        Args:
            config: 引擎配置
        """
        self.config = config or {}
        self.validators: Dict[str, BaseValidator] = {}
        self.validator_chains: Dict[str, List[str]] = {}
        self.parallel_execution = self.config.get("parallel_execution", True)
        self.max_workers = self.config.get("max_workers", 4)
        self.stop_on_critical = self.config.get("stop_on_critical", True)
        self.logger = logging.getLogger("validation.engine")
        
    def register_validator(self, validator: BaseValidator, chain: str = "default"):
        """
        註冊驗證器
        
        Args:
            validator: 驗證器實例
            chain: 驗證器鏈名稱
        """
        if validator.name in self.validators:
            self.logger.warning(f"Validator {validator.name} already registered, replacing...")
            
        self.validators[validator.name] = validator
        
        # 添加到驗證鏈
        if chain not in self.validator_chains:
            self.validator_chains[chain] = []
            
        if validator.name not in self.validator_chains[chain]:
            self.validator_chains[chain].append(validator.name)
            
        self.logger.info(f"Registered validator: {validator.name} in chain: {chain}")
        
    def unregister_validator(self, validator_name: str):
        """
        取消註冊驗證器
        
        Args:
            validator_name: 驗證器名稱
        """
        if validator_name in self.validators:
            del self.validators[validator_name]
            
            # 從所有鏈中移除
            for chain_validators in self.validator_chains.values():
                if validator_name in chain_validators:
                    chain_validators.remove(validator_name)
                    
            self.logger.info(f"Unregistered validator: {validator_name}")
        else:
            self.logger.warning(f"Validator {validator_name} not found for unregistration")
            
    def validate_data(self, 
                     data: Any, 
                     context: ValidationContext = None,
                     validator_chain: str = "default") -> Dict[str, Any]:
        """
        執行數據驗證
        
        Args:
            data: 要驗證的數據
            context: 驗證上下文
            validator_chain: 要使用的驗證器鏈
            
        Returns:
            驗證結果摘要
        """
        if context is None:
            context = ValidationContext()
            
        self.logger.info(f"Starting validation with chain: {validator_chain}")
        
        # 獲取要運行的驗證器列表
        validator_names = self.validator_chains.get(validator_chain, [])
        if not validator_names:
            self.logger.warning(f"No validators found in chain: {validator_chain}")
            return self._create_empty_result(context)
            
        all_results = []
        blocking_errors = []
        
        try:
            if self.parallel_execution and len(validator_names) > 1:
                # 並行執行驗證器
                all_results = self._run_validators_parallel(validator_names, data, context)
            else:
                # 序列執行驗證器
                all_results = self._run_validators_sequential(validator_names, data, context)
                
        except Exception as e:
            self.logger.exception(f"Validation engine error: {e}")
            error_result = ValidationResult(
                validator_name="ValidationEngine",
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Validation engine failed: {str(e)}",
                details={"exception": str(e)}
            )
            all_results.append(error_result)
            
        # 分析結果
        summary = self._analyze_results(all_results, context)
        
        # 檢查是否有阻斷性錯誤
        blocking_results = [r for r in all_results if r.is_blocking()]
        if blocking_results:
            self.logger.error(f"Found {len(blocking_results)} blocking validation errors")
            summary["has_blocking_errors"] = True
            summary["blocking_errors"] = [r.to_dict() for r in blocking_results]
            
            # 如果設置了遇到嚴重錯誤就停止
            if self.stop_on_critical:
                summary["validation_aborted"] = True
                
        return summary
        
    def _run_validators_sequential(self, 
                                 validator_names: List[str], 
                                 data: Any, 
                                 context: ValidationContext) -> List[ValidationResult]:
        """序列執行驗證器"""
        all_results = []
        
        for validator_name in validator_names:
            if validator_name not in self.validators:
                self.logger.error(f"Validator {validator_name} not found")
                continue
                
            validator = self.validators[validator_name]
            context.add_validator(validator_name)
            
            try:
                results = validator.run_validation(data, context.to_dict())
                all_results.extend(results)
                
                # 檢查是否需要因嚴重錯誤而停止
                if self.stop_on_critical:
                    blocking_results = [r for r in results if r.is_blocking()]
                    if blocking_results:
                        self.logger.error(f"Stopping validation due to blocking errors in {validator_name}")
                        break
                        
            except Exception as e:
                error_result = ValidationResult(
                    validator_name=validator_name,
                    status=ValidationStatus.ERROR,
                    level=ValidationLevel.CRITICAL,
                    message=f"Validator execution failed: {str(e)}",
                    details={"exception": str(e)}
                )
                all_results.append(error_result)
                
                if self.stop_on_critical:
                    break
                    
        return all_results
        
    def _run_validators_parallel(self, 
                               validator_names: List[str], 
                               data: Any, 
                               context: ValidationContext) -> List[ValidationResult]:
        """並行執行驗證器"""
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有驗證任務
            future_to_validator = {}
            for validator_name in validator_names:
                if validator_name not in self.validators:
                    self.logger.error(f"Validator {validator_name} not found")
                    continue
                    
                validator = self.validators[validator_name]
                future = executor.submit(self._run_single_validator, validator, data, context)
                future_to_validator[future] = validator_name
                
            # 收集結果
            for future in as_completed(future_to_validator):
                validator_name = future_to_validator[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    self.logger.exception(f"Validator {validator_name} failed: {e}")
                    error_result = ValidationResult(
                        validator_name=validator_name,
                        status=ValidationStatus.ERROR,
                        level=ValidationLevel.CRITICAL,
                        message=f"Validator execution failed: {str(e)}",
                        details={"exception": str(e)}
                    )
                    all_results.append(error_result)
                    
        return all_results
        
    def _run_single_validator(self, 
                            validator: BaseValidator, 
                            data: Any, 
                            context: ValidationContext) -> List[ValidationResult]:
        """運行單個驗證器（用於並行執行）"""
        context.add_validator(validator.name)
        return validator.run_validation(data, context.to_dict())
        
    def _analyze_results(self, 
                        results: List[ValidationResult], 
                        context: ValidationContext) -> Dict[str, Any]:
        """分析驗證結果"""
        if not results:
            return self._create_empty_result(context)
            
        # 統計各種狀態
        status_counts = {}
        level_counts = {}
        validator_results = {}
        
        for result in results:
            # 統計狀態
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 統計層級
            level = result.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
            
            # 按驗證器分組
            validator_name = result.validator_name
            if validator_name not in validator_results:
                validator_results[validator_name] = []
            validator_results[validator_name].append(result.to_dict())
            
        # 計算總體狀態
        overall_status = ValidationStatus.PASSED
        if status_counts.get("failed", 0) > 0:
            overall_status = ValidationStatus.FAILED
        elif status_counts.get("warning", 0) > 0:
            overall_status = ValidationStatus.WARNING
        elif status_counts.get("error", 0) > 0:
            overall_status = ValidationStatus.ERROR
            
        return {
            "validation_summary": {
                "overall_status": overall_status.value,
                "total_results": len(results),
                "validators_executed": len(validator_results),
                "execution_time_seconds": context.get_duration()
            },
            "status_distribution": status_counts,
            "level_distribution": level_counts,
            "validator_results": validator_results,
            "context": context.to_dict(),
            "has_blocking_errors": False,  # 會在上層方法中設置
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def _create_empty_result(self, context: ValidationContext) -> Dict[str, Any]:
        """創建空驗證結果"""
        return {
            "validation_summary": {
                "overall_status": ValidationStatus.SKIPPED.value,
                "total_results": 0,
                "validators_executed": 0,
                "execution_time_seconds": context.get_duration()
            },
            "status_distribution": {},
            "level_distribution": {},
            "validator_results": {},
            "context": context.to_dict(),
            "has_blocking_errors": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def get_validator_info(self) -> Dict[str, Any]:
        """獲取驗證器信息"""
        return {
            "total_validators": len(self.validators),
            "validator_names": list(self.validators.keys()),
            "validator_chains": self.validator_chains,
            "engine_config": {
                "parallel_execution": self.parallel_execution,
                "max_workers": self.max_workers,
                "stop_on_critical": self.stop_on_critical
            }
        }
        
    def __str__(self) -> str:
        return f"ValidationEngine(validators={len(self.validators)}, chains={len(self.validator_chains)})"
