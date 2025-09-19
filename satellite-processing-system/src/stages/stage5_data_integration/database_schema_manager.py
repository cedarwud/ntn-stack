"""
Database Schema Manager - PostgreSQL架構管理組件
專責數據庫表結構建立、索引優化和混合存儲驗證
"""

import logging
from typing import Dict, Any, Optional
import psycopg2

logger = logging.getLogger(__name__)

class DatabaseSchemaManager:
    """PostgreSQL數據庫架構管理器 - 專責表結構和索引管理"""

    def __init__(self, connection: psycopg2.extensions.connection, table_schemas: Dict[str, Any]):
        """
        初始化數據庫架構管理器

        Args:
            connection: PostgreSQL數據庫連接
            table_schemas: 表結構定義
        """
        self.logger = logging.getLogger(__name__)
        self.connection = connection
        self.table_schemas = table_schemas
        self.schema_statistics = {
            "tables_created": 0,
            "indexes_created": 0,
            "storage_verified": False
        }

    def create_postgresql_tables(self) -> Dict[str, Any]:
        """創建PostgreSQL表結構"""
        self.logger.info("📋 創建PostgreSQL表結構...")

        result = {
            "success": True,
            "tables_created": [],
            "errors": []
        }

        cursor = self.connection.cursor()

        try:
            for table_info in self.table_schemas.values():
                table_name = table_info["table_name"]
                columns = table_info["columns"]

                # 檢查表是否已存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = %s
                    );
                """, (table_name,))

                table_exists = cursor.fetchone()[0]

                if not table_exists:
                    # 創建表
                    columns_sql = ", ".join(columns)
                    create_sql = f"CREATE TABLE {table_name} ({columns_sql});"

                    cursor.execute(create_sql)
                    result["tables_created"].append(table_name)
                    self.schema_statistics["tables_created"] += 1
                    self.logger.info(f"   ✅ 創建表: {table_name}")
                else:
                    self.logger.info(f"   📋 表已存在: {table_name}")

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            error_msg = f"表創建失敗: {e}"
            result["success"] = False
            result["errors"].append(error_msg)
            self.logger.error(f"   ❌ {error_msg}")
        finally:
            cursor.close()

        return result

    def create_postgresql_indexes(self) -> Dict[str, Any]:
        """創建PostgreSQL索引以優化查詢性能"""
        self.logger.info("🚀 創建PostgreSQL索引優化...")

        result = {
            "success": True,
            "indexes_created": [],
            "errors": []
        }

        # 定義關鍵索引 - 基於混合存儲查詢模式優化
        indexes = [
            {
                "name": "idx_satellite_metadata_constellation",
                "table": "satellite_metadata",
                "columns": ["constellation", "satellite_id"],
                "type": "btree"
            },
            {
                "name": "idx_signal_statistics_timestamp",
                "table": "signal_statistics",
                "columns": ["timestamp", "satellite_id"],
                "type": "btree"
            },
            {
                "name": "idx_handover_events_type_timestamp",
                "table": "handover_events",
                "columns": ["event_type", "event_timestamp"],
                "type": "btree"
            },
            {
                "name": "idx_processing_summary_stage_timestamp",
                "table": "processing_summary",
                "columns": ["stage_name", "processing_timestamp"],
                "type": "btree"
            }
        ]

        cursor = self.connection.cursor()

        try:
            for index in indexes:
                # 檢查索引是否已存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes
                        WHERE indexname = %s
                    );
                """, (index["name"],))

                index_exists = cursor.fetchone()[0]

                if not index_exists:
                    columns_sql = ", ".join(index["columns"])
                    create_sql = f"""
                        CREATE INDEX {index["name"]}
                        ON {index["table"]}
                        USING {index["type"]} ({columns_sql});
                    """

                    cursor.execute(create_sql)
                    result["indexes_created"].append(index["name"])
                    self.schema_statistics["indexes_created"] += 1
                    self.logger.info(f"   ✅ 創建索引: {index['name']}")
                else:
                    self.logger.info(f"   🚀 索引已存在: {index['name']}")

            self.connection.commit()

        except Exception as e:
            self.connection.rollback()
            error_msg = f"索引創建失敗: {e}"
            result["success"] = False
            result["errors"].append(error_msg)
            self.logger.error(f"   ❌ {error_msg}")
        finally:
            cursor.close()

        return result

    def verify_mixed_storage(self) -> Dict[str, Any]:
        """驗證混合存儲架構的完整性"""
        self.logger.info("🔍 驗證混合存儲架構...")

        verification_result = {
            "postgresql_tables": {},
            "volume_files": {},
            "storage_balance": {},
            "success": True,
            "errors": []
        }

        cursor = self.connection.cursor()

        try:
            # 驗證PostgreSQL表數據
            for table_info in self.table_schemas.values():
                table_name = table_info["table_name"]

                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]

                cursor.execute(f"""
                    SELECT pg_size_pretty(pg_total_relation_size('{table_name}'));
                """)
                size = cursor.fetchone()[0]

                verification_result["postgresql_tables"][table_name] = {
                    "row_count": count,
                    "table_size": size
                }

            # 計算存儲平衡
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """)
            total_db_size = cursor.fetchone()[0]

            verification_result["storage_balance"] = {
                "postgresql_total_size": total_db_size,
                "mixed_storage_strategy": "postgresql_structured_volume_timeseries",
                "verification_status": "completed"
            }

            self.schema_statistics["storage_verified"] = True
            self.logger.info("   ✅ 混合存儲架構驗證完成")

        except Exception as e:
            error_msg = f"混合存儲驗證失敗: {e}"
            verification_result["success"] = False
            verification_result["errors"].append(error_msg)
            self.logger.error(f"   ❌ {error_msg}")
        finally:
            cursor.close()

        return verification_result

    def get_schema_statistics(self) -> Dict[str, Any]:
        """獲取架構管理統計信息"""
        return self.schema_statistics.copy()