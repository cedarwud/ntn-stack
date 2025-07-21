"""
數據庫初始化服務
確保所有必要的數據庫表在應用啟動時被創建
"""

import asyncio
import asyncpg
import structlog
from pathlib import Path
from typing import Optional

logger = structlog.get_logger(__name__)


class DatabaseInitializer:
    """數據庫初始化器"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        # 從當前文件位置計算 schema 文件路徑
        # 當前文件: netstack_api/services/database_init.py
        # 目標文件: netstack_api/services/rl_training/database/satellite_cache_schema.sql
        self.schema_path = (
            Path(__file__).parent
            / "rl_training"
            / "database"
            / "satellite_cache_schema.sql"
        )

    async def ensure_tables_exist(self) -> bool:
        """確保所有必要的表都存在"""
        try:
            # 連接到數據庫
            conn = await asyncpg.connect(self.database_url)

            # 檢查 d2_measurement_cache 表是否存在
            table_exists = await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'd2_measurement_cache'
                );
            """
            )

            if not table_exists:
                logger.info("🔧 數據庫表不存在，開始初始化...")
                await self._create_tables(conn)
                logger.info("✅ 數據庫表初始化完成")
            else:
                logger.info("✅ 數據庫表已存在")

            await conn.close()
            return True

        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
            return False

    async def _create_tables(self, conn: asyncpg.Connection) -> None:
        """創建數據庫表"""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema 文件不存在: {self.schema_path}")

        # 讀取並執行 schema
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        await conn.execute(schema_sql)
        logger.info("📊 數據庫表結構創建完成")


async def ensure_database_initialized(database_url: Optional[str] = None) -> bool:
    """確保數據庫已初始化"""
    if not database_url:
        # 從環境變量獲取數據庫 URL
        import os

        database_url = os.getenv(
            "RL_DATABASE_URL",
            "postgresql://rl_user:rl_password@rl-postgres:5432/rl_research",
        )

    initializer = DatabaseInitializer(database_url)
    return await initializer.ensure_tables_exist()


if __name__ == "__main__":
    # 用於測試
    asyncio.run(ensure_database_initialized())
