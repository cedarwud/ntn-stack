"""
統一數據庫連接管理器
解決多個服務重複創建數據庫連接池的問題
"""
import os
import asyncio
from typing import Optional
import asyncpg
import structlog

logger = structlog.get_logger(__name__)


class DatabaseConnectionManager:
    """統一的數據庫連接管理器 - 單例模式"""
    
    _instance: Optional['DatabaseConnectionManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        if DatabaseConnectionManager._instance is not None:
            raise RuntimeError("DatabaseConnectionManager 是單例，請使用 get_instance() 方法")
        
        self.db_url = os.getenv(
            "SATELLITE_DATABASE_URL", 
            "postgresql://netstack_user:netstack_password@netstack-postgres:5432/netstack_db"
        )
        self.connection_pool: Optional[asyncpg.Pool] = None
        self._initialized = False
    
    @classmethod
    async def get_instance(cls) -> 'DatabaseConnectionManager':
        """獲取數據庫連接管理器單例實例"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self):
        """初始化數據庫連接池"""
        if self._initialized:
            return
        
        try:
            # 創建統一的連接池
            self.connection_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=5,          # 最小連接數
                max_size=20,         # 最大連接數
                max_queries=50000,   # 每個連接最大查詢數
                max_inactive_connection_lifetime=300.0,  # 非活躍連接生命週期 (5分鐘)
                setup=self._setup_connection,
                command_timeout=60   # 命令超時時間
            )
            
            # 測試連接
            async with self.connection_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            self._initialized = True
            logger.info(f"🔗 統一數據庫連接池初始化成功 (pool_size: 5-20)")
            
        except Exception as e:
            logger.error(f"❌ 數據庫連接池初始化失敗: {e}")
            raise
    
    async def _setup_connection(self, conn: asyncpg.Connection):
        """設置新連接的初始參數"""
        # 設置連接的時區
        await conn.execute("SET timezone TO 'UTC'")
        # 設置連接編碼
        await conn.execute("SET client_encoding TO 'UTF8'")
    
    async def get_connection(self) -> asyncpg.Connection:
        """獲取數據庫連接"""
        if not self._initialized:
            await self.initialize()
        
        if self.connection_pool is None:
            raise RuntimeError("數據庫連接池未初始化")
        
        return await self.connection_pool.acquire()
    
    def release_connection(self, conn: asyncpg.Connection):
        """釋放數據庫連接"""
        if self.connection_pool:
            self.connection_pool.release(conn)
    
    async def execute_query(self, query: str, *args):
        """執行查詢 - 便捷方法"""
        async with self.connection_pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args):
        """執行命令 - 便捷方法"""
        async with self.connection_pool.acquire() as conn:
            return await conn.execute(command, *args)
    
    async def get_pool_stats(self) -> dict:
        """獲取連接池統計信息"""
        if not self.connection_pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "size": self.connection_pool.get_size(),
            "min_size": self.connection_pool.get_min_size(),
            "max_size": self.connection_pool.get_max_size(),
            "idle_size": self.connection_pool.get_idle_size(),
            "database_url": self.db_url.replace(self.db_url.split('@')[0].split('//')[1], '***')  # 隱藏密碼
        }
    
    async def health_check(self) -> dict:
        """健康檢查"""
        try:
            if not self._initialized:
                return {"status": "not_initialized"}
            
            # 測試連接
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    return {"status": "unhealthy", "error": "query_failed"}
            
            stats = await self.get_pool_stats()
            return {
                "status": "healthy",
                "pool_stats": stats
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e)
            }
    
    async def close(self):
        """關閉連接池"""
        if self.connection_pool:
            await self.connection_pool.close()
            self.connection_pool = None
            self._initialized = False
            logger.info("🔗 數據庫連接池已關閉")


# 便捷函數
async def get_db_manager() -> DatabaseConnectionManager:
    """獲取數據庫管理器實例 - 便捷函數"""
    return await DatabaseConnectionManager.get_instance()


async def get_db_connection() -> asyncpg.Connection:
    """獲取數據庫連接 - 便捷函數"""
    manager = await get_db_manager()
    return await manager.get_connection()


def release_db_connection(conn: asyncpg.Connection):
    """釋放數據庫連接 - 便捷函數"""
    # 這個需要異步上下文，建議使用 async with 語法
    pass


class DatabaseConnectionContext:
    """數據庫連接上下文管理器"""
    
    def __init__(self):
        self.connection: Optional[asyncpg.Connection] = None
        self.manager: Optional[DatabaseConnectionManager] = None
    
    async def __aenter__(self) -> asyncpg.Connection:
        self.manager = await get_db_manager()
        self.connection = await self.manager.get_connection()
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection and self.manager:
            self.manager.release_connection(self.connection)


# 使用示例:
# async with DatabaseConnectionContext() as conn:
#     result = await conn.fetch("SELECT * FROM satellites")