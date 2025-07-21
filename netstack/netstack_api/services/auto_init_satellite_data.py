#!/usr/bin/env python3
"""
自動初始化真實衛星數據服務
在容器啟動時自動檢查並下載真實 TLE 數據
"""

import asyncio
import os
import asyncpg
import structlog
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)

async def check_and_init_satellite_data():
    """檢查數據庫是否有衛星數據，如果沒有則自動下載"""
    try:
        # 獲取數據庫連接
        db_url = os.getenv("RL_DATABASE_URL", "postgresql://rl_user:rl_password@netstack-rl-postgres:5432/rl_research")
        
        conn = await asyncpg.connect(db_url)
        
        # 檢查是否有衛星數據
        count = await conn.fetchval("SELECT COUNT(*) FROM satellite_tle_data WHERE is_active = TRUE")
        
        if count == 0:
            logger.info("🛰️ 數據庫中沒有衛星數據，開始自動下載真實 TLE 數據...")
            
            # 導入衛星數據管理器
            from .satellite_data_manager import SatelliteDataManager
            
            # 初始化管理器
            manager = SatelliteDataManager(db_url)
            await manager.initialize()
            
            # 下載主要星座的數據
            constellations = ["starlink", "oneweb", "gps", "galileo"]
            
            for constellation in constellations:
                try:
                    logger.info(f"📡 下載 {constellation} TLE 數據...")
                    result = await manager.update_tle_data(constellation)
                    
                    success_count = result.get("satellites_added", 0) + result.get("satellites_updated", 0)
                    if success_count > 0:
                        logger.info(f"✅ {constellation} 成功載入 {success_count} 顆衛星")
                    else:
                        logger.warning(f"⚠️ {constellation} 沒有成功載入衛星數據")
                        
                except Exception as e:
                    logger.error(f"❌ {constellation} TLE 數據下載失敗: {e}")
                    
            await manager.close()
            
            # 重新檢查數據量
            final_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_tle_data WHERE is_active = TRUE")
            logger.info(f"🎉 衛星數據初始化完成，共載入 {final_count} 顆活躍衛星")
            
        else:
            logger.info(f"✅ 數據庫中已有 {count} 顆活躍衛星數據，跳過初始化")
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ 衛星數據自動初始化失敗: {e}")

def init_satellite_data_sync():
    """同步版本的初始化函數"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(check_and_init_satellite_data())
    finally:
        loop.close()

if __name__ == "__main__":
    init_satellite_data_sync()