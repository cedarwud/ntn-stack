from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Any, Dict, Type

T = TypeVar("T")


class RepositoryInterface(Generic[T], ABC):
    """通用的儲存庫接口，定義基本的CRUD操作"""

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """通過ID獲取實體

        Args:
            id: 實體唯一標識符

        Returns:
            找到的實體，如果未找到則返回None
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[T]:
        """獲取所有實體

        Returns:
            實體列表
        """
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """創建新實體

        Args:
            entity: 要創建的實體

        Returns:
            創建後的實體（可能包含生成的ID等）
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """更新實體

        Args:
            entity: 要更新的實體

        Returns:
            更新後的實體
        """
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """刪除實體

        Args:
            id: 要刪除的實體的ID

        Returns:
            操作是否成功
        """
        pass

    @abstractmethod
    async def exists(self, id: str) -> bool:
        """檢查實體是否存在

        Args:
            id: 要檢查的實體ID

        Returns:
            實體是否存在
        """
        pass
