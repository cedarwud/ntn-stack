"""
PostgreSQL 配置模組
提供 PostgreSQL 客戶端連接和配置管理
用於替代 MongoDB 存儲 SimWorld 數據

Phase 2 重構：統一配置管理，移除重複的環境變數處理
"""
import logging
import os
from typing import Optional
import asyncpg
from asyncpg import Pool
from contextlib import asynccontextmanager

# Phase 2 重構：使用統一的配置管理
from app.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

class PostgreSQLConfig:
    """PostgreSQL 配置類"""
    
    def __init__(self):
        # 使用統一的配置管理
        self.database_url = DATABASE_URL
        
        # 移除 +asyncpg 前綴，因為 asyncpg 不需要
        if self.database_url.startswith("postgresql+asyncpg://"):
            self.database_url = self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        self.pool: Optional[Pool] = None
        
    async def connect(self) -> Pool:
        """建立 PostgreSQL 連接池"""
        if self.pool is None:
            try:
                logger.info(f"Connecting to PostgreSQL at {self.database_url}")
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=1,
                    max_size=10,
                    command_timeout=30,
                    server_settings={
                        'application_name': 'simworld_backend',
                    }
                )
                
                # 測試連接
                async with self.pool.acquire() as connection:
                    await connection.fetchval('SELECT 1')
                
                logger.info("Successfully connected to PostgreSQL")
                
                # 初始化數據庫 schema
                await self._initialize_schema()
                
            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL: {e}")
                self.pool = None
                raise
        return self.pool
    
    async def _initialize_schema(self):
        """初始化數據庫 schema"""
        try:
            schema_file = os.path.join(
                os.path.dirname(__file__), 
                'postgresql_schema.sql'
            )
            
            if os.path.exists(schema_file):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                async with self.pool.acquire() as connection:
                    await connection.execute(schema_sql)
                    logger.info("PostgreSQL schema initialized successfully")
            else:
                logger.warning(f"Schema file not found: {schema_file}")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL schema: {e}")
            raise
    
    async def disconnect(self):
        """關閉 PostgreSQL 連接池"""
        if self.pool:
            logger.info("Closing PostgreSQL connection pool")
            await self.pool.close()
            self.pool = None
    
    @asynccontextmanager
    async def get_connection(self):
        """獲取數據庫連接的上下文管理器"""
        if self.pool is None:
            raise RuntimeError("PostgreSQL pool not connected. Call connect() first.")
        
        async with self.pool.acquire() as connection:
            yield connection

# 全局 PostgreSQL 配置實例
postgresql_config = PostgreSQLConfig()

async def get_postgresql_pool() -> Pool:
    """獲取 PostgreSQL 連接池"""
    return await postgresql_config.connect()

async def get_postgresql_connection():
    """獲取 PostgreSQL 連接"""
    pool = await get_postgresql_pool()
    return postgresql_config.get_connection()