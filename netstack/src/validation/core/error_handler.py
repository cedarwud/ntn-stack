"""
驗證框架錯誤處理類別
定義驗證過程中可能出現的各種錯誤和警告
"""

from typing import Dict, Any, Optional
import traceback


class ValidationError(Exception):
    """驗證錯誤基礎類"""
    
    def __init__(self, 
                 message: str,
                 validator_name: str = "",
                 error_code: str = "",
                 details: Dict[str, Any] = None,
                 original_exception: Exception = None):
        """
        初始化驗證錯誤
        
        Args:
            message: 錯誤消息
            validator_name: 發生錯誤的驗證器名稱
            error_code: 錯誤代碼
            details: 錯誤詳細信息
            original_exception: 原始異常
        """
        self.message = message
        self.validator_name = validator_name
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception
        
        # 構建完整錯誤消息
        full_message = f"[{validator_name}] {message}"
        if error_code:
            full_message = f"[{error_code}] {full_message}"
            
        super().__init__(full_message)
        
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            "message": self.message,
            "validator_name": self.validator_name,
            "error_code": self.error_code,
            "details": self.details
        }
        
        if self.original_exception:
            result["original_exception"] = {
                "type": type(self.original_exception).__name__,
                "message": str(self.original_exception),
                "traceback": traceback.format_exception(
                    type(self.original_exception),
                    self.original_exception,
                    self.original_exception.__traceback__
                )
            }
            
        return result


class AcademicStandardsViolationError(ValidationError):
    """學術標準違規錯誤"""
    
    def __init__(self, message: str, violation_type: str = "", **kwargs):
        """
        初始化學術標準違規錯誤
        
        Args:
            message: 錯誤消息
            violation_type: 違規類型（如 zero_eci_coordinates, fake_data, etc.）
            **kwargs: 其他參數傳遞給父類
        """
        self.violation_type = violation_type
        error_code = f"ACADEMIC_VIOLATION_{violation_type.upper()}" if violation_type else "ACADEMIC_VIOLATION"
        
        super().__init__(
            message=message,
            error_code=error_code,
            **kwargs
        )
        
        # 添加違規類型到詳細信息
        self.details.update({"violation_type": violation_type})


class DataQualityError(ValidationError):
    """數據品質錯誤"""
    
    def __init__(self, message: str, quality_issue: str = "", **kwargs):
        """
        初始化數據品質錯誤
        
        Args:
            message: 錯誤消息
            quality_issue: 品質問題類型
            **kwargs: 其他參數傳遞給父類
        """
        self.quality_issue = quality_issue
        error_code = f"DATA_QUALITY_{quality_issue.upper()}" if quality_issue else "DATA_QUALITY"
        
        super().__init__(
            message=message,
            error_code=error_code,
            **kwargs
        )
        
        self.details.update({"quality_issue": quality_issue})


class ConfigurationError(ValidationError):
    """配置錯誤"""
    
    def __init__(self, message: str, config_key: str = "", **kwargs):
        """
        初始化配置錯誤
        
        Args:
            message: 錯誤消息
            config_key: 配置鍵名
            **kwargs: 其他參數傳遞給父類
        """
        self.config_key = config_key
        error_code = "CONFIGURATION_ERROR"
        
        super().__init__(
            message=message,
            error_code=error_code,
            **kwargs
        )
        
        self.details.update({"config_key": config_key})


class ValidationWarning(UserWarning):
    """驗證警告基礎類"""
    
    def __init__(self, 
                 message: str,
                 validator_name: str = "",
                 warning_code: str = "",
                 details: Dict[str, Any] = None):
        """
        初始化驗證警告
        
        Args:
            message: 警告消息
            validator_name: 發生警告的驗證器名稱
            warning_code: 警告代碼
            details: 警告詳細信息
        """
        self.message = message
        self.validator_name = validator_name
        self.warning_code = warning_code
        self.details = details or {}
        
        # 構建完整警告消息
        full_message = f"[{validator_name}] {message}"
        if warning_code:
            full_message = f"[{warning_code}] {full_message}"
            
        super().__init__(full_message)
        
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "message": self.message,
            "validator_name": self.validator_name,
            "warning_code": self.warning_code,
            "details": self.details
        }


class ErrorHandler:
    """錯誤處理器，提供統一的錯誤處理功能"""
    
    @staticmethod
    def handle_validation_error(error: Exception, validator_name: str = "") -> ValidationError:
        """
        處理驗證錯誤，將普通異常轉換為驗證錯誤
        
        Args:
            error: 原始錯誤
            validator_name: 驗證器名稱
            
        Returns:
            包裝後的驗證錯誤
        """
        if isinstance(error, ValidationError):
            return error
            
        # 根據錯誤類型進行分類處理
        if "academic" in str(error).lower() or "grade" in str(error).lower():
            return AcademicStandardsViolationError(
                message=str(error),
                validator_name=validator_name,
                original_exception=error
            )
        elif "quality" in str(error).lower() or "data" in str(error).lower():
            return DataQualityError(
                message=str(error),
                validator_name=validator_name,
                original_exception=error
            )
        elif "config" in str(error).lower():
            return ConfigurationError(
                message=str(error),
                validator_name=validator_name,
                original_exception=error
            )
        else:
            return ValidationError(
                message=str(error),
                validator_name=validator_name,
                original_exception=error
            )
            
    @staticmethod
    def format_error_summary(errors: list) -> Dict[str, Any]:
        """
        格式化錯誤摘要
        
        Args:
            errors: 錯誤列表
            
        Returns:
            錯誤摘要字典
        """
        if not errors:
            return {"total_errors": 0, "error_types": {}, "critical_errors": []}
            
        error_types = {}
        critical_errors = []
        
        for error in errors:
            if isinstance(error, ValidationError):
                error_type = error.error_code or "UNKNOWN_ERROR"
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
                # 收集嚴重錯誤
                if "CRITICAL" in error_type or "ACADEMIC_VIOLATION" in error_type:
                    critical_errors.append(error.to_dict())
            else:
                error_types["GENERAL_ERROR"] = error_types.get("GENERAL_ERROR", 0) + 1
                
        return {
            "total_errors": len(errors),
            "error_types": error_types,
            "critical_errors": critical_errors,
            "has_blocking_errors": len(critical_errors) > 0
        }
