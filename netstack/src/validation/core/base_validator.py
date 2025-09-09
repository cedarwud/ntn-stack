"""
驗證器基礎類別
實現所有驗證器共用的基礎功能和介面規範
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """驗證層級定義"""
    CRITICAL = "critical"    # 嚴重違規，必須阻斷
    HIGH = "high"           # 高風險，建議阻斷  
    MEDIUM = "medium"       # 中等風險，警告
    LOW = "low"            # 低風險，記錄
    INFO = "info"          # 信息，僅記錄


class ValidationStatus(Enum):
    """驗證狀態定義"""
    PASSED = "passed"       # 驗證通過
    FAILED = "failed"       # 驗證失敗
    WARNING = "warning"     # 驗證有警告
    SKIPPED = "skipped"     # 驗證跳過
    ERROR = "error"         # 驗證錯誤


class ValidationResult:
    """驗證結果封裝類"""
    
    def __init__(self, 
                 validator_name: str,
                 status: ValidationStatus,
                 level: ValidationLevel = ValidationLevel.INFO,
                 message: str = "",
                 details: Dict[str, Any] = None,
                 metadata: Dict[str, Any] = None):
        """
        初始化驗證結果
        
        Args:
            validator_name: 驗證器名稱
            status: 驗證狀態
            level: 驗證層級  
            message: 驗證消息
            details: 詳細信息
            metadata: 元數據
        """
        self.validator_name = validator_name
        self.status = status
        self.level = level
        self.message = message
        self.details = details or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "validator_name": self.validator_name,
            "status": self.status.value,
            "level": self.level.value,
            "message": self.message,
            "details": self.details,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
        
    def is_blocking(self) -> bool:
        """判斷是否為阻斷性結果"""
        return (self.status == ValidationStatus.FAILED and 
                self.level in [ValidationLevel.CRITICAL, ValidationLevel.HIGH])
                
    def __str__(self) -> str:
        return f"[{self.level.value.upper()}] {self.validator_name}: {self.message}"


class BaseValidator(ABC):
    """驗證器基礎抽象類"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化基礎驗證器
        
        Args:
            name: 驗證器名稱
            config: 驗證器配置
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"validation.{name}")
        
    @abstractmethod
    def validate(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        執行驗證邏輯（抽象方法）
        
        Args:
            data: 要驗證的數據
            context: 驗證上下文
            
        Returns:
            驗證結果列表
        """
        pass
        
    def pre_validate(self, data: Any) -> bool:
        """
        預驗證檢查
        
        Args:
            data: 要驗證的數據
            
        Returns:
            是否可以進行驗證
        """
        if data is None:
            return False
            
        # 子類可以覆蓋此方法進行特定檢查
        return True
        
    def post_validate(self, results: List[ValidationResult]) -> List[ValidationResult]:
        """
        後處理驗證結果
        
        Args:
            results: 原始驗證結果
            
        Returns:  
            處理後的驗證結果
        """
        # 子類可以覆蓋此方法進行結果後處理
        return results
        
    def create_result(self, 
                     status: ValidationStatus,
                     level: ValidationLevel = ValidationLevel.INFO,
                     message: str = "",
                     details: Dict[str, Any] = None,
                     metadata: Dict[str, Any] = None) -> ValidationResult:
        """
        創建驗證結果便捷方法
        
        Args:
            status: 驗證狀態
            level: 驗證層級
            message: 驗證消息  
            details: 詳細信息
            metadata: 元數據
            
        Returns:
            驗證結果對象
        """
        return ValidationResult(
            validator_name=self.name,
            status=status,
            level=level,
            message=message,
            details=details,
            metadata=metadata
        )
        
    def run_validation(self, data: Any, context: Dict[str, Any] = None) -> List[ValidationResult]:
        """
        運行完整驗證流程
        
        Args:
            data: 要驗證的數據
            context: 驗證上下文
            
        Returns:
            驗證結果列表
        """
        try:
            # 預驗證檢查
            if not self.pre_validate(data):
                return [self.create_result(
                    status=ValidationStatus.SKIPPED,
                    level=ValidationLevel.INFO,
                    message=f"Validator {self.name} pre-validation failed, skipping validation"
                )]
            
            # 執行主要驗證邏輯
            results = self.validate(data, context)
            
            # 後處理結果
            results = self.post_validate(results)
            
            # 記錄驗證結果
            self.logger.info(f"Validation completed: {len(results)} results")
            for result in results:
                if result.level in [ValidationLevel.CRITICAL, ValidationLevel.HIGH]:
                    self.logger.error(str(result))
                elif result.level == ValidationLevel.MEDIUM:
                    self.logger.warning(str(result))
                else:
                    self.logger.info(str(result))
                    
            return results
            
        except Exception as e:
            self.logger.exception(f"Validation error in {self.name}: {e}")
            return [self.create_result(
                status=ValidationStatus.ERROR,
                level=ValidationLevel.CRITICAL,
                message=f"Validation failed due to error: {str(e)}",
                details={"exception": str(e)}
            )]
            
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        獲取配置值
        
        Args:
            key: 配置鍵
            default: 預設值
            
        Returns:
            配置值
        """
        return self.config.get(key, default)
        
    def __str__(self) -> str:
        return f"Validator: {self.name}"
