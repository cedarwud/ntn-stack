"""
決策執行器接口定義
==================

定義了決策執行和監控的統一接口。
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from .decision_engine import Decision
from datetime import datetime
import uuid


class ExecutionStatus(Enum):
    """執行狀態枚舉"""

    PENDING = "pending"  # 等待執行
    RUNNING = "running"  # 執行中
    SUCCESS = "success"  # 執行成功
    FAILED = "failed"  # 執行失敗
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 執行超時


@dataclass
class ExecutionResult:
    """執行結果數據結構"""

    success: bool  # 是否成功
    execution_time: float  # 執行時間 (毫秒)
    performance_metrics: Dict[str, float]  # 性能指標
    status: ExecutionStatus  # 執行狀態
    decision: Optional[Decision] = None  # 原始決策
    error_message: Optional[str] = None  # 錯誤訊息
    execution_id: Optional[str] = None  # 執行ID
    rollback_data: Optional[Dict[str, Any]] = None  # 回滾數據

    def __post_init__(self):
        """後處理驗證"""
        if self.success and self.status != ExecutionStatus.SUCCESS:
            self.status = ExecutionStatus.SUCCESS
        elif not self.success and self.status == ExecutionStatus.SUCCESS:
            self.status = ExecutionStatus.FAILED


@dataclass
class ExecutionContext:
    """執行上下文"""

    execution_id: str  # 執行ID
    timestamp: float  # 執行時間戳
    user_id: Optional[str] = None  # 用戶ID
    session_id: Optional[str] = None  # 會話ID
    priority: int = 0  # 執行優先級 (0-10)
    timeout_seconds: float = 30.0  # 超時時間
    retry_count: int = 0  # 重試次數
    max_retries: int = 3  # 最大重試次數
    metadata: Optional[Dict[str, Any]] = None  # 額外元數據


class DecisionExecutorInterface(ABC):
    """決策執行器抽象接口"""

    @abstractmethod
    def execute_decision(
        self, decision: Decision, context: Optional[ExecutionContext] = None
    ) -> ExecutionResult:
        """
        執行決策

        Args:
            decision: 要執行的決策
            context: 執行上下文

        Returns:
            ExecutionResult: 執行結果
        """
        pass

    @abstractmethod
    def rollback_decision(self, execution_id: str) -> bool:
        """
        回滾決策

        Args:
            execution_id: 執行ID

        Returns:
            bool: 是否成功回滾
        """
        pass

    @abstractmethod
    def monitor_execution(self, execution_id: str) -> Dict[str, Any]:
        """
        監控決策執行狀態

        Args:
            execution_id: 執行ID

        Returns:
            Dict[str, Any]: 執行狀態信息
        """
        pass

    @abstractmethod
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """
        獲取執行歷史

        Args:
            limit: 返回記錄數限制

        Returns:
            List[ExecutionResult]: 執行歷史列表
        """
        pass

    @abstractmethod
    def cancel_execution(self, execution_id: str) -> bool:
        """
        取消執行

        Args:
            execution_id: 執行ID

        Returns:
            bool: 是否成功取消
        """
        pass

    @abstractmethod
    def validate_decision(self, decision: Decision) -> bool:
        """
        驗證決策的可執行性

        Args:
            decision: 要驗證的決策

        Returns:
            bool: 是否可執行
        """
        pass

    @abstractmethod
    def estimate_execution_time(self, decision: Decision) -> float:
        """
        估計執行時間

        Args:
            decision: 決策

        Returns:
            float: 預估執行時間 (毫秒)
        """
        pass

    @abstractmethod
    def get_resource_usage(self) -> Dict[str, float]:
        """
        獲取資源使用情況

        Returns:
            Dict[str, float]: 資源使用統計
        """
        pass


class ExecutionError(Exception):
    """執行錯誤基類"""

    pass


class ExecutionTimeoutError(ExecutionError):
    """執行超時錯誤"""

    pass


class ExecutionValidationError(ExecutionError):
    """執行驗證錯誤"""

    pass
