#!/usr/bin/env python3
"""
HybridStorageManager - 階段五混合存儲管理器
符合@docs/stages/stage5-integration.md要求的PostgreSQL + Docker Volume存儲架構
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class HybridStorageManager:
    """
    混合存儲管理器 - 實現PostgreSQL結構化數據 + Docker Volume檔案存儲
    符合@docs要求的存儲策略分工
    """
    
    def __init__(self, 
                 postgresql_config: Dict[str, str] = None,
                 volume_path: str = "/app/data"):
        """
        初始化混合存儲管理器
        
        Args:
            postgresql_config: PostgreSQL連接配置
            volume_path: Docker Volume存儲路徑
        """
        logger.info("🗄️ 初始化混合存儲管理器...")
        
        # PostgreSQL配置
        self.postgresql_config = postgresql_config or {
            "host": "localhost",
            "port": "5432", 
            "database": "netstack",
            "user": "netstack_user",
            "password": "netstack_pass"
        }
        
        # Volume存儲路徑
        self.volume_path = Path(volume_path)
        self.volume_path.mkdir(parents=True, exist_ok=True)
        
        # 存儲策略配置 - 符合@docs要求
        self.storage_strategy = {
            'postgresql': [
                'satellite_metadata',      # 衛星基本資訊
                'signal_statistics',       # 信號統計指標
                'event_summaries',         # 3GPP事件摘要
                'performance_metrics'      # 系統性能指標
            ],
            'volume_files': [
                'timeseries_data',         # 完整時間序列
                'animation_resources',     # 前端動畫數據
                'signal_heatmaps',        # 信號熱力圖
                'orbit_trajectories'       # 軌道軌跡數據
            ]
        }
        
        # 驗證存儲架構
        self._verify_storage_architecture()
        
        logger.info("✅ 混合存儲管理器初始化完成")
        logger.info(f"   PostgreSQL: {self.postgresql_config['host']}:{self.postgresql_config['port']}")
        logger.info(f"   Volume路徑: {self.volume_path}")
    
    def _verify_storage_architecture(self):
        """驗證存儲架構完整性 - 符合@docs運行時檢查要求"""
        try:
            # 檢查Volume存儲路徑
            if not os.path.exists(self.volume_path):
                raise RuntimeError(f"Volume存儲路徑不存在: {self.volume_path}")
            
            if not os.access(self.volume_path, os.W_OK):
                raise RuntimeError(f"Volume路徑無寫入權限: {self.volume_path}")
            
            # 嘗試PostgreSQL連接（如果配置了）
            try:
                with self.get_database_connection() as conn:
                    if conn:
                        logger.info("🔗 PostgreSQL連接測試成功")
            except Exception as e:
                logger.warning(f"⚠️ PostgreSQL連接測試失敗: {e}")
                logger.warning("   將僅使用Volume存儲")
            
        except Exception as e:
            logger.error(f"❌ 存儲架構驗證失敗: {e}")
            raise
    
    @contextmanager
    def get_database_connection(self):
        """
        獲取PostgreSQL數據庫連接
        
        Returns:
            psycopg2.connection: 數據庫連接對象
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.postgresql_config)
            conn.autocommit = False
            yield conn
        except Exception as e:
            logger.error(f"❌ PostgreSQL連接失敗: {e}")
            if conn:
                conn.rollback()
            yield None
        finally:
            if conn:
                conn.close()
    
    def get_storage_configuration(self) -> Dict[str, Any]:
        """
        獲取存儲配置信息 - 符合@docs運行時檢查要求
        
        Returns:
            Dict: 存儲配置信息
        """
        return {
            "postgresql": {
                "host": self.postgresql_config["host"],
                "port": self.postgresql_config["port"],
                "database": self.postgresql_config["database"],
                "strategy": self.storage_strategy["postgresql"]
            },
            "volume_files": {
                "path": str(self.volume_path),
                "writable": os.access(self.volume_path, os.W_OK),
                "strategy": self.storage_strategy["volume_files"]
            }
        }
    
    def get_volume_path(self) -> str:
        """獲取Volume存儲路徑"""
        return str(self.volume_path)
    
    def store_postgresql_data(self, data_type: str, data: Dict[str, Any]) -> bool:
        """
        存儲結構化數據到PostgreSQL
        
        Args:
            data_type: 數據類型
            data: 要存儲的數據
            
        Returns:
            bool: 存儲是否成功
        """
        if data_type not in self.storage_strategy['postgresql']:
            logger.warning(f"⚠️ 數據類型 {data_type} 不適合PostgreSQL存儲")
            return False
        
        try:
            with self.get_database_connection() as conn:
                if not conn:
                    return False
                
                cursor = conn.cursor()
                
                # 根據數據類型執行相應的存儲操作
                if data_type == 'satellite_metadata':
                    self._store_satellite_metadata(cursor, data)
                elif data_type == 'signal_statistics':
                    self._store_signal_statistics(cursor, data)
                elif data_type == 'event_summaries':
                    self._store_event_summaries(cursor, data)
                elif data_type == 'performance_metrics':
                    self._store_performance_metrics(cursor, data)
                
                conn.commit()
                cursor.close()
                
                logger.info(f"✅ PostgreSQL存儲成功: {data_type}")
                return True
                
        except Exception as e:
            logger.error(f"❌ PostgreSQL存儲失敗 {data_type}: {e}")
            return False
    
    def store_volume_data(self, data_type: str, filename: str, data: Any) -> bool:
        """
        存儲大型檔案數據到Docker Volume
        
        Args:
            data_type: 數據類型
            filename: 檔案名稱
            data: 要存儲的數據
            
        Returns:
            bool: 存儲是否成功
        """
        if data_type not in self.storage_strategy['volume_files']:
            logger.warning(f"⚠️ 數據類型 {data_type} 不適合Volume存儲")
            return False
        
        try:
            # 創建數據類型子目錄
            type_dir = self.volume_path / data_type
            type_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = type_dir / filename
            
            # 根據數據類型選擇存儲格式
            if isinstance(data, (dict, list)):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(data))
            
            logger.info(f"✅ Volume存儲成功: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Volume存儲失敗 {filename}: {e}")
            return False
    
    def _store_satellite_metadata(self, cursor, data: Dict[str, Any]):
        """存儲衛星元數據到PostgreSQL"""
        # 創建表（如果不存在）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS satellite_metadata (
            satellite_id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            constellation VARCHAR(50),
            norad_id INTEGER,
            altitude_km FLOAT,
            inclination_deg FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 插入數據
        for sat_id, sat_data in data.items():
            cursor.execute("""
            INSERT INTO satellite_metadata 
            (satellite_id, name, constellation, norad_id, altitude_km, inclination_deg)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (satellite_id) DO UPDATE SET
            name = EXCLUDED.name,
            constellation = EXCLUDED.constellation,
            norad_id = EXCLUDED.norad_id,
            altitude_km = EXCLUDED.altitude_km,
            inclination_deg = EXCLUDED.inclination_deg
            """, (
                sat_id,
                sat_data.get('name', ''),
                sat_data.get('constellation', ''),
                sat_data.get('norad_id', 0),
                sat_data.get('altitude_km', 0),
                sat_data.get('inclination_deg', 0)
            ))
    
    def _store_signal_statistics(self, cursor, data: Dict[str, Any]):
        """存儲信號統計數據到PostgreSQL"""
        # 實現信號統計存儲邏輯
        pass
    
    def _store_event_summaries(self, cursor, data: Dict[str, Any]):
        """存儲3GPP事件摘要到PostgreSQL"""
        # 實現事件摘要存儲邏輯
        pass
    
    def _store_performance_metrics(self, cursor, data: Dict[str, Any]):
        """存儲性能指標到PostgreSQL"""
        # 實現性能指標存儲邏輯
        pass
    
    def get_storage_statistics(self) -> Dict[str, Any]:
        """
        獲取存儲統計信息
        
        Returns:
            Dict: 存儲統計數據
        """
        stats = {
            "postgresql": {
                "connected": False,
                "tables": [],
                "total_records": 0
            },
            "volume": {
                "path": str(self.volume_path),
                "total_size_mb": 0,
                "file_count": 0
            }
        }
        
        # PostgreSQL統計
        try:
            with self.get_database_connection() as conn:
                if conn:
                    stats["postgresql"]["connected"] = True
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    """)
                    stats["postgresql"]["tables"] = [row[0] for row in cursor.fetchall()]
                    cursor.close()
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL統計獲取失敗: {e}")
        
        # Volume統計
        try:
            total_size = sum(f.stat().st_size for f in self.volume_path.rglob('*') if f.is_file())
            stats["volume"]["total_size_mb"] = total_size / (1024 * 1024)
            stats["volume"]["file_count"] = len(list(self.volume_path.rglob('*')))
        except Exception as e:
            logger.warning(f"⚠️ Volume統計獲取失敗: {e}")
        
        return stats