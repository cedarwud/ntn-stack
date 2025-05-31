"""
資料庫連接管理器
提供資料庫連接的生命週期管理
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine
from app.db.base import engine
from app.db.base_class import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """資料庫連接管理器"""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.is_connected = False

    async def connect(self):
        """建立資料庫連接並創建表格"""
        try:
            logger.info("正在建立資料庫連接...")

            # 創建所有表格
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            self.is_connected = True
            logger.info("✅ 資料庫連接已建立，表格已創建")

        except Exception as e:
            logger.error(f"❌ 資料庫連接失敗: {e}")
            raise e

    async def disconnect(self):
        """關閉資料庫連接"""
        try:
            if self.is_connected:
                await self.engine.dispose()
                self.is_connected = False
                logger.info("✅ 資料庫連接已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉資料庫連接時發生錯誤: {e}")

    def is_ready(self) -> bool:
        """檢查資料庫是否就緒"""
        return self.is_connected


# 創建全域資料庫管理器實例
database = DatabaseManager(engine)
