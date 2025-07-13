#!/usr/bin/env python3
"""
LEO衛星換手決策RL系統 - PostgreSQL 數據庫初始化腳本
Phase 1: 真實數據庫實施
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

import asyncpg
from asyncpg import Connection

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默認數據庫配置
DEFAULT_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": "rl_user",
    "password": "rl_password",
    "database": "rl_research_db",
    "admin_user": "postgres",
    "admin_password": "postgres"
}

class RLDatabaseInitializer:
    """RL系統數據庫初始化器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DEFAULT_CONFIG
        self.schema_path = Path(__file__).parent / "schema.sql"
        
    async def create_database_and_user(self) -> bool:
        """創建數據庫和用戶"""
        try:
            # 連接到 PostgreSQL 服務器（使用管理員賬戶）
            admin_conn = await asyncpg.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["admin_user"],
                password=self.config["admin_password"],
                database="postgres"
            )
            
            logger.info("✅ 成功連接到 PostgreSQL 服務器")
            
            # 檢查用戶是否存在
            user_exists = await admin_conn.fetchval(
                "SELECT 1 FROM pg_user WHERE usename = $1",
                self.config["user"]
            )
            
            if not user_exists:
                # 創建用戶
                await admin_conn.execute(f"""
                    CREATE USER {self.config["user"]} 
                    WITH PASSWORD '{self.config["password"]}';
                """)
                logger.info(f"✅ 創建用戶: {self.config['user']}")
            else:
                logger.info(f"ℹ️  用戶已存在: {self.config['user']}")
            
            # 檢查數據庫是否存在
            db_exists = await admin_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                self.config["database"]
            )
            
            if not db_exists:
                # 創建數據庫
                await admin_conn.execute(f"""
                    CREATE DATABASE {self.config["database"]}
                    WITH OWNER {self.config["user"]}
                    ENCODING 'UTF8'
                    LC_COLLATE = 'en_US.UTF-8'
                    LC_CTYPE = 'en_US.UTF-8'
                    TEMPLATE template0;
                """)
                logger.info(f"✅ 創建數據庫: {self.config['database']}")
            else:
                logger.info(f"ℹ️  數據庫已存在: {self.config['database']}")
            
            # 授予權限
            await admin_conn.execute(f"""
                GRANT ALL PRIVILEGES ON DATABASE {self.config["database"]} 
                TO {self.config["user"]};
            """)
            
            await admin_conn.close()
            logger.info("✅ 數據庫和用戶創建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 數據庫創建失敗: {e}")
            return False
    
    async def initialize_schema(self) -> bool:
        """初始化數據庫表結構"""
        try:
            # 連接到目標數據庫
            conn = await asyncpg.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"]
            )
            
            logger.info(f"✅ 連接到目標數據庫: {self.config['database']}")
            
            # 讀取並執行 schema.sql
            if not self.schema_path.exists():
                raise FileNotFoundError(f"Schema 文件不存在: {self.schema_path}")
            
            schema_sql = self.schema_path.read_text(encoding='utf-8')
            
            # 執行 schema
            await conn.execute(schema_sql)
            logger.info("✅ 數據庫表結構初始化完成")
            
            # 驗證表創建
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'rl_%'
                ORDER BY table_name;
            """)
            
            table_names = [table['table_name'] for table in tables]
            logger.info(f"✅ 創建的 RL 表: {table_names}")
            
            # 檢查示例數據
            session_count = await conn.fetchval(
                "SELECT COUNT(*) FROM rl_experiment_sessions"
            )
            logger.info(f"✅ 示例實驗會話數量: {session_count}")
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 表結構初始化失敗: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """測試數據庫連接"""
        try:
            conn = await asyncpg.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"]
            )
            
            # 測試基本查詢
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                logger.info("✅ 數據庫連接測試成功")
                
                # 測試 RL 表查詢
                table_count = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name LIKE 'rl_%'
                """)
                logger.info(f"✅ RL 表數量: {table_count}")
                
                await conn.close()
                return True
            else:
                logger.error("❌ 數據庫連接測試失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 數據庫連接失敗: {e}")
            return False
    
    async def full_initialization(self) -> bool:
        """完整的數據庫初始化流程"""
        logger.info("🚀 開始 LEO RL 系統 PostgreSQL 數據庫初始化")
        
        # 步驟 1: 創建數據庫和用戶
        if not await self.create_database_and_user():
            return False
        
        # 步驟 2: 初始化表結構
        if not await self.initialize_schema():
            return False
        
        # 步驟 3: 測試連接
        if not await self.test_connection():
            return False
        
        logger.info("🎉 PostgreSQL 數據庫初始化完成！")
        logger.info("📊 系統現在可以使用真實的 PostgreSQL 儲存庫")
        return True

def get_config_from_env() -> Dict[str, Any]:
    """從環境變量獲取配置"""
    return {
        "host": os.getenv("POSTGRES_HOST", DEFAULT_CONFIG["host"]),
        "port": int(os.getenv("POSTGRES_PORT", DEFAULT_CONFIG["port"])),
        "user": os.getenv("POSTGRES_USER", DEFAULT_CONFIG["user"]),
        "password": os.getenv("POSTGRES_PASSWORD", DEFAULT_CONFIG["password"]),
        "database": os.getenv("POSTGRES_DATABASE", DEFAULT_CONFIG["database"]),
        "admin_user": os.getenv("POSTGRES_ADMIN_USER", DEFAULT_CONFIG["admin_user"]),
        "admin_password": os.getenv("POSTGRES_ADMIN_PASSWORD", DEFAULT_CONFIG["admin_password"])
    }

async def main():
    """主函數"""
    config = get_config_from_env()
    
    logger.info("🔧 數據庫配置:")
    for key, value in config.items():
        if "password" in key:
            logger.info(f"  {key}: {'*' * len(str(value))}")
        else:
            logger.info(f"  {key}: {value}")
    
    initializer = RLDatabaseInitializer(config)
    
    success = await initializer.full_initialization()
    
    if success:
        logger.info("✅ 數據庫初始化成功！")
        logger.info("🔗 數據庫連接字串:")
        logger.info(f"  postgresql://{config['user']}:***@{config['host']}:{config['port']}/{config['database']}")
        return 0
    else:
        logger.error("❌ 數據庫初始化失敗")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))