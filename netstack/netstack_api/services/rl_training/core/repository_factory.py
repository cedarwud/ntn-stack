"""
🏭 數據倉庫工廠
提供統一的數據倉庫創建和配置接口
"""

import os
import logging
from typing import Optional, Dict, Any
from enum import Enum

from ..interfaces.data_repository import IDataRepository
from ..implementations.postgresql_repository import PostgreSQLRepository  
# MockRepository 已刪除 - 違反 CLAUDE.md 核心原則
# from ..implementations.mock_repository import MockRepository

logger = logging.getLogger(__name__)


class RepositoryType(Enum):
    """數據倉庫類型"""
    POSTGRESQL = "postgresql"
    MOCK = "mock"


class RepositoryFactory:
    """數據倉庫工廠
    
    根據配置創建適當的數據倉庫實例。
    支援 PostgreSQL 和 Mock 兩種實現。
    """
    
    _instances: Dict[str, IDataRepository] = {}
    
    @classmethod
    async def create_repository(
        cls,
        repository_type: Optional[RepositoryType] = None,
        database_url: Optional[str] = None,
        use_singleton: bool = True,
        **kwargs
    ) -> IDataRepository:
        """創建數據倉庫實例
        
        Args:
            repository_type: 倉庫類型，如果為 None 則從環境變數推斷
            database_url: 數據庫連接 URL
            use_singleton: 是否使用單例模式
            **kwargs: 額外的配置參數
            
        Returns:
            IDataRepository: 數據倉庫實例
        """
        try:
            # 推斷倉庫類型
            if repository_type is None:
                repository_type = cls._infer_repository_type()
            
            # 生成實例鍵
            instance_key = f"{repository_type.value}_{hash(database_url or '')}"
            
            # 如果使用單例且實例已存在，直接返回
            if use_singleton and instance_key in cls._instances:
                logger.debug(f"返回現有倉庫實例: {repository_type.value}")
                return cls._instances[instance_key]
            
            # 創建新實例
            repository = await cls._create_repository_instance(
                repository_type, database_url, **kwargs
            )
            
            # 初始化倉庫
            if hasattr(repository, 'initialize'):
                await repository.initialize()
            
            # 如果使用單例，緩存實例
            if use_singleton:
                cls._instances[instance_key] = repository
            
            logger.info(f"成功創建數據倉庫實例: {repository_type.value}")
            return repository
            
        except Exception as e:
            logger.error(f"創建數據倉庫失敗: {e}")
            raise
    
    @classmethod
    def _infer_repository_type(cls) -> RepositoryType:
        """從環境變數推斷倉庫類型
        
        Returns:
            RepositoryType: 推斷的倉庫類型
        """
        # 檢查是否明確指定使用 Mock
        mock_enabled = os.getenv("MOCK_DATA_ENABLED", "false").lower() == "true"
        if mock_enabled:
            return RepositoryType.MOCK
        
        # 檢查是否明確指定倉庫類型
        repo_type = os.getenv("REPOSITORY_TYPE", "").lower()
        if repo_type == "mock":
            return RepositoryType.MOCK
        elif repo_type == "postgresql":
            return RepositoryType.POSTGRESQL
        
        # 根據數據庫 URL 推斷
        database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRESQL_URL")
        if database_url and database_url.startswith("postgresql"):
            return RepositoryType.POSTGRESQL
        
        # 檢查環境類型
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment in ["test", "testing"]:
            return RepositoryType.MOCK
        
        # 預設使用 PostgreSQL（如果有連接配置）
        if database_url:
            return RepositoryType.POSTGRESQL
        
        # 如果無法推斷類型，強制使用 PostgreSQL
        logger.error("無法推斷倉庫類型，強制使用 PostgreSQL - 不接受 Mock Repository 回退")
        return RepositoryType.POSTGRESQL
    
    @classmethod
    async def _create_repository_instance(
        cls,
        repository_type: RepositoryType,
        database_url: Optional[str],
        **kwargs
    ) -> IDataRepository:
        """創建具體的倉庫實例
        
        Args:
            repository_type: 倉庫類型
            database_url: 數據庫連接 URL
            **kwargs: 額外配置
            
        Returns:
            IDataRepository: 倉庫實例
        """
        if repository_type == RepositoryType.POSTGRESQL:
            return await cls._create_postgresql_repository(database_url, **kwargs)
        elif repository_type == RepositoryType.MOCK:
            # Mock Repository 已刪除 - 強制使用 PostgreSQL
            logger.error("Mock Repository 已被禁用，強制使用 PostgreSQL")
            return await cls._create_postgresql_repository(database_url, **kwargs)
        else:
            raise ValueError(f"不支援的倉庫類型: {repository_type}")
    
    @classmethod
    async def _create_postgresql_repository(
        cls,
        database_url: Optional[str],
        **kwargs
    ) -> PostgreSQLRepository:
        """創建 PostgreSQL 倉庫實例
        
        Args:
            database_url: 數據庫連接 URL
            **kwargs: 額外配置
            
        Returns:
            PostgreSQLRepository: PostgreSQL 倉庫實例
        """
        # 獲取數據庫 URL
        if not database_url:
            database_url = (
                os.getenv("DATABASE_URL") or 
                os.getenv("POSTGRESQL_URL") or
                "postgresql://rl_user:rl_password@netstack-postgres:5432/rl_db"
            )
        
        # 獲取連接池配置
        max_connections = kwargs.get('max_connections') or int(os.getenv("DB_MAX_CONNECTIONS", "10"))
        
        logger.info(f"創建 PostgreSQL 倉庫: {database_url}")
        return PostgreSQLRepository(
            database_url=database_url,
            max_connections=max_connections
        )
    
    @classmethod
    def _create_mock_repository(cls, **kwargs):
        """Mock Repository 已刪除 - 違反 CLAUDE.md 核心原則
        
        此方法已被廢棄，禁止使用模擬數據
        """
        raise RuntimeError("Mock Repository 已被禁用 - 違反 CLAUDE.md 核心原則，必須使用真實數據")
    
    @classmethod
    async def get_default_repository(cls) -> IDataRepository:
        """獲取預設數據倉庫實例
        
        Returns:
            IDataRepository: 預設倉庫實例
        """
        return await cls.create_repository(use_singleton=True)
    
    @classmethod
    def clear_instances(cls) -> None:
        """清除所有緩存的實例"""
        cls._instances.clear()
        logger.info("已清除所有倉庫實例緩存")
    
    @classmethod
    async def shutdown_all(cls) -> None:
        """關閉所有倉庫實例"""
        for instance in cls._instances.values():
            try:
                if hasattr(instance, 'close'):
                    await instance.close()
            except Exception as e:
                logger.warning(f"關閉倉庫實例失敗: {e}")
        
        cls.clear_instances()
        logger.info("已關閉所有倉庫實例")
    
    @classmethod
    def get_instance_info(cls) -> Dict[str, Any]:
        """獲取實例資訊
        
        Returns:
            Dict[str, Any]: 實例資訊
        """
        return {
            "total_instances": len(cls._instances),
            "instance_keys": list(cls._instances.keys()),
            "supported_types": [t.value for t in RepositoryType]
        }


