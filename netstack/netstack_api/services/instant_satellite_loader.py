import os
import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class InstantSatelliteLoader:
    """容器啟動時立即載入衛星數據"""
    
    def __init__(self, postgres_url: str):
        self.postgres_url = postgres_url
        self.embedded_data_path = "/app/data/satellite_history_embedded.sql"
        
    async def ensure_data_available(self) -> bool:
        """確保衛星數據立即可用"""
        
        try:
            # 1. 檢查 PostgreSQL 中是否已有數據
            existing_data = await self._check_existing_data()
            
            if existing_data and self._is_data_fresh(existing_data):
                logger.info(f"✅ 發現 {existing_data['count']} 條新鮮的衛星歷史數據，跳過載入")
                return True
                
            # 2. 載入內建預載數據
            logger.info("📡 載入內建衛星歷史數據...")
            success = await self._load_embedded_data()
            
            if success:
                logger.info("✅ 衛星數據載入完成，系統立即可用")
                return True
                
            # 3. 緊急 fallback：生成最小可用數據集
            logger.warning("⚠️ 使用緊急 fallback 數據")
            return await self._generate_emergency_data()
            
        except Exception as e:
            logger.error(f"❌ 數據載入過程出現錯誤: {e}")
            return False
        
    async def _check_existing_data(self) -> Optional[Dict[str, Any]]:
        """檢查現有數據"""
        conn = await asyncpg.connect(self.postgres_url)
        try:
            result = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as count,
                    MAX(timestamp) as latest_time,
                    MIN(timestamp) as earliest_time
                FROM satellite_orbital_cache 
                WHERE constellation = 'precomputed'
            """)
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"❌ 檢查現有數據失敗: {e}")
            return None
        finally:
            await conn.close()
            
    def _is_data_fresh(self, data_info: Dict[str, Any]) -> bool:
        """判斷數據是否夠新鮮（7天內）"""
        if not data_info['latest_time']:
            return False
            
        age = datetime.utcnow() - data_info['latest_time'].replace(tzinfo=None)
        return age.days < 7 and data_info['count'] > 1000
        
    async def _load_embedded_data(self) -> bool:
        """載入內建預載數據"""
        if not os.path.exists(self.embedded_data_path):
            logger.error(f"❌ 內建數據文件不存在: {self.embedded_data_path}")
            return False
            
        conn = await asyncpg.connect(self.postgres_url)
        try:
            # 清空舊數據
            await conn.execute("""
                DELETE FROM satellite_orbital_cache 
                WHERE constellation = 'precomputed'
            """)
            
            # 載入預載數據
            with open(self.embedded_data_path, 'r') as f:
                sql_content = f.read()
                await conn.execute(sql_content)
                
            # 驗證載入結果
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM satellite_orbital_cache 
                WHERE constellation = 'precomputed'
            """)
            
            logger.info(f"✅ 成功載入 {count} 條預載衛星數據")
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ 載入內建數據失敗: {e}")
            return False
        finally:
            await conn.close()
            
    async def _generate_emergency_data(self) -> bool:
        """生成緊急最小數據集（1小時數據）"""
        try:
            from .emergency_satellite_generator import EmergencySatelliteGenerator
            
            generator = EmergencySatelliteGenerator(self.postgres_url)
            return await generator.generate_minimal_dataset(
                observer_lat=24.94417,
                observer_lon=121.37139,
                duration_hours=1,
                time_step_seconds=60
            )
        except ImportError:
            logger.error("❌ EmergencySatelliteGenerator 模組未找到")
            return False
        except Exception as e:
            logger.error(f"❌ 緊急數據生成失敗: {e}")
            return False