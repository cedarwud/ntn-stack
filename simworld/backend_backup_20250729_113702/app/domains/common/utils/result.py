from enum import Enum
from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResultStatus(str, Enum):
    """操作結果狀態枚舉"""

    SUCCESS = "success"
    FAILURE = "failure"


class Error(BaseModel):
    """錯誤信息模型"""

    code: str = Field(..., description="錯誤代碼")
    message: str = Field(..., description="錯誤消息")
    details: Optional[Dict[str, Any]] = Field(None, description="錯誤詳情")


class Result(Generic[T], BaseModel):
    """操作結果包裝類

    用於統一處理領域操作的結果和錯誤
    """

    status: ResultStatus = Field(..., description="操作狀態")
    data: Optional[T] = Field(None, description="結果數據")
    errors: List[Error] = Field(default_factory=list, description="錯誤列表")

    @classmethod
    def success(cls, data: Optional[T] = None) -> "Result[T]":
        """創建成功結果

        Args:
            data: 結果數據

        Returns:
            成功結果對象
        """
        return cls(status=ResultStatus.SUCCESS, data=data)

    @classmethod
    def failure(
        cls, error_code: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> "Result[T]":
        """創建失敗結果

        Args:
            error_code: 錯誤代碼
            message: 錯誤消息
            details: 錯誤詳情

        Returns:
            失敗結果對象
        """
        error = Error(code=error_code, message=message, details=details)
        return cls(status=ResultStatus.FAILURE, errors=[error])

    def is_success(self) -> bool:
        """檢查結果是否成功

        Returns:
            是否成功
        """
        return self.status == ResultStatus.SUCCESS

    def is_failure(self) -> bool:
        """檢查結果是否失敗

        Returns:
            是否失敗
        """
        return self.status == ResultStatus.FAILURE

    def add_error(
        self, error_code: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> "Result[T]":
        """添加錯誤

        Args:
            error_code: 錯誤代碼
            message: 錯誤消息
            details: 錯誤詳情

        Returns:
            當前結果對象
        """
        error = Error(code=error_code, message=message, details=details)
        self.errors.append(error)
        self.status = ResultStatus.FAILURE
        return self