class RepositoryConfig:
    """倉庫配置類"""
    
    def __init__(self):
        self.repository_type = os.getenv("REPOSITORY_TYPE", "auto")
        self.database_url = os.getenv("DATABASE_URL")
        self.mock_enabled = os.getenv("MOCK_DATA_ENABLED", "false").lower() == "true"
        self.max_connections = int(os.getenv("DB_MAX_CONNECTIONS", "10"))
        self.environment = os.getenv("ENVIRONMENT", "development")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式
        
        Returns:
            Dict[str, Any]: 配置字典
        """
        return {
            "repository_type": self.repository_type,
            "database_url": self.database_url,
            "mock_enabled": self.mock_enabled,
            "max_connections": self.max_connections,
            "environment": self.environment
        }
    
    def validate(self) -> bool:
        """驗證配置
        
        Returns:
            bool: 配置是否有效
        """
        if self.mock_enabled:
            return True
        
        if self.repository_type == "postgresql":
            return bool(self.database_url)
        
        return True


# 工具函數
async def create_default_repository() -> IDataRepository:
    """創建預設倉庫實例（便捷函數）
    
    Returns:
        IDataRepository: 倉庫實例
    """
    return await RepositoryFactory.get_default_repository()


def get_repository_config() -> RepositoryConfig:
    """獲取倉庫配置（便捷函數）
    
    Returns:
        RepositoryConfig: 倉庫配置
    """
    return RepositoryConfig()